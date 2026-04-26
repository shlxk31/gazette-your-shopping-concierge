"""
Internal session model.
Tracks the full lifecycle of a user's refinement + discovery session.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Optional
from app.core.constants import SessionStatus, QuestionMode


@dataclass
class AnsweredQuestion:
    question_id: str
    question_text: str
    value: Any                  # str | int | float | list[str]


@dataclass
class Session:
    session_id: str
    raw_query: str
    detected_category: str = ""
    mode: QuestionMode = QuestionMode.BASIC
    status: SessionStatus = SessionStatus.QUESTIONING

    # All questions generated for this session (basic + advanced)
    all_questions: list[dict] = field(default_factory=list)

    # IDs of questions already sent to the frontend (to avoid re-sending)
    served_question_ids: set[str] = field(default_factory=set)

    # Answers collected from the user
    answers: list[AnsweredQuestion] = field(default_factory=list)

    # Extra context added via the chat endpoint
    chat_context: list[str] = field(default_factory=list)

    # Discovered products (set once discovery is complete)
    products: list[dict] = field(default_factory=list)

    # Price data keyed by product_id
    price_cache: dict[str, list[dict]] = field(default_factory=dict)

    def answered_question_ids(self) -> set[str]:
        return {a.question_id for a in self.answers}

    def unanswered_questions(self) -> list[dict]:
        answered = self.answered_question_ids()
        return [q for q in self.all_questions if q["id"] not in answered]

    def get_answer_map(self) -> dict[str, Any]:
        """Returns {question_id: value} for prompt construction."""
        return {a.question_id: a.value for a in self.answers}

    def summarise_preferences(self) -> str:
        """Human-readable preference summary used in product discovery prompts."""
        lines = [f"Original query: {self.raw_query}"]
        for a in self.answers:
            lines.append(f"- {a.question_text}: {a.value}")
        for msg in self.chat_context:
            lines.append(f"- User note: {msg}")
        return "\n".join(lines)
