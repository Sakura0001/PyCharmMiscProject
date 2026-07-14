"""Strict, immutable contracts for plan-first multi-agent feature analysis.

These contracts contain planning data only.  They deliberately do not expose a
database endpoint, an executable case, or a scheduler route.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path, PurePosixPath
from typing import Any, Mapping, Optional, Sequence, Type, TypeVar, Union

import yaml

from .contracts import ContractValidationError


_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_STABLE_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")
_SQLSTATE = re.compile(r"^[0-9A-Z]{5}$")
TARGET_EDITIONS = ("mysql_8_0_22", "mysql_8_0_41")
COMBINATION_STRATEGIES = (
    "full_cross",
    "conditional_cross",
    "boundary",
    "negative",
    "representative",
    "pairwise",
    "not_applicable",
    "unresolved",
)


class _UniqueKeyLoader(yaml.SafeLoader):
    def construct_mapping(self, node, deep=False):
        seen = set()
        for key_node, _ in node.value:
            key = self.construct_object(key_node, deep=deep)
            if key in seen:
                raise ContractValidationError(f"duplicate YAML key {key}")
            seen.add(key)
        return super().construct_mapping(node, deep=deep)


def canonical_json_bytes(value: Any) -> bytes:
    try:
        return json.dumps(
            value,
            ensure_ascii=False,
            allow_nan=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise ContractValidationError(f"value is not canonical JSON: {exc}") from exc


def canonical_json_sha256(value: Any) -> str:
    return hashlib.sha256(canonical_json_bytes(value)).hexdigest()


def _mapping(value: Any, location: str) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        raise ContractValidationError(f"{location} must be a mapping")
    document = dict(value)
    if any(not isinstance(key, str) for key in document):
        raise ContractValidationError(f"{location} keys must be strings")
    canonical_json_bytes(document)
    return document


def _closed(
    document: Mapping[str, Any],
    required: set[str],
    optional: set[str],
    location: str,
) -> None:
    missing = sorted(required - set(document))
    unexpected = sorted(set(document) - required - optional)
    if missing or unexpected:
        details = []
        if missing:
            details.append("missing " + ", ".join(missing))
        if unexpected:
            details.append("unexpected " + ", ".join(unexpected))
        raise ContractValidationError(f"{location} has invalid fields: " + "; ".join(details))


def _header(document: Mapping[str, Any], kind: str, location: str) -> None:
    if document.get("schema_version") != 1:
        raise ContractValidationError(f"{location}.schema_version must be 1")
    if document.get("kind") != kind:
        raise ContractValidationError(f"{location}.kind must be {kind}")


def _text(value: Any, location: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ContractValidationError(f"{location} must be a non-empty string")
    return value.strip()


def _identifier(value: Any, location: str) -> str:
    value = _text(value, location)
    if _STABLE_ID.fullmatch(value) is None:
        raise ContractValidationError(f"{location} must be a portable stable identifier")
    return value


def _strings(value: Any, location: str, nonempty: bool = False) -> tuple[str, ...]:
    if isinstance(value, (str, bytes)) or not isinstance(value, Sequence):
        raise ContractValidationError(f"{location} must be a sequence")
    result = tuple(_text(item, f"{location}[{index}]") for index, item in enumerate(value))
    if nonempty and not result:
        raise ContractValidationError(f"{location} must not be empty")
    if len(set(result)) != len(result):
        raise ContractValidationError(f"{location} contains duplicates")
    return result


def _identifiers(value: Any, location: str, nonempty: bool = False) -> tuple[str, ...]:
    result = _strings(value, location, nonempty=nonempty)
    for index, item in enumerate(result):
        _identifier(item, f"{location}[{index}]")
    return result


def _digest(value: Any, location: str) -> str:
    if not isinstance(value, str) or _SHA256.fullmatch(value) is None:
        raise ContractValidationError(f"{location} must be a lowercase 64-character SHA-256")
    return value


def _relative_path(value: Any, location: str) -> str:
    value = _text(value, location)
    if "\\" in value:
        raise ContractValidationError(f"{location} must use portable forward slashes")
    path = PurePosixPath(value)
    if path.is_absolute() or ".." in path.parts:
        raise ContractValidationError(f"{location} must be relative and must not escape its root")
    return value


def _locator(value: Any, location: str) -> str:
    locator = _text(value, location)
    base = locator.split("#", 1)[0]
    _relative_path(base, location)
    return locator


def _timestamp(value: Any, location: str) -> str:
    value = _text(value, location)
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ContractValidationError(f"{location} must be an RFC3339 timestamp") from exc
    if parsed.tzinfo is None:
        raise ContractValidationError(f"{location} must include a timezone")
    return value


def _edition(value: Any, location: str) -> str:
    value = _text(value, location)
    if value not in TARGET_EDITIONS:
        raise ContractValidationError(f"{location} must be one of {', '.join(TARGET_EDITIONS)}")
    return value


T = TypeVar("T")


def load_planning_contract(path: Union[str, Path], contract_type: Type[T]) -> T:
    source = Path(path)
    try:
        raw = yaml.load(source.read_text(encoding="utf-8"), Loader=_UniqueKeyLoader)
    except ContractValidationError:
        raise
    except (OSError, UnicodeError, yaml.YAMLError) as exc:
        raise ContractValidationError(f"cannot load planning contract {source}: {exc}") from exc
    parser = getattr(contract_type, "from_dict", None)
    if parser is None:
        raise TypeError("contract_type must expose from_dict")
    return parser(raw)


@dataclass(frozen=True)
class ArtifactBinding:
    path: str
    sha256: str

    def __post_init__(self) -> None:
        _relative_path(self.path, "artifact_binding.path")
        _digest(self.sha256, "artifact_binding.sha256")

    @classmethod
    def from_dict(cls, raw: Mapping[str, Any], location: str = "artifact_binding") -> "ArtifactBinding":
        document = _mapping(raw, location)
        _closed(document, {"path", "sha256"}, set(), location)
        return cls(
            _relative_path(document.get("path"), f"{location}.path"),
            _digest(document.get("sha256"), f"{location}.sha256"),
        )

    def to_dict(self) -> dict[str, str]:
        return {"path": self.path, "sha256": self.sha256}


@dataclass(frozen=True)
class AtomicRequirement:
    requirement_id: str
    description: str
    source_locator: str

    @classmethod
    def from_dict(cls, raw: Mapping[str, Any], location: str) -> "AtomicRequirement":
        document = _mapping(raw, location)
        _closed(document, {"id", "description", "source_locator"}, set(), location)
        return cls(
            _identifier(document.get("id"), f"{location}.id"),
            _text(document.get("description"), f"{location}.description"),
            _locator(document.get("source_locator"), f"{location}.source_locator"),
        )

    def to_dict(self) -> dict[str, str]:
        return {
            "id": self.requirement_id,
            "description": self.description,
            "source_locator": self.source_locator,
        }


@dataclass(frozen=True)
class UnresolvedQuestion:
    question_id: str
    question: str
    coverage_impact: str
    source_locator: str

    @classmethod
    def from_dict(cls, raw: Mapping[str, Any], location: str) -> "UnresolvedQuestion":
        document = _mapping(raw, location)
        _closed(document, {"id", "question", "coverage_impact", "source_locator"}, set(), location)
        return cls(
            _identifier(document.get("id"), f"{location}.id"),
            _text(document.get("question"), f"{location}.question"),
            _text(document.get("coverage_impact"), f"{location}.coverage_impact"),
            _locator(document.get("source_locator"), f"{location}.source_locator"),
        )

    def to_dict(self) -> dict[str, str]:
        return {
            "id": self.question_id,
            "question": self.question,
            "coverage_impact": self.coverage_impact,
            "source_locator": self.source_locator,
        }


@dataclass(frozen=True)
class FeatureSpec:
    feature_id: str
    operation: str
    target_objects: tuple[str, ...]
    behavior_change: str
    affected_phases: tuple[str, ...]
    target_editions: tuple[str, ...]
    constraints: tuple[str, ...]
    requirements: tuple[AtomicRequirement, ...]
    source_locators: tuple[str, ...]
    unresolved_questions: tuple[UnresolvedQuestion, ...]
    status: str
    schema_version: int = 1

    @classmethod
    def from_dict(cls, raw: Mapping[str, Any]) -> "FeatureSpec":
        location = "feature_spec"
        document = _mapping(raw, location)
        required = {
            "schema_version", "kind", "feature_id", "operation", "target_objects",
            "behavior_change", "affected_phases", "target_editions", "constraints",
            "requirements", "source_locators", "unresolved_questions", "status",
        }
        _closed(document, required, set(), location)
        _header(document, "feature_spec", location)
        target_editions = _strings(document.get("target_editions"), f"{location}.target_editions", True)
        for index, edition in enumerate(target_editions):
            _edition(edition, f"{location}.target_editions[{index}]")
        requirements_raw = document.get("requirements")
        if isinstance(requirements_raw, (str, bytes)) or not isinstance(requirements_raw, Sequence):
            raise ContractValidationError(f"{location}.requirements must be a sequence")
        requirements = tuple(
            AtomicRequirement.from_dict(item, f"{location}.requirements[{index}]")
            for index, item in enumerate(requirements_raw)
        )
        if not requirements:
            raise ContractValidationError(f"{location}.requirements must not be empty")
        if len({item.requirement_id for item in requirements}) != len(requirements):
            raise ContractValidationError("duplicate requirement id")
        questions_raw = document.get("unresolved_questions")
        if isinstance(questions_raw, (str, bytes)) or not isinstance(questions_raw, Sequence):
            raise ContractValidationError(f"{location}.unresolved_questions must be a sequence")
        questions = tuple(
            UnresolvedQuestion.from_dict(item, f"{location}.unresolved_questions[{index}]")
            for index, item in enumerate(questions_raw)
        )
        if len({item.question_id for item in questions}) != len(questions):
            raise ContractValidationError("duplicate unresolved question id")
        status = _text(document.get("status"), f"{location}.status")
        if status not in ("complete", "blocked"):
            raise ContractValidationError(f"{location}.status must be complete or blocked")
        if status == "complete" and questions:
            raise ContractValidationError("feature_spec cannot mark unresolved questions complete")
        if status == "blocked" and not questions:
            raise ContractValidationError("feature_spec blocked status requires unresolved questions")
        source_locators = _strings(document.get("source_locators"), f"{location}.source_locators", True)
        for index, locator in enumerate(source_locators):
            _locator(locator, f"{location}.source_locators[{index}]")
        return cls(
            feature_id=_identifier(document.get("feature_id"), f"{location}.feature_id"),
            operation=_identifier(document.get("operation"), f"{location}.operation"),
            target_objects=_identifiers(document.get("target_objects"), f"{location}.target_objects", True),
            behavior_change=_text(document.get("behavior_change"), f"{location}.behavior_change"),
            affected_phases=_identifiers(document.get("affected_phases"), f"{location}.affected_phases", True),
            target_editions=target_editions,
            constraints=_strings(document.get("constraints"), f"{location}.constraints"),
            requirements=requirements,
            source_locators=source_locators,
            unresolved_questions=questions,
            status=status,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "kind": "feature_spec",
            "feature_id": self.feature_id,
            "operation": self.operation,
            "target_objects": list(self.target_objects),
            "behavior_change": self.behavior_change,
            "affected_phases": list(self.affected_phases),
            "target_editions": list(self.target_editions),
            "constraints": list(self.constraints),
            "requirements": [item.to_dict() for item in self.requirements],
            "source_locators": list(self.source_locators),
            "unresolved_questions": [item.to_dict() for item in self.unresolved_questions],
            "status": self.status,
        }


@dataclass(frozen=True)
class ImpactNode:
    node_id: str
    node_type: str
    label: str
    sources: tuple[str, ...]

    @classmethod
    def from_dict(cls, raw: Mapping[str, Any], location: str) -> "ImpactNode":
        document = _mapping(raw, location)
        _closed(document, {"id", "type", "label", "sources"}, set(), location)
        node_type = _text(document.get("type"), f"{location}.type")
        allowed = {
            "requirement", "object", "operation", "factor_domain", "inventory_selector",
            "constraint", "risk", "observable", "version_claim",
        }
        if node_type not in allowed:
            raise ContractValidationError(f"{location}.type is not a supported impact node type")
        sources = _strings(document.get("sources"), f"{location}.sources", True)
        return cls(
            _identifier(document.get("id"), f"{location}.id"), node_type,
            _text(document.get("label"), f"{location}.label"), sources,
        )

    def to_dict(self) -> dict[str, Any]:
        return {"id": self.node_id, "type": self.node_type, "label": self.label, "sources": list(self.sources)}


@dataclass(frozen=True)
class ImpactEdge:
    edge_id: str
    from_node: str
    to_node: str
    rule_id: str
    evidence: tuple[str, ...]

    @classmethod
    def from_dict(cls, raw: Mapping[str, Any], location: str) -> "ImpactEdge":
        document = _mapping(raw, location)
        _closed(document, {"id", "from", "to", "rule_id", "evidence"}, set(), location)
        return cls(
            _identifier(document.get("id"), f"{location}.id"),
            _identifier(document.get("from"), f"{location}.from"),
            _identifier(document.get("to"), f"{location}.to"),
            _identifier(document.get("rule_id"), f"{location}.rule_id"),
            _strings(document.get("evidence"), f"{location}.evidence", True),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.edge_id, "from": self.from_node, "to": self.to_node,
            "rule_id": self.rule_id, "evidence": list(self.evidence),
        }


@dataclass(frozen=True)
class FeatureImpactGraph:
    feature_id: str
    nodes: tuple[ImpactNode, ...]
    edges: tuple[ImpactEdge, ...]
    schema_version: int = 1

    @classmethod
    def from_dict(cls, raw: Mapping[str, Any]) -> "FeatureImpactGraph":
        location = "feature_impact_graph"
        document = _mapping(raw, location)
        _closed(document, {"schema_version", "kind", "feature_id", "nodes", "edges"}, set(), location)
        _header(document, "feature_impact_graph", location)
        nodes_raw = document.get("nodes")
        edges_raw = document.get("edges")
        if not isinstance(nodes_raw, Sequence) or isinstance(nodes_raw, (str, bytes)) or not nodes_raw:
            raise ContractValidationError(f"{location}.nodes must be a non-empty sequence")
        if not isinstance(edges_raw, Sequence) or isinstance(edges_raw, (str, bytes)):
            raise ContractValidationError(f"{location}.edges must be a sequence")
        nodes = tuple(ImpactNode.from_dict(item, f"{location}.nodes[{index}]") for index, item in enumerate(nodes_raw))
        edges = tuple(ImpactEdge.from_dict(item, f"{location}.edges[{index}]") for index, item in enumerate(edges_raw))
        node_ids = [item.node_id for item in nodes]
        edge_ids = [item.edge_id for item in edges]
        if len(set(node_ids)) != len(node_ids):
            raise ContractValidationError("duplicate impact node id")
        if len(set(edge_ids)) != len(edge_ids):
            raise ContractValidationError("duplicate impact edge id")
        known = set(node_ids)
        for edge in edges:
            if edge.from_node not in known or edge.to_node not in known:
                raise ContractValidationError(f"impact edge {edge.edge_id} references an unknown node")
        return cls(_identifier(document.get("feature_id"), f"{location}.feature_id"), nodes, edges)

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version, "kind": "feature_impact_graph",
            "feature_id": self.feature_id,
            "nodes": [item.to_dict() for item in self.nodes],
            "edges": [item.to_dict() for item in self.edges],
        }


@dataclass(frozen=True)
class FactorDecision:
    factor_id: str
    domain: str
    status: str
    trigger_path: tuple[str, ...]
    edition_applicability: Mapping[str, str]
    combination_strategy: str
    dependencies: tuple[str, ...]
    exclusions: tuple[str, ...]
    review_state: str
    inventory_source: Optional[str] = None
    inventory_sha256: Optional[str] = None
    owning_suite_id: Optional[str] = None
    reason: Optional[str] = None
    sources: tuple[str, ...] = ()
    schema_version: int = 1

    @classmethod
    def from_dict(cls, raw: Mapping[str, Any]) -> "FactorDecision":
        location = "factor_decision"
        document = _mapping(raw, location)
        required = {
            "schema_version", "kind", "factor_id", "domain", "status", "trigger_path",
            "edition_applicability", "combination_strategy", "dependencies", "exclusions", "review_state",
        }
        optional = {"inventory_source", "inventory_sha256", "owning_suite_id", "reason", "sources"}
        _closed(document, required, optional, location)
        _header(document, "factor_decision", location)
        status = _text(document.get("status"), f"{location}.status")
        if status not in ("covered", "justified_na", "unknown"):
            raise ContractValidationError(f"{location}.status must be covered, justified_na, or unknown")
        strategy = _text(document.get("combination_strategy"), f"{location}.combination_strategy")
        if strategy not in COMBINATION_STRATEGIES:
            raise ContractValidationError(f"{location}.combination_strategy is unsupported")
        applicability = _mapping(document.get("edition_applicability"), f"{location}.edition_applicability")
        if set(applicability) != set(TARGET_EDITIONS):
            raise ContractValidationError(f"{location}.edition_applicability must contain both target editions")
        for edition, value in applicability.items():
            if value not in ("applicable", "not_applicable", "unknown"):
                raise ContractValidationError(f"{location}.edition_applicability.{edition} is invalid")
        inventory_source = document.get("inventory_source")
        inventory_sha256 = document.get("inventory_sha256")
        owning_suite_id = document.get("owning_suite_id")
        reason = document.get("reason")
        sources = _strings(document.get("sources", []), f"{location}.sources")
        if status == "covered":
            inventory_source = _locator(inventory_source, f"{location}.inventory_source")
            inventory_sha256 = _digest(inventory_sha256, f"{location}.inventory_sha256")
            owning_suite_id = _identifier(owning_suite_id, f"{location}.owning_suite_id")
            if strategy in ("not_applicable", "unresolved"):
                raise ContractValidationError(f"{location} covered factor requires an executable strategy")
            if reason is not None or sources:
                raise ContractValidationError(f"{location} covered factor must not declare reason or sources")
        else:
            reason = _text(reason, f"{location}.reason")
            if not sources:
                raise ContractValidationError(f"{location}.sources must not be empty for {status}")
            if any(value is not None for value in (inventory_source, inventory_sha256, owning_suite_id)):
                raise ContractValidationError(f"{location} {status} factor must not own an inventory or suite")
            expected_strategy = "not_applicable" if status == "justified_na" else "unresolved"
            if strategy != expected_strategy:
                raise ContractValidationError(f"{location} {status} factor requires {expected_strategy} strategy")
        review_state = _text(document.get("review_state"), f"{location}.review_state")
        if review_state not in ("proposed", "reviewed", "blocked"):
            raise ContractValidationError(f"{location}.review_state is invalid")
        return cls(
            factor_id=_identifier(document.get("factor_id"), f"{location}.factor_id"),
            domain=_identifier(document.get("domain"), f"{location}.domain"),
            status=status,
            trigger_path=_identifiers(document.get("trigger_path"), f"{location}.trigger_path", True),
            edition_applicability=applicability,
            combination_strategy=strategy,
            dependencies=_identifiers(document.get("dependencies"), f"{location}.dependencies"),
            exclusions=_strings(document.get("exclusions"), f"{location}.exclusions"),
            review_state=review_state,
            inventory_source=inventory_source,
            inventory_sha256=inventory_sha256,
            owning_suite_id=owning_suite_id,
            reason=reason,
            sources=sources,
        )

    def to_dict(self) -> dict[str, Any]:
        document: dict[str, Any] = {
            "schema_version": self.schema_version, "kind": "factor_decision",
            "factor_id": self.factor_id, "domain": self.domain, "status": self.status,
            "trigger_path": list(self.trigger_path),
            "edition_applicability": dict(self.edition_applicability),
            "combination_strategy": self.combination_strategy,
            "dependencies": list(self.dependencies), "exclusions": list(self.exclusions),
            "owning_suite_id": self.owning_suite_id,
            "review_state": self.review_state,
            "inventory_source": self.inventory_source, "inventory_sha256": self.inventory_sha256,
        }
        if self.status != "covered":
            document.pop("owning_suite_id")
            document.pop("inventory_source")
            document.pop("inventory_sha256")
            document["reason"] = self.reason
            document["sources"] = list(self.sources)
        return document


def _nonempty_json_mapping(value: Any, location: str) -> dict[str, Any]:
    document = _mapping(value, location)
    if not document:
        raise ContractValidationError(f"{location} must not be empty")
    return document


@dataclass(frozen=True)
class PlanCaseBlueprint:
    blueprint_id: str
    plan_id: str
    edition: str
    obligation_id: str
    assignments: Mapping[str, Any]
    setup_recipe: Mapping[str, Any]
    target_statement: Mapping[str, Any]
    verification_oracle: Mapping[str, Any]
    cleanup_procedure: Mapping[str, Any]
    expected_outcome: str
    execution_profile: str
    diagnostic_contract: Optional[Mapping[str, Any]] = None
    execution_harness: Optional[str] = None
    schema_version: int = 1

    @classmethod
    def from_dict(cls, raw: Mapping[str, Any]) -> "PlanCaseBlueprint":
        location = "plan_case_blueprint"
        document = _mapping(raw, location)
        required = {
            "schema_version", "kind", "blueprint_id", "plan_id", "edition", "obligation_id",
            "assignments", "setup_recipe", "target_statement", "verification_oracle",
            "cleanup_procedure", "expected_outcome", "execution_profile",
        }
        _closed(document, required, {"diagnostic_contract", "execution_harness"}, location)
        _header(document, "plan_case_blueprint", location)
        outcome = _text(document.get("expected_outcome"), f"{location}.expected_outcome")
        if outcome not in ("success", "expected_failure"):
            raise ContractValidationError(f"{location}.expected_outcome must be success or expected_failure")
        diagnostic = document.get("diagnostic_contract")
        if outcome == "expected_failure":
            diagnostic = _mapping(diagnostic, f"{location}.diagnostic_contract")
            _closed(
                diagnostic,
                {"error_code", "sqlstate", "terminal_error_count", "message_pattern"},
                set(), f"{location}.diagnostic_contract",
            )
            code = diagnostic.get("error_code")
            if (type(code) is not int or code < 1) and (not isinstance(code, str) or not code.strip()):
                raise ContractValidationError(f"{location}.diagnostic_contract.error_code is invalid")
            if not isinstance(diagnostic.get("sqlstate"), str) or _SQLSTATE.fullmatch(diagnostic["sqlstate"]) is None:
                raise ContractValidationError(f"{location}.diagnostic_contract.sqlstate must be five uppercase characters")
            if type(diagnostic.get("terminal_error_count")) is not int or diagnostic["terminal_error_count"] < 1:
                raise ContractValidationError(f"{location}.diagnostic_contract.terminal_error_count must be positive")
            _text(diagnostic.get("message_pattern"), f"{location}.diagnostic_contract.message_pattern")
        elif diagnostic is not None:
            raise ContractValidationError(f"{location}.diagnostic_contract is forbidden for success")
        profile = _text(document.get("execution_profile"), f"{location}.execution_profile")
        if profile not in ("basic_mysql", "external_isolated"):
            raise ContractValidationError(f"{location}.execution_profile is invalid")
        harness = document.get("execution_harness")
        if profile == "external_isolated":
            harness = _identifier(harness, f"{location}.execution_harness")
        elif harness is not None:
            raise ContractValidationError(f"{location}.execution_harness is forbidden for basic_mysql")
        return cls(
            blueprint_id=_identifier(document.get("blueprint_id"), f"{location}.blueprint_id"),
            plan_id=_identifier(document.get("plan_id"), f"{location}.plan_id"),
            edition=_edition(document.get("edition"), f"{location}.edition"),
            obligation_id=_identifier(document.get("obligation_id"), f"{location}.obligation_id"),
            assignments=_nonempty_json_mapping(document.get("assignments"), f"{location}.assignments"),
            setup_recipe=_nonempty_json_mapping(document.get("setup_recipe"), f"{location}.setup_recipe"),
            target_statement=_nonempty_json_mapping(document.get("target_statement"), f"{location}.target_statement"),
            verification_oracle=_nonempty_json_mapping(document.get("verification_oracle"), f"{location}.verification_oracle"),
            cleanup_procedure=_nonempty_json_mapping(document.get("cleanup_procedure"), f"{location}.cleanup_procedure"),
            expected_outcome=outcome, execution_profile=profile,
            diagnostic_contract=diagnostic, execution_harness=harness,
        )

    def to_dict(self) -> dict[str, Any]:
        document: dict[str, Any] = {
            "schema_version": self.schema_version, "kind": "plan_case_blueprint",
            "blueprint_id": self.blueprint_id, "plan_id": self.plan_id, "edition": self.edition,
            "obligation_id": self.obligation_id, "assignments": dict(self.assignments),
            "setup_recipe": dict(self.setup_recipe), "target_statement": dict(self.target_statement),
            "verification_oracle": dict(self.verification_oracle),
            "cleanup_procedure": dict(self.cleanup_procedure),
            "expected_outcome": self.expected_outcome, "execution_profile": self.execution_profile,
        }
        if self.diagnostic_contract is not None:
            document["diagnostic_contract"] = dict(self.diagnostic_contract)
        if self.execution_harness is not None:
            document["execution_harness"] = self.execution_harness
        return document


@dataclass(frozen=True)
class DryRenderArtifact:
    dry_render_id: str
    blueprint_id: str
    edition: str
    blueprint_sha256: str
    canonical_sql_ast: Mapping[str, Any]
    canonical_ast_sha256: str
    normalized_identifiers: Mapping[str, Any]
    preview_text: str
    runnable: bool = False
    schema_version: int = 1

    @classmethod
    def from_dict(cls, raw: Mapping[str, Any]) -> "DryRenderArtifact":
        location = "dry_render_artifact"
        document = _mapping(raw, location)
        required = {
            "schema_version", "kind", "dry_render_id", "blueprint_id", "edition",
            "blueprint_sha256", "canonical_sql_ast", "canonical_ast_sha256",
            "normalized_identifiers", "preview_text", "runnable",
        }
        _closed(document, required, set(), location)
        _header(document, "dry_render_artifact", location)
        if document.get("runnable") is not False:
            raise ContractValidationError(f"{location}.runnable must be false")
        ast = _nonempty_json_mapping(document.get("canonical_sql_ast"), f"{location}.canonical_sql_ast")
        ast_digest = _digest(document.get("canonical_ast_sha256"), f"{location}.canonical_ast_sha256")
        if ast_digest != canonical_json_sha256(ast):
            raise ContractValidationError(f"{location}.canonical_ast_sha256 does not match canonical_sql_ast")
        return cls(
            _identifier(document.get("dry_render_id"), f"{location}.dry_render_id"),
            _identifier(document.get("blueprint_id"), f"{location}.blueprint_id"),
            _edition(document.get("edition"), f"{location}.edition"),
            _digest(document.get("blueprint_sha256"), f"{location}.blueprint_sha256"),
            ast, ast_digest,
            _nonempty_json_mapping(document.get("normalized_identifiers"), f"{location}.normalized_identifiers"),
            _text(document.get("preview_text"), f"{location}.preview_text"), False,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version, "kind": "dry_render_artifact",
            "dry_render_id": self.dry_render_id, "blueprint_id": self.blueprint_id,
            "edition": self.edition, "blueprint_sha256": self.blueprint_sha256,
            "canonical_sql_ast": dict(self.canonical_sql_ast),
            "canonical_ast_sha256": self.canonical_ast_sha256,
            "normalized_identifiers": dict(self.normalized_identifiers),
            "preview_text": self.preview_text, "runnable": False,
        }


@dataclass(frozen=True)
class AuditFinding:
    finding_id: str
    status: str
    severity: str
    description: str
    sources: tuple[str, ...]
    closure_evidence: tuple[ArtifactBinding, ...] = ()

    @classmethod
    def from_dict(cls, raw: Mapping[str, Any], location: str) -> "AuditFinding":
        document = _mapping(raw, location)
        _closed(document, {"id", "status", "severity", "description", "sources"}, {"closure_evidence"}, location)
        status = _text(document.get("status"), f"{location}.status")
        if status not in ("open", "closed"):
            raise ContractValidationError(f"{location}.status must be open or closed")
        severity = _text(document.get("severity"), f"{location}.severity")
        if severity not in ("low", "medium", "high", "critical"):
            raise ContractValidationError(f"{location}.severity is invalid")
        evidence_raw = document.get("closure_evidence", [])
        if not isinstance(evidence_raw, Sequence) or isinstance(evidence_raw, (str, bytes)):
            raise ContractValidationError(f"{location}.closure_evidence must be a sequence")
        evidence = tuple(ArtifactBinding.from_dict(item, f"{location}.closure_evidence[{index}]") for index, item in enumerate(evidence_raw))
        if status == "closed" and not evidence:
            raise ContractValidationError(f"{location}.closure_evidence is required when closed")
        if status == "open" and evidence:
            raise ContractValidationError(f"{location}.closure_evidence is forbidden when open")
        return cls(
            _identifier(document.get("id"), f"{location}.id"), status, severity,
            _text(document.get("description"), f"{location}.description"),
            _strings(document.get("sources"), f"{location}.sources", True), evidence,
        )

    def to_dict(self) -> dict[str, Any]:
        result: dict[str, Any] = {
            "id": self.finding_id, "status": self.status, "severity": self.severity,
            "description": self.description, "sources": list(self.sources),
        }
        if self.closure_evidence:
            result["closure_evidence"] = [item.to_dict() for item in self.closure_evidence]
        return result


@dataclass(frozen=True)
class AuditAttestation:
    attestation_id: str
    auditor_role: str
    permitted_inputs: tuple[ArtifactBinding, ...]
    candidate_plan_sha256: str
    reconstructed_factor_ids: tuple[str, ...]
    missing_factor_ids: tuple[str, ...]
    excess_factor_ids: tuple[str, ...]
    findings: tuple[AuditFinding, ...]
    final_decision: str
    schema_version: int = 1

    @classmethod
    def from_dict(cls, raw: Mapping[str, Any]) -> "AuditAttestation":
        location = "audit_attestation"
        document = _mapping(raw, location)
        required = {
            "schema_version", "kind", "attestation_id", "auditor_role", "permitted_inputs",
            "candidate_plan_sha256", "reconstructed_factor_ids", "missing_factor_ids",
            "excess_factor_ids", "findings", "final_decision",
        }
        _closed(document, required, set(), location)
        _header(document, "audit_attestation", location)
        inputs_raw = document.get("permitted_inputs")
        findings_raw = document.get("findings")
        if not isinstance(inputs_raw, Sequence) or isinstance(inputs_raw, (str, bytes)) or not inputs_raw:
            raise ContractValidationError(f"{location}.permitted_inputs must be a non-empty sequence")
        if not isinstance(findings_raw, Sequence) or isinstance(findings_raw, (str, bytes)):
            raise ContractValidationError(f"{location}.findings must be a sequence")
        inputs = tuple(ArtifactBinding.from_dict(item, f"{location}.permitted_inputs[{index}]") for index, item in enumerate(inputs_raw))
        if len({item.path for item in inputs}) != len(inputs):
            raise ContractValidationError("duplicate permitted input path")
        findings = tuple(AuditFinding.from_dict(item, f"{location}.findings[{index}]") for index, item in enumerate(findings_raw))
        if len({item.finding_id for item in findings}) != len(findings):
            raise ContractValidationError("duplicate audit finding id")
        missing = _identifiers(document.get("missing_factor_ids"), f"{location}.missing_factor_ids")
        excess = _identifiers(document.get("excess_factor_ids"), f"{location}.excess_factor_ids")
        decision = _text(document.get("final_decision"), f"{location}.final_decision")
        if decision not in ("pass", "rework", "blocked"):
            raise ContractValidationError(f"{location}.final_decision is invalid")
        if decision == "pass" and (missing or excess or any(item.status == "open" for item in findings)):
            raise ContractValidationError("audit pass cannot contain missing/excess factors or an open finding")
        return cls(
            _identifier(document.get("attestation_id"), f"{location}.attestation_id"),
            _identifier(document.get("auditor_role"), f"{location}.auditor_role"), inputs,
            _digest(document.get("candidate_plan_sha256"), f"{location}.candidate_plan_sha256"),
            _identifiers(document.get("reconstructed_factor_ids"), f"{location}.reconstructed_factor_ids"),
            missing, excess, findings, decision,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version, "kind": "audit_attestation",
            "attestation_id": self.attestation_id, "auditor_role": self.auditor_role,
            "permitted_inputs": [item.to_dict() for item in self.permitted_inputs],
            "candidate_plan_sha256": self.candidate_plan_sha256,
            "reconstructed_factor_ids": list(self.reconstructed_factor_ids),
            "missing_factor_ids": list(self.missing_factor_ids),
            "excess_factor_ids": list(self.excess_factor_ids),
            "findings": [item.to_dict() for item in self.findings],
            "final_decision": self.final_decision,
        }


@dataclass(frozen=True)
class ExecutionCount:
    edition: str
    suite_id: str
    total: int
    success: int
    expected_failure: int
    justified_na: int

    @classmethod
    def from_dict(cls, raw: Mapping[str, Any], location: str) -> "ExecutionCount":
        document = _mapping(raw, location)
        _closed(document, {"edition", "suite_id", "total", "success", "expected_failure", "justified_na"}, set(), location)
        counts = []
        for key in ("total", "success", "expected_failure", "justified_na"):
            value = document.get(key)
            if type(value) is not int or value < 0:
                raise ContractValidationError(f"{location}.{key} must be a non-negative integer")
            counts.append(value)
        if counts[0] < 1 or counts[0] != sum(counts[1:]):
            raise ContractValidationError(f"{location}.total must equal success + expected_failure + justified_na and be positive")
        return cls(
            _edition(document.get("edition"), f"{location}.edition"),
            _identifier(document.get("suite_id"), f"{location}.suite_id"), *counts,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "edition": self.edition, "suite_id": self.suite_id, "total": self.total,
            "success": self.success, "expected_failure": self.expected_failure,
            "justified_na": self.justified_na,
        }


@dataclass(frozen=True)
class ExecutionCost:
    estimated_seconds: int
    disk_bytes: int
    max_concurrency: int

    @classmethod
    def from_dict(cls, raw: Mapping[str, Any], location: str) -> "ExecutionCost":
        document = _mapping(raw, location)
        _closed(document, {"estimated_seconds", "disk_bytes", "max_concurrency"}, set(), location)
        values = []
        for key in ("estimated_seconds", "disk_bytes", "max_concurrency"):
            value = document.get(key)
            minimum = 0 if key == "disk_bytes" else 1
            if type(value) is not int or value < minimum:
                raise ContractValidationError(f"{location}.{key} must be an integer >= {minimum}")
            values.append(value)
        return cls(*values)

    def to_dict(self) -> dict[str, int]:
        return {
            "estimated_seconds": self.estimated_seconds,
            "disk_bytes": self.disk_bytes,
            "max_concurrency": self.max_concurrency,
        }


@dataclass(frozen=True)
class PartialExecutionProposal:
    proposal_id: str
    selected_suite_ids: tuple[str, ...]
    cost: ExecutionCost
    confidence_lost: tuple[str, ...]

    @classmethod
    def from_dict(cls, raw: Mapping[str, Any], location: str) -> "PartialExecutionProposal":
        document = _mapping(raw, location)
        _closed(document, {"proposal_id", "selected_suite_ids", "cost", "confidence_lost"}, set(), location)
        return cls(
            _identifier(document.get("proposal_id"), f"{location}.proposal_id"),
            _identifiers(document.get("selected_suite_ids"), f"{location}.selected_suite_ids", True),
            ExecutionCost.from_dict(document.get("cost"), f"{location}.cost"),
            _strings(document.get("confidence_lost"), f"{location}.confidence_lost", True),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "proposal_id": self.proposal_id,
            "selected_suite_ids": list(self.selected_suite_ids),
            "cost": self.cost.to_dict(),
            "confidence_lost": list(self.confidence_lost),
        }


@dataclass(frozen=True)
class ExecutionRequirements:
    endpoints: tuple[str, ...]
    topology: tuple[str, ...]
    privileges: tuple[str, ...]
    disk_bytes: int
    time_seconds: int
    max_concurrency: int
    harnesses: tuple[str, ...]

    @classmethod
    def from_dict(cls, raw: Mapping[str, Any], location: str) -> "ExecutionRequirements":
        document = _mapping(raw, location)
        _closed(document, {"endpoints", "topology", "privileges", "disk_bytes", "time_seconds", "max_concurrency", "harnesses"}, set(), location)
        for key in ("disk_bytes", "time_seconds", "max_concurrency"):
            value = document.get(key)
            if type(value) is not int or value < 1:
                raise ContractValidationError(f"{location}.{key} must be a positive integer")
        return cls(
            _strings(document.get("endpoints"), f"{location}.endpoints", True),
            _strings(document.get("topology"), f"{location}.topology", True),
            _strings(document.get("privileges"), f"{location}.privileges", True),
            document["disk_bytes"], document["time_seconds"], document["max_concurrency"],
            _identifiers(document.get("harnesses"), f"{location}.harnesses", True),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "endpoints": list(self.endpoints), "topology": list(self.topology),
            "privileges": list(self.privileges), "disk_bytes": self.disk_bytes,
            "time_seconds": self.time_seconds, "max_concurrency": self.max_concurrency,
            "harnesses": list(self.harnesses),
        }


@dataclass(frozen=True)
class ExecutionBrief:
    brief_id: str
    planning_bundle_sha256: str
    counts: tuple[ExecutionCount, ...]
    full_cost: ExecutionCost
    partial_proposals: tuple[PartialExecutionProposal, ...]
    requirements: ExecutionRequirements
    safety_blockers: tuple[str, ...]
    known_risks: tuple[str, ...]
    schema_version: int = 1

    @classmethod
    def from_dict(cls, raw: Mapping[str, Any]) -> "ExecutionBrief":
        location = "execution_brief"
        document = _mapping(raw, location)
        required = {
            "schema_version", "kind", "brief_id", "planning_bundle_sha256", "counts",
            "full_cost", "partial_proposals", "requirements", "safety_blockers", "known_risks",
        }
        _closed(document, required, set(), location)
        _header(document, "execution_brief", location)
        counts_raw = document.get("counts")
        proposals_raw = document.get("partial_proposals")
        if not isinstance(counts_raw, Sequence) or isinstance(counts_raw, (str, bytes)) or not counts_raw:
            raise ContractValidationError(f"{location}.counts must be a non-empty sequence")
        if not isinstance(proposals_raw, Sequence) or isinstance(proposals_raw, (str, bytes)):
            raise ContractValidationError(f"{location}.partial_proposals must be a sequence")
        counts = tuple(ExecutionCount.from_dict(item, f"{location}.counts[{index}]") for index, item in enumerate(counts_raw))
        keys = [(item.edition, item.suite_id) for item in counts]
        if len(set(keys)) != len(keys):
            raise ContractValidationError("duplicate execution count edition/suite")
        if {item.edition for item in counts} != set(TARGET_EDITIONS):
            raise ContractValidationError("execution_brief.counts must cover both target editions")
        proposals = tuple(PartialExecutionProposal.from_dict(item, f"{location}.partial_proposals[{index}]") for index, item in enumerate(proposals_raw))
        if len({item.proposal_id for item in proposals}) != len(proposals):
            raise ContractValidationError("duplicate partial proposal id")
        return cls(
            _identifier(document.get("brief_id"), f"{location}.brief_id"),
            _digest(document.get("planning_bundle_sha256"), f"{location}.planning_bundle_sha256"),
            counts, ExecutionCost.from_dict(document.get("full_cost"), f"{location}.full_cost"),
            proposals, ExecutionRequirements.from_dict(document.get("requirements"), f"{location}.requirements"),
            _strings(document.get("safety_blockers"), f"{location}.safety_blockers"),
            _strings(document.get("known_risks"), f"{location}.known_risks"),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version, "kind": "execution_brief",
            "brief_id": self.brief_id, "planning_bundle_sha256": self.planning_bundle_sha256,
            "counts": [item.to_dict() for item in self.counts], "full_cost": self.full_cost.to_dict(),
            "partial_proposals": [item.to_dict() for item in self.partial_proposals],
            "requirements": self.requirements.to_dict(),
            "safety_blockers": list(self.safety_blockers), "known_risks": list(self.known_risks),
        }


@dataclass(frozen=True)
class PlanningBundleManifest:
    request_id: str
    request_revision: int
    entries: tuple[ArtifactBinding, ...]
    policy_sha256: str
    created_at: str
    bundle_sha256: str
    schema_version: int = 1

    @staticmethod
    def _payload(
        request_id: str,
        request_revision: int,
        entries: Sequence[ArtifactBinding],
        policy_sha256: str,
        created_at: str,
    ) -> dict[str, Any]:
        return {
            "schema_version": 1, "kind": "planning_bundle_manifest",
            "request_id": request_id, "request_revision": request_revision,
            "entries": [item.to_dict() for item in entries],
            "policy_sha256": policy_sha256, "created_at": created_at,
        }

    @classmethod
    def create(
        cls,
        request_id: str,
        request_revision: int,
        entries: Sequence[ArtifactBinding],
        policy_sha256: str,
        created_at: str,
    ) -> "PlanningBundleManifest":
        request_id = _identifier(request_id, "planning_bundle_manifest.request_id")
        if type(request_revision) is not int or request_revision < 1:
            raise ContractValidationError("planning_bundle_manifest.request_revision must be positive")
        entries = tuple(entries)
        cls._validate_entries(entries)
        policy_sha256 = _digest(policy_sha256, "planning_bundle_manifest.policy_sha256")
        created_at = _timestamp(created_at, "planning_bundle_manifest.created_at")
        digest = canonical_json_sha256(cls._payload(request_id, request_revision, entries, policy_sha256, created_at))
        return cls(request_id, request_revision, entries, policy_sha256, created_at, digest)

    @staticmethod
    def _validate_entries(entries: Sequence[ArtifactBinding]) -> None:
        if not entries:
            raise ContractValidationError("planning_bundle_manifest.entries must not be empty")
        paths = [item.path for item in entries]
        if len(set(paths)) != len(paths):
            raise ContractValidationError("duplicate planning bundle entry path")
        for path in paths:
            if path in ("planning_bundle_manifest.json", "planning_run.json"):
                raise ContractValidationError(f"planning bundle must not include {path}")
            if PurePosixPath(path).parts and PurePosixPath(path).parts[0] == "decision":
                raise ContractValidationError("planning bundle must not include decision paths")

    @classmethod
    def from_dict(cls, raw: Mapping[str, Any]) -> "PlanningBundleManifest":
        location = "planning_bundle_manifest"
        document = _mapping(raw, location)
        required = {"schema_version", "kind", "request_id", "request_revision", "entries", "policy_sha256", "created_at", "bundle_sha256"}
        _closed(document, required, set(), location)
        _header(document, "planning_bundle_manifest", location)
        revision = document.get("request_revision")
        if type(revision) is not int or revision < 1:
            raise ContractValidationError(f"{location}.request_revision must be positive")
        entries_raw = document.get("entries")
        if not isinstance(entries_raw, Sequence) or isinstance(entries_raw, (str, bytes)):
            raise ContractValidationError(f"{location}.entries must be a sequence")
        entries = tuple(ArtifactBinding.from_dict(item, f"{location}.entries[{index}]") for index, item in enumerate(entries_raw))
        result = cls.create(
            _identifier(document.get("request_id"), f"{location}.request_id"), revision, entries,
            _digest(document.get("policy_sha256"), f"{location}.policy_sha256"),
            _timestamp(document.get("created_at"), f"{location}.created_at"),
        )
        supplied = _digest(document.get("bundle_sha256"), f"{location}.bundle_sha256")
        if supplied != result.bundle_sha256:
            raise ContractValidationError(f"{location}.bundle_sha256 does not match manifest contents")
        return result

    def to_dict(self) -> dict[str, Any]:
        result = self._payload(self.request_id, self.request_revision, self.entries, self.policy_sha256, self.created_at)
        result["bundle_sha256"] = self.bundle_sha256
        return result


@dataclass(frozen=True)
class ExecutionDecision:
    decision_id: str
    status: str
    planning_bundle_sha256: str
    editions: tuple[str, ...] = ()
    execution_scope: tuple[str, ...] = ()
    mode: Optional[str] = None
    resource_limits: Optional[Mapping[str, int]] = None
    valid_from: Optional[str] = None
    expires_at: Optional[str] = None
    approver_identity: Optional[str] = None
    reason: Optional[str] = None
    sources: tuple[str, ...] = ()
    schema_version: int = 1

    @classmethod
    def from_dict(cls, raw: Mapping[str, Any]) -> "ExecutionDecision":
        location = "execution_decision"
        document = _mapping(raw, location)
        required = {"schema_version", "kind", "decision_id", "status", "planning_bundle_sha256"}
        optional = {"editions", "execution_scope", "mode", "resource_limits", "valid_from", "expires_at", "approver_identity", "reason", "sources"}
        _closed(document, required, optional, location)
        _header(document, "execution_decision", location)
        status = _text(document.get("status"), f"{location}.status")
        if status not in ("pending", "approved", "declined", "deferred"):
            raise ContractValidationError(f"{location}.status is invalid")
        if status == "pending":
            unexpected = sorted(set(document) & optional)
            if unexpected:
                raise ContractValidationError(f"{location} pending decision has unexpected authorization fields: " + ", ".join(unexpected))
            return cls(
                _identifier(document.get("decision_id"), f"{location}.decision_id"), status,
                _digest(document.get("planning_bundle_sha256"), f"{location}.planning_bundle_sha256"),
            )
        if status in ("declined", "deferred"):
            allowed = {"reason", "sources"}
            unexpected = sorted((set(document) & optional) - allowed)
            if unexpected:
                raise ContractValidationError(f"{location} {status} decision has unexpected authorization fields")
            return cls(
                _identifier(document.get("decision_id"), f"{location}.decision_id"), status,
                _digest(document.get("planning_bundle_sha256"), f"{location}.planning_bundle_sha256"),
                reason=_text(document.get("reason"), f"{location}.reason"),
                sources=_strings(document.get("sources"), f"{location}.sources", True),
            )
        approved_required = {"editions", "execution_scope", "mode", "resource_limits", "valid_from", "expires_at", "approver_identity"}
        missing = approved_required - set(document)
        if missing:
            raise ContractValidationError(f"{location} approved decision missing " + ", ".join(sorted(missing)))
        if "reason" in document or "sources" in document:
            raise ContractValidationError(f"{location} approved decision must not declare reason or sources")
        editions = _strings(document.get("editions"), f"{location}.editions", True)
        for index, edition in enumerate(editions):
            _edition(edition, f"{location}.editions[{index}]")
        mode = _text(document.get("mode"), f"{location}.mode")
        if mode not in ("full", "partial"):
            raise ContractValidationError(f"{location}.mode must be full or partial")
        limits = _mapping(document.get("resource_limits"), f"{location}.resource_limits")
        _closed(limits, {"max_concurrency", "time_seconds", "disk_bytes"}, set(), f"{location}.resource_limits")
        for key, value in limits.items():
            minimum = 0 if key == "disk_bytes" else 1
            if type(value) is not int or value < minimum:
                raise ContractValidationError(f"{location}.resource_limits.{key} is invalid")
        valid_from = _timestamp(document.get("valid_from"), f"{location}.valid_from")
        expires_at = _timestamp(document.get("expires_at"), f"{location}.expires_at")
        if datetime.fromisoformat(expires_at.replace("Z", "+00:00")) <= datetime.fromisoformat(valid_from.replace("Z", "+00:00")):
            raise ContractValidationError(f"{location}.expires_at must be after valid_from")
        return cls(
            _identifier(document.get("decision_id"), f"{location}.decision_id"), status,
            _digest(document.get("planning_bundle_sha256"), f"{location}.planning_bundle_sha256"),
            editions, _identifiers(document.get("execution_scope"), f"{location}.execution_scope", True),
            mode, limits, valid_from, expires_at,
            _text(document.get("approver_identity"), f"{location}.approver_identity"),
        )

    def to_dict(self) -> dict[str, Any]:
        document: dict[str, Any] = {
            "schema_version": self.schema_version, "kind": "execution_decision",
            "decision_id": self.decision_id, "status": self.status,
            "planning_bundle_sha256": self.planning_bundle_sha256,
        }
        if self.status == "approved":
            document.update({
                "editions": list(self.editions), "execution_scope": list(self.execution_scope),
                "mode": self.mode, "resource_limits": dict(self.resource_limits or {}),
                "valid_from": self.valid_from, "expires_at": self.expires_at,
                "approver_identity": self.approver_identity,
            })
        elif self.status in ("declined", "deferred"):
            document["reason"] = self.reason
            document["sources"] = list(self.sources)
        return document


@dataclass(frozen=True)
class ExecutionHandoff:
    handoff_id: str
    decision_id: str
    decision_sha256: str
    planning_bundle_sha256: str
    editions: tuple[str, ...]
    execution_scope: tuple[str, ...]
    mode: str
    plan_bindings: tuple[ArtifactBinding, ...]
    expires_at: str
    schema_version: int = 1

    @classmethod
    def from_dict(cls, raw: Mapping[str, Any]) -> "ExecutionHandoff":
        location = "execution_handoff"
        document = _mapping(raw, location)
        required = {
            "schema_version", "kind", "handoff_id", "decision_id", "decision_sha256",
            "planning_bundle_sha256", "editions", "execution_scope", "mode", "plan_bindings", "expires_at",
        }
        _closed(document, required, set(), location)
        _header(document, "execution_handoff", location)
        editions = _strings(document.get("editions"), f"{location}.editions", True)
        for index, edition in enumerate(editions):
            _edition(edition, f"{location}.editions[{index}]")
        mode = _text(document.get("mode"), f"{location}.mode")
        if mode not in ("full", "partial"):
            raise ContractValidationError(f"{location}.mode must be full or partial")
        bindings_raw = document.get("plan_bindings")
        if not isinstance(bindings_raw, Sequence) or isinstance(bindings_raw, (str, bytes)) or not bindings_raw:
            raise ContractValidationError(f"{location}.plan_bindings must be a non-empty sequence")
        bindings = tuple(ArtifactBinding.from_dict(item, f"{location}.plan_bindings[{index}]") for index, item in enumerate(bindings_raw))
        if len({item.path for item in bindings}) != len(bindings):
            raise ContractValidationError("duplicate execution handoff plan binding")
        return cls(
            _identifier(document.get("handoff_id"), f"{location}.handoff_id"),
            _identifier(document.get("decision_id"), f"{location}.decision_id"),
            _digest(document.get("decision_sha256"), f"{location}.decision_sha256"),
            _digest(document.get("planning_bundle_sha256"), f"{location}.planning_bundle_sha256"),
            editions, _identifiers(document.get("execution_scope"), f"{location}.execution_scope", True),
            mode, bindings, _timestamp(document.get("expires_at"), f"{location}.expires_at"),
        )

    def binds(self, decision: ExecutionDecision) -> bool:
        return (
            decision.status == "approved"
            and self.decision_id == decision.decision_id
            and self.decision_sha256 == canonical_json_sha256(decision.to_dict())
            and self.planning_bundle_sha256 == decision.planning_bundle_sha256
            and self.editions == decision.editions
            and self.execution_scope == decision.execution_scope
            and self.mode == decision.mode
            and self.expires_at == decision.expires_at
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version, "kind": "execution_handoff",
            "handoff_id": self.handoff_id, "decision_id": self.decision_id,
            "decision_sha256": self.decision_sha256,
            "planning_bundle_sha256": self.planning_bundle_sha256,
            "editions": list(self.editions), "execution_scope": list(self.execution_scope),
            "mode": self.mode, "plan_bindings": [item.to_dict() for item in self.plan_bindings],
            "expires_at": self.expires_at,
        }


__all__ = [
    "ArtifactBinding", "AtomicRequirement", "UnresolvedQuestion", "FeatureSpec",
    "ImpactNode", "ImpactEdge", "FeatureImpactGraph", "FactorDecision",
    "PlanCaseBlueprint", "DryRenderArtifact", "AuditFinding", "AuditAttestation",
    "ExecutionCount", "ExecutionCost", "PartialExecutionProposal", "ExecutionRequirements",
    "ExecutionBrief", "PlanningBundleManifest", "ExecutionDecision", "ExecutionHandoff",
    "canonical_json_bytes", "canonical_json_sha256", "load_planning_contract",
]
