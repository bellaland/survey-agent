from typing import Literal
from pydantic import BaseModel, Field

QuestionType = Literal[
    "instruction",
    "multiple_choice",
    "checkbox",
    "text",
    "slider",
    "matrix",
    "ranking",
    "dropdown",
    "form",
    "side_by_side",
    "unknown",
]

QuestionCategory = Literal[
    "instruction",
    "factual",
    "opinion",
    "demographic",
    "attention_check",
    "ai_disclosure",
    "unknown",
]


class InputSummary(BaseModel):
    radio_count: int = 0
    checkbox_count: int = 0
    textarea_count: int = 0
    text_input_count: int = 0
    range_count: int = 0
    select_count: int = 0
    slider_count: int = 0
    choice_count: int = 0


class Option(BaseModel):
    label: str
    selector: str | None = None
    value: str | None = None


class Question(BaseModel):
    qid: str
    text: str
    type: QuestionType = "unknown"
    category: QuestionCategory = "unknown"
    options: list[Option] = Field(default_factory=list)
    required: bool = False
    selector: str
    input_summary: InputSummary = Field(default_factory=InputSummary)
