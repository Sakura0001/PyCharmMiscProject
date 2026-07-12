from __future__ import annotations

import re
from pathlib import Path

from .models import AuditReport


SQL_BLOCK_PATTERN = re.compile(r"```sql\s*(.*?)```", re.DOTALL | re.IGNORECASE)
FORBIDDEN_PATTERNS = (
    ("dialect.mysql.auto_increment", re.compile(r"\bAUTO_INCREMENT\b", re.IGNORECASE), "MySQL AUTO_INCREMENT is not PostgreSQL syntax"),
    ("dialect.mysql.charset", re.compile(r"\b(?:DEFAULT\s+)?CHARSET\s*=", re.IGNORECASE), "MySQL table CHARSET clause is not PostgreSQL syntax"),
    ("dialect.mysql.engine", re.compile(r"\bENGINE\s*=", re.IGNORECASE), "MySQL table ENGINE clause is not PostgreSQL syntax"),
    ("dialect.mysql.optimizer_switch", re.compile(r"\boptimizer_switch\b", re.IGNORECASE), "MySQL optimizer_switch is not a PostgreSQL setting"),
)
HOST_COMMAND_PATTERN = re.compile(r"^\s*\\!", re.MULTILINE)


def _scan_text(report: AuditReport, root: Path, path: Path, text: str) -> None:
    for code, pattern, message in FORBIDDEN_PATTERNS:
        for match in pattern.finditer(text):
            line = text.count("\n", 0, match.start()) + 1
            report.error(code, message, path=path, root=root, line=line)
    for match in HOST_COMMAND_PATTERN.finditer(text):
        line = text.count("\n", 0, match.start()) + 1
        report.error(
            "dialect.host_command",
            "psql host commands (\\!) are forbidden in generated or bundled SQL",
            path=path,
            root=root,
            line=line,
        )


def audit_dialect(root: Path | str) -> AuditReport:
    root = Path(root)
    report = AuditReport()
    skill_root = root / "skills" / "pg-sql-generation"
    scanned = 0
    for path in sorted(skill_root.glob("**/*.sql")) if skill_root.exists() else []:
        _scan_text(report, root, path, path.read_text(encoding="utf-8"))
        scanned += 1
    for path in sorted(skill_root.glob("**/*.md")) if skill_root.exists() else []:
        raw_text = path.read_text(encoding="utf-8")
        for match in SQL_BLOCK_PATTERN.finditer(raw_text):
            block = match.group(1)
            prefix_lines = raw_text.count("\n", 0, match.start(1))
            block_report = AuditReport()
            _scan_text(block_report, root, path, block)
            for finding in block_report.findings:
                adjusted_line = finding.line + prefix_lines if finding.line is not None else None
                report.add(
                    finding.severity,
                    finding.code,
                    finding.message,
                    path=path,
                    root=root,
                    line=adjusted_line,
                )
            scanned += 1
    report.summary["sql_sources_scanned"] = scanned
    return report
