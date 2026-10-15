import os
from pathlib import Path

import sys

sys.path.insert(0, str(Path(__file__).parents[1]))
from rae_guard import validate_runtime_preflight


def main():
    assert os.access("/tmp", os.W_OK)
    denied = []
    for path in ("/etc/rae-canary", "/opt/rae-canary"):
        try:
            Path(path).write_text("canary")
        except OSError:
            denied.append(path)
    assert denied == ["/etc/rae-canary", "/opt/rae-canary"]

    env = {
        "RAE_ISOLATION_ATTESTED": "1",
        "RAE_SNAPSHOT_ID": "synthetic-snapshot",
        "RAE_EGRESS_LOG": "/tmp/egress.log",
        "RAE_ARTIFACT_SHA256": "synthetic-hash",
        "ANTHROPIC_API_KEY": "synthetic-secret",
    }
    try:
        validate_runtime_preflight(env, {"127.0.0.1"})
    except ValueError:
        print("permission and secret environment negative tests: PASS")
        return
    raise AssertionError("secret environment variable was accepted")


if __name__ == "__main__":
    main()
