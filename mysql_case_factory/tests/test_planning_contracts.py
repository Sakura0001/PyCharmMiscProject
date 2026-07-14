from __future__ import annotations

import copy
import json
from dataclasses import fields
from pathlib import Path

import pytest
import yaml

from mysql_case_factory.contracts import (
    ContractValidationError,
    CoverageContract,
    CoverageExpectedCounts,
    CoveragePlan,
)
from mysql_case_factory.coverage import expand_coverage_plan
from mysql_case_factory.planning_contracts import (
    ArtifactBinding,
    AuditAttestation,
    DryRenderArtifact,
    ExecutionBrief,
    ExecutionDecision,
    ExecutionHandoff,
    FactorDecision,
    FeatureImpactGraph,
    FeatureSpec,
    PlanCaseBlueprint,
    PlanningBundleManifest,
    Provenance,
    canonical_json_sha256,
    load_planning_contract,
)


FIXTURES = Path(__file__).parent / "fixtures" / "coverage"
SHA_A = "a" * 64
SHA_B = "b" * 64


def provenance(role: str) -> dict:
    return {
        "producer_role": role,
        "input_artifacts": [
            {"path": "inputs/feature.md", "sha256": SHA_A},
        ],
        "output_sha256": SHA_B,
        "policy_sha256": SHA_A,
        "created_at": "2026-07-14T00:00:00Z",
    }


def test_artifact_bindings_are_closed_portable_and_digest_bound(tmp_path: Path) -> None:
    binding = ArtifactBinding.from_dict({"path": "analysis/feature_spec.yaml", "sha256": SHA_A})
    assert binding.to_dict() == {"path": "analysis/feature_spec.yaml", "sha256": SHA_A}

    for path in ("/tmp/spec.yaml", "../spec.yaml", "analysis\\spec.yaml"):
        with pytest.raises(ContractValidationError, match="relative|portable|escape"):
            ArtifactBinding.from_dict({"path": path, "sha256": SHA_A})
    with pytest.raises(ContractValidationError, match="unexpected"):
        ArtifactBinding.from_dict(
            {"path": "analysis/spec.yaml", "sha256": SHA_A, "ignored": True}
        )
    with pytest.raises(ContractValidationError, match="SHA-256"):
        ArtifactBinding.from_dict({"path": "analysis/spec.yaml", "sha256": "weak"})

    path = tmp_path / "binding.yaml"
    path.write_text("path: a.yaml\npath: b.yaml\nsha256: " + SHA_A + "\n", encoding="utf-8")
    with pytest.raises(ContractValidationError, match="duplicate YAML key path"):
        load_planning_contract(path, ArtifactBinding)

    malformed = tmp_path / "unhashable-key.yaml"
    malformed.write_text("? [nested, key]\n: value\n", encoding="utf-8")
    with pytest.raises(ContractValidationError, match="mapping keys must be strings"):
        load_planning_contract(malformed, ArtifactBinding)


@pytest.mark.parametrize(
    "path",
    (
        "./planning_bundle_manifest.json",
        "./planning_run.json",
        "./decision/execution_decision.yaml",
        "a//b.yaml",
        "a/./b.yaml",
    ),
)
def test_relative_path_aliases_are_rejected_before_bundle_checks(path: str) -> None:
    with pytest.raises(ContractValidationError, match="canonical relative path"):
        ArtifactBinding.from_dict({"path": path, "sha256": SHA_A})


def test_canonical_json_is_recursive_and_preserves_bool_int_identity() -> None:
    with pytest.raises(ContractValidationError, match="mapping keys must be strings"):
        canonical_json_sha256({1: "integer-key"})
    with pytest.raises(ContractValidationError, match="finite|supported"):
        canonical_json_sha256({"nested": [float("nan")]})
    assert canonical_json_sha256({"value": True}) != canonical_json_sha256({"value": 1})


def feature_spec_document() -> dict:
    return {
        "schema_version": 1,
        "kind": "feature_spec",
        "feature_id": "alter-table-add-column-enhancement",
        "operation": "alter_table_add_column",
        "target_objects": ["innodb_table"],
        "behavior_change": "ADD COLUMN semantics are enhanced.",
        "affected_phases": ["definition", "execution", "verification"],
        "target_editions": ["mysql_8_0_22", "mysql_8_0_41"],
        "constraints": ["engine=innodb"],
        "requirements": [
            {
                "id": "REQ-ADD-1",
                "description": "Plan the enhanced ADD COLUMN behavior.",
                "source_locator": "inputs/feature.md#alter-table-add-column",
            }
        ],
        "source_locators": ["inputs/feature.md#alter-table-add-column"],
        "unresolved_questions": [],
        "status": "complete",
        "provenance": provenance("requirement_analyst"),
    }


def test_feature_spec_is_closed_and_complete_rejects_unresolved_questions() -> None:
    spec = FeatureSpec.from_dict(feature_spec_document())
    assert spec.operation == "alter_table_add_column"
    assert spec.to_dict() == feature_spec_document()

    unresolved = feature_spec_document()
    unresolved["unresolved_questions"] = [
        {
            "id": "Q-1",
            "question": "Does the enhancement alter positional INSTANT support?",
            "coverage_impact": "Changes the version-witness suite.",
            "source_locator": "inputs/feature.md#alter-table-add-column",
        }
    ]
    with pytest.raises(ContractValidationError, match="unresolved questions.*complete"):
        FeatureSpec.from_dict(unresolved)


def impact_graph_document() -> dict:
    return {
        "schema_version": 1,
        "kind": "feature_impact_graph",
        "feature_id": "alter-table-add-column-enhancement",
        "nodes": [
            {
                "id": "requirement.REQ-ADD-1",
                "type": "requirement",
                "label": "ADD COLUMN enhancement",
                "sources": ["inputs/feature.md#alter-table-add-column"],
            },
            {
                "id": "factor.added_column_type",
                "type": "factor_domain",
                "label": "Added column type",
                "sources": ["references/common/feature_association_knowledge.yaml#rules.add-column"],
            },
        ],
        "edges": [
            {
                "id": "edge.requirement-to-type",
                "from": "requirement.REQ-ADD-1",
                "to": "factor.added_column_type",
                "rule_id": "rule.add-column-implies-type",
                "evidence": [
                    "references/common/feature_association_knowledge.yaml#rules.add-column"
                ],
            }
        ],
        "provenance": provenance("factor_association"),
    }


def test_impact_graph_has_typed_referentially_closed_unique_nodes_and_edges() -> None:
    graph = FeatureImpactGraph.from_dict(impact_graph_document())
    assert graph.to_dict() == impact_graph_document()

    duplicate = impact_graph_document()
    duplicate["nodes"].append(copy.deepcopy(duplicate["nodes"][0]))
    with pytest.raises(ContractValidationError, match="duplicate impact node id"):
        FeatureImpactGraph.from_dict(duplicate)

    dangling = impact_graph_document()
    dangling["edges"][0]["to"] = "factor.missing"
    with pytest.raises(ContractValidationError, match="unknown node"):
        FeatureImpactGraph.from_dict(dangling)


def factor_document(status: str = "covered") -> dict:
    document = {
        "schema_version": 1,
        "kind": "factor_decision",
        "factor_id": "added_column_type",
        "domain": "data_and_type",
        "status": status,
        "trigger_path": ["requirement.REQ-ADD-1", "factor.added_column_type"],
        "edition_applicability": {
            "mysql_8_0_22": "applicable",
            "mysql_8_0_41": "applicable",
        },
        "combination_strategy": "full_cross",
        "dependencies": ["innodb_table_recipe"],
        "exclusions": [],
        "owning_suite_id": "suite.add-column-primary",
        "review_state": "reviewed",
        "inventory_source": "references/common/added_column_type_inventory.yaml#types",
        "inventory_sha256": SHA_A,
        "provenance": provenance("factor_association"),
    }
    if status != "covered":
        document.update(
            {
                "combination_strategy": "not_applicable" if status == "justified_na" else "unresolved",
                "reason": "No relevant executable surface is currently established.",
                "sources": ["references/common/mandatory_factor_domain_policy.yaml#domains"],
            }
        )
        document.pop("inventory_source")
        document.pop("inventory_sha256")
        document.pop("owning_suite_id")
    return document


def test_factor_decisions_require_inventory_or_evidenced_non_success() -> None:
    assert FactorDecision.from_dict(factor_document()).status == "covered"
    assert FactorDecision.from_dict(factor_document("justified_na")).status == "justified_na"
    assert FactorDecision.from_dict(factor_document("unknown")).status == "unknown"

    for field in ("reason", "sources"):
        invalid = factor_document("unknown")
        del invalid[field]
        with pytest.raises(ContractValidationError, match=field):
            FactorDecision.from_dict(invalid)

    missing_owner = factor_document()
    del missing_owner["owning_suite_id"]
    with pytest.raises(ContractValidationError, match="owning_suite_id"):
        FactorDecision.from_dict(missing_owner)

    with pytest.raises(ContractValidationError, match="unexpected"):
        FactorDecision.from_dict({**factor_document(), "unreviewed_hint": "sample"})


def blueprint_document(outcome: str = "success") -> dict:
    document = {
        "schema_version": 1,
        "kind": "plan_case_blueprint",
        "blueprint_id": "BP-ADD-1",
        "plan_id": "PLAN-ADD-8022",
        "edition": "mysql_8_0_22",
        "obligation_id": "obl-add-1",
        "assignments": {"innodb_table_recipe": "plain", "added_column_type": "int"},
        "setup_recipe": {"recipe_id": "plain", "steps": ["create_table", "seed"]},
        "target_statement": {"operation": "alter_table_add_column", "position": "last"},
        "verification_oracle": {"metadata": "column_exists", "data": "round_trip"},
        "cleanup_procedure": {"steps": ["drop_table"], "idempotent": True},
        "expected_outcome": outcome,
        "execution_profile": "basic_mysql",
        "provenance": provenance("lifecycle_oracle"),
    }
    if outcome == "expected_failure":
        document["diagnostic_contract"] = {
            "error_code": 1846,
            "sqlstate": "0A000",
            "terminal_error_count": 1,
            "message_pattern": "ALGORITHM=INSTANT is not supported",
        }
    return document


def test_blueprint_requires_all_lifecycle_phases_and_exact_negative_diagnostic() -> None:
    assert PlanCaseBlueprint.from_dict(blueprint_document()).diagnostic_contract is None
    negative = PlanCaseBlueprint.from_dict(blueprint_document("expected_failure"))
    assert negative.diagnostic_contract["sqlstate"] == "0A000"

    missing_phase = blueprint_document()
    missing_phase["verification_oracle"] = {}
    with pytest.raises(ContractValidationError, match="verification_oracle.*not be empty"):
        PlanCaseBlueprint.from_dict(missing_phase)

    missing_diagnostic = blueprint_document("expected_failure")
    del missing_diagnostic["diagnostic_contract"]["sqlstate"]
    with pytest.raises(ContractValidationError, match="sqlstate"):
        PlanCaseBlueprint.from_dict(missing_diagnostic)

    nested_non_string_key = blueprint_document()
    nested_non_string_key["setup_recipe"]["options"] = {1: "unsafe"}
    with pytest.raises(ContractValidationError, match="mapping keys must be strings"):
        PlanCaseBlueprint.from_dict(nested_non_string_key)


def test_dry_render_is_non_runnable_and_contains_no_execution_route() -> None:
    document = {
        "schema_version": 1,
        "kind": "dry_render_artifact",
        "dry_render_id": "DRY-ADD-1",
        "blueprint_id": "BP-ADD-1",
        "edition": "mysql_8_0_22",
        "blueprint_sha256": SHA_A,
        "canonical_sql_ast": {"statement": "alter_table", "action": "add_column"},
        "canonical_ast_sha256": canonical_json_sha256(
            {"statement": "alter_table", "action": "add_column"}
        ),
        "normalized_identifiers": {"table": "<table>", "column": "<added_column>"},
        "preview_text": "NON-RUNNABLE PREVIEW: ALTER TABLE <table> ADD COLUMN <added_column> INT",
        "runnable": False,
        "provenance": provenance("deterministic_coverage_compiler"),
    }
    artifact = DryRenderArtifact.from_dict(document)
    assert artifact.to_dict() == document

    executable = copy.deepcopy(document)
    executable["runnable"] = True
    with pytest.raises(ContractValidationError, match="runnable must be false"):
        DryRenderArtifact.from_dict(executable)
    with pytest.raises(ContractValidationError, match="unexpected"):
        DryRenderArtifact.from_dict({**document, "endpoint": "mysql://secret"})


def attestation_document() -> dict:
    return {
        "schema_version": 1,
        "kind": "audit_attestation",
        "attestation_id": "AUDIT-COVERAGE-1",
        "auditor_role": "coverage_auditor",
        "permitted_inputs": [
            {"path": "inputs/feature.md", "sha256": SHA_A},
            {"path": "audits/blind_draft.yaml", "sha256": SHA_B},
        ],
        "candidate_plan_sha256": SHA_A,
        "reconstructed_factor_ids": ["added_column_type", "innodb_table_recipe"],
        "missing_factor_ids": [],
        "excess_factor_ids": [],
        "findings": [],
        "final_decision": "pass",
        "provenance": provenance("coverage_auditor"),
    }


def test_audit_pass_rejects_open_findings_or_factor_diffs() -> None:
    assert AuditAttestation.from_dict(attestation_document()).final_decision == "pass"

    invalid = attestation_document()
    invalid["missing_factor_ids"] = ["algorithm"]
    with pytest.raises(ContractValidationError, match="pass.*missing"):
        AuditAttestation.from_dict(invalid)

    invalid = attestation_document()
    invalid["findings"] = [
        {
            "id": "F-1",
            "status": "open",
            "severity": "high",
            "description": "Algorithm coverage is absent.",
            "sources": ["references/common/mandatory_factor_domain_policy.yaml#domains"],
        }
    ]
    with pytest.raises(ContractValidationError, match="pass.*open finding"):
        AuditAttestation.from_dict(invalid)


@pytest.mark.parametrize("decision", ["rework", "blocked"])
def test_non_pass_audit_requires_a_reason_and_sources(decision: str) -> None:
    invalid = attestation_document()
    invalid["final_decision"] = decision
    with pytest.raises(ContractValidationError, match="reason|sources"):
        AuditAttestation.from_dict(invalid)

    valid = attestation_document()
    valid["final_decision"] = decision
    valid["reason"] = "Coverage findings require owner rework."
    valid["sources"] = ["audits/blind_draft.yaml#findings"]
    attestation = AuditAttestation.from_dict(valid)
    assert attestation.to_dict() == valid


def execution_brief_document() -> dict:
    return {
        "schema_version": 1,
        "kind": "execution_brief",
        "brief_id": "BRIEF-ADD-1",
        "counts": [
            {
                "edition": "mysql_8_0_22",
                "suite_id": "suite.add-column-primary",
                "total": 66,
                "success": 65,
                "expected_failure": 1,
                "justified_na": 0,
            },
            {
                "edition": "mysql_8_0_41",
                "suite_id": "suite.add-column-primary",
                "total": 66,
                "success": 66,
                "expected_failure": 0,
                "justified_na": 0,
            },
            {
                "edition": "mysql_8_0_22",
                "suite_id": "suite.add-column-version-witness",
                "total": 1,
                "success": 0,
                "expected_failure": 1,
                "justified_na": 0,
            },
            {
                "edition": "mysql_8_0_41",
                "suite_id": "suite.add-column-version-witness",
                "total": 1,
                "success": 1,
                "expected_failure": 0,
                "justified_na": 0,
            },
        ],
        "full_cost": {"estimated_seconds": 900, "disk_bytes": 1048576, "max_concurrency": 2},
        "partial_proposals": [
            {
                "proposal_id": "partial.version-witness-only",
                "selected_suite_ids": ["suite.add-column-version-witness"],
                "cost": {"estimated_seconds": 30, "disk_bytes": 4096, "max_concurrency": 1},
                "confidence_lost": [
                    "Does not validate the full InnoDB recipe by added-column-type Cartesian set."
                ],
            }
        ],
        "requirements": {
            "endpoints": ["one reference and one DUT for each exact patch edition"],
            "topology": ["standalone primary for the primary suite"],
            "privileges": ["CREATE", "ALTER", "DROP", "SELECT", "INSERT"],
            "disk_bytes": 1048576,
            "time_seconds": 900,
            "max_concurrency": 2,
            "harnesses": ["basic_mysql"],
        },
        "safety_blockers": [],
        "known_risks": ["DDL runtime varies by table shape."],
        "decision_consequences": {
            "full": ["Runs every approved obligation and can support a full validation claim."],
            "partial": ["Cannot support a complete feature-validation claim."],
            "deferred": ["Preserves the plan but produces no runtime product evidence."],
            "declined": ["Closes this execution request without runtime product evidence."],
        },
        "provenance": provenance("execution_gatekeeper"),
    }


def test_execution_brief_has_exact_counts_and_partial_confidence_loss() -> None:
    brief = ExecutionBrief.from_dict(execution_brief_document())
    assert brief.to_dict() == execution_brief_document()

    bad_count = execution_brief_document()
    bad_count["counts"][0]["success"] = 64
    with pytest.raises(ContractValidationError, match="total must equal"):
        ExecutionBrief.from_dict(bad_count)

    no_loss = execution_brief_document()
    no_loss["partial_proposals"][0]["confidence_lost"] = []
    with pytest.raises(ContractValidationError, match="confidence_lost"):
        ExecutionBrief.from_dict(no_loss)

    no_partials = execution_brief_document()
    no_partials["partial_proposals"] = []
    assert ExecutionBrief.from_dict(no_partials).to_dict() == no_partials

    unknown_suite = execution_brief_document()
    unknown_suite["partial_proposals"][0]["selected_suite_ids"] = ["suite.missing"]
    with pytest.raises(ContractValidationError, match="unknown selected suite"):
        ExecutionBrief.from_dict(unknown_suite)

    inconsistent_scope = execution_brief_document()
    inconsistent_scope["counts"] = [
        row
        for row in inconsistent_scope["counts"]
        if not (
            row["suite_id"] == "suite.add-column-version-witness"
            and row["edition"] == "mysql_8_0_41"
        )
    ]
    with pytest.raises(ContractValidationError, match="edition scope"):
        ExecutionBrief.from_dict(inconsistent_scope)

    for decision in ("full", "partial", "deferred", "declined"):
        missing = execution_brief_document()
        del missing["decision_consequences"][decision]
        with pytest.raises(ContractValidationError, match="decision_consequences"):
            ExecutionBrief.from_dict(missing)

        empty = execution_brief_document()
        empty["decision_consequences"][decision] = []
        with pytest.raises(ContractValidationError, match=decision):
            ExecutionBrief.from_dict(empty)


def test_execution_brief_is_digestible_before_bundle_and_rejects_bundle_digest() -> None:
    brief = ExecutionBrief.from_dict(execution_brief_document())
    brief_sha256 = canonical_json_sha256(brief.to_dict())
    manifest = PlanningBundleManifest.create(
        request_id="REQ-ADD-1",
        request_revision=1,
        entries=(ArtifactBinding("execution_brief.json", brief_sha256),),
        policy_sha256=SHA_A,
        created_at="2026-07-14T00:00:00Z",
    )
    assert manifest.entries[0].sha256 == brief_sha256
    assert "planning_bundle_sha256" not in brief.to_dict()

    circular = execution_brief_document()
    circular["planning_bundle_sha256"] = manifest.bundle_sha256
    with pytest.raises(ContractValidationError, match="unexpected.*planning_bundle_sha256"):
        ExecutionBrief.from_dict(circular)


def test_bundle_manifest_excludes_itself_ledger_and_decision_tree() -> None:
    entries = (
        ArtifactBinding("analysis/feature_spec.yaml", SHA_A),
        ArtifactBinding("execution_brief.json", SHA_B),
    )
    manifest = PlanningBundleManifest.create(
        request_id="REQ-ADD-1",
        request_revision=1,
        entries=entries,
        policy_sha256=SHA_A,
        created_at="2026-07-14T00:00:00Z",
    )
    assert PlanningBundleManifest.from_dict(manifest.to_dict()) == manifest
    assert manifest.provenance.producer_role == "planning_orchestrator"

    for forbidden in (
        "planning_bundle_manifest.json",
        "planning_run.json",
        "decision/execution_decision.yaml",
    ):
        with pytest.raises(ContractValidationError, match="must not include|decision"):
            PlanningBundleManifest.create(
                request_id="REQ-ADD-1",
                request_revision=1,
                entries=(ArtifactBinding(forbidden, SHA_A),),
                policy_sha256=SHA_A,
                created_at="2026-07-14T00:00:00Z",
            )


def test_every_planning_artifact_requires_strict_provenance() -> None:
    manifest = PlanningBundleManifest.create(
        request_id="REQ-ADD-1",
        request_revision=1,
        entries=(ArtifactBinding("analysis/feature_spec.yaml", SHA_A),),
        policy_sha256=SHA_A,
        created_at="2026-07-14T00:00:00Z",
    ).to_dict()
    artifacts = (
        (FeatureSpec, feature_spec_document()),
        (FeatureImpactGraph, impact_graph_document()),
        (FactorDecision, factor_document()),
        (PlanCaseBlueprint, blueprint_document()),
        (
            DryRenderArtifact,
            {
                "schema_version": 1,
                "kind": "dry_render_artifact",
                "dry_render_id": "DRY-ADD-1",
                "blueprint_id": "BP-ADD-1",
                "edition": "mysql_8_0_22",
                "blueprint_sha256": SHA_A,
                "canonical_sql_ast": {"statement": "alter_table"},
                "canonical_ast_sha256": canonical_json_sha256({"statement": "alter_table"}),
                "normalized_identifiers": {"table": "<table>"},
                "preview_text": "NON-RUNNABLE PREVIEW",
                "runnable": False,
                "provenance": provenance("deterministic_coverage_compiler"),
            },
        ),
        (AuditAttestation, attestation_document()),
        (ExecutionBrief, execution_brief_document()),
        (PlanningBundleManifest, manifest),
    )
    for contract_type, document in artifacts:
        missing = copy.deepcopy(document)
        del missing["provenance"]
        with pytest.raises(ContractValidationError, match="provenance"):
            contract_type.from_dict(missing)

    valid_provenance = provenance("planning_orchestrator")
    assert Provenance.from_dict(valid_provenance).to_dict() == valid_provenance
    with pytest.raises(ContractValidationError, match="unexpected"):
        Provenance.from_dict({**valid_provenance, "endpoint": "must-not-exist"})


def test_external_decision_and_handoff_are_outside_planning_artifact_provenance() -> None:
    decision = approved_decision_document()
    decision["provenance"] = provenance("planning_orchestrator")
    with pytest.raises(ContractValidationError, match="unexpected"):
        ExecutionDecision.from_dict(decision)

    approved = ExecutionDecision.from_dict(approved_decision_document())
    handoff = {
        "schema_version": 1,
        "kind": "execution_handoff",
        "handoff_id": "HANDOFF-BOUNDARY-1",
        "decision_id": approved.decision_id,
        "decision_sha256": canonical_json_sha256(approved.to_dict()),
        "planning_bundle_sha256": approved.planning_bundle_sha256,
        "editions": list(approved.editions),
        "execution_scope": list(approved.execution_scope),
        "mode": approved.mode,
        "plan_bindings": [
            {"path": "plans/mysql_8_0_22/coverage_plan.yaml", "sha256": SHA_A},
        ],
        "expires_at": approved.expires_at,
        "provenance": provenance("planning_orchestrator"),
    }
    with pytest.raises(ContractValidationError, match="unexpected"):
        ExecutionHandoff.from_dict(handoff)


def _direct_reconstruct(value):
    return type(value)(**{field.name: getattr(value, field.name) for field in fields(value)})


def test_security_contracts_require_factories_and_deep_freeze_input_state() -> None:
    blueprint_source = blueprint_document()
    blueprint = PlanCaseBlueprint.from_dict(blueprint_source)
    blueprint_digest = canonical_json_sha256(blueprint.to_dict())
    blueprint_source["assignments"]["added_column_type"] = "bigint"
    blueprint_source["setup_recipe"]["steps"].append("tamper")
    assert canonical_json_sha256(blueprint.to_dict()) == blueprint_digest
    assert blueprint.assignments["added_column_type"] == "int"
    with pytest.raises(TypeError):
        blueprint.assignments["added_column_type"] = "text"
    with pytest.raises(AttributeError):
        blueprint.setup_recipe["steps"].append("tamper")
    with pytest.raises(ContractValidationError, match="validated factory"):
        _direct_reconstruct(blueprint)

    dry_source = {
        "schema_version": 1,
        "kind": "dry_render_artifact",
        "dry_render_id": "DRY-FROZEN",
        "blueprint_id": "BP-ADD-1",
        "edition": "mysql_8_0_22",
        "blueprint_sha256": SHA_A,
        "canonical_sql_ast": {"statement": "alter_table", "parts": ["add", "column"]},
        "canonical_ast_sha256": canonical_json_sha256(
            {"statement": "alter_table", "parts": ["add", "column"]}
        ),
        "normalized_identifiers": {"table": "<table>"},
        "preview_text": "NON-RUNNABLE PREVIEW",
        "runnable": False,
        "provenance": provenance("deterministic_coverage_compiler"),
    }
    dry = DryRenderArtifact.from_dict(dry_source)
    dry_source["canonical_sql_ast"]["parts"].append("tamper")
    assert dry.canonical_sql_ast["parts"] == ("add", "column")
    with pytest.raises(ContractValidationError, match="validated factory"):
        _direct_reconstruct(dry)

    decision_source = approved_decision_document()
    decision = ExecutionDecision.from_dict(decision_source)
    decision_source["resource_limits"]["max_concurrency"] = 999
    assert decision.resource_limits["max_concurrency"] == 2
    with pytest.raises(TypeError):
        decision.resource_limits["max_concurrency"] = 3
    with pytest.raises(ContractValidationError, match="validated factory"):
        _direct_reconstruct(decision)

    brief_source = execution_brief_document()
    brief = ExecutionBrief.from_dict(brief_source)
    brief_source["partial_proposals"][0]["selected_suite_ids"].append("suite.tamper")
    assert brief.partial_proposals[0].selected_suite_ids == (
        "suite.add-column-version-witness",
    )
    with pytest.raises(ContractValidationError, match="validated factory"):
        _direct_reconstruct(brief)


def approved_decision_document() -> dict:
    return {
        "schema_version": 1,
        "kind": "execution_decision",
        "decision_id": "DECISION-ADD-1",
        "status": "approved",
        "planning_bundle_sha256": SHA_A,
        "editions": ["mysql_8_0_22", "mysql_8_0_41"],
        "execution_scope": ["suite.add-column-primary"],
        "mode": "partial",
        "resource_limits": {"max_concurrency": 2, "time_seconds": 900, "disk_bytes": 1048576},
        "valid_from": "2026-07-14T00:00:00Z",
        "expires_at": "2026-07-15T00:00:00Z",
        "approver_identity": "host:user:yuyu",
    }


def test_execution_decision_is_explicit_and_handoff_binds_its_digest() -> None:
    decision = ExecutionDecision.from_dict(approved_decision_document())
    assert decision.status == "approved"

    pending = {
        "schema_version": 1,
        "kind": "execution_decision",
        "decision_id": "DECISION-ADD-1",
        "status": "pending",
        "planning_bundle_sha256": SHA_A,
    }
    assert ExecutionDecision.from_dict(pending).status == "pending"

    invalid = approved_decision_document()
    del invalid["approver_identity"]
    with pytest.raises(ContractValidationError, match="approver_identity"):
        ExecutionDecision.from_dict(invalid)

    decision_sha256 = canonical_json_sha256(decision.to_dict())
    handoff_document = {
        "schema_version": 1,
        "kind": "execution_handoff",
        "handoff_id": "HANDOFF-ADD-1",
        "decision_id": decision.decision_id,
        "decision_sha256": decision_sha256,
        "planning_bundle_sha256": SHA_A,
        "editions": ["mysql_8_0_22", "mysql_8_0_41"],
        "execution_scope": ["suite.add-column-primary"],
        "mode": "partial",
        "plan_bindings": [
            {"path": "plans/mysql_8_0_22/coverage_plan.yaml", "sha256": SHA_A},
            {"path": "plans/mysql_8_0_41/coverage_plan.yaml", "sha256": SHA_B},
        ],
        "expires_at": "2026-07-15T00:00:00Z",
    }
    handoff = ExecutionHandoff.from_dict(handoff_document)
    assert handoff.binds(decision)
    assert not handoff.binds(ExecutionDecision.from_dict({**pending, "decision_id": "DECISION-OTHER"}))


def test_coverage_contract_is_strict_and_legacy_v1_bytes_and_ids_are_frozen() -> None:
    expected = CoverageExpectedCounts.from_dict(
        {"total": 6, "success": 4, "expected_failure": 1, "justified_na": 1}
    )
    contract = CoverageContract.from_dict(
        {
            "combination_policy": "full_cross",
            "primary_axes": ["innodb_table_recipe", "added_column_type"],
            "condition_axes": [],
            "expected_counts": expected.to_dict(),
        }
    )
    assert contract.expected_counts == expected

    with pytest.raises(ContractValidationError, match="total must equal"):
        CoverageExpectedCounts.from_dict(
            {"total": 6, "success": 4, "expected_failure": 0, "justified_na": 1}
        )
    with pytest.raises(ContractValidationError, match="overlap"):
        CoverageContract.from_dict(
            {
                "combination_policy": "full_cross",
                "primary_axes": ["table"],
                "condition_axes": ["table"],
                "expected_counts": {"total": 1, "success": 1, "expected_failure": 0, "justified_na": 0},
            }
        )

    fixture_text = (FIXTURES / "legacy_plan_v1.yaml").read_text(encoding="utf-8")
    plan = CoveragePlan.from_dict(yaml.safe_load(fixture_text))
    assert all(point.coverage_contract is None for point in plan.test_points)
    assert yaml.safe_dump(plan.to_dict(), allow_unicode=True, sort_keys=False) == fixture_text

    obligations = [item.to_dict() for item in expand_coverage_plan(plan)]
    expected_obligations = json.loads(
        (FIXTURES / "legacy_obligations.json").read_text(encoding="utf-8")
    )
    assert obligations == expected_obligations
