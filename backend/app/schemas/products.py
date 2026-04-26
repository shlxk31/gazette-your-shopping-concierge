from typing import Optional
from pydantic import BaseModel
from app.schemas.common import BaseResponse
from app.core.constants import ReviewSentiment


class ReviewSummary(BaseModel):
    rating: float
    sentiment: ReviewSentiment
    highlights: list[str]
    concerns: list[str]


class Reliability(BaseModel):
    score: float
    summary: str


class Warranty(BaseModel):
    duration: str
    type: str


class Product(BaseModel):
    id: str
    name: str
    image: str
    description: str
    features: list[str]
    match_score: float
    match_reasons: list[str]
    missing_features: list[str]
    review_summary: ReviewSummary
    reliability: Reliability
    warranty: Warranty


class ProductsData(BaseModel):
    products: list[Product]


class ProductsResponse(BaseResponse):
    data: Optional[ProductsData] = None
