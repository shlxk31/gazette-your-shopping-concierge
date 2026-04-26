from enum import Enum


# ──────────────────────────────────────────────
# Question enums
# ──────────────────────────────────────────────

class QuestionCategory(str, Enum):
    BUDGET = "budget"
    USAGE = "usage"
    PREFERENCE = "preference"
    TECHNICAL = "technical"
    BRAND = "brand"
    OTHER = "other"


class InputType(str, Enum):
    RADIO = "radio"
    CHECKBOX = "checkbox"
    RANGE_SLIDER = "range_slider"
    DROPDOWN = "dropdown"
    TEXT_INPUT = "text_input"


class QuestionMode(str, Enum):
    BASIC = "basic"
    ADVANCED = "advanced"


# ──────────────────────────────────────────────
# Session enums
# ──────────────────────────────────────────────

class SessionStatus(str, Enum):
    QUESTIONING = "questioning"       # Still gathering user preferences
    READY = "ready"                   # All questions answered, ready for product search
    SEARCHING = "searching"           # Product discovery in progress
    COMPLETE = "complete"             # Products found and ready


# ──────────────────────────────────────────────
# Product / Review enums
# ──────────────────────────────────────────────

class ReviewSentiment(str, Enum):
    POSITIVE = "positive"
    NEUTRAL = "neutral"
    NEGATIVE = "negative"


class Availability(str, Enum):
    IN_STOCK = "in_stock"
    OUT_OF_STOCK = "out_of_stock"
    LIMITED = "limited"


# ──────────────────────────────────────────────
# Error codes
# ──────────────────────────────────────────────

class ErrorCode(str, Enum):
    SESSION_NOT_FOUND = "SESSION_NOT_FOUND"
    SESSION_EXPIRED = "SESSION_EXPIRED"
    SESSION_NOT_READY = "SESSION_NOT_READY"
    INVALID_ANSWERS = "INVALID_ANSWERS"
    LLM_ERROR = "LLM_ERROR"
    SEARCH_ERROR = "SEARCH_ERROR"
    PRODUCT_NOT_FOUND = "PRODUCT_NOT_FOUND"
    VALIDATION_ERROR = "VALIDATION_ERROR"
    INTERNAL_ERROR = "INTERNAL_ERROR"


# ──────────────────────────────────────────────
# API versioning
# ──────────────────────────────────────────────

API_V1_PREFIX = "/api/v1"
API_VERSION = "1.0.0"


# ──────────────────────────────────────────────
# LLM prompting constants
# ──────────────────────────────────────────────

MAX_QUESTIONS_TOTAL = 12          # Hard cap on questions generated per session
BASIC_QUESTIONS_COUNT = 4         # How many questions to show in basic mode per batch
ADVANCED_QUESTIONS_COUNT = 8      # How many questions in advanced mode per batch
MAX_PRODUCTS_RETURNED = 10        # Max products in discovery result
MAX_REDDIT_POSTS = 5              # Reddit posts fetched per product query
MAX_WEB_RESULTS = 5               # Web results fetched per product query

# Redirect paths sent to frontend after session is complete
REDIRECT_PRODUCTS = "/products"
