from __future__ import annotations

import csv
import hashlib
import itertools
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Mapping

import yaml

from .applicability import LEDGER_COLUMNS
from .matrix_generation import load_statement_reference


@dataclass
class EditionKnowledgeReport:
    edition_id: str = ""
    statement_count: int = 0
    matrix_count: int = 0
    factor_pair_count: int = 0
    factor_value_count: int = 0
    unreviewed_count: int = 0
    errors: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.errors

    def to_dict(self) -> dict[str, Any]:
        return {
            "edition_id": self.edition_id,
            "ok": self.ok,
            "statement_count": self.statement_count,
            "matrix_count": self.matrix_count,
            "factor_pair_count": self.factor_pair_count,
            "factor_value_count": self.factor_value_count,
            "unreviewed_count": self.unreviewed_count,
            "errors": list(self.errors),
        }


def _load_mapping(path: Path) -> dict[str, Any]:
    document = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(document, Mapping):
        raise ValueError(f"{path} must contain a YAML mapping")
    return dict(document)


def _factor_values(config: Mapping[str, Any]) -> dict[str, tuple[str, ...]]:
    factors = config.get("factors")
    if not isinstance(factors, Mapping) or not factors:
        raise ValueError("statement reference has no factors")
    result: dict[str, tuple[str, ...]] = {}
    for factor_name, raw in factors.items():
        if not isinstance(raw, Mapping) or not isinstance(raw.get("values"), list):
            raise ValueError(f"factor {factor_name} has no values")
        values: list[str] = []
        for item in raw["values"]:
            value = item.get("key") if isinstance(item, Mapping) else item
            values.append(str(value).lower() if isinstance(value, bool) else str(value))
        if not values or len(values) != len(set(values)):
            raise ValueError(f"factor {factor_name} values are empty or duplicated")
        result[str(factor_name)] = tuple(values)
    return result


def _audit_matrix(
    report: EditionKnowledgeReport,
    matrix_path: Path,
    reference_path: Path,
    config: Mapping[str, Any],
) -> None:
    try:
        matrix = _load_mapping(matrix_path)
    except (OSError, ValueError, yaml.YAMLError) as exc:
        report.errors.append(str(exc))
        return
    if matrix.get("kind") != "statement_combination_matrix":
        report.errors.append(f"{matrix_path}: invalid matrix kind")
        return
    factors = _factor_values(config)
    contract = matrix.get("factor_contract")
    contract_factors = contract.get("factors") if isinstance(contract, Mapping) else None
    if not isinstance(contract_factors, Mapping) or set(contract_factors) != set(factors):
        report.errors.append(f"{matrix_path}: factor contract does not match statement reference")
        return
    for name, values in factors.items():
        declared = contract_factors[name].get("required_values")
        if declared != list(values):
            report.errors.append(f"{matrix_path}: factor {name} required values are incomplete")

    groups = matrix.get("combination_groups")
    if not isinstance(groups, list) or not groups:
        report.errors.append(f"{matrix_path}: combination_groups must be nonempty")
        return
    assignments = [group.get("factors", {}) for group in groups if isinstance(group, Mapping)]
    policy = config.get("coverage_policy") if isinstance(config.get("coverage_policy"), Mapping) else {}
    main_axes = [str(item) for item in policy.get("main_combination_axes", [])]
    if not main_axes:
        main_axes = list(factors)
    expected_main = set(itertools.product(*(factors[name] for name in main_axes)))
    actual_main = {
        tuple(str(assignment.get(name)) for name in main_axes)
        for assignment in assignments
        if all(name in assignment for name in main_axes)
    }
    missing_main = expected_main - actual_main
    if missing_main:
        report.errors.append(f"{matrix_path}: missing {len(missing_main)} required Cartesian combinations")
    for name, values in factors.items():
        covered = {str(assignment.get(name)) for assignment in assignments if name in assignment}
        missing = set(values) - covered
        if missing:
            report.errors.append(f"{matrix_path}: factor {name} misses values {sorted(missing)}")


def audit_edition_knowledge(edition_root: Path | str) -> EditionKnowledgeReport:
    root = Path(edition_root).resolve()
    report = EditionKnowledgeReport()
    try:
        manifest = _load_mapping(root / "edition.yaml")
    except (OSError, ValueError, yaml.YAMLError) as exc:
        report.errors.append(str(exc))
        return report
    report.edition_id = str(manifest.get("edition_id") or "")
    if manifest.get("review_state") != "complete":
        report.unreviewed_count += 1
        report.errors.append(f"{root / 'edition.yaml'}: review_state must be complete")
    skill = manifest.get("skill")
    if not isinstance(skill, Mapping) or not isinstance(skill.get("root"), str):
        report.errors.append(f"{root / 'edition.yaml'}: skill root is missing")
        return report
    skill_root = (root / skill["root"]).resolve()
    if root not in skill_root.parents or not skill_root.is_dir():
        report.errors.append(f"{root / 'edition.yaml'}: skill root is invalid")
        return report
    support_path = skill_root / "references" / "common" / "statement_support_inventory.yaml"
    if not support_path.is_file():
        report.errors.append(f"missing {support_path.name}: {support_path}")
        return report
    try:
        support = _load_mapping(support_path)
    except (OSError, ValueError, yaml.YAMLError) as exc:
        report.errors.append(str(exc))
        return report
    if (
        support.get("kind") != "mysql_statement_support_inventory"
        or support.get("edition_id") != report.edition_id
        or support.get("target_version") != manifest.get("target_version")
    ):
        report.errors.append(f"{support_path}: edition metadata mismatch")
    rows = support.get("statements")
    if not isinstance(rows, list):
        report.errors.append(f"{support_path}: statements must be a list")
        return report

    seen_keys: set[str] = set()
    expected_ledger_keys: set[tuple[str, str, str]] = set()
    expected_pairs: set[tuple[str, str]] = set()
    for index, row in enumerate(rows):
        if not isinstance(row, Mapping):
            report.errors.append(f"{support_path}: statements[{index}] must be a mapping")
            continue
        key = str(row.get("key") or "")
        if not key or key in seen_keys:
            report.errors.append(f"{support_path}: duplicate or empty statement key {key!r}")
            continue
        seen_keys.add(key)
        if row.get("review_state") != "static_complete":
            report.unreviewed_count += 1
            report.errors.append(f"{support_path}: statement {key} is not static_complete")
        reference_text = str(row.get("reference") or "")
        matrix_text = str(row.get("matrix") or "")
        reference = (skill_root / reference_text).resolve()
        matrix = (skill_root / matrix_text).resolve()
        if skill_root not in reference.parents or not reference.is_file():
            report.errors.append(f"{support_path}: statement {key} reference is invalid")
            continue
        if skill_root not in matrix.parents or not matrix.is_file():
            report.errors.append(f"{support_path}: statement {key} matrix is missing")
            continue
        if not str(row.get("official_source") or "").startswith("https://dev.mysql.com/"):
            report.errors.append(f"{support_path}: statement {key} lacks an official source")
        try:
            config = load_statement_reference(reference)
            statement = config.get("statement")
            if not isinstance(statement, Mapping) or statement.get("key") != key:
                raise ValueError("statement key mismatch")
            values = _factor_values(config)
        except (OSError, ValueError, yaml.YAMLError) as exc:
            report.errors.append(f"{reference}: {exc}")
            continue
        for factor, factor_values in values.items():
            expected_pairs.add((key, factor))
            expected_ledger_keys.update((key, factor, value) for value in factor_values)
        _audit_matrix(report, matrix, reference, config)
        report.matrix_count += 1

    report.statement_count = len(seen_keys)
    actual_references = list((skill_root / "references" / "statements").rglob("*.md"))
    actual_matrices = [
        path
        for path in (skill_root / "references" / "combinations").rglob("*.yaml")
        if "_shared" not in path.parts
    ]
    if len(actual_references) != report.statement_count:
        report.errors.append("support inventory does not cover every statement reference")
    if len(actual_matrices) != report.statement_count:
        report.errors.append("support inventory does not cover every statement matrix")

    factor_audit = support.get("factor_audit")
    if not isinstance(factor_audit, Mapping):
        report.errors.append(f"{support_path}: factor_audit is missing")
        return report
    ledger_path = (skill_root / str(factor_audit.get("path") or "")).resolve()
    try:
        payload = ledger_path.read_bytes()
        if hashlib.sha256(payload).hexdigest() != factor_audit.get("sha256"):
            report.errors.append(f"{ledger_path}: SHA-256 mismatch")
        reader = csv.DictReader(payload.decode("utf-8").splitlines(), delimiter="\t")
        if tuple(reader.fieldnames or ()) != LEDGER_COLUMNS:
            raise ValueError("factor audit header mismatch")
        actual_keys: set[tuple[str, str, str]] = set()
        for row in reader:
            key = (row["statement_key"], row["factor"], row["value"])
            actual_keys.add(key)
            if row["review_status"] != "static_reviewed" or row["catalog_readiness"] != "static_ready":
                report.unreviewed_count += 1
        if actual_keys != expected_ledger_keys:
            report.errors.append(f"{ledger_path}: factor/value rows are not closed")
        report.factor_value_count = len(actual_keys)
        report.factor_pair_count = len({(key, factor) for key, factor, _ in actual_keys})
    except (OSError, UnicodeError, ValueError, KeyError) as exc:
        report.errors.append(f"{ledger_path}: {exc}")
    if report.factor_pair_count != len(expected_pairs):
        report.errors.append("factor audit pair count does not match references")
    return report
