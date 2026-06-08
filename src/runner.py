from datetime import UTC, datetime
from uuid import uuid4

from playwright.sync_api import Error as PlaywrightError
from playwright.sync_api import Page, sync_playwright

from src.classifier import Classifier
from src.config import load_config
from src.generator import Generator
from src.handlers.registry import Registry
from src.models.answer_result import AnswerResult
from src.parser import Parser
from src.policy import Policy
from src.storage import Storage
from src.verifier import Verifier


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

                self._wait_for_manual_recaptcha(page)
                self._wait_for_manual_verification_challenge(page)

                for page_index in range(self.config.runtime.max_pages):
                    if page.is_closed():
                        status = "completed"
                        break

                    print(f"page {page_index} | url={page.url}")

                    self._wait_for_manual_recaptcha(page)
                    self._wait_for_manual_verification_challenge(page)

                    if page.is_closed():
                        status = "completed"
                        break

                    screenshot_path = self.storage.save_screenshot(
                        run_id,
                        page_index,
                        page,
                    )
                    html_path = self.storage.save_html_snapshot(
                        run_id,
                        page_index,
                        page,
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

                    has_slider_question = any(
                        q.type == "slider" for q in state.questions
                    )

                    # Do not run emergency fallback on slider-heavy pages after the
                    # slider handler succeeds. This avoids crashes on long slider pages.
                    if not has_slider_question and not page.is_closed():
                        self._fill_remaining_visible_inputs(page)

                    if page.is_closed():
                        status = "completed"
                        break

                    if not self.verifier.verify_no_visible_validation_error(page):
                        raise RuntimeError("Visible validation error found before next")

                    self._scroll_to_bottom(page)

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

                    try:
                        next_button.click()
                        page.wait_for_timeout(2000)
                    except PlaywrightError as exc:
                        if self._is_target_closed_error(exc):
                            print("Page closed after click; treating run as completed.")
                            status = "completed"
                            pages_completed = page_index + 1
                            break
                        raise

                    if page.is_closed():
                        print("Page closed after click; treating run as completed.")
                        status = "completed"
                        pages_completed = page_index + 1
                        break

                    self._wait_for_manual_recaptcha(page)
                    self._wait_for_manual_verification_challenge(page)

                    if page.is_closed():
                        print(
                            "Page closed after verification; treating run as completed."
                        )
                        status = "completed"
                        pages_completed = page_index + 1
                        break

                    new_text = page.locator("body").inner_text()[:200]

                    if old_text == new_text:
                        print(
                            "Page did not change after first click. "
                            "Trying fallback fill once."
                        )

                        if not page.is_closed():
                            self._fill_remaining_visible_inputs(page)

                        if page.is_closed():
                            print(
                                "Page closed during fallback; "
                                "treating run as completed."
                            )
                            status = "completed"
                            pages_completed = page_index + 1
                            break

                        self._scroll_to_bottom(page)
                        page.wait_for_timeout(500)

                        retry_button = self._find_next_button(page)

                        if retry_button is None:
                            raise RuntimeError(
                                "page did not change and no retry button found"
                            )

                        try:
                            retry_button.click()
                            page.wait_for_timeout(2000)
                        except PlaywrightError as exc:
                            if self._is_target_closed_error(exc):
                                print(
                                    "Page closed after retry click; "
                                    "treating run as completed."
                                )
                                status = "completed"
                                pages_completed = page_index + 1
                                break
                            raise

                        if page.is_closed():
                            print(
                                "Page closed after retry click; "
                                "treating run as completed."
                            )
                            status = "completed"
                            pages_completed = page_index + 1
                            break

                        self._wait_for_manual_recaptcha(page)
                        self._wait_for_manual_verification_challenge(page)

                        if page.is_closed():
                            print(
                                "Page closed after retry verification; "
                                "treating run as completed."
                            )
                            status = "completed"
                            pages_completed = page_index + 1
                            break

                        retry_text = page.locator("body").inner_text()[:200]

                        if retry_text == old_text:
                            raise RuntimeError(
                                "page did not change after fallback retry"
                            )

                    pages_completed = page_index + 1

                try:
                    if not page.is_closed():
                        browser.close()
                except PlaywrightError:
                    status = "completed"

        except PlaywrightError as exc:
            if self._is_target_closed_error(exc):
                print("Browser/page closed; treating run as completed.")
                status = "completed"
            else:
                status = "failed"
                raise

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

    def _is_target_closed_error(self, exc: PlaywrightError) -> bool:
        return "Target page, context or browser has been closed" in str(exc)

    def _scroll_to_bottom(self, page: Page) -> None:
        if page.is_closed():
            return

        try:
            page.evaluate(
                """
                () => {
                    window.scrollTo({
                        top: document.body.scrollHeight,
                        behavior: "instant"
                    });
                }
                """
            )
            page.wait_for_timeout(500)
        except PlaywrightError:
            return

    def _find_next_button(self, page: Page):
        if page.is_closed():
            return None

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
            try:
                locator = page.locator(selector)

                if locator.count() == 0:
                    continue

                candidate = locator.first

                try:
                    candidate.scroll_into_view_if_needed()
                    page.wait_for_timeout(200)
                except PlaywrightError:
                    pass

                if candidate.is_visible():
                    return candidate

            except PlaywrightError:
                continue

        buttons = page.locator("button")

        for i in range(buttons.count()):
            try:
                button = buttons.nth(i)
                button.scroll_into_view_if_needed()
                page.wait_for_timeout(100)

                if not button.is_visible():
                    continue

                text = button.inner_text().strip()

                if text in {"→", "->", ">", "›"}:
                    return button

            except PlaywrightError:
                continue

        visible_buttons = []

        for i in range(buttons.count()):
            try:
                button = buttons.nth(i)
                button.scroll_into_view_if_needed()
                page.wait_for_timeout(100)

                if button.is_visible():
                    box = button.bounding_box()

                    if box:
                        visible_buttons.append((box["x"], button))

            except PlaywrightError:
                continue

        if visible_buttons:
            visible_buttons.sort(key=lambda item: item[0])
            return visible_buttons[-1][1]

        return None

    def _wait_for_manual_recaptcha(self, page: Page) -> None:
        if page.is_closed():
            return

        visible_recaptcha = False

        try:
            iframe_locator = page.locator("iframe[src*='recaptcha']")

            for i in range(iframe_locator.count()):
                iframe = iframe_locator.nth(i)

                try:
                    if iframe.is_visible():
                        visible_recaptcha = True
                        break
                except PlaywrightError:
                    continue

            widget_locator = page.locator(".g-recaptcha")

            for i in range(widget_locator.count()):
                widget = widget_locator.nth(i)

                try:
                    if widget.is_visible():
                        visible_recaptcha = True
                        break
                except PlaywrightError:
                    continue

        except PlaywrightError:
            return

        if not visible_recaptcha:
            return

        print("\nreCAPTCHA detected.")
        print("Please solve it manually in the browser.")
        input("After solving reCAPTCHA and moving forward, press Enter here...")

        if not page.is_closed():
            page.wait_for_timeout(2000)

    def _wait_for_manual_verification_challenge(self, page: Page) -> None:
        if page.is_closed():
            return

        try:
            body_text = page.locator("body").inner_text().lower()
        except PlaywrightError:
            return

        challenge_keywords = [
            "please solve the math problem",
            "math problem pictured",
            "enter your answer below",
            "i'm not a robot",
            "recaptcha",
        ]

        if not any(keyword in body_text for keyword in challenge_keywords):
            return

        print("\nManual verification challenge detected.")
        print("Please solve it manually in the browser.")
        print("Waiting until the verification page clears...")

        try:
            page.wait_for_function(
                """
                () => {
                    const text = document.body.innerText.toLowerCase();
                    return !(
                        text.includes("please solve the math problem") ||
                        text.includes("math problem pictured") ||
                        text.includes("enter your answer below") ||
                        text.includes("i'm not a robot") ||
                        text.includes("recaptcha")
                    );
                }
                """,
                timeout=180_000,
            )
            print("Manual verification cleared. Continuing.")
        except PlaywrightError:
            print("Manual verification wait timed out. Continuing cautiously.")

        if not page.is_closed():
            page.wait_for_timeout(2000)

    def _fill_remaining_visible_inputs(self, page: Page) -> None:
        if page.is_closed():
            return

        try:
            body_text = page.locator("body").inner_text().lower()
        except PlaywrightError:
            return

        self._fill_visible_text_inputs(page, body_text)
        self._fill_visible_radio_groups(page)
        self._fill_visible_checkboxes(page)
        self._fill_visible_dropdowns(page)

    def _fill_visible_text_inputs(self, page: Page, body_text: str) -> None:
        if page.is_closed():
            return

        try:
            text_inputs = page.locator(
                "input[type='text']:not([name='g-recaptcha-response']), "
                "input:not([type])"
            )
            input_count = text_inputs.count()
        except PlaywrightError:
            return

        for i in range(input_count):
            try:
                if page.is_closed():
                    return

                input_box = text_inputs.nth(i)

                if not input_box.is_visible():
                    continue

                current = input_box.input_value().strip()
                if current:
                    continue

                nearby_text = (
                    input_box.locator(
                        "xpath=ancestor::*[self::div or self::td or self::tr][1]"
                    )
                    .inner_text()
                    .lower()
                )

                value = self._infer_text_input_value(
                    nearby_text=nearby_text,
                    body_text=body_text,
                    input_index=i,
                )

                input_box.fill(value)

            except PlaywrightError:
                return
            except Exception:
                continue

    def _infer_text_input_value(
        self,
        nearby_text: str,
        body_text: str,
        input_index: int,
    ) -> str:
        if (
            "age in years" in nearby_text
            or "number only" in nearby_text
            or "how old are you" in nearby_text
            or ("age" in nearby_text and "years" in nearby_text)
        ):
            return self.config.profile.demographic.get("age_number", "25")

        if "gender" in nearby_text:
            return self.config.profile.demographic.get("gender", "Prefer not to say")

        if "gender" in body_text and input_index == 0:
            return self.config.profile.demographic.get("gender", "Prefer not to say")

        if (
            "age in years" in body_text
            or "number only" in body_text
            or "how old are you" in body_text
        ) and input_index <= 1:
            return self.config.profile.demographic.get("age_number", "25")

        if "calories" in nearby_text:
            return "110"

        if "carbohydrate" in nearby_text:
            return "26"

        if "fat" in nearby_text:
            return "0"

        if "protein" in nearby_text:
            return "2"

        if (
            "calories" in body_text
            or "carbohydrate" in body_text
            or "protein" in body_text
        ):
            nutrition_defaults = ["110", "26", "0", "2"]
            if input_index < len(nutrition_defaults):
                return nutrition_defaults[input_index]
            return "0"

        return "N/A"

    def _fill_visible_radio_groups(self, page: Page) -> None:
        if page.is_closed():
            return

        try:
            radios = page.locator("input[type='radio']")
            radio_count = radios.count()
        except PlaywrightError:
            return

        radio_names: list[str] = []

        for i in range(radio_count):
            try:
                radio = radios.nth(i)
                name = radio.get_attribute("name")

                if name and name not in radio_names:
                    radio_names.append(name)

            except PlaywrightError:
                return
            except Exception:
                continue

        for name in radio_names:
            try:
                if page.is_closed():
                    return

                group = page.locator(f"input[type='radio'][name='{name}']")

                already_checked = page.locator(
                    f"input[type='radio'][name='{name}']:checked"
                ).count()

                if already_checked > 0:
                    continue

                count = group.count()
                if count == 0:
                    continue

                labels = self._get_radio_group_labels(page, group, count)
                target_index = self._choose_radio_index(labels)

                target = group.nth(target_index)

                try:
                    target.scroll_into_view_if_needed()
                    page.wait_for_timeout(100)
                    target.click()
                except PlaywrightError:
                    target.evaluate(
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

            except PlaywrightError:
                return
            except Exception:
                continue

    def _get_radio_group_labels(self, page: Page, group, count: int) -> list[str]:
        labels: list[str] = []

        for i in range(count):
            radio = group.nth(i)
            label_text = ""

            try:
                radio_id = radio.get_attribute("id")

                if radio_id:
                    label = page.locator(f"label[for='{radio_id}']")

                    if label.count() > 0:
                        label_text = label.first.inner_text().strip().lower()

            except Exception:
                pass

            labels.append(label_text)

        return labels

    def _choose_radio_index(self, labels: list[str]) -> int:
        preferred_keywords = [
            "prefer not",
            "not to answer",
            "no",
            "neither",
            "neutral",
            "not sure",
        ]

        for keyword in preferred_keywords:
            for idx, label_text in enumerate(labels):
                if keyword in label_text:
                    return idx

        return 0

    def _fill_visible_checkboxes(self, page: Page) -> None:
        if page.is_closed():
            return

        try:
            checkboxes = page.locator("input[type='checkbox']")
            checkbox_count = checkboxes.count()
            already_checked_count = page.locator(
                "input[type='checkbox']:checked"
            ).count()
        except PlaywrightError:
            return

        if already_checked_count > 0:
            return

        for i in range(checkbox_count):
            try:
                if page.is_closed():
                    return

                checkbox = checkboxes.nth(i)
                checkbox.scroll_into_view_if_needed()
                page.wait_for_timeout(100)

                if not checkbox.is_visible():
                    continue

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

                checkbox.click()
                break

            except PlaywrightError:
                return
            except Exception:
                continue

    def _fill_visible_dropdowns(self, page: Page) -> None:
        if page.is_closed():
            return

        try:
            selects = page.locator("select")
            select_count = selects.count()
        except PlaywrightError:
            return

        for i in range(select_count):
            try:
                if page.is_closed():
                    return

                select = selects.nth(i)

                if not select.is_visible():
                    continue

                current = select.input_value().strip()

                if current and "null" not in current.lower():
                    continue

                options = select.locator("option")
                option_count = options.count()

                if option_count <= 1:
                    continue

                for j in range(1, option_count):
                    value = options.nth(j).get_attribute("value")
                    label = options.nth(j).inner_text().strip()

                    if value:
                        select.select_option(value=value)
                        break

                    if label:
                        select.select_option(label=label)
                        break

            except PlaywrightError:
                return
            except Exception:
                continue
