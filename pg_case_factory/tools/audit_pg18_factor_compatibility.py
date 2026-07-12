from __future__ import annotations

import argparse
import csv
import hashlib
import io
import re
import sys
from collections.abc import Mapping
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import yaml


YAML_BLOCK_PATTERN = re.compile(r"```yaml\s*(.*?)```", re.DOTALL)
REFENTRY_ID_PATTERN = re.compile(r"<refentry\s+id=\"([^\"]+)\"", re.IGNORECASE)
SYNOPSIS_PATTERN = re.compile(r"<refsynopsisdiv(?:\s[^>]*)?>(.*?)</refsynopsisdiv>", re.IGNORECASE | re.DOTALL)
COMMENT_PATTERN = re.compile(r"<!--.*?-->", re.DOTALL)
TAG_PATTERN = re.compile(r"<[^>]+>", re.DOTALL)

DEFAULT_PROFILE = Path("skills/pg-sql-generation/references/common/compatibility_profile.yaml")
DEFAULT_INVENTORY = Path("skills/pg-sql-generation/references/common/statement_support_inventory.yaml")
DEFAULT_LEDGER = Path(
    "skills/pg-sql-generation/references/common/postgresql_18_4_factor_audit.tsv"
)
STATEMENTS_ROOT = Path("skills/pg-sql-generation/references/statements")
COMBINATIONS_ROOT = Path("skills/pg-sql-generation/references/combinations")

READY_REVIEW_STATUSES = {"synopsis_adapted", "semantic_reviewed", "runtime_verified"}
ALLOWED_REVIEW_STATUSES = READY_REVIEW_STATUSES | {"pending_semantic_review", "blocked"}


@dataclass(frozen=True)
class SgmlDocument:
    ref_id: str
    path: Path
    synopsis: str
    document: str
    synopsis_sha256: str
    document_sha256: str


@dataclass(frozen=True)
class LedgerRow:
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


@dataclass
class StatementRecord:
    statement_key: str
    source_reference: str
    sgml_ref_id: str
    official_source_baseline: str
    official_source_target: str
    synopsis_change: str
    document_change: str
    baseline_synopsis_sha256: str
    target_synopsis_sha256: str
    baseline_document_sha256: str
    target_document_sha256: str
    support_status: str
    static_catalog_ready: bool
    factor_count: int
    factor_value_rows: int
    required_test_points: list[str]
    affected_factors: dict[str, list[str]]
    test_point_affected_values: dict[str, dict[str, list[str]]]
    review_note: str


@dataclass
class AuditResult:
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    records: list[StatementRecord] = field(default_factory=list)
    ledger_rows: list[LedgerRow] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        return not self.errors and self.pending_static_review_count == 0

    @property
    def statement_count(self) -> int:
        return len(self.records)

    @property
    def factor_count(self) -> int:
        return sum(item.factor_count for item in self.records)

    @property
    def value_count(self) -> int:
        return len(self.ledger_rows)

    @property
    def static_catalog_ready_count(self) -> int:
        return sum(item.static_catalog_ready for item in self.records)

    @property
    def pending_static_review_count(self) -> int:
        return self.statement_count - self.static_catalog_ready_count

    @property
    def runtime_verified_statement_count(self) -> int:
        return sum(item.support_status == "runtime_verified" for item in self.records)

    @property
    def changed_synopsis_count(self) -> int:
        return sum(item.synopsis_change == "changed" for item in self.records)

    @property
    def changed_document_count(self) -> int:
        return sum(item.document_change == "changed" for item in self.records)


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _sgml_tree_identity(root: Path) -> tuple[int, str]:
    paths = sorted(root.glob("*.sgml"))
    digest = hashlib.sha256()
    for path in paths:
        digest.update(path.name.encode("utf-8"))
        digest.update(b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")
    return len(paths), digest.hexdigest()


def _validate_sgml_provenance(profile: Mapping[str, Any], role: str, root: Path) -> None:
    version = dict(profile.get(role) or {})
    expected_count = version.get("sgml_ref_file_count")
    expected_digest = str(version.get("sgml_ref_tree_sha256") or "")
    if expected_count is None and not expected_digest:
        return
    actual_count, actual_digest = _sgml_tree_identity(root)
    if expected_count is not None and actual_count != expected_count:
        raise ValueError(
            f"{role} SGML reference file count mismatch: expected {expected_count}, got {actual_count}"
        )
    if expected_digest and actual_digest != expected_digest:
        raise ValueError(
            f"{role} SGML reference tree SHA256 mismatch: expected {expected_digest}, got {actual_digest}"
        )


def _visible_text(raw: str) -> str:
    without_comments = COMMENT_PATTERN.sub(" ", raw)
    without_tags = TAG_PATTERN.sub(" ", without_comments)
    return re.sub(r"\s+", " ", without_tags).strip()


def _load_sgml_documents(root: Path) -> tuple[dict[str, SgmlDocument], dict[str, SgmlDocument]]:
    by_ref_id: dict[str, SgmlDocument] = {}
    by_stem: dict[str, SgmlDocument] = {}
    if not root.exists() or not root.is_dir():
        raise ValueError(f"SGML reference root does not exist: {root}")
    for path in sorted(root.glob("*.sgml")):
        raw = path.read_text(encoding="utf-8")
        id_match = REFENTRY_ID_PATTERN.search(raw)
        if not id_match:
            continue
        synopsis_match = SYNOPSIS_PATTERN.search(raw)
        synopsis = _visible_text(synopsis_match.group(1) if synopsis_match else "")
        document = _visible_text(raw)
        doc = SgmlDocument(
            ref_id=id_match.group(1),
            path=path,
            synopsis=synopsis,
            document=document,
            synopsis_sha256=_sha256(synopsis),
            document_sha256=_sha256(document),
        )
        by_ref_id[doc.ref_id] = doc
        by_stem[path.stem] = doc
    return by_ref_id, by_stem


def _load_yaml(path: Path) -> dict[str, Any]:
    parsed = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(parsed, Mapping):
        raise ValueError(f"{path}: YAML root must be a mapping")
    return dict(parsed)


def _load_statement(path: Path) -> dict[str, Any]:
    raw = path.read_text(encoding="utf-8")
    match = YAML_BLOCK_PATTERN.search(raw)
    if not match:
        raise ValueError(f"{path}: no fenced YAML block found")
    parsed = yaml.safe_load(match.group(1)) or {}
    if not isinstance(parsed, Mapping):
        raise ValueError(f"{path}: structured YAML must be a mapping")
    config = parsed.get("structured_config", parsed)
    if not isinstance(config, Mapping):
        raise ValueError(f"{path}: structured_config must be a mapping")
    return dict(config)


def _statement_key(config: Mapping[str, Any]) -> str:
    statement = config.get("statement") or {}
    if isinstance(statement, Mapping):
        return str(statement.get("key") or "")
    return ""


def _source_slug(official_source: str) -> str:
    path_name = Path(urlparse(official_source).path).name
    return path_name[:-5] if path_name.endswith(".html") else path_name


def _resolve_sgml_document(
    *,
    config: Mapping[str, Any],
    statement_path: Path,
    by_ref_id: Mapping[str, SgmlDocument],
    by_stem: Mapping[str, SgmlDocument],
    aliases: Mapping[str, Any],
) -> SgmlDocument | None:
    key = _statement_key(config)
    source_slug = _source_slug(str(config.get("official_source") or ""))
    alias = str(aliases.get(source_slug) or aliases.get(key) or "")
    candidates = [source_slug, alias, f"sql-{key.replace('_', '')}", key, statement_path.stem]
    for candidate in candidates:
        if not candidate:
            continue
        if candidate in by_ref_id:
            return by_ref_id[candidate]
        if candidate in by_stem:
            return by_stem[candidate]
    return None


def _factor_tiers(config: Mapping[str, Any]) -> dict[str, str]:
    tiers: dict[str, str] = {}
    for layer in config.get("factor_layers") or []:
        if not isinstance(layer, Mapping):
            continue
        tier = str(layer.get("tier") or "")
        for factor in layer.get("factors") or []:
            tiers[str(factor)] = tier
    return tiers


def _value_key(value: Any) -> str:
    if isinstance(value, Mapping):
        return str(value.get("key") or "")
    if isinstance(value, bool):
        return str(value).lower()
    return str(value)


def _factor_values(config: Mapping[str, Any]) -> dict[str, list[str]]:
    result: dict[str, list[str]] = {}
    factors = config.get("factors") or {}
    if not isinstance(factors, Mapping):
        return result
    for name, raw_doc in factors.items():
        factor_doc = dict(raw_doc) if isinstance(raw_doc, Mapping) else {}
        result[str(name)] = [_value_key(value) for value in factor_doc.get("values") or [] if _value_key(value)]
    return result


def _load_matrix_test_points(root: Path, target_version: str) -> dict[str, dict[str, dict[str, Any]]]:
    by_statement: dict[str, dict[str, dict[str, Any]]] = {}
    combinations = root / COMBINATIONS_ROOT
    if not combinations.exists():
        return by_statement
    for path in sorted(combinations.glob("**/*.yaml")):
        if "_shared" in path.relative_to(combinations).parts:
            continue
        matrix = _load_yaml(path)
        statement = matrix.get("statement") or {}
        if not isinstance(statement, Mapping):
            continue
        key = str(statement.get("key") or "")
        compatibility = matrix.get("pg18_compatibility") or {}
        if not isinstance(compatibility, Mapping):
            continue
        declared_target = str(compatibility.get("target_version") or "")
        if declared_target and declared_target != target_version:
            continue
        points: dict[str, dict[str, Any]] = {}
        for raw_point in compatibility.get("test_points") or []:
            if not isinstance(raw_point, Mapping):
                continue
            point = dict(raw_point)
            point_id = str(point.get("id") or "")
            if point_id:
                points[point_id] = point
        by_statement[key] = points
    return by_statement


def _official_version_source(source: str, profile: Mapping[str, Any], version_role: str) -> str:
    docs_base = str(dict(profile.get(version_role) or {}).get("docs_base") or "")
    slug = _source_slug(source)
    return f"{docs_base.rstrip('/')}/{slug}.html" if docs_base and slug else ""


def _validate_statement_compatibility_metadata(
    *,
    result: AuditResult,
    key: str,
    config: Mapping[str, Any],
    expected_status: str,
    expected_source: str,
    target_version: str,
) -> None:
    metadata = config.get("pg18_compatibility") or {}
    if not isinstance(metadata, Mapping):
        result.errors.append(f"{key}: pg18_compatibility must be a mapping")
        return
    if not metadata:
        result.errors.append(f"{key}: changed official document requires statement pg18_compatibility metadata")
        return
    if str(metadata.get("target_version") or "") != target_version:
        result.errors.append(f"{key}: statement pg18_compatibility.target_version must be {target_version}")
    if str(metadata.get("review_status") or "") != expected_status:
        result.errors.append(f"{key}: statement pg18_compatibility.review_status must be {expected_status}")
    if str(metadata.get("official_source") or "") != expected_source:
        result.errors.append(f"{key}: statement pg18_compatibility.official_source must be {expected_source}")


def _review_status(
    *,
    result: AuditResult,
    key: str,
    synopsis_change: str,
    document_change: str,
    review: Mapping[str, Any],
    factor_values: Mapping[str, list[str]],
    test_points: Mapping[str, Mapping[str, Any]],
    target_version: str,
) -> tuple[
    str,
    bool,
    dict[str, list[str]],
    list[str],
    dict[str, dict[str, list[str]]],
    str,
]:
    if synopsis_change == "missing" or document_change == "missing":
        result.errors.append(f"{key}: official SGML reference is missing in one or both versions")
        return "blocked", False, {}, [], {}, "Official SGML reference could not be resolved."

    if synopsis_change == "unchanged" and document_change == "unchanged":
        return "static_reviewed", True, {}, [], {}, "Official statement document is semantically identical after normalization."

    status = str(review.get("status") or "")
    note = str(review.get("note") or "").strip()
    reviewed_against = str(review.get("reviewed_against") or "")
    required_points = [str(item) for item in review.get("required_test_points") or []]
    raw_affected = review.get("affected_factors")
    if raw_affected is None:
        raw_affected = {}
    affected: dict[str, list[str]] = {}
    expanded_affected: dict[str, set[str]] = {}
    invalid_affected = False
    if isinstance(raw_affected, Mapping):
        for factor, values in raw_affected.items():
            factor_name = str(factor)
            if not isinstance(values, list):
                result.errors.append(
                    f"{key}: review affected_factors.{factor_name} must be a list"
                )
                invalid_affected = True
                continue
            affected_values = [_value_key(item) for item in values]
            affected[factor_name] = affected_values
            if factor_name in factor_values:
                expanded_affected[factor_name] = (
                    set(factor_values[factor_name]) if not affected_values else set(affected_values)
                )
    else:
        result.errors.append(f"{key}: review affected_factors must be a mapping")
        invalid_affected = True

    if not status:
        if synopsis_change == "changed":
            result.errors.append(f"{key}: changed PG18 synopsis has no completed review")
            return "pending_review", False, affected, required_points, {}, "Synopsis change requires adaptation."
        return "pending_semantic_review", False, affected, required_points, {}, "Statement body changed and requires semantic review."

    if status not in ALLOWED_REVIEW_STATUSES:
        result.errors.append(f"{key}: unsupported review status: {status}")
        return "pending_review", False, affected, required_points, {}, note
    if status in READY_REVIEW_STATUSES:
        if reviewed_against != target_version:
            result.errors.append(f"{key}: ready review must declare reviewed_against={target_version}")
        if not note:
            result.errors.append(f"{key}: ready review must include a note")
        if synopsis_change == "changed" and status not in {"synopsis_adapted", "runtime_verified"}:
            result.errors.append(f"{key}: changed synopsis must use synopsis_adapted or runtime_verified")

    for factor, values in affected.items():
        if factor not in factor_values:
            result.errors.append(f"{key}: review references unknown factor: {factor}")
            invalid_affected = True
            continue
        unknown_values = sorted(set(values) - set(factor_values[factor]))
        if unknown_values:
            result.errors.append(f"{key}: review references unknown factor values: {factor}={', '.join(unknown_values)}")
            invalid_affected = True

    missing_points = sorted(set(required_points) - set(test_points))
    if missing_points:
        result.errors.append(f"{key}: missing PG18 test point(s): {', '.join(missing_points)}")

    point_value_coverage: dict[str, set[str]] = {}
    point_affected_values: dict[str, dict[str, list[str]]] = {}
    invalid_point_affected_values = False
    for point_id in required_points:
        point = test_points.get(point_id)
        if not point:
            continue
        if not point.get("sql"):
            result.errors.append(f"{key}: PG18 test point {point_id} must define sql")
        if point.get("oracle") != "reference_parity":
            result.errors.append(f"{key}: PG18 test point {point_id} must use oracle=reference_parity")
        raw_point_factors = point.get("affected_factors")
        point_factors = (
            {str(item) for item in raw_point_factors}
            if isinstance(raw_point_factors, list)
            else set()
        )
        if not point_factors:
            result.errors.append(f"{key}: PG18 test point {point_id} must declare affected_factors")
            invalid_point_affected_values = True
        unknown_point_factors = sorted(point_factors - set(factor_values))
        if unknown_point_factors:
            result.errors.append(
                f"{key}: PG18 test point {point_id} references unknown factors: {', '.join(unknown_point_factors)}"
            )
            invalid_point_affected_values = True

        raw_point_values = point.get("affected_values")
        if not isinstance(raw_point_values, Mapping) or not raw_point_values:
            result.errors.append(
                f"{key}: PG18 test point {point_id} must declare a non-empty affected_values mapping"
            )
            invalid_point_affected_values = True
            continue

        point_value_factors = {str(factor) for factor in raw_point_values}
        if point_factors != point_value_factors:
            result.errors.append(
                f"{key}: PG18 test point {point_id} affected_factors must exactly match affected_values keys"
            )
            invalid_point_affected_values = True

        normalized_point_values: dict[str, list[str]] = {}
        for raw_factor, raw_values in raw_point_values.items():
            factor = str(raw_factor)
            if factor not in factor_values:
                result.errors.append(
                    f"{key}: PG18 test point {point_id} affected_values references unknown factor: {factor}"
                )
                invalid_point_affected_values = True
                continue
            if not isinstance(raw_values, list):
                result.errors.append(
                    f"{key}: PG18 test point {point_id} affected_values.{factor} must be a list"
                )
                invalid_point_affected_values = True
                continue
            if not raw_values:
                result.errors.append(
                    f"{key}: PG18 test point {point_id} affected_values.{factor} must be a non-empty explicit value list"
                )
                invalid_point_affected_values = True
                continue
            declared_values = {_value_key(item) for item in raw_values}
            unknown_values = sorted(declared_values - set(factor_values[factor]))
            if unknown_values:
                result.errors.append(
                    f"{key}: PG18 test point {point_id} references unknown affected values: "
                    f"{factor}={', '.join(unknown_values)}"
                )
                invalid_point_affected_values = True
                continue
            expanded_values = declared_values
            reviewed_values = expanded_affected.get(factor)
            if reviewed_values is None:
                result.errors.append(
                    f"{key}: PG18 test point {point_id} claims factor not declared affected by review: {factor}"
                )
                invalid_point_affected_values = True
                continue
            undeclared_values = sorted(expanded_values - reviewed_values)
            if undeclared_values:
                result.errors.append(
                    f"{key}: PG18 test point {point_id} claims values not declared affected by review: "
                    f"{factor}={', '.join(undeclared_values)}"
                )
                invalid_point_affected_values = True
                continue
            point_value_coverage.setdefault(factor, set()).update(expanded_values)
            normalized_point_values[factor] = sorted(expanded_values)
        if normalized_point_values:
            point_affected_values[point_id] = normalized_point_values

    if affected and not required_points:
        result.errors.append(
            f"{key}: reviewed affected factors require at least one PG18 reference-parity test point"
        )
    uncovered_affected_values: dict[str, list[str]] = {}
    for factor, values in expanded_affected.items():
        missing_values = sorted(values - point_value_coverage.get(factor, set()))
        if missing_values:
            uncovered_affected_values[factor] = missing_values
            result.errors.append(
                f"{key}: reviewed affected values have no PG18 test point coverage: "
                f"{factor}={', '.join(missing_values)}"
            )

    ready = (
        status in READY_REVIEW_STATUSES
        and not missing_points
        and not invalid_affected
        and not invalid_point_affected_values
        and not uncovered_affected_values
        and (not affected or bool(required_points))
        and reviewed_against == target_version
        and bool(note)
    )
    return (
        status if ready or status not in READY_REVIEW_STATUSES else "pending_review",
        ready,
        affected,
        required_points,
        point_affected_values,
        note,
    )


def audit_repository(
    root: Path,
    profile_path: Path,
    baseline_sgml_root: Path,
    target_sgml_root: Path,
) -> AuditResult:
    root = root.resolve()
    profile_path = profile_path if profile_path.is_absolute() else root / profile_path
    profile = _load_yaml(profile_path)
    if profile.get("kind") != "postgresql_compatibility_profile":
        raise ValueError(f"{profile_path}: kind must be postgresql_compatibility_profile")
    baseline_version = str(dict(profile.get("baseline") or {}).get("version") or "")
    target_version = str(dict(profile.get("target") or {}).get("version") or "")
    if not baseline_version or not target_version:
        raise ValueError(f"{profile_path}: baseline.version and target.version are required")
    if not dict(profile.get("baseline") or {}).get("docs_base"):
        raise ValueError(f"{profile_path}: baseline.docs_base is required")
    if not dict(profile.get("target") or {}).get("docs_base"):
        raise ValueError(f"{profile_path}: target.docs_base is required")

    _validate_sgml_provenance(profile, "baseline", baseline_sgml_root)
    _validate_sgml_provenance(profile, "target", target_sgml_root)

    baseline_by_id, baseline_by_stem = _load_sgml_documents(baseline_sgml_root)
    target_by_id, target_by_stem = _load_sgml_documents(target_sgml_root)
    aliases = dict(profile.get("sgml_ref_aliases") or {})
    reviews = dict(profile.get("statement_reviews") or {})
    policy = dict(profile.get("policy") or {})
    matrix_points = _load_matrix_test_points(root, target_version)
    result = AuditResult()

    statements_root = root / STATEMENTS_ROOT
    for statement_path in sorted(statements_root.glob("**/*.md")):
        config = _load_statement(statement_path)
        key = _statement_key(config)
        if not key:
            result.errors.append(f"{statement_path}: statement.key is required")
            continue
        baseline_doc = _resolve_sgml_document(
            config=config,
            statement_path=statement_path,
            by_ref_id=baseline_by_id,
            by_stem=baseline_by_stem,
            aliases=aliases,
        )
        target_doc = _resolve_sgml_document(
            config=config,
            statement_path=statement_path,
            by_ref_id=target_by_id,
            by_stem=target_by_stem,
            aliases=aliases,
        )
        if baseline_doc and target_doc:
            synopsis_change = "unchanged" if baseline_doc.synopsis == target_doc.synopsis else "changed"
            document_change = "unchanged" if baseline_doc.document == target_doc.document else "changed"
            ref_id = target_doc.ref_id
        else:
            synopsis_change = "missing"
            document_change = "missing"
            ref_id = (target_doc or baseline_doc).ref_id if (target_doc or baseline_doc) else ""

        values_by_factor = _factor_values(config)
        factor_tiers = _factor_tiers(config)
        review = dict(reviews.get(key) or {})
        status, ready, affected, required_points, point_affected_values, note = _review_status(
            result=result,
            key=key,
            synopsis_change=synopsis_change,
            document_change=document_change,
            review=review,
            factor_values=values_by_factor,
            test_points=matrix_points.get(key, {}),
            target_version=target_version,
        )

        source_reference = statement_path.relative_to(root / "skills" / "pg-sql-generation").as_posix()
        declared_official_source = str(config.get("official_source") or "")
        official_baseline = _official_version_source(
            declared_official_source, profile, "baseline"
        )
        official_target = _official_version_source(
            declared_official_source, profile, "target"
        )
        if policy.get("require_changed_statement_metadata") is True and document_change == "changed":
            _validate_statement_compatibility_metadata(
                result=result,
                key=key,
                config=config,
                expected_status=status,
                expected_source=official_target,
                target_version=target_version,
            )
        record = StatementRecord(
            statement_key=key,
            source_reference=source_reference,
            sgml_ref_id=ref_id,
            official_source_baseline=official_baseline,
            official_source_target=official_target,
            synopsis_change=synopsis_change,
            document_change=document_change,
            baseline_synopsis_sha256=baseline_doc.synopsis_sha256 if baseline_doc else "",
            target_synopsis_sha256=target_doc.synopsis_sha256 if target_doc else "",
            baseline_document_sha256=baseline_doc.document_sha256 if baseline_doc else "",
            target_document_sha256=target_doc.document_sha256 if target_doc else "",
            support_status=status,
            static_catalog_ready=ready,
            factor_count=len(values_by_factor),
            factor_value_rows=sum(len(values) for values in values_by_factor.values()),
            required_test_points=required_points,
            affected_factors=affected,
            test_point_affected_values=point_affected_values,
            review_note=note,
        )
        result.records.append(record)

        point_ids_by_factor_value: dict[tuple[str, str], list[str]] = {}
        for point_id, point_factors in point_affected_values.items():
            for factor, values in point_factors.items():
                for value in values:
                    point_ids_by_factor_value.setdefault((factor, value), []).append(point_id)

        for factor, values in sorted(values_by_factor.items()):
            affected_values = affected.get(factor)
            for value in values:
                is_affected = affected_values is not None and (not affected_values or value in affected_values)
                if is_affected:
                    disposition = "adapted" if ready else "pending_adaptation"
                elif status == "static_reviewed":
                    disposition = "inherited_unchanged"
                elif ready:
                    disposition = "reviewed_unaffected"
                else:
                    disposition = "pending_review"
                evidence = f"{ref_id}:{target_doc.synopsis_sha256[:12] if target_doc else 'missing'}"
                result.ledger_rows.append(
                    LedgerRow(
                        statement_key=key,
                        source_reference=source_reference,
                        factor=factor,
                        tier=factor_tiers.get(factor, "unassigned"),
                        value=value,
                        synopsis_change=synopsis_change,
                        document_change=document_change,
                        review_status=status,
                        catalog_readiness="static_ready" if ready else "pending_static_review",
                        factor_disposition=disposition,
                        required_test_points=",".join(point_ids_by_factor_value.get((factor, value), [])),
                        official_source_target=official_target,
                        evidence=evidence,
                    )
                )

    result.records.sort(key=lambda item: item.statement_key)
    result.ledger_rows.sort(key=lambda item: (item.statement_key, item.factor, item.value))
    return result


def render_support_inventory(result: AuditResult, profile_path: Path) -> str:
    payload = {
        "schema_version": 1,
        "kind": "statement_support_inventory",
        "compatibility_profile": profile_path.as_posix(),
        "summary": {
            "statements": result.statement_count,
            "static_catalog_ready": result.static_catalog_ready_count,
            "pending_static_review": result.pending_static_review_count,
            "runtime_verified_statements": result.runtime_verified_statement_count,
            "synopsis_changed": result.changed_synopsis_count,
            "document_changed": result.changed_document_count,
            "statement_factor_pairs": result.factor_count,
            "statement_factor_value_rows": result.value_count,
        },
        "statements": [asdict(item) for item in result.records],
    }
    return yaml.safe_dump(payload, sort_keys=False, allow_unicode=True, width=120)


def render_factor_ledger(result: AuditResult) -> str:
    output = io.StringIO(newline="")
    fieldnames = [field.name for field in LedgerRow.__dataclass_fields__.values()]
    writer = csv.DictWriter(output, fieldnames=fieldnames, delimiter="\t", lineterminator="\n")
    writer.writeheader()
    for row in result.ledger_rows:
        writer.writerow(asdict(row))
    return output.getvalue()


def _write_or_check(path: Path, content: str, *, write: bool, result: AuditResult) -> None:
    if write:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        return
    if not path.exists():
        result.errors.append(f"generated audit artifact is missing: {path}")
        return
    if path.read_text(encoding="utf-8") != content:
        result.errors.append(f"generated audit artifact is stale: {path}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Audit statement factors against PostgreSQL SGML versions.")
    parser.add_argument("--root", type=Path, default=Path.cwd(), help="pg_case_factory root")
    parser.add_argument("--profile", type=Path, default=DEFAULT_PROFILE)
    parser.add_argument("--baseline-sgml-root", type=Path, required=True)
    parser.add_argument("--target-sgml-root", type=Path, required=True)
    parser.add_argument("--inventory", type=Path, default=DEFAULT_INVENTORY)
    parser.add_argument("--ledger", type=Path, default=DEFAULT_LEDGER)
    parser.add_argument("--write", action="store_true", help="write deterministic inventory and ledger instead of checking them")
    args = parser.parse_args(argv)

    root = args.root.resolve()
    profile = args.profile if args.profile.is_absolute() else root / args.profile
    inventory = args.inventory if args.inventory.is_absolute() else root / args.inventory
    ledger = args.ledger if args.ledger.is_absolute() else root / args.ledger
    try:
        result = audit_repository(root, profile, args.baseline_sgml_root, args.target_sgml_root)
        _write_or_check(inventory, render_support_inventory(result, args.profile), write=args.write, result=result)
        _write_or_check(ledger, render_factor_ledger(result), write=args.write, result=result)
    except (OSError, ValueError, yaml.YAMLError) as exc:
        print(f"ERROR: {exc}")
        return 1

    for warning in result.warnings:
        print(f"WARNING: {warning}")
    for error in result.errors:
        print(f"ERROR: {error}")
    summary = (
        f"statements={result.statement_count} static_catalog_ready={result.static_catalog_ready_count} "
        f"pending_static_review={result.pending_static_review_count} "
        f"runtime_verified_statements={result.runtime_verified_statement_count} "
        f"statement_factor_pairs={result.factor_count} "
        f"statement_factor_value_rows={result.value_count} "
        f"synopsis_changed={result.changed_synopsis_count} document_changed={result.changed_document_count}"
    )
    if result.passed:
        print(f"PASS static PostgreSQL 18.4 catalog compatibility audit: {summary}")
        return 0
    print(f"FAIL PostgreSQL factor compatibility audit: {summary} errors={len(result.errors)}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
