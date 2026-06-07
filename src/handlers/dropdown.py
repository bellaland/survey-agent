from playwright.sync_api import Page
from src.models.answer_plan import AnswerPlan
from src.models.question import Question
from src.handlers.handler import Handler


class DropdownHandler(Handler):
    def fill(
        self,
        page: Page,
        question: Question,
        plan: AnswerPlan,
    ) -> None:
        block = page.locator(question.selector)
        selects = block.locator("select")
        if selects.count() == 0:
            raise ValueError(f"No dropdown found for {question.qid}")
        select = selects.first
        answer = str(plan.answer)
        try:
            select.select_option(value=answer)
        except Exception:
            select.select_option(label=answer)
