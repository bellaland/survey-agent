from playwright.sync_api import Page
from src.models.answer_plan import AnswerPlan
from src.models.question import Question
from src.handlers.handler import Handler


class RankingHandler(Handler):
    def fill(
        self,
        page: Page,
        question: Question,
        plan: AnswerPlan,
    ) -> None:
        block = page.locator(question.selector)
        if block.locator("ranking").count() > 0:
            block.locator("ranking").first.fill(str(plan.answer))
            return
        if block.locator("input[type='numerical']").count() > 0:
            block.locator("input[type='nunmerical']").first.fill(str(plan.answer))
            return
        raise ValueError(f"No ranking found for {question.qid}")
