"""
Groq LLM client.
Provides a thin wrapper around the Groq SDK with:
  - automatic retry on transient failures
  - structured JSON response extraction
  - a plain text completion helper
"""

import json
import logging
import re
from typing import Any, Optional

from groq import Groq, APIStatusError, APITimeoutError
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from app.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

_client: Optional[Groq] = None


def get_groq_client() -> Groq:
    global _client
    if _client is None:
        _client = Groq(api_key=settings.groq_api_key)
    return _client


# ──────────────────────────────────────────────
# Retry policy
# ──────────────────────────────────────────────

_RETRYABLE = (APITimeoutError,)


@retry(
    retry=retry_if_exception_type(_RETRYABLE),
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=8),
    reraise=True,
)
def _chat_completion(messages: list[dict], temperature: float = 0.3) -> str:
    """Raw completion — returns the assistant message string."""
    client = get_groq_client()
    response = client.chat.completions.create(
        model=settings.groq_model,
        messages=messages,
        temperature=temperature,
        max_tokens=4096,
    )
    return response.choices[0].message.content or ""


# ──────────────────────────────────────────────
# Public helpers
# ──────────────────────────────────────────────

def complete(system_prompt: str, user_prompt: str, temperature: float = 0.3) -> str:
    """Return raw text completion."""
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]
    return _chat_completion(messages, temperature=temperature)


def complete_json(system_prompt: str, user_prompt: str, temperature: float = 0.1) -> Any:
    """
    Return parsed JSON from LLM.
    Strips markdown fences if the model wraps its output in ```json ... ```.
    Raises ValueError if the response cannot be parsed.
    """
    full_system = (
        system_prompt
        + "\n\nIMPORTANT: Respond ONLY with valid JSON. "
        "Do not include any explanation, markdown fences, or commentary outside the JSON."
    )
    raw = complete(full_system, user_prompt, temperature=temperature)
    return _extract_json(raw)


def complete_with_history(
    messages: list[dict],
    temperature: float = 0.4,
) -> str:
    """Multi-turn completion — caller manages the full message history."""
    return _chat_completion(messages, temperature=temperature)


# ──────────────────────────────────────────────
# Internals
# ──────────────────────────────────────────────

def _extract_json(raw: str) -> Any:
    """Strip markdown fences and parse JSON."""
    # Remove ```json ... ``` or ``` ... ``` wrappers
    cleaned = re.sub(r"^```(?:json)?\s*", "", raw.strip(), flags=re.IGNORECASE)
    cleaned = re.sub(r"\s*```$", "", cleaned.strip())
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError as exc:
        logger.error("JSON parse failed. Raw LLM output:\n%s", raw)
        raise ValueError(f"LLM returned non-JSON output: {exc}") from exc
