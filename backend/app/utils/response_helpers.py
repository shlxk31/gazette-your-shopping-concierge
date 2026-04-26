"""
Response helpers.
Build standardised API response envelopes and meta objects.
"""

import uuid
from datetime import datetime, timezone
from typing import Any, Optional

from app.schemas.common import ErrorObject, MetaObject
from app.core.constants import ErrorCode, API_VERSION


def make_meta() -> MetaObject:
    return MetaObject(
        request_id=str(uuid.uuid4()),
        timestamp=datetime.now(tz=timezone.utc).isoformat(),
        version=API_VERSION,
    )


def make_error(
    code: ErrorCode,
    message: str,
    field: Optional[str] = None,
) -> ErrorObject:
    return ErrorObject(code=code.value, message=message, field=field)


def format_search_results(results: list[dict]) -> str:
    """Serialise a list of search result dicts into a readable block for LLM prompts."""
    if not results:
        return "No results found."
    lines = []
    for i, r in enumerate(results, 1):
        title = r.get("title", "")
        url = r.get("url", "")
        body = r.get("body", "")[:600]   # Truncate to keep prompt size sane
        lines.append(f"[{i}] {title}\nURL: {url}\n{body}\n")
    return "\n".join(lines)


def paginate_questions(
    questions: list[dict],
    served_ids: set[str],
    batch_size: int,
) -> list[dict]:
    """
    Return the next batch of questions not yet served to the user.
    Respects priority ordering (lower number = higher priority).
    """
    unserved = [q for q in questions if q["id"] not in served_ids]
    unserved_sorted = sorted(unserved, key=lambda q: q.get("priority", 99))
    return unserved_sorted[:batch_size]
