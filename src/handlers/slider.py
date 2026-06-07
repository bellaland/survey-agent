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
        sliders = block.locator("input[type='range']")
        if sliders.count() == 0:
            raise ValueError(f"No slider found for {question.qid}")
        slider = sliders.first
        slider.evaluate(
            """(el, value) => {
                const nativeInputValueSetter =
                    Object.getOwnPropertyDescriptor(
                        window.HTMLInputElement.prototype,
                        "value"
                    ).set;
                nativeInputValueSetter.call(el, value);
                el.dispatchEvent(new Event('input', { bubbles: true }));
                el.dispatchEvent(new Event('change', { bubbles: true}));
            }""",
            str(plan.answer),
        )
        page.wait_for_timeout(300)
        actual = slider.input_value()
        print(f"slider value after fill: {actual}")
