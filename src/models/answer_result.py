from pydantic import BaseModel


class AnswerResult(BaseModel):
    qid: str
    answer: str | int | float | list[str] | None
    success: bool
    verified: bool
    error: str | None = None
    screenshot_path: str | None = None
