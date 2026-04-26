from __future__ import annotations
from typing import Any, Optional, Union
from pydantic import BaseModel, Field
from app.core.constants import QuestionCategory, InputType, QuestionMode


# ──────────────────────────────────────────────
# Shared sub-models
# ──────────────────────────────────────────────

class QuestionOption(BaseModel):
    label: str
    value: str


class QuestionRange(BaseModel):
    min: float
    max: float
    step: float
    unit: str


class QuestionDependency(BaseModel):
    question_id: str
    value: Union[str, int, float, list[str]]


class QuestionValidation(BaseModel):
    min: Optional[float] = None
    max: Optional[float] = None
    regex: Optional[str] = None


class Question(BaseModel):
    id: str
    category: QuestionCategory
    question_text: str
    description: Optional[str] = None
    input_type: InputType
    options: Optional[list[QuestionOption]] = None
    range: Optional[QuestionRange] = None
    default_value: Optional[Union[str, int, float, list[str]]] = None
    placeholder: Optional[str] = None
    is_required: bool = True
    depends_on: Optional[QuestionDependency] = None
    validation: Optional[QuestionValidation] = None
    priority: int = 0
    mode: QuestionMode = QuestionMode.BASIC
    tags: list[str] = Field(default_factory=list)


# ──────────────────────────────────────────────
# Envelope types
# ──────────────────────────────────────────────

class ErrorObject(BaseModel):
    code: str
    message: str
    field: Optional[str] = None


class MetaObject(BaseModel):
    request_id: str
    timestamp: str          # ISO-8601
    version: str


class BaseResponse(BaseModel):
    success: bool
    error: Optional[ErrorObject] = None
    meta: MetaObject
