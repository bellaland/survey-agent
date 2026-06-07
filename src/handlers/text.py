from playwright.sync_api import Page
from src.models.answer_plan import AnswerPlan
from src.models.question import Question
from src.handlers.handler import Handler


class TextHandler(Handler):
    def fill(
        self,
        page: Page,
        question: Question,
        plan: AnswerPlan,
    ) -> None:
        block = page.locator(question.selector)
        if block.locator("textarea").count() > 0:
            block.locator("textarea").first.fill(str(plan.answer))
            return
        if block.locator("input[type='text']").count() > 0:
            block.locator("input[type='text']").first.fill(str(plan.answer))
            return
        raise ValueError(f"No text input found for {question.qid}")
