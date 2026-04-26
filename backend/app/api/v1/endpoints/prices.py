import logging
from fastapi import APIRouter, Query

from app.agents import marketplace_aggregator_agent
from app.core import session_store
from app.core.constants import ErrorCode
from app.schemas.prices import PricesResponse, PricesData, MarketplacePrice
from app.utils.response_helpers import make_meta, make_error

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/{product_id}/prices", response_model=PricesResponse)
def get_prices(
    product_id: str,
    session_id: str = Query(...),
) -> PricesResponse:
    """
    Fetches and compares pricing for a product across multiple marketplaces.
    """
    meta = make_meta()

    session = session_store.get_session(session_id)
    if session is None:
        return PricesResponse(
            success=False,
            error=make_error(
                ErrorCode.SESSION_NOT_FOUND,
                f"Session '{session_id}' not found or has expired.",
            ),
            meta=meta,
        )

    try:
        raw_prices = marketplace_aggregator_agent.get_prices(session, product_id)
        if not raw_prices:
            return PricesResponse(
                success=False,
                error=make_error(
                    ErrorCode.PRODUCT_NOT_FOUND,
                    f"No pricing data found for product '{product_id}'.",
                ),
                meta=meta,
            )

        prices = []
        for p in raw_prices:
            try:
                prices.append(MarketplacePrice(**p))
            except Exception as parse_exc:
                logger.warning("Skipping malformed price entry: %s", parse_exc)

        return PricesResponse(
            success=True,
            data=PricesData(prices=prices),
            meta=meta,
        )
    except Exception as exc:
        logger.exception("Unexpected error in /prices: %s", exc)
        return PricesResponse(
            success=False,
            error=make_error(ErrorCode.INTERNAL_ERROR, "An unexpected error occurred."),
            meta=meta,
        )
