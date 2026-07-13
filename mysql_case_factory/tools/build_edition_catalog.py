from __future__ import annotations

import argparse
import csv
import hashlib
import io
from pathlib import Path
from typing import Any, Mapping

import yaml

from mysql_case_factory.applicability import LEDGER_COLUMNS
from mysql_case_factory.matrix_generation import load_statement_reference


EXTERNAL_STATEMENTS = {
    "alter_instance",
    "create_logfile_group",
    "alter_logfile_group",
    "drop_logfile_group",
    "create_server",
    "alter_server",
    "drop_server",
    "create_tablespace",
    "alter_tablespace",
    "drop_tablespace",
    "create_resource_group",
    "alter_resource_group",
    "drop_resource_group",
    "set_resource_group",
    "install_component",
    "uninstall_component",
    "install_plugin",
    "uninstall_plugin",
    "create_function_loadable",
    "drop_function_loadable",
    "flush",
    "kill",
    "restart",
    "shutdown",
    "import_table",
    "load_data",
    "load_xml",
    "lock_instance",
    "unlock_instance",
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def factor_tiers(config: Mapping[str, Any]) -> dict[str, str]:
    result: dict[str, str] = {}
    layers = config.get("factor_layers") if isinstance(config.get("factor_layers"), list) else []
    for layer in layers:
        if not isinstance(layer, Mapping):
            continue
        for name in layer.get("factors", []):
            result[str(name)] = str(layer.get("tier") or "T3")
    return result


def factor_values(config: Mapping[str, Any]) -> dict[str, list[str]]:
    result: dict[str, list[str]] = {}
    factors = config.get("factors")
    if not isinstance(factors, Mapping):
        raise ValueError("statement reference has no factor mapping")
    for name, document in factors.items():
        if not isinstance(document, Mapping) or not isinstance(document.get("values"), list):
            raise ValueError(f"factor {name} has no values")
        values = []
        for item in document["values"]:
            value = item.get("key") if isinstance(item, Mapping) else item
            values.append(str(value).lower() if isinstance(value, bool) else str(value))
        result[str(name)] = values
    return result


def build(edition_root: Path) -> dict[str, int]:
    edition_root = edition_root.resolve()
    manifest_path = edition_root / "edition.yaml"
    manifest = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
    skill_root = edition_root / manifest["skill"]["root"]
    statements_root = skill_root / "references" / "statements"
    common_root = skill_root / "references" / "common"
    ledger_name = f"mysql_{manifest['target_version'].replace('.', '_')}_factor_audit.tsv"
    ledger_path = common_root / ledger_name

    support_rows: list[dict[str, Any]] = []
    ledger_rows: list[dict[str, str]] = []
    pair_count = 0
    for reference in sorted(statements_root.rglob("*.md")):
        config = load_statement_reference(reference)
        statement = config["statement"]
        key = str(statement["key"])
        category = str(config.get("category") or "unknown")
        domain = str(config.get("domain") or "unknown")
        relative_reference = reference.relative_to(skill_root).as_posix()
        relative_matrix = (
            Path("references/combinations")
            / reference.relative_to(statements_root).with_suffix(".yaml")
        ).as_posix()
        official_source = str(config.get("official_source") or statement.get("official_source") or "")
        if not official_source.startswith("https://dev.mysql.com/"):
            raise ValueError(f"{reference}: missing official MySQL source")
        support_rows.append(
            {
                "key": key,
                "name": str(statement.get("name") or key),
                "category": category,
                "domain": domain,
                "reference": relative_reference,
                "matrix": relative_matrix,
                "official_source": official_source,
                "support_status": "supported",
                "review_state": "static_complete",
                "runtime_state": "not_verified",
                "execution_profile": "external_isolated" if key in EXTERNAL_STATEMENTS else "basic_mysql",
            }
        )
        tiers = factor_tiers(config)
        values_by_factor = factor_values(config)
        pair_count += len(values_by_factor)
        evidence = f"mysql-{manifest['target_version']}-manual:{sha256(reference)[:16]}"
        for factor, values in values_by_factor.items():
            for value in values:
                ledger_rows.append(
                    {
                        "statement_key": key,
                        "source_reference": relative_reference,
                        "factor": factor,
                        "tier": tiers.get(factor, "T3"),
                        "value": value,
                        "synopsis_change": "edition_baseline",
                        "document_change": "edition_baseline",
                        "review_status": "static_reviewed",
                        "catalog_readiness": "static_ready",
                        "factor_disposition": "mysql_native",
                        "required_test_points": "",
                        "official_source_target": official_source,
                        "evidence": evidence,
                    }
                )

    buffer = io.StringIO(newline="")
    writer = csv.DictWriter(buffer, fieldnames=LEDGER_COLUMNS, delimiter="\t", lineterminator="\n")
    writer.writeheader()
    writer.writerows(ledger_rows)
    ledger_path.write_text(buffer.getvalue(), encoding="utf-8")
    ledger_digest = sha256(ledger_path)
    support_path = common_root / "statement_support_inventory.yaml"
    support_document = {
        "schema_version": 1,
        "kind": "mysql_statement_support_inventory",
        "edition_id": manifest["edition_id"],
        "target_version": manifest["target_version"],
        "source_policy": {
            "primary": "MySQL Community Server Reference Manual",
            "version_boundary": "Exact patch release notes plus version annotations in the rolling 8.0 manual.",
        },
        "statements": support_rows,
        "factor_audit": {
            "path": f"references/common/{ledger_name}",
            "sha256": ledger_digest,
            "statement_count": len(support_rows),
            "factor_pair_count": pair_count,
            "factor_value_count": len(ledger_rows),
        },
    }
    support_path.write_text(
        yaml.safe_dump(support_document, sort_keys=False, allow_unicode=True, width=120),
        encoding="utf-8",
    )
    manifest["review_state"] = "complete"
    manifest["inventories"] = [
        {
            "kind": "statement_support_inventory",
            "path": support_path.relative_to(edition_root).as_posix(),
            "sha256": sha256(support_path),
            "count": len(support_rows),
        },
        {
            "kind": "statement_factor_value_audit",
            "path": ledger_path.relative_to(edition_root).as_posix(),
            "sha256": ledger_digest,
            "count": len(ledger_rows),
        },
    ]
    manifest_path.write_text(
        yaml.safe_dump(manifest, sort_keys=False, allow_unicode=True, width=120),
        encoding="utf-8",
    )
    return {
        "statements": len(support_rows),
        "factor_pairs": pair_count,
        "factor_values": len(ledger_rows),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Build one edition's closed support and factor ledgers.")
    parser.add_argument("--edition-root", type=Path, required=True)
    arguments = parser.parse_args()
    counts = build(arguments.edition_root)
    print(yaml.safe_dump(counts, sort_keys=False).strip())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
