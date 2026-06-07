from abc import ABC, abstractmethod
from playwright.sync_api import Page
from src.models.answer_plan import AnswerPlan
from src.models.question import Question


class Handler(ABC):
    @abstractmethod
    def fill(
        self,
        page: Page,
        question: Question,
        plan: AnswerPlan,
    ) -> None:
        pass
