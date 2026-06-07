from playwright.sync_api import Page
from src.models.answer_plan import AnswerPlan
from src.models.question import Question
from src.handlers.handler import Handler


class CheckboxHandler(Handler):
    def fill(
        self,
        page: Page,
        question: Question,
        plan: AnswerPlan,
    ) -> None:
        answers = plan.answer
        if not isinstance(answers, list):
            answers = [str(answers)]
        wanted = {str(a) for a in answers}
        clicked = 0
        for option in question.options:
            if str(option.value) in wanted:
                page.locator(option.selector).click()
                clicked += 1
        if clicked == 0:
            raise ValueError(f"No checkbox option selected for {question.qid}")
