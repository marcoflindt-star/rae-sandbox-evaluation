import http.server
import json
import os
import sys
import threading
from pathlib import Path
from tempfile import TemporaryDirectory
from urllib.parse import urlparse

sys.path.insert(0, str(Path(__file__).parents[1]))

from playwright.sync_api import sync_playwright

from rae_guard import redact_har


class FixtureHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        body = b"<body>direct playwright fixture</body>"
        self.send_response(200)
        self.send_header("Content-Type", "text/html")
        self.send_header("Set-Cookie", "direct_fixture=synthetic")
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *_args):
        return


def main():
    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), FixtureHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        with TemporaryDirectory() as directory:
            raw = Path(directory) / "raw.har"
            redacted = Path(directory) / "redacted.har"
            with sync_playwright() as playwright:
                executable_path = os.environ.get("PLAYWRIGHT_EXECUTABLE_PATH")
                browser = playwright.chromium.launch(
                    executable_path=executable_path or None,
                    headless=True,
                    args=["--disable-background-networking", "--no-first-run", "--no-sandbox"],
                )
                context = browser.new_context(record_har_path=str(raw), record_har_content="embed")
                requests = []

                def guard_request(route):
                    host = urlparse(route.request.url).hostname
                    requests.append({"url": route.request.url, "host": host})
                    if host not in {"127.0.0.1", "localhost"}:
                        route.abort()
                        raise AssertionError(f"unexpected egress host: {host}")
                    route.continue_()

                context.route("**/*", guard_request)
                page = context.new_page()
                page.goto(f"http://127.0.0.1:{server.server_port}/?secret=synthetic", wait_until="networkidle")
                context.close()
                browser.close()
            redact_har(raw, redacted)
            serialized = json.dumps(json.loads(redacted.read_text()))
            assert "secret=synthetic" not in serialized
            assert "direct_fixture=synthetic" not in serialized
            assert requests and all(item["host"] in {"127.0.0.1", "localhost"} for item in requests)
            print("direct Playwright isolated browser test: PASS")
    finally:
        server.shutdown()


if __name__ == "__main__":
    main()
