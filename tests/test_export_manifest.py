import hashlib
import json
import tempfile
from pathlib import Path


def main():
    with tempfile.TemporaryDirectory(prefix="rae-export-") as directory:
        root = Path(directory)
        artifacts = {"egress.log": "synthetic-run-001 localhost\n", "report.json": '{"status":"PASS"}\n'}
        for name, content in artifacts.items():
            (root / name).write_text(content)
        manifest = {"schema": 1, "run_id": "synthetic-run-001", "files": {}}
        for name in sorted(artifacts):
            manifest["files"][name] = hashlib.sha256((root / name).read_bytes()).hexdigest()
        encoded = json.dumps(manifest, sort_keys=True)
        assert json.loads(encoded)["run_id"] == "synthetic-run-001"
        (root / "manifest.json").write_text(encoded + "\n")
        for name, expected in manifest["files"].items():
            assert hashlib.sha256((root / name).read_bytes()).hexdigest() == expected
        (root / "report.json").write_text('{"status":"TAMPERED"}\n')
        assert hashlib.sha256((root / "report.json").read_bytes()).hexdigest() != manifest["files"]["report.json"]
    print("artifact export manifest integrity test: PASS")


if __name__ == "__main__":
    main()
