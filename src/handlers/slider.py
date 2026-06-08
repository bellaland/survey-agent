from playwright.sync_api import Page

from src.handlers.handler import Handler
from src.models.answer_plan import AnswerPlan
from src.models.question import Question


class SliderHandler(Handler):
    def fill(
        self,
        page: Page,
        question: Question,
        plan: AnswerPlan,
    ) -> None:
        block = page.locator(question.selector)
        answer = plan.answer if plan.answer is not None else 50

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

        text_inputs = block.locator(
            "input[type='text']:not([name='g-recaptcha-response'])"
        )

        if text_inputs.count() > 0:
            value = str(answer)

            if value == "50":
                value = "3"

            filled = 0

            for i in range(text_inputs.count()):
                input_box = text_inputs.nth(i)

                try:
                    input_box.scroll_into_view_if_needed()
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
                    filled += 1
                except Exception:
                    continue

            if filled > 0:
                return

        handles = block.locator(
            ".handle, "
            ".sliderToolTipBox, "
            "[role='slider'], "
            "[class*='handle'], "
            "[class*='Handle']"
        )

        handle_count = handles.count()
        moved = 0

        for i in range(handle_count):
            handle = handles.nth(i)

            try:
                handle.scroll_into_view_if_needed()
                page.wait_for_timeout(200)

                handle_box = handle.bounding_box()
                if not handle_box:
                    continue

                start_x = handle_box["x"] + handle_box["width"] / 2
                start_y = handle_box["y"] + handle_box["height"] / 2

                track_locator = block.locator(
                    ".track, "
                    ".SliderTrack, "
                    "[class*='track'], "
                    "[class*='Track'], "
                    "[class*='bar'], "
                    "[class*='Bar'], "
                    "[class*='rail'], "
                    "[class*='Rail']"
                )

                target_x = None

                for j in range(track_locator.count()):
                    track = track_locator.nth(j)

                    try:
                        if not track.is_visible():
                            continue

                        track_box = track.bounding_box()
                        if not track_box:
                            continue

                        same_row = (
                            abs((track_box["y"] + track_box["height"] / 2) - start_y)
                            < 80
                        )

                        if same_row and track_box["width"] > 100:
                            target_x = track_box["x"] + track_box["width"] * 0.5
                            break

                    except Exception:
                        continue

                if target_x is None:
                    target_x = start_x + 300

                page.mouse.move(start_x, start_y)
                page.mouse.down()
                page.mouse.move(target_x, start_y, steps=15)
                page.mouse.up()

                moved += 1
                page.wait_for_timeout(200)

            except Exception:
                continue

        print(f"slider handles moved for {question.qid}: {moved}/{handle_count}")

        if moved > 0:
            return

        clickable_options = block.locator(
            "label, button, [role='radio'], [role='button']"
        )

        visible_options = []

        for i in range(clickable_options.count()):
            option = clickable_options.nth(i)

            try:
                option.scroll_into_view_if_needed()
                if option.is_visible():
                    box = option.bounding_box()
                    if box:
                        visible_options.append(option)
            except Exception:
                continue

        if visible_options:
            target = visible_options[len(visible_options) // 2]
            target.click()
            return

        raise ValueError(f"No slider found for {question.qid}")
