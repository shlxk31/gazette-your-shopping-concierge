"""
Agent registry.
Instantiate agents once at startup and expose them via this module.
All endpoints import agents from here — never instantiate agents in endpoint files.
"""

from app.agents.query_refinement_agent import QueryRefinementAgent
from app.agents.product_discovery_agent import ProductDiscoveryAgent
from app.agents.marketplace_aggregator_agent import MarketplaceAggregatorAgent

query_refinement_agent = QueryRefinementAgent()
product_discovery_agent = ProductDiscoveryAgent()
marketplace_aggregator_agent = MarketplaceAggregatorAgent()
