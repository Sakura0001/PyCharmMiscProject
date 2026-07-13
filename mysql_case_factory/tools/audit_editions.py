from __future__ import annotations

import json
from pathlib import Path

from mysql_case_factory.editions import load_edition
from mysql_case_factory.knowledge_audit import audit_edition_knowledge
from mysql_case_factory.version_delta import audit_version_delta


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    reports = []
    ok = True
    for directory in ("mysql_8_0_22", "mysql_8_0_41"):
        edition_root = root / "editions" / directory
        try:
            edition = load_edition(edition_root, repository_root=root, verify_files=True)
            report = audit_edition_knowledge(edition_root)
            payload = {"manifest": edition.edition_id, **report.to_dict()}
            ok = ok and report.ok
        except (OSError, ValueError) as exc:
            payload = {"manifest": directory, "ok": False, "errors": [str(exc)]}
            ok = False
        reports.append(payload)
    delta = audit_version_delta(
        root / "editions/mysql_8_0_22",
        root / "editions/mysql_8_0_41",
        root / "editions/mysql_8_0_41/version_delta_from_8_0_22.tsv",
    )
    ok = ok and delta.ok
    print(json.dumps({"ok": ok, "editions": reports, "version_delta": delta.to_dict()}, indent=2))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
