# Agentic E-Commerce Backend

A multi-agent FastAPI backend that turns a vague user product query into curated,
reviewed, and price-compared product recommendations — no LangChain, no LangGraph,
just clean Python orchestration.

---

## Architecture

```
app/
├── agents/
│   ├── __init__.py                      # Agent registry (single instances)
│   ├── query_refinement_agent.py        # Intent parsing + question generation
│   ├── product_discovery_agent.py       # Web/Reddit search + LLM synthesis
│   └── marketplace_aggregator_agent.py  # Price comparison across marketplaces
│
├── api/v1/endpoints/
│   ├── query.py        # POST /api/v1/query
│   ├── questions.py    # POST /api/v1/questions/answer
│   ├── products.py     # GET  /api/v1/products
│   ├── prices.py       # GET  /api/v1/products/:id/prices
│   └── chat.py         # POST /api/v1/chat
│
├── core/
│   ├── config.py        # Pydantic-settings (env vars)
│   ├── constants.py     # All enums and magic numbers
│   └── session_store.py # Thread-safe in-memory session store (TTL-evicting)
│
├── models/
│   └── session.py       # Internal session dataclass (full lifecycle state)
│
├── schemas/
│   ├── common.py        # Question, ErrorObject, MetaObject, BaseResponse
│   └── query.py / questions.py / products.py / prices.py / chat.py
│
├── services/
│   ├── groq_client.py   # Groq SDK wrapper with retry + JSON extraction
│   ├── web_search.py    # DuckDuckGo search (no API key required)
│   └── reddit_search.py # PRAW + DDG fallback
│
├── utils/
│   ├── prompt_builder.py   # All LLM prompt templates
│   └── response_helpers.py # Meta/error factories, search result formatter
│
└── main.py  # FastAPI app factory, CORS, lifespan
```

### Agent Flow

```
User query
    │
    ▼
[Query Refinement Agent]
    ├── Calls Groq to detect product category
    ├── Generates structured questions (basic + advanced modes)
    ├── Serves questions in priority-ordered batches
    └── Handles free-form chat context
    │
    ▼  (all required questions answered)
[Product Discovery Agent]
    ├── Calls Groq to build web + Reddit search queries
    ├── Fans out parallel searches (ThreadPoolExecutor)
    │     ├── DuckDuckGo web search (3 queries x 5 results)
    │     └── Reddit via PRAW (or DDG fallback)
    └── Calls Groq to synthesise raw results -> ranked Product list
    │
    ▼  (user selects a product)
[Marketplace Aggregator Agent]
    ├── Fans out parallel marketplace searches (8 marketplaces)
    ├── Calls Groq to extract structured price data from snippets
    └── Marks the best (lowest in-stock) price
```

---

## Setup

### 1. Clone and configure

```bash
git clone <repo>
cd ecommerce-agent
cp .env.example .env
```

Edit `.env`:

```
GROQ_API_KEY=gsk_...           # Required
GROQ_MODEL=llama3-70b-8192     # Or any Groq-hosted model

REDDIT_CLIENT_ID=...           # Optional — falls back to DuckDuckGo if omitted
REDDIT_CLIENT_SECRET=...
REDDIT_USER_AGENT=ecommerce-agent/1.0
```

### 2. Run with Docker (recommended)

```bash
docker compose up --build
```

API available at `http://localhost:8000`
Interactive docs at `http://localhost:8000/docs`

### 3. Run locally (without Docker)

```bash
python -m venv .venv
source .venv/bin/activate       # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

---

## API Reference

### `POST /api/v1/query`
Start a session. Returns structured questions.

```json
// Request
{ "query": "I need a powerful laptop for machine learning" }

// Response
{
  "success": true,
  "data": {
    "session_id": "uuid",
    "detected_category": "laptop",
    "initial_questions": [...],
    "mode": "basic"
  }
}
```

### `POST /api/v1/questions/answer`
Submit answers. Returns next batch or `is_complete: true`.

```json
{
  "session_id": "uuid",
  "answers": [
    { "question_id": "q_budget", "value": 1500 },
    { "question_id": "q_usage", "value": ["ml", "data_science"] }
  ]
}
```

### `GET /api/v1/products?session_id=uuid`
Triggers product discovery. Returns ranked products with review summaries.

### `GET /api/v1/products/{product_id}/prices?session_id=uuid`
Price comparison across Amazon, Flipkart, eBay, Best Buy, Walmart, Croma, Reliance Digital, Newegg.

### `POST /api/v1/chat`
Free-form chat to refine preferences alongside structured questions.

```json
{ "session_id": "uuid", "message": "I also need good battery life" }
```

---

## Question Modes

| Mode       | Covers                                  |
|------------|-----------------------------------------|
| `basic`    | Budget, use case, OS preference         |
| `advanced` | RAM, GPU, display specs, connectivity   |

Toggle by having the frontend send a mode switch — the agent will serve
the unserved advanced questions for the session.

---

## Running Tests

```bash
pip install pytest
pytest
```

All external I/O (Groq, web search, Reddit) is mocked. No API keys required.

---

## Key Design Decisions

| Decision | Rationale |
|---|---|
| No LangChain/LangGraph | Raw Python is simpler, debuggable, and avoids framework lock-in |
| DuckDuckGo for web search | Zero-cost, no API key, sufficient for discovery |
| PRAW + DDG fallback | Reddit creds are optional; system degrades gracefully |
| ThreadPoolExecutor fan-out | Parallel I/O without async complexity |
| In-memory session store | Zero-dependency; swap dict for Redis in production |
| All prompts in prompt_builder.py | Single file to tune LLM behaviour without touching agent logic |
| Enums + constants file | No magic strings scattered across the codebase |

---

## Production Checklist

- [ ] Replace in-memory session store with Redis
- [ ] Restrict CORS origins in `main.py`
- [ ] Add rate limiting (e.g. `slowapi`)
- [ ] Add authentication (API key header or OAuth)
- [ ] Set `LOG_LEVEL=WARNING` in production `.env`
- [ ] Remove `--reload` from production Dockerfile CMD
- [ ] Add product image URL resolution (currently returns empty string)
