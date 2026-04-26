"""
Tests for QueryRefinementAgent.
Groq calls are mocked so no API key is required to run tests.
"""

import pytest
from unittest.mock import patch, MagicMock

from app.agents.query_refinement_agent import QueryRefinementAgent
from app.core.constants import SessionStatus, QuestionMode
from app.schemas.questions import AnswerItem


# ── Fixtures ──────────────────────────────────────────────────────────────────

MOCK_LLM_QUESTIONS = {
    "detected_category": "laptop",
    "questions": [
        {
            "id": "q_budget",
            "category": "budget",
            "question_text": "What is your budget?",
            "description": None,
            "input_type": "range_slider",
            "options": None,
            "range": {"min": 300, "max": 5000, "step": 100, "unit": "USD"},
            "default_value": None,
            "placeholder": None,
            "is_required": True,
            "depends_on": None,
            "validation": None,
            "priority": 1,
            "mode": "basic",
            "tags": ["budget"],
        },
        {
            "id": "q_usage",
            "category": "usage",
            "question_text": "What will you primarily use it for?",
            "description": None,
            "input_type": "checkbox",
            "options": [
                {"label": "Machine Learning", "value": "ml"},
                {"label": "Web Development", "value": "web_dev"},
                {"label": "Data Science", "value": "data_science"},
            ],
            "range": None,
            "default_value": None,
            "placeholder": None,
            "is_required": True,
            "depends_on": None,
            "validation": None,
            "priority": 2,
            "mode": "basic",
            "tags": ["usage"],
        },
        {
            "id": "q_os",
            "category": "preference",
            "question_text": "Which OS do you prefer?",
            "description": None,
            "input_type": "radio",
            "options": [
                {"label": "Windows", "value": "windows"},
                {"label": "macOS", "value": "macos"},
                {"label": "Linux", "value": "linux"},
            ],
            "range": None,
            "default_value": None,
            "placeholder": None,
            "is_required": True,
            "depends_on": None,
            "validation": None,
            "priority": 3,
            "mode": "basic",
            "tags": ["os"],
        },
        {
            "id": "q_ram",
            "category": "technical",
            "question_text": "How much RAM do you need?",
            "description": "Minimum RAM in GB",
            "input_type": "radio",
            "options": [
                {"label": "8 GB", "value": "8"},
                {"label": "16 GB", "value": "16"},
                {"label": "32 GB", "value": "32"},
                {"label": "64 GB", "value": "64"},
            ],
            "range": None,
            "default_value": None,
            "placeholder": None,
            "is_required": False,
            "depends_on": None,
            "validation": None,
            "priority": 4,
            "mode": "advanced",
            "tags": ["ram", "technical"],
        },
    ],
}


@pytest.fixture
def agent():
    return QueryRefinementAgent()


# ── Tests ─────────────────────────────────────────────────────────────────────

@patch("app.agents.query_refinement_agent.complete_json", return_value=MOCK_LLM_QUESTIONS)
@patch("app.agents.query_refinement_agent.session_store.create_session")
def test_initialise_session_creates_correct_session(mock_create, mock_llm, agent):
    session = agent.initialise_session("I need a powerful laptop for ML")

    assert session.raw_query == "I need a powerful laptop for ML"
    assert session.detected_category == "laptop"
    assert session.status == SessionStatus.QUESTIONING
    assert session.mode == QuestionMode.BASIC
    assert len(session.all_questions) == 4
    mock_create.assert_called_once()


@patch("app.agents.query_refinement_agent.complete_json", return_value=MOCK_LLM_QUESTIONS)
@patch("app.agents.query_refinement_agent.session_store.create_session")
@patch("app.agents.query_refinement_agent.session_store.update_session")
def test_get_initial_questions_returns_only_basic(mock_update, mock_create, mock_llm, agent):
    session = agent.initialise_session("I need a powerful laptop for ML")
    batch = agent.get_initial_questions(session)

    # Only basic questions should be in the initial batch
    for q in batch:
        assert q["mode"] == "basic"

    served_ids = {q["id"] for q in batch}
    assert served_ids == session.served_question_ids


@patch("app.agents.query_refinement_agent.complete_json", return_value=MOCK_LLM_QUESTIONS)
@patch("app.agents.query_refinement_agent.session_store.create_session")
@patch("app.agents.query_refinement_agent.session_store.update_session")
def test_submit_answers_marks_session_ready_when_all_answered(
    mock_update, mock_create, mock_llm, agent
):
    session = agent.initialise_session("ML laptop")
    agent.get_initial_questions(session)  # serve all basic questions

    answers = [
        AnswerItem(question_id="q_budget", value=1500),
        AnswerItem(question_id="q_usage", value=["ml", "data_science"]),
        AnswerItem(question_id="q_os", value="linux"),
    ]
    result = agent.submit_answers(session, answers)

    # All basic questions answered — session should be complete
    assert result["is_complete"] is True
    assert result["redirect_to"] == "/products"
    assert session.status == SessionStatus.READY


@patch("app.agents.query_refinement_agent.complete_json", return_value=MOCK_LLM_QUESTIONS)
@patch("app.agents.query_refinement_agent.session_store.create_session")
@patch("app.agents.query_refinement_agent.session_store.update_session")
def test_submit_partial_answers_returns_next_batch(
    mock_update, mock_create, mock_llm, agent
):
    session = agent.initialise_session("ML laptop")
    # Only serve q_budget so q_usage and q_os are still unserved
    session.served_question_ids.add("q_budget")

    answers = [AnswerItem(question_id="q_budget", value=1500)]
    result = agent.submit_answers(session, answers)

    assert result["is_complete"] is False
    assert result["next_questions"] is not None


@patch("app.agents.query_refinement_agent.complete_json", return_value=MOCK_LLM_QUESTIONS)
@patch("app.agents.query_refinement_agent.session_store.create_session")
@patch("app.agents.query_refinement_agent.session_store.update_session")
def test_summarise_preferences_includes_all_context(
    mock_update, mock_create, mock_llm, agent
):
    session = agent.initialise_session("ML laptop")
    session.answers = []  # reset

    from app.models.session import AnsweredQuestion
    session.answers.append(
        AnsweredQuestion(question_id="q_budget", question_text="What is your budget?", value=1500)
    )
    session.chat_context.append("I prefer thin and light")

    summary = session.summarise_preferences()
    assert "ML laptop" in summary
    assert "1500" in summary
    assert "thin and light" in summary


@patch(
    "app.agents.query_refinement_agent.complete_json",
    return_value={"reply": "Noted!", "new_questions": []},
)
@patch("app.agents.query_refinement_agent.session_store.update_session")
def test_handle_chat_appends_context(mock_update, mock_llm, agent):
    from app.models.session import Session

    session = Session(session_id="test-123", raw_query="laptop")
    result = agent.handle_chat(session, "I also need good battery life")

    assert "I also need good battery life" in session.chat_context
    assert result["reply"] == "Noted!"
    assert result["new_questions"] == []
