import hashlib
import json


def manifest():
    fixtures = {
        "egress.log": "synthetic-run-001 localhost\n",
        "evaluation.json": {"status": "PASS", "scope": "synthetic"},
    }
    canonical = json.dumps(fixtures, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode()).hexdigest()


def main():
    first = manifest()
    second = manifest()
    assert first == second
    assert len(first) == 64
    print(f"reproducibility manifest test: PASS ({first})")


if __name__ == "__main__":
    main()
