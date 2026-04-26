"""
Web search service.
Uses DuckDuckGo search (no API key needed) via the duckduckgo-search library.
Returns a list of plain result dicts for agent consumption.
"""

import logging
from typing import Optional
from duckduckgo_search import DDGS
from app.core.constants import MAX_WEB_RESULTS

logger = logging.getLogger(__name__)


def web_search(query: str, max_results: int = MAX_WEB_RESULTS) -> list[dict]:
    """
    Search the web for a query.

    Returns a list of dicts with keys:
      - title: str
      - url: str
      - body: str  (snippet)
    """
    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=max_results))
        logger.info("Web search '%s' → %d results", query, len(results))
        return [
            {
                "title": r.get("title", ""),
                "url": r.get("href", ""),
                "body": r.get("body", ""),
            }
            for r in results
        ]
    except Exception as exc:
        logger.warning("Web search failed for query '%s': %s", query, exc)
        return []


def product_review_search(product_name: str) -> list[dict]:
    """Convenience wrapper for review-focused search."""
    query = f"{product_name} review reliability problems 2024"
    return web_search(query)


def marketplace_price_search(product_name: str, marketplace: str) -> list[dict]:
    """Convenience wrapper for marketplace price lookups."""
    query = f"{product_name} buy price site:{_marketplace_domain(marketplace)}"
    return web_search(query, max_results=3)


def _marketplace_domain(marketplace: str) -> str:
    domains = {
        "amazon": "amazon.com",
        "flipkart": "flipkart.com",
        "ebay": "ebay.com",
        "bestbuy": "bestbuy.com",
        "walmart": "walmart.com",
        "newegg": "newegg.com",
        "croma": "croma.com",
        "reliance digital": "reliancedigital.in",
    }
    return domains.get(marketplace.lower(), f"{marketplace.lower().replace(' ', '')}.com")
