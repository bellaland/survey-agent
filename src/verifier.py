from playwright.sync_api import Page
from src.models.answer_plan import AnswerPlan
from src.models.question import Question


class Verifier:
    def verify_question_answered(
        self,
        page: Page,
        question: Question,
        plan: AnswerPlan,
    ) -> bool:
        if question.type == "instruction":
            return True

        if question.type == "multiple_choice":
            return self._verify_choice(page, question)

        if question.type == "checkbox":
            return self._verify_choice(page, question)

        if question.type == "text":
            return self._verify_text(page, question)

        if question.type == "slider":
            return self._verify_slider(page, question, plan.answer)

        return False

    def _verify_choice(self, page: Page, question: Question) -> bool:
        block = page.locator(question.selector)
        return block.locator("input:checked").count() > 0

    def _verify_text(self, page: Page, question: Question) -> bool:
        block = page.locator(question.selector)
        if block.locator("textarea").count() > 0:
            value = block.locator("textarea").first.input_value()
            return len(value.strip()) > 0
        if block.locator("input[type='text']").count() > 0:
            value = block.locator("input[type='text']").first.input_value()
            return len(value.strip()) > 0
        return False

    def _verify_slider(
        self, page: Page, question: Question, expected_answer: object
    ) -> bool:
        block = page.locator(question.selector)
        sliders = block.locator("input[type='range']")
        if sliders.count() == 0:
            return False
        slider = sliders.first
        actual = slider.input_value()
        print(f"verify slider: expected={expected_answer}, actual={actual}")
        if expected_answer is None:
            return actual.strip() != ""
        try:
            return int(float(actual)) == int(float(str(expected_answer)))
        except ValueError:
            return str(actual).strip() == str(expected_answer).strip()

    def verify_no_visible_validation_error(self, page: Page) -> bool:
        error_selectors = [
            ".error-message",
            ".error-banner",
            ".ValidationError",
            "[role='alert']",
        ]
        for selector in error_selectors:
            locator = page.locator(selector)
            if locator.count() > 0 and locator.first.is_visible():
                return False
        return True
