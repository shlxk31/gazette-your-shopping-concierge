"""
Web search service.
Primary: Airtop API (real browser-based search, bypasses blocks).
Fallback: DuckDuckGo (no API key needed) via duckduckgo-search library.

Function signatures are unchanged — agents call web_search() exactly as before.
"""

import json
import logging
import re
import requests
from typing import Optional

from duckduckgo_search import DDGS

from app.core.config import get_settings
from app.core.constants import MAX_WEB_RESULTS

logger = logging.getLogger(__name__)
settings = get_settings()

AIRTOP_BASE_URL = "https://api.airtop.ai/v1"

# JSON schema for structured search result extraction
_SEARCH_RESULT_SCHEMA = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "type": "object",
    "properties": {
        "results": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "title": {"type": "string", "description": "Title of the search result"},
                    "url":   {"type": "string", "description": "Full URL of the result"},
                    "body":  {"type": "string", "description": "Snippet or description"},
                },
                "required": ["title", "url", "body"],
                "additionalProperties": False,
            },
        },
        "error": {"type": "string", "description": "Error message if results cannot be extracted", "minLength": 1},
    },
}

# JSON schema for price extraction
_PRICE_RESULT_SCHEMA = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "type": "object",
    "properties": {
        "results": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "title": {"type": "string", "description": "Product name as shown on page"},
                    "url":   {"type": "string", "description": "Product page URL"},
                    "body":  {"type": "string", "description": "Price with currency and availability, e.g. 'Price: Rs.85990 | Availability: In Stock'"},
                },
                "required": ["title", "url", "body"],
                "additionalProperties": False,
            },
        },
        "error": {"type": "string", "description": "Error if product not found", "minLength": 1},
    },
}


# ──────────────────────────────────────────────
# Shared Airtop helpers
# ──────────────────────────────────────────────

def _airtop_headers() -> dict:
    return {
        "Authorization": f"Bearer {settings.airtop_api_key}",
        "Content-Type": "application/json",
    }


def _airtop_create_session() -> Optional[str]:
    resp = requests.post(
        f"{AIRTOP_BASE_URL}/sessions",
        headers=_airtop_headers(),
        json={"configuration": {"timeoutMinutes": 2}},
        timeout=30,
    )
    resp.raise_for_status()
    session_id = resp.json().get("data", {}).get("id")
    if not session_id:
        logger.warning("Airtop: no session ID in response: %s", resp.text[:200])
    return session_id


def _airtop_create_window(session_id: str, url: str) -> Optional[str]:
    resp = requests.post(
        f"{AIRTOP_BASE_URL}/sessions/{session_id}/windows",
        headers=_airtop_headers(),
        json={"url": url},
        timeout=30,
    )
    resp.raise_for_status()
    data = resp.json().get("data", {})
    # Airtop returns windowId for windows (not id)
    window_id = data.get("windowId") or data.get("id")
    if not window_id:
        logger.warning("Airtop: no windowId in response: %s", resp.text[:200])
    return window_id


def _airtop_page_query(session_id: str, window_id: str, prompt: str, schema: dict) -> dict:
    resp = requests.post(
        f"{AIRTOP_BASE_URL}/sessions/{session_id}/windows/{window_id}/page-query",
        headers=_airtop_headers(),
        json={
            "prompt": prompt,
            "configuration": {"outputSchema": schema},
        },
        timeout=90,
    )
    resp.raise_for_status()
    raw_text = resp.json().get("data", {}).get("modelResponse", "")
    logger.debug("Airtop modelResponse: %s", raw_text[:300])
    cleaned = re.sub(r"^```(?:json)?\s*", "", raw_text.strip(), flags=re.IGNORECASE)
    cleaned = re.sub(r"\s*```$", "", cleaned.strip())
    return json.loads(cleaned)


def _airtop_terminate(session_id: str) -> None:
    try:
        requests.delete(
            f"{AIRTOP_BASE_URL}/sessions/{session_id}",
            headers=_airtop_headers(),
            timeout=10,
        )
    except Exception:
        pass


# ──────────────────────────────────────────────
# Airtop web search (Google)
# ──────────────────────────────────────────────

def _airtop_search(query: str, max_results: int) -> Optional[list[dict]]:
    if not settings.airtop_api_key:
        return None

    session_id = None
    try:
        session_id = _airtop_create_session()
        if not session_id:
            return None

        url = f"https://www.google.com/search?q={requests.utils.quote(query)}&num={max_results}"
        window_id = _airtop_create_window(session_id, url)
        if not window_id:
            return None

        prompt = (
            f"This is a Google search results page for: '{query}'. "
            f"Extract the top {max_results} organic results (skip ads). "
            "Provide title, url, and body snippet for each."
        )
        data = _airtop_page_query(session_id, window_id, prompt, _SEARCH_RESULT_SCHEMA)

        if data.get("error"):
            logger.warning("Airtop search error: %s", data["error"])
            return None

        results = data.get("results", [])
        logger.info("Airtop search '%s' → %d results", query, len(results))
        return results[:max_results] if results else None

    except Exception as exc:
        logger.warning("Airtop search failed '%s': %s", query, exc)
        return None
    finally:
        if session_id:
            _airtop_terminate(session_id)


# ──────────────────────────────────────────────
# Airtop marketplace price fetch
# ──────────────────────────────────────────────

def _marketplace_url(domain: str, product_name: str) -> str:
    templates = {
        "amazon.in":          f"https://www.amazon.in/s?k={requests.utils.quote(product_name)}",
        "amazon.com":         f"https://www.amazon.com/s?k={requests.utils.quote(product_name)}",
        "flipkart.com":       f"https://www.flipkart.com/search?q={requests.utils.quote(product_name)}",
        "ebay.com":           f"https://www.ebay.com/sch/i.html?_nkw={requests.utils.quote(product_name)}",
        "bestbuy.com":        f"https://www.bestbuy.com/site/searchpage.jsp?st={requests.utils.quote(product_name)}",
        "walmart.com":        f"https://www.walmart.com/search?q={requests.utils.quote(product_name)}",
        "newegg.com":         f"https://www.newegg.com/p/pl?d={requests.utils.quote(product_name)}",
        "croma.com":          f"https://www.croma.com/searchB?q={requests.utils.quote(product_name)}",
        "reliancedigital.in": f"https://www.reliancedigital.in/search?q={requests.utils.quote(product_name)}",
    }
    return templates.get(domain, f"https://www.{domain}/search?q={requests.utils.quote(product_name)}")


def _airtop_marketplace_price(product_name: str, marketplace: str, domain: str) -> Optional[list[dict]]:
    if not settings.airtop_api_key:
        return None

    session_id = None
    try:
        session_id = _airtop_create_session()
        if not session_id:
            return None

        url = _marketplace_url(domain, product_name)
        window_id = _airtop_create_window(session_id, url)
        if not window_id:
            return None

        prompt = (
            f"This is a {marketplace} search results page for '{product_name}'. "
            f"Find the first product that best matches '{product_name}'. "
            "Extract its title, product page URL, and body in this exact format: "
            "'Price: <price with currency> | Availability: <In Stock or Out of Stock>'. "
            "Use the error field if no matching product is visible."
        )
        data = _airtop_page_query(session_id, window_id, prompt, _PRICE_RESULT_SCHEMA)

        if data.get("error"):
            logger.info("Airtop price: not found on %s — %s", marketplace, data["error"])
            return None

        results = data.get("results", [])
        if results:
            logger.info("Airtop price '%s' on %s → %s", product_name, marketplace, results[0].get("body", ""))
            return results[:1]
        return None

    except Exception as exc:
        logger.warning("Airtop price failed [%s] '%s': %s", marketplace, product_name, exc)
        return None
    finally:
        if session_id:
            _airtop_terminate(session_id)


# ──────────────────────────────────────────────
# Google Shopping — single-session price aggregation
# ──────────────────────────────────────────────

# JSON schema for Shopping page extraction
_SHOPPING_RESULT_SCHEMA = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "type": "object",
    "properties": {
        "results": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "title":        {"type": "string", "description": "Product name as shown"},
                    "url":          {"type": "string", "description": "Link to the seller's product page"},
                    "body":         {"type": "string", "description": "Seller name, price with currency, and stock status. Format: 'Seller: <name> | Price: <price> | Availability: <In Stock|Out of Stock>'"},
                },
                "required": ["title", "url", "body"],
                "additionalProperties": False,
            },
        },
        "error": {"type": "string", "description": "Error message if no results found", "minLength": 1},
    },
}


def _airtop_google_shopping(product_name: str, locale: str = "in") -> Optional[list[dict]]:
    """
    Scrape one Google Shopping page that already aggregates multiple sellers.
    locale='in' → google.co.in (Amazon.in, Flipkart, Croma, etc.)
    locale='com' → google.com (Amazon.com, Best Buy, etc.)
    """
    if not settings.airtop_api_key:
        return None

    session_id = None
    domain = "google.co.in" if locale == "in" else "google.com"
    url = f"https://www.{domain}/search?tbm=shop&q={requests.utils.quote(product_name)}&hl=en"
    if locale == "in":
        url += "&gl=in"

    try:
        session_id = _airtop_create_session()
        if not session_id:
            return None

        window_id = _airtop_create_window(session_id, url)
        if not window_id:
            return None

        prompt = (
            f"This is a Google Shopping page for '{product_name}'. "
            "Extract up to 8 product listings. For each, capture the seller name "
            "(e.g. Amazon, Flipkart, Croma), the price with currency symbol, "
            "and whether it is in stock. "
            "Format the body field exactly as: "
            "'Seller: <name> | Price: <price> | Availability: <In Stock or Out of Stock>'. "
            "Skip duplicate sellers — keep the cheapest listing per seller. "
            "Use the error field only if the page shows no products at all."
        )
        data = _airtop_page_query(session_id, window_id, prompt, _SHOPPING_RESULT_SCHEMA)

        if data.get("error"):
            logger.info("Airtop Shopping (%s): no results — %s", domain, data["error"])
            return None

        results = data.get("results", [])
        logger.info(
            "Airtop Shopping (%s) '%s' → %d seller listings",
            domain, product_name, len(results),
        )
        return results if results else None

    except Exception as exc:
        logger.warning("Airtop Shopping failed (%s) '%s': %s", domain, product_name, exc)
        return None
    finally:
        if session_id:
            _airtop_terminate(session_id)


def google_shopping_search(product_name: str) -> list[dict]:
    """
    Public interface for marketplace price aggregation.
    Strategy: google.co.in (India) → google.com (global) → DDG fallback.
    Returns a list of search-result dicts [{title, url, body}, ...].
    """
    # 1. Try India Shopping page
    results = _airtop_google_shopping(product_name, locale="in")
    if results:
        return results

    # 2. Fall back to global Shopping page
    logger.info("Shopping .co.in failed — trying google.com for '%s'", product_name)
    results = _airtop_google_shopping(product_name, locale="com")
    if results:
        return results

    # 3. DDG text search as last resort
    logger.info("Airtop Shopping unavailable — DDG fallback for '%s'", product_name)
    ddg_query = f"{product_name} buy price Amazon Flipkart Croma site:google.com/shopping OR amazon.in OR flipkart.com"
    return _ddg_search(f"{product_name} price buy online India", max_results=6)


# ──────────────────────────────────────────────
# DuckDuckGo fallback
# ──────────────────────────────────────────────

def _ddg_search(query: str, max_results: int) -> list[dict]:
    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=max_results))
        logger.info("DDG '%s' → %d results", query, len(results))
        return [
            {"title": r.get("title", ""), "url": r.get("href", ""), "body": r.get("body", "")}
            for r in results
        ]
    except Exception as exc:
        logger.warning("DDG failed '%s': %s", query, exc)
        return []


# ──────────────────────────────────────────────
# Public interface — signatures unchanged
# ──────────────────────────────────────────────

def web_search(query: str, max_results: int = MAX_WEB_RESULTS) -> list[dict]:
    """Search the web. Airtop primary, DuckDuckGo fallback."""
    results = _airtop_search(query, max_results)
    if results:
        return results
    logger.info("DDG fallback for: '%s'", query)
    return _ddg_search(query, max_results)


def product_review_search(product_name: str) -> list[dict]:
    query = f"{product_name} review reliability problems 2025"
    return web_search(query)


def marketplace_price_search(product_name: str, marketplace: str) -> list[dict]:
    """
    Legacy per-marketplace price lookup (kept for backwards compat).
    Agents should prefer google_shopping_search() for efficiency.
    Price lookup via Airtop real browser, DDG snippets as fallback.
    """
    domain = _marketplace_domain(marketplace)
    results = _airtop_marketplace_price(product_name, marketplace, domain)
    if results:
        return results
    logger.info("DDG price fallback for '%s' on %s", product_name, marketplace)
    return _ddg_search(f"{product_name} buy price site:{domain}", max_results=2)


def _marketplace_domain(marketplace: str) -> str:
    domains = {
        "amazon":           "amazon.in",        # India-first (users in Mumbai)
        "flipkart":         "flipkart.com",
        "ebay":             "ebay.com",
        "best buy":         "bestbuy.com",
        "walmart":          "walmart.com",
        "newegg":           "newegg.com",
        "croma":            "croma.com",
        "reliance digital": "reliancedigital.in",
    }
    return domains.get(marketplace.lower(), f"{marketplace.lower().replace(' ', '')}.com")