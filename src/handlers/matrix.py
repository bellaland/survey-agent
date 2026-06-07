from playwright.sync_api import Page
from src.models.answer_plan import AnswerPlan
from src.models.question import Question
from src.handlers.handler import Handler


class MatrixHandler(Handler):
    def fill(
        self,
        page: Page,
        question: Question,
        plan: AnswerPlan,
    ) -> None:
        block = page.locator(question.selector)
        if block.locator("matrix").count() > 0:
            block.locator("matrix").first.fill(str(plan.answer))
            return
        if block.locator("input[type='vector']").count() > 0:
            block.locator("input[type='vector']").first.fill(str(plan.answer))
            return
        raise ValueError(f"No matrix found for {question.qid}")
