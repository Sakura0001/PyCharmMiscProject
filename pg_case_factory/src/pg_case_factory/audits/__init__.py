from __future__ import annotations

from pathlib import Path

from .assets import audit_assets
from .capabilities import CAPABILITY_LEVELS, audit_capabilities
from .dialect import audit_dialect
from .integrity import audit_repository_integrity
from .models import AuditFinding, AuditReport, CapabilityRecord
from .placeholders import audit_placeholders, template_fields
from .statements import audit_statement_references


def audit_repository(root: Path | str) -> AuditReport:
    root = Path(root)
    report = AuditReport()
    reports = (
        audit_repository_integrity(root),
        audit_statement_references(root),
        audit_placeholders(root),
        audit_dialect(root),
        audit_assets(root),
        audit_capabilities(root),
    )
    for item in reports:
        report.extend(item)
    report.summary.update(
        {
            "error_count": len(report.errors),
            "warning_count": len(report.warnings),
            "capability_count": len(report.capabilities),
        }
    )
    return report


__all__ = [
    "AuditFinding",
    "AuditReport",
    "CAPABILITY_LEVELS",
    "CapabilityRecord",
    "audit_assets",
    "audit_capabilities",
    "audit_dialect",
    "audit_repository_integrity",
    "audit_placeholders",
    "audit_repository",
    "audit_statement_references",
    "template_fields",
]
