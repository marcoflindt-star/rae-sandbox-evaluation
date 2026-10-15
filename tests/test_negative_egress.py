import threading
import os
from urllib.parse import urlparse

from playwright.sync_api import sync_playwright


def main():
    blocked = []
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(
            executable_path=os.environ.get("PLAYWRIGHT_EXECUTABLE_PATH") or None,
            headless=True,
            args=["--disable-background-networking", "--no-first-run", "--no-sandbox"],
        )
        context = browser.new_context()

        def guard_request(route):
            host = urlparse(route.request.url).hostname
            if host not in {"127.0.0.1", "localhost"}:
                blocked.append(host)
                route.abort()
                return
            route.continue_()

        context.route("**/*", guard_request)
        page = context.new_page()
        try:
            page.goto("https://external.invalid/should-be-blocked", wait_until="commit", timeout=5000)
        except Exception:
            pass
        context.close()
        browser.close()
    assert blocked == ["external.invalid"]
    print("negative egress blocking test: PASS")


if __name__ == "__main__":
    main()
