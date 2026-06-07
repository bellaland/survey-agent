from pydantic import BaseModel
from src.models.question import Question


class State(BaseModel):
    page_index: int
    url: str
    questions: list[Question]
    screenshot_path: str | None = None
    html_path: str | None = None
