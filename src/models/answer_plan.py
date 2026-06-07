from typing import Literal
from pydantic import BaseModel

AnswerAction = Literal[
    "continue",
    "select",
    "check",
    "type",
    "set_slider",
    "rank",
    "skip",
]


class AnswerPlan(BaseModel):
    qid: str
    action: AnswerAction
    answer: str | int | float | list[str] | None
    policy: str
    tool_used: str | None = None
    confidence: float = 1.0
