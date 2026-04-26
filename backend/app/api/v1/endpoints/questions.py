import logging
from fastapi import APIRouter

from app.agents import query_refinement_agent
from app.core import session_store
from app.core.constants import ErrorCode
from app.schemas.questions import AnswerRequest, AnswerResponse, AnswerData
from app.schemas.common import Question
from app.utils.response_helpers import make_meta, make_error

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/answer", response_model=AnswerResponse)
def submit_answers(request: AnswerRequest) -> AnswerResponse:
    """
    Accepts user answers and returns the next batch of questions
    or signals that preference gathering is complete.
    """
    meta = make_meta()

    session = session_store.get_session(request.session_id)
    if session is None:
        return AnswerResponse(
            success=False,
            error=make_error(
                ErrorCode.SESSION_NOT_FOUND,
                f"Session '{request.session_id}' not found or has expired.",
            ),
            meta=meta,
        )

    try:
        result = query_refinement_agent.submit_answers(session, request.answers)
        next_q_dicts = result.get("next_questions") or []
        next_questions = [Question(**q) for q in next_q_dicts] if next_q_dicts else None

        return AnswerResponse(
            success=True,
            data=AnswerData(
                next_questions=next_questions,
                is_complete=result["is_complete"],
                redirect_to=result.get("redirect_to"),
            ),
            meta=meta,
        )
    except Exception as exc:
        logger.exception("Error in /questions/answer: %s", exc)
        return AnswerResponse(
            success=False,
            error=make_error(ErrorCode.INTERNAL_ERROR, "An unexpected error occurred."),
            meta=meta,
        )
