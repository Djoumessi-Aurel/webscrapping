from playwright.sync_api import sync_playwright


def main():
    with sync_playwright() as playwright:
        browser = playwright.firefox.launch()
        page = browser.new_page()
        page.goto("softweight.vercel.app")
        # page.wait_for_timeout(5000)
        page.pause()


if __name__ == "__main__":
    main()