from playwright.sync_api import Page
from src.models.question import Option, Question
from src.models.state import State
from src.models.question import InputSummary


class Parser:
    def parse_page(self, page: Page, page_index: int) -> State:
        """
        Parse curr Playwright page
        Return State
        """
        questions: list[Question] = []
        blocks = page.locator(".question")
        if blocks.count() == 0:
            blocks = page.locator("[id^='QID'], .QuestionOuter")
        count = blocks.count()

        for i in range(count):
            block = blocks.nth(i)
            qid = (
                block.get_attribute("id")
                or block.get_attribute("data-questionid")
                or f"question_{page_index}_{i}"
            )
            text = self._extract_question_text(block)
            options = self._extract_options(block, qid, i)
            required = self._extract_required(block)
            input_summary = self._extract_input_summary(block)
            questions.append(
                Question(
                    qid=qid,
                    text=text,
                    options=options,
                    required=required,
                    selector=self._build_selector(qid, i),
                    input_summary=input_summary,
                )
            )

        return State(
            page_index=page_index,
            url=page.url,
            questions=questions,
        )

    def _extract_question_text(self, block) -> str:
        selectors = [
            ".question-display",
            ".QuestionText",
            "[class*='question-display']",
        ]

        for selector in selectors:
            locator = block.locator(selector)
            if locator.count() > 0:
                text = locator.first.inner_text().strip()
                if text:
                    return text
        return block.inner_text().strip().split("\n")[0]

    def _extract_options(self, block, qid: str, question_index: int) -> list[Option]:
        options: list[Option] = []
        choices = block.locator(".choice")
        if choices.count() > 0:
            for j in range(choices.count()):
                choice = choices.nth(j)
                label_locator = choice.locator(".choice-content")
                if label_locator.count() > 0:
                    label = label_locator.first.inner_text().strip()
                else:
                    label = choice.inner_text().strip()
                if label:
                    options.append(
                        Option(
                            label=label,
                            selector=f".question >> nth={question_index} >> .choice >> nth={j}",
                            value=label,
                        )
                    )
            return options
        labels = block.locator("label")
        for j in range(labels.count()):
            label = labels.nth(j)
            label_text = label.inner_text().strip()
            if label_text:
                options.append(
                    Option(
                        label=label_text,
                        selector=f"#{qid} label >> nth={j}",
                        value=label_text,
                    )
                )
        return options

    def _extract_required(self, block) -> bool:
        marker_count = block.locator(
            ".required-marker, "
            ".required-marker-text, "
            "[aria-label*='Required'],"
            "[title*='Required']"
        ).count()
        if marker_count > 0:
            return True
        text = block.inner_text().lower()
        if "* required" in text or "required" in text:
            return True
        if block.locator("[required], [aria-required='true']").count() > 0:
            return True
        return False

    def _extract_input_summary(self, block) -> InputSummary:
        return InputSummary(
            radio_count=block.locator("input[type='radio']").count(),
            checkbox_count=block.locator("input[type='checkbox']").count(),
            textarea_count=block.locator("textarea").count(),
            text_input_count=block.locator("input[type='text']").count(),
            range_count=block.locator("input[type='range']").count(),
            select_count=block.locator("select").count(),
            slider_count=block.locator("[role='slider'], .slider").count(),
            choice_count=block.locator(".choice").count(),
        )

    def _build_selector(self, qid: str, index: int) -> str:
        if qid.startswith("question_"):
            return f".question >> nth={index}"
        return f"#{qid}"
