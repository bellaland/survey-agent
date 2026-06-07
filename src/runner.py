from playwright.sync_api import sync_playwright

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
                    next_button = page.locator("#next-button")
                    if next_button.count() == 0:
                        status = "completed"
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
