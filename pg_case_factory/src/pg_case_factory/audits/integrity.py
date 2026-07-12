from __future__ import annotations

import csv
from collections.abc import Mapping
from pathlib import Path

import yaml

from ._documents import UniqueKeySafeLoader, statement_paths
from .models import AuditReport


def _load_yaml(path: Path, report: AuditReport, root: Path):
    try:
        return yaml.load(path.read_text(encoding="utf-8"), Loader=UniqueKeySafeLoader)
    except (OSError, yaml.YAMLError) as exc:
        report.error(
            "repository.invalid_yaml",
            f"required repository YAML cannot be parsed: {exc}",
            path=path,
            root=root,
        )
        return None


def audit_repository_integrity(root: Path | str) -> AuditReport:
    """Fail closed when the expected PG18.4 corpus is absent or stale."""

    root = Path(root)
    report = AuditReport()
    required = (
        root / "pyproject.toml",
        root / "skills/pg-sql-generation/SKILL.md",
        root / "skills/pg-sql-generation/references/statements",
        root / "skills/pg-sql-generation/references/combinations",
        root / "skills/pg-sql-generation/references/common/compatibility_profile.yaml",
        root / "skills/pg-sql-generation/references/common/statement_support_inventory.yaml",
        root / "skills/pg-sql-generation/references/common/pg18_type_catalog.md",
        root
        / "skills/pg-sql-generation/references/common/postgresql_18_4_factor_audit.tsv",
    )
    for path in required:
        if not path.exists():
            report.error(
                "repository.required_path_missing",
                "required PG18.4 project path is missing",
                path=path,
                root=root,
            )

    statements = statement_paths(root)
    matrices_root = root / "skills/pg-sql-generation/references/combinations"
    matrices = (
        [
            path
            for path in sorted(matrices_root.glob("**/*.yaml"))
            if "_shared" not in path.relative_to(matrices_root).parts
        ]
        if matrices_root.exists()
        else []
    )
    if not statements:
        report.error(
            "repository.statement_corpus_empty",
            "statement reference corpus must not be empty",
            path=matrices_root.parent / "statements",
            root=root,
        )
    if not matrices:
        report.error(
            "repository.matrix_corpus_empty",
            "statement combination matrix corpus must not be empty",
            path=matrices_root,
            root=root,
        )
    if statements and matrices and len(statements) != len(matrices):
        report.error(
            "repository.statement_matrix_count_mismatch",
            f"statement/matrix corpus must be one-to-one: statements={len(statements)} matrices={len(matrices)}",
            path=matrices_root,
            root=root,
        )

    support_path = root / "skills/pg-sql-generation/references/common/statement_support_inventory.yaml"
    ledger_path = (
        root
        / "skills/pg-sql-generation/references/common/postgresql_18_4_factor_audit.tsv"
    )
    if support_path.is_file():
        support = _load_yaml(support_path, report, root)
        summary = dict(support.get("summary") or {}) if isinstance(support, Mapping) else {}
        expected = len(statements)
        if summary.get("statements") != expected:
            report.error(
                "repository.support_inventory_statement_mismatch",
                f"support inventory statements={summary.get('statements')!r}, expected {expected}",
                path=support_path,
                root=root,
            )
        if summary.get("static_catalog_ready") != expected or summary.get(
            "pending_static_review"
        ) != 0:
            report.error(
                "repository.static_catalog_not_ready",
                "all statement catalogs must be statically reviewed with zero pending entries",
                path=support_path,
                root=root,
            )
        if "runtime_verified_statements" not in summary:
            report.error(
                "repository.runtime_verification_metric_missing",
                "support inventory must report runtime verification separately",
                path=support_path,
                root=root,
            )
        expected_rows = summary.get("statement_factor_value_rows")
        if ledger_path.is_file() and isinstance(expected_rows, int):
            try:
                with ledger_path.open(encoding="utf-8", newline="") as handle:
                    row_count = sum(1 for _ in csv.DictReader(handle, delimiter="\t"))
            except OSError as exc:
                report.error(
                    "repository.factor_ledger_unreadable",
                    str(exc),
                    path=ledger_path,
                    root=root,
                )
            else:
                if row_count != expected_rows:
                    report.error(
                        "repository.factor_ledger_count_mismatch",
                        f"factor ledger rows={row_count}, expected {expected_rows}",
                        path=ledger_path,
                        root=root,
                    )

    report.summary.update(
        {
            "integrity_statement_count": len(statements),
            "integrity_matrix_count": len(matrices),
        }
    )
    return report


__all__ = ["audit_repository_integrity"]
