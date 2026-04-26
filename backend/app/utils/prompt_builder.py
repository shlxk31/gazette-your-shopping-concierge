"""
Prompt builder.
All LLM prompt templates live here so agents stay clean.
"""

from app.core.constants import (
    MAX_QUESTIONS_TOTAL,
    BASIC_QUESTIONS_COUNT,
    ADVANCED_QUESTIONS_COUNT,
    MAX_PRODUCTS_RETURNED,
)


# ──────────────────────────────────────────────
# Query Refinement Agent prompts
# ──────────────────────────────────────────────

QUERY_REFINEMENT_SYSTEM = """
You are an intelligent shopping assistant that helps users find the perfect product.
Your job is to analyse a user's vague product query and generate precise, relevant questions 
to understand their needs. You output ONLY valid JSON.

Rules:
1. Questions must be directly relevant to the specific product type.
2. Cover: budget, primary use case, preferences, brand, and (if advanced) technical specs.
3. Use the most appropriate input type for each question.
4. Detect the product category from the query.
5. Generate both basic and advanced questions but tag each with its mode.
6. Prioritise questions — lower priority number = shown first.
"""

QUERY_REFINEMENT_USER = """
User query: "{query}"

Generate a JSON object with exactly these fields:
{{
  "detected_category": "<single word like laptop, phone, headphones, camera, etc.>",
  "questions": [
    {{
      "id": "q_<short_snake_case_id>",
      "category": "<budget|usage|preference|technical|brand|other>",
      "question_text": "<clear question>",
      "description": "<optional helpful hint or null>",
      "input_type": "<radio|checkbox|range_slider|dropdown|text_input>",
      "options": [{{"label": "...", "value": "..."}}] or null,
      "range": {{"min": N, "max": N, "step": N, "unit": "..."}} or null,
      "default_value": null,
      "placeholder": "<placeholder text or null>",
      "is_required": true,
      "depends_on": null,
      "validation": null,
      "priority": <integer 1-{max_q}>,
      "mode": "<basic|advanced>",
      "tags": ["<relevant_tag>"]
    }}
  ]
}}

Generate {basic_count} basic questions and {advanced_count} advanced questions.
Basic questions cover budget, primary use case, and key preferences.
Advanced questions cover technical specs, connectivity, form factor, etc.
"""


def build_query_refinement_prompt(query: str) -> tuple[str, str]:
    """Returns (system_prompt, user_prompt)."""
    return (
        QUERY_REFINEMENT_SYSTEM,
        QUERY_REFINEMENT_USER.format(
            query=query,
            max_q=MAX_QUESTIONS_TOTAL,
            basic_count=BASIC_QUESTIONS_COUNT,
            advanced_count=ADVANCED_QUESTIONS_COUNT,
        ),
    )


# ──────────────────────────────────────────────
# Chat refinement prompt
# ──────────────────────────────────────────────

CHAT_REFINEMENT_SYSTEM = """
You are a helpful shopping assistant in a conversation with a user.
The user has described what they want, answered some questions, and is now adding
more context via chat. Acknowledge their input, update your understanding, and
optionally return new or revised questions to ask. Output ONLY valid JSON.
"""

CHAT_REFINEMENT_USER = """
Session context:
{preferences}

User just said: "{message}"

Respond with:
{{
  "reply": "<friendly acknowledgement and any clarifications in 1-2 sentences>",
  "new_questions": [] or a list of new Question objects if the message revealed gaps
}}

Only add new questions if the message genuinely reveals something not yet covered.
If adding questions, use the same Question schema used earlier.
"""


def build_chat_prompt(preferences: str, message: str) -> tuple[str, str]:
    return (
        CHAT_REFINEMENT_SYSTEM,
        CHAT_REFINEMENT_USER.format(preferences=preferences, message=message),
    )


# ──────────────────────────────────────────────
# Product Discovery Agent prompts
# ──────────────────────────────────────────────

DISCOVERY_QUERY_SYSTEM = """
You are a product research assistant. Given user preferences, generate precise
search queries to find matching products. Output ONLY valid JSON.
"""

DISCOVERY_QUERY_USER = """
User preferences:
{preferences}

Generate a JSON object:
{{
  "web_queries": ["<query1>", "<query2>", "<query3>"],
  "reddit_query": "<single best query for Reddit opinion search>",
  "target_products": ["<specific product name 1>", "<specific product name 2>", ...]
}}

Web queries should target product listings, comparison articles, and review sites.
Reddit query should seek real user opinions and experiences.
Target products should be 3-6 specific model names you'd expect to match these preferences.
"""


def build_discovery_query_prompt(preferences: str) -> tuple[str, str]:
    return DISCOVERY_QUERY_SYSTEM, DISCOVERY_QUERY_USER.format(preferences=preferences)


PRODUCT_SYNTHESIS_SYSTEM = """
You are an expert product analyst. Given user preferences and raw search results 
(web snippets and Reddit discussions), synthesise a ranked list of product recommendations.
Output ONLY valid JSON.
"""

PRODUCT_SYNTHESIS_USER = """
User preferences:
{preferences}

Web search results:
{web_results}

Reddit opinions:
{reddit_results}

Based on these sources, return a JSON array of up to {max_products} products:
[
  {{
    "id": "<slugified_product_name>",
    "name": "<Full Product Name>",
    "image": "",
    "description": "<2-3 sentence description>",
    "features": ["<feature1>", "<feature2>", ...],
    "match_score": <0.0-1.0 based on how well it matches preferences>,
    "match_reasons": ["<why it matches pref 1>", ...],
    "missing_features": ["<what it lacks vs preferences>"],
    "review_summary": {{
      "rating": <3.0-5.0>,
      "sentiment": "<positive|neutral|negative>",
      "highlights": ["<positive point>", ...],
      "concerns": ["<negative point>", ...]
    }},
    "reliability": {{
      "score": <0.0-1.0>,
      "summary": "<1-2 sentence reliability assessment>"
    }},
    "warranty": {{
      "duration": "<e.g. 1 year, 2 years>",
      "type": "<e.g. Limited manufacturer warranty>"
    }}
  }}
]

Sort by match_score descending. Be honest about concerns found in reviews.
"""


def build_product_synthesis_prompt(
    preferences: str,
    web_results: str,
    reddit_results: str,
) -> tuple[str, str]:
    return (
        PRODUCT_SYNTHESIS_SYSTEM,
        PRODUCT_SYNTHESIS_USER.format(
            preferences=preferences,
            web_results=web_results,
            reddit_results=reddit_results,
            max_products=MAX_PRODUCTS_RETURNED,
        ),
    )


# ──────────────────────────────────────────────
# Marketplace Aggregator Agent prompts
# ──────────────────────────────────────────────

PRICE_SYNTHESIS_SYSTEM = """
You are a price comparison assistant. Given web search results from various marketplaces,
extract and structure pricing data. Output ONLY valid JSON.
"""

PRICE_SYNTHESIS_USER = """
Product: {product_name}

Marketplace search results:
{search_results}

Extract pricing info and return a JSON array:
[
  {{
    "marketplace": "<marketplace name>",
    "price": <numeric price or 0 if not found>,
    "currency": "<USD|INR|EUR|GBP|etc>",
    "url": "<direct product URL>",
    "availability": "<in_stock|out_of_stock|limited>",
    "is_best": false
  }}
]

After building the list, set is_best to true only on the entry with the lowest price
that is in_stock or limited. If no prices are found, return an empty array [].
"""


def build_price_synthesis_prompt(
    product_name: str, search_results: str
) -> tuple[str, str]:
    return (
        PRICE_SYNTHESIS_SYSTEM,
        PRICE_SYNTHESIS_USER.format(
            product_name=product_name, search_results=search_results
        ),
    )
