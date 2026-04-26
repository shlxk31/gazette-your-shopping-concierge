from typing import Any, Optional, Union
from pydantic import BaseModel
from app.schemas.common import BaseResponse, Question


class AnswerItem(BaseModel):
    question_id: str
    value: Union[str, int, float, list[str]]


class AnswerRequest(BaseModel):
    session_id: str
    answers: list[AnswerItem]


class AnswerData(BaseModel):
    next_questions: Optional[list[Question]] = None
    is_complete: bool = False
    redirect_to: Optional[str] = None


class AnswerResponse(BaseResponse):
    data: Optional[AnswerData] = None
