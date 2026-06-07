from pathlib import Path
from playwright.sync_api import sync_playwright
from src.parser import Parser
from src.classifier import Classifier

URL = "https://chicagobooth.az1.qualtrics.com/jfe/form/SV_cRSvOqgeHKie1sG"
Path("logs/debug").mkdir(parents=True, exist_ok=True)
with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    page = browser.new_page()
    page.goto(URL, wait_until="domcontentloaded")
    page.wait_for_timeout(8000)
    page.screenshot(path="logs/debug/debug_page.png", full_page=True)
    with open("logs/debug/debug_page.html", "w", encoding="utf-8") as f:
        f.write(page.content())
    print("Title:", page.title())
    print("URL:", page.url)
    print("Body text:")
    print(page.locator("body").inner_text()[:2000])
    print("Question:", page.locator(".question").count())
    print("Question display:", page.locator(".question-display").count())
    print("Choice:", page.locator(".choice").count())
    print("NextButton:", page.locator("#next-button").count())
    print("Button:", page.locator("button").count())
    print("Input:", page.locator("input").count())
    print("Iframe:", page.locator("iframe").count())

    parser = Parser()
    state = parser.parse_page(page, page_index=0)
    print(state.model_dump_json(indent=2))
    browser.close()

    classifier = Classifier()
    state.questions = classifier.classify_all(state.questions)

    print(state.model_dump_json(indent=2))
