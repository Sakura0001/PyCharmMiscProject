"""Actual-byte coverage validation for CREATE INDEX factor-loop SQL.

Re-renders the canonical bytes for every case (frozen 101-case baseline +
bounded extension) and compares them exactly against the on-disk SQL.
Fails closed on any drift: byte mismatch, header mismatch, primary-target
cardinality != 1, placeholder leakage, missing/duplicate/unknown cases,
or an extension case lacking a derivation record.  Also gates that every
required factor value is still witnessed across ``baseline union extension``.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
import hashlib
from pathlib import Path
import re
from typing import Any, Mapping

from .create_index_factor_render import (
    count_primary_create_index,
    render_create_index_factor_case,
    resolve_create_index_factor_witness,
)

_PRIMARY_BEGIN = "-- primary-target-begin"
_PRIMARY_END = "-- primary-target-end"


@dataclass(frozen=True)
class CreateIndexFactorProgramValidation:
    passed: bool
    issues: tuple[str, ...]
    baseline_case_count: int
    extension_case_count: int
    sql_file_count: int
    missing_case_ids: tuple[str, ...]
    duplicate_case_ids: tuple[str, ...]
    unknown_obligation_ids: tuple[str, ...]
    semantic_witness_mismatch_case_ids: tuple[str, ...]
    coverage_gaps: tuple[str, ...]
    sql_sha256: Mapping[str, str]
    records: tuple[Mapping[str, Any], ...]

    @property
    def missing_case_count(self) -> int:
        return len(self.missing_case_ids)

    @property
    def duplicate_case_count(self) -> int:
        return len(self.duplicate_case_ids)

    @property
    def unknown_obligation_count(self) -> int:
        return len(self.unknown_obligation_ids)

    @property
    def semantic_witness_mismatch_count(self) -> int:
        return len(self.semantic_witness_mismatch_case_ids)

    @property
    def coverage_gap_count(self) -> int:
        return len(self.coverage_gaps)

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": 1,
            "kind": (
                "create_index_actual_factor_witness_report"
            ),
            "generation_mode": (
                "marginal_baseline_plus_bounded_extension_v1"
            ),
            "passed": self.passed,
            "issues": list(self.issues),
            "baseline_case_count": self.baseline_case_count,
            "extension_case_count": self.extension_case_count,
            "sql_file_count": self.sql_file_count,
            "missing_case_ids": list(self.missing_case_ids),
            "duplicate_case_ids": list(self.duplicate_case_ids),
            "unknown_obligation_ids": list(
                self.unknown_obligation_ids
            ),
            "semantic_witness_mismatch_case_ids": list(
                self.semantic_witness_mismatch_case_ids
            ),
            "coverage_gaps": list(self.coverage_gaps),
            "missing_case_count": self.missing_case_count,
            "duplicate_case_count": self.duplicate_case_count,
            "unknown_obligation_count": (
                self.unknown_obligation_count
            ),
            "semantic_witness_mismatch_count": (
                self.semantic_witness_mismatch_count
            ),
            "coverage_gap_count": self.coverage_gap_count,
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
    matches = re.findall(rf"(?m)^-- {re.escape(field)}: (.+)$", sql)
    return matches[0] if len(matches) == 1 else None


def _contains_all_exact(sql: str, fragments: tuple[str, ...]) -> bool:
    return all(fragment.rstrip() in sql for fragment in fragments)


def _is_extension(case: object) -> bool:
    return bool(getattr(case, "is_extension", False))


def _primary_identifier(case: object) -> str:
    if _is_extension(case):
        return getattr(case, "derivation_id")
    return getattr(case, "primary_obligation_id")


def _has_derivation_record(case: object) -> bool:
    return bool(
        getattr(case, "derivation_id", "")
        and getattr(case, "derived_from_combination_group", "")
        and getattr(case, "derivation_reason", "")
    )


def _semantic_program_matches(
    case: object,
    sql: str,
    repository_root: Path,
) -> tuple[bool, tuple[str, ...], Mapping[str, Any]]:
    reasons: list[str] = []
    witness = resolve_create_index_factor_witness(
        case, repository_root
    )
    expected_sql = render_create_index_factor_case(
        case, repository_root
    )
    expected_target = _target_region(expected_sql)
    actual_target = _target_region(sql)
    case_id = getattr(case, "case_id")
    outcome = getattr(case, "outcome")
    expected_sqlstate = getattr(case, "expected_sqlstate")
    if "{" in sql or "}" in sql:
        reasons.append("placeholder_leakage")
    if _single_header_value(sql, "case_id") != case_id:
        reasons.append("case_id_header_mismatch")
    if (
        _single_header_value(sql, "primary_obligation_id")
        != _primary_identifier(case)
    ):
        reasons.append("primary_obligation_header_mismatch")
    if _single_header_value(sql, "expected_outcome") != outcome:
        reasons.append("expected_outcome_header_mismatch")
    if _single_header_value(sql, "expected_sqlstate") != expected_sqlstate:
        reasons.append("expected_sqlstate_header_mismatch")
    if actual_target is None or count_primary_create_index(sql) != 1:
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
        f"SELECT :'target_sqlstate' = '{expected_sqlstate}' "
        "AS target_sqlstate_matches_expected;"
    )
    if sqlstate_oracle not in sql:
        reasons.append("sqlstate_oracle_mismatch")
    if sql.encode("utf-8") != expected_sql.encode("utf-8"):
        reasons.append("canonical_program_bytes_mismatch")
    if _is_extension(case) and not _has_derivation_record(case):
        reasons.append("extension_derivation_record_missing")
    unique = tuple(dict.fromkeys(reasons))
    record = {
        "case_id": case_id,
        "sql_filename": getattr(case, "sql_filename"),
        "primary_obligation_id": _primary_identifier(case),
        "is_extension": _is_extension(case),
        "consumer_action_id": getattr(case, "consumer_action_id"),
        "semantic_locus": witness.semantic_locus,
        "expected_outcome": outcome,
        "expected_sqlstate": expected_sqlstate,
        "actual_target_sha256": (
            _sha256(actual_target.encode("utf-8"))
            if actual_target is not None
            else None
        ),
        "semantic_witness_passed": not unique,
        "mismatch_reasons": list(unique),
    }
    return not unique, unique, record


def _all_cases(
    baseline_plan: object, extension_plan: object
) -> tuple[object, ...]:
    return tuple(baseline_plan.cases) + tuple(extension_plan.cases)


def _required_factor_pairs(
    baseline_plan: object,
) -> frozenset[tuple[str, str]]:
    pairs: set[tuple[str, str]] = set()
    for case in baseline_plan.cases:
        for factor, value in case.baseline_assignments:
            pairs.add((factor, value))
    return frozenset(pairs)


def _witnessed_factor_pairs(
    cases: tuple[object, ...],
) -> set[tuple[str, str]]:
    pairs: set[tuple[str, str]] = set()
    for case in cases:
        assignment = (
            case.factor_assignment
            if hasattr(case, "factor_assignment")
            else case.baseline_assignments
        )
        for factor, value in assignment:
            pairs.add((factor, value))
    return pairs


def _coverage_gaps(
    baseline_plan: object,
    all_cases: tuple[object, ...],
) -> tuple[str, ...]:
    required = _required_factor_pairs(baseline_plan)
    witnessed = _witnessed_factor_pairs(all_cases)
    gaps = sorted(f"{f}={v}" for f, v in (required - witnessed))
    return tuple(gaps)


def validate_create_index_factor_programs(
    baseline_plan: object,
    extension_plan: object,
    programs: Mapping[str, str | bytes],
    repository_root: Path,
    *,
    selected_case_ids: set[str] | None = None,
) -> CreateIndexFactorProgramValidation:
    """Reconstruct credited cases from final SQL bytes and fail closed."""

    root = Path(repository_root).resolve(strict=True)
    all_cases = _all_cases(baseline_plan, extension_plan)
    if selected_case_ids is None:
        selected = all_cases
        validate_all = True
    else:
        selected = tuple(
            case for case in all_cases if case.case_id in selected_case_ids
        )
        unknown_selection = selected_case_ids - {
            c.case_id for c in selected
        }
        if unknown_selection:
            raise ValueError(
                "unknown selected case IDs: "
                + ", ".join(sorted(unknown_selection))
            )
        validate_all = False
    case_by_filename = {case.sql_filename: case for case in selected}
    expected_ids = tuple(c.case_id for c in selected)
    actual_ids: list[str] = []
    unknown_ids: list[str] = []
    mismatch_cases: list[str] = []
    issues: list[str] = []
    hashes: dict[str, str] = {}
    records: list[Mapping[str, Any]] = []
    for filename in sorted(programs):
        payload = programs[filename]
        raw = payload if isinstance(payload, bytes) else payload.encode(
            "utf-8"
        )
        hashes[filename] = _sha256(raw)
        case = case_by_filename.get(filename)
        if case is None:
            if validate_all:
                try:
                    sql = raw.decode("utf-8")
                    header_id = _single_header_value(
                        sql, "primary_obligation_id"
                    )
                    if header_id is not None:
                        unknown_ids.append(header_id)
                except UnicodeDecodeError:
                    issues.append(f"{filename}: SQL is not UTF-8")
                issues.append(f"{filename}: unexpected SQL program")
            continue
        try:
            sql = raw.decode("utf-8")
        except UnicodeDecodeError:
            issues.append(f"{filename}: SQL is not UTF-8")
            continue
        passed, reasons, record = _semantic_program_matches(
            case, sql, root
        )
        records.append(record)
        if passed:
            actual_ids.append(case.case_id)
        else:
            mismatch_cases.append(case.case_id)
            issues.append(
                f"{filename}: semantic witness mismatch: "
                + ", ".join(reasons)
            )
    actual_counter = Counter(actual_ids)
    missing = tuple(cid for cid in expected_ids if actual_counter[cid] == 0)
    duplicate = tuple(
        sorted(cid for cid, count in actual_counter.items() if count > 1)
    )
    unknown_tuple = tuple(sorted(set(unknown_ids)))
    if missing:
        issues.append(f"missing {len(missing)} cases")
    if duplicate:
        issues.append(f"duplicated {len(duplicate)} cases")
    if unknown_tuple:
        issues.append(f"unknown {len(unknown_tuple)} obligations")
    absent = sorted(set(case_by_filename) - set(programs))
    if absent:
        issues.append(f"missing {len(absent)} SQL programs")
    coverage_gaps = _coverage_gaps(baseline_plan, all_cases)
    if coverage_gaps:
        issues.append(
            f"coverage gaps: {len(coverage_gaps)} factor values"
        )
    return CreateIndexFactorProgramValidation(
        passed=not issues,
        issues=tuple(dict.fromkeys(issues)),
        baseline_case_count=len(baseline_plan.cases),
        extension_case_count=len(extension_plan.cases),
        sql_file_count=len(programs),
        missing_case_ids=missing,
        duplicate_case_ids=duplicate,
        unknown_obligation_ids=unknown_tuple,
        semantic_witness_mismatch_case_ids=tuple(
            dict.fromkeys(mismatch_cases)
        ),
        coverage_gaps=coverage_gaps,
        sql_sha256=dict(sorted(hashes.items())),
        records=tuple(records),
    )


def remove_primary_semantic_locus_but_keep_comments(
    sql: str,
    case: object,
) -> str:
    """Mutation helper proving that trace comments alone receive no credit."""

    if f"-- case_id: {getattr(case, 'case_id')}" not in sql:
        raise ValueError("case trace is missing")
    target = _target_region(sql)
    if target is None:
        raise ValueError("primary target boundary is missing")
    return sql.replace(
        target, "SELECT true AS removed_primary_semantic_locus;", 1
    )


__all__ = [
    "CreateIndexFactorProgramValidation",
    "remove_primary_semantic_locus_but_keep_comments",
    "validate_create_index_factor_programs",
]
