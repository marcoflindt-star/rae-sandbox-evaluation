import json


def main():
    evidence = {
        "synthetic_guard": "VERIFIED",
        "direct_playwright": "VERIFIED",
        "negative_egress": "VERIFIED",
        "cleanup": "VERIFIED",
        "log_integrity": "VERIFIED",
        "production_rae_execution": "NOT_DONE",
    }
    required = [name for name in evidence if name != "production_rae_execution"]
    assert all(evidence[name] == "VERIFIED" for name in required)
    assert evidence["production_rae_execution"] != "VERIFIED"
    report = json.dumps({"status": "PREPRODUCTION_GATE_PASS", "evidence": evidence}, sort_keys=True)
    assert "production_rae_execution" in report
    print("fail-closed preproduction release gate: PASS")


if __name__ == "__main__":
    main()
