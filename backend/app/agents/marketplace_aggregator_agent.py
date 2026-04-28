"""
Marketplace Aggregator Agent.

Responsibilities:
  1. Take a product name and fetch prices via a single Google Shopping page.
     (Google Shopping already aggregates Amazon, Flipkart, Croma, etc. in one request,
     replacing the previous 8-session fan-out approach.)
  2. Use Groq to extract and normalise pricing data from the Shopping results.
  3. Identify the best (lowest in-stock) price.
  4. Cache results on the session's price_cache to avoid repeat lookups.
"""

import logging

from app.core import session_store
from app.models.session import Session
from app.services.groq_client import complete_json
from app.services.web_search import google_shopping_search
from app.utils.prompt_builder import build_price_synthesis_prompt
from app.utils.response_helpers import format_search_results

logger = logging.getLogger(__name__)


class MarketplaceAggregatorAgent:
    """
    Aggregates pricing across marketplaces for a given product using a single
    Google Shopping scrape instead of per-marketplace Airtop sessions.
    """

    def get_prices(self, session: Session, product_id: str) -> list[dict]:
        """
        Returns a list of MarketplacePrice dicts for the given product_id.
        Uses session.price_cache to avoid redundant fetches.
        """
        if product_id in session.price_cache:
            logger.info(
                "Session %s: returning cached prices for product %s.",
                session.session_id,
                product_id,
            )
            return session.price_cache[product_id]

        product_name = self._resolve_product_name(session, product_id)
        if not product_name:
            logger.warning(
                "Session %s: product_id '%s' not found in session products.",
                session.session_id,
                product_id,
            )
            return []

        logger.info(
            "Session %s: fetching Shopping prices for '%s'.",
            session.session_id,
            product_name,
        )

        # ── Step 1: Single Google Shopping scrape (india-first, global fallback) ──
        shopping_results = google_shopping_search(product_name)

        # ── Step 2: Synthesise into structured prices via LLM ──
        prices = self._synthesise_prices(product_name, shopping_results)

        # ── Step 3: Cache and return ──
        session.price_cache[product_id] = prices
        session_store.update_session(session)
        return prices

    # ──────────────────────────────────────────────
    # LLM price synthesis
    # ──────────────────────────────────────────────

    def _synthesise_prices(
        self, product_name: str, search_results: list[dict]
    ) -> list[dict]:
        if not search_results:
            logger.warning("No Shopping results for '%s' — returning empty prices.", product_name)
            return []

        results_text = format_search_results(search_results)
        system_prompt, user_prompt = build_price_synthesis_prompt(product_name, results_text)

        try:
            prices = complete_json(system_prompt, user_prompt)
            if not isinstance(prices, list):
                logger.warning("Price synthesis returned non-list; falling back to empty.")
                return []
        except ValueError as exc:
            logger.error("Price synthesis LLM call failed: %s", exc)
            return []

        return self._mark_best_price(prices)

    # ──────────────────────────────────────────────
    # Helpers
    # ──────────────────────────────────────────────

    def _resolve_product_name(self, session: Session, product_id: str) -> str:
        for product in session.products:
            if product.get("id") == product_id:
                return product.get("name", "")
        return ""

    def _mark_best_price(self, prices: list[dict]) -> list[dict]:
        """
        Ensure exactly one entry has is_best=True — the lowest in-stock/limited price.
        Overrides whatever the LLM set to guarantee correctness.
        """
        for p in prices:
            p["is_best"] = False

        eligible = [
            p for p in prices
            if p.get("price", 0) > 0
            and p.get("availability") in ("in_stock", "limited")
        ]
        if eligible:
            best = min(eligible, key=lambda p: p["price"])
            best["is_best"] = True

        return prices