from typing import Optional
from pydantic import BaseModel
from app.schemas.common import BaseResponse, Question


class ChatRequest(BaseModel):
    session_id: str
    message: str


class ChatData(BaseModel):
    message: str
    updated_questions: Optional[list[Question]] = None


class ChatResponse(BaseResponse):
    data: Optional[ChatData] = None
