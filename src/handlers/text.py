from playwright.sync_api import Page

from src.handlers.handler import Handler
from src.models.answer_plan import AnswerPlan
from src.models.question import Question


class TextHandler(Handler):
    def fill(
        self,
        page: Page,
        question: Question,
        plan: AnswerPlan,
    ) -> None:
        block = page.locator(question.selector)
        answer = "" if plan.answer is None else str(plan.answer)

        textareas = block.locator("textarea:not([name='g-recaptcha-response'])")

        filled = 0

        for i in range(textareas.count()):
            textarea = textareas.nth(i)
            if textarea.is_visible():
                textarea.fill(answer)
                filled += 1

        inputs = block.locator(
            "input[type='text']:not([name='g-recaptcha-response']), input:not([type])"
        )

        for i in range(inputs.count()):
            input_box = inputs.nth(i)
            if input_box.is_visible():
                input_box.fill(answer)
                filled += 1

        if filled == 0:
            raise ValueError(f"No visible text input found for {question.qid}")
