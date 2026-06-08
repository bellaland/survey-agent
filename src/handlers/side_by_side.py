from playwright.sync_api import Page
from src.models.answer_plan import AnswerPlan
from src.models.question import Question
from src.handlers.handler import Handler


class SideBySideHandler(Handler):
    def fill(
        self,
        page: Page,
        question: Question,
        plan: AnswerPlan,
    ) -> None:
        block = page.locator(question.selector)
        radios = block.locator("input[type='radio']")
        count = radios.count()
        names: list[str] = []
        for i in range(count):
            name = radios.nth(i).get_attribute("name")
            if name and name not in names:
                names.append(name)
        for name in names:
            group = block.locator(f"input[type='radio'][name='{name}']")
            group_count = group.count()
            if group_count == 0:
                continue
            target_index = group_count // 2
            target = group.nth(target_index)
            target.evaluate(
                """
                (el) => {
                    el.checked = true;
                    el.dispatchEvent(new Event('input', { bubbles: true}));
                    el.dispatchEvent(new Event('change', { bubbles: true}));
                    el.click();
                }
                """
            )
        selects = block.locator("select")
        for i in range(selects.count()):
            select = selects.nth(i)
            options = select.locator("option")
            if options.count() <= 1:
                continue
            value = options.nth(1).get_attribute("value")
            label = options.nth(1).inner_text().strip()
            if value:
                select.select_option(value=value)
            elif label:
                select.select_option(label=label)
