from __future__ import annotations

import json
import os
import re
from pathlib import Path
from urllib.parse import urlsplit

FORBIDDEN = ("@latest", "npm install", "npm i ", "npx ", "pip install", "uv pip", "--auto-install", "--autoconnect", "docker.sock")
SECRET_ENV = re.compile(r"(API_KEY|TOKEN|PASSWORD|SECRET|PRIVATE_KEY|CREDENTIAL|COOKIE|AUTH)", re.I)
REDACT_HEADERS = re.compile(r"^(authorization|proxy-authorization|cookie|set-cookie|x-api-key|x-auth-token)$", re.I)


def validate_command(argv: list[str], env: dict[str, str], allowed_hosts: set[str]) -> None:
    joined = " ".join(argv).lower()
    hits = [needle for needle in FORBIDDEN if needle in joined]
    if hits:
        raise ValueError(f"blocked command patterns: {', '.join(hits)}")
    leaked = sorted(name for name in env if SECRET_ENV.search(name))
    if leaked:
        raise ValueError(f"blocked secret-like environment variables: {', '.join(leaked)}")
    if not allowed_hosts:
        raise ValueError("no network allowlist configured")


def validate_runtime_preflight(env: dict[str, str], allowed_hosts: set[str]) -> None:
    required = {"RAE_ISOLATION_ATTESTED": "1", "RAE_SNAPSHOT_ID": None, "RAE_EGRESS_LOG": None, "RAE_ARTIFACT_SHA256": None}
    for name, expected in required.items():
        value = env.get(name, "").strip()
        if not value or (expected is not None and value != expected):
            raise ValueError(f"missing runtime attestation: {name}")
    if not allowed_hosts:
        raise ValueError("network allowlist is empty")
    if env.get("RAE_MOUNTS") or env.get("DOCKER_HOST", "").endswith("docker.sock") or env.get("SSH_AUTH_SOCK"):
        raise ValueError("host mount or host socket exposed")
    validate_command(["rae-runtime"], env, allowed_hosts)


def redact_har(source: Path, destination: Path) -> None:
    document = json.loads(source.read_text(encoding="utf-8"))
    for entry in document.get("log", {}).get("entries", []):
        request = entry.get("request", {})
        response = entry.get("response", {})
        for message in (request, response):
            for header in message.get("headers", []):
                if REDACT_HEADERS.match(str(header.get("name", ""))):
                    header["value"] = "[REDACTED]"
        for cookie in request.get("cookies", []) + response.get("cookies", []):
            cookie["value"] = "[REDACTED]"
        if isinstance(request.get("url"), str):
            parts = urlsplit(request["url"])
            request["url"] = parts._replace(query="", fragment="").geturl()
            request["queryString"] = []
    destination.write_text(json.dumps(document, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
