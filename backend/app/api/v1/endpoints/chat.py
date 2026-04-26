import logging
from fastapi import APIRouter

from app.agents import query_refinement_agent
from app.core import session_store
from app.core.constants import ErrorCode
from app.schemas.chat import ChatRequest, ChatResponse, ChatData
from app.schemas.common import Question
from app.utils.response_helpers import make_meta, make_error

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("", response_model=ChatResponse)
def chat(request: ChatRequest) -> ChatResponse:
    """
    Handles a free-form user message to refine preferences.
    Returns an assistant reply and optionally new/updated questions.
    """
    meta = make_meta()

    session = session_store.get_session(request.session_id)
    if session is None:
        return ChatResponse(
            success=False,
            error=make_error(
                ErrorCode.SESSION_NOT_FOUND,
                f"Session '{request.session_id}' not found or has expired.",
            ),
            meta=meta,
        )

    try:
        result = query_refinement_agent.handle_chat(session, request.message)
        new_q_dicts = result.get("new_questions") or []
        updated_questions = [Question(**q) for q in new_q_dicts] if new_q_dicts else None

        return ChatResponse(
            success=True,
            data=ChatData(
                message=result["reply"],
                updated_questions=updated_questions,
            ),
            meta=meta,
        )
    except ValueError as exc:
        logger.error("LLM error in /chat: %s", exc)
        return ChatResponse(
            success=False,
            error=make_error(ErrorCode.LLM_ERROR, str(exc)),
            meta=meta,
        )
    except Exception as exc:
        logger.exception("Unexpected error in /chat: %s", exc)
        return ChatResponse(
            success=False,
            error=make_error(ErrorCode.INTERNAL_ERROR, "An unexpected error occurred."),
            meta=meta,
        )
