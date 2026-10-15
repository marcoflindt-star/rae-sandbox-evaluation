import json
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1]))
from rae_guard import redact_har, validate_runtime_preflight


def test_preflight_rejects_missing_attestation():
    try:
        validate_runtime_preflight({}, {"fixture.test"})
    except ValueError:
        return
    raise AssertionError("missing isolation attestation was accepted")


def test_preflight_rejects_empty_allowlist():
    env = {
        "RAE_ISOLATION_ATTESTED": "1",
        "RAE_SNAPSHOT_ID": "synthetic-snapshot",
        "RAE_EGRESS_LOG": "/tmp/egress.log",
        "RAE_ARTIFACT_SHA256": "synthetic-hash",
    }
    try:
        validate_runtime_preflight(env, set())
    except ValueError:
        return
    raise AssertionError("empty network allowlist was accepted")


def test_har_redaction():
    with tempfile.TemporaryDirectory() as directory:
        source = Path(directory) / "in.har"
        target = Path(directory) / "out.har"
        source.write_text(json.dumps({"log": {"entries": [{"request": {
            "url": "https://fixture.test/api?token=canary",
            "headers": [{"name": "Authorization", "value": "Bearer canary"}],
            "cookies": [{"name": "sid", "value": "canary"}],
        }}]}}))
        redact_har(source, target)
        result = json.loads(target.read_text())
        request = result["log"]["entries"][0]["request"]
        assert "token=canary" not in request["url"]
        assert request["headers"][0]["value"] == "[REDACTED]"
        assert request["cookies"][0]["value"] == "[REDACTED]"


if __name__ == "__main__":
    test_preflight_rejects_missing_attestation()
    test_preflight_rejects_empty_allowlist()
    test_har_redaction()
    print("synthetic guard tests: PASS")
