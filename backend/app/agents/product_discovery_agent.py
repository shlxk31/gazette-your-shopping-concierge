"""
Product Discovery Agent.

Responsibilities:
  1. Build targeted search queries from user preferences.
  2. Fan out to web search and Reddit concurrently.
  3. Synthesise raw results into ranked, structured product recommendations via Groq.
  4. Persist discovered products on the session.
"""

import logging
import asyncio
from concurrent.futures import ThreadPoolExecutor, as_completed
from app.services.web_search import web_search, product_review_search, product_image_search
from typing import Optional

from app.core import session_store
from app.core.constants import SessionStatus, MAX_WEB_RESULTS, MAX_REDDIT_POSTS
from app.models.session import Session
from app.services.groq_client import complete_json
from app.services.reddit_search import search_reddit
from app.utils.prompt_builder import (
    build_discovery_query_prompt,
    build_product_synthesis_prompt,
)
from app.utils.response_helpers import format_search_results

logger = logging.getLogger(__name__)


class ProductDiscoveryAgent:
    """
    Discovers products matching user preferences using multi-source search
    and LLM-driven synthesis.
    """

    def discover(self, session: Session) -> list[dict]:
        """
        Main entry point.
        Returns a list of product dicts conforming to the Product schema.
        Also caches results on the session.
        """
        if session.products:
            logger.info("Session %s: returning cached products.", session.session_id)
            return session.products

        session.status = SessionStatus.SEARCHING
        session_store.update_session(session)

        preferences = session.summarise_preferences()
        logger.info("Session %s: starting product discovery.", session.session_id)

        # ── Step 1: Generate search queries via LLM ──
        queries = self._generate_queries(preferences)
        web_queries: list[str] = queries.get("web_queries", [preferences])
        reddit_query: str = queries.get("reddit_query", preferences)
        logger.debug("Discovery queries — web: %s | reddit: %s", web_queries, reddit_query)

        # ── Step 2: Fan-out searches in parallel ──
        web_results, reddit_results = self._parallel_search(
            web_queries, reddit_query, session.detected_category
        )

        # ── Step 3: Synthesise results via LLM ──
        products = self._synthesise_products(preferences, web_results, reddit_results)

        # ── Step 4: Persist and return ──
        session.products = products
        session.status = SessionStatus.COMPLETE
        session_store.update_session(session)
        logger.info(
            "Session %s: discovery complete — %d products found.",
            session.session_id,
            len(products),
        )
        return products

    # ──────────────────────────────────────────────
    # Step 1: Generate search queries
    # ──────────────────────────────────────────────

    def _generate_queries(self, preferences: str) -> dict:
        system_prompt, user_prompt = build_discovery_query_prompt(preferences)
        try:
            return complete_json(system_prompt, user_prompt)
        except ValueError as exc:
            logger.warning("Query generation failed: %s — using raw preference as fallback.", exc)
            return {
                "web_queries": [preferences],
                "reddit_query": preferences,
                "target_products": [],
            }

    # ──────────────────────────────────────────────
    # Step 2: Parallel web + Reddit search
    # ──────────────────────────────────────────────

    def _parallel_search(
        self,
        web_queries: list[str],
        reddit_query: str,
        category: str,
    ) -> tuple[list[dict], list[dict]]:
        """
        Runs web searches and Reddit search concurrently using a thread pool.
        Returns (web_results, reddit_results).
        """
        all_web: list[dict] = []
        all_reddit: list[dict] = []

        tasks = {}
        with ThreadPoolExecutor(max_workers=6) as pool:
            # Submit web search tasks
            for q in web_queries[:3]:   # cap at 3 web queries
                fut = pool.submit(web_search, q, MAX_WEB_RESULTS)
                tasks[fut] = ("web", q)

            # Submit Reddit task
            reddit_fut = pool.submit(search_reddit, reddit_query, category, MAX_REDDIT_POSTS)
            tasks[reddit_fut] = ("reddit", reddit_query)

            for future in as_completed(tasks):
                source, query = tasks[future]
                try:
                    result = future.result()
                    if source == "web":
                        all_web.extend(result)
                    else:
                        all_reddit.extend(result)
                except Exception as exc:
                    logger.warning("Search task failed [%s] '%s': %s", source, query, exc)

        # Deduplicate web results by URL
        seen_urls: set[str] = set()
        unique_web = []
        for r in all_web:
            if r["url"] not in seen_urls:
                seen_urls.add(r["url"])
                unique_web.append(r)

        return unique_web, all_reddit

    # ──────────────────────────────────────────────
    # Step 3: Synthesise into product recommendations
    # ──────────────────────────────────────────────

    def _synthesise_products(
        self,
        preferences: str,
        web_results: list[dict],
        reddit_results: list[dict],
    ) -> list[dict]:
        web_text = format_search_results(web_results)
        reddit_text = format_search_results(reddit_results)

        system_prompt, user_prompt = build_product_synthesis_prompt(
            preferences, web_text, reddit_text
        )
        try:
            products = complete_json(system_prompt, user_prompt)
            if not isinstance(products, list):
                logger.warning("LLM synthesis returned non-list; wrapping.")
                products = [products] if isinstance(products, dict) else []
        except ValueError as exc:
            logger.error("Product synthesis failed: %s", exc)
            products = []

        for p in products:
            if not p.get("image"):
                p["image"] = product_image_search(p.get("name", "")) or ""

        return products
