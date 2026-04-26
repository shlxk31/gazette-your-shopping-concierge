"""
Marketplace Aggregator Agent.

Responsibilities:
  1. Take a product name and search for it across known marketplaces.
  2. Use Groq to extract and normalise pricing data from search snippets.
  3. Identify the best (lowest in-stock) price.
  4. Cache results on the session's price_cache to avoid repeat lookups.
"""

import logging
from concurrent.futures import ThreadPoolExecutor, as_completed

from app.core import session_store
from app.models.session import Session
from app.services.groq_client import complete_json
from app.services.web_search import web_search
from app.utils.prompt_builder import build_price_synthesis_prompt
from app.utils.response_helpers import format_search_results

logger = logging.getLogger(__name__)

# Marketplaces to query — extend as needed
MARKETPLACES = [
    "Amazon",
    "Flipkart",
    "eBay",
    "Best Buy",
    "Walmart",
    "Croma",
    "Reliance Digital",
    "Newegg",
]

# Number of web results per marketplace query
RESULTS_PER_MARKETPLACE = 2


class MarketplaceAggregatorAgent:
    """
    Aggregates pricing across multiple marketplaces for a given product.
    """

    def get_prices(self, session: Session, product_id: str) -> list[dict]:
        """
        Returns a list of MarketplacePrice dicts for the given product_id.
        Uses session.price_cache to avoid redundant searches.
        """
        if product_id in session.price_cache:
            logger.info(
                "Session %s: returning cached prices for product %s.",
                session.session_id,
                product_id,
            )
            return session.price_cache[product_id]

        # Resolve product name from session products
        product_name = self._resolve_product_name(session, product_id)
        if not product_name:
            logger.warning(
                "Session %s: product_id '%s' not found in session products.",
                session.session_id,
                product_id,
            )
            return []

        logger.info(
            "Session %s: fetching prices for '%s' across %d marketplaces.",
            session.session_id,
            product_name,
            len(MARKETPLACES),
        )

        # ── Step 1: Fan-out marketplace searches in parallel ──
        all_results = self._parallel_marketplace_search(product_name)

        # ── Step 2: Synthesise into structured prices via LLM ──
        prices = self._synthesise_prices(product_name, all_results)

        # ── Step 3: Cache and return ──
        session.price_cache[product_id] = prices
        session_store.update_session(session)
        return prices

    # ──────────────────────────────────────────────
    # Parallel search across all marketplaces
    # ──────────────────────────────────────────────

    def _parallel_marketplace_search(self, product_name: str) -> list[dict]:
        """
        Runs one web search query per marketplace concurrently.
        Returns the combined, deduplicated list of search result dicts.
        """
        all_results: list[dict] = []

        def search_marketplace(marketplace: str) -> list[dict]:
            query = f'"{product_name}" buy price {marketplace}'
            return web_search(query, max_results=RESULTS_PER_MARKETPLACE)

        with ThreadPoolExecutor(max_workers=len(MARKETPLACES)) as pool:
            futures = {
                pool.submit(search_marketplace, mp): mp for mp in MARKETPLACES
            }
            for future in as_completed(futures):
                marketplace = futures[future]
                try:
                    results = future.result()
                    all_results.extend(results)
                except Exception as exc:
                    logger.warning(
                        "Marketplace search failed for '%s': %s", marketplace, exc
                    )

        # Deduplicate by URL
        seen: set[str] = set()
        unique = []
        for r in all_results:
            if r["url"] not in seen:
                seen.add(r["url"])
                unique.append(r)

        return unique

    # ──────────────────────────────────────────────
    # LLM price synthesis
    # ──────────────────────────────────────────────

    def _synthesise_prices(
        self, product_name: str, search_results: list[dict]
    ) -> list[dict]:
        if not search_results:
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

        # Safety: ensure is_best is set on exactly one entry
        prices = self._mark_best_price(prices)
        return prices

    # ──────────────────────────────────────────────
    # Helpers
    # ──────────────────────────────────────────────

    def _resolve_product_name(self, session: Session, product_id: str) -> str:
        """Find the product name from the session's discovered products list."""
        for product in session.products:
            if product.get("id") == product_id:
                return product.get("name", "")
        return ""

    def _mark_best_price(self, prices: list[dict]) -> list[dict]:
        """
        Ensure exactly one entry has is_best=True — the lowest in-stock/limited price.
        Override whatever the LLM set to guarantee correctness.
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
