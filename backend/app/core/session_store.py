"""
In-memory session store.
Stores all session data keyed by session_id.
For production, swap the dict backend with Redis.
"""

import time
import threading
from typing import Optional
from app.models.session import Session
from app.core.config import get_settings

settings = get_settings()

_store: dict[str, tuple[Session, float]] = {}   # session_id -> (session, expiry_timestamp)
_lock = threading.Lock()


def create_session(session: Session) -> None:
    expiry = time.time() + settings.session_ttl_seconds
    with _lock:
        _store[session.session_id] = (session, expiry)


def get_session(session_id: str) -> Optional[Session]:
    with _lock:
        entry = _store.get(session_id)
        if entry is None:
            return None
        session, expiry = entry
        if time.time() > expiry:
            del _store[session_id]
            return None
        return session


def update_session(session: Session) -> None:
    expiry = time.time() + settings.session_ttl_seconds
    with _lock:
        _store[session.session_id] = (session, expiry)


def delete_session(session_id: str) -> None:
    with _lock:
        _store.pop(session_id, None)


def evict_expired() -> int:
    """Remove all expired sessions. Returns count evicted."""
    now = time.time()
    expired_keys = []
    with _lock:
        for sid, (_, expiry) in _store.items():
            if now > expiry:
                expired_keys.append(sid)
        for key in expired_keys:
            del _store[key]
    return len(expired_keys)
