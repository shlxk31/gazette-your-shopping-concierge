from typing import Optional
from pydantic import BaseModel
from app.schemas.common import BaseResponse, Question
from app.core.constants import QuestionMode


class QueryRequest(BaseModel):
    query: str


class QueryData(BaseModel):
    session_id: str
    detected_category: str
    initial_questions: list[Question]
    mode: QuestionMode


class QueryResponse(BaseResponse):
    data: Optional[QueryData] = None
