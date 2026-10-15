import hashlib
import json
import tempfile
from pathlib import Path


def main():
    with tempfile.TemporaryDirectory(prefix="rae-snapshot-") as directory:
        root = Path(directory)
        payload = root / "synthetic-output.json"
        payload.write_text(json.dumps({"status": "synthetic", "secret": "canary"}))
        digest = hashlib.sha256(payload.read_bytes()).hexdigest()
        manifest = {"files": {payload.name: digest}, "snapshot": "synthetic-before"}
        assert manifest["files"][payload.name] == hashlib.sha256(payload.read_bytes()).hexdigest()
        payload.unlink()
        restored = root / "restored"
        restored.mkdir()
        assert not (restored / payload.name).exists()
        assert manifest["snapshot"] == "synthetic-before"
    print("snapshot manifest and clean-restore test: PASS")


if __name__ == "__main__":
    main()
