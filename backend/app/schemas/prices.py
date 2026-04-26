from typing import Optional
from pydantic import BaseModel
from app.schemas.common import BaseResponse
from app.core.constants import Availability


class MarketplacePrice(BaseModel):
    marketplace: str
    price: float
    currency: str
    url: str
    availability: Availability
    is_best: Optional[bool] = None


class PricesData(BaseModel):
    prices: list[MarketplacePrice]


class PricesResponse(BaseResponse):
    data: Optional[PricesData] = None
