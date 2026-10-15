from pathlib import Path


def main():
    compose = (Path(__file__).parents[1] / "docker-compose.yml").read_text()
    for marker in (
        "read_only: true",
        "cap_drop:",
        "network_mode: none",
        "user: \"65532:65532\"",
        "RAE_EXECUTION_CONFIRMATION: \"\"",
    ):
        assert marker in compose
    for marker in ("privileged: true", "docker.sock", "network_mode: host"):
        assert marker not in compose
    print("container permission policy contract: PASS")


if __name__ == "__main__":
    main()
