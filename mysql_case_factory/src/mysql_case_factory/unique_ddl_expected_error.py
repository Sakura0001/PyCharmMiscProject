from __future__ import annotations

import gzip
import hashlib
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Iterator

UNIQUE_DDL_ERROR_BATCH_ID = "2026-10-20-unique-ddl-expected-error-v1"
UNIQUE_DDL_ERROR_BATCH_KIND = "unique_ddl_expected_error"
UNIQUE_DDL_ERROR_CASE_PREFIX = "TUCUD"
UNIQUE_DDL_ERROR_DATABASE = "qa_unique_ddl_expected_error"
UNIQUE_DDL_ERROR_PROFILE = "inplace"

DDL_FORMS = (
    "create_unique_index",
    "add_unique_index",
    "add_unique_key",
    "add_constraint_unique",
)
INDEX_SHAPES = (
    "integer",
    "string",
    "prefix",
    "case_insensitive",
    "generated",
    "composite",
)
DML_TYPES = (
    "insert",
    "insert_ignore",
    "insert_on_duplicate",
    "insert_select",
    "multi_row_insert",
    "update",
    "update_join",
    "delete_insert",
)
SCENARIO_COUNT = len(DDL_FORMS) * len(INDEX_SHAPES) * len(DML_TYPES)


@dataclass(frozen=True)
class UniqueDDLErrorScenario:
    case_no: int
    ddl_form: str
    shape: str
    dml_type: str

    @property
    def case_id(self) -> str:
        return f"{UNIQUE_DDL_ERROR_CASE_PREFIX}-{self.case_no:06d}"

    @property
    def table(self) -> str:
        return f"tab_{UNIQUE_DDL_ERROR_CASE_PREFIX.lower()}_{self.shape}_target"

    @property
    def index_name(self) -> str:
        return "uq_tucud_v"

    @property
    def batch_id(self) -> str:
        return UNIQUE_DDL_ERROR_BATCH_ID

    @property
    def batch_kind(self) -> str:
        return UNIQUE_DDL_ERROR_BATCH_KIND

    def to_json(self) -> dict[str, Any]:
        payload = asdict(self)
        payload.update(
            {
                "batch_id": self.batch_id,
                "batch_kind": self.batch_kind,
                "case_id": self.case_id,
                "database": UNIQUE_DDL_ERROR_DATABASE,
                "profile": UNIQUE_DDL_ERROR_PROFILE,
                "table": self.table,
                "index_name": self.index_name,
                "expected_error_codes": [1062, 1859],
            }
        )
        return payload


def iter_unique_ddl_error_scenarios() -> Iterator[UniqueDDLErrorScenario]:
    case_no = 0
    for ddl_form in DDL_FORMS:
        for shape in INDEX_SHAPES:
            for dml_type in DML_TYPES:
                case_no += 1
                yield UniqueDDLErrorScenario(case_no, ddl_form, shape, dml_type)
    if case_no != SCENARIO_COUNT:
        raise AssertionError(f"unexpected scenario count: {case_no}")


def smoke_unique_ddl_error_scenarios() -> list[UniqueDDLErrorScenario]:
    scenarios = list(iter_unique_ddl_error_scenarios())
    return [
        next(
            scenario
            for scenario in scenarios
            if scenario.shape == shape
            and scenario.ddl_form == "add_unique_index"
            and scenario.dml_type == "insert"
        )
        for shape in INDEX_SHAPES
    ]


def _base36(value: int) -> str:
    chars = "0123456789abcdefghijklmnopqrstuvwxyz"
    if value == 0:
        return "0"
    result = ""
    while value:
        value, remainder = divmod(value, 36)
        result = chars[remainder] + result
    return result


def index_expression(shape: str) -> str:
    if shape == "integer":
        return "v"
    if shape == "string":
        return "v"
    if shape == "prefix":
        return "v(5)"
    if shape == "case_insensitive":
        return "v"
    if shape == "generated":
        return "lower_v"
    if shape == "composite":
        return "a,b"
    raise AssertionError(shape)


def create_table_sql(shape: str, table: str) -> str:
    if shape == "integer":
        columns = "id INT NOT NULL, v INT NOT NULL"
    elif shape in {"string", "prefix"}:
        columns = "id INT NOT NULL, v VARCHAR(100) NOT NULL COLLATE utf8mb4_bin"
    elif shape == "case_insensitive":
        columns = "id INT NOT NULL, v VARCHAR(100) NOT NULL COLLATE utf8mb4_0900_ai_ci"
    elif shape == "generated":
        columns = (
            "id INT NOT NULL, v VARCHAR(100) NOT NULL COLLATE utf8mb4_bin, "
            "lower_v VARCHAR(100) GENERATED ALWAYS AS (LOWER(v)) STORED"
        )
    elif shape == "composite":
        columns = "id INT NOT NULL, a INT NOT NULL, b INT NOT NULL"
    else:
        raise AssertionError(shape)
    return (
        f"CREATE TABLE `{table}` ({columns}, PRIMARY KEY(id)) "
        "ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci"
    )


def seed_row(shape: str, row_no: int) -> tuple[Any, ...]:
    if shape == "integer":
        return (row_no, row_no)
    if shape in {"string", "case_insensitive", "generated"}:
        return (row_no, f"ABC{row_no:08d}")
    if shape == "prefix":
        return (row_no, f"{_base36(row_no):0>5}X{row_no:08d}")
    if shape == "composite":
        return (row_no, row_no, row_no)
    raise AssertionError(shape)


def duplicate_value(shape: str) -> Any:
    if shape == "integer":
        return 1
    if shape == "string":
        return "ABC00000001"
    if shape == "prefix":
        return "00001Y99999999"
    if shape == "case_insensitive":
        return "abc00000001"
    if shape == "generated":
        return "abc00000001"
    if shape == "composite":
        return (1, 1)
    raise AssertionError(shape)


def unique_tail_value(shape: str, row_no: int) -> Any:
    if shape == "integer":
        return row_no
    if shape in {"string", "case_insensitive", "generated"}:
        return f"ABC{row_no:08d}"
    if shape == "prefix":
        return f"{_base36(row_no):0>5}X{row_no:08d}"
    if shape == "composite":
        return (row_no, row_no)
    raise AssertionError(shape)


def _quote(value: Any) -> str:
    if isinstance(value, str):
        return "'" + value.replace("\\", "\\\\").replace("'", "''") + "'"
    return str(value)


def _insert_values(shape: str, row_no: int, value: Any) -> str:
    if shape == "composite":
        return f"({row_no},{value[0]},{value[1]})"
    return f"({row_no},{_quote(value)})"


def render_ddl_sql(scenario: UniqueDDLErrorScenario) -> str:
    table = scenario.table
    expression = index_expression(scenario.shape)
    form = scenario.ddl_form
    if form == "create_unique_index":
        return f"CREATE UNIQUE INDEX `{scenario.index_name}` ON `{table}` ({expression}) ALGORITHM=INPLACE"
    if form == "add_unique_index":
        return f"ALTER TABLE `{table}` ADD UNIQUE INDEX `{scenario.index_name}` ({expression}), ALGORITHM=INPLACE, LOCK=NONE"
    if form == "add_unique_key":
        return f"ALTER TABLE `{table}` ADD UNIQUE KEY `{scenario.index_name}` ({expression}), ALGORITHM=INPLACE, LOCK=NONE"
    if form == "add_constraint_unique":
        return f"ALTER TABLE `{table}` ADD CONSTRAINT `{scenario.index_name}` UNIQUE ({expression}), ALGORITHM=INPLACE, LOCK=NONE"
    raise AssertionError(form)


def render_dml_sql(scenario: UniqueDDLErrorScenario, rows: int) -> str:
    shape = scenario.shape
    table = scenario.table
    duplicate = duplicate_value(shape)
    row = rows
    new_id = rows + 1
    second_id = rows + 2
    second_value = unique_tail_value(shape, second_id)
    dml_type = scenario.dml_type

    if dml_type == "insert":
        return f"INSERT INTO `{table}` (id, {'a,b' if shape == 'composite' else 'v'}) VALUES {_insert_values(shape, new_id, duplicate)}"
    if dml_type == "insert_ignore":
        return f"INSERT IGNORE INTO `{table}` (id, {'a,b' if shape == 'composite' else 'v'}) VALUES {_insert_values(shape, new_id, duplicate)}"
    if dml_type == "insert_on_duplicate":
        if shape == "composite":
            return (
                f"INSERT INTO `{table}` (id,a,b) VALUES {_insert_values(shape, new_id, duplicate)} "
                "ON DUPLICATE KEY UPDATE a=1,b=1"
            )
        return (
            f"INSERT INTO `{table}` (id,v) VALUES {_insert_values(shape, new_id, duplicate)} "
            f"ON DUPLICATE KEY UPDATE v={_quote(duplicate)}"
        )
    if dml_type == "insert_select":
        if shape == "composite":
            return f"INSERT INTO `{table}` (id,a,b) SELECT {new_id},a,b FROM `{table}` WHERE id=1"
        return f"INSERT INTO `{table}` (id,v) SELECT {new_id},v FROM `{table}` WHERE id=1"
    if dml_type == "multi_row_insert":
        return (
            f"INSERT INTO `{table}` (id, {'a,b' if shape == 'composite' else 'v'}) VALUES "
            f"{_insert_values(shape, new_id, duplicate)},{_insert_values(shape, second_id, second_value)}"
        )
    if dml_type == "update":
        if shape == "composite":
            return f"UPDATE `{table}` SET a=1,b=1 WHERE id={row}"
        return f"UPDATE `{table}` SET v={_quote(duplicate)} WHERE id={row}"
    if dml_type == "update_join":
        if shape == "composite":
            return (
                f"UPDATE `{table}` JOIN (SELECT 1 AS a,1 AS b) d ON `{table}`.id={row} "
                f"SET `{table}`.a=d.a,`{table}`.b=d.b"
            )
        return (
            f"UPDATE `{table}` JOIN (SELECT {_quote(duplicate)} AS duplicate_value) d "
            f"ON `{table}`.id={row} SET `{table}`.v=d.duplicate_value"
        )
    if dml_type == "delete_insert":
        insert = (
            f"INSERT INTO `{table}` (id,a,b) VALUES {_insert_values(shape, new_id, duplicate)}"
            if shape == "composite"
            else f"INSERT INTO `{table}` (id,v) VALUES {_insert_values(shape, new_id, duplicate)}"
        )
        return f"DELETE FROM `{table}` WHERE id={row}; {insert}"
    raise AssertionError(dml_type)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _gzip_bytes(payload: str) -> bytes:
    return gzip.compress(payload.encode("utf-8"), compresslevel=9, mtime=0)


def write_unique_ddl_error_artifacts(output: Path, *, rows: int = 200_000) -> dict[str, Any]:
    output.mkdir(parents=True, exist_ok=True)
    scenarios = list(iter_unique_ddl_error_scenarios())
    smoke = smoke_unique_ddl_error_scenarios()

    def scenario_payload(scenario: UniqueDDLErrorScenario) -> dict[str, Any]:
        payload = scenario.to_json()
        payload["ddl_sql"] = render_ddl_sql(scenario)
        payload["dml_sql"] = render_dml_sql(scenario, rows)
        return payload

    cases_payload = "".join(
        json.dumps(scenario_payload(scenario), ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n"
        for scenario in scenarios
    )
    smoke_payload = "".join(
        json.dumps(scenario_payload(scenario), ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n"
        for scenario in smoke
    )
    (output / "cases.jsonl.gz").write_bytes(_gzip_bytes(cases_payload))
    (output / "smoke_cases.jsonl.gz").write_bytes(_gzip_bytes(smoke_payload))

    coverage_lines = [
        "ddl_form\tshape\tdml_type\tscenario_count",
        *[
            f"{ddl_form}\t{shape}\t{dml_type}\t1"
            for ddl_form in DDL_FORMS
            for shape in INDEX_SHAPES
            for dml_type in DML_TYPES
        ],
    ]
    (output / "coverage.tsv").write_text("\n".join(coverage_lines) + "\n", encoding="utf-8")

    artifact_hashes = {
        name: _sha256(output / name)
        for name in ("cases.jsonl.gz", "smoke_cases.jsonl.gz", "coverage.tsv")
    }
    manifest = {
        "artifacts_sha256": artifact_hashes,
        "batch_id": UNIQUE_DDL_ERROR_BATCH_ID,
        "batch_kind": UNIQUE_DDL_ERROR_BATCH_KIND,
        "case_count": len(scenarios),
        "case_id_prefix": UNIQUE_DDL_ERROR_CASE_PREFIX,
        "database": UNIQUE_DDL_ERROR_DATABASE,
        "ddl_form_count": len(DDL_FORMS),
        "dml_type_count": len(DML_TYPES),
        "expected_error_codes": [1062, 1859],
        "index_shape_count": len(INDEX_SHAPES),
        "materialization": "virtual_runner",
        "profile": UNIQUE_DDL_ERROR_PROFILE,
        "profile_counts": {UNIQUE_DDL_ERROR_PROFILE: len(scenarios)},
        "rows_per_shape": rows,
        "smoke_case_count": len(smoke),
    }
    (output / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    readme = f"""# Unique-DDL expected-error batch

This batch verifies that online unique secondary-index DDL fails with MySQL
1062 when concurrent DML introduces a duplicate after the DDL has started.

- **BATCH_ID:** `{UNIQUE_DDL_ERROR_BATCH_ID}`
- **BATCH_KIND:** `{UNIQUE_DDL_ERROR_BATCH_KIND}`
- **CASE_PREFIX:** `{UNIQUE_DDL_ERROR_CASE_PREFIX}`
- **Database:** `{UNIQUE_DDL_ERROR_DATABASE}`
- **Cases:** {len(scenarios)}
- **DDL forms:** {len(DDL_FORMS)}
- **Index shapes:** {len(INDEX_SHAPES)}
- **DML types:** {len(DML_TYPES)}
- **Rows per shape:** {rows}
- **Smoke cases:** {len(smoke)}

## Execution

```bash
PYTHONPATH=src python3 tools/run_unique_ddl_expected_error.py \\
  --all \\
  --results generated/unique_ddl_expected_error_v1/inplace_results.jsonl \\
  --summary generated/unique_ddl_expected_error_v1/inplace_summary.json \\
  --external \\
  --host <authorized-host> \\
  --port 3306 \\
  --user <authorized-user> \\
  --password-env UNIQUE_DDL_MYSQL_PASSWORD
```

Use `--smoke` for the six shape representatives. Increase `--rows` if any case
reports `NO_OVERLAP`.
"""
    (output / "README.md").write_text(readme, encoding="utf-8")
    return manifest
