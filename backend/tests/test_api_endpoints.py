"""
API endpoint integration tests.
Uses FastAPI TestClient with agents fully mocked.
"""

import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

from app.main import app
from app.models.session import Session
from app.core.constants import SessionStatus, QuestionMode

client = TestClient(app)


# ── Shared fixtures ───────────────────────────────────────────────────────────

MOCK_SESSION = Session(
    session_id="test-session-abc",
    raw_query="I need a laptop for ML",
    detected_category="laptop",
    mode=QuestionMode.BASIC,
    status=SessionStatus.QUESTIONING,
)

MOCK_SESSION_READY = Session(
    session_id="test-session-ready",
    raw_query="I need a laptop for ML",
    detected_category="laptop",
    status=SessionStatus.READY,
)
MOCK_SESSION_READY.products = [
    {
        "id": "macbook-pro-m3",
        "name": "Apple MacBook Pro M3",
        "image": "",
        "description": "Great ML laptop.",
        "features": ["M3 chip"],
        "match_score": 0.9,
        "match_reasons": ["Fast"],
        "missing_features": [],
        "review_summary": {"rating": 4.7, "sentiment": "positive", "highlights": [], "concerns": []},
        "reliability": {"score": 0.9, "summary": "Reliable."},
        "warranty": {"duration": "1 year", "type": "Limited"},
    }
]

MOCK_QUESTION = {
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
    "tags": [],
}


# ── POST /api/v1/query ────────────────────────────────────────────────────────

@patch("app.api.v1.endpoints.query.query_refinement_agent.initialise_session", return_value=MOCK_SESSION)
@patch("app.api.v1.endpoints.query.query_refinement_agent.get_initial_questions", return_value=[MOCK_QUESTION])
def test_post_query_success(mock_questions, mock_init):
    response = client.post("/api/v1/query", json={"query": "I need a laptop for ML"})

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["data"]["session_id"] == "test-session-abc"
    assert body["data"]["detected_category"] == "laptop"
    assert len(body["data"]["initial_questions"]) == 1
    assert body["error"] is None


def test_post_query_missing_body():
    response = client.post("/api/v1/query", json={})
    assert response.status_code == 422


# ── POST /api/v1/questions/answer ────────────────────────────────────────────

@patch("app.api.v1.endpoints.questions.session_store.get_session", return_value=MOCK_SESSION)
@patch(
    "app.api.v1.endpoints.questions.query_refinement_agent.submit_answers",
    return_value={"next_questions": None, "is_complete": True, "redirect_to": "/products"},
)
def test_post_answers_complete(mock_submit, mock_session):
    response = client.post(
        "/api/v1/questions/answer",
        json={
            "session_id": "test-session-abc",
            "answers": [{"question_id": "q_budget", "value": 1500}],
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["data"]["is_complete"] is True
    assert body["data"]["redirect_to"] == "/products"


@patch("app.api.v1.endpoints.questions.session_store.get_session", return_value=None)
def test_post_answers_session_not_found(mock_session):
    response = client.post(
        "/api/v1/questions/answer",
        json={"session_id": "ghost-session", "answers": []},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["success"] is False
    assert body["error"]["code"] == "SESSION_NOT_FOUND"


# ── GET /api/v1/products ──────────────────────────────────────────────────────

@patch("app.api.v1.endpoints.products.session_store.get_session", return_value=MOCK_SESSION_READY)
@patch(
    "app.api.v1.endpoints.products.product_discovery_agent.discover",
    return_value=MOCK_SESSION_READY.products,
)
def test_get_products_success(mock_discover, mock_session):
    response = client.get("/api/v1/products?session_id=test-session-ready")

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert len(body["data"]["products"]) == 1
    assert body["data"]["products"][0]["id"] == "macbook-pro-m3"


@patch("app.api.v1.endpoints.products.session_store.get_session", return_value=MOCK_SESSION)
def test_get_products_session_not_ready(mock_session):
    # MOCK_SESSION has status=QUESTIONING
    response = client.get("/api/v1/products?session_id=test-session-abc")

    body = response.json()
    assert body["success"] is False
    assert body["error"]["code"] == "SESSION_NOT_READY"


# ── GET /api/v1/products/:id/prices ──────────────────────────────────────────

MOCK_PRICES = [
    {"marketplace": "Amazon", "price": 1999.0, "currency": "USD", "url": "https://amazon.com", "availability": "in_stock", "is_best": True},
]

@patch("app.api.v1.endpoints.prices.session_store.get_session", return_value=MOCK_SESSION_READY)
@patch(
    "app.api.v1.endpoints.prices.marketplace_aggregator_agent.get_prices",
    return_value=MOCK_PRICES,
)
def test_get_prices_success(mock_prices, mock_session):
    response = client.get("/api/v1/products/macbook-pro-m3/prices?session_id=test-session-ready")

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert len(body["data"]["prices"]) == 1
    assert body["data"]["prices"][0]["is_best"] is True


# ── POST /api/v1/chat ─────────────────────────────────────────────────────────

@patch("app.api.v1.endpoints.chat.session_store.get_session", return_value=MOCK_SESSION)
@patch(
    "app.api.v1.endpoints.chat.query_refinement_agent.handle_chat",
    return_value={"reply": "Got it!", "new_questions": []},
)
def test_post_chat_success(mock_chat, mock_session):
    response = client.post(
        "/api/v1/chat",
        json={"session_id": "test-session-abc", "message": "I prefer thin and light"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["data"]["message"] == "Got it!"
    assert body["data"]["updated_questions"] is None


# ── Health check ──────────────────────────────────────────────────────────────

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
