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
                egress_log = []

                def guard_request(route):
                    host = urlparse(route.request.url).hostname
                    egress_log.append({"url": route.request.url, "host": host})
                    if host not in {"127.0.0.1", "localhost"}:
                        route.abort()
                        raise AssertionError(f"blocked unexpected egress host: {host}")
                    route.continue_()

                context.route("**/*", guard_request)
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
            assert egress_log and all(item["host"] in {"127.0.0.1", "localhost"} for item in egress_log)
            artifact_dir = Path(os.environ.get("RAE_ARTIFACT_DIR", directory))
            artifact_dir.mkdir(parents=True, exist_ok=True)
            (artifact_dir / "egress.log").write_text(json.dumps(egress_log, indent=2) + "\n")
            (artifact_dir / "evaluation_report.json").write_text(json.dumps({
                "status": "PASS",
                "scope": "synthetic_browser_har_and_redaction",
                "network_policy": "localhost_only",
                "egress_request_count": len(egress_log),
                "secrets": "synthetic_only",
                "rae_execution": "not_run",
            }, indent=2) + "\n")
            print("synthetic browser HAR capture and redaction: PASS")
    finally:
        server.shutdown()


if __name__ == "__main__":
    main()
