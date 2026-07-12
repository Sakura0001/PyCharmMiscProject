"""Fail-closed feature applicability accounting for the PostgreSQL 18.4 catalog.

The ordinary coverage-plan reconciler can only prove completeness for axes a
plan already declared.  This module supplies the independent universe needed
to prove that a feature review considered every shipped statement, factor and
factor value.  It intentionally does not attempt to infer SQL semantics.

Phase 1 is deliberately self-contained: callers may scaffold and validate the
review bundle today, then pass expanded plan obligations and case manifests to
``reconcile_applicability_bindings`` when the orchestration layer is wired in.
"""

from __future__ import annotations

import csv
import hashlib
import io
import json
import os
import re
import tempfile
from collections import OrderedDict
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass, field
from pathlib import Path, PurePosixPath
from typing import Any, Optional

import yaml


LEDGER_COLUMNS = (
    "statement_key",
    "source_reference",
    "factor",
    "tier",
    "value",
    "synopsis_change",
    "document_change",
    "review_status",
    "catalog_readiness",
    "factor_disposition",
    "required_test_points",
    "official_source_target",
    "evidence",
)
DEFAULT_LEDGER_PATH = Path(
    "skills/pg-sql-generation/references/common/postgresql_18_4_factor_audit.tsv"
)
SHIPPED_STATEMENT_COUNT = 183
SHIPPED_FACTOR_PAIR_COUNT = 3357
SHIPPED_VALUE_ROW_COUNT = 9978
SHIPPED_UNIVERSE_SEMANTIC_SHA256 = (
    "42707defa63ed63e2c15e6d0fa1cde04b93aef9b3c735d1149198b10eb6977fc"
)

INDEX_KIND = "feature_applicability_index"
REVIEW_KIND = "statement_feature_applicability"
COMPATIBILITY_TARGET = "postgresql-18.4"
DECISION_STATUSES = frozenset({"pending", "covered", "justified_exclusion"})
EXECUTABLE_OUTCOMES = frozenset({"success", "expected_failure"})
EXECUTION_PROFILES = frozenset({"basic_psql", "external_isolated"})
SHA256_PATTERN = re.compile(r"^[0-9a-f]{64}$")
STABLE_ID_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]*$")
STATEMENT_KEY_PATTERN = re.compile(r"^[a-z][a-z0-9_]*$")
FACTOR_KEY_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")
HARNESS_ID_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")
FEATURE_LOCATOR_PATTERN = re.compile(
    r"^feature:(?P<requirement>[A-Za-z0-9][A-Za-z0-9._-]*)$"
)
PG18_LOCATOR_PATTERN = re.compile(r"^pg18:[a-z0-9][a-z0-9._-]*$")
APPLICABILITY_AXIS_PREFIX = "applicability_row__"
APPLICABILITY_TEST_POINT_PREFIX = "TP-SFV-"
APPLICABILITY_COMPILER_METADATA_KEY = "applicability_compiler"

_PLACEHOLDER_REASONS = {
    "n/a",
    "na",
    "none",
    "not applicable",
    "not-applicable",
    "pending",
    "replace me",
    "replace-me",
    "tbd",
    "todo",
    "unknown",
    "无",
    "不适用",
    "待定",
    "未知",
}


class ApplicabilityValidationError(ValueError):
    """Raised when an applicability universe or review fails closed."""

    def __init__(self, issues: str | Iterable[str]):
        if isinstance(issues, str):
            normalized = (issues,)
        else:
            normalized = tuple(str(item) for item in issues)
        self.issues = normalized
        super().__init__("; ".join(normalized))


class _UniqueKeySafeLoader(yaml.SafeLoader):
    pass


def _construct_unique_mapping(loader, node, deep=False):
    loader.flatten_mapping(node)
    result = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node, deep=deep)
        if not isinstance(key, str):
            raise ApplicabilityValidationError(
                "applicability YAML mapping keys must be strings"
            )
        if key in result:
            raise ApplicabilityValidationError(f"duplicate YAML key {key}")
        result[key] = loader.construct_object(value_node, deep=deep)
    return result


_UniqueKeySafeLoader.add_constructor(
    yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG,
    _construct_unique_mapping,
)


def _load_yaml(path: Path, location: str) -> Mapping[str, Any]:
    try:
        raw = yaml.load(path.read_text(encoding="utf-8"), Loader=_UniqueKeySafeLoader)
    except ApplicabilityValidationError:
        raise
    except (OSError, UnicodeError, yaml.YAMLError) as exc:
        raise ApplicabilityValidationError(f"cannot load {location}: {exc}") from exc
    if not isinstance(raw, Mapping):
        raise ApplicabilityValidationError(f"{location} must be a YAML mapping")
    return raw


def _mapping(value: Any, location: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise ApplicabilityValidationError(f"{location} must be a mapping")
    return value


def _sequence(value: Any, location: str) -> list[Any]:
    if not isinstance(value, list):
        raise ApplicabilityValidationError(f"{location} must be a list")
    return value


def _exact_keys(
    document: Mapping[str, Any], expected: set[str], location: str
) -> None:
    actual = set(document)
    if actual == expected:
        return
    details = []
    missing = sorted(expected - actual)
    unexpected = sorted(actual - expected)
    if missing:
        details.append("missing " + ", ".join(missing))
    if unexpected:
        details.append("unexpected " + ", ".join(unexpected))
    raise ApplicabilityValidationError(
        f"{location} has an invalid schema: " + "; ".join(details)
    )


def _required_string(
    document: Mapping[str, Any], key: str, location: str
) -> str:
    value = document.get(key)
    if not isinstance(value, str) or not value.strip() or value != value.strip():
        raise ApplicabilityValidationError(
            f"{location}.{key} must be a non-empty trimmed string"
        )
    if "\x00" in value or "\n" in value or "\r" in value:
        raise ApplicabilityValidationError(
            f"{location}.{key} must not contain control line separators"
        )
    return value


def _positive_int(document: Mapping[str, Any], key: str, location: str) -> int:
    value = document.get(key)
    if type(value) is not int or value < 1:
        raise ApplicabilityValidationError(
            f"{location}.{key} must be a positive integer"
        )
    return value


def _sha256_string(
    document: Mapping[str, Any], key: str, location: str
) -> str:
    value = document.get(key)
    if not isinstance(value, str) or not SHA256_PATTERN.fullmatch(value):
        raise ApplicabilityValidationError(
            f"{location}.{key} must be a 64-character lowercase SHA-256"
        )
    return value


def _string_list(
    value: Any,
    location: str,
    *,
    nonempty: bool = False,
) -> tuple[str, ...]:
    values = _sequence(value, location)
    if nonempty and not values:
        raise ApplicabilityValidationError(f"{location} must not be empty")
    normalized = []
    for index, item in enumerate(values):
        if not isinstance(item, str) or not item.strip() or item != item.strip():
            raise ApplicabilityValidationError(
                f"{location}[{index}] must be a non-empty trimmed string"
            )
        normalized.append(item)
    if len(normalized) != len(set(normalized)):
        raise ApplicabilityValidationError(f"{location} contains duplicates")
    return tuple(normalized)


def _portable_relative_path(value: str, location: str) -> PurePosixPath:
    if "\\" in value:
        raise ApplicabilityValidationError(
            f"{location} must use portable forward slashes"
        )
    path = PurePosixPath(value)
    if path.is_absolute() or not path.parts or ".." in path.parts:
        raise ApplicabilityValidationError(
            f"{location} must be relative and stay under its root"
        )
    return path


def _resolve_contained_file(
    root: Path,
    relative_path: str,
    location: str,
) -> Path:
    portable = _portable_relative_path(relative_path, location)
    try:
        resolved_root = root.resolve(strict=True)
    except OSError as exc:
        raise ApplicabilityValidationError(
            f"cannot resolve {location} root {root}: {exc}"
        ) from exc
    if not resolved_root.is_dir():
        raise ApplicabilityValidationError(f"{location} root is not a directory")
    current = resolved_root
    for component in portable.parts:
        current = current / component
        if current.is_symlink():
            raise ApplicabilityValidationError(
                f"{location} must not traverse a symbolic link: {relative_path}"
            )
    try:
        resolved = current.resolve(strict=True)
        resolved.relative_to(resolved_root)
    except FileNotFoundError as exc:
        raise ApplicabilityValidationError(
            f"{location} does not exist: {relative_path}"
        ) from exc
    except (OSError, ValueError) as exc:
        raise ApplicabilityValidationError(
            f"{location} escapes its root: {relative_path}"
        ) from exc
    if not resolved.is_file():
        raise ApplicabilityValidationError(
            f"{location} is not a regular file: {relative_path}"
        )
    return resolved


def _file_sha256(path: Path) -> str:
    try:
        return hashlib.sha256(path.read_bytes()).hexdigest()
    except OSError as exc:
        raise ApplicabilityValidationError(f"cannot hash {path}: {exc}") from exc


def stable_catalog_row_id(statement_key: str, factor: str, value: str) -> str:
    """Return a stable, type-unambiguous ID for one statement-factor-value row."""

    components = (statement_key, factor, value)
    if any(not isinstance(item, str) or not item for item in components):
        raise ApplicabilityValidationError(
            "stable catalog row IDs require non-empty statement, factor, and value strings"
        )
    payload = json.dumps(
        components,
        ensure_ascii=False,
        separators=(",", ":"),
    ).encode("utf-8")
    return "sfv-" + hashlib.sha256(payload).hexdigest()[:24]


def applicability_axis_id(statement_key: str) -> str:
    """Return the reserved one-row-per-obligation axis ID for a statement."""

    normalized = re.sub(r"[^a-z0-9_]+", "_", statement_key.lower()).strip("_")
    if not normalized:
        raise ApplicabilityValidationError("statement key cannot form an axis ID")
    return APPLICABILITY_AXIS_PREFIX + normalized


def applicability_test_point_id(statement_key: str) -> str:
    """Return the reserved one-job-per-statement test-point ID."""

    if not STATEMENT_KEY_PATTERN.fullmatch(statement_key):
        raise ApplicabilityValidationError(
            "statement key cannot form an applicability test-point ID"
        )
    return APPLICABILITY_TEST_POINT_PREFIX + statement_key.upper().replace("_", "-")


@dataclass(frozen=True)
class UniverseCounts:
    statements: int
    statement_factor_pairs: int
    statement_factor_values: int


SHIPPED_UNIVERSE_COUNTS = UniverseCounts(
    SHIPPED_STATEMENT_COUNT,
    SHIPPED_FACTOR_PAIR_COUNT,
    SHIPPED_VALUE_ROW_COUNT,
)


@dataclass(frozen=True)
class CatalogRow:
    row_id: str
    statement_key: str
    source_reference: str
    factor: str
    tier: str
    value: str
    synopsis_change: str
    document_change: str
    review_status: str
    catalog_readiness: str
    factor_disposition: str
    required_test_points: str
    official_source_target: str
    evidence: str

    @property
    def key(self) -> tuple[str, str, str]:
        return self.statement_key, self.factor, self.value

    def ledger_dict(self) -> dict[str, str]:
        return {column: getattr(self, column) for column in LEDGER_COLUMNS}


@dataclass(frozen=True)
class ApplicabilityUniverse:
    source_path: Path
    source_sha256: str
    semantic_sha256: str
    rows: tuple[CatalogRow, ...]
    counts: UniverseCounts

    @property
    def statement_keys(self) -> tuple[str, ...]:
        return tuple(dict.fromkeys(row.statement_key for row in self.rows))

    def rows_for_statement(self, statement_key: str) -> tuple[CatalogRow, ...]:
        return tuple(row for row in self.rows if row.statement_key == statement_key)

    def row_by_id(self) -> dict[str, CatalogRow]:
        return {row.row_id: row for row in self.rows}


def _universe_semantic_sha256(rows: Sequence[CatalogRow]) -> str:
    digest = hashlib.sha256(b"pg-case-feature-applicability-universe-v1\n")
    for row in rows:
        payload = json.dumps(
            row.ledger_dict(),
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
        digest.update(payload)
        digest.update(b"\n")
    return digest.hexdigest()


def load_applicability_universe(
    ledger_path: str | Path,
    *,
    expected_counts: UniverseCounts | None = None,
) -> ApplicabilityUniverse:
    """Load and strictly validate the canonical statement-factor-value ledger."""

    path = Path(ledger_path)
    if path.is_symlink():
        raise ApplicabilityValidationError(
            f"applicability ledger must not be a symbolic link: {path}"
        )
    try:
        raw_bytes = path.read_bytes()
        raw_text = raw_bytes.decode("utf-8")
    except (OSError, UnicodeError) as exc:
        raise ApplicabilityValidationError(
            f"cannot read applicability ledger {path}: {exc}"
        ) from exc
    if not raw_text.strip():
        raise ApplicabilityValidationError("applicability ledger must not be empty")
    if any(not line for line in raw_text.splitlines()[1:]):
        raise ApplicabilityValidationError(
            "applicability ledger must not contain blank data lines"
        )
    reader = csv.DictReader(io.StringIO(raw_text, newline=""), delimiter="\t")
    if tuple(reader.fieldnames or ()) != LEDGER_COLUMNS:
        raise ApplicabilityValidationError(
            "applicability ledger header must exactly match: "
            + ", ".join(LEDGER_COLUMNS)
        )

    rows: list[CatalogRow] = []
    seen_keys: dict[tuple[str, str, str], int] = {}
    seen_ids: dict[str, tuple[str, str, str]] = {}
    statement_sources: dict[str, str] = {}
    factor_tiers: dict[tuple[str, str], str] = {}
    nullable_columns = {"required_test_points"}
    for line_number, document in enumerate(reader, start=2):
        if None in document:
            raise ApplicabilityValidationError(
                f"applicability ledger line {line_number} has extra columns"
            )
        for column in LEDGER_COLUMNS:
            value = document.get(column)
            if not isinstance(value, str):
                raise ApplicabilityValidationError(
                    f"applicability ledger line {line_number}.{column} must be text"
                )
            if column not in nullable_columns and not value:
                raise ApplicabilityValidationError(
                    f"applicability ledger line {line_number}.{column} must not be empty"
                )
            if "\x00" in value or "\n" in value or "\r" in value:
                raise ApplicabilityValidationError(
                    f"applicability ledger line {line_number}.{column} contains a control separator"
                )
        if document["catalog_readiness"] != "static_ready":
            raise ApplicabilityValidationError(
                f"applicability ledger line {line_number} is not static_ready"
            )
        if not STATEMENT_KEY_PATTERN.fullmatch(document["statement_key"]):
            raise ApplicabilityValidationError(
                f"applicability ledger line {line_number}.statement_key is not a "
                "portable lowercase identifier"
            )
        if not FACTOR_KEY_PATTERN.fullmatch(document["factor"]):
            raise ApplicabilityValidationError(
                f"applicability ledger line {line_number}.factor is not a portable identifier"
            )
        source_reference = document["source_reference"]
        source_path = _portable_relative_path(
            source_reference,
            f"applicability ledger line {line_number}.source_reference",
        )
        if source_path.parts[:2] != ("references", "statements"):
            raise ApplicabilityValidationError(
                f"applicability ledger line {line_number}.source_reference must be "
                "under references/statements"
            )
        key = (
            document["statement_key"],
            document["factor"],
            document["value"],
        )
        if key in seen_keys:
            raise ApplicabilityValidationError(
                f"duplicate applicability ledger key {key!r} on lines "
                f"{seen_keys[key]} and {line_number}"
            )
        seen_keys[key] = line_number
        row_id = stable_catalog_row_id(*key)
        if row_id in seen_ids and seen_ids[row_id] != key:
            raise ApplicabilityValidationError(
                f"stable row ID collision {row_id}: {seen_ids[row_id]!r} and {key!r}"
            )
        seen_ids[row_id] = key
        previous_source = statement_sources.setdefault(
            document["statement_key"], document["source_reference"]
        )
        if previous_source != document["source_reference"]:
            raise ApplicabilityValidationError(
                f"statement {document['statement_key']} has inconsistent source_reference values"
            )
        pair = document["statement_key"], document["factor"]
        previous_tier = factor_tiers.setdefault(pair, document["tier"])
        if previous_tier != document["tier"]:
            raise ApplicabilityValidationError(
                f"factor {pair!r} has inconsistent tier values"
            )
        rows.append(CatalogRow(row_id=row_id, **document))

    counts = UniverseCounts(
        statements=len(statement_sources),
        statement_factor_pairs=len(factor_tiers),
        statement_factor_values=len(rows),
    )
    if expected_counts is not None and counts != expected_counts:
        raise ApplicabilityValidationError(
            "applicability universe count mismatch: "
            f"expected {expected_counts.statements}/"
            f"{expected_counts.statement_factor_pairs}/"
            f"{expected_counts.statement_factor_values}, got "
            f"{counts.statements}/{counts.statement_factor_pairs}/"
            f"{counts.statement_factor_values}"
        )
    return ApplicabilityUniverse(
        source_path=path.resolve(),
        source_sha256=hashlib.sha256(raw_bytes).hexdigest(),
        semantic_sha256=_universe_semantic_sha256(rows),
        rows=tuple(rows),
        counts=counts,
    )


def load_shipped_applicability_universe(
    repository_root: str | Path,
) -> ApplicabilityUniverse:
    root = Path(repository_root)
    universe = load_applicability_universe(
        root / DEFAULT_LEDGER_PATH,
        expected_counts=SHIPPED_UNIVERSE_COUNTS,
    )
    if universe.semantic_sha256 != SHIPPED_UNIVERSE_SEMANTIC_SHA256:
        raise ApplicabilityValidationError(
            "shipped applicability universe semantic SHA-256 does not match the "
            "pinned PostgreSQL 18.4 snapshot"
        )
    return universe


@dataclass(frozen=True)
class ReviewDecision:
    status: str
    requirement_ids: tuple[str, ...] = ()
    source_locators: tuple[str, ...] = ()
    reason_id: Optional[str] = None


@dataclass(frozen=True)
class ExclusionReason:
    reason_id: str
    text: str
    requirement_ids: tuple[str, ...]
    source_locators: tuple[str, ...]


@dataclass(frozen=True)
class ObligationBinding:
    test_point_id: str
    obligation_id: str


@dataclass(frozen=True)
class MatrixWitness:
    path: str
    sha256: str
    combination_group_id: str


@dataclass(frozen=True)
class MatrixWitnessCoverageAudit:
    total_rows: int
    covered_rows: int
    combination_group_rows: int
    pg18_compatibility_point_rows: int
    missing_row_ids: tuple[str, ...]
    witnesses: Mapping[str, MatrixWitness]

    @property
    def complete(self) -> bool:
        return (
            self.total_rows == self.covered_rows
            and not self.missing_row_ids
            and self.covered_rows
            == self.combination_group_rows + self.pg18_compatibility_point_rows
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "total_rows": self.total_rows,
            "covered_rows": self.covered_rows,
            "combination_group_rows": self.combination_group_rows,
            "pg18_compatibility_point_rows": self.pg18_compatibility_point_rows,
            "missing_row_ids": list(self.missing_row_ids),
            "complete": self.complete,
        }


@dataclass(frozen=True)
class _MatrixEvidence:
    statement_key: str
    source_reference: str
    required_values_by_factor: Mapping[str, frozenset[str]]
    groups_by_id: Mapping[str, Mapping[str, Any]]
    pg18_points_by_id: Mapping[str, Mapping[str, Any]]


@dataclass(frozen=True)
class ValueReview:
    row_id: str
    value: str
    decision: ReviewDecision
    planned_outcome: Optional[str] = None
    expected_failure_reason: Optional[str] = None
    execution_profile: Optional[str] = None
    execution_harness: Optional[str] = None
    binding: Optional[ObligationBinding] = None
    matrix_witness: Optional[MatrixWitness] = None


@dataclass(frozen=True)
class FactorReview:
    factor: str
    tier: str
    decision: ReviewDecision
    values: tuple[ValueReview, ...]


@dataclass(frozen=True)
class StatementReview:
    feature_id: str
    statement_key: str
    source_reference: str
    decision: ReviewDecision
    factors: tuple[FactorReview, ...]
    reasons: Mapping[str, ExclusionReason]
    source_path: Path
    source_sha256: str


@dataclass(frozen=True)
class ReviewReference:
    statement_key: str
    path: str
    sha256: str


@dataclass(frozen=True)
class ApplicabilitySummary:
    total: int
    covered: int
    justified_exclusion: int
    pending: int
    unbound_covered: int
    pending_statement_decisions: int
    pending_factor_decisions: int

    @property
    def complete(self) -> bool:
        return (
            self.total == self.covered + self.justified_exclusion + self.pending
            and self.pending == 0
            and self.unbound_covered == 0
            and self.pending_statement_decisions == 0
            and self.pending_factor_decisions == 0
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "total": self.total,
            "covered": self.covered,
            "justified_exclusion": self.justified_exclusion,
            "pending": self.pending,
            "unbound_covered": self.unbound_covered,
            "pending_statement_decisions": self.pending_statement_decisions,
            "pending_factor_decisions": self.pending_factor_decisions,
            "complete": self.complete,
        }


def _summarize_reviews(reviews: Sequence[StatementReview]) -> ApplicabilitySummary:
    value_reviews = [
        value
        for review in reviews
        for factor in review.factors
        for value in factor.values
    ]
    value_statuses = [value.decision.status for value in value_reviews]
    return ApplicabilitySummary(
        total=len(value_statuses),
        covered=sum(item == "covered" for item in value_statuses),
        justified_exclusion=sum(
            item == "justified_exclusion" for item in value_statuses
        ),
        pending=sum(item == "pending" for item in value_statuses),
        unbound_covered=sum(
            value.decision.status == "covered" and value.binding is None
            for value in value_reviews
        ),
        pending_statement_decisions=sum(
            review.decision.status == "pending" for review in reviews
        ),
        pending_factor_decisions=sum(
            factor.decision.status == "pending"
            for review in reviews
            for factor in review.factors
        ),
    )


@dataclass(frozen=True)
class FeatureApplicability:
    feature_id: str
    compatibility_target: str
    universe: ApplicabilityUniverse
    reviews: tuple[StatementReview, ...]
    index_path: Path

    @property
    def summary(self) -> ApplicabilitySummary:
        return _summarize_reviews(self.reviews)

    def covered_rows(self) -> tuple[tuple[CatalogRow, ValueReview], ...]:
        rows_by_id = self.universe.row_by_id()
        return tuple(
            (rows_by_id[value.row_id], value)
            for review in self.reviews
            for factor in review.factors
            for value in factor.values
            if value.decision.status == "covered"
        )


def _validate_locator_evidence(
    requirement_ids: tuple[str, ...],
    locators: tuple[str, ...],
    location: str,
    known_requirement_ids: Optional[set[str]],
) -> None:
    feature_requirements = set()
    has_pg18 = False
    for locator in locators:
        feature_match = FEATURE_LOCATOR_PATTERN.fullmatch(locator)
        if feature_match:
            feature_requirements.add(feature_match.group("requirement"))
            continue
        if PG18_LOCATOR_PATTERN.fullmatch(locator):
            has_pg18 = True
            continue
        raise ApplicabilityValidationError(
            f"{location} has invalid source locator {locator!r}"
        )
    missing_locator_ids = sorted(set(requirement_ids) - feature_requirements)
    if missing_locator_ids:
        raise ApplicabilityValidationError(
            f"{location} lacks feature locator(s) for: "
            + ", ".join(missing_locator_ids)
        )
    if not has_pg18:
        raise ApplicabilityValidationError(
            f"{location} requires at least one pg18:<official-topic> locator"
        )
    if known_requirement_ids is not None:
        unknown = sorted(set(requirement_ids) - known_requirement_ids)
        if unknown:
            raise ApplicabilityValidationError(
                f"{location} references unknown requirement(s): "
                + ", ".join(unknown)
            )


def _parse_scope_decision(
    raw: Any,
    location: str,
    known_requirement_ids: Optional[set[str]],
) -> ReviewDecision:
    document = _mapping(raw, location)
    status = _required_string(document, "status", location)
    if status not in DECISION_STATUSES:
        raise ApplicabilityValidationError(
            f"{location}.status must be pending, covered, or justified_exclusion"
        )
    if status == "pending":
        _exact_keys(document, {"status"}, location)
        return ReviewDecision(status=status)
    if status == "covered":
        _exact_keys(
            document,
            {"status", "requirement_ids", "source_locators"},
            location,
        )
        requirement_ids = _string_list(
            document["requirement_ids"],
            f"{location}.requirement_ids",
            nonempty=True,
        )
        locators = _string_list(
            document["source_locators"],
            f"{location}.source_locators",
            nonempty=True,
        )
        _validate_locator_evidence(
            requirement_ids,
            locators,
            location,
            known_requirement_ids,
        )
        return ReviewDecision(status, requirement_ids, locators)
    _exact_keys(document, {"status", "reason_id"}, location)
    reason_id = _required_string(document, "reason_id", location)
    if not STABLE_ID_PATTERN.fullmatch(reason_id):
        raise ApplicabilityValidationError(f"{location}.reason_id is not stable")
    return ReviewDecision(status=status, reason_id=reason_id)


def _parse_reason(
    raw: Any,
    location: str,
    known_requirement_ids: Optional[set[str]],
) -> ExclusionReason:
    document = _mapping(raw, location)
    _exact_keys(
        document,
        {"id", "text", "requirement_ids", "source_locators"},
        location,
    )
    reason_id = _required_string(document, "id", location)
    if not STABLE_ID_PATTERN.fullmatch(reason_id):
        raise ApplicabilityValidationError(f"{location}.id is not stable")
    text = _required_string(document, "text", location)
    if text.casefold() in _PLACEHOLDER_REASONS:
        raise ApplicabilityValidationError(
            f"{location}.text must be a concrete exclusion reason, not {text!r}"
        )
    requirement_ids = _string_list(
        document["requirement_ids"],
        f"{location}.requirement_ids",
        nonempty=True,
    )
    locators = _string_list(
        document["source_locators"],
        f"{location}.source_locators",
        nonempty=True,
    )
    _validate_locator_evidence(
        requirement_ids,
        locators,
        location,
        known_requirement_ids,
    )
    return ExclusionReason(reason_id, text, requirement_ids, locators)


def _parse_binding(raw: Any, location: str) -> ObligationBinding:
    document = _mapping(raw, location)
    _exact_keys(document, {"test_point_id", "obligation_id"}, location)
    test_point_id = _required_string(document, "test_point_id", location)
    obligation_id = _required_string(document, "obligation_id", location)
    if not STABLE_ID_PATTERN.fullmatch(test_point_id):
        raise ApplicabilityValidationError(
            f"{location}.test_point_id is not a stable identifier"
        )
    if not STABLE_ID_PATTERN.fullmatch(obligation_id):
        raise ApplicabilityValidationError(
            f"{location}.obligation_id is not a stable identifier"
        )
    return ObligationBinding(test_point_id, obligation_id)


def _parse_matrix_witness(raw: Any, location: str) -> MatrixWitness:
    document = _mapping(raw, location)
    _exact_keys(
        document,
        {"path", "sha256", "combination_group_id"},
        location,
    )
    path = _required_string(document, "path", location)
    _portable_relative_path(path, f"{location}.path")
    sha256 = _sha256_string(document, "sha256", location)
    group_id = _required_string(document, "combination_group_id", location)
    if not STABLE_ID_PATTERN.fullmatch(group_id):
        raise ApplicabilityValidationError(
            f"{location}.combination_group_id is not stable"
        )
    return MatrixWitness(path, sha256, group_id)


def _parse_value_decision(
    raw: Any,
    location: str,
    known_requirement_ids: Optional[set[str]],
    allow_unbound_covered: bool = False,
) -> tuple[
    ReviewDecision,
    Optional[str],
    Optional[str],
    Optional[str],
    Optional[str],
    Optional[ObligationBinding],
    Optional[MatrixWitness],
]:
    document = _mapping(raw, location)
    status = _required_string(document, "status", location)
    if status not in DECISION_STATUSES:
        raise ApplicabilityValidationError(
            f"{location}.status must be pending, covered, or justified_exclusion"
        )
    if status == "pending":
        _exact_keys(document, {"status"}, location)
        return ReviewDecision(status), None, None, None, None, None, None
    if status == "justified_exclusion":
        _exact_keys(document, {"status", "reason_id"}, location)
        reason_id = _required_string(document, "reason_id", location)
        if not STABLE_ID_PATTERN.fullmatch(reason_id):
            raise ApplicabilityValidationError(f"{location}.reason_id is not stable")
        return (
            ReviewDecision(status=status, reason_id=reason_id),
            None,
            None,
            None,
            None,
            None,
            None,
        )

    base_keys = {
        "status",
        "requirement_ids",
        "source_locators",
        "planned_outcome",
        "execution_profile",
        "matrix_witness",
    }
    outcome = _required_string(document, "planned_outcome", location)
    if outcome not in EXECUTABLE_OUTCOMES:
        raise ApplicabilityValidationError(
            f"{location}.planned_outcome must be success or expected_failure"
        )
    execution_profile = _required_string(document, "execution_profile", location)
    if execution_profile not in EXECUTION_PROFILES:
        raise ApplicabilityValidationError(
            f"{location}.execution_profile must be basic_psql or external_isolated"
        )
    expected_keys = set(base_keys)
    binding = None
    if "binding" in document:
        expected_keys.add("binding")
        binding = _parse_binding(document["binding"], f"{location}.binding")
    elif not allow_unbound_covered:
        expected_keys.add("binding")
    if outcome == "expected_failure":
        expected_keys.add("expected_failure_reason")
    execution_harness = None
    if execution_profile == "external_isolated":
        expected_keys.add("execution_harness")
        execution_harness = _required_string(
            document,
            "execution_harness",
            location,
        )
        if not HARNESS_ID_PATTERN.fullmatch(execution_harness):
            raise ApplicabilityValidationError(
                f"{location}.execution_harness must be a stable harness identifier"
            )
    _exact_keys(document, expected_keys, location)
    requirement_ids = _string_list(
        document["requirement_ids"],
        f"{location}.requirement_ids",
        nonempty=True,
    )
    locators = _string_list(
        document["source_locators"],
        f"{location}.source_locators",
        nonempty=True,
    )
    _validate_locator_evidence(
        requirement_ids,
        locators,
        location,
        known_requirement_ids,
    )
    failure_reason = None
    if outcome == "expected_failure":
        failure_reason = _required_string(
            document,
            "expected_failure_reason",
            location,
        )
        if failure_reason.casefold() in _PLACEHOLDER_REASONS:
            raise ApplicabilityValidationError(
                f"{location}.expected_failure_reason must be concrete"
            )
    decision = ReviewDecision(status, requirement_ids, locators)
    return (
        decision,
        outcome,
        failure_reason,
        execution_profile,
        execution_harness,
        binding,
        _parse_matrix_witness(
            document["matrix_witness"],
            f"{location}.matrix_witness",
        ),
    )


def _matrix_group_covers_value(
    group: Mapping[str, Any],
    factor: str,
    value: str,
) -> bool:
    factors = group.get("factors")
    if isinstance(factors, Mapping) and factors.get(factor) == value:
        return True
    expansion = group.get("expansion")
    if not isinstance(expansion, Mapping):
        return False
    candidate_axes = {factor, factor + "s"}
    for axis_name, axis in expansion.items():
        if axis_name not in candidate_axes or not isinstance(axis, Mapping):
            continue
        values = axis.get("values")
        if isinstance(values, list) and value in values:
            return True
        if factor == "statement_branch" and isinstance(values, Mapping):
            if value in values.values():
                return True
    return False


def _validate_matrix_witness(
    row: CatalogRow,
    witness: MatrixWitness,
    repository_root: Path,
    location: str,
    matrix_cache: Optional[dict[tuple[str, str], _MatrixEvidence]] = None,
) -> None:
    portable = PurePosixPath(witness.path)
    required_prefix = (
        "skills",
        "pg-sql-generation",
        "references",
        "combinations",
    )
    if (
        portable.parts[: len(required_prefix)] != required_prefix
        or "_shared" in portable.parts
    ):
        raise ApplicabilityValidationError(
            f"{location}.path must identify a statement combination matrix under "
            "skills/pg-sql-generation/references/combinations"
        )
    cache = matrix_cache if matrix_cache is not None else {}
    cache_key = (witness.path, witness.sha256)
    evidence = cache.get(cache_key)
    if evidence is None:
        matrix_path = _resolve_contained_file(
            repository_root,
            witness.path,
            f"{location}.path",
        )
        actual_sha256 = _file_sha256(matrix_path)
        if actual_sha256 != witness.sha256:
            raise ApplicabilityValidationError(
                f"{location}.sha256 does not match {witness.path}"
            )
        matrix = _load_yaml(matrix_path, f"matrix witness {witness.path}")
        if matrix.get("kind") != "statement_combination_matrix":
            raise ApplicabilityValidationError(
                f"{location}.path is not a statement_combination_matrix"
            )
        statement = matrix.get("statement")
        if not isinstance(statement, Mapping):
            raise ApplicabilityValidationError(
                f"{location}.path has no statement mapping"
            )
        factor_contract = matrix.get("factor_contract")
        contract_factors = (
            factor_contract.get("factors")
            if isinstance(factor_contract, Mapping)
            else None
        )
        required_values_by_factor: dict[str, frozenset[str]] = {}
        if isinstance(contract_factors, Mapping):
            for factor_name, factor_document in contract_factors.items():
                required_values = (
                    factor_document.get("required_values")
                    if isinstance(factor_document, Mapping)
                    else None
                )
                if isinstance(factor_name, str) and isinstance(required_values, list):
                    required_values_by_factor[factor_name] = frozenset(
                        item for item in required_values if isinstance(item, str)
                    )
        groups = matrix.get("combination_groups")
        if not isinstance(groups, list):
            raise ApplicabilityValidationError(
                f"{location} matrix has no combination_groups list"
            )
        groups_by_id: dict[str, Mapping[str, Any]] = {}
        for group in groups:
            if not isinstance(group, Mapping):
                raise ApplicabilityValidationError(
                    f"{location} matrix combination group must be a mapping"
                )
            group_id = group.get("id")
            if not isinstance(group_id, str) or not group_id:
                raise ApplicabilityValidationError(
                    f"{location} matrix combination group has no stable id"
                )
            if group_id in groups_by_id:
                raise ApplicabilityValidationError(
                    f"{location} matrix has duplicate combination group {group_id}"
                )
            groups_by_id[group_id] = group
        pg18_points_by_id: dict[str, Mapping[str, Any]] = {}
        compatibility = matrix.get("pg18_compatibility")
        if compatibility is not None:
            if not isinstance(compatibility, Mapping):
                raise ApplicabilityValidationError(
                    f"{location} matrix pg18_compatibility must be a mapping"
                )
            points = compatibility.get("test_points")
            if not isinstance(points, list):
                raise ApplicabilityValidationError(
                    f"{location} matrix pg18_compatibility.test_points must be a list"
                )
            if points and compatibility.get("target_version") != "18.4":
                raise ApplicabilityValidationError(
                    f"{location} matrix PG18 compatibility points require target_version=18.4"
                )
            for point in points:
                if not isinstance(point, Mapping):
                    raise ApplicabilityValidationError(
                        f"{location} matrix PG18 compatibility point must be a mapping"
                    )
                point_id = point.get("id")
                if (
                    not isinstance(point_id, str)
                    or not STABLE_ID_PATTERN.fullmatch(point_id)
                ):
                    raise ApplicabilityValidationError(
                        f"{location} matrix PG18 compatibility point has no stable id"
                    )
                if point_id in groups_by_id or point_id in pg18_points_by_id:
                    raise ApplicabilityValidationError(
                        f"{location} matrix coverage witness ID is not unique: {point_id}"
                    )
                if point.get("oracle") != "reference_parity":
                    raise ApplicabilityValidationError(
                        f"{location} PG18 point {point_id} must use oracle=reference_parity"
                    )
                sql = point.get("sql")
                if not isinstance(sql, str) or not sql.strip():
                    raise ApplicabilityValidationError(
                        f"{location} PG18 point {point_id} must declare non-empty SQL"
                    )
                affected_factors = point.get("affected_factors")
                affected_values = point.get("affected_values")
                if (
                    not isinstance(affected_factors, list)
                    or not affected_factors
                    or any(
                        not isinstance(item, str) or not item
                        for item in affected_factors
                    )
                    or len(affected_factors) != len(set(affected_factors))
                ):
                    raise ApplicabilityValidationError(
                        f"{location} PG18 point {point_id} must declare unique affected_factors"
                    )
                if not isinstance(affected_values, Mapping) or set(
                    affected_values
                ) != set(affected_factors):
                    raise ApplicabilityValidationError(
                        f"{location} PG18 point {point_id} affected_values must exactly "
                        "match affected_factors"
                    )
                for factor_name, values in affected_values.items():
                    if (
                        not isinstance(values, list)
                        or not values
                        or any(not isinstance(item, str) or not item for item in values)
                        or len(values) != len(set(values))
                    ):
                        raise ApplicabilityValidationError(
                            f"{location} PG18 point {point_id} affected_values.{factor_name} "
                            "must be a non-empty unique string list"
                        )
                pg18_points_by_id[point_id] = point
        evidence = _MatrixEvidence(
            statement_key=str(statement.get("key") or ""),
            source_reference=str(statement.get("source_reference") or ""),
            required_values_by_factor=required_values_by_factor,
            groups_by_id=groups_by_id,
            pg18_points_by_id=pg18_points_by_id,
        )
        cache[cache_key] = evidence

    if evidence.statement_key != row.statement_key:
        raise ApplicabilityValidationError(
            f"{location} matrix statement does not match {row.statement_key}"
        )
    if evidence.source_reference != row.source_reference:
        raise ApplicabilityValidationError(
            f"{location} matrix source_reference does not match the canonical row"
        )
    group = evidence.groups_by_id.get(witness.combination_group_id)
    point = evidence.pg18_points_by_id.get(witness.combination_group_id)
    if group is None and point is None:
        raise ApplicabilityValidationError(
            f"{location}.combination_group_id must identify exactly one coverage "
            "witness (combination group or PG18 compatibility point)"
        )
    if group is not None and not _matrix_group_covers_value(group, row.factor, row.value):
        raise ApplicabilityValidationError(
            f"{location} coverage witness {witness.combination_group_id} does not declare or "
            f"expand {row.factor}={row.value}"
        )
    if (
        group is not None
        and row.value
        not in evidence.required_values_by_factor.get(row.factor, frozenset())
    ):
        raise ApplicabilityValidationError(
            f"{location} matrix factor contract does not declare "
            f"{row.factor}={row.value}"
        )
    if point is not None:
        affected_factors = point["affected_factors"]
        affected_values = point["affected_values"]
        if (
            row.factor not in affected_factors
            or row.value not in affected_values.get(row.factor, [])
        ):
            raise ApplicabilityValidationError(
                f"{location} PG18 coverage witness {witness.combination_group_id} does not "
                f"bind {row.factor}={row.value}"
            )


def audit_universe_matrix_witness_coverage(
    universe: ApplicabilityUniverse,
    *,
    repository_root: str | Path,
) -> MatrixWitnessCoverageAudit:
    """Prove every canonical row has a matrix group or PG18 point witness."""

    repository = Path(repository_root)
    cache: dict[tuple[str, str], _MatrixEvidence] = {}
    witnesses: dict[str, MatrixWitness] = {}
    missing: list[str] = []
    group_rows = 0
    pg18_rows = 0
    for statement_key in universe.statement_keys:
        rows = universe.rows_for_statement(statement_key)
        source = PurePosixPath(rows[0].source_reference)
        if source.parts[:2] != ("references", "statements") or source.suffix != ".md":
            raise ApplicabilityValidationError(
                f"statement {statement_key} has an invalid canonical source reference"
            )
        matrix_relative = PurePosixPath(
            "skills",
            "pg-sql-generation",
            "references",
            "combinations",
            *source.parts[2:],
        ).with_suffix(".yaml")
        matrix_path = _resolve_contained_file(
            repository,
            matrix_relative.as_posix(),
            f"statement {statement_key} matrix",
        )
        matrix_sha = _file_sha256(matrix_path)
        matrix = _load_yaml(matrix_path, f"statement {statement_key} matrix")
        groups = [
            group
            for group in matrix.get("combination_groups", [])
            if isinstance(group, Mapping) and isinstance(group.get("id"), str)
        ]
        compatibility = matrix.get("pg18_compatibility")
        points = [
            point
            for point in (
                compatibility.get("test_points", [])
                if isinstance(compatibility, Mapping)
                else []
            )
            if isinstance(point, Mapping) and isinstance(point.get("id"), str)
        ]
        for row in rows:
            group_candidates = [
                str(group["id"])
                for group in groups
                if _matrix_group_covers_value(group, row.factor, row.value)
            ]
            point_candidates = [
                str(point["id"])
                for point in points
                if isinstance(point.get("affected_values"), Mapping)
                and row.value in point["affected_values"].get(row.factor, [])
            ]
            if group_candidates:
                witness_id = group_candidates[0]
                group_rows += 1
            elif point_candidates:
                witness_id = point_candidates[0]
                pg18_rows += 1
            else:
                missing.append(row.row_id)
                continue
            witness = MatrixWitness(
                path=matrix_relative.as_posix(),
                sha256=matrix_sha,
                combination_group_id=witness_id,
            )
            _validate_matrix_witness(
                row,
                witness,
                repository,
                f"canonical row {row.row_id} coverage witness",
                cache,
            )
            witnesses[row.row_id] = witness
    return MatrixWitnessCoverageAudit(
        total_rows=len(universe.rows),
        covered_rows=len(witnesses),
        combination_group_rows=group_rows,
        pg18_compatibility_point_rows=pg18_rows,
        missing_row_ids=tuple(missing),
        witnesses=witnesses,
    )


def _validate_hierarchy(
    review: StatementReview,
    location: str,
) -> None:
    for factor in review.factors:
        statuses = tuple(value.decision.status for value in factor.values)
        factor_location = f"{location}.factors.{factor.factor}"
        if factor.decision.status == "covered":
            if "pending" in statuses or "covered" not in statuses:
                raise ApplicabilityValidationError(
                    f"{factor_location} covered decision requires no pending values "
                    "and at least one covered value"
                )
        elif factor.decision.status == "justified_exclusion":
            if any(item != "justified_exclusion" for item in statuses):
                raise ApplicabilityValidationError(
                    f"{factor_location} justified exclusion requires every value "
                    "to be a justified exclusion"
                )

    factor_statuses = tuple(factor.decision.status for factor in review.factors)
    value_statuses = tuple(
        value.decision.status
        for factor in review.factors
        for value in factor.values
    )
    if review.decision.status == "covered":
        if (
            "pending" in factor_statuses
            or "pending" in value_statuses
            or "covered" not in value_statuses
        ):
            raise ApplicabilityValidationError(
                f"{location} covered statement requires no pending descendants and "
                "at least one covered value"
            )
    elif review.decision.status == "justified_exclusion":
        if any(item != "justified_exclusion" for item in factor_statuses) or any(
            item != "justified_exclusion" for item in value_statuses
        ):
            raise ApplicabilityValidationError(
                f"{location} justified exclusion requires every factor and value "
                "to be a justified exclusion"
            )


def _referenced_reason_ids(review: StatementReview) -> set[str]:
    result = set()
    if review.decision.reason_id is not None:
        result.add(review.decision.reason_id)
    for factor in review.factors:
        if factor.decision.reason_id is not None:
            result.add(factor.decision.reason_id)
        for value in factor.values:
            if value.decision.reason_id is not None:
                result.add(value.decision.reason_id)
    return result


def _load_statement_review(
    path: Path,
    *,
    feature_id: str,
    expected_rows: Sequence[CatalogRow],
    known_requirement_ids: Optional[set[str]],
    repository_root: Path,
    matrix_cache: Optional[dict[tuple[str, str], _MatrixEvidence]] = None,
    allow_unbound_covered: bool = False,
) -> StatementReview:
    location = f"statement review {path}"
    document = _load_yaml(path, location)
    _exact_keys(
        document,
        {
            "schema_version",
            "kind",
            "feature_id",
            "statement_key",
            "source_reference",
            "statement_decision",
            "factors",
            "reasons",
        },
        location,
    )
    if document.get("schema_version") != 1:
        raise ApplicabilityValidationError(
            f"{location}.schema_version must be 1"
        )
    if document.get("kind") != REVIEW_KIND:
        raise ApplicabilityValidationError(f"{location}.kind must be {REVIEW_KIND}")
    actual_feature_id = _required_string(document, "feature_id", location)
    if actual_feature_id != feature_id:
        raise ApplicabilityValidationError(
            f"{location}.feature_id does not match the index"
        )
    statement_key = _required_string(document, "statement_key", location)
    expected_statement = expected_rows[0].statement_key
    if statement_key != expected_statement:
        raise ApplicabilityValidationError(
            f"{location}.statement_key must be {expected_statement}"
        )
    source_reference = _required_string(document, "source_reference", location)
    if source_reference != expected_rows[0].source_reference:
        raise ApplicabilityValidationError(
            f"{location}.source_reference does not match the canonical universe"
        )
    decision = _parse_scope_decision(
        document["statement_decision"],
        f"{location}.statement_decision",
        known_requirement_ids,
    )

    reasons: dict[str, ExclusionReason] = {}
    for index, raw_reason in enumerate(_sequence(document["reasons"], f"{location}.reasons")):
        reason = _parse_reason(
            raw_reason,
            f"{location}.reasons[{index}]",
            known_requirement_ids,
        )
        if reason.reason_id in reasons:
            raise ApplicabilityValidationError(
                f"{location}.reasons contains duplicate id {reason.reason_id}"
            )
        reasons[reason.reason_id] = reason

    expected_by_factor: "OrderedDict[str, list[CatalogRow]]" = OrderedDict()
    for row in expected_rows:
        expected_by_factor.setdefault(row.factor, []).append(row)
    factor_documents = _sequence(document["factors"], f"{location}.factors")
    if len(factor_documents) != len(expected_by_factor):
        raise ApplicabilityValidationError(
            f"{location}.factors must contain exactly {len(expected_by_factor)} factors"
        )
    factors: list[FactorReview] = []
    observed_row_ids: list[str] = []
    for factor_index, ((expected_factor, factor_rows), raw_factor) in enumerate(
        zip(expected_by_factor.items(), factor_documents)
    ):
        factor_location = f"{location}.factors[{factor_index}]"
        factor_document = _mapping(raw_factor, factor_location)
        _exact_keys(
            factor_document,
            {"factor", "tier", "factor_decision", "values"},
            factor_location,
        )
        factor_name = _required_string(factor_document, "factor", factor_location)
        if factor_name != expected_factor:
            raise ApplicabilityValidationError(
                f"{factor_location}.factor must be {expected_factor}; wildcard, "
                "reordered, missing, and unknown factors are forbidden"
            )
        tier = _required_string(factor_document, "tier", factor_location)
        if tier != factor_rows[0].tier:
            raise ApplicabilityValidationError(
                f"{factor_location}.tier does not match the canonical universe"
            )
        factor_decision = _parse_scope_decision(
            factor_document["factor_decision"],
            f"{factor_location}.factor_decision",
            known_requirement_ids,
        )
        value_documents = _sequence(
            factor_document["values"],
            f"{factor_location}.values",
        )
        if len(value_documents) != len(factor_rows):
            raise ApplicabilityValidationError(
                f"{factor_location}.values must contain exactly {len(factor_rows)} rows"
            )
        values: list[ValueReview] = []
        for value_index, (expected_row, raw_value) in enumerate(
            zip(factor_rows, value_documents)
        ):
            value_location = f"{factor_location}.values[{value_index}]"
            value_document = _mapping(raw_value, value_location)
            _exact_keys(
                value_document,
                {"row_id", "value", "decision"},
                value_location,
            )
            row_id = _required_string(value_document, "row_id", value_location)
            value = _required_string(value_document, "value", value_location)
            if row_id != expected_row.row_id or value != expected_row.value:
                raise ApplicabilityValidationError(
                    f"{value_location} must be canonical row {expected_row.row_id} "
                    f"({expected_factor}={expected_row.value}); wildcard, reordered, "
                    "missing, duplicate, and unknown rows are forbidden"
                )
            if row_id in observed_row_ids:
                raise ApplicabilityValidationError(
                    f"{value_location} duplicates row_id {row_id}"
                )
            observed_row_ids.append(row_id)
            (
                value_decision,
                planned_outcome,
                failure_reason,
                execution_profile,
                execution_harness,
                binding,
                witness,
            ) = _parse_value_decision(
                value_document["decision"],
                f"{value_location}.decision",
                known_requirement_ids,
                allow_unbound_covered,
            )
            if value_decision.status == "covered":
                assert witness is not None
                _validate_matrix_witness(
                    expected_row,
                    witness,
                    repository_root,
                    f"{value_location}.decision.matrix_witness",
                    matrix_cache,
                )
            values.append(
                ValueReview(
                    row_id=row_id,
                    value=value,
                    decision=value_decision,
                    planned_outcome=planned_outcome,
                    expected_failure_reason=failure_reason,
                    execution_profile=execution_profile,
                    execution_harness=execution_harness,
                    binding=binding,
                    matrix_witness=witness,
                )
            )
        factors.append(FactorReview(factor_name, tier, factor_decision, tuple(values)))

    expected_row_ids = [row.row_id for row in expected_rows]
    if observed_row_ids != expected_row_ids:
        raise ApplicabilityValidationError(
            f"{location} does not contain the canonical row set in canonical order"
        )
    review = StatementReview(
        feature_id=feature_id,
        statement_key=statement_key,
        source_reference=source_reference,
        decision=decision,
        factors=tuple(factors),
        reasons=reasons,
        source_path=path,
        source_sha256=_file_sha256(path),
    )
    referenced_reason_ids = _referenced_reason_ids(review)
    unknown_reasons = sorted(referenced_reason_ids - set(reasons))
    if unknown_reasons:
        raise ApplicabilityValidationError(
            f"{location} references unknown exclusion reason(s): "
            + ", ".join(unknown_reasons)
        )
    unused_reasons = sorted(set(reasons) - referenced_reason_ids)
    if unused_reasons:
        raise ApplicabilityValidationError(
            f"{location} has unused exclusion reason(s): "
            + ", ".join(unused_reasons)
        )
    _validate_hierarchy(review, location)
    return review


def _yaml_bytes(document: Mapping[str, Any]) -> bytes:
    return yaml.safe_dump(
        dict(document),
        allow_unicode=True,
        sort_keys=False,
        width=1000,
    ).encode("utf-8")


def _atomic_write(path: Path, payload: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary: Optional[Path] = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="wb",
            dir=str(path.parent),
            prefix=f".{path.name}.",
            suffix=".tmp",
            delete=False,
        ) as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
            temporary = Path(handle.name)
        os.replace(temporary, path)
        temporary = None
    finally:
        if temporary is not None:
            try:
                temporary.unlink()
            except FileNotFoundError:
                pass


def _pending_review_document(
    feature_id: str,
    rows: Sequence[CatalogRow],
) -> dict[str, Any]:
    factors: "OrderedDict[str, list[CatalogRow]]" = OrderedDict()
    for row in rows:
        factors.setdefault(row.factor, []).append(row)
    return {
        "schema_version": 1,
        "kind": REVIEW_KIND,
        "feature_id": feature_id,
        "statement_key": rows[0].statement_key,
        "source_reference": rows[0].source_reference,
        "statement_decision": {"status": "pending"},
        "factors": [
            {
                "factor": factor,
                "tier": factor_rows[0].tier,
                "factor_decision": {"status": "pending"},
                "values": [
                    {
                        "row_id": row.row_id,
                        "value": row.value,
                        "decision": {"status": "pending"},
                    }
                    for row in factor_rows
                ],
            }
            for factor, factor_rows in factors.items()
        ],
        "reasons": [],
    }


def scaffold_feature_applicability(
    universe: ApplicabilityUniverse,
    output_directory: str | Path,
    *,
    feature_id: str,
    universe_path: str,
) -> Path:
    """Create a deterministic 183-review skeleton with every value pending.

    The destination must not already exist.  This avoids silently overwriting a
    partially reviewed bundle and makes repeated runs explicit.
    """

    if not isinstance(feature_id, str) or not STABLE_ID_PATTERN.fullmatch(feature_id):
        raise ApplicabilityValidationError(
            "feature_id must be a stable non-empty identifier"
        )
    _portable_relative_path(universe_path, "feature applicability universe.path")
    output = Path(output_directory)
    if output.exists() or output.is_symlink():
        raise ApplicabilityValidationError(
            f"applicability scaffold destination already exists: {output}"
        )
    try:
        output.mkdir(parents=True, exist_ok=False)
    except OSError as exc:
        raise ApplicabilityValidationError(
            f"cannot create applicability scaffold destination {output}: {exc}"
        ) from exc

    reviews_root = output / "reviews"
    reviews_root.mkdir()
    review_entries = []
    for statement_key in universe.statement_keys:
        rows = universe.rows_for_statement(statement_key)
        review_path = reviews_root / f"{statement_key}.yaml"
        payload = _yaml_bytes(_pending_review_document(feature_id, rows))
        _atomic_write(review_path, payload)
        review_entries.append(
            {
                "statement_key": statement_key,
                "path": f"reviews/{statement_key}.yaml",
                "sha256": hashlib.sha256(payload).hexdigest(),
            }
        )

    index_document = {
        "schema_version": 1,
        "kind": INDEX_KIND,
        "feature_id": feature_id,
        "compatibility_target": COMPATIBILITY_TARGET,
        "universe": {
            "path": universe_path,
            "sha256": universe.source_sha256,
            "semantic_sha256": universe.semantic_sha256,
            "statements": universe.counts.statements,
            "statement_factor_pairs": universe.counts.statement_factor_pairs,
            "statement_factor_values": universe.counts.statement_factor_values,
        },
        "reviews": review_entries,
    }
    index_path = output / "feature_applicability_index.yaml"
    _atomic_write(index_path, _yaml_bytes(index_document))
    return index_path


def _parse_review_reference(raw: Any, location: str) -> ReviewReference:
    document = _mapping(raw, location)
    _exact_keys(document, {"statement_key", "path", "sha256"}, location)
    statement_key = _required_string(document, "statement_key", location)
    path = _required_string(document, "path", location)
    _portable_relative_path(path, f"{location}.path")
    sha256 = _sha256_string(document, "sha256", location)
    return ReviewReference(statement_key, path, sha256)


def load_feature_applicability_index(
    index_path: str | Path,
    *,
    repository_root: str | Path,
    known_requirement_ids: Iterable[str] | None = None,
    require_complete: bool = False,
    expected_counts: UniverseCounts | None = None,
    draft: bool = False,
) -> FeatureApplicability:
    """Load, validate, and reconcile an index with its exact review universe."""

    path = Path(index_path)
    if path.is_symlink():
        raise ApplicabilityValidationError(
            f"feature applicability index must not be a symbolic link: {path}"
        )
    document = _load_yaml(path, f"feature applicability index {path}")
    location = f"feature applicability index {path}"
    _exact_keys(
        document,
        {
            "schema_version",
            "kind",
            "feature_id",
            "compatibility_target",
            "universe",
            "reviews",
        },
        location,
    )
    if document.get("schema_version") != 1:
        raise ApplicabilityValidationError(f"{location}.schema_version must be 1")
    if document.get("kind") != INDEX_KIND:
        raise ApplicabilityValidationError(f"{location}.kind must be {INDEX_KIND}")
    feature_id = _required_string(document, "feature_id", location)
    if not STABLE_ID_PATTERN.fullmatch(feature_id):
        raise ApplicabilityValidationError(f"{location}.feature_id is not stable")
    compatibility_target = _required_string(
        document,
        "compatibility_target",
        location,
    )
    if compatibility_target != COMPATIBILITY_TARGET:
        raise ApplicabilityValidationError(
            f"{location}.compatibility_target must be {COMPATIBILITY_TARGET}"
        )
    universe_document = _mapping(document["universe"], f"{location}.universe")
    _exact_keys(
        universe_document,
        {
            "path",
            "sha256",
            "semantic_sha256",
            "statements",
            "statement_factor_pairs",
            "statement_factor_values",
        },
        f"{location}.universe",
    )
    universe_relative = _required_string(
        universe_document,
        "path",
        f"{location}.universe",
    )
    if expected_counts == SHIPPED_UNIVERSE_COUNTS and PurePosixPath(
        universe_relative
    ) != PurePosixPath(DEFAULT_LEDGER_PATH.as_posix()):
        raise ApplicabilityValidationError(
            f"{location}.universe.path must be the shipped canonical ledger "
            f"{DEFAULT_LEDGER_PATH.as_posix()}"
        )
    universe_path = _resolve_contained_file(
        Path(repository_root),
        universe_relative,
        f"{location}.universe.path",
    )
    declared_source_sha = _sha256_string(
        universe_document,
        "sha256",
        f"{location}.universe",
    )
    declared_semantic_sha = _sha256_string(
        universe_document,
        "semantic_sha256",
        f"{location}.universe",
    )
    declared_counts = UniverseCounts(
        statements=_positive_int(
            universe_document,
            "statements",
            f"{location}.universe",
        ),
        statement_factor_pairs=_positive_int(
            universe_document,
            "statement_factor_pairs",
            f"{location}.universe",
        ),
        statement_factor_values=_positive_int(
            universe_document,
            "statement_factor_values",
            f"{location}.universe",
        ),
    )
    if expected_counts is not None and declared_counts != expected_counts:
        raise ApplicabilityValidationError(
            f"{location}.universe counts do not match the required canonical counts"
        )
    universe = load_applicability_universe(
        universe_path,
        expected_counts=declared_counts,
    )
    if universe.source_sha256 != declared_source_sha:
        raise ApplicabilityValidationError(
            f"{location}.universe.sha256 does not match the ledger bytes"
        )
    if universe.semantic_sha256 != declared_semantic_sha:
        raise ApplicabilityValidationError(
            f"{location}.universe.semantic_sha256 does not match the ledger rows"
        )
    if (
        expected_counts == SHIPPED_UNIVERSE_COUNTS
        and universe.semantic_sha256 != SHIPPED_UNIVERSE_SEMANTIC_SHA256
    ):
        raise ApplicabilityValidationError(
            f"{location}.universe does not match the pinned PostgreSQL 18.4 semantic snapshot"
        )

    requirement_ids = None
    if known_requirement_ids is not None:
        requirement_ids = set(known_requirement_ids)
        if any(
            not isinstance(item, str) or not STABLE_ID_PATTERN.fullmatch(item)
            for item in requirement_ids
        ):
            raise ApplicabilityValidationError(
                "known_requirement_ids must contain stable string identifiers"
            )
    references = tuple(
        _parse_review_reference(raw, f"{location}.reviews[{index}]")
        for index, raw in enumerate(
            _sequence(document["reviews"], f"{location}.reviews")
        )
    )
    expected_statements = universe.statement_keys
    observed_statements = tuple(item.statement_key for item in references)
    if observed_statements != expected_statements:
        missing = sorted(set(expected_statements) - set(observed_statements))
        unexpected = sorted(set(observed_statements) - set(expected_statements))
        duplicate = sorted(
            key for key in set(observed_statements) if observed_statements.count(key) > 1
        )
        detail = []
        if missing:
            detail.append("missing " + ", ".join(missing))
        if unexpected:
            detail.append("unexpected " + ", ".join(unexpected))
        if duplicate:
            detail.append("duplicate " + ", ".join(duplicate))
        if not detail:
            detail.append("statement reviews are reordered")
        raise ApplicabilityValidationError(
            f"{location}.reviews must match all canonical statements exactly: "
            + "; ".join(detail)
        )

    index_root = path.parent
    reviews = []
    matrix_cache: dict[tuple[str, str], _MatrixEvidence] = {}
    for reference in references:
        review_path = _resolve_contained_file(
            index_root,
            reference.path,
            f"{location}.reviews.{reference.statement_key}.path",
        )
        if _file_sha256(review_path) != reference.sha256:
            raise ApplicabilityValidationError(
                f"{location}.reviews.{reference.statement_key}.sha256 does not "
                "match the review bytes"
            )
        reviews.append(
            _load_statement_review(
                review_path,
                feature_id=feature_id,
                expected_rows=universe.rows_for_statement(reference.statement_key),
                known_requirement_ids=requirement_ids,
                repository_root=Path(repository_root),
                matrix_cache=matrix_cache,
                allow_unbound_covered=draft,
            )
        )
    result = FeatureApplicability(
        feature_id=feature_id,
        compatibility_target=compatibility_target,
        universe=universe,
        reviews=tuple(reviews),
        index_path=path.resolve(),
    )
    if result.summary.total != universe.counts.statement_factor_values:
        raise ApplicabilityValidationError(
            f"{location} review row total does not match the canonical universe"
        )

    bindings: dict[str, str] = {}
    for row, value_review in result.covered_rows():
        if value_review.binding is None:
            if draft:
                continue
            raise ApplicabilityValidationError(
                f"covered row {row.row_id} has no obligation binding"
            )
        previous = bindings.setdefault(
            value_review.binding.obligation_id,
            row.row_id,
        )
        if previous != row.row_id:
            raise ApplicabilityValidationError(
                "covered applicability rows must bind unique obligations: "
                f"{previous} and {row.row_id} both bind "
                f"{value_review.binding.obligation_id}"
            )
    if require_complete and not result.summary.complete:
        raise ApplicabilityValidationError(
            "feature applicability review is incomplete: "
            + json.dumps(result.summary.to_dict(), sort_keys=True)
        )
    return result


def refresh_feature_applicability_index(
    index_path: str | Path,
    *,
    repository_root: str | Path,
    expected_counts: UniverseCounts | None = None,
) -> Path:
    """Refresh only review SHA-256 values in an existing index.

    This operation is intentionally narrow.  It refuses path, statement,
    feature, universe, or schema drift; it does not modify a review decision or
    make an incomplete review complete.  Call
    :func:`load_feature_applicability_index` afterwards for semantic
    validation.
    """

    path = Path(index_path)
    if path.is_symlink():
        raise ApplicabilityValidationError(
            f"feature applicability index must not be a symbolic link: {path}"
        )
    location = f"feature applicability index {path}"
    document = _load_yaml(path, location)
    _exact_keys(
        document,
        {
            "schema_version",
            "kind",
            "feature_id",
            "compatibility_target",
            "universe",
            "reviews",
        },
        location,
    )
    if document.get("schema_version") != 1 or document.get("kind") != INDEX_KIND:
        raise ApplicabilityValidationError(
            f"{location} must be schema 1 kind {INDEX_KIND}"
        )
    feature_id = _required_string(document, "feature_id", location)
    if document.get("compatibility_target") != COMPATIBILITY_TARGET:
        raise ApplicabilityValidationError(
            f"{location}.compatibility_target must be {COMPATIBILITY_TARGET}"
        )

    universe_document = _mapping(document["universe"], f"{location}.universe")
    _exact_keys(
        universe_document,
        {
            "path",
            "sha256",
            "semantic_sha256",
            "statements",
            "statement_factor_pairs",
            "statement_factor_values",
        },
        f"{location}.universe",
    )
    universe_relative = _required_string(
        universe_document,
        "path",
        f"{location}.universe",
    )
    if expected_counts == SHIPPED_UNIVERSE_COUNTS and PurePosixPath(
        universe_relative
    ) != PurePosixPath(DEFAULT_LEDGER_PATH.as_posix()):
        raise ApplicabilityValidationError(
            f"{location}.universe.path must remain the shipped canonical ledger"
        )
    universe_path = _resolve_contained_file(
        Path(repository_root),
        universe_relative,
        f"{location}.universe.path",
    )
    declared_counts = UniverseCounts(
        _positive_int(universe_document, "statements", f"{location}.universe"),
        _positive_int(
            universe_document,
            "statement_factor_pairs",
            f"{location}.universe",
        ),
        _positive_int(
            universe_document,
            "statement_factor_values",
            f"{location}.universe",
        ),
    )
    if expected_counts is not None and declared_counts != expected_counts:
        raise ApplicabilityValidationError(
            f"{location}.universe counts do not match the required canonical counts"
        )
    universe = load_applicability_universe(
        universe_path,
        expected_counts=declared_counts,
    )
    if universe.source_sha256 != _sha256_string(
        universe_document, "sha256", f"{location}.universe"
    ) or universe.semantic_sha256 != _sha256_string(
        universe_document, "semantic_sha256", f"{location}.universe"
    ):
        raise ApplicabilityValidationError(
            f"{location}.universe snapshot changed; create a new applicability bundle"
        )
    if (
        expected_counts == SHIPPED_UNIVERSE_COUNTS
        and universe.semantic_sha256 != SHIPPED_UNIVERSE_SEMANTIC_SHA256
    ):
        raise ApplicabilityValidationError(
            f"{location}.universe does not match the pinned PostgreSQL 18.4 semantic snapshot"
        )

    references = tuple(
        _parse_review_reference(raw, f"{location}.reviews[{index}]")
        for index, raw in enumerate(
            _sequence(document["reviews"], f"{location}.reviews")
        )
    )
    if tuple(item.statement_key for item in references) != universe.statement_keys:
        raise ApplicabilityValidationError(
            f"{location}.reviews paths/statements no longer match the canonical universe"
        )

    refreshed_reviews = []
    for reference in references:
        review_path = _resolve_contained_file(
            path.parent,
            reference.path,
            f"{location}.reviews.{reference.statement_key}.path",
        )
        review_location = f"statement review {review_path}"
        review_document = _load_yaml(review_path, review_location)
        _exact_keys(
            review_document,
            {
                "schema_version",
                "kind",
                "feature_id",
                "statement_key",
                "source_reference",
                "statement_decision",
                "factors",
                "reasons",
            },
            review_location,
        )
        if (
            review_document.get("schema_version") != 1
            or review_document.get("kind") != REVIEW_KIND
            or review_document.get("feature_id") != feature_id
            or review_document.get("statement_key") != reference.statement_key
            or review_document.get("source_reference")
            != universe.rows_for_statement(reference.statement_key)[0].source_reference
        ):
            raise ApplicabilityValidationError(
                f"{review_location} identity changed; refresh only permits decision edits"
            )
        refreshed_reviews.append(
            {
                "statement_key": reference.statement_key,
                "path": reference.path,
                "sha256": _file_sha256(review_path),
            }
        )

    refreshed_document = {
        "schema_version": 1,
        "kind": INDEX_KIND,
        "feature_id": feature_id,
        "compatibility_target": COMPATIBILITY_TARGET,
        "universe": dict(universe_document),
        "reviews": refreshed_reviews,
    }
    _atomic_write(path, _yaml_bytes(refreshed_document))
    return path.resolve()


@dataclass(frozen=True)
class ApplicabilityCompilationResult:
    output_path: Path
    plan: Any
    obligations: tuple[Any, ...]
    applicability: FeatureApplicability
    reconciliation: "ApplicabilityBindingReconciliation"
    generated_axis_ids: tuple[str, ...]
    generated_test_point_ids: tuple[str, ...]
    canonical_upper_bound: int


def _canonical_document_sha256(document: Mapping[str, Any]) -> str:
    payload = json.dumps(
        dict(document),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _ordered_union(*values: Iterable[str]) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for items in values:
        for item in items:
            if item not in seen:
                seen.add(item)
                result.append(item)
    return result


def _generated_risk_id(harness_id: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "_", harness_id.lower()).strip("_") or "harness"
    digest = hashlib.sha256(harness_id.encode("utf-8")).hexdigest()[:10]
    return f"applicability_external_{slug}_{digest}"


def _covered_by_statement(
    applicability: FeatureApplicability,
) -> "OrderedDict[str, list[tuple[CatalogRow, ValueReview]]]":
    rows_by_id = applicability.universe.row_by_id()
    result: "OrderedDict[str, list[tuple[CatalogRow, ValueReview]]]" = OrderedDict()
    for review in applicability.reviews:
        covered = [
            (rows_by_id[value.row_id], value)
            for factor in review.factors
            for value in factor.values
            if value.decision.status == "covered"
        ]
        if covered:
            result[review.statement_key] = covered
    return result


def _build_compiled_plan_document(
    base_plan: Any,
    manifest: Any,
    applicability: FeatureApplicability,
) -> tuple[dict[str, Any], tuple[str, ...], tuple[str, ...], str]:
    from .contracts import inventory_values_sha256

    base_document = base_plan.to_dict()
    base_metadata = dict(base_document.get("metadata") or {})
    if APPLICABILITY_COMPILER_METADATA_KEY in base_metadata:
        raise ApplicabilityValidationError(
            "base coverage plan is already an applicability-compiled output"
        )
    existing_axes = set(base_document["axes"])
    reserved_axes = sorted(
        axis_id for axis_id in existing_axes if axis_id.startswith(APPLICABILITY_AXIS_PREFIX)
    )
    if reserved_axes:
        raise ApplicabilityValidationError(
            "base coverage plan already contains reserved applicability axis/axes: "
            + ", ".join(reserved_axes)
        )
    existing_points = {point["id"] for point in base_document["test_points"]}
    reserved_points = sorted(
        point_id
        for point_id in existing_points
        if point_id.startswith(APPLICABILITY_TEST_POINT_PREFIX)
    )
    if reserved_points:
        raise ApplicabilityValidationError(
            "base coverage plan already contains reserved applicability test point(s): "
            + ", ".join(reserved_points)
        )
    if base_plan.feature_id != manifest.feature_id:
        raise ApplicabilityValidationError(
            "base coverage plan feature_id does not match the feature manifest"
        )
    if applicability.feature_id != manifest.feature_id:
        raise ApplicabilityValidationError(
            "feature applicability index feature_id does not match the feature manifest"
        )

    generated_axes: dict[str, Any] = {}
    generated_points: list[dict[str, Any]] = []
    harness_usage: "OrderedDict[str, dict[str, list[str]]]" = OrderedDict()
    covered_statements = _covered_by_statement(applicability)
    for statement_key, covered in covered_statements.items():
        axis_id = applicability_axis_id(statement_key)
        point_id = applicability_test_point_id(statement_key)
        if axis_id in existing_axes:
            raise ApplicabilityValidationError(
                f"generated applicability axis collides with base axis {axis_id}"
            )
        if point_id in existing_points:
            raise ApplicabilityValidationError(
                f"generated applicability test point collides with base point {point_id}"
            )
        row_ids = [row.row_id for row, _ in covered]
        requirement_ids = _ordered_union(
            *(value.decision.requirement_ids for _, value in covered)
        )
        source_locators = _ordered_union(
            *(value.decision.source_locators for _, value in covered)
        )
        generated_axes[axis_id] = {
            "values": row_ids,
            "inventory_source": f"inline:feature-applicability/{statement_key}",
            "coverage_mode": "complete",
            "inventory_count": len(row_ids),
            "inventory_sha256": inventory_values_sha256(row_ids),
            "description": (
                f"Every feature-reviewed covered PostgreSQL 18.4 factor value for "
                f"statement {statement_key}."
            ),
            "derivation": (
                "Select exactly the covered row IDs from the run-bound feature "
                "applicability review; pending and justified exclusions are not executable."
            ),
            "source_locators": source_locators,
            "exclusion_policy": (
                "Only rows explicitly marked justified_exclusion remain outside this "
                "executable axis; pending rows keep formal applicability incomplete."
            ),
            "review_status": "semantic_reviewed",
        }
        classification_rules = []
        execution_rules = []
        for row, value in covered:
            classification = {
                "when": {axis_id: row.row_id},
                "outcome": value.planned_outcome,
            }
            if value.planned_outcome == "expected_failure":
                classification["reason"] = value.expected_failure_reason
            classification_rules.append(classification)
            execution_rule = {
                "when": {axis_id: row.row_id},
                "execution_profile": value.execution_profile,
            }
            if value.execution_harness is not None:
                execution_rule["execution_harness"] = value.execution_harness
                usage = harness_usage.setdefault(
                    value.execution_harness,
                    {"axes": [], "test_points": []},
                )
                usage["axes"] = _ordered_union(usage["axes"], [axis_id])
                usage["test_points"] = _ordered_union(
                    usage["test_points"], [point_id]
                )
            execution_rules.append(execution_rule)
        generated_points.append(
            {
                "id": point_id,
                "title": f"Statement factor applicability: {statement_key}",
                "description": (
                    "One explicit executable obligation per covered canonical "
                    "statement-factor-value row."
                ),
                "requirement_ids": requirement_ids,
                "core_axes": [axis_id],
                "dependencies": [],
                "classification_rules": classification_rules,
                "execution_rules": execution_rules,
            }
        )

    risk_decisions = {
        risk_id: dict(decision)
        for risk_id, decision in base_document["risk_decisions"].items()
    }
    for harness_id, usage in harness_usage.items():
        matching_risks = [
            risk_id
            for risk_id, decision in risk_decisions.items()
            if decision.get("execution_harness") == harness_id
        ]
        if len(matching_risks) > 1:
            raise ApplicabilityValidationError(
                f"base coverage plan declares execution harness {harness_id} in "
                "multiple risk decisions; compiler merge is ambiguous"
            )
        if matching_risks:
            risk_id = matching_risks[0]
            decision = risk_decisions[risk_id]
            if decision.get("status") != "covered":
                raise ApplicabilityValidationError(
                    f"risk decision {risk_id} cannot route covered harness {harness_id}"
                )
            decision["axes"] = _ordered_union(
                decision.get("axes") or [], usage["axes"]
            )
            decision["test_points"] = _ordered_union(
                decision.get("test_points") or [], usage["test_points"]
            )
        else:
            risk_id = _generated_risk_id(harness_id)
            if risk_id in risk_decisions:
                raise ApplicabilityValidationError(
                    f"generated applicability risk ID collides with base risk {risk_id}"
                )
            risk_decisions[risk_id] = {
                "status": "covered",
                "axes": list(usage["axes"]),
                "test_points": list(usage["test_points"]),
                "execution_harness": harness_id,
            }

    base_digest = _canonical_document_sha256(base_document)
    metadata = dict(base_metadata)
    metadata[APPLICABILITY_COMPILER_METADATA_KEY] = {
        "schema_version": 1,
        "base_plan_sha256": base_digest,
        "feature_id": manifest.feature_id,
        "universe_semantic_sha256": applicability.universe.semantic_sha256,
        "covered_rows": applicability.summary.covered,
        "pending_rows": applicability.summary.pending,
        "canonical_upper_bound": applicability.universe.counts.statement_factor_values,
        "generated_axis_ids": list(generated_axes),
        "generated_test_point_ids": [point["id"] for point in generated_points],
    }
    compiled_document = dict(base_document)
    compiled_document["axes"] = {
        **base_document["axes"],
        **generated_axes,
    }
    compiled_document["risk_decisions"] = risk_decisions
    compiled_document["test_points"] = [
        *base_document["test_points"],
        *generated_points,
    ]
    compiled_document["metadata"] = metadata
    return (
        compiled_document,
        tuple(generated_axes),
        tuple(point["id"] for point in generated_points),
        base_digest,
    )


def _obligation_bindings_for_rows(
    applicability: FeatureApplicability,
    obligations: Sequence[Any],
) -> dict[str, ObligationBinding]:
    obligations_by_point: dict[str, list[Any]] = {}
    for obligation in obligations:
        point_id = _object_field(obligation, "test_point_id")
        if isinstance(point_id, str):
            obligations_by_point.setdefault(point_id, []).append(obligation)
    result: dict[str, ObligationBinding] = {}
    for row, review in applicability.covered_rows():
        point_id = applicability_test_point_id(row.statement_key)
        axis_id = applicability_axis_id(row.statement_key)
        matches = [
            obligation
            for obligation in obligations_by_point.get(point_id, [])
            if isinstance(_object_field(obligation, "assignments"), Mapping)
            and _object_field(obligation, "assignments").get(axis_id) == row.row_id
        ]
        if len(matches) != 1:
            raise ApplicabilityValidationError(
                f"compiled plan must produce exactly one obligation for covered row "
                f"{row.row_id}; got {len(matches)}"
            )
        obligation = matches[0]
        if (
            _object_field(obligation, "outcome") != review.planned_outcome
            or _object_field(obligation, "execution_profile")
            != review.execution_profile
            or _object_field(obligation, "execution_harness")
            != review.execution_harness
        ):
            raise ApplicabilityValidationError(
                f"compiled obligation route/outcome does not match covered row {row.row_id}"
            )
        binding = ObligationBinding(
            point_id,
            str(_object_field(obligation, "obligation_id")),
        )
        if review.binding is not None and review.binding != binding:
            raise ApplicabilityValidationError(
                f"covered row {row.row_id} existing binding would change from "
                f"{review.binding.obligation_id} to {binding.obligation_id}; use the "
                "same base plan/plan_id or create a new applicability review"
            )
        result[row.row_id] = binding
    if len({binding.obligation_id for binding in result.values()}) != len(result):
        raise ApplicabilityValidationError(
            "compiled applicability bindings are not one-to-one"
        )
    return result


def _review_and_index_payloads_with_bindings(
    applicability: FeatureApplicability,
    bindings: Mapping[str, ObligationBinding],
) -> tuple[dict[str, bytes], bytes]:
    index_document = _load_yaml(
        applicability.index_path,
        f"feature applicability index {applicability.index_path}",
    )
    references = tuple(
        _parse_review_reference(
            raw,
            f"feature applicability index {applicability.index_path}.reviews[{index}]",
        )
        for index, raw in enumerate(index_document["reviews"])
    )
    review_payloads: dict[str, bytes] = {}
    refreshed_references = []
    for reference in references:
        review_path = _resolve_contained_file(
            applicability.index_path.parent,
            reference.path,
            f"feature applicability review {reference.statement_key}",
        )
        try:
            original_payload = review_path.read_bytes()
        except OSError as exc:
            raise ApplicabilityValidationError(
                f"cannot read review {review_path}: {exc}"
            ) from exc
        document = _load_yaml(review_path, f"statement review {review_path}")
        changed = False
        for factor in document["factors"]:
            for value in factor["values"]:
                row_id = value["row_id"]
                binding = bindings.get(row_id)
                if binding is None:
                    continue
                decision = value["decision"]
                expected_binding = {
                    "test_point_id": binding.test_point_id,
                    "obligation_id": binding.obligation_id,
                }
                existing = decision.get("binding")
                if existing is None:
                    decision["binding"] = expected_binding
                    changed = True
                elif existing != expected_binding:
                    raise ApplicabilityValidationError(
                        f"covered row {row_id} review binding does not match compiled obligation"
                    )
        payload = _yaml_bytes(document) if changed else original_payload
        review_payloads[reference.path] = payload
        refreshed_references.append(
            {
                "statement_key": reference.statement_key,
                "path": reference.path,
                "sha256": hashlib.sha256(payload).hexdigest(),
            }
        )
    refreshed_index = {
        "schema_version": 1,
        "kind": INDEX_KIND,
        "feature_id": applicability.feature_id,
        "compatibility_target": applicability.compatibility_target,
        "universe": dict(index_document["universe"]),
        "reviews": refreshed_references,
    }
    return review_payloads, _yaml_bytes(refreshed_index)


def _require_all_covered_bindings_match(
    applicability: FeatureApplicability,
    report: "ApplicabilityBindingReconciliation",
) -> None:
    if (
        report.matched_obligations != applicability.summary.covered
        or report.missing_row_ids
        or report.unexpected_obligation_ids
        or report.mismatched_obligation_ids
    ):
        raise ApplicabilityValidationError(
            "compiled applicability obligation reconciliation failed: "
            + json.dumps(report.to_dict(), ensure_ascii=False, sort_keys=True)
        )


def _validate_existing_compiled_output(
    output_path: Path,
    *,
    base_digest: str,
    feature_id: str,
    universe_sha256: str,
) -> None:
    if not output_path.exists() and not output_path.is_symlink():
        return
    if output_path.is_symlink() or not output_path.is_file():
        raise ApplicabilityValidationError(
            f"compiled plan output must be a regular non-symlink file: {output_path}"
        )
    document = _load_yaml(output_path, f"existing compiled plan {output_path}")
    metadata = document.get("metadata")
    marker = (
        metadata.get(APPLICABILITY_COMPILER_METADATA_KEY)
        if isinstance(metadata, Mapping)
        else None
    )
    if (
        document.get("kind") != "coverage_plan"
        or not isinstance(marker, Mapping)
        or marker.get("base_plan_sha256") != base_digest
        or marker.get("feature_id") != feature_id
        or marker.get("universe_semantic_sha256") != universe_sha256
    ):
        raise ApplicabilityValidationError(
            "refusing to overwrite an output that is not a compiler artifact for "
            "this exact base plan, feature, and applicability universe"
        )


def compile_feature_applicability_plan(
    *,
    manifest_path: str | Path,
    base_plan_path: str | Path,
    index_path: str | Path,
    output_path: str | Path,
    repository_root: str | Path,
    source_root: str | Path | None = None,
    inventory_root: str | Path | None = None,
    expected_counts: UniverseCounts | None = SHIPPED_UNIVERSE_COUNTS,
) -> ApplicabilityCompilationResult:
    """Compile covered review rows into a separate deterministic coverage plan.

    Covered rows may omit ``binding`` in draft reviews.  All other covered-row
    evidence remains mandatory.  The compiler never edits the base plan and
    refuses a base that already contains reserved generated axes/points.
    """

    from .contracts import CoveragePlan, load_coverage_plan, load_feature_manifest
    from .coverage import expand_coverage_plan
    from .feature_plan import validate_coverage_plan

    repository = Path(repository_root).resolve(strict=True)
    manifest_file = Path(manifest_path)
    base_file = Path(base_plan_path)
    index_file = Path(index_path)
    output_file = Path(output_path)
    if output_file.resolve(strict=False) == base_file.resolve(strict=True):
        raise ApplicabilityValidationError(
            "compiled output must be separate from the immutable base coverage plan"
        )
    if output_file.resolve(strict=False) == index_file.resolve(strict=True):
        raise ApplicabilityValidationError(
            "compiled output must be separate from the applicability index"
        )

    manifest = load_feature_manifest(
        manifest_file,
        verify_source=True,
        source_root=source_root,
    )
    resolved_inventory_root = inventory_root or repository
    base_plan = load_coverage_plan(
        base_file,
        manifest=manifest,
        inventory_root=resolved_inventory_root,
    )
    requirement_ids = {
        requirement.requirement_id for requirement in manifest.requirements
    }
    draft_applicability = load_feature_applicability_index(
        index_file,
        repository_root=repository,
        known_requirement_ids=requirement_ids,
        require_complete=False,
        expected_counts=expected_counts,
        draft=True,
    )
    (
        compiled_document,
        generated_axis_ids,
        generated_test_point_ids,
        base_digest,
    ) = _build_compiled_plan_document(base_plan, manifest, draft_applicability)
    compiled_plan = CoveragePlan.from_dict(compiled_document)
    validate_coverage_plan(compiled_plan, manifest=manifest)
    obligations = expand_coverage_plan(compiled_plan, require_complete=True)
    bindings = _obligation_bindings_for_rows(draft_applicability, obligations)
    review_payloads, index_payload = _review_and_index_payloads_with_bindings(
        draft_applicability,
        bindings,
    )
    plan_payload = _yaml_bytes(compiled_plan.to_dict())

    _validate_existing_compiled_output(
        output_file,
        base_digest=base_digest,
        feature_id=manifest.feature_id,
        universe_sha256=draft_applicability.universe.semantic_sha256,
    )
    protected_paths = {
        manifest_file.resolve(strict=True),
        base_file.resolve(strict=True),
        index_file.resolve(strict=True),
        *(review.source_path.resolve(strict=True) for review in draft_applicability.reviews),
    }
    if output_file.resolve(strict=False) in protected_paths:
        raise ApplicabilityValidationError(
            "compiled output must not overwrite a manifest, base plan, index, or review"
        )

    with tempfile.TemporaryDirectory(prefix="pg-applicability-compile-") as temporary:
        staging_root = Path(temporary)
        staging_bundle = staging_root / "bundle"
        for relative, payload in review_payloads.items():
            _atomic_write(staging_bundle / PurePosixPath(relative), payload)
        staging_index = staging_bundle / "feature_applicability_index.yaml"
        _atomic_write(staging_index, index_payload)
        staging_plan = staging_root / "compiled_plan.yaml"
        _atomic_write(staging_plan, plan_payload)
        serialized_plan = load_coverage_plan(
            staging_plan,
            manifest=manifest,
            inventory_root=resolved_inventory_root,
        )
        serialized_obligations = expand_coverage_plan(
            serialized_plan,
            require_complete=True,
        )
        staged_applicability = load_feature_applicability_index(
            staging_index,
            repository_root=repository,
            known_requirement_ids=requirement_ids,
            require_complete=False,
            expected_counts=expected_counts,
            draft=False,
        )
        staged_report = reconcile_applicability_bindings(
            staged_applicability,
            serialized_obligations,
        )
        _require_all_covered_bindings_match(staged_applicability, staged_report)

    # Publish the compiled plan first, reviews next, and the refreshed index
    # last.  A process interruption can leave a hash mismatch, never a false
    # complete state; rerunning refresh/compile safely recovers it.
    _atomic_write(output_file, plan_payload)
    for review in draft_applicability.reviews:
        relative = review.source_path.relative_to(
            index_file.parent.resolve(strict=True)
        ).as_posix()
        payload = review_payloads[relative]
        if review.source_path.read_bytes() != payload:
            _atomic_write(review.source_path, payload)
    _atomic_write(index_file, index_payload)

    persisted_plan = load_coverage_plan(
        output_file,
        manifest=manifest,
        inventory_root=resolved_inventory_root,
    )
    persisted_obligations = expand_coverage_plan(
        persisted_plan,
        require_complete=True,
    )
    persisted_applicability = load_feature_applicability_index(
        index_file,
        repository_root=repository,
        known_requirement_ids=requirement_ids,
        require_complete=False,
        expected_counts=expected_counts,
        draft=False,
    )
    report = reconcile_applicability_bindings(
        persisted_applicability,
        persisted_obligations,
    )
    _require_all_covered_bindings_match(persisted_applicability, report)
    return ApplicabilityCompilationResult(
        output_path=output_file.resolve(strict=True),
        plan=persisted_plan,
        obligations=tuple(persisted_obligations),
        applicability=persisted_applicability,
        reconciliation=report,
        generated_axis_ids=generated_axis_ids,
        generated_test_point_ids=generated_test_point_ids,
        canonical_upper_bound=persisted_applicability.universe.counts.statement_factor_values,
    )


@dataclass(frozen=True)
class ApplicabilityBindingReconciliation:
    universe_rows: int
    covered_rows: int
    justified_exclusions: int
    pending_rows: int
    pending_statement_decisions: int
    pending_factor_decisions: int
    matched_obligations: int
    missing_row_ids: tuple[str, ...]
    unexpected_obligation_ids: tuple[str, ...]
    mismatched_obligation_ids: tuple[str, ...]
    cases_checked: bool
    test_point_id: Optional[str] = None
    matched_cases: int = 0
    missing_case_obligation_ids: tuple[str, ...] = ()
    unexpected_case_ids: tuple[str, ...] = ()
    mismatched_case_ids: tuple[str, ...] = ()

    @property
    def complete(self) -> bool:
        decision_complete = (
            self.universe_rows
            == self.covered_rows + self.justified_exclusions + self.pending_rows
            and self.pending_rows == 0
            and self.pending_statement_decisions == 0
            and self.pending_factor_decisions == 0
        )
        obligations_complete = (
            self.matched_obligations == self.covered_rows
            and not self.missing_row_ids
            and not self.unexpected_obligation_ids
            and not self.mismatched_obligation_ids
        )
        cases_complete = (
            not self.cases_checked
            or (
                self.matched_cases == self.covered_rows
                and not self.missing_case_obligation_ids
                and not self.unexpected_case_ids
                and not self.mismatched_case_ids
            )
        )
        return decision_complete and obligations_complete and cases_complete

    def to_dict(self) -> dict[str, Any]:
        return {
            "universe_rows": self.universe_rows,
            "covered_rows": self.covered_rows,
            "justified_exclusions": self.justified_exclusions,
            "pending_rows": self.pending_rows,
            "pending_statement_decisions": self.pending_statement_decisions,
            "pending_factor_decisions": self.pending_factor_decisions,
            "matched_obligations": self.matched_obligations,
            "missing_row_ids": list(self.missing_row_ids),
            "unexpected_obligation_ids": list(self.unexpected_obligation_ids),
            "mismatched_obligation_ids": list(self.mismatched_obligation_ids),
            "cases_checked": self.cases_checked,
            "test_point_id": self.test_point_id,
            "matched_cases": self.matched_cases,
            "missing_case_obligation_ids": list(self.missing_case_obligation_ids),
            "unexpected_case_ids": list(self.unexpected_case_ids),
            "mismatched_case_ids": list(self.mismatched_case_ids),
            "complete": self.complete,
        }


def _object_field(document: Any, field_name: str, default: Any = None) -> Any:
    if isinstance(document, Mapping):
        return document.get(field_name, default)
    return getattr(document, field_name, default)


def _canonical_claim(row: CatalogRow, review: ValueReview) -> dict[str, str]:
    assert review.matrix_witness is not None
    return {
        "row_id": row.row_id,
        "statement_key": row.statement_key,
        "factor": row.factor,
        "value": row.value,
        "matrix_path": review.matrix_witness.path,
        "matrix_sha256": review.matrix_witness.sha256,
        "combination_group_id": review.matrix_witness.combination_group_id,
    }


def reconcile_applicability_bindings(
    applicability: FeatureApplicability,
    obligations: Iterable[Any],
    *,
    cases: Iterable[Any] | None = None,
    test_point_id: str | None = None,
) -> ApplicabilityBindingReconciliation:
    """Reconcile covered rows to unique plan obligations and optional cases.

    Obligation objects may be mappings or dataclasses exposing
    ``obligation_id``, ``test_point_id``, ``assignments`` and ``outcome``.
    Each applicability obligation must carry the reserved statement-specific
    assignment ``applicability_row__<statement>=<row-id>``.

    When cases are supplied, each case must have one matching obligation plus
    ``metadata.applicability_claim`` equal to the canonical row/matrix witness.
    Passing ``cases=None`` intentionally performs planning-only reconciliation;
    passing an empty iterable checks the case layer and reports every case as
    missing.
    """

    scoped_reviews: tuple[StatementReview, ...] = applicability.reviews
    if test_point_id is not None:
        scoped_reviews = tuple(
            review
            for review in applicability.reviews
            if any(
                value.binding is not None
                and value.binding.test_point_id == test_point_id
                for factor in review.factors
                for value in factor.values
            )
        )
        if not scoped_reviews:
            scoped_reviews = tuple(
                review
                for review in applicability.reviews
                if applicability_test_point_id(review.statement_key) == test_point_id
            )
        if len(scoped_reviews) != 1:
            raise ApplicabilityValidationError(
                f"unknown or ambiguous applicability test point {test_point_id}"
            )
    scoped_row_ids = {
        value.row_id
        for review in scoped_reviews
        for factor in review.factors
        for value in factor.values
    }
    materialized_obligations = tuple(obligations)
    obligation_by_id: dict[str, Any] = {}
    for index, obligation in enumerate(materialized_obligations):
        obligation_id = _object_field(obligation, "obligation_id")
        if not isinstance(obligation_id, str) or not obligation_id:
            raise ApplicabilityValidationError(
                f"obligations[{index}].obligation_id must be a non-empty string"
            )
        if obligation_id in obligation_by_id:
            raise ApplicabilityValidationError(
                f"duplicate obligation_id {obligation_id}"
            )
        obligation_by_id[obligation_id] = obligation

    covered = tuple(
        (row, review)
        for row, review in applicability.covered_rows()
        if row.row_id in scoped_row_ids
    )
    expected_by_obligation: dict[str, tuple[CatalogRow, ValueReview]] = {}
    for row, review in covered:
        if review.binding is None:
            raise ApplicabilityValidationError(
                f"covered row {row.row_id} has no obligation binding"
            )
        if review.binding.obligation_id in expected_by_obligation:
            previous = expected_by_obligation[review.binding.obligation_id][0]
            raise ApplicabilityValidationError(
                f"covered rows {previous.row_id} and {row.row_id} bind the same "
                f"obligation {review.binding.obligation_id}"
            )
        expected_by_obligation[review.binding.obligation_id] = (row, review)

    missing_rows: list[str] = []
    mismatched_obligations: list[str] = []
    matched_obligations = 0
    for obligation_id, (row, review) in expected_by_obligation.items():
        obligation = obligation_by_id.get(obligation_id)
        if obligation is None:
            missing_rows.append(row.row_id)
            continue
        binding = review.binding
        assert binding is not None
        assignments = _object_field(obligation, "assignments")
        expected_axis = applicability_axis_id(row.statement_key)
        if (
            _object_field(obligation, "test_point_id") != binding.test_point_id
            or _object_field(obligation, "outcome") != review.planned_outcome
            or _object_field(obligation, "execution_profile")
            != review.execution_profile
            or _object_field(obligation, "execution_harness")
            != review.execution_harness
            or not isinstance(assignments, Mapping)
            or assignments.get(expected_axis) != row.row_id
        ):
            mismatched_obligations.append(obligation_id)
            continue
        matched_obligations += 1

    unexpected_obligations = []
    for obligation_id, obligation in obligation_by_id.items():
        assignments = _object_field(obligation, "assignments")
        if not isinstance(assignments, Mapping):
            continue
        if (
            test_point_id is not None
            and _object_field(obligation, "test_point_id") != test_point_id
        ):
            continue
        if any(str(key).startswith(APPLICABILITY_AXIS_PREFIX) for key in assignments):
            if obligation_id not in expected_by_obligation:
                unexpected_obligations.append(obligation_id)

    cases_checked = cases is not None
    matched_cases = 0
    missing_case_obligation_ids: list[str] = []
    unexpected_case_ids: list[str] = []
    mismatched_case_ids: list[str] = []
    if cases is not None:
        materialized_cases = tuple(cases)
        case_by_obligation: dict[str, Any] = {}
        seen_case_ids: set[str] = set()
        sql_hash_owner: dict[str, str] = {}
        for index, case in enumerate(materialized_cases):
            case_id = _object_field(case, "case_id")
            obligation_id = _object_field(case, "obligation_id")
            if not isinstance(case_id, str) or not case_id:
                raise ApplicabilityValidationError(
                    f"cases[{index}].case_id must be a non-empty string"
                )
            if case_id in seen_case_ids:
                raise ApplicabilityValidationError(f"duplicate case_id {case_id}")
            seen_case_ids.add(case_id)
            metadata = _object_field(case, "metadata", {})
            claim = metadata.get("applicability_claim") if isinstance(metadata, Mapping) else None
            is_expected = obligation_id in expected_by_obligation
            if not is_expected:
                if (
                    claim is not None
                    and (
                        test_point_id is None
                        or _object_field(case, "test_point_id") == test_point_id
                    )
                ):
                    unexpected_case_ids.append(case_id)
                continue
            if obligation_id in case_by_obligation:
                unexpected_case_ids.append(case_id)
                mismatched_case_ids.append(_object_field(case_by_obligation[obligation_id], "case_id"))
                continue
            case_by_obligation[obligation_id] = case
            row, review = expected_by_obligation[obligation_id]
            binding = review.binding
            assert binding is not None
            assignments = metadata.get("assignments") if isinstance(metadata, Mapping) else None
            expected_axis = applicability_axis_id(row.statement_key)
            actual_claim = dict(claim) if isinstance(claim, Mapping) else None
            if (
                _object_field(case, "test_point_id") != binding.test_point_id
                or _object_field(case, "outcome") != review.planned_outcome
                or _object_field(case, "execution_profile")
                != review.execution_profile
                or _object_field(case, "execution_harness")
                != review.execution_harness
                or not isinstance(assignments, Mapping)
                or assignments.get(expected_axis) != row.row_id
                or actual_claim != _canonical_claim(row, review)
            ):
                mismatched_case_ids.append(case_id)
                continue
            sql_sha256 = _object_field(case, "sql_sha256")
            if not isinstance(sql_sha256, str) or not SHA256_PATTERN.fullmatch(sql_sha256):
                mismatched_case_ids.append(case_id)
                continue
            previous_owner = sql_hash_owner.setdefault(sql_sha256, case_id)
            if previous_owner != case_id:
                mismatched_case_ids.extend((previous_owner, case_id))
                continue
            matched_cases += 1
        missing_case_obligation_ids.extend(
            obligation_id
            for obligation_id in expected_by_obligation
            if obligation_id not in case_by_obligation
        )

    summary = _summarize_reviews(scoped_reviews)
    return ApplicabilityBindingReconciliation(
        universe_rows=summary.total,
        covered_rows=summary.covered,
        justified_exclusions=summary.justified_exclusion,
        pending_rows=summary.pending,
        pending_statement_decisions=summary.pending_statement_decisions,
        pending_factor_decisions=summary.pending_factor_decisions,
        matched_obligations=matched_obligations,
        missing_row_ids=tuple(missing_rows),
        unexpected_obligation_ids=tuple(unexpected_obligations),
        mismatched_obligation_ids=tuple(dict.fromkeys(mismatched_obligations)),
        cases_checked=cases_checked,
        test_point_id=test_point_id,
        matched_cases=matched_cases,
        missing_case_obligation_ids=tuple(missing_case_obligation_ids),
        unexpected_case_ids=tuple(dict.fromkeys(unexpected_case_ids)),
        mismatched_case_ids=tuple(dict.fromkeys(mismatched_case_ids)),
    )


__all__ = [
    "APPLICABILITY_AXIS_PREFIX",
    "APPLICABILITY_TEST_POINT_PREFIX",
    "ApplicabilityCompilationResult",
    "ApplicabilityBindingReconciliation",
    "ApplicabilitySummary",
    "ApplicabilityUniverse",
    "ApplicabilityValidationError",
    "CatalogRow",
    "COMPATIBILITY_TARGET",
    "DEFAULT_LEDGER_PATH",
    "FeatureApplicability",
    "MatrixWitnessCoverageAudit",
    "SHIPPED_UNIVERSE_COUNTS",
    "SHIPPED_UNIVERSE_SEMANTIC_SHA256",
    "UniverseCounts",
    "applicability_axis_id",
    "applicability_test_point_id",
    "audit_universe_matrix_witness_coverage",
    "compile_feature_applicability_plan",
    "load_applicability_universe",
    "load_feature_applicability_index",
    "load_shipped_applicability_universe",
    "reconcile_applicability_bindings",
    "refresh_feature_applicability_index",
    "scaffold_feature_applicability",
    "stable_catalog_row_id",
]
