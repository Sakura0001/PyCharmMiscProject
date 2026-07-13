#!/usr/bin/env python3
"""Verify the four Docker smoke endpoints have exact versions and identities."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
COMPOSE = ROOT / "docker-compose.smoke.yml"
EXPECTED = {
    "mysql8022-reference": "8.0.22",
    "mysql8022-candidate": "8.0.22",
    "mysql8041-reference": "8.0.41",
    "mysql8041-candidate": "8.0.41",
}


def probe(service: str) -> dict[str, str]:
    command = [
        "docker",
        "compose",
        "-f",
        str(COMPOSE),
        "exec",
        "-T",
        service,
        "sh",
        "-c",
        'MYSQL_PWD="$MYSQL_ROOT_PASSWORD" mysql -uroot --batch '
        "--skip-column-names -e \"SELECT @@version, @@server_uuid\"",
    ]
    completed = subprocess.run(command, check=True, capture_output=True, text=True)
    fields = completed.stdout.strip().split("\t")
    if len(fields) != 2:
        raise RuntimeError(f"{service} returned an invalid identity row")
    return {"service": service, "version": fields[0], "server_uuid": fields[1]}


def main() -> int:
    identities = [probe(service) for service in EXPECTED]
    errors = []
    for identity in identities:
        expected = EXPECTED[identity["service"]]
        if identity["version"] != expected:
            errors.append(
                f"{identity['service']} expected {expected}, got {identity['version']}"
            )
    uuids = [identity["server_uuid"] for identity in identities]
    if len(set(uuids)) != len(uuids):
        errors.append("smoke endpoints must expose four distinct server UUIDs")
    print(json.dumps({"ok": not errors, "identities": identities, "errors": errors}, indent=2))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
