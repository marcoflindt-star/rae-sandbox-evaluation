import http.server
import json
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
        if self.path == "/":
            body = b"<body>synthetic fixture</body>"
            content_type = "text/html"
        elif self.path.startswith("/api/data"):
            body = b'{"result":"synthetic"}'
            content_type = "application/json"
        else:
            self.send_error(404)
            return
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Set-Cookie", "fixture_session=canary")
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
                browser = playwright.chromium.launch(headless=True, args=["--disable-background-networking", "--no-first-run"])
                context = browser.new_context(record_har_path=str(raw), record_har_content="embed")
                page = context.new_page()
                page.goto(f"http://127.0.0.1:{server.server_port}/", wait_until="networkidle")
                page.evaluate("fetch('/api/data?token=canary', {headers: {Authorization: 'Bearer canary'}})")
                context.close()
                browser.close()
            redact_har(raw, redacted)
            document = json.loads(redacted.read_text())
            serialized = json.dumps(document)
            assert "Bearer canary" not in serialized
            assert "fixture_session=canary" not in serialized
            assert "token=canary" not in serialized
            assert "127.0.0.1" in serialized
            print("synthetic browser HAR capture and redaction: PASS")
    finally:
        server.shutdown()


if __name__ == "__main__":
    main()
