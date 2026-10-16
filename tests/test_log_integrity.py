import hashlib
import json


def digest(record):
    body = {key: record[key] for key in ("run_id", "sequence", "previous_hash", "event")}
    return hashlib.sha256(json.dumps(body, sort_keys=True).encode()).hexdigest()


def verify(records):
    seen = set()
    previous = "0" * 64
    for record in records:
        assert record["sequence"] not in seen
        assert record["previous_hash"] == previous
        assert record["hash"] == digest(record)
        seen.add(record["sequence"])
        previous = record["hash"]


def main():
    records = []
    previous = "0" * 64
    for sequence, event in enumerate(("start", "egress", "finish"), start=1):
        record = {
            "run_id": "synthetic-run-001",
            "sequence": sequence,
            "previous_hash": previous,
            "event": event,
        }
        record["hash"] = digest(record)
        records.append(record)
        previous = record["hash"]
    verify(records)

    tampered = [dict(record) for record in records]
    tampered[1]["event"] = "external-egress"
    try:
        verify(tampered)
    except AssertionError:
        pass
    else:
        raise AssertionError("tampered event was accepted")

    duplicate = [dict(record) for record in records]
    duplicate[2]["sequence"] = 2
    try:
        verify(duplicate)
    except AssertionError:
        pass
    else:
        raise AssertionError("duplicate sequence was accepted")
    print("log integrity, run correlation, duplicate and tamper tests: PASS")


if __name__ == "__main__":
    main()
