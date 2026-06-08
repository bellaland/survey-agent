from playwright.sync_api import Page, sync_playwright

from src.config import load_config
from src.parser import Parser
from src.classifier import Classifier
from src.handlers.registry import Registry
from src.policy import Policy
from src.verifier import Verifier
from uuid import uuid4
from datetime import UTC, datetime
from src.storage import Storage
from src.models.answer_result import AnswerResult
from src.generator import Generator


class Runner:
    def __init__(self):
        self.config = load_config()
        self.parser = Parser()
        self.classifier = Classifier()
        self.policy = Policy()
        self.generator = Generator(self.config)
        self.registry = Registry()
        self.verifier = Verifier()
        self.storage = Storage(self.config.storage.db_path)

    def run(self, url: str) -> None:
        run_id = str(uuid4())
        started_at = datetime.now(UTC).isoformat()
        pages_completed = 0
        status = "running"
        self.storage.save_run_start(
            run_id=run_id,
            survey_url=url,
            started_at=started_at,
        )
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=self.config.runtime.headless)
                page = browser.new_page()
                page.goto(url, wait_until="domcontentloaded")
                page.wait_for_timeout(3000)
                for page_index in range(self.config.runtime.max_pages):
                    print(f"page {page_index} | url={page.url}")
                    screenshot_path = self.storage.save_screenshot(
                        run_id, page_index, page
                    )
                    html_path = self.storage.save_html_snapshot(
                        run_id, page_index, page
                    )
                    state = self.parser.parse_page(page, page_index)
                    state.questions = self.classifier.classify_all(state.questions)
                    print(state.model_dump_json(indent=2))
                    self.storage.save_page(
                        run_id=run_id,
                        page_index=page_index,
                        url=page.url,
                        screenshot_path=screenshot_path,
                        html_path=html_path,
                    )
                    for question in state.questions:
                        plan = self.policy.decide(question)
                        plan = self.generator.generate(question, plan)
                        if plan.action == "continue":
                            continue
                        handler = self.registry.get(question.type)
                        handler.fill(page=page, question=question, plan=plan)
                        verified = self.verifier.verify_question_answered(
                            page=page,
                            question=question,
                            plan=plan,
                        )
                        if not verified:
                            raise RuntimeError(
                                f"Answer verification failed for {question.qid}"
                            )
                        result = AnswerResult(
                            qid=question.qid,
                            answer=plan.answer,
                            success=True,
                            verified=verified,
                        )
                        self.storage.save_answer_result(
                            run_id=run_id,
                            page_index=page_index,
                            question=question,
                            plan=plan,
                            result=result,
                        )
                    if not self.verifier.verify_no_visible_validation_error(page):
                        raise RuntimeError("Visible validation error found before next")
                    next_button = self._find_next_button(page)
                    if next_button is None:
                        print("No next/submit button found. Ending run.")
                        status = "completed"
                        break
                    button_text = next_button.inner_text().lower().strip()
                    body_text = page.locator("body").inner_text().lower()
                    if (
                        "submit" in button_text
                        or "finish" in button_text
                        or "end of survey" in body_text
                    ):
                        if not self.config.runtime.submit_final:
                            print("dry run: final submit blocked.")
                            status = "dry_run_completed"
                            break
                    old_text = page.locator("body").inner_text()[:200]
                    next_button.click()
                    page.wait_for_timeout(2000)
                    new_text = page.locator("body").inner_text()[:200]
                    if old_text == new_text:
                        raise RuntimeError("page did not change after clicking next")
                    pages_completed = page_index + 1
                browser.close()
        except Exception:
            status = "failed"
            raise
        finally:
            finished_at = datetime.now(UTC).isoformat()
            self.storage.save_run_end(
                run_id=run_id,
                finished_at=finished_at,
                status=status,
                pages_completed=pages_completed,
            )
            self.storage.close()

    def _find_next_button(self, page: Page):
        selectors = [
            "#next-button",
            "#NextButton",
            "button:has-text('Next')",
            "button:has-text('Continue')",
            "button:has-text('Submit')",
            "input[type='submit']",
            "input[value='Next']",
            "input[value='Continue']",
            "input[value='Submit']",
            "button[aria-label*='Next']",
            "button[aria-label*='next']",
            "button[aria-label*='Continue']",
            "button[aria-label*='continue']",
        ]
        for selector in selectors:
            locator = page.locator(selector)
            if locator.count() > 0 and locator.first.is_visible():
                return locator.first
        buttons = page.locator("button")
        for i in range(buttons.count()):
            button = buttons.nth(i)
            if not button.is_visible():
                continue
            text = button.inner_text().strip()
            if text in {"->", ">", ">"}:
                return button
        visible_buttons = []
        for i in range(buttons.count()):
            button = buttons.nth(i)
            if button.is_visible():
                box = button.bounding.box()
                if box:
                    visible_buttons.append((box["x"], button))
        if visible_buttons:
            visible_buttons.sort(key=lambda item: item[0])
            return visible_buttons[-1][1]
        return None
