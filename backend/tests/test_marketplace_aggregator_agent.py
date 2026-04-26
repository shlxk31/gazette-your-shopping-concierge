"""
Tests for MarketplaceAggregatorAgent.
"""

import pytest
from unittest.mock import patch

from app.agents.marketplace_aggregator_agent import MarketplaceAggregatorAgent
from app.models.session import Session
from app.core.constants import SessionStatus

MOCK_PRODUCTS_ON_SESSION = [
    {"id": "macbook-pro-m3", "name": "Apple MacBook Pro M3"}
]

MOCK_RAW_PRICES = [
    {"marketplace": "Amazon", "price": 1999.0, "currency": "USD", "url": "https://amazon.com/mbp", "availability": "in_stock", "is_best": False},
    {"marketplace": "Best Buy", "price": 2049.0, "currency": "USD", "url": "https://bestbuy.com/mbp", "availability": "in_stock", "is_best": False},
    {"marketplace": "Walmart", "price": 0, "currency": "USD", "url": "", "availability": "out_of_stock", "is_best": False},
]

MOCK_SEARCH_RESULTS = [
    {"title": "MacBook Pro M3 on Amazon", "url": "https://amazon.com/mbp", "body": "Price: $1,999"},
]


@pytest.fixture
def agent():
    return MarketplaceAggregatorAgent()


@pytest.fixture
def session_with_products():
    session = Session(
        session_id="sess-prices-1",
        raw_query="ML laptop",
        detected_category="laptop",
        status=SessionStatus.COMPLETE,
    )
    session.products = MOCK_PRODUCTS_ON_SESSION
    return session


@patch("app.agents.marketplace_aggregator_agent.session_store.update_session")
@patch("app.agents.marketplace_aggregator_agent.complete_json", return_value=MOCK_RAW_PRICES)
@patch("app.agents.marketplace_aggregator_agent.web_search", return_value=MOCK_SEARCH_RESULTS)
def test_get_prices_returns_list(mock_web, mock_llm, mock_update, agent, session_with_products):
    prices = agent.get_prices(session_with_products, "macbook-pro-m3")

    assert isinstance(prices, list)
    assert len(prices) == 3


@patch("app.agents.marketplace_aggregator_agent.session_store.update_session")
@patch("app.agents.marketplace_aggregator_agent.complete_json", return_value=MOCK_RAW_PRICES)
@patch("app.agents.marketplace_aggregator_agent.web_search", return_value=MOCK_SEARCH_RESULTS)
def test_best_price_is_lowest_in_stock(mock_web, mock_llm, mock_update, agent, session_with_products):
    prices = agent.get_prices(session_with_products, "macbook-pro-m3")

    best = [p for p in prices if p.get("is_best")]
    assert len(best) == 1
    assert best[0]["marketplace"] == "Amazon"     # $1999 < $2049, out_of_stock excluded


@patch("app.agents.marketplace_aggregator_agent.session_store.update_session")
@patch("app.agents.marketplace_aggregator_agent.complete_json", return_value=MOCK_RAW_PRICES)
@patch("app.agents.marketplace_aggregator_agent.web_search", return_value=MOCK_SEARCH_RESULTS)
def test_get_prices_uses_cache(mock_web, mock_llm, mock_update, agent, session_with_products):
    agent.get_prices(session_with_products, "macbook-pro-m3")
    first_llm_count = mock_llm.call_count

    # Second call — should hit cache
    agent.get_prices(session_with_products, "macbook-pro-m3")
    assert mock_llm.call_count == first_llm_count


def test_get_prices_returns_empty_for_unknown_product(agent, session_with_products):
    prices = agent.get_prices(session_with_products, "nonexistent-product-id")
    assert prices == []


@patch("app.agents.marketplace_aggregator_agent.session_store.update_session")
@patch("app.agents.marketplace_aggregator_agent.complete_json", return_value=[])
@patch("app.agents.marketplace_aggregator_agent.web_search", return_value=[])
def test_get_prices_handles_no_results(mock_web, mock_llm, mock_update, agent, session_with_products):
    prices = agent.get_prices(session_with_products, "macbook-pro-m3")
    assert prices == []
