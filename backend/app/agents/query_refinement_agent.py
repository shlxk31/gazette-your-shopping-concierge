"""
Query Refinement Agent.

Responsibilities:
  1. Accept a raw user query and understand the product intent.
  2. Ask Groq to generate structured questions (basic + advanced).
  3. Store the questions against the session.
  4. Handle chat messages that add context and optionally emit new questions.
"""

import uuid
import logging
from typing import Optional

from app.core.constants import (
    QuestionMode,
    SessionStatus,
    BASIC_QUESTIONS_COUNT,
    ADVANCED_QUESTIONS_COUNT,
)
from app.core import session_store
from app.models.session import Session, AnsweredQuestion
from app.schemas.common import Question
from app.schemas.questions import AnswerItem
from app.services.groq_client import complete_json
from app.utils.prompt_builder import build_query_refinement_prompt, build_chat_prompt
from app.utils.response_helpers import paginate_questions
from app.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class QueryRefinementAgent:
    """
    Stateless agent class — all state lives in the Session object.
    Each public method accepts a session and returns updated data.
    """

    # ──────────────────────────────────────────────
    # Initialise a new session from a raw user query
    # ──────────────────────────────────────────────

    def initialise_session(self, query: str) -> Session:
        """
        Parse the user query, generate questions, and persist a new session.
        Returns the newly created Session.
        """
        logger.info("Initialising session for query: %s", query)

        system_prompt, user_prompt = build_query_refinement_prompt(query)
        llm_data = complete_json(system_prompt, user_prompt)

        detected_category: str = llm_data.get("detected_category", "product")
        raw_questions: list[dict] = llm_data.get("questions", [])

        # Ensure all questions have required fields with safe defaults
        questions = [self._normalise_question(q) for q in raw_questions]

        session = Session(
            session_id=str(uuid.uuid4()),
            raw_query=query,
            detected_category=detected_category,
            mode=QuestionMode.BASIC,
            status=SessionStatus.QUESTIONING,
            all_questions=questions,
        )
        session_store.create_session(session)
        logger.info(
            "Session %s created | category=%s | questions=%d",
            session.session_id,
            detected_category,
            len(questions),
        )
        return session

    # ──────────────────────────────────────────────
    # Get the first batch of questions to serve
    # ──────────────────────────────────────────────

    def get_initial_questions(self, session: Session) -> list[dict]:
        """
        Returns the first batch of basic questions, sorted by priority.
        Marks them as served.
        """
        mode_questions = [
            q for q in session.all_questions if q.get("mode") == QuestionMode.BASIC
        ]
        batch = paginate_questions(
            mode_questions,
            session.served_question_ids,
            settings.questions_batch_size,
        )
        for q in batch:
            session.served_question_ids.add(q["id"])
        session_store.update_session(session)
        return batch

    # ──────────────────────────────────────────────
    # Submit answers and determine next step
    # ──────────────────────────────────────────────

    def submit_answers(
        self,
        session: Session,
        answer_items: list[AnswerItem],
    ) -> dict:
        """
        Record the user's answers.
        Returns a dict:
          {
            "next_questions": list[dict] | None,
            "is_complete": bool,
            "redirect_to": str | None,
          }
        """
        # Persist answers
        answered_ids = session.answered_question_ids()
        question_text_map = {q["id"]: q["question_text"] for q in session.all_questions}

        for item in answer_items:
            if item.question_id in answered_ids:
                # Update existing answer
                for ans in session.answers:
                    if ans.question_id == item.question_id:
                        ans.value = item.value
                        break
            else:
                session.answers.append(
                    AnsweredQuestion(
                        question_id=item.question_id,
                        question_text=question_text_map.get(item.question_id, ""),
                        value=item.value,
                    )
                )

        # Determine which questions are still pending for the current mode
        pending = self._pending_for_mode(session)

        if pending:
            # Serve next batch
            batch = paginate_questions(
                pending,
                session.served_question_ids,
                settings.questions_batch_size,
            )
            for q in batch:
                session.served_question_ids.add(q["id"])
            session_store.update_session(session)
            return {"next_questions": batch, "is_complete": False, "redirect_to": None}

        # All required questions answered — mark session ready
        session.status = SessionStatus.READY
        session_store.update_session(session)
        logger.info("Session %s is now READY for product discovery.", session.session_id)
        return {
            "next_questions": None,
            "is_complete": True,
            "redirect_to": "/products",
        }

    # ──────────────────────────────────────────────
    # Switch mode (basic ↔ advanced)
    # ──────────────────────────────────────────────

    def set_mode(self, session: Session, mode: QuestionMode) -> list[dict]:
        """
        Switch the session mode and return unserved questions for that mode.
        """
        session.mode = mode
        advanced_questions = [
            q for q in session.all_questions if q.get("mode") == QuestionMode.ADVANCED
        ]
        batch = paginate_questions(
            advanced_questions,
            session.served_question_ids,
            settings.questions_batch_size,
        )
        for q in batch:
            session.served_question_ids.add(q["id"])
        session_store.update_session(session)
        return batch

    # ──────────────────────────────────────────────
    # Chat message handling
    # ──────────────────────────────────────────────

    def handle_chat(self, session: Session, message: str) -> dict:
        """
        Process a free-form user message.
        Adds context to session, optionally emits new questions.
        Returns {"reply": str, "new_questions": list[dict]}.
        """
        session.chat_context.append(message)

        preferences = session.summarise_preferences()
        system_prompt, user_prompt = build_chat_prompt(preferences, message)

        llm_data = complete_json(system_prompt, user_prompt)

        reply: str = llm_data.get("reply", "Got it! I've noted that.")
        new_raw: list[dict] = llm_data.get("new_questions", [])

        new_questions = []
        for q in new_raw:
            normalised = self._normalise_question(q)
            # Only add if not already in session
            existing_ids = {eq["id"] for eq in session.all_questions}
            if normalised["id"] not in existing_ids:
                session.all_questions.append(normalised)
                new_questions.append(normalised)

        session_store.update_session(session)
        return {"reply": reply, "new_questions": new_questions}

    # ──────────────────────────────────────────────
    # Private helpers
    # ──────────────────────────────────────────────

    def _pending_for_mode(self, session: Session) -> list[dict]:
        """Return unanswered, unserved questions for the current session mode."""
        answered = session.answered_question_ids()
        return [
            q
            for q in session.all_questions
            if q["id"] not in answered
            and q["id"] not in session.served_question_ids
            and q.get("mode", QuestionMode.BASIC) == session.mode
        ]

    def _normalise_question(self, q: dict) -> dict:
        """Apply safe defaults to an LLM-generated question dict."""
        q.setdefault("id", f"q_{uuid.uuid4().hex[:8]}")
        q.setdefault("category", "other")
        q.setdefault("description", None)
        q.setdefault("options", None)
        q.setdefault("range", None)
        q.setdefault("default_value", None)
        q.setdefault("placeholder", None)
        q.setdefault("is_required", True)
        q.setdefault("depends_on", None)
        q.setdefault("validation", None)
        q.setdefault("priority", 99)
        q.setdefault("mode", "basic")
        q.setdefault("tags", [])
        return q
