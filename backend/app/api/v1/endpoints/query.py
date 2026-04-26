import logging
from fastapi import APIRouter

from app.agents import query_refinement_agent
from app.schemas.query import QueryRequest, QueryResponse, QueryData
from app.schemas.common import Question
from app.utils.response_helpers import make_meta, make_error
from app.core.constants import ErrorCode

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("", response_model=QueryResponse)
def initialise_query(request: QueryRequest) -> QueryResponse:
    """
    Accepts a raw user query, creates a session, and returns
    the first batch of structured questions.
    """
    meta = make_meta()
    try:
        session = query_refinement_agent.initialise_session(request.query)
        initial_q_dicts = query_refinement_agent.get_initial_questions(session)
        initial_questions = [Question(**q) for q in initial_q_dicts]

        return QueryResponse(
            success=True,
            data=QueryData(
                session_id=session.session_id,
                detected_category=session.detected_category,
                initial_questions=initial_questions,
                mode=session.mode,
            ),
            meta=meta,
        )
    except ValueError as exc:
        logger.error("LLM error during query init: %s", exc)
        return QueryResponse(
            success=False,
            error=make_error(ErrorCode.LLM_ERROR, str(exc)),
            meta=meta,
        )
    except Exception as exc:
        logger.exception("Unexpected error in /query: %s", exc)
        return QueryResponse(
            success=False,
            error=make_error(ErrorCode.INTERNAL_ERROR, "An unexpected error occurred."),
            meta=meta,
        )
