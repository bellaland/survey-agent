from playwright.sync_api import Page

from src.handlers.handler import Handler
from src.models.answer_plan import AnswerPlan
from src.models.question import Question


class FormHandler(Handler):
    def fill(
        self,
        page: Page,
        question: Question,
        plan: AnswerPlan,
    ) -> None:
        block = page.locator(question.selector)
        text = question.text.lower()

        inputs = block.locator(
            "input[type='text']:not([name='g-recaptcha-response']), "
            "input[type='email'], "
            "input[type='tel'], "
            "input:not([type])"
        )

        # UPDATED:
        # Nutrition-estimate page: 8 oz orange juice approximate values.
        if "calories" in text and "carbohydrates" in text and "orange juice" in text:
            values = ["110", "26", "0", "2"]
        elif (
            "first name" in block.inner_text().lower()
            or "email address" in block.inner_text().lower()
        ):
            values = ["Alex", "Taylor", "alex.taylor@example.com", "555-123-4567"]
        else:
            values = ["1"] * max(inputs.count(), 1)

        filled = 0

        for i in range(inputs.count()):
            input_box = inputs.nth(i)

            try:
                if not input_box.is_visible():
                    continue

                value = values[i] if i < len(values) else values[-1]
                input_box.fill(value)
                filled += 1
            except Exception:
                continue

        if filled == 0:
            raise ValueError(f"No visible form input found for {question.qid}")
