#!/usr/bin/env python3
"""Audit canonical PG18.4 inventories against official PostgreSQL sources."""

from __future__ import annotations

import argparse
import hashlib
import re
import sys
import tarfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Mapping

import yaml


COVERAGE_INVENTORY = Path(
    "skills/pg-sql-generation/references/combinations/_shared/coverage_inventory.yaml"
)
TYPE_CATALOG = Path(
    "skills/pg-sql-generation/references/common/pg18_type_catalog.md"
)
YAML_BLOCK = re.compile(r"```yaml\s*(.*?)```", re.DOTALL)

# These dimensions are semantic partitions used by the generator rather than
# one-to-one catalog enums.  Pin their exact closed sets here so changing the
# committed values and recomputing their self-hash cannot silently redefine
# what a plan calls "complete" table coverage.
EXPECTED_TABLE_DIMENSIONS = {
    "relpersistence": ("permanent", "unlogged", "temp"),
    "partition_role": ("non_partitioned", "partitioned_parent", "partition_leaf"),
    "partition_strategy": ("none", "range", "list", "hash"),
    "inheritance_role": ("none", "parent", "child", "parent_and_child"),
    "builtin_table_access_methods": ("heap",),
    "table_access_method_selection": (
        "default",
        "explicit_builtin",
        "extension_provided",
    ),
}
EXPECTED_DECLARATION_ALIASES = {
    "smallint": "int2",
    "integer": "int4",
    "bigint": "int8",
    "smallserial": "int2_with_sequence_default",
    "serial": "int4_with_sequence_default",
    "bigserial": "int8_with_sequence_default",
    "decimal": "numeric",
    "real": "float4",
    "double_precision": "float8",
    "float": "float4_or_float8_by_typmod",
    "character": "bpchar",
    "character_varying": "varchar",
    "boolean": "bool",
    "timestamp_with_time_zone": "timestamptz",
    "time_with_time_zone": "timetz",
    "bit_varying": "varbit",
}
EXPECTED_TYPMOD_PROFILES = {
    "numeric": {
        "success": ("NUMERIC", "NUMERIC(1)", "NUMERIC(1000)", "NUMERIC(10,0)", "NUMERIC(10,2)", "NUMERIC(10,-2)", "NUMERIC(1,1000)"),
        "failure": ("NUMERIC(0)", "NUMERIC(1001)", "NUMERIC(10,-1001)", "NUMERIC(10,1001)"),
    },
    "character": {
        "success": ("VARCHAR", "VARCHAR(1)", "VARCHAR(10485760)", "CHARACTER", "CHARACTER(1)", "CHARACTER(10485760)"),
        "failure": ("VARCHAR(0)", "VARCHAR(10485761)", "CHARACTER(0)", "CHARACTER(10485761)"),
    },
    "bit_string": {
        "success": ("BIT", "BIT(1)", "BIT(83886080)", "BIT VARYING", "BIT VARYING(1)", "BIT VARYING(83886080)"),
        "failure": ("BIT(0)", "BIT(83886081)", "BIT VARYING(0)", "BIT VARYING(83886081)"),
    },
    "float": {
        "success": ("FLOAT", "FLOAT(1)", "FLOAT(24)", "FLOAT(25)", "FLOAT(53)"),
        "failure": ("FLOAT(0)", "FLOAT(54)"),
    },
    "datetime_precision": {
        "success": ("TIME(0)", "TIME(6)", "TIMESTAMP(0)", "TIMESTAMP(6)", "INTERVAL(0)", "INTERVAL(6)"),
        "failure": ("TIME(7)", "TIMESTAMP(7)", "INTERVAL(7)"),
    },
    "interval_fields": {
        "success": ("INTERVAL YEAR", "INTERVAL MONTH", "INTERVAL DAY", "INTERVAL HOUR", "INTERVAL MINUTE", "INTERVAL SECOND", "INTERVAL YEAR TO MONTH", "INTERVAL DAY TO HOUR", "INTERVAL DAY TO MINUTE", "INTERVAL DAY TO SECOND", "INTERVAL HOUR TO MINUTE", "INTERVAL HOUR TO SECOND", "INTERVAL MINUTE TO SECOND"),
        "failure": (),
    },
}
EXPECTED_USER_DEFINED_ARCHETYPES = (
    "enum",
    "domain",
    "composite",
    "table_row_type",
    "base_type",
    "range",
    "multirange",
    "array_of_user_defined_type",
)


class UniqueKeySafeLoader(yaml.SafeLoader):
    def construct_mapping(self, node, deep=False):
        seen = set()
        for key_node, _ in node.value:
            key = self.construct_object(key_node, deep=deep)
            if key in seen:
                raise ValueError(f"duplicate YAML key {key}")
            seen.add(key)
        return super().construct_mapping(node, deep=deep)


@dataclass
class AuditResult:
    errors: list[str] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        return not self.errors


@dataclass(frozen=True)
class PgTypeInventory:
    concrete: tuple[str, ...]
    array_elements: tuple[str, ...]
    pseudo: tuple[str, ...]


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def inventory_values_sha256(values) -> str:
    """Match pg_case_factory's ordered, type-tagged inventory digest."""

    tagged = [{"tag": "tag:yaml.org,2002:str", "value": value} for value in values]
    payload = yaml.safe_dump(
        tagged,
        allow_unicode=True,
        default_flow_style=False,
        explicit_start=True,
        sort_keys=True,
        width=4096,
    ).encode("utf-8")
    return _sha256(payload)


def derive_relkind_records(source: str) -> tuple[tuple[str, str], ...]:
    records = tuple(
        (name.lower(), code)
        for name, code in re.findall(
            r"^#define\s+RELKIND_([A-Z0-9_]+)\s+'([^']+)'",
            source,
            re.MULTILINE,
        )
    )
    if len(records) != 10 or len({name for name, _ in records}) != len(records):
        raise ValueError(f"expected 10 unique RELKIND records, found {len(records)}")
    if len({code for _, code in records}) != len(records):
        raise ValueError("RELKIND codes are not unique")
    return records


def derive_relpersistence_values(source: str) -> tuple[str, ...]:
    values = tuple(
        name.lower()
        for name in re.findall(
            r"^#define\s+RELPERSISTENCE_([A-Z0-9_]+)\s+'[^']+'",
            source,
            re.MULTILINE,
        )
    )
    if values != ("permanent", "unlogged", "temp"):
        raise ValueError(f"unexpected RELPERSISTENCE inventory: {values}")
    return values


def derive_object_types(source: str) -> tuple[str, ...]:
    match = re.search(
        r"typedef\s+enum\s+ObjectType\s*\{(.*?)\}\s*ObjectType\s*;",
        source,
        re.DOTALL,
    )
    if not match:
        raise ValueError("ObjectType enum was not found")
    values = tuple(
        name.lower() for name in re.findall(r"\bOBJECT_([A-Z0-9_]+)\b", match.group(1))
    )
    if len(values) != 52 or len(set(values)) != len(values):
        raise ValueError(f"expected 52 unique ObjectType members, found {len(values)}")
    return values


def _dat_records(source: str) -> tuple[str, ...]:
    return tuple(re.findall(r"\{(.*?)\}", source, re.DOTALL))


def derive_pg_type_inventory(source: str) -> PgTypeInventory:
    concrete: list[str] = []
    arrays: list[str] = []
    pseudo: list[str] = []
    for record in _dat_records(source):
        name_match = re.search(r"typname\s*=>\s*'([^']+)'", record)
        if not name_match:
            continue
        name = name_match.group(1)
        type_match = re.search(r"typtype\s*=>\s*'([^']+)'", record)
        typtype = type_match.group(1) if type_match else "b"
        if typtype == "p":
            pseudo.append(name)
            continue
        concrete.append(name)
        if re.search(r"array_type_oid\s*=>\s*'[^']+'", record):
            arrays.append(name)
    inventory = PgTypeInventory(tuple(concrete), tuple(arrays), tuple(pseudo))
    if len(inventory.concrete) != 85:
        raise ValueError(
            f"expected 85 explicit non-pseudo pg_type records, found {len(inventory.concrete)}"
        )
    if len(inventory.array_elements) != 79:
        raise ValueError(
            f"expected 79 non-pseudo automatic-array element types, found {len(inventory.array_elements)}"
        )
    if len(inventory.pseudo) != 26:
        raise ValueError(
            f"expected 26 explicit pseudo-types, found {len(inventory.pseudo)}"
        )
    return inventory


def derive_builtin_table_access_methods(source: str) -> tuple[str, ...]:
    values: list[str] = []
    for record in _dat_records(source):
        name = re.search(r"amname\s*=>\s*'([^']+)'", record)
        amtype = re.search(r"amtype\s*=>\s*'([^']+)'", record)
        if name and amtype and amtype.group(1) == "t":
            values.append(name.group(1))
    if tuple(values) != ("heap",):
        raise ValueError(f"unexpected built-in table access methods: {values}")
    return tuple(values)


class SourceBundle:
    def __init__(self, *, archive: Path | None = None, source_root: Path | None = None):
        if (archive is None) == (source_root is None):
            raise ValueError("provide exactly one of archive or source_root")
        self.archive = archive
        self.source_root = source_root

    def archive_sha256(self) -> str | None:
        if self.archive is None:
            return None
        return _sha256(self.archive.read_bytes())

    def read(self, relative_path: str) -> bytes:
        if self.source_root is not None:
            return (self.source_root / relative_path).read_bytes()
        assert self.archive is not None
        with tarfile.open(self.archive, "r:*") as handle:
            matches = [
                member
                for member in handle.getmembers()
                if member.isfile() and member.name.endswith("/" + relative_path)
            ]
            if len(matches) != 1:
                raise ValueError(
                    f"expected one archive member ending /{relative_path}, found {len(matches)}"
                )
            extracted = handle.extractfile(matches[0])
            if extracted is None:
                raise ValueError(f"cannot read archive member {matches[0].name}")
            return extracted.read()


def _load_type_catalog(path: Path) -> Mapping[str, object]:
    match = YAML_BLOCK.search(path.read_text(encoding="utf-8"))
    if not match:
        raise ValueError(f"missing YAML structured_config in {path}")
    document = yaml.load(match.group(1), Loader=UniqueKeySafeLoader)
    return document["structured_config"]


def _expect_equal(result: AuditResult, location: str, actual, expected) -> None:
    if actual != expected:
        result.errors.append(f"{location} does not match official PG18.4 source")


def _expect_snapshot(result: AuditResult, location: str, document: Mapping[str, object], values) -> None:
    _expect_equal(result, f"{location}.count", document.get("count"), len(values))
    _expect_equal(
        result,
        f"{location}.inventory_sha256",
        document.get("inventory_sha256"),
        inventory_values_sha256(values),
    )


def audit_repository(root: Path, sources: SourceBundle) -> AuditResult:
    result = AuditResult()
    coverage = yaml.load(
        (root / COVERAGE_INVENTORY).read_text(encoding="utf-8"),
        Loader=UniqueKeySafeLoader,
    )
    types = _load_type_catalog(root / TYPE_CATALOG)
    provenance = coverage["source_provenance"]

    archive_sha = sources.archive_sha256()
    if archive_sha is not None:
        _expect_equal(
            result,
            "source_provenance.source_archive_sha256",
            provenance["source_archive_sha256"],
            archive_sha,
        )

    source_data: dict[str, bytes] = {}
    for key, record in provenance["members"].items():
        data = sources.read(record["path"])
        source_data[key] = data
        _expect_equal(result, f"source_provenance.members.{key}.sha256", record["sha256"], _sha256(data))

    pg_class = source_data["pg_class_h"].decode("utf-8")
    parsenodes = source_data["parsenodes_h"].decode("utf-8")
    pg_type = source_data["pg_type_dat"].decode("utf-8")
    pg_am = source_data["pg_am_dat"].decode("utf-8")

    relkinds = derive_relkind_records(pg_class)
    _expect_equal(
        result,
        "relation_kinds.all_pg18_relkinds",
        tuple(coverage["relation_kinds"]["all_pg18_relkinds"]),
        tuple(name for name, _ in relkinds),
    )
    _expect_snapshot(
        result,
        "relation_kinds",
        coverage["relation_kinds"],
        coverage["relation_kinds"]["all_pg18_relkinds"],
    )
    _expect_equal(
        result,
        "relation_kinds.codes",
        dict(coverage["relation_kinds"]["codes"]),
        dict(relkinds),
    )
    _expect_equal(
        result,
        "relation_dimensions.relpersistence.values",
        tuple(coverage["relation_dimensions"]["relpersistence"]["values"]),
        derive_relpersistence_values(pg_class),
    )
    _expect_equal(
        result,
        "sql_object_types.all_sql_object_types",
        tuple(coverage["sql_object_types"]["all_sql_object_types"]),
        derive_object_types(parsenodes),
    )
    _expect_snapshot(
        result,
        "sql_object_types",
        coverage["sql_object_types"],
        coverage["sql_object_types"]["all_sql_object_types"],
    )
    if coverage["object_kinds"].get("canonical") is not False:
        result.errors.append("legacy object_kinds selector must be explicitly noncanonical")
    _expect_equal(
        result,
        "legacy object selector alias",
        tuple(coverage["object_kinds"]["all_object_kinds"]),
        tuple(coverage["test_target_contexts"]["all_legacy_test_target_contexts"]),
    )
    if coverage["table_kinds"].get("canonical") is not False:
        result.errors.append("legacy table_kinds selector must be explicitly noncanonical")
    if coverage["relation_kinds"].get("legacy_selector_status") != "deprecated_matrix_selector":
        result.errors.append("legacy all_relation_kinds selector must be explicitly deprecated")
    _expect_equal(
        result,
        "legacy relation selector alias",
        tuple(coverage["relation_kinds"]["all_relation_kinds"]),
        tuple(coverage["legacy_relation_test_shapes"]["values"]),
    )
    _expect_equal(
        result,
        "legacy table selector alias",
        tuple(coverage["table_kinds"]["all_table_kinds"]),
        tuple(coverage["legacy_table_test_shapes"]["values"]),
    )
    _expect_equal(
        result,
        "relation_dimensions.builtin_table_access_methods.values",
        tuple(coverage["relation_dimensions"]["builtin_table_access_methods"]["values"]),
        derive_builtin_table_access_methods(pg_am),
    )
    for dimension, expected_values in EXPECTED_TABLE_DIMENSIONS.items():
        document = coverage["relation_dimensions"][dimension]
        _expect_equal(
            result,
            f"relation_dimensions.{dimension}.values",
            tuple(document["values"]),
            expected_values,
        )
        _expect_snapshot(
            result,
            f"relation_dimensions.{dimension}",
            document,
            document["values"],
        )

    derived_types = derive_pg_type_inventory(pg_type)
    type_source = types["source_audit"]["catalog_sources"]["pg_type_dat"]
    _expect_equal(result, "type source path", type_source["path"], provenance["members"]["pg_type_dat"]["path"])
    _expect_equal(result, "type source sha256", type_source["sha256"], _sha256(source_data["pg_type_dat"]))
    _expect_equal(
        result,
        "concrete_builtin_types.values",
        tuple(types["concrete_builtin_types"]["values"]),
        derived_types.concrete,
    )
    _expect_equal(
        result,
        "auto_array_types.element_types",
        tuple(types["auto_array_types"]["element_types"]),
        derived_types.array_elements,
    )
    _expect_equal(
        result,
        "pseudo_types.values",
        tuple(types["pseudo_types"]["values"]),
        derived_types.pseudo,
    )
    for key, expected_count in (
        ("concrete_builtin_types", 85),
        ("auto_array_types", 79),
        ("pseudo_types", 26),
    ):
        _expect_equal(result, f"{key}.count", types[key]["count"], expected_count)
        values_key = "element_types" if key == "auto_array_types" else "values"
        _expect_equal(
            result,
            f"{key}.inventory_sha256",
            types[key]["inventory_sha256"],
            inventory_values_sha256(types[key][values_key]),
        )

    profile_set = types["type_sets"]["canonical_executable_column_profiles"]
    if profile_set.get("selector") != "structured_config.types":
        result.errors.append("canonical executable type profiles must select structured_config.types")
    if profile_set.get("completeness_scope") != "core_executable_profiles":
        result.errors.append("canonical executable type profiles must declare their finite completeness scope")
    _expect_equal(result, "canonical profile inventory_count", profile_set.get("inventory_count"), len(types["types"]))
    _expect_equal(
        result,
        "canonical profile inventory_sha256",
        profile_set.get("inventory_sha256"),
        inventory_values_sha256(types["types"].keys()),
    )
    if types["type_sets"]["all_pg18_column_types"].get("canonical") is not False:
        result.errors.append("legacy all_pg18_column_types name must be explicitly noncanonical")

    aliases = types["declaration_aliases"]
    _expect_equal(
        result,
        "declaration_aliases.mappings",
        dict(aliases["mappings"]),
        EXPECTED_DECLARATION_ALIASES,
    )
    _expect_snapshot(
        result,
        "declaration_aliases",
        aliases,
        tuple(aliases["mappings"]),
    )

    typmod_profiles = types["typmod_profiles"]
    flattened_typmods: list[str] = []
    expected_failures: list[str] = []
    _expect_equal(
        result,
        "typmod_profiles families",
        tuple(
            family
            for family, profile in typmod_profiles.items()
            if isinstance(profile, Mapping)
        ),
        tuple(EXPECTED_TYPMOD_PROFILES),
    )
    for family, expected_profile in EXPECTED_TYPMOD_PROFILES.items():
        actual_profile = typmod_profiles[family]
        for outcome in ("success", "failure"):
            actual_values = tuple(actual_profile.get(outcome, ()))
            _expect_equal(
                result,
                f"typmod_profiles.{family}.{outcome}",
                actual_values,
                expected_profile[outcome],
            )
            flattened_typmods.extend(actual_values)
            if outcome == "failure":
                expected_failures.extend(actual_values)
    typmod_inventory = types["typmod_declarations"]
    _expect_equal(
        result,
        "typmod_declarations.values",
        tuple(typmod_inventory["values"]),
        tuple(flattened_typmods),
    )
    _expect_equal(
        result,
        "typmod_declarations.expected_failure_values",
        tuple(typmod_inventory["expected_failure_values"]),
        tuple(expected_failures),
    )
    _expect_snapshot(
        result,
        "typmod_declarations",
        typmod_inventory,
        typmod_inventory["values"],
    )

    archetypes = types["user_defined_archetypes"]
    _expect_equal(
        result,
        "user_defined_archetypes.values",
        tuple(archetypes["values"]),
        EXPECTED_USER_DEFINED_ARCHETYPES,
    )
    _expect_snapshot(
        result,
        "user_defined_archetypes",
        archetypes,
        archetypes["values"],
    )

    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--source-archive", type=Path)
    group.add_argument("--source-root", type=Path)
    args = parser.parse_args(argv)
    try:
        result = audit_repository(
            args.root.resolve(),
            SourceBundle(archive=args.source_archive, source_root=args.source_root),
        )
    except (KeyError, OSError, TypeError, ValueError, yaml.YAMLError, tarfile.TarError) as exc:
        print(f"ERROR: {exc}")
        return 1
    for error in result.errors:
        print(f"ERROR: {error}")
    if result.passed:
        print("PASS PG18.4 source-derived inventories: objects=52 relkinds=10 builtins=85 arrays=79 pseudo=26 table_ams=1")
        return 0
    print(f"FAIL PG18.4 source-derived inventories: errors={len(result.errors)}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
