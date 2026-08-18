"""Deterministic inventory and progress ledger for the statement-factor cycle.

The ledger deliberately separates *declared coverage* from generated SQL.  A
statement can only move from pending to completed in inventory order and only
after a machine-readable validation record says that the generated package
passed.  This makes the Markdown checklist a rendered view of evidence rather
than a manually editable claim.
"""

from __future__ import annotations

import hashlib
import json
import os
import tempfile
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any, Mapping

import yaml

from .applicability import (
    ApplicabilityValidationError,
    audit_universe_matrix_witness_coverage,
    load_shipped_applicability_universe,
)


_SCHEMA_VERSION = 1
_INVENTORY_PATH = Path(
    "skills/pg-sql-generation/references/common/statement_support_inventory.yaml"
)
_MATRIX_ROOT = Path("skills/pg-sql-generation/references/combinations")
_SKILL_ROOT = Path("skills/pg-sql-generation")
_RETAINED_PACKAGES = {
    "close": "artifacts/regress/cursor-factor-full-v1",
    "declare": "artifacts/regress/cursor-factor-full-v1",
    "fetch": "artifacts/regress/cursor-factor-full-v1",
    "move": "artifacts/regress/cursor-factor-full-v1",
    "grant": "artifacts/regress/dcl-factor-full-v1",
    "revoke": "artifacts/regress/dcl-factor-full-v1",
}


class StatementFactorCycleError(ValueError):
    """Raised when the inventory or its sequential progress is inconsistent."""


@dataclass(frozen=True)
class StatementFactorDefinition:
    name: str
    tier: str
    coverage_role: str
    values: tuple[str, ...]
    row_ids: tuple[str, ...]
    matrix_bindings: tuple[str, ...]
    witness_ids: tuple[str, ...]

    def __post_init__(self) -> None:
        lengths = {
            len(self.values),
            len(self.row_ids),
            len(self.matrix_bindings),
            len(self.witness_ids),
        }
        if len(lengths) != 1:
            raise StatementFactorCycleError(
                f"factor {self.name} canonical value metadata differs in length"
            )
        if not set(self.matrix_bindings) <= {
            "factor_contract",
            "pg18_compatibility",
        }:
            raise StatementFactorCycleError(
                f"factor {self.name} has an unsupported matrix binding"
            )


@dataclass(frozen=True)
class StatementCycleEntry:
    ordinal: int
    statement_key: str
    category: str
    domain: str
    matrix_path: Path
    reference_path: Path
    official_source: str
    support_status: str
    factor_count: int
    factor_value_count: int
    factors: tuple[StatementFactorDefinition, ...]
    matrix_sha256: str
    reference_sha256: str
    retained_package: str | None = None

    @property
    def is_retained(self) -> bool:
        return self.retained_package is not None


@dataclass(frozen=True)
class StatementFactorCycleSnapshot:
    repository_root: Path
    entries: tuple[StatementCycleEntry, ...]
    fingerprint: str
    inventory_sha256: str
    universe_semantic_sha256: str

    @property
    def retained_entries(self) -> tuple[StatementCycleEntry, ...]:
        return tuple(entry for entry in self.entries if entry.is_retained)

    @property
    def pending_entries(self) -> tuple[StatementCycleEntry, ...]:
        return tuple(entry for entry in self.entries if not entry.is_retained)

    @property
    def statement_count(self) -> int:
        return len(self.entries)

    @property
    def factor_count(self) -> int:
        return sum(entry.factor_count for entry in self.entries)

    @property
    def factor_value_count(self) -> int:
        return sum(entry.factor_value_count for entry in self.entries)

    @property
    def retained_statement_count(self) -> int:
        return len(self.retained_entries)

    @property
    def pending_statement_count(self) -> int:
        return len(self.pending_entries)

    @property
    def pending_factor_count(self) -> int:
        return sum(entry.factor_count for entry in self.pending_entries)

    @property
    def pending_factor_value_count(self) -> int:
        return sum(entry.factor_value_count for entry in self.pending_entries)

    @property
    def pg18_compatibility_value_count(self) -> int:
        return sum(
            binding == "pg18_compatibility"
            for entry in self.entries
            for factor in entry.factors
            for binding in factor.matrix_bindings
        )

    @property
    def pending_pg18_compatibility_value_count(self) -> int:
        return sum(
            binding == "pg18_compatibility"
            for entry in self.pending_entries
            for factor in entry.factors
            for binding in factor.matrix_bindings
        )


@dataclass(frozen=True)
class StatementFactorCycleState:
    document: Mapping[str, Any]

    @property
    def next_pending_statement(self) -> str | None:
        value = self.document.get("next_pending_statement")
        return value if isinstance(value, str) else None


def _load_yaml_mapping(path: Path, location: str) -> dict[str, Any]:
    if path.is_symlink() or not path.is_file():
        raise StatementFactorCycleError(f"{location} is missing: {path}")
    try:
        document = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, yaml.YAMLError) as exc:
        raise StatementFactorCycleError(f"cannot read {location}: {exc}") from exc
    if not isinstance(document, dict):
        raise StatementFactorCycleError(f"{location} must contain a YAML mapping")
    return document


def _load_json_mapping(path: Path, location: str) -> dict[str, Any]:
    if path.is_symlink() or not path.is_file():
        raise StatementFactorCycleError(f"{location} is missing: {path}")
    try:
        document = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise StatementFactorCycleError(f"cannot read {location}: {exc}") from exc
    if not isinstance(document, dict):
        raise StatementFactorCycleError(f"{location} must contain a JSON object")
    return document


def _write_json_atomic(path: Path, document: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = (
        json.dumps(document, ensure_ascii=False, indent=2, sort_keys=False) + "\n"
    ).encode("utf-8")
    descriptor, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    except BaseException:
        try:
            os.unlink(temporary)
        except FileNotFoundError:
            pass
        raise


def _write_text_atomic(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = text.encode("utf-8")
    descriptor, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    except BaseException:
        try:
            os.unlink(temporary)
        except FileNotFoundError:
            pass
        raise


def _required_text(value: Any, location: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise StatementFactorCycleError(f"{location} must be a non-empty string")
    return value.strip()


def _required_count(value: Any, location: str) -> int:
    if type(value) is not int or value < 0:
        raise StatementFactorCycleError(f"{location} must be a non-negative integer")
    return value


def _factor_value(value: Any) -> str:
    if isinstance(value, str):
        return value
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        return str(value)
    return yaml.safe_dump(value, default_flow_style=True, sort_keys=True).strip()


def _file_sha256(path: Path) -> str:
    try:
        return hashlib.sha256(path.read_bytes()).hexdigest()
    except OSError as exc:
        raise StatementFactorCycleError(f"cannot hash input file {path}: {exc}") from exc


def _snapshot_fingerprint(
    entries: tuple[StatementCycleEntry, ...],
    inventory_sha256: str,
    universe_semantic_sha256: str,
) -> str:
    document = {
        "inventory_sha256": inventory_sha256,
        "universe_semantic_sha256": universe_semantic_sha256,
        "entries": [
            {
                "statement_key": entry.statement_key,
                "matrix_path": entry.matrix_path.as_posix(),
                "reference_path": entry.reference_path.as_posix(),
                "factors": [
                    {
                        "name": factor.name,
                        "values": list(factor.values),
                        "row_ids": list(factor.row_ids),
                        "matrix_bindings": list(factor.matrix_bindings),
                        "witness_ids": list(factor.witness_ids),
                    }
                    for factor in entry.factors
                ],
                "matrix_sha256": entry.matrix_sha256,
                "reference_sha256": entry.reference_sha256,
            }
            for entry in entries
        ],
    }
    payload = json.dumps(
        document, ensure_ascii=False, separators=(",", ":"), sort_keys=True
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def discover_statement_factor_cycle(
    repository_root: Path,
) -> StatementFactorCycleSnapshot:
    """Discover and cross-check all statement matrices in inventory order."""

    return _discover_statement_factor_cycle_cached(
        str(repository_root.resolve(strict=True))
    )


@lru_cache(maxsize=8)
def _discover_statement_factor_cycle_cached(
    resolved_repository_root: str,
) -> StatementFactorCycleSnapshot:
    """Cached implementation keyed by one canonical repository path."""

    root = Path(resolved_repository_root)
    try:
        universe = load_shipped_applicability_universe(root)
        witness_audit = audit_universe_matrix_witness_coverage(
            universe,
            repository_root=root,
        )
    except ApplicabilityValidationError as exc:
        raise StatementFactorCycleError(
            f"canonical applicability universe is invalid: {exc}"
        ) from exc
    if not witness_audit.complete:
        raise StatementFactorCycleError(
            "canonical applicability rows lack matrix witnesses: "
            + json.dumps(witness_audit.to_dict(), ensure_ascii=False, sort_keys=True)
        )

    inventory = _load_yaml_mapping(root / _INVENTORY_PATH, "statement inventory")
    inventory_rows = inventory.get("statements")
    if not isinstance(inventory_rows, list):
        raise StatementFactorCycleError("statement inventory.statements must be a list")

    matrices: dict[str, tuple[Path, dict[str, Any]]] = {}
    for absolute_path in sorted((root / _MATRIX_ROOT).rglob("*.yaml")):
        document = _load_yaml_mapping(absolute_path, "statement matrix")
        if document.get("kind") != "statement_combination_matrix":
            continue
        statement = document.get("statement")
        if not isinstance(statement, dict):
            raise StatementFactorCycleError(
                f"statement matrix has no statement mapping: {absolute_path}"
            )
        key = _required_text(statement.get("key"), f"{absolute_path}: statement.key")
        if key in matrices:
            raise StatementFactorCycleError(f"duplicate statement matrix for {key}")
        matrices[key] = (absolute_path.relative_to(root), document)

    entries: list[StatementCycleEntry] = []
    seen_keys: set[str] = set()
    for ordinal, support_row in enumerate(inventory_rows, start=1):
        if not isinstance(support_row, dict):
            raise StatementFactorCycleError(
                f"statement inventory row {ordinal} must be a mapping"
            )
        key = _required_text(
            support_row.get("statement_key"),
            f"statement inventory row {ordinal}.statement_key",
        )
        if key in seen_keys:
            raise StatementFactorCycleError(f"duplicate statement inventory row for {key}")
        seen_keys.add(key)
        try:
            matrix_path, matrix = matrices[key]
        except KeyError as exc:
            raise StatementFactorCycleError(f"missing statement matrix for {key}") from exc

        statement = matrix["statement"]
        factor_contract = matrix.get("factor_contract")
        if not isinstance(factor_contract, dict) or not isinstance(
            factor_contract.get("factors"), dict
        ):
            raise StatementFactorCycleError(f"{key} has no factor_contract.factors")

        canonical_rows = universe.rows_for_statement(key)
        if not canonical_rows:
            raise StatementFactorCycleError(
                f"canonical applicability universe has no rows for {key}"
            )
        canonical_source = canonical_rows[0].source_reference
        canonical_by_factor: dict[str, list[Any]] = {}
        for canonical_row in canonical_rows:
            canonical_by_factor.setdefault(canonical_row.factor, []).append(canonical_row)
        matrix_factors = factor_contract["factors"]
        if set(canonical_by_factor) != set(matrix_factors):
            missing = sorted(set(canonical_by_factor) - set(matrix_factors))
            unexpected_factors = sorted(set(matrix_factors) - set(canonical_by_factor))
            raise StatementFactorCycleError(
                f"{key} factor names differ between canonical ledger and matrix: "
                f"missing={missing}, unexpected={unexpected_factors}"
            )

        factors: list[StatementFactorDefinition] = []
        for factor_name, canonical_factor_rows in canonical_by_factor.items():
            factor_document = matrix_factors[factor_name]
            if not isinstance(factor_document, dict):
                raise StatementFactorCycleError(
                    f"{key}.{factor_name} factor must be a mapping"
                )
            canonical_tiers = {row.tier for row in canonical_factor_rows}
            if len(canonical_tiers) != 1:
                raise StatementFactorCycleError(
                    f"{key}.{factor_name} has inconsistent tiers in canonical ledger"
                )
            canonical_tier = next(iter(canonical_tiers))
            matrix_tier = _required_text(
                factor_document.get("tier"), f"{key}.{factor_name}.tier"
            )
            if matrix_tier != canonical_tier:
                raise StatementFactorCycleError(
                    f"{key}.{factor_name} tier differs between canonical ledger "
                    f"({canonical_tier}) and matrix ({matrix_tier})"
                )
            required_values = factor_document.get("required_values")
            if not isinstance(required_values, list) or not required_values:
                raise StatementFactorCycleError(
                    f"{key}.{factor_name}.required_values must be a non-empty list"
                )
            matrix_required_values = {
                _factor_value(value) for value in required_values
            }
            matrix_bindings = tuple(
                (
                    "factor_contract"
                    if row.value in matrix_required_values
                    else "pg18_compatibility"
                )
                for row in canonical_factor_rows
            )
            witness_ids = tuple(
                witness_audit.witnesses[row.row_id].combination_group_id
                for row in canonical_factor_rows
            )
            factors.append(
                StatementFactorDefinition(
                    name=_required_text(factor_name, f"{key} factor name"),
                    tier=canonical_tier,
                    coverage_role=_required_text(
                        factor_document.get("coverage_role"),
                        f"{key}.{factor_name}.coverage_role",
                    ),
                    values=tuple(row.value for row in canonical_factor_rows),
                    row_ids=tuple(row.row_id for row in canonical_factor_rows),
                    matrix_bindings=matrix_bindings,
                    witness_ids=witness_ids,
                )
            )

        factor_count = len(factors)
        factor_value_count = sum(len(factor.values) for factor in factors)
        declared_factor_count = _required_count(
            support_row.get("factor_count"), f"{key}.factor_count"
        )
        declared_value_count = _required_count(
            support_row.get("factor_value_rows"), f"{key}.factor_value_rows"
        )
        if factor_count != declared_factor_count:
            raise StatementFactorCycleError(
                f"{key} factor count mismatch: inventory={declared_factor_count}, "
                f"matrix={factor_count}"
            )
        if factor_value_count != declared_value_count:
            raise StatementFactorCycleError(
                f"{key} factor value count mismatch: inventory={declared_value_count}, "
                f"matrix={factor_value_count}"
            )

        source_reference = _required_text(
            statement.get("source_reference"), f"{key}.statement.source_reference"
        )
        if (
            source_reference != support_row.get("source_reference")
            or source_reference != canonical_source
        ):
            raise StatementFactorCycleError(
                f"{key} source reference differs across inventory, matrix, and canonical ledger"
            )
        reference_path = _SKILL_ROOT / source_reference
        if not (root / reference_path).is_file():
            raise StatementFactorCycleError(
                f"official statement reference is missing for {key}: {reference_path}"
            )

        entries.append(
            StatementCycleEntry(
                ordinal=ordinal,
                statement_key=key,
                category=_required_text(statement.get("category"), f"{key}.category"),
                domain=_required_text(statement.get("domain"), f"{key}.domain"),
                matrix_path=matrix_path,
                reference_path=reference_path,
                official_source=_required_text(
                    statement.get("official_source"), f"{key}.official_source"
                ),
                support_status=_required_text(
                    support_row.get("support_status"), f"{key}.support_status"
                ),
                factor_count=factor_count,
                factor_value_count=factor_value_count,
                factors=tuple(factors),
                matrix_sha256=_file_sha256(root / matrix_path),
                reference_sha256=_file_sha256(root / reference_path),
                retained_package=_RETAINED_PACKAGES.get(key),
            )
        )

    unexpected = sorted(set(matrices) - seen_keys)
    if unexpected:
        raise StatementFactorCycleError(
            "statement matrices absent from inventory: " + ", ".join(unexpected)
        )

    result = tuple(entries)
    summary = inventory.get("summary")
    if not isinstance(summary, dict):
        raise StatementFactorCycleError("statement inventory.summary must be a mapping")
    expected_totals = {
        "statements": len(result),
        "statement_factor_pairs": sum(entry.factor_count for entry in result),
        "statement_factor_value_rows": sum(
            entry.factor_value_count for entry in result
        ),
    }
    for field, actual in expected_totals.items():
        declared = _required_count(summary.get(field), f"inventory.summary.{field}")
        if declared != actual:
            raise StatementFactorCycleError(
                f"inventory summary mismatch for {field}: "
                f"declared={declared}, discovered={actual}"
            )

    inventory_sha256 = _file_sha256(root / _INVENTORY_PATH)
    return StatementFactorCycleSnapshot(
        repository_root=root,
        entries=result,
        fingerprint=_snapshot_fingerprint(
            result,
            inventory_sha256,
            universe.semantic_sha256,
        ),
        inventory_sha256=inventory_sha256,
        universe_semantic_sha256=universe.semantic_sha256,
    )


def _next_pending(
    snapshot: StatementFactorCycleSnapshot, statements: Mapping[str, Any]
) -> str | None:
    for entry in snapshot.entries:
        record = statements.get(entry.statement_key)
        if isinstance(record, dict) and record.get("status") == "pending":
            return entry.statement_key
    return None


def initialize_cycle_state(
    snapshot: StatementFactorCycleSnapshot, state_path: Path
) -> StatementFactorCycleState:
    """Create the deterministic initial state with the six retained statements done."""

    if state_path.exists() or state_path.is_symlink():
        raise StatementFactorCycleError(f"cycle state already exists: {state_path}")

    statements: dict[str, dict[str, Any]] = {}
    for entry in snapshot.entries:
        if entry.is_retained:
            statements[entry.statement_key] = {
                "status": "retained_existing",
                "package_path": entry.retained_package,
                "sql_file_count": None,
                "validation_evidence": None,
                "validation_evidence_sha256": None,
            }
        else:
            statements[entry.statement_key] = {
                "status": "pending",
                "package_path": None,
                "sql_file_count": None,
                "validation_evidence": None,
                "validation_evidence_sha256": None,
            }
    document: dict[str, Any] = {
        "schema_version": _SCHEMA_VERSION,
        "inventory_fingerprint": snapshot.fingerprint,
        "inventory_sha256": snapshot.inventory_sha256,
        "universe_semantic_sha256": snapshot.universe_semantic_sha256,
        "statement_count": snapshot.statement_count,
        "retained_statement_count": snapshot.retained_statement_count,
        "pending_statement_count": snapshot.pending_statement_count,
        "next_pending_statement": _next_pending(snapshot, statements),
        "statements": statements,
    }
    _write_json_atomic(state_path, document)
    return StatementFactorCycleState(document=document)


def _validated_state(
    snapshot: StatementFactorCycleSnapshot, state_path: Path
) -> dict[str, Any]:
    document = _load_json_mapping(state_path, "cycle state")
    if document.get("schema_version") != _SCHEMA_VERSION:
        raise StatementFactorCycleError("cycle state schema version is unsupported")
    if document.get("inventory_fingerprint") != snapshot.fingerprint:
        raise StatementFactorCycleError("cycle state inventory fingerprint is stale")
    if document.get("inventory_sha256") != snapshot.inventory_sha256:
        raise StatementFactorCycleError("cycle state support inventory digest is stale")
    if (
        document.get("universe_semantic_sha256")
        != snapshot.universe_semantic_sha256
    ):
        raise StatementFactorCycleError(
            "cycle state canonical applicability digest is stale"
        )
    statements = document.get("statements")
    if not isinstance(statements, dict) or set(statements) != {
        entry.statement_key for entry in snapshot.entries
    }:
        raise StatementFactorCycleError("cycle state statement universe is inconsistent")
    expected_next = _next_pending(snapshot, statements)
    if document.get("next_pending_statement") != expected_next:
        raise StatementFactorCycleError("cycle state next-pending pointer is inconsistent")
    return document


def complete_cycle_statement(
    snapshot: StatementFactorCycleSnapshot,
    state_path: Path,
    statement_key: str,
    *,
    package_path: str,
    sql_file_count: int,
    validation_evidence: Path,
    plan_path: Path | None = None,
) -> StatementFactorCycleState:
    """Complete exactly the next statement after verifying pass evidence."""

    document = _validated_state(snapshot, state_path)
    statements = document["statements"]
    next_statement = _next_pending(snapshot, statements)
    if next_statement is None:
        raise StatementFactorCycleError("the statement-factor cycle is already complete")
    if statement_key != next_statement:
        raise StatementFactorCycleError(
            f"next pending statement is {next_statement}, not {statement_key}"
        )
    if not isinstance(package_path, str) or not package_path.strip():
        raise StatementFactorCycleError("package_path must be a non-empty string")
    if type(sql_file_count) is not int or sql_file_count < 1:
        raise StatementFactorCycleError("sql_file_count must be a positive integer")
    if validation_evidence.is_symlink() or not validation_evidence.is_file():
        raise StatementFactorCycleError(
            f"validation evidence is missing: {validation_evidence}"
        )
    evidence = _load_json_mapping(validation_evidence, "validation evidence")
    if evidence.get("passed") is not True:
        raise StatementFactorCycleError("validation evidence did not pass")
    entry = next(
        entry for entry in snapshot.entries if entry.statement_key == statement_key
    )
    if evidence.get("statement_key") != statement_key:
        raise StatementFactorCycleError(
            f"validation evidence statement does not match {statement_key}"
        )
    if evidence.get("cycle_fingerprint") != snapshot.fingerprint:
        raise StatementFactorCycleError(
            "validation evidence cycle fingerprint does not match"
        )
    if evidence.get("issues") != []:
        raise StatementFactorCycleError("validation evidence contains unresolved issues")
    if evidence.get("sql_file_count") != sql_file_count:
        raise StatementFactorCycleError(
            "validation evidence SQL file count does not match completion"
        )
    if evidence.get("factor_value_count") != entry.factor_value_count:
        raise StatementFactorCycleError(
            "validation evidence factor value count does not match canonical entry"
        )
    expected_inputs = {
        "matrix": entry.matrix_sha256,
        "reference": entry.reference_sha256,
        "applicability_universe_semantic": snapshot.universe_semantic_sha256,
    }
    if evidence.get("input_sha256") != expected_inputs:
        raise StatementFactorCycleError(
            "validation evidence input SHA-256 bindings do not match"
        )
    if evidence.get("runtime_status") != "not_run_static_sql_only":
        raise StatementFactorCycleError(
            "validation evidence runtime boundary is missing or overstated"
        )

    package_candidate = Path(package_path.strip())
    resolved_package = (
        package_candidate
        if package_candidate.is_absolute()
        else snapshot.repository_root / package_candidate
    )
    try:
        resolved_package = resolved_package.resolve(strict=True)
    except OSError as exc:
        raise StatementFactorCycleError(
            f"completed package directory is missing: {package_path}"
        ) from exc
    if resolved_package.is_symlink() or not resolved_package.is_dir():
        raise StatementFactorCycleError(
            f"completed package path is not a regular directory: {package_path}"
        )
    sql_paths = sorted(
        path
        for path in resolved_package.iterdir()
        if path.is_file() and not path.is_symlink() and path.suffix.lower() == ".sql"
    )
    actual_sql_sha256 = {
        path.name: hashlib.sha256(path.read_bytes()).hexdigest() for path in sql_paths
    }
    if len(sql_paths) != sql_file_count:
        raise StatementFactorCycleError(
            "real completed package SQL file count does not match completion"
        )
    if evidence.get("sql_sha256") != actual_sql_sha256:
        raise StatementFactorCycleError(
            "validation evidence SQL SHA-256 map does not match real files"
        )
    evidence_package_path = validation_evidence.parent / "package.json"
    if evidence_package_path.is_symlink() or not evidence_package_path.is_file():
        raise StatementFactorCycleError(
            "validation evidence package.json is missing"
        )
    package_evidence_sha256 = hashlib.sha256(
        evidence_package_path.read_bytes()
    ).hexdigest()
    if evidence.get("package_sha256") != package_evidence_sha256:
        raise StatementFactorCycleError(
            "validation evidence package SHA-256 does not match"
        )
    evidence_payload = validation_evidence.read_bytes()

    statements[statement_key] = {
        "status": "completed",
        "package_path": package_path.strip(),
        "sql_file_count": sql_file_count,
        "validation_evidence": validation_evidence.as_posix(),
        "validation_evidence_sha256": hashlib.sha256(evidence_payload).hexdigest(),
    }
    document["next_pending_statement"] = _next_pending(snapshot, statements)
    _write_json_atomic(state_path, document)
    state = StatementFactorCycleState(document=document)
    if plan_path is not None:
        _write_text_atomic(plan_path, render_cycle_plan_markdown(snapshot, state))
    return state


def render_factor_inventory_markdown(
    snapshot: StatementFactorCycleSnapshot,
) -> str:
    """Render every pending factor and value before SQL generation begins."""

    lines = [
        "# 剩余语句全量生成因子清单",
        "",
        "> 本文档由语句矩阵确定性生成；只列出尚需生成的 177 条语句。",
        "> 六条已保留语句仍纳入全局守恒计数，但不重复列入待生成明细。",
        "",
        "## 守恒统计",
        "",
        f"- 全部语句：{snapshot.statement_count}",
        f"- 剩余语句：{snapshot.pending_statement_count}",
        f"- 语句-因子：{snapshot.pending_factor_count:,}",
        f"- 因子值：{snapshot.pending_factor_value_count:,}",
        (
            "- PG18 compatibility-only 因子值："
            f"{snapshot.pending_pg18_compatibility_value_count}"
        ),
        f"- 清单指纹：`{snapshot.fingerprint}`",
        "",
        "## 已保留、不重复生成",
        "",
        "| 语句 | 已有包 |",
        "|---|---|",
    ]
    for entry in snapshot.retained_entries:
        lines.append(f"| `{entry.statement_key}` | `{entry.retained_package}` |")

    lines.extend(["", "## 待生成语句与因子", ""])
    for entry in snapshot.pending_entries:
        lines.extend(
            [
                f"<!-- statement:{entry.statement_key} -->",
                f"### {entry.ordinal:03d}. `{entry.statement_key}`",
                "",
                f"- 分类：`{entry.category}/{entry.domain}`",
                f"- 矩阵：`{entry.matrix_path.as_posix()}`",
                f"- 官方语法快照：`{entry.reference_path.as_posix()}`",
                f"- 官方来源：{entry.official_source}",
                f"- 因子数 / 因子值数：{entry.factor_count} / {entry.factor_value_count}",
                "",
                "| 因子 | 层级 | 覆盖角色 | 全部必需值 |",
                "|---|---|---|---|",
            ]
        )
        for factor in entry.factors:
            lines.append(f"<!-- factor:{entry.statement_key}:{factor.name} -->")
            value_text = "<br>".join(
                f"<!-- row:{row_id} -->`{factor.name}={value}` "
                f"(`{binding}` → `{witness_id}`)"
                for value, row_id, binding, witness_id in zip(
                    factor.values,
                    factor.row_ids,
                    factor.matrix_bindings,
                    factor.witness_ids,
                )
            )
            lines.append(
                f"| `{factor.name}` | `{factor.tier}` | "
                f"`{factor.coverage_role}` | {value_text} |"
            )
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def render_cycle_plan_markdown(
    snapshot: StatementFactorCycleSnapshot, state: StatementFactorCycleState
) -> str:
    """Render a checkbox plan from the evidence-backed JSON state."""

    statements = state.document.get("statements")
    if not isinstance(statements, Mapping):
        raise StatementFactorCycleError("cycle state has no statements mapping")
    next_statement = state.next_pending_statement
    lines = [
        "# 剩余语句 Regress 顺序生成计划",
        "",
        "> 勾选项由进度状态生成，不手工修改。只有生成包通过校验并写入证据后才会勾选。",
        "",
        "## 当前状态",
        "",
        f"- 清单指纹：`{snapshot.fingerprint}`",
        f"- 下一条：`{next_statement}`" if next_statement else "- 下一条：全部完成",
        "",
        "## 顺序清单",
        "",
        "| 完成 | 序号 | 语句 | 分类目录 | 因子 / 值 | SQL 文件 | 生成包或状态 |",
        "|---|---:|---|---|---:|---:|---|",
    ]
    for entry in snapshot.entries:
        record = statements.get(entry.statement_key)
        if not isinstance(record, Mapping):
            raise StatementFactorCycleError(
                f"cycle state record is invalid for {entry.statement_key}"
            )
        status = record.get("status")
        checked = status in {"retained_existing", "completed"}
        sql_count = record.get("sql_file_count")
        sql_text = str(sql_count) if isinstance(sql_count, int) else "—"
        package = record.get("package_path")
        package_text = f"`{package}`" if isinstance(package, str) else "待生成"
        if status == "retained_existing":
            package_text += "（保留已有）"
        lines.append(
            f"| [{'x' if checked else ' '}] | {entry.ordinal:03d} | "
            f"`{entry.statement_key}` | `{entry.category}/{entry.domain}` | "
            f"{entry.factor_count} / {entry.factor_value_count} | {sql_text} | "
            f"{package_text} |"
        )
    return "\n".join(lines).rstrip() + "\n"


def materialize_cycle_documents(
    snapshot: StatementFactorCycleSnapshot,
    *,
    state_path: Path,
    inventory_path: Path,
    plan_path: Path,
) -> StatementFactorCycleState:
    """Create or resume the ledger and atomically render both Markdown views."""

    if state_path.exists() or state_path.is_symlink():
        document = _validated_state(snapshot, state_path)
        state = StatementFactorCycleState(document=document)
    else:
        state = initialize_cycle_state(snapshot, state_path)
    _write_text_atomic(inventory_path, render_factor_inventory_markdown(snapshot))
    _write_text_atomic(plan_path, render_cycle_plan_markdown(snapshot, state))
    return state
