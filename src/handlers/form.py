from playwright.sync_api import Page
from src.models.answer_plan import AnswerPlan
from src.models.question import Question
from src.handlers.handler import Handler


class FormHandler(Handler):
    def fill(
        self,
        page: Page,
        question: Question,
        plan: AnswerPlan,
    ) -> None:
        block = page.locator(question.selector)
        values = [
            "Alex",
            "Taylor",
            "alex.taylor@google.com",
            "312-573-2971",
            "N/A",
        ]
        inputs = block.locator(
            "input[type='text'], input[type='email'], input[type='tel']"
        )
        for i in range(inputs.count()):
            value = values[i] if i < len(values) else "N/A"
            inputs.nth(i).fill(value)
