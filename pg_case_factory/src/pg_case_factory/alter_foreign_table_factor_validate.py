"""Actual-byte coverage validation for ALTER FOREIGN TABLE factor-loop SQL."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
import hashlib
from pathlib import Path
import re
from typing import Any, Mapping

from .alter_foreign_table_factor_loop import (
    AlterForeignTableFactorCase,
    AlterForeignTableFactorLoopPlan,
)
from .alter_foreign_table_factor_render import (
    count_primary_alter_foreign_table,
    render_alter_foreign_table_factor_case,
    resolve_alter_foreign_table_factor_witness,
)


_PRIMARY_BEGIN = "-- primary-target-begin"
_PRIMARY_END = "-- primary-target-end"


@dataclass(frozen=True)
class AlterForeignTableFactorProgramValidation:
    passed: bool
    issues: tuple[str, ...]
    decision_count: int
    sql_file_count: int
    delegated_count: int
    expected_primary_obligation_ids: tuple[str, ...]
    actual_primary_obligation_ids: tuple[str, ...]
    delegated_obligation_ids: tuple[str, ...]
    missing_obligation_ids: tuple[str, ...]
    duplicate_obligation_ids: tuple[str, ...]
    unknown_obligation_ids: tuple[str, ...]
    semantic_witness_mismatch_case_ids: tuple[str, ...]
    sql_sha256: Mapping[str, str]
    records: tuple[Mapping[str, Any], ...]

    @property
    def missing_obligation_count(self) -> int:
        return len(self.missing_obligation_ids)

    @property
    def duplicate_obligation_count(self) -> int:
        return len(self.duplicate_obligation_ids)

    @property
    def unknown_obligation_count(self) -> int:
        return len(self.unknown_obligation_ids)

    @property
    def semantic_witness_mismatch_count(self) -> int:
        return len(self.semantic_witness_mismatch_case_ids)

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": 1,
            "kind": "alter_foreign_table_actual_factor_witness_report",
            "generation_mode": "factor_value_independent_loop_v1",
            "passed": self.passed,
            "issues": list(self.issues),
            "decision_count": self.decision_count,
            "sql_file_count": self.sql_file_count,
            "delegated_count": self.delegated_count,
            "expected_primary_obligation_ids": list(
                self.expected_primary_obligation_ids
            ),
            "actual_primary_obligation_ids": list(
                self.actual_primary_obligation_ids
            ),
            "delegated_obligation_ids": list(self.delegated_obligation_ids),
            "missing_obligation_ids": list(self.missing_obligation_ids),
            "duplicate_obligation_ids": list(self.duplicate_obligation_ids),
            "unknown_obligation_ids": list(self.unknown_obligation_ids),
            "semantic_witness_mismatch_case_ids": list(
                self.semantic_witness_mismatch_case_ids
            ),
            "missing_obligation_count": self.missing_obligation_count,
            "duplicate_obligation_count": self.duplicate_obligation_count,
            "unknown_obligation_count": self.unknown_obligation_count,
            "semantic_witness_mismatch_count": (
                self.semantic_witness_mismatch_count
            ),
            "sql_sha256": dict(self.sql_sha256),
            "records": [dict(record) for record in self.records],
        }


def _sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _target_region(sql: str) -> str | None:
    if sql.count(_PRIMARY_BEGIN) != 1 or sql.count(_PRIMARY_END) != 1:
        return None
    before_end, after_end = sql.split(_PRIMARY_END, 1)
    if _PRIMARY_BEGIN not in before_end or _PRIMARY_BEGIN in after_end:
        return None
    return before_end.split(_PRIMARY_BEGIN, 1)[1].strip()


def _single_header_value(sql: str, field: str) -> str | None:
    matches = re.findall(
        rf"(?m)^-- {re.escape(field)}: (.+)$",
        sql,
    )
    return matches[0] if len(matches) == 1 else None


def _contains_all_exact(sql: str, fragments: tuple[str, ...]) -> bool:
    return all(fragment.rstrip() in sql for fragment in fragments)


def _semantic_program_matches(
    plan: AlterForeignTableFactorLoopPlan,
    case: AlterForeignTableFactorCase,
    sql: str,
    repository_root: Path,
) -> tuple[bool, tuple[str, ...], Mapping[str, Any]]:
    reasons: list[str] = []
    witness = resolve_alter_foreign_table_factor_witness(case, repository_root)
    expected_sql = render_alter_foreign_table_factor_case(
        plan,
        case,
        repository_root,
    )
    expected_target = _target_region(expected_sql)
    actual_target = _target_region(sql)

    if _single_header_value(sql, "case_id") != case.case_id:
        reasons.append("case_id_header_mismatch")
    if (
        _single_header_value(sql, "primary_obligation_id")
        != case.primary_obligation_id
    ):
        reasons.append("primary_obligation_header_mismatch")
    if _single_header_value(sql, "expected_outcome") != case.outcome:
        reasons.append("expected_outcome_header_mismatch")
    if _single_header_value(sql, "expected_sqlstate") != case.expected_sqlstate:
        reasons.append("expected_sqlstate_header_mismatch")
    if actual_target is None or count_primary_alter_foreign_table(sql) != 1:
        reasons.append("primary_target_cardinality_mismatch")
    elif actual_target != expected_target:
        reasons.append("primary_target_semantic_mismatch")
    if not _contains_all_exact(sql, witness.setup_sql):
        reasons.append("fixture_semantic_locus_mismatch")
    if not _contains_all_exact(sql, witness.oracle_sql):
        reasons.append("oracle_semantic_locus_mismatch")
    if not _contains_all_exact(sql, witness.cleanup_sql):
        reasons.append("cleanup_semantic_locus_mismatch")
    sqlstate_oracle = (
        f"SELECT :'target_sqlstate' = '{case.expected_sqlstate}' "
        "AS target_sqlstate_matches_expected;"
    )
    if sqlstate_oracle not in sql:
        reasons.append("sqlstate_oracle_mismatch")
    if sql.encode("utf-8") != expected_sql.encode("utf-8"):
        reasons.append("canonical_program_bytes_mismatch")

    unique_reasons = tuple(dict.fromkeys(reasons))
    record = {
        "case_id": case.case_id,
        "sql_filename": case.sql_filename,
        "primary_obligation_id": case.primary_obligation_id,
        "kind": case.kind,
        "factor_key": case.factor_key,
        "factor_value": case.factor_value,
        "consumer_action_id": case.consumer_action_id,
        "semantic_locus": witness.semantic_locus,
        "expected_outcome": case.outcome,
        "expected_sqlstate": case.expected_sqlstate,
        "actual_target_sha256": (
            _sha256(actual_target.encode("utf-8"))
            if actual_target is not None
            else None
        ),
        "semantic_witness_passed": not unique_reasons,
        "mismatch_reasons": list(unique_reasons),
    }
    return not unique_reasons, unique_reasons, record


def validate_alter_foreign_table_factor_programs(
    plan: AlterForeignTableFactorLoopPlan,
    programs: Mapping[str, str | bytes],
    repository_root: Path,
    *,
    selected_case_ids: set[str] | None = None,
) -> AlterForeignTableFactorProgramValidation:
    """Reconstruct credited obligations from final SQL bytes and fail closed."""

    root = Path(repository_root).resolve(strict=True)
    if selected_case_ids is None:
        selected_cases = plan.cases
    else:
        selected_cases = tuple(
            case for case in plan.cases if case.case_id in selected_case_ids
        )
        selected_unknown = selected_case_ids - {
            case.case_id for case in selected_cases
        }
        if selected_unknown:
            raise ValueError(
                "unknown selected case IDs: " + ", ".join(sorted(selected_unknown))
            )

    case_by_filename = {case.sql_filename: case for case in selected_cases}
    expected_ids = tuple(case.primary_obligation_id for case in selected_cases)
    expected_id_set = set(expected_ids)
    known_all_ids = {row.obligation_id for row in plan.obligations}
    actual_ids: list[str] = []
    unknown_ids: list[str] = []
    mismatch_cases: list[str] = []
    issues: list[str] = []
    hashes: dict[str, str] = {}
    records: list[Mapping[str, Any]] = []

    for filename in sorted(programs):
        payload = programs[filename]
        raw = payload if isinstance(payload, bytes) else payload.encode("utf-8")
        hashes[filename] = _sha256(raw)
        try:
            sql = raw.decode("utf-8")
        except UnicodeDecodeError:
            issues.append(f"{filename}: SQL is not UTF-8")
            continue
        case = case_by_filename.get(filename)
        if case is None:
            header_id = _single_header_value(sql, "primary_obligation_id")
            if header_id is not None:
                unknown_ids.append(header_id)
            issues.append(f"{filename}: unexpected SQL program")
            continue
        passed, reasons, record = _semantic_program_matches(
            plan,
            case,
            sql,
            root,
        )
        records.append(record)
        header_id = _single_header_value(sql, "primary_obligation_id")
        if header_id is not None and header_id not in known_all_ids:
            unknown_ids.append(header_id)
        if passed:
            actual_ids.append(case.primary_obligation_id)
        else:
            mismatch_cases.append(case.case_id)
            issues.append(
                f"{filename}: semantic witness mismatch: " + ", ".join(reasons)
            )

    actual_counter = Counter(actual_ids)
    missing_ids = tuple(
        obligation_id
        for obligation_id in expected_ids
        if actual_counter[obligation_id] == 0
    )
    duplicate_ids = tuple(
        sorted(
            obligation_id
            for obligation_id, count in actual_counter.items()
            if count > 1
        )
    )
    unknown_ids.extend(sorted(set(actual_counter) - expected_id_set))
    unknown_tuple = tuple(sorted(set(unknown_ids)))
    if missing_ids:
        issues.append(f"missing {len(missing_ids)} primary obligations")
    if duplicate_ids:
        issues.append(f"duplicated {len(duplicate_ids)} primary obligations")
    if unknown_tuple:
        issues.append(f"unknown {len(unknown_tuple)} primary obligations")
    if set(programs) != set(case_by_filename):
        absent_files = sorted(set(case_by_filename) - set(programs))
        if absent_files:
            issues.append(f"missing {len(absent_files)} SQL programs")

    delegated_ids = tuple(row.obligation_id for row in plan.delegated)
    mismatch_tuple = tuple(dict.fromkeys(mismatch_cases))
    return AlterForeignTableFactorProgramValidation(
        passed=not issues,
        issues=tuple(dict.fromkeys(issues)),
        decision_count=len(plan.obligations),
        sql_file_count=len(programs),
        delegated_count=len(delegated_ids),
        expected_primary_obligation_ids=expected_ids,
        actual_primary_obligation_ids=tuple(actual_ids),
        delegated_obligation_ids=delegated_ids,
        missing_obligation_ids=missing_ids,
        duplicate_obligation_ids=duplicate_ids,
        unknown_obligation_ids=unknown_tuple,
        semantic_witness_mismatch_case_ids=mismatch_tuple,
        sql_sha256=dict(sorted(hashes.items())),
        records=tuple(records),
    )


def remove_primary_semantic_locus_but_keep_comments(
    sql: str,
    case: AlterForeignTableFactorCase,
) -> str:
    """Mutation helper proving that trace comments alone receive no credit."""

    if f"-- case_id: {case.case_id}" not in sql:
        raise ValueError("case trace is missing")
    target = _target_region(sql)
    if target is None:
        raise ValueError("primary target boundary is missing")
    return sql.replace(target, "SELECT true AS removed_primary_semantic_locus;", 1)


__all__ = [
    "AlterForeignTableFactorProgramValidation",
    "remove_primary_semantic_locus_but_keep_comments",
    "validate_alter_foreign_table_factor_programs",
]
