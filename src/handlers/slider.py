from playwright.sync_api import Page
from src.models.answer_plan import AnswerPlan
from src.models.question import Question
from src.handlers.handler import Handler


class SliderHandler(Handler):
    def fill(
        self,
        page: Page,
        question: Question,
        plan: AnswerPlan,
    ) -> None:
        block = page.locator(question.selector)
        answer = plan.answer if plan.answer is not None else 98
        ranges = block.locator("input[type='range']")
        if ranges.count() > 0:
            for i in range(ranges.count()):
                slider = ranges.nth(i)
                slider.evaluate(
                    """
                    (el, value) => {
                        el.value = value;
                        el.dispatchEvent(new Event("input", { bubbles: true }));
                        el.dispatchEvent(new Event("change", { bubbles: true }));
                    }
                    """,
                    str(answer),
                )
            return
        text_inputs = block.locator("input[type='text']")
        if text_inputs.count() > 0:
            value = str(answer)
            if value == "98":
                value = "3"
            for i in range(text_inputs.count()):
                input_box = text_inputs.nth(i)
                input_box.evaluate(
                    """
                   (el, value) => {
                        el.value = value;
                        el.dispatchEvent(new Event("input", { bubbles: true }));
                        el.dispatchEvent(new Event("change", { bubbles: true }));
                        el.dispatchEvent(new Event("blur", { bubbles: true }));
                    }
                    """,
                    value,
                )
            return
        role_sliders = block.locator("[role='slider']")
        if role_sliders.count() > 0:
            for i in range(role_sliders.count()):
                slider = role_sliders.nth(i)
                slider.evaluate(
                    """
                   (el, value) => {
                        el.setAttribute("aria-valuenow", value);
                        el.dispatchEvent(new Event("input", { bubbles: true }));
                        el.dispatchEvent(new Event("change", { bubbles: true }));
                    }
                    """,
                    str(answer),
                )
            return
        raise ValueError(f"No slider found for {question.qid}")
