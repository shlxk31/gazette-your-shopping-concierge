"""
Reddit search service using PRAW.
Pulls top posts and comments from relevant subreddits for product opinions.

If credentials are not configured, falls back to DuckDuckGo site:reddit.com search
so the rest of the application still works without Reddit API keys.
"""

import logging
from typing import Optional

import praw
from praw.exceptions import PRAWException

from app.core.config import get_settings
from app.core.constants import MAX_REDDIT_POSTS
from app.services.web_search import web_search

logger = logging.getLogger(__name__)
settings = get_settings()


# Subreddits to search by detected product category
CATEGORY_SUBREDDITS: dict[str, list[str]] = {
    "laptop": ["laptops", "SuggestALaptop", "hardware", "techsupport"],
    "phone": ["Android", "iphone", "smartphones", "gadgets"],
    "headphones": ["headphones", "audiophile", "budgetaudiophile"],
    "keyboard": ["MechanicalKeyboards", "keyboards", "hardware"],
    "monitor": ["Monitors", "hardware", "buildapc"],
    "gpu": ["hardware", "buildapc", "nvidia", "Amd"],
    "cpu": ["hardware", "buildapc", "intel", "Amd"],
    "camera": ["photography", "Cameras", "canon", "nikon", "SonyAlpha"],
    "tv": ["4kTV", "hometheater", "Televisions"],
    "default": ["gadgets", "hardware", "BuyItForLife", "techsupport"],
}


def _get_reddit_client() -> Optional[praw.Reddit]:
    if not settings.reddit_client_id or not settings.reddit_client_secret:
        return None
    try:
        return praw.Reddit(
            client_id=settings.reddit_client_id,
            client_secret=settings.reddit_client_secret,
            user_agent=settings.reddit_user_agent,
            read_only=True,
        )
    except Exception as exc:
        logger.warning("Reddit client init failed: %s", exc)
        return None


def search_reddit(
    query: str,
    category: str = "default",
    max_results: int = MAX_REDDIT_POSTS,
) -> list[dict]:
    """
    Search Reddit for product opinions.

    Returns a list of dicts with:
      - title: str
      - url: str
      - score: int
      - body: str   (selftext or top comments joined)
      - subreddit: str
    """
    reddit = _get_reddit_client()

    if reddit is None:
        return _fallback_reddit_search(query, max_results)

    subreddits = CATEGORY_SUBREDDITS.get(category.lower(), CATEGORY_SUBREDDITS["default"])
    subreddit_str = "+".join(subreddits)

    try:
        results = []
        subreddit = reddit.subreddit(subreddit_str)
        for submission in subreddit.search(query, sort="relevance", limit=max_results):
            # Grab the top-level comments for context
            submission.comments.replace_more(limit=0)
            top_comments = [
                c.body for c in submission.comments.list()[:3] if hasattr(c, "body")
            ]
            results.append({
                "title": submission.title,
                "url": f"https://reddit.com{submission.permalink}",
                "score": submission.score,
                "body": (submission.selftext or "") + "\n" + "\n".join(top_comments),
                "subreddit": submission.subreddit.display_name,
            })
        logger.info("Reddit search '%s' → %d results", query, len(results))
        return results
    except PRAWException as exc:
        logger.warning("PRAW search failed: %s — falling back to DDG", exc)
        return _fallback_reddit_search(query, max_results)


def _fallback_reddit_search(query: str, max_results: int) -> list[dict]:
    """DuckDuckGo site:reddit.com fallback when PRAW is unavailable."""
    ddg_results = web_search(f"site:reddit.com {query}", max_results=max_results)
    return [
        {
            "title": r["title"],
            "url": r["url"],
            "score": 0,
            "body": r["body"],
            "subreddit": "unknown",
        }
        for r in ddg_results
    ]
