from playwright.sync_api import Page

from src.handlers.handler import Handler
from src.models.answer_plan import AnswerPlan
from src.models.question import Question


class CheckboxHandler(Handler):
    def fill(
        self,
        page: Page,
        question: Question,
        plan: AnswerPlan,
    ) -> None:
        block = page.locator(question.selector)

        answers = plan.answer
        if not isinstance(answers, list):
            answers = [str(answers)]

        wanted = {str(a) for a in answers}
        clicked = 0

        for option in question.options:
            if option.value is None:
                continue

            if str(option.value) not in wanted:
                continue

            if option.selector is None:
                continue

            locator = page.locator(option.selector)

            try:
                locator.scroll_into_view_if_needed()
                page.wait_for_timeout(100)
                locator.click()
                clicked += 1
            except Exception:
                continue

        if clicked > 0:
            return

        checkboxes = block.locator("input[type='checkbox']")

        for i in range(checkboxes.count()):
            checkbox = checkboxes.nth(i)

            try:
                checkbox.scroll_into_view_if_needed()
                page.wait_for_timeout(100)

                if checkbox.is_checked():
                    return

                label_text = ""

                checkbox_id = checkbox.get_attribute("id")
                if checkbox_id:
                    label = page.locator(f"label[for='{checkbox_id}']")
                    if label.count() > 0:
                        label_text = label.first.inner_text().strip().lower()

                if (
                    "none of the above" in label_text
                    or label_text == "none"
                    or label_text == "na"
                    or label_text == "n/a"
                ):
                    continue

                try:
                    checkbox.click()
                except Exception:
                    checkbox.evaluate(
                        """
                        (el) => {
                            el.checked = true;
                            el.dispatchEvent(
                                new Event("input", { bubbles: true })
                            );
                            el.dispatchEvent(
                                new Event("change", { bubbles: true })
                            );
                            el.click();
                        }
                        """
                    )

                return

            except Exception:
                continue

        raise ValueError(f"Unable to check any option for {question.qid}")
