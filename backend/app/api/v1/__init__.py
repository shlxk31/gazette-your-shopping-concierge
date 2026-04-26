from fastapi import APIRouter
from app.api.v1.endpoints import query, questions, products, prices, chat

api_router = APIRouter()

api_router.include_router(query.router, prefix="/query", tags=["Query"])
api_router.include_router(questions.router, prefix="/questions", tags=["Questions"])
api_router.include_router(products.router, prefix="/products", tags=["Products"])
api_router.include_router(prices.router, prefix="/products", tags=["Prices"])
api_router.include_router(chat.router, prefix="/chat", tags=["Chat"])
