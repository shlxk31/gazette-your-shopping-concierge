"""
Web search service.
Provider: Tavily (handles web search, image search, and domain-targeted price search).
"""

import logging
from typing import Optional
from tavily import TavilyClient

from app.core.config import get_settings
from app.core.constants import MAX_WEB_RESULTS

logger = logging.getLogger(__name__)
settings = get_settings()

_client: Optional[TavilyClient] = None

def _get_client() -> TavilyClient:
    global _client
    if _client is None:
        _client = TavilyClient(api_key=settings.tavily_api_key)
    return _client


# ──────────────────────────────────────────────
# Internal helpers
# ──────────────────────────────────────────────

def _tavily_search(query: str, max_results: int, **kwargs) -> list[dict]:
    try:
        resp = _get_client().search(
            query=query,
            max_results=max_results,
            **kwargs
        )
        results = resp.get("results", [])
        logger.info("Tavily '%s' → %d results", query, len(results))
        return [
            {"title": r.get("title", ""), "url": r.get("url", ""), "body": r.get("content", "")}
            for r in results
        ]
    except Exception as exc:
        logger.warning("Tavily search failed '%s': %s", query, exc)
        return []


def _tavily_image(query: str) -> Optional[str]:
    """Return first image URL for a product name, or None."""
    try:
        resp = _get_client().search(
            query=query,
            max_results=3,
            include_images=True,
        )
        images = resp.get("images", [])
        return images[0] if images else None
    except Exception as exc:
        logger.warning("Tavily image search failed '%s': %s", query, exc)
        return None


# ──────────────────────────────────────────────
# Public interface — signatures unchanged
# ──────────────────────────────────────────────

def web_search(query: str, max_results: int = MAX_WEB_RESULTS) -> list[dict]:
    return _tavily_search(query, max_results)


def product_review_search(product_name: str) -> list[dict]:
    query = f"{product_name} review reliability problems 2025"
    return _tavily_search(query, MAX_WEB_RESULTS)


def marketplace_price_search(product_name: str, marketplace: str) -> list[dict]:
    """Legacy per-marketplace lookup — kept for backwards compat."""
    return _tavily_search(
        f"{product_name} price buy {marketplace}",
        max_results=3,
        include_domains=[f"{marketplace.lower().replace(' ', '')}.com",
                         f"{marketplace.lower().replace(' ', '')}.in"],
    )


def google_shopping_search(product_name: str) -> list[dict]:
    """
    Single Tavily call targeting Indian marketplaces.
    Used by MarketplaceAggregatorAgent — replaces the 8-session Airtop fan-out.
    """
    return _tavily_search(
        f"{product_name} buy price",
        max_results=8,
        include_domains=[
            "amazon.in", "flipkart.com", "croma.com", "reliancedigital.in"
        ],
    )


def product_image_search(product_name: str) -> Optional[str]:
    result = _tavily_image(product_name)
    if result:
        return result
    return f"https://loremflickr.com/400/300/{product_name.replace(' ', ',')}"