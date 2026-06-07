from playwright.sync_api import Page
from src.models.answer_plan import AnswerPlan
from src.models.question import Question
from src.handlers.handler import Handler


class MultipleChoiceHandler(Handler):
    def fill(
        self,
        page: Page,
        question: Question,
        plan: AnswerPlan,
    ) -> None:
        answer = str(plan.answer)
        for option in question.options:
            if option.value == answer:
                page.locator(option.selector).click()
                return
        raise ValueError(f"Unable to find option {answer} for {question.qid}")
