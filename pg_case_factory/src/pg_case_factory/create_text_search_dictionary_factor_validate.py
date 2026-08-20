"""Actual-byte coverage validation for CREATE TEXT SEARCH DICTIONARY factor-loop SQL.

Re-renders canonical bytes for every case (frozen 45-case baseline +
bounded extension) and compares exactly against on-disk SQL.  Fails
closed on any drift: byte mismatch, header mismatch, primary-target
cardinality != 1, placeholder leakage, missing/duplicate/unknown cases,
or extension case lacking derivation record.  Also gates that every
required factor value is still witnessed across baseline union
extension.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
import hashlib
from pathlib import Path
import re
from typing import Any, Mapping

from .create_text_search_dictionary_factor_render import (
    count_primary_create_text_search_dictionary,
    render_create_text_search_dictionary_factor_case,
    resolve_create_text_search_dictionary_factor_witness,
)

_PRIMARY_BEGIN = "-- primary-target-begin"
_PRIMARY_END = "-- primary-target-end"


def _sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _target_region(sql: str) -> str | None:
    if sql.count(_PRIMARY_BEGIN) != 1:
        return None
    if sql.count(_PRIMARY_END) != 1:
        return None
    begin_idx = sql.index(_PRIMARY_BEGIN)
    end_idx = sql.index(_PRIMARY_END)
    if begin_idx > end_idx:
        return None
    return sql[begin_idx:end_idx].split(_PRIMARY_BEGIN, 1)[1].strip()


def _single_header_value(sql: str, field: str) -> str | None:
    matches = re.findall(
        rf"(?m)^-- {re.escape(field)}: (.+)$", sql
    )
    if len(matches) != 1:
        return None
    return matches[0]


def _contains_all_exact(
    sql: str, fragments: tuple[str, ...]
) -> bool:
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
    witness = (
        resolve_create_text_search_dictionary_factor_witness(
            case, repository_root
        )
    )
    expected_target = witness.target_sql_fragment
    expected_bytes = (
        render_create_text_search_dictionary_factor_case(
            case, repository_root
        )
    )
    actual_target = _target_region(sql)
    reasons: list[str] = []

    if "{" in sql or "}" in sql:
        reasons.append("placeholder_leakage")
    header_case_id = _single_header_value(sql, "case_id")
    if header_case_id != getattr(case, "case_id"):
        reasons.append("case_id_header_mismatch")
    header_obligation = _single_header_value(
        sql, "primary_obligation_id"
    )
    if header_obligation != _primary_identifier(case):
        reasons.append("primary_obligation_header_mismatch")
    header_outcome = _single_header_value(
        sql, "expected_outcome"
    )
    if header_outcome != getattr(case, "outcome"):
        reasons.append("expected_outcome_header_mismatch")
    header_sqlstate = _single_header_value(
        sql, "expected_sqlstate"
    )
    if header_sqlstate != getattr(case, "expected_sqlstate"):
        reasons.append("expected_sqlstate_header_mismatch")

    if actual_target is None:
        reasons.append("primary_target_cardinality_mismatch")
    elif (
        count_primary_create_text_search_dictionary(sql) != 1
    ):
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
        f"SELECT :'target_sqlstate' = "
        f"'{getattr(case, 'expected_sqlstate')}' "
        f"AS target_sqlstate_matches_expected;"
    )
    if sqlstate_oracle not in sql:
        reasons.append("sqlstate_oracle_mismatch")

    if expected_bytes != sql:
        reasons.append("canonical_program_bytes_mismatch")

    if _is_extension(case) and not _has_derivation_record(case):
        reasons.append("extension_derivation_record_missing")

    record: dict[str, Any] = {
        "case_id": getattr(case, "case_id"),
        "sql_filename": getattr(case, "sql_filename"),
        "primary_obligation_id": _primary_identifier(case),
        "is_extension": _is_extension(case),
        "consumer_action_id": getattr(
            case, "consumer_action_id"
        ),
        "semantic_locus": witness.semantic_locus,
        "expected_outcome": getattr(case, "outcome"),
        "expected_sqlstate": getattr(
            case, "expected_sqlstate"
        ),
        "actual_target_sha256": _sha256(
            (actual_target or "").encode("utf-8")
        ),
        "semantic_witness_passed": not reasons,
        "mismatch_reasons": tuple(reasons),
    }
    return (not reasons, tuple(reasons), record)


def _all_cases(
    baseline_plan: object, extension_plan: object
) -> tuple[object, ...]:
    return tuple(baseline_plan.cases) + tuple(
        extension_plan.cases
    )


def _required_factor_pairs(
    baseline_plan: object,
) -> frozenset[tuple[str, str]]:
    pairs: set[tuple[str, str]] = set()
    for case in baseline_plan.cases:
        for key, value in case.baseline_assignments:
            pairs.add((key, value))
    return frozenset(pairs)


def _witnessed_factor_pairs(
    cases: tuple[object, ...],
) -> set[tuple[str, str]]:
    pairs: set[tuple[str, str]] = set()
    for case in cases:
        assignment = getattr(
            case, "factor_assignment", None
        )
        if assignment is not None:
            for key, value in assignment:
                pairs.add((key, value))
        else:
            for key, value in getattr(
                case, "baseline_assignments"
            ):
                pairs.add((key, value))
    return pairs


def _coverage_gaps(
    baseline_plan: object,
    all_cases: tuple[object, ...],
) -> tuple[str, ...]:
    required = _required_factor_pairs(baseline_plan)
    witnessed = _witnessed_factor_pairs(all_cases)
    gaps = required - witnessed
    return tuple(sorted(f"{f}={v}" for f, v in gaps))


@dataclass(frozen=True)
class CreateTextSearchDictionaryFactorProgramValidation:
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
                "create_text_search_dictionary_actual_factor_"
                "witness_report"
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
            "duplicate_case_ids": list(
                self.duplicate_case_ids
            ),
            "unknown_obligation_ids": list(
                self.unknown_obligation_ids
            ),
            "semantic_witness_mismatch_case_ids": list(
                self.semantic_witness_mismatch_case_ids
            ),
            "coverage_gaps": list(self.coverage_gaps),
            "sql_sha256": dict(self.sql_sha256),
            "records": [
                dict(r) for r in self.records
            ],
        }


def validate_create_text_search_dictionary_factor_programs(
    baseline_plan: object,
    extension_plan: object,
    programs: Mapping[str, str | bytes],
    repository_root: Path,
    *,
    selected_case_ids: set[str] | None = None,
) -> CreateTextSearchDictionaryFactorProgramValidation:
    root = Path(repository_root).resolve(strict=True)
    all_cases = _all_cases(baseline_plan, extension_plan)
    case_by_filename = {
        getattr(c, "sql_filename"): c for c in all_cases
    }

    if selected_case_ids is None:
        validate_all = True
        selected = {getattr(c, "case_id") for c in all_cases}
    else:
        validate_all = False
        selected = set(selected_case_ids)
        known_ids = {getattr(c, "case_id") for c in all_cases}
        unknown_selection = selected - known_ids
        if unknown_selection:
            raise ValueError(
                f"unknown selected case ids: {unknown_selection}"
            )

    hashes: dict[str, str] = {}
    records: list[Mapping[str, Any]] = []
    issues: list[str] = []
    actual_ids: list[str] = []
    missing_cases: list[str] = []
    duplicate_cases: list[str] = []
    unknown_ids: list[str] = []

    actual_counter: Counter[str] = Counter()

    for filename in sorted(programs):
        payload = programs[filename]
        if isinstance(payload, str):
            payload = payload.encode("utf-8")
        sha = _sha256(payload)
        hashes[filename] = sha
        case = case_by_filename.get(filename)
        if case is None:
            if validate_all:
                try:
                    text = payload.decode("utf-8")
                    unknown_id = (
                        _single_header_value(
                            text, "primary_obligation_id"
                        )
                        or "unknown"
                    )
                    unknown_ids.append(unknown_id)
                except Exception:
                    unknown_ids.append("unknown")
                issues.append(
                    f"unknown sql file: {filename}"
                )
            continue
        if getattr(case, "case_id") not in selected:
            continue
        text = payload.decode("utf-8")
        passed, reasons, record = _semantic_program_matches(
            case, text, root
        )
        records.append(record)
        actual_ids.append(getattr(case, "case_id"))
        actual_counter[getattr(case, "case_id")] += 1
        if not passed:
            issues.append(
                f"semantic witness mismatch: "
                f"{getattr(case, 'case_id')}: {reasons}"
            )

    expected_ids = {
        getattr(c, "case_id"): c for c in all_cases
        if getattr(c, "case_id") in selected
    }
    for case_id in expected_ids:
        if case_id not in actual_counter:
            missing_cases.append(case_id)
            issues.append(f"missing case: {case_id}")
    for case_id, count in actual_counter.items():
        if count > 1:
            duplicate_cases.append(case_id)
            issues.append(
                f"duplicate case: {case_id} ({count})"
            )

    for filename, case in case_by_filename.items():
        if getattr(case, "case_id") in selected:
            if filename not in programs:
                issues.append(
                    f"absent program: {filename}"
                )

    gaps = _coverage_gaps(baseline_plan, all_cases)
    if gaps:
        for gap in gaps:
            issues.append(f"coverage gap: {gap}")

    return CreateTextSearchDictionaryFactorProgramValidation(
        passed=not issues,
        issues=tuple(dict.fromkeys(issues)),
        baseline_case_count=len(baseline_plan.cases),
        extension_case_count=len(extension_plan.cases),
        sql_file_count=len(programs),
        missing_case_ids=tuple(dict.fromkeys(missing_cases)),
        duplicate_case_ids=tuple(
            dict.fromkeys(duplicate_cases)
        ),
        unknown_obligation_ids=tuple(
            dict.fromkeys(unknown_ids)
        ),
        semantic_witness_mismatch_case_ids=tuple(
            dict.fromkeys(
                r["case_id"]
                for r in records
                if not r["semantic_witness_passed"]
            )
        ),
        coverage_gaps=gaps,
        sql_sha256=dict(sorted(hashes.items())),
        records=tuple(records),
    )


def remove_primary_semantic_locus_but_keep_comments(
    sql: str, case: object
) -> str:
    from .create_text_search_dictionary_factor_render import (
        CreateTextSearchDictionaryFactorRenderError,
        _as_render_case,
    )

    rc = _as_render_case(case)
    trace = f"-- case_id: {rc.case_id}"
    if trace not in sql:
        raise CreateTextSearchDictionaryFactorRenderError(
            "case trace is missing"
        )
    if (
        sql.count(_PRIMARY_BEGIN) != 1
        or sql.count(_PRIMARY_END) != 1
    ):
        raise CreateTextSearchDictionaryFactorRenderError(
            "primary target markers not found"
        )
    begin_idx = sql.index(_PRIMARY_BEGIN) + len(
        _PRIMARY_BEGIN
    )
    end_idx = sql.index(_PRIMARY_END)
    region = sql[begin_idx:end_idx]
    kept: list[str] = []
    for line in region.split("\n"):
        stripped = line.strip()
        if stripped.startswith("--") or not stripped:
            kept.append(line)
    kept.append("SELECT true AS removed_primary_semantic_locus;")
    return sql[:begin_idx] + "\n".join(kept) + sql[end_idx:]


__all__ = [
    "CreateTextSearchDictionaryFactorProgramValidation",
    "remove_primary_semantic_locus_but_keep_comments",
    "validate_create_text_search_dictionary_factor_programs",
]
