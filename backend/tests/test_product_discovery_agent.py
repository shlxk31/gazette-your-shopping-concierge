"""
Tests for ProductDiscoveryAgent.
All external I/O (Groq, web search, Reddit) is mocked.
"""

import pytest
from unittest.mock import patch, MagicMock

from app.agents.product_discovery_agent import ProductDiscoveryAgent
from app.core.constants import SessionStatus
from app.models.session import Session, AnsweredQuestion


MOCK_QUERY_PLAN = {
    "web_queries": ["best laptop for machine learning 2024", "top ML laptops review"],
    "reddit_query": "best laptop machine learning recommendations",
    "target_products": ["MacBook Pro M3", "Dell XPS 15", "Lenovo ThinkPad X1 Carbon"],
}

MOCK_PRODUCTS = [
    {
        "id": "macbook-pro-m3",
        "name": "Apple MacBook Pro M3",
        "image": "",
        "description": "A powerhouse laptop for ML workloads.",
        "features": ["M3 chip", "16GB unified memory", "MagSafe charging"],
        "match_score": 0.92,
        "match_reasons": ["Excellent ML performance", "Long battery life"],
        "missing_features": ["No dedicated GPU"],
        "review_summary": {
            "rating": 4.7,
            "sentiment": "positive",
            "highlights": ["Blazing fast", "Great display"],
            "concerns": ["Expensive", "Limited ports"],
        },
        "reliability": {"score": 0.9, "summary": "Highly reliable with few reported issues."},
        "warranty": {"duration": "1 year", "type": "Limited manufacturer warranty"},
    }
]

MOCK_WEB_RESULTS = [
    {"title": "Best ML Laptops 2024", "url": "https://example.com/ml-laptops", "body": "MacBook Pro M3 leads..."},
]

MOCK_REDDIT_RESULTS = [
    {"title": "Best laptop for ML?", "url": "https://reddit.com/r/laptops/1", "score": 120, "body": "Get the MacBook Pro M3", "subreddit": "laptops"},
]


@pytest.fixture
def agent():
    return ProductDiscoveryAgent()


@pytest.fixture
def ready_session():
    session = Session(
        session_id="sess-discover-1",
        raw_query="ML laptop",
        detected_category="laptop",
        status=SessionStatus.READY,
    )
    session.answers = [
        AnsweredQuestion("q_budget", "What is your budget?", 2000),
        AnsweredQuestion("q_usage", "What will you use it for?", ["ml"]),
    ]
    return session


@patch("app.agents.product_discovery_agent.session_store.update_session")
@patch("app.agents.product_discovery_agent.complete_json")
@patch("app.agents.product_discovery_agent.web_search", return_value=MOCK_WEB_RESULTS)
@patch("app.agents.product_discovery_agent.search_reddit", return_value=MOCK_REDDIT_RESULTS)
def test_discover_returns_products(mock_reddit, mock_web, mock_llm, mock_update, agent, ready_session):
    mock_llm.side_effect = [MOCK_QUERY_PLAN, MOCK_PRODUCTS]

    products = agent.discover(ready_session)

    assert len(products) == 1
    assert products[0]["id"] == "macbook-pro-m3"
    assert ready_session.status == SessionStatus.COMPLETE


@patch("app.agents.product_discovery_agent.session_store.update_session")
@patch("app.agents.product_discovery_agent.complete_json")
@patch("app.agents.product_discovery_agent.web_search", return_value=MOCK_WEB_RESULTS)
@patch("app.agents.product_discovery_agent.search_reddit", return_value=MOCK_REDDIT_RESULTS)
def test_discover_uses_cache_on_second_call(mock_reddit, mock_web, mock_llm, mock_update, agent, ready_session):
    mock_llm.side_effect = [MOCK_QUERY_PLAN, MOCK_PRODUCTS]

    # First call — actually runs discovery
    agent.discover(ready_session)
    first_llm_call_count = mock_llm.call_count

    # Second call — should hit cache, no new LLM calls
    agent.discover(ready_session)
    assert mock_llm.call_count == first_llm_call_count


@patch("app.agents.product_discovery_agent.session_store.update_session")
@patch("app.agents.product_discovery_agent.complete_json")
@patch("app.agents.product_discovery_agent.web_search", return_value=[])
@patch("app.agents.product_discovery_agent.search_reddit", return_value=[])
def test_discover_handles_empty_search_results(mock_reddit, mock_web, mock_llm, mock_update, agent, ready_session):
    mock_llm.side_effect = [MOCK_QUERY_PLAN, []]

    products = agent.discover(ready_session)
    assert products == []
    assert ready_session.status == SessionStatus.COMPLETE


@patch("app.agents.product_discovery_agent.session_store.update_session")
@patch("app.agents.product_discovery_agent.complete_json")
@patch("app.agents.product_discovery_agent.web_search", return_value=MOCK_WEB_RESULTS)
@patch("app.agents.product_discovery_agent.search_reddit", return_value=MOCK_REDDIT_RESULTS)
def test_discover_gracefully_handles_llm_failure(mock_reddit, mock_web, mock_llm, mock_update, agent, ready_session):
    # Query plan succeeds but synthesis fails
    mock_llm.side_effect = [MOCK_QUERY_PLAN, ValueError("LLM timeout")]

    products = agent.discover(ready_session)
    assert products == []
