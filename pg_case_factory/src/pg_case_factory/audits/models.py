from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class AuditFinding:
    severity: str
    code: str
    message: str
    path: str = ""
    line: int | None = None

    def to_dict(self) -> dict[str, Any]:
        result: dict[str, Any] = {
            "severity": self.severity,
            "code": self.code,
            "message": self.message,
        }
        if self.path:
            result["path"] = self.path
        if self.line is not None:
            result["line"] = self.line
        return result


@dataclass(frozen=True)
class CapabilityRecord:
    statement_key: str
    level: str
    path: str
    reasons: tuple[str, ...] = ()
    evidence: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "statement_key": self.statement_key,
            "level": self.level,
            "path": self.path,
            "reasons": list(self.reasons),
            "evidence": list(self.evidence),
        }


@dataclass
class AuditReport:
    findings: list[AuditFinding] = field(default_factory=list)
    capabilities: list[CapabilityRecord] = field(default_factory=list)
    summary: dict[str, Any] = field(default_factory=dict)

    @property
    def errors(self) -> list[AuditFinding]:
        return [item for item in self.findings if item.severity == "error"]

    @property
    def warnings(self) -> list[AuditFinding]:
        return [item for item in self.findings if item.severity == "warning"]

    @property
    def ok(self) -> bool:
        return not self.errors

    def add(
        self,
        severity: str,
        code: str,
        message: str,
        *,
        path: Path | str | None = None,
        root: Path | None = None,
        line: int | None = None,
    ) -> None:
        normalized_path = ""
        if path is not None:
            candidate = Path(path)
            if root is not None:
                try:
                    candidate = candidate.resolve().relative_to(root.resolve())
                except ValueError:
                    pass
            normalized_path = candidate.as_posix()
        finding = AuditFinding(
            severity=severity,
            code=code,
            message=message,
            path=normalized_path,
            line=line,
        )
        if finding not in self.findings:
            self.findings.append(finding)

    def error(self, code: str, message: str, **kwargs: Any) -> None:
        self.add("error", code, message, **kwargs)

    def warning(self, code: str, message: str, **kwargs: Any) -> None:
        self.add("warning", code, message, **kwargs)

    def extend(self, other: "AuditReport") -> None:
        for finding in other.findings:
            if finding not in self.findings:
                self.findings.append(finding)
        by_statement = {item.statement_key: item for item in self.capabilities}
        for capability in other.capabilities:
            by_statement[capability.statement_key] = capability
        self.capabilities = sorted(by_statement.values(), key=lambda item: item.statement_key)
        self.summary.update(other.summary)

    def to_dict(self) -> dict[str, Any]:
        return {
            "errors": [item.to_dict() for item in self.errors],
            "warnings": [item.to_dict() for item in self.warnings],
            "capabilities": [item.to_dict() for item in self.capabilities],
            "summary": dict(self.summary),
            "ok": self.ok,
        }
