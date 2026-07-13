from __future__ import annotations

import argparse
from pathlib import Path

import yaml

from mysql_case_factory.contracts import REQUIRED_RISK_DECISIONS, inventory_values_sha256


OBJECTS = [
    "database", "table", "index", "view", "trigger", "procedure", "function",
    "event", "user", "role", "tablespace", "server", "resource_group",
    "spatial_reference_system", "component", "plugin", "loadable_function",
    "prepared_statement",
]
RELATIONS = ["base_table", "temporary_table", "view", "system_view"]
TABLE_AXES = {
    "table_persistence": (
        ["permanent", "temporary"],
        "references/combinations/_shared/coverage_inventory.yaml#relation_dimensions.relpersistence.values",
    ),
    "partition_role": (
        ["nonpartitioned", "partitioned", "partition"],
        "references/combinations/_shared/coverage_inventory.yaml#relation_dimensions.partition_role.values",
    ),
    "partition_strategy": (
        ["none", "range", "list", "hash", "key"],
        "references/combinations/_shared/coverage_inventory.yaml#relation_dimensions.partition_strategy.values",
    ),
    "inheritance_role": (
        ["unsupported"],
        "references/combinations/_shared/coverage_inventory.yaml#relation_dimensions.inheritance_role.values",
    ),
    "storage_engine": (
        ["innodb", "memory", "myisam"],
        "references/combinations/_shared/coverage_inventory.yaml#relation_dimensions.table_access_method_selection.values",
    ),
}
TYPE_AXES = {
    "numeric_type": (["tinyint", "smallint", "mediumint", "int", "bigint", "decimal", "float", "double", "bit"], "numeric"),
    "string_type": (["char", "varchar", "binary", "varbinary", "tinytext", "text", "mediumtext", "longtext", "enum", "set"], "string"),
    "temporal_type": (["date", "time", "datetime", "timestamp", "year"], "temporal"),
    "json_type": (["json"], "json"),
    "spatial_type": (["geometry", "point", "linestring", "polygon"], "spatial"),
    "blob_type": (["tinyblob", "blob", "mediumblob", "longblob"], "blob"),
}


def axis(values: list[str], source: str) -> dict:
    return {
        "values": values,
        "inventory_source": source,
        "coverage_mode": "complete",
        "inventory_count": len(values),
        "inventory_sha256": inventory_values_sha256(values),
    }


def point(point_id: str, title: str, axes: list[str]) -> dict:
    return {
        "id": point_id,
        "title": title,
        "requirement_ids": ["REQ-001"],
        "core_axes": axes,
        "dependencies": [],
        "classification_rules": [],
        "default_outcome": "success",
    }


def build(edition_root: Path) -> None:
    edition_root = edition_root.resolve()
    manifest = yaml.safe_load((edition_root / "edition.yaml").read_text(encoding="utf-8"))
    skill_root = edition_root / manifest["skill"]["root"]
    templates = skill_root / "assets" / "templates"
    templates.mkdir(parents=True, exist_ok=True)
    target = manifest["edition_id"]
    version = manifest["target_version"]

    feature = {
        "schema_version": 1,
        "kind": "feature_manifest",
        "feature_id": "mysql-storage-feature",
        "title": "MySQL storage compatibility feature",
        "compatibility_target": target,
        "summary": f"Verify exact MySQL {version} observable behavior on reference and DUT.",
        "source": {
            "path": "feature-document.md",
            "sha256": "0" * 64,
            "revision": "user-supplied-revision",
        },
        "requirements": [
            {
                "id": "REQ-001",
                "description": f"Reference and DUT preserve exact MySQL {version} SQL-visible behavior.",
                "source": {"section": "scope", "locator": "observable compatibility boundary"},
            }
        ],
        "metadata": {
            "assumptions": [f"Both endpoints implement MySQL Community Server {version} SQL semantics."],
            "unresolved_questions": [],
            "observable_boundary": "sql-and-user-visible-output",
            "storage_diagnostics_owner": "user",
        },
    }
    (templates / "feature_manifest_template.yaml").write_text(
        yaml.safe_dump(feature, sort_keys=False, allow_unicode=True, width=120), encoding="utf-8"
    )

    axes = {
        "object_type": axis(
            OBJECTS,
            "references/combinations/_shared/coverage_inventory.yaml#sql_object_types.all_sql_object_types",
        ),
        "relation_kind": axis(
            RELATIONS,
            "references/combinations/_shared/coverage_inventory.yaml#relation_kinds.all_mysql8022_relkinds",
        ),
    }
    for name, (values, source) in TABLE_AXES.items():
        axes[name] = axis(values, source)
    for name, (values, family) in TYPE_AXES.items():
        axes[name] = axis(
            values,
            f"references/common/mysql80_type_catalog.md#structured_config.families.{family}.values",
        )

    points = [
        point("TP-OBJECT", "Every supported MySQL object type", ["object_type"]),
        point("TP-RELATION", "Every MySQL relation kind", ["relation_kind"]),
        point("TP-TABLE", "Complete MySQL table-storage cross product", list(TABLE_AXES)),
    ]
    points.extend(
        point(f"TP-TYPE-{name.upper().replace('_', '-')}", f"Every {family} column type", [name])
        for name, (_, family) in TYPE_AXES.items()
    )
    risk_binding = {
        "syntax": ("object_type", "TP-OBJECT"),
        "operation": ("object_type", "TP-OBJECT"),
        "lifecycle": ("relation_kind", "TP-RELATION"),
        "data_profile": ("numeric_type", "TP-TYPE-NUMERIC-TYPE"),
        "large_value_lob": ("blob_type", "TP-TYPE-BLOB-TYPE"),
        "transaction": ("table_persistence", "TP-TABLE"),
        "partitioning": ("partition_strategy", "TP-TABLE"),
        "index_constraint_trigger": ("object_type", "TP-OBJECT"),
        "privilege": ("object_type", "TP-OBJECT"),
        "maintenance": ("storage_engine", "TP-TABLE"),
        "concurrency": ("relation_kind", "TP-RELATION"),
        "restart_recovery": ("storage_engine", "TP-TABLE"),
    }
    risks = {
        risk: {
            "status": "covered",
            "axes": [risk_binding[risk][0]],
            "test_points": [risk_binding[risk][1]],
        }
        for risk in REQUIRED_RISK_DECISIONS
    }
    plan = {
        "schema_version": 1,
        "kind": "coverage_plan",
        "plan_id": f"PLAN-MYSQL-{version.replace('.', '-')}-BASELINE",
        "feature_id": "mysql-storage-feature",
        "axes": axes,
        "scope_decisions": {
            "object": {"status": "complete", "axis": "object_type"},
            "relation": {"status": "complete", "axis": "relation_kind"},
            "table": {"status": "complete", "axes": list(TABLE_AXES)},
            "column_type": {"status": "complete", "axes": list(TYPE_AXES)},
        },
        "risk_decisions": risks,
        "test_points": points,
        "metadata": {"edition_id": target, "template_obligation_count": 145},
    }
    (templates / "coverage_plan_template.yaml").write_text(
        yaml.safe_dump(plan, sort_keys=False, allow_unicode=True, width=120), encoding="utf-8"
    )

    profile = {
        "schema_version": 1,
        "kind": "execution_profile",
        "compatibility_target": target,
        "reference": {
            "login_path": f"mysql{version.replace('.', '')}_reference",
            "database": "regression",
            "expected_server_uuid": "11111111-1111-1111-1111-111111111111",
            "expected_current_user": "regression_user@%",
        },
        "dut": {
            "login_path": f"mysql{version.replace('.', '')}_dut",
            "database": "regression",
            "expected_server_uuid": "22222222-2222-2222-2222-222222222222",
            "expected_current_user": "regression_user@%",
        },
        "runner": {"executable": "mysql", "timeout_seconds": 300, "stop_on_error": True},
        "comparison": {
            "mode": "exact_text",
            "normalization": {"drop_line_patterns": [], "replacements": [], "strip_trailing_whitespace": False},
        },
        "security": {"credential_source": "external-mysql-login-path", "persist_credentials": False},
    }
    (templates / "execution_profile_template.yaml").write_text(
        yaml.safe_dump(profile, sort_keys=False, allow_unicode=True, width=120), encoding="utf-8"
    )

    case = {
        "schema_version": 1,
        "kind": "case_manifest",
        "case_id": "CASE-TP-OBJECT-0001",
        "test_point_id": "TP-OBJECT",
        "obligation_id": "obl-replace-with-expanded-id",
        "outcome": "success",
        "sql_files": ["cases/sql/TP-OBJECT/case_0001.sql"],
        "sql_sha256": "b4e0497804e46e0a0b0b8c31975b062152d551bac49c3c2e80932567b4085dcd",
        "execution_profile": "basic_mysql",
        "comparison": {"mode": "exact_text", "oracle": f"upstream-{target}", "require_identical": True},
        "cleanup": {"required": True, "idempotent": True},
        "metadata": {
            "assignments": {"object_type": "table"},
            "requirement_ids": ["REQ-001"],
            "source_manifest": "inputs/feature_manifest.yaml",
            "coverage_plan": "plans/coverage_plan.yaml",
        },
    }
    (templates / "case_manifest_template.yaml").write_text(
        yaml.safe_dump(case, sort_keys=False, allow_unicode=True, width=120), encoding="utf-8"
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Build complete contract templates for one MySQL edition.")
    parser.add_argument("--edition-root", type=Path, required=True)
    args = parser.parse_args()
    build(args.edition_root)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
