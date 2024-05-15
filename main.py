from playwright.sync_api import sync_playwright, Playwright

def run(playwright: Playwright):
    chromium = playwright.chromium
    browser = chromium.launch(headless=False)
    page = browser.new_page()
    page.goto("https://us.supreme.com/collections/all?nt=1&")
    page.screenshot(path="screenshot.png")
    browser.close()


with sync_playwright() as playwright:
    run(playwright)

