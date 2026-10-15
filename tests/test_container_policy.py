from pathlib import Path


ROOT = Path(__file__).parents[1]
COMPOSE = (ROOT / "docker-compose.yml").read_text()


def test_container_policy_is_fail_closed():
    required = [
        "network_mode: none",
        "read_only: true",
        "cap_drop:",
        "no-new-privileges:true",
        "user: \"65532:65532\"",
        "RAE_ALLOWED_HOSTS: \"\"",
        "RAE_EXECUTION_CONFIRMATION: \"\"",
    ]
    for marker in required:
        assert marker in COMPOSE


def test_container_policy_has_no_host_mounts_or_privileged_mode():
    forbidden = ["privileged: true", "docker.sock", "/var/run", "network_mode: host"]
    for marker in forbidden:
        assert marker not in COMPOSE
