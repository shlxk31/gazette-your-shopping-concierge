import logging
from fastapi import APIRouter, Query

from app.agents import product_discovery_agent
from app.core import session_store
from app.core.constants import ErrorCode, SessionStatus
from app.schemas.products import ProductsResponse, ProductsData, Product
from app.utils.response_helpers import make_meta, make_error

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("", response_model=ProductsResponse)
def get_products(session_id: str = Query(...)) -> ProductsResponse:
    """
    Triggers product discovery (if not already done) and returns
    the curated list of product recommendations.
    """
    meta = make_meta()

    session = session_store.get_session(session_id)
    if session is None:
        return ProductsResponse(
            success=False,
            error=make_error(
                ErrorCode.SESSION_NOT_FOUND,
                f"Session '{session_id}' not found or has expired.",
            ),
            meta=meta,
        )

    if session.status == SessionStatus.QUESTIONING:
        return ProductsResponse(
            success=False,
            error=make_error(
                ErrorCode.SESSION_NOT_READY,
                "Session preference gathering is not yet complete.",
            ),
            meta=meta,
        )

    try:
        raw_products = product_discovery_agent.discover(session)
        products = []
        for p in raw_products:
            try:
                products.append(Product(**p))
            except Exception as parse_exc:
                logger.warning("Skipping malformed product dict: %s", parse_exc)

        return ProductsResponse(
            success=True,
            data=ProductsData(products=products),
            meta=meta,
        )
    except ValueError as exc:
        logger.error("LLM error during product discovery: %s", exc)
        return ProductsResponse(
            success=False,
            error=make_error(ErrorCode.LLM_ERROR, str(exc)),
            meta=meta,
        )
    except Exception as exc:
        logger.exception("Unexpected error in /products: %s", exc)
        return ProductsResponse(
            success=False,
            error=make_error(ErrorCode.INTERNAL_ERROR, "An unexpected error occurred."),
            meta=meta,
        )
