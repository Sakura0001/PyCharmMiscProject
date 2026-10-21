from __future__ import annotations

import gzip
import hashlib
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Iterator

TYPE_PERFORMANCE_BATCH_ID = "2026-10-21-type-upgrade-performance-v1"
TYPE_PERFORMANCE_BATCH_KIND = "type_upgrade_performance"
TYPE_PERFORMANCE_CASE_PREFIX = "TUCPF"
TYPE_PERFORMANCE_DATABASE = "qa_type_upgrade_performance"
TYPE_PERFORMANCE_PROFILE = "performance"

SCENARIOS = (
    "source_baseline",
    "all_copy",
    "all_inplace",
    "all_instant",
    "mixed_inplace_first",
    "mixed_instant_first",
    "reference",
)

UPGRADE_COLUMNS: tuple[tuple[str, str, str], ...] = (
    ("i_tiny", "TINYINT", "SMALLINT"),
    ("i_tiny_unsigned", "TINYINT UNSIGNED", "SMALLINT UNSIGNED"),
    ("i_small", "SMALLINT", "MEDIUMINT"),
    ("i_small_unsigned", "SMALLINT UNSIGNED", "MEDIUMINT UNSIGNED"),
    ("i_medium", "MEDIUMINT", "INT"),
    ("i_medium_unsigned", "MEDIUMINT UNSIGNED", "INT UNSIGNED"),
    ("i_int", "INT", "BIGINT"),
    ("i_int_unsigned", "INT UNSIGNED", "BIGINT UNSIGNED"),
    ("i_bigint", "BIGINT", "BIGINT"),
    ("i_bigint_unsigned", "BIGINT UNSIGNED", "BIGINT UNSIGNED"),
    ("dec_10_2", "DECIMAL(10,2)", "DECIMAL(20,2)"),
    ("dec_18_6", "DECIMAL(18,6)", "DECIMAL(38,6)"),
    ("dec_38_18", "DECIMAL(38,18)", "DECIMAL(65,18)"),
    ("bit_8", "BIT(8)", "BIT(16)"),
    ("bit_32", "BIT(32)", "BIT(64)"),
    ("char_16", "CHAR(16)", "CHAR(255)"),
    ("char_255", "CHAR(255)", "VARCHAR(256)"),
    ("varchar_16", "VARCHAR(16)", "VARCHAR(255)"),
    ("varchar_255", "VARCHAR(255)", "VARCHAR(256)"),
    ("varchar_256", "VARCHAR(256)", "VARCHAR(1024)"),
    ("binary_16", "BINARY(16)", "BINARY(255)"),
    ("binary_255", "BINARY(255)", "VARBINARY(256)"),
    ("varbinary_16", "VARBINARY(16)", "VARBINARY(255)"),
    ("varbinary_255", "VARBINARY(255)", "VARBINARY(256)"),
    ("varbinary_256", "VARBINARY(256)", "VARBINARY(1024)"),
    ("tinytext", "TINYTEXT", "TEXT"),
    ("text", "TEXT", "MEDIUMTEXT"),
    ("mediumtext", "MEDIUMTEXT", "LONGTEXT"),
    ("tinyblob", "TINYBLOB", "BLOB"),
    ("blob", "BLOB", "MEDIUMBLOB"),
    ("mediumblob", "MEDIUMBLOB", "LONGBLOB"),
)

NOISE_COLUMNS: tuple[tuple[str, str], ...] = (
    ("noise_float", "FLOAT"),
    ("noise_double", "DOUBLE"),
    ("noise_date", "DATE"),
    ("noise_json", "JSON"),
)


@dataclass(frozen=True)
class TypePerformanceScenario:
    case_no: int
    scenario: str

    @property
    def case_id(self) -> str:
        return f"{TYPE_PERFORMANCE_CASE_PREFIX}-{self.case_no:06d}"

    @property
    def batch_id(self) -> str:
        return TYPE_PERFORMANCE_BATCH_ID

    @property
    def batch_kind(self) -> str:
        return TYPE_PERFORMANCE_BATCH_KIND

    def to_json(self) -> dict[str, Any]:
        payload = asdict(self)
        payload.update(
            {
                "batch_id": self.batch_id,
                "batch_kind": self.batch_kind,
                "case_id": self.case_id,
                "database": TYPE_PERFORMANCE_DATABASE,
                "profile": TYPE_PERFORMANCE_PROFILE,
            }
        )
        return payload


def iter_type_performance_scenarios() -> Iterator[TypePerformanceScenario]:
    for case_no, scenario in enumerate(SCENARIOS, start=1):
        yield TypePerformanceScenario(case_no, scenario)


def type_performance_scenarios() -> tuple[TypePerformanceScenario, ...]:
    return tuple(iter_type_performance_scenarios())


def _column_definitions(target: bool) -> list[str]:
    definitions = ["id BIGINT NOT NULL"]
    for name, source_type, target_type in UPGRADE_COLUMNS:
        definitions.append(f"`{name}` {target_type if target else source_type} NULL")
    for name, noise_type in NOISE_COLUMNS:
        definitions.append(f"`{name}` {noise_type} NULL")
    definitions.append("PRIMARY KEY(id)")
    definitions.append("KEY idx_i_int(`i_int`)")
    definitions.append("KEY idx_varchar_255(`varchar_255`)")
    definitions.append("KEY idx_noise_date(`noise_date`)")
    return definitions


def build_source_table_sql(table: str = "tab_tucpf_source") -> str:
    return (
        f"CREATE TABLE `{table}` (\n  "
        + ",\n  ".join(_column_definitions(target=False))
        + "\n) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci"
    )


def build_reference_table_sql(table: str = "tab_tucpf_reference") -> str:
    return (
        f"CREATE TABLE `{table}` (\n  "
        + ",\n  ".join(_column_definitions(target=True))
        + "\n) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci"
    )


def _length_expression(row_number: str, short: int, medium: int, large: int) -> str:
    return (
        f"CASE WHEN MOD({row_number}, 1000) = 0 THEN {large} "
        f"WHEN MOD({row_number}, 1000) < 50 THEN {medium} "
        f"ELSE {short} END"
    )


def build_numbers_table_sql(table: str = "tab_tucpf_numbers") -> str:
    return f"CREATE TABLE `{table}` (n BIGINT NOT NULL PRIMARY KEY)"


def build_insert_numbers_sql(table: str = "tab_tucpf_numbers", rows: int = 100_000) -> str:
    return (
        f"INSERT INTO `{table}` (n) "
        "WITH RECURSIVE seq(n) AS "
        f"(SELECT 1 UNION ALL SELECT n+1 FROM seq WHERE n < {rows}) "
        "SELECT n FROM seq"
    )


def build_generate_source_sql(
    source_table: str = "tab_tucpf_source",
    numbers_table: str = "tab_tucpf_numbers",
    multiplier_table: str = "tab_tucpf_multiplier",
    rows: int = 12_000_000,
) -> str:
    n = "((m.n - 1) * 100000 + d.n)"
    values: list[str] = [n]

    # Integer boundary and normal values.
    integer_sources = {
        "i_tiny": 127,
        "i_tiny_unsigned": 255,
        "i_small": 32767,
        "i_small_unsigned": 65535,
        "i_medium": 8388607,
        "i_medium_unsigned": 16777215,
        "i_int": 2147483647,
        "i_int_unsigned": 4294967295,
        "i_bigint": 9223372036854775807,
        "i_bigint_unsigned": 18446744073709551615,
    }
    for column, maximum in integer_sources.items():
        values.append(
            f"CASE WHEN MOD({n},10000)=0 THEN {maximum} ELSE MOD({n},{maximum}) END"
        )

    # Decimal boundary and normal values.
    decimal_sources = {
        "dec_10_2": ("99999999.99", "100000"),
        "dec_18_6": ("999999999999.999999", "1000000000"),
        "dec_38_18": ("99999999999999999999.999999999999999999", "100000000000000000"),
    }
    for column, (maximum, modulus) in decimal_sources.items():
        values.append(
            f"CASE WHEN MOD({n},10000)=0 THEN CAST({maximum} AS DECIMAL(65,18)) "
            f"ELSE CAST(MOD({n},{modulus}) / 100 AS DECIMAL(65,18)) END"
        )

    # BIT normal and boundary values.
    values.append(f"CASE WHEN MOD({n},10000)=0 THEN 255 ELSE MOD({n},256) END")
    values.append(f"CASE WHEN MOD({n},10000)=0 THEN 4294967295 ELSE MOD({n},4294967296) END")

    # Character columns.
    character_sources = {
        "char_16": 16,
        "char_255": 255,
        "varchar_16": 16,
        "varchar_255": 255,
        "varchar_256": 256,
    }
    for column, maximum in character_sources.items():
        length = _length_expression(n, min(maximum, 128), min(maximum, 2048), maximum)
        values.append(f"REPEAT(CHAR(97 + MOD({n},26)), {length})")

    # Binary columns.
    binary_sources = {
        "binary_16": 16,
        "binary_255": 255,
        "varbinary_16": 16,
        "varbinary_255": 255,
        "varbinary_256": 256,
    }
    for column, maximum in binary_sources.items():
        length = _length_expression(n, min(maximum, 128), min(maximum, 2048), maximum)
        values.append(f"REPEAT(UNHEX('01'), {length})")

    # TEXT/BLOB distributions.
    text_sources = {
        "tinytext": (128, 255, 255),
        "text": (128, 2048, 32768),
        "mediumtext": (512, 8192, 32768),
    }
    for column, (short, medium, large) in text_sources.items():
        length = _length_expression(n, short, medium, large)
        values.append(f"REPEAT(CHAR(97 + MOD({n},26)), {length})")

    blob_sources = {
        "tinyblob": (128, 255, 255),
        "blob": (128, 2048, 32768),
        "mediumblob": (512, 8192, 32768),
    }
    for column, (short, medium, large) in blob_sources.items():
        length = _length_expression(n, short, medium, large)
        values.append(f"REPEAT(UNHEX('01'), {length})")

    # Noise columns.
    values.append(f"CAST(MOD({n},1000000) / 100 AS DOUBLE)")
    values.append(f"CAST(MOD({n},1000000000) / 1000 AS DOUBLE)")
    values.append(f"DATE_ADD('2000-01-01', INTERVAL MOD({n},3650) DAY)")
    values.append(f"CAST(CONCAT('{{\"n\":', {n}, '}}') AS JSON)")

    return (
        f"INSERT INTO `{source_table}` "
        f"SELECT {', '.join(values)} "
        f"FROM `{numbers_table}` d CROSS JOIN `{multiplier_table}` m "
        f"LIMIT {rows}"
    )


def build_copy_source_sql(
    source_table: str = "tab_tucpf_source",
    target_table: str = "tab_tucpf_reference",
) -> str:
    columns = ["id", *[column[0] for column in UPGRADE_COLUMNS], *[column[0] for column in NOISE_COLUMNS]]
    quoted = ", ".join(f"`{column}`" for column in columns)
    return f"INSERT INTO `{target_table}` ({quoted}) SELECT {quoted} FROM `{source_table}`"


def build_full_scan_query(table: str) -> str:
    aggregates: list[str] = ["COUNT(*)"]
    for name, source_type, target_type in UPGRADE_COLUMNS:
        if name.startswith("i_"):
            aggregates.append(f"SUM(`{name}`)")
        elif name.startswith("dec_"):
            aggregates.append(f"SUM(`{name}`)")
        elif name.startswith("bit_"):
            aggregates.append(f"SUM(CAST(`{name}` AS UNSIGNED))")
        elif name.startswith(("char_", "varchar_", "tinytext", "text", "mediumtext")):
            aggregates.append(f"SUM(LENGTH(`{name}`))")
        else:
            aggregates.append(f"SUM(LENGTH(`{name}`))")
    aggregates.append("SUM(LENGTH(noise_json))")
    return f"SELECT {', '.join(aggregates)} FROM `{table}`"


def _alter_columns(algorithm: str, columns: tuple[tuple[str, str, str], ...]) -> str:
    modifications = ", ".join(f"MODIFY `{name}` {target_type} NULL" for name, _, target_type in columns)
    if algorithm == "copy":
        return f"ALTER TABLE tab_tucpf_candidate {modifications}, ALGORITHM=COPY"
    if algorithm == "inplace":
        return f"ALTER TABLE tab_tucpf_candidate {modifications}, ALGORITHM=INPLACE, LOCK=NONE"
    if algorithm == "instant":
        return f"ALTER TABLE tab_tucpf_candidate {modifications}, ALGORITHM=INSTANT"
    raise AssertionError(algorithm)


def build_ddl_sql(scenario: str) -> tuple[str, ...]:
    if scenario == "all_copy":
        return (_alter_columns("copy", UPGRADE_COLUMNS),)
    if scenario == "all_inplace":
        return (_alter_columns("inplace", UPGRADE_COLUMNS),)
    if scenario == "all_instant":
        return (_alter_columns("instant", UPGRADE_COLUMNS),)
    midpoint = len(UPGRADE_COLUMNS) // 2
    first = UPGRADE_COLUMNS[:midpoint]
    second = UPGRADE_COLUMNS[midpoint:]
    if scenario == "mixed_inplace_first":
        return (_alter_columns("inplace", first), _alter_columns("instant", second))
    if scenario == "mixed_instant_first":
        return (_alter_columns("instant", first), _alter_columns("inplace", second))
    return ()


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _gzip_bytes(payload: str) -> bytes:
    return gzip.compress(payload.encode("utf-8"), compresslevel=9, mtime=0)


def write_type_performance_artifacts(output: Path) -> dict[str, Any]:
    output.mkdir(parents=True, exist_ok=True)
    scenarios = type_performance_scenarios()

    cases_payload = "".join(
        json.dumps(scenario.to_json(), ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n"
        for scenario in scenarios
    )
    (output / "cases.jsonl.gz").write_bytes(_gzip_bytes(cases_payload))

    coverage_lines = [
        "family\tsource_type\ttarget_type\tcolumn",
        *[
            f"{'integer' if column.startswith('i_') else 'decimal' if column.startswith('dec_') else 'bit' if column.startswith('bit_') else 'character' if column.startswith(('char_', 'varchar_')) else 'binary' if column.startswith(('binary_', 'varbinary_')) else 'text' if 'text' in column else 'blob'}\t{source}\t{target}\t{column}"
            for column, source, target in UPGRADE_COLUMNS
        ],
    ]
    (output / "coverage.tsv").write_text("\n".join(coverage_lines) + "\n", encoding="utf-8")

    hashes = {
        "cases.jsonl.gz": _sha256(output / "cases.jsonl.gz"),
        "coverage.tsv": _sha256(output / "coverage.tsv"),
    }
    manifest = {
        "artifacts_sha256": hashes,
        "batch_id": TYPE_PERFORMANCE_BATCH_ID,
        "batch_kind": TYPE_PERFORMANCE_BATCH_KIND,
        "case_count": len(scenarios),
        "case_id_prefix": TYPE_PERFORMANCE_CASE_PREFIX,
        "database": TYPE_PERFORMANCE_DATABASE,
        "materialization": "virtual_runner",
        "profile": TYPE_PERFORMANCE_PROFILE,
        "profile_counts": {TYPE_PERFORMANCE_PROFILE: len(scenarios)},
        "scenario_count": len(scenarios),
        "upgrade_column_count": len(UPGRADE_COLUMNS),
        "noise_column_count": len(NOISE_COLUMNS),
    }
    (output / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    readme = f"""# Type-upgrade performance batch

This batch measures large-table type-upgrade performance and post-upgrade
query/DML performance.

- **BATCH_ID:** `{TYPE_PERFORMANCE_BATCH_ID}`
- **CASE_PREFIX:** `{TYPE_PERFORMANCE_CASE_PREFIX}`
- **Database:** `{TYPE_PERFORMANCE_DATABASE}`
- **Scenarios:** {len(scenarios)}
- **Upgrade columns:** {len(UPGRADE_COLUMNS)}
- **Noise columns:** {len(NOISE_COLUMNS)}

## Execution

```bash
PYTHONPATH=src python3 tools/run_type_upgrade_performance.py \\
  --all \\
  --results generated/type_upgrade_performance_v1/performance_results.jsonl \\
  --summary generated/type_upgrade_performance_v1/performance_summary.json \\
  --external \\
  --host <authorized-host> \\
  --port 3306 \\
  --user <authorized-user> \\
  --password-env TYPE_PERFORMANCE_MYSQL_PASSWORD
```
"""
    (output / "README.md").write_text(readme, encoding="utf-8")
    return manifest
