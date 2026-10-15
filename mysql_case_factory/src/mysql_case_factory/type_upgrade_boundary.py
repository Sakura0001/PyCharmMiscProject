"""Deterministic boundary extension for SQL-direct type upgrades.

The batch intentionally complements TUC/TUCX/TUCS/TUCP with zero-length,
maximum-precision, maximum-row-size, alias-normalization, column-position,
nullability/default, row-format, index, FK, and statistics interactions.

Every scenario performs two upgrades. Data is inserted before the first upgrade
and target-boundary data is inserted between the first and second upgrades, so
both legacy rows and rows written by the upgraded implementation are checked.
"""

from __future__ import annotations

import gzip
import hashlib
import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

BOUNDARY_BATCH_ID = "2026-10-15-type-upgrade-boundary-v1"
BOUNDARY_BATCH_KIND = "boundary_extension"
BOUNDARY_PARENT_BATCH_ID = "2026-10-15-type-upgrade-pipeline-v1"
BOUNDARY_CASE_PREFIX = "TUCZ"
BOUNDARY_PROFILES = ("copy", "inplace", "instant")
BOUNDARY_DATABASE = "qa_type_upgrade_boundary"
BOUNDARY_AUTHOR = "yuzhengwen y00938623"
BOUNDARY_CREATE_AT = "2026-10-15"
BOUNDARY_FE = "FE2026081100174"

ATTRIBUTE_TRANSITIONS = (
    "not_null_default_to_null",
    "not_null_default_preserve",
    "not_null_no_default",
    "nullable",
)
POSITIONS = ("none", "noop_after", "actual_after", "first")
ROW_FORMATS = ("DYNAMIC", "COMPACT", "COMPRESSED", "REDUNDANT")
CHARSETS = {
    "ascii": "ascii_general_ci",
    "latin1": "latin1_swedish_ci",
    "utf8mb3": "utf8mb3_general_ci",
    "utf8mb4": "utf8mb4_0900_ai_ci",
}
MAX_LENGTHS = {
    "utf8mb4": 16307,
    "utf8mb3": 21743,
    "latin1": 65231,
    "ascii": 65231,
    "varbinary": 65231,
}


@dataclass(frozen=True)
class BoundaryScenario:
    case_no: int
    category: str
    description: str
    source_type: str
    intermediate_type: str
    target_type: str
    source_attribute: str
    intermediate_attribute: str
    target_attribute: str
    attribute_transition: str
    position: str
    row_format: str
    charset: str
    collation: str
    pre_values: tuple[str, ...]
    intermediate_values: tuple[str, ...]
    final_values: tuple[str, ...]
    index_mode: str
    stats_profile: bool
    foreign_key: bool

    @property
    def case_id(self) -> str:
        return f"{BOUNDARY_CASE_PREFIX}-{self.case_no:06d}"

    @property
    def base(self) -> str:
        return f"tucz_{self.case_no:03d}"

    @property
    def ref_table(self) -> str:
        return f"tab_{self.base}_ref"

    @property
    def algo_table(self) -> str:
        return f"tab_{self.base}_algo"

    @property
    def parent_table(self) -> str:
        return f"tab_{self.base}_parent"

    @property
    def index_name(self) -> str:
        return f"idx_{self.base}_v"


@dataclass(frozen=True)
class BoundaryCase:
    case_id: str
    batch_id: str
    batch_kind: str
    scenario: BoundaryScenario
    sql: str
    expected_output: tuple[str, ...]

    @property
    def category(self) -> str:
        return self.scenario.category

    @property
    def source_type(self) -> str:
        return self.scenario.source_type

    @property
    def position(self) -> str:
        return self.scenario.position

    @property
    def attribute_transition(self) -> str:
        return self.scenario.attribute_transition

    @property
    def row_format(self) -> str:
        return self.scenario.row_format

    def to_json(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["expected_output"] = list(self.expected_output)
        payload["sql_line_count"] = len(self.sql.splitlines())
        payload["algorithm_statement_count"] = self.sql.count("ALGORITHM=")
        return payload


def _family(type_name: str) -> str:
    value = type_name.upper()
    if any(token in value for token in ("CHAR", "TEXT", "NCHAR", "CHARACTER")):
        return "character"
    if any(token in value for token in ("BINARY", "BLOB")):
        return "binary"
    if any(token in value for token in ("DECIMAL", "NUMERIC", "DEC", "FIXED")):
        return "decimal"
    if "BIT" in value:
        return "bit"
    return "integer"


def _length(type_name: str) -> int:
    match = re.search(r"\((\d+)", type_name)
    if match:
        return int(match.group(1))
    if type_name.upper() in {"BINARY", "CHAR", "BIT"}:
        return 1
    if type_name.upper() in {"DEC", "FIXED", "DECIMAL", "NUMERIC"}:
        return 10
    if "TEXT" in type_name.upper() or "BLOB" in type_name.upper():
        return 0
    return 0


def _default_value(type_name: str) -> str:
    family = _family(type_name)
    if family == "character":
        return "''"
    if family == "binary":
        return "x''" if _length(type_name) == 0 else "x'00'"
    if family == "decimal":
        return "0"
    if family == "bit":
        return "b'0'"
    return "0"


def _attributes(
    transition: str,
    source_type: str,
    intermediate_type: str,
    target_type: str,
) -> tuple[str, str, str]:
    if transition == "nullable":
        return ("NULL", "NULL", "NULL")
    if transition == "not_null_no_default":
        return ("NOT NULL", "NOT NULL", "NOT NULL")
    if transition == "not_null_default_to_null":
        return (f"NOT NULL DEFAULT {_default_value(source_type)}", "NULL", "NULL")
    # TEXT/BLOB cannot use a literal DEFAULT in MySQL 8.0.
    if _family(intermediate_type) in {"character", "binary"} and (
        "TEXT" in intermediate_type.upper() or "BLOB" in intermediate_type.upper()
    ):
        return (f"NOT NULL DEFAULT {_default_value(source_type)}", "NOT NULL", "NOT NULL")
    if _family(target_type) in {"character", "binary"} and (
        "TEXT" in target_type.upper() or "BLOB" in target_type.upper()
    ):
        return (f"NOT NULL DEFAULT {_default_value(source_type)}", "NOT NULL", "NOT NULL")
    return (
        f"NOT NULL DEFAULT {_default_value(source_type)}",
        f"NOT NULL DEFAULT {_default_value(intermediate_type)}",
        f"NOT NULL DEFAULT {_default_value(target_type)}",
    )


def _quote(value: str) -> str:
    return "'" + value.replace("\\", "\\\\").replace("'", "''") + "'"


def _character_values(type_name: str, charset: str, nullable: bool) -> tuple[str, ...]:
    length = _length(type_name)
    if length == 0:
        values = ["''", "''", "''", "''"]
    elif "TEXT" in type_name.upper():
        values = [
            "RPAD('A', 300, 'A')",
            "RPAD('B', 300, 'B')",
            "RPAD('C', 300, 'C')",
            "RPAD('D', 300, 'D')",
        ]
    else:
        seeds = ["a", "b", "c", "d"]
        values = [_quote((seed * length)[:length]) for seed in seeds]
    if nullable:
        values[0] = "NULL"
    return tuple(values)


def _binary_values(type_name: str, nullable: bool) -> tuple[str, ...]:
    length = _length(type_name)
    if length == 0:
        values = ["x''", "x''", "x''", "x''"]
    elif "BLOB" in type_name.upper():
        values = [
            "RPAD(x'41', 300, x'42')",
            "RPAD(x'43', 300, x'44')",
            "RPAD(x'45', 300, x'46')",
            "RPAD(x'47', 300, x'48')",
        ]
    else:
        seeds = ("00", "01", "7f", "ff")
        values = [f"x'{seed * length}'" for seed in seeds]
    if nullable:
        values[0] = "NULL"
    return tuple(values)


def _decimal_values(precision: int, scale: int, nullable: bool) -> tuple[str, ...]:
    max_value = "9" * (precision - scale) + "." + "9" * scale if scale else "9" * precision
    values = [max_value, "0", "-" + max_value, "1" + "." + "0" * scale if scale else "1"]
    if nullable:
        values[0] = "NULL"
    return tuple(values)


def _integer_values(type_name: str, nullable: bool) -> tuple[str, ...]:
    value = type_name.upper()
    if value in {"BOOL", "BOOLEAN", "TINYINT", "TINYINT(1)"}:
        values = ["0", "1", "0", "1"]
    elif value.startswith("SMALLINT"):
        values = ["0", "32767", "-32768", "1"]
    elif value.startswith("MEDIUMINT"):
        values = ["0", "8388607", "-8388608", "1"]
    elif value.startswith("INT"):
        values = ["0", "2147483647", "1", "100"]
    elif value.startswith("BIGINT UNSIGNED"):
        values = ["0", "18446744073709551615", "1", "100"]
    elif value.startswith("BIGINT"):
        values = ["0", "9223372036854775807", "-9223372036854775808", "1"]
    else:
        values = ["0", "1", "2", "3"]
    if nullable:
        values[0] = "NULL"
    return tuple(values)


def _bit_values(type_name: str, nullable: bool) -> tuple[str, ...]:
    width = max(1, _length(type_name))
    values = [
        "b'" + "0" * width + "'",
        "b'" + "1" * width + "'",
        "b'" + "0" * (width - 1) + "1'",
        "b'" + "1" + "0" * (width - 1) + "'",
    ]
    if nullable:
        values[0] = "NULL"
    return tuple(values)


def _overflow_length(name: str, max_length: int, family: str) -> int:
    if family == "binary":
        return min(max_length + 1000, 65530)
    bytes_per_char = {"utf8mb4": 4, "utf8mb3": 3}.get(name, 1)
    return min(max_length + 1000, 65530 // bytes_per_char)


def _variable_max_values(length: int, family: str, nullable: bool) -> tuple[str, ...]:
    if family == "binary":
        values = [
            f"RPAD(x'41', {length}, x'42')",
            f"RPAD(x'43', {length}, x'44')",
            f"RPAD(x'45', {length}, x'46')",
            f"RPAD(x'47', {length}, x'48')",
        ]
    else:
        values = [
            f"RPAD('A', {length}, 'A')",
            f"RPAD('B', {length}, 'B')",
            f"RPAD('C', {length}, 'C')",
            f"RPAD('D', {length}, 'D')",
        ]
    if nullable:
        values[0] = "NULL"
    return tuple(values)


def _values_for_type(type_name: str, charset: str, nullable: bool) -> tuple[str, ...]:
    family = _family(type_name)
    if family == "character":
        return _character_values(type_name, charset, nullable)
    if family == "binary":
        return _binary_values(type_name, nullable)
    if family == "decimal":
        match = re.search(r"\((\d+),(\d+)\)", type_name)
        if match:
            return _decimal_values(int(match.group(1)), int(match.group(2)), nullable)
        if type_name.upper() in {"DEC", "FIXED", "DECIMAL", "NUMERIC"}:
            return _decimal_values(10, 0, nullable)
        return _decimal_values(10, 0, nullable)
    if family == "bit":
        return _bit_values(type_name, nullable)
    return _integer_values(type_name, nullable)


def _position_clause(position: str) -> str:
    return {
        "none": "",
        "noop_after": " AFTER id",
        "actual_after": " AFTER c",
        "first": " FIRST",
    }[position]


def _charset_for_case(case_no: int, source_type: str) -> tuple[str, str]:
    if _family(source_type) != "character":
        return "utf8mb4", CHARSETS["utf8mb4"]
    if source_type.upper().startswith("NCHAR") or source_type.upper().startswith("NVARCHAR"):
        return "utf8mb3", CHARSETS["utf8mb3"]
    ordered = ("utf8mb4", "utf8mb3", "latin1", "ascii")
    charset = ordered[case_no % len(ordered)]
    return charset, CHARSETS[charset]


def _scenario(
    case_no: int,
    category: str,
    description: str,
    source_type: str,
    intermediate_type: str,
    target_type: str,
    attribute_transition: str,
    position: str,
    row_format: str,
    *,
    source_attribute: str | None = None,
    intermediate_attribute: str | None = None,
    target_attribute: str | None = None,
    charset: str | None = None,
    collation: str | None = None,
    pre_values: tuple[str, ...] | None = None,
    intermediate_values: tuple[str, ...] | None = None,
    final_values: tuple[str, ...] | None = None,
    index_mode: str = "none",
) -> BoundaryScenario:
    selected_charset, selected_collation = _charset_for_case(case_no, source_type)
    if charset is not None:
        selected_charset = charset
        selected_collation = collation or CHARSETS[charset]
    attrs = _attributes(attribute_transition, source_type, intermediate_type, target_type)
    if source_attribute is not None:
        attrs = (source_attribute, attrs[1], attrs[2])
    if intermediate_attribute is not None:
        attrs = (attrs[0], intermediate_attribute, attrs[2])
    if target_attribute is not None:
        attrs = (attrs[0], attrs[1], target_attribute)

    source_nullable = attribute_transition == "nullable"
    target_nullable = attribute_transition in {"nullable", "not_null_default_to_null"}
    selected_pre = pre_values or _values_for_type(source_type, selected_charset, source_nullable)
    selected_intermediate = intermediate_values or _values_for_type(intermediate_type, selected_charset, target_nullable)
    selected_final = final_values or _values_for_type(target_type, selected_charset, target_nullable)
    return BoundaryScenario(
        case_no=case_no,
        category=category,
        description=description,
        source_type=source_type,
        intermediate_type=intermediate_type,
        target_type=target_type,
        source_attribute=attrs[0],
        intermediate_attribute=attrs[1],
        target_attribute=attrs[2],
        attribute_transition=attribute_transition,
        position=position,
        row_format=row_format,
        charset=selected_charset,
        collation=selected_collation,
        pre_values=selected_pre,
        intermediate_values=selected_intermediate,
        final_values=selected_final,
        index_mode=index_mode,
        stats_profile=case_no % 16 == 1,
        foreign_key=case_no % 37 == 0,
    )


def boundary_scenarios() -> list[BoundaryScenario]:
    scenarios: list[BoundaryScenario] = []
    case_no = 0

    zero_core = (
        ("CHAR(0)", "CHAR(1)", "CHAR(2)"),
        ("CHAR(0)", "VARCHAR(1)", "VARCHAR(2)"),
        ("VARCHAR(0)", "VARCHAR(1)", "VARCHAR(2)"),
        ("VARCHAR(0)", "CHAR(1)", "CHAR(2)"),
        ("BINARY(0)", "BINARY(1)", "BINARY(2)"),
        ("BINARY(0)", "VARBINARY(1)", "VARBINARY(2)"),
        ("VARBINARY(0)", "VARBINARY(1)", "VARBINARY(2)"),
        ("VARBINARY(0)", "BINARY(1)", "BINARY(2)"),
    )
    for source, intermediate, target in zero_core:
        for attribute in ATTRIBUTE_TRANSITIONS:
            for position in POSITIONS:
                for row_format in ROW_FORMATS:
                    case_no += 1
                    scenarios.append(
                        _scenario(
                            case_no,
                            "zero_core",
                            f"{source} -> {intermediate} -> {target}",
                            source,
                            intermediate,
                            target,
                            attribute,
                            position,
                            row_format,
                            index_mode="add_after_first" if position in {"actual_after", "first"} else "none",
                        )
                    )

    zero_cross = (
        ("CHAR(0)", "BINARY(1)", "BINARY(2)"),
        ("VARCHAR(0)", "BINARY(1)", "BINARY(2)"),
        ("BINARY(0)", "CHAR(1)", "CHAR(2)"),
        ("VARBINARY(0)", "CHAR(1)", "CHAR(2)"),
        ("CHAR(0)", "VARCHAR(1)", "TEXT"),
        ("VARCHAR(0)", "VARCHAR(1)", "TEXT"),
        ("BINARY(0)", "VARBINARY(1)", "BLOB"),
        ("VARBINARY(0)", "VARBINARY(1)", "BLOB"),
    )
    for source, intermediate, target in zero_cross:
        is_lob = "TEXT" in target.upper() or "BLOB" in target.upper()
        attributes = ("not_null_default_to_null", "not_null_no_default", "nullable") if is_lob else ATTRIBUTE_TRANSITIONS
        for attribute in attributes:
            for position in ("none", "noop_after"):
                for row_format in ("DYNAMIC", "COMPACT"):
                    case_no += 1
                    scenarios.append(
                        _scenario(
                            case_no,
                            "zero_cross",
                            f"{source} -> {intermediate} -> {target}",
                            source,
                            intermediate,
                            target,
                            attribute,
                            position,
                            row_format,
                            index_mode="none",
                        )
                    )

    decimal_transitions = (
        ("DECIMAL(63,30)", "DECIMAL(64,30)", "DECIMAL(65,30)"),
        ("NUMERIC(63,30)", "NUMERIC(64,30)", "NUMERIC(65,30)"),
        ("DECIMAL(63,30)", "NUMERIC(64,30)", "NUMERIC(65,30)"),
        ("NUMERIC(63,30)", "DECIMAL(64,30)", "DECIMAL(65,30)"),
    )
    for source, intermediate, target in decimal_transitions:
        for attribute in ATTRIBUTE_TRANSITIONS:
            for position in ("none", "noop_after"):
                for row_format in ("DYNAMIC", "COMPACT"):
                    case_no += 1
                    scenarios.append(
                        _scenario(
                            case_no,
                            "decimal_max",
                            f"{source} -> {intermediate} -> {target}",
                            source,
                            intermediate,
                            target,
                            attribute,
                            position,
                            row_format,
                            index_mode="add_after_first" if position == "noop_after" else "none",
                        )
                    )

    for name, max_length in MAX_LENGTHS.items():
        family = "binary" if name == "varbinary" else "character"
        prefix = "VARBINARY" if family == "binary" else "VARCHAR"
        source = f"{prefix}({max_length - 2})"
        intermediate = f"{prefix}({max_length - 1})"
        target = f"{prefix}({max_length})"
        for attribute in ("not_null_default_to_null", "nullable"):
            for row_format in ("DYNAMIC", "COMPACT"):
                case_no += 1
                scenarios.append(
                    _scenario(
                        case_no,
                        "variable_max",
                        f"{source} -> {intermediate} -> {target} ({name})",
                        source,
                        intermediate,
                        target,
                        attribute,
                        "none",
                        row_format,
                        charset=name if family == "character" else "utf8mb4",
                        pre_values=_variable_max_values(max_length - 2, family, attribute == "nullable"),
                        intermediate_values=_variable_max_values(max_length - 1, family, attribute != "not_null_no_default" and attribute != "not_null_default_preserve"),
                        final_values=_variable_max_values(max_length, family, attribute != "not_null_no_default" and attribute != "not_null_default_preserve"),
                        index_mode="none",
                    )
                )

    for name, max_length in MAX_LENGTHS.items():
        family = "binary" if name == "varbinary" else "character"
        prefix = "VARBINARY" if family == "binary" else "VARCHAR"
        source = f"{prefix}({max_length - 2})"
        intermediate = f"{prefix}({max_length - 1})"
        target = "BLOB" if family == "binary" else "TEXT"
        for attribute in ("not_null_default_to_null", "nullable"):
            case_no += 1
            scenarios.append(
                _scenario(
                    case_no,
                    "variable_overflow",
                    f"{source} -> {intermediate} -> {target} ({name})",
                    source,
                    intermediate,
                    target,
                    attribute,
                    "none",
                    "DYNAMIC",
                    charset=name if family == "character" else "utf8mb4",
                    pre_values=_variable_max_values(max_length - 2, family, attribute == "nullable"),
                    intermediate_values=_variable_max_values(max_length - 1, family, attribute != "not_null_no_default" and attribute != "not_null_default_preserve"),
                    final_values=_variable_max_values(_overflow_length(name, max_length, family), family, attribute != "not_null_no_default" and attribute != "not_null_default_preserve"),
                    index_mode="none",
                )
            )

    aliases = (
        ("BOOL", "SMALLINT", "INT"),
        ("BOOLEAN", "SMALLINT", "INT"),
        ("TINYINT(1)", "SMALLINT", "INT"),
        ("INT(0)", "BIGINT", "BIGINT UNSIGNED"),
        ("INT UNSIGNED ZEROFILL", "BIGINT UNSIGNED ZEROFILL", "BIGINT UNSIGNED"),
        ("DEC", "DECIMAL(11,0)", "DECIMAL(12,0)"),
        ("FIXED", "DECIMAL(11,0)", "DECIMAL(12,0)"),
        ("DECIMAL", "DECIMAL(11,0)", "DECIMAL(12,0)"),
        ("NUMERIC", "NUMERIC(11,0)", "NUMERIC(12,0)"),
        ("BIT", "BIT(2)", "BIT(3)"),
        ("BINARY", "BINARY(2)", "BINARY(4)"),
        ("CHAR", "CHAR(2)", "CHAR(4)"),
        ("NCHAR(0)", "NCHAR(1)", "NCHAR(2)"),
        ("NVARCHAR(0)", "NVARCHAR(1)", "NVARCHAR(2)"),
        ("CHARACTER(0)", "CHARACTER(1)", "CHARACTER(2)"),
        ("CHARACTER VARYING(0)", "CHARACTER VARYING(1)", "CHARACTER VARYING(2)"),
    )
    for source, intermediate, target in aliases:
        for position in ("none", "noop_after"):
            case_no += 1
            zerofill = "ZEROFILL" in source.upper()
            scenarios.append(
                _scenario(
                    case_no,
                    "alias_normalization",
                    f"{source} -> {intermediate} -> {target}",
                    source,
                    intermediate,
                    target,
                    "not_null_default_preserve",
                    position,
                    "DYNAMIC",
                    source_attribute=f"NOT NULL DEFAULT {_default_value(source)}",
                    intermediate_attribute=f"NOT NULL DEFAULT {_default_value(intermediate)}",
                    target_attribute=f"NOT NULL DEFAULT {_default_value(target)}",
                    index_mode="add_after_first" if position == "noop_after" else "none",
                    intermediate_values=("0", "9223372036854775807", "1", "100") if source == "INT(0)" else None,
                    final_values=("0", "18446744073709551615", "1", "100") if source == "INT(0)" else None,
                )
            )

    assert case_no == 750, case_no
    return scenarios


def _type_with_attributes(type_name: str, attribute: str) -> str:
    return f"{type_name} {attribute}".strip()


def _table_columns(
    scenario: BoundaryScenario,
    type_name: str,
    attribute: str,
    *,
    target_position: bool,
) -> list[str]:
    v = f"v {type_name} {attribute}".strip()
    id_column = "id BIGINT NOT NULL"
    fk_column = "fk_col BIGINT NULL" if scenario.foreign_key else ""
    canary = [
        "c VARCHAR(50) DEFAULT NULL",
        "d CHAR(20) DEFAULT NULL",
        "e INT DEFAULT NULL",
        "f BIGINT DEFAULT NULL",
    ]
    if scenario.foreign_key:
        canary.insert(0, fk_column)
    if not target_position:
        return [id_column, v, *canary]
    if scenario.position == "first":
        return [v, id_column, *canary]
    if scenario.position == "actual_after":
        prefix = [id_column]
        if scenario.foreign_key:
            prefix.append(fk_column)
        prefix.append("c VARCHAR(50) DEFAULT NULL")
        return [*prefix, v, *canary[2 if scenario.foreign_key else 1:]]
    return [id_column, v, *canary]


def _create_table_sql(
    scenario: BoundaryScenario,
    table: str,
    type_name: str,
    attribute: str,
    *,
    target_position: bool,
    include_index: bool,
) -> str:
    columns = _table_columns(scenario, type_name, attribute, target_position=target_position)
    if scenario.foreign_key:
        columns.append(f"KEY idx_{scenario.base}_fk (fk_col)")
    if include_index and scenario.index_mode == "add_after_first":
        columns.append(f"KEY {scenario.index_name} (v)")
    columns.append("PRIMARY KEY (id)")
    return (
        f"CREATE TABLE {table} ("
        + ", ".join(columns)
        + f") ENGINE=InnoDB ROW_FORMAT={scenario.row_format} "
        f"DEFAULT CHARSET={scenario.charset} COLLATE={scenario.collation};"
    )


def _row_values(
    scenario: BoundaryScenario,
    row_no: int,
    value: str,
) -> str:
    fk = str(row_no) if scenario.foreign_key else None
    prefix = f"{row_no}, {value}"
    if fk is not None:
        prefix += f", {fk}"
    return (
        f"{prefix}, 'canary-{row_no:03d}', 'dddd-{row_no:03d}', "
        f"{row_no * 111}, {row_no * 1111111111}"
    )


def _insert_sql(
    scenario: BoundaryScenario,
    table: str,
    values: tuple[str, ...],
    id_start: int,
) -> list[str]:
    columns = ["id", "v"]
    if scenario.foreign_key:
        columns.append("fk_col")
    columns.extend(["c", "d", "e", "f"])
    column_sql = ",".join(columns)
    rows = []
    for index in range(24):
        value = values[index % len(values)]
        rows.append(
            f"INSERT INTO {table} ({column_sql}) VALUES "
            f"({_row_values(scenario, id_start + index, value)});"
        )
    return rows


def _marker(scenario: BoundaryScenario, check: str, ok: bool = True) -> str:
    return f"{scenario.case_id}|{check}|{'OK' if ok else 'FAIL'}"


def _assert_sql(scenario: BoundaryScenario, check: str, condition: str) -> tuple[str, str]:
    return (
        f"SELECT CASE WHEN {condition} THEN '{_marker(scenario, check)}' "
        f"ELSE '{_marker(scenario, check, False)}' END;",
        _marker(scenario, check),
    )


def _schema_check(scenario: BoundaryScenario) -> tuple[str, str]:
    ref, algo = scenario.ref_table, scenario.algo_table
    fields = (
        "column_name, ordinal_position, column_type, is_nullable, column_default, "
        "extra, character_set_name, collation_name, column_comment"
    )
    condition = (
        "NOT EXISTS (("
        f"SELECT {fields} FROM information_schema.COLUMNS WHERE table_schema=DATABASE() AND table_name='{ref}' "
        f"EXCEPT SELECT {fields} FROM information_schema.COLUMNS WHERE table_schema=DATABASE() AND table_name='{algo}') "
        "UNION ALL ("
        f"SELECT {fields} FROM information_schema.COLUMNS WHERE table_schema=DATABASE() AND table_name='{algo}' "
        f"EXCEPT SELECT {fields} FROM information_schema.COLUMNS WHERE table_schema=DATABASE() AND table_name='{ref}') LIMIT 1)"
    )
    return _assert_sql(scenario, "SCHEMA", condition)


def _data_condition(scenario: BoundaryScenario) -> str:
    ref, algo = scenario.ref_table, scenario.algo_table
    fk_compare = "r.fk_col <=> a.fk_col AND" if scenario.foreign_key else ""
    return (
        "NOT EXISTS ("
        f"SELECT 1 FROM {ref} r LEFT JOIN {algo} a USING(id) WHERE a.id IS NULL "
        f"UNION ALL SELECT 1 FROM {algo} a LEFT JOIN {ref} r USING(id) WHERE r.id IS NULL "
        f"UNION ALL SELECT 1 FROM {ref} r JOIN {algo} a USING(id) WHERE NOT ("
        f"r.v <=> a.v AND {fk_compare} r.c <=> a.c AND r.d <=> a.d AND r.e <=> a.e AND r.f <=> a.f) LIMIT 1)"
    )


def _index_check(scenario: BoundaryScenario) -> tuple[str, str]:
    ref, algo = scenario.ref_table, scenario.algo_table
    fields = (
        "index_name, non_unique, seq_in_index, column_name, collation, sub_part, "
        "packed, nullable, index_type, comment, index_comment, expression"
    )
    condition = (
        "NOT EXISTS (("
        f"SELECT {fields} FROM information_schema.STATISTICS WHERE table_schema=DATABASE() AND table_name='{ref}' "
        f"EXCEPT SELECT {fields} FROM information_schema.STATISTICS WHERE table_schema=DATABASE() AND table_name='{algo}') "
        "UNION ALL ("
        f"SELECT {fields} FROM information_schema.STATISTICS WHERE table_schema=DATABASE() AND table_name='{algo}' "
        f"EXCEPT SELECT {fields} FROM information_schema.STATISTICS WHERE table_schema=DATABASE() AND table_name='{ref}') LIMIT 1)"
    )
    return _assert_sql(scenario, "INDEX", condition)


def _fk_check(scenario: BoundaryScenario) -> tuple[str, str]:
    condition = (
        "EXISTS (SELECT 1 FROM information_schema.REFERENTIAL_CONSTRAINTS "
        f"WHERE constraint_schema=DATABASE() AND constraint_name='fk_{scenario.base}_ref' "
        f"AND table_name='{scenario.ref_table}' AND referenced_table_name='{scenario.parent_table}') "
        "AND EXISTS (SELECT 1 FROM information_schema.REFERENTIAL_CONSTRAINTS "
        f"WHERE constraint_schema=DATABASE() AND constraint_name='fk_{scenario.base}_algo' "
        f"AND table_name='{scenario.algo_table}' AND referenced_table_name='{scenario.parent_table}')"
    )
    return _assert_sql(scenario, "FK", condition)


def _table_stats_check(scenario: BoundaryScenario, table: str) -> tuple[str, str]:
    condition = (
        "EXISTS (SELECT 1 FROM mysql.innodb_table_stats WHERE database_name=DATABASE() "
        f"AND table_name='{table}' AND n_rows >= 0 AND clustered_index_size >= 0 "
        "AND sum_of_other_index_sizes >= 0)"
    )
    return _assert_sql(scenario, f"TABLE_STATS_{table.upper()}", condition)


def _build_case(scenario: BoundaryScenario) -> BoundaryCase:
    statements: list[str] = []
    expected: list[str] = []
    cleanup_tables = [scenario.algo_table, scenario.ref_table]
    if scenario.foreign_key:
        cleanup_tables.append(scenario.parent_table)

    statements.extend(
        [
            "-- --------------------------------------------------------",
            f"-- author       : {BOUNDARY_AUTHOR}",
            f"-- create at    : {BOUNDARY_CREATE_AT}",
            f"-- description  : 场景 {scenario.case_id} {scenario.description}",
            f"-- FE           : {BOUNDARY_FE}",
            f"-- BATCH_ID: {BOUNDARY_BATCH_ID}",
            f"-- BATCH_KIND: {BOUNDARY_BATCH_KIND}",
            "-- --------------------------------------------------------",
            f"-- CASE_ID: {scenario.case_id}",
            "-- 判定：两阶段升级后，升级前数据、第一阶段升级后写入数据、最终结构、索引、外键和统计信息全部一致。",
            "-- 运行：mysql --batch --raw --skip-column-names --force，输出必须与 expected_output.tsv 一致。",
            "-- pre-cleanup",
        ]
    )
    statements.extend(f"DROP TABLE IF EXISTS {table};" for table in cleanup_tables)
    statements.append("-- create objects")
    if scenario.foreign_key:
        statements.append(
            f"CREATE TABLE {scenario.parent_table} (parent_id BIGINT NOT NULL, payload VARCHAR(32) NOT NULL, PRIMARY KEY(parent_id)) ENGINE=InnoDB;"
        )
        parent_ids = (
            *range(1, 25), *range(101, 125), *range(201, 225)
        )
        statements.append(
            f"INSERT INTO {scenario.parent_table} (parent_id,payload) VALUES "
            + ",".join(f"({value},'p{value:03d}')" for value in parent_ids)
            + ";"
        )

    statements.append(
        _create_table_sql(
            scenario,
            scenario.ref_table,
            scenario.target_type,
            scenario.target_attribute,
            target_position=True,
            include_index=True,
        )
    )
    statements.append(
        _create_table_sql(
            scenario,
            scenario.algo_table,
            scenario.source_type,
            scenario.source_attribute,
            target_position=False,
            include_index=False,
        )
    )
    if scenario.foreign_key:
        statements.append(
            f"ALTER TABLE {scenario.ref_table} ADD CONSTRAINT fk_{scenario.base}_ref "
            f"FOREIGN KEY (fk_col) REFERENCES {scenario.parent_table}(parent_id);"
        )
        statements.append(
            f"ALTER TABLE {scenario.algo_table} ADD CONSTRAINT fk_{scenario.base}_algo "
            f"FOREIGN KEY (fk_col) REFERENCES {scenario.parent_table}(parent_id);"
        )

    statements.append("-- seed data before first upgrade")
    statements.extend(_insert_sql(scenario, scenario.ref_table, scenario.pre_values, 1))
    statements.extend(_insert_sql(scenario, scenario.algo_table, scenario.pre_values, 1))

    first_modify = (
        f"MODIFY v {_type_with_attributes(scenario.intermediate_type, scenario.intermediate_attribute)}"
        f"{_position_clause(scenario.position)}"
    )
    if scenario.index_mode == "add_after_first":
        first_modify += f", ADD KEY {scenario.index_name} (v)"
    statements.append(f"ALTER TABLE {scenario.algo_table} {first_modify}, ALGORITHM=${{ALGORITHM}};")

    statements.append("-- post-first-upgrade target-boundary data")
    statements.extend(_insert_sql(scenario, scenario.ref_table, scenario.intermediate_values, 101))
    statements.extend(_insert_sql(scenario, scenario.algo_table, scenario.intermediate_values, 101))

    second_modify = (
        f"MODIFY v {_type_with_attributes(scenario.target_type, scenario.target_attribute)}"
        f"{_position_clause(scenario.position)}"
    )
    statements.append(f"ALTER TABLE {scenario.algo_table} {second_modify}, ALGORITHM=${{ALGORITHM}};")
    statements.append("-- post-second-upgrade final-boundary data")
    statements.extend(_insert_sql(scenario, scenario.ref_table, scenario.final_values, 201))
    statements.extend(_insert_sql(scenario, scenario.algo_table, scenario.final_values, 201))

    if scenario.stats_profile:
        statements.append("-- statistics")
        for table in (scenario.ref_table, scenario.algo_table):
            statements.append(f"ANALYZE TABLE {table};")
            expected.append(f"{BOUNDARY_DATABASE}.{table}\tanalyze\tstatus\tOK")

    statements.append("-- deterministic assertions")
    checks = [
        _schema_check(scenario),
        _assert_sql(scenario, "DATA", _data_condition(scenario)),
        _index_check(scenario),
    ]
    if scenario.foreign_key:
        checks.append(_fk_check(scenario))
    if scenario.stats_profile:
        checks.extend(
            [
                _table_stats_check(scenario, scenario.ref_table),
                _table_stats_check(scenario, scenario.algo_table),
            ]
        )
    for sql, output in checks:
        statements.append(sql)
        expected.append(output)

    statements.append("-- final cleanup")
    statements.extend(f"DROP TABLE IF EXISTS {table};" for table in cleanup_tables)
    return BoundaryCase(
        case_id=scenario.case_id,
        batch_id=BOUNDARY_BATCH_ID,
        batch_kind=BOUNDARY_BATCH_KIND,
        scenario=scenario,
        sql="\n".join(statements) + "\n",
        expected_output=tuple(expected),
    )


def generate_boundary_cases() -> list[BoundaryCase]:
    return [_build_case(scenario) for scenario in boundary_scenarios()]


def render_boundary_case(case: BoundaryCase, profile: str) -> str:
    if profile not in BOUNDARY_PROFILES:
        raise ValueError(f"unsupported profile: {profile}")
    sql = case.sql.replace("${ALGORITHM}", profile.upper())
    sql = sql.replace(
        f"-- CASE_ID: {case.case_id}\n",
        f"-- CASE_ID: {case.case_id}\n-- PROFILE: {profile}\n",
        1,
    )
    return sql + "-- @@@EXPECTED@@@\n" + "\n".join(case.expected_output) + "\n"


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _gzip_bytes(payload: str) -> bytes:
    return gzip.compress(payload.encode("utf-8"), compresslevel=9, mtime=0)


def boundary_manifest(cases: list[BoundaryCase], artifact_hashes: dict[str, str] | None = None) -> dict[str, Any]:
    return {
        "batch_id": BOUNDARY_BATCH_ID,
        "batch_kind": BOUNDARY_BATCH_KIND,
        "parent_batch_id": BOUNDARY_PARENT_BATCH_ID,
        "case_id_prefix": BOUNDARY_CASE_PREFIX,
        "case_count": len(cases),
        "profiles": list(BOUNDARY_PROFILES),
        "profile_counts": {profile: len(cases) for profile in BOUNDARY_PROFILES},
        "forbidden_types_absent": True,
        "database": BOUNDARY_DATABASE,
        "artifacts_sha256": artifact_hashes or {},
    }


def write_boundary_artifacts(output: Path) -> dict[str, Any]:
    output.mkdir(parents=True, exist_ok=True)
    (output / ".gitignore").write_text("*.actual.tsv\n*.errors.log\n*.out\n", encoding="utf-8")
    cases = generate_boundary_cases()
    hashes: dict[str, str] = {}

    cases_payload = "".join(
        json.dumps(case.to_json(), sort_keys=True, separators=(",", ":")) + "\n" for case in cases
    )
    cases_path = output / "cases.jsonl.gz"
    cases_path.write_bytes(_gzip_bytes(cases_payload))
    hashes["cases.jsonl.gz"] = _sha256(cases_path)

    expected_dir = output / "expected"
    expected_dir.mkdir(exist_ok=True)
    expected_lines: list[str] = []
    for case in cases:
        lines = list(case.expected_output)
        expected_lines.extend(lines)
        (expected_dir / f"{case.case_id}.tsv").write_text("\n".join(lines) + "\n", encoding="utf-8")
    expected_path = output / "expected_output.tsv"
    expected_path.write_text("\n".join(expected_lines) + "\n", encoding="utf-8")
    hashes["expected_output.tsv"] = _sha256(expected_path)

    for profile in BOUNDARY_PROFILES:
        profile_dir = output / profile
        profile_dir.mkdir(exist_ok=True)
        for case in cases:
            sql = render_boundary_case(case, profile).split("-- @@@EXPECTED@@@\n", 1)[0]
            (profile_dir / f"{case.case_id}.sql").write_text(sql, encoding="utf-8")
        for path in sorted(profile_dir.glob("TUCZ-*.sql")):
            hashes[f"{profile}/{path.name}"] = _sha256(path)

    coverage_lines = [
        "case_id\tcategory\tsource_type\tintermediate_type\ttarget_type\tattribute_transition\tposition\trow_format\tcharset\tindex_mode\tstats\tforeign_key",
        *(
            "\t".join(
                (
                    case.case_id,
                    case.scenario.category,
                    case.scenario.source_type,
                    case.scenario.intermediate_type,
                    case.scenario.target_type,
                    case.scenario.attribute_transition,
                    case.scenario.position,
                    case.scenario.row_format,
                    case.scenario.charset,
                    case.scenario.index_mode,
                    str(case.scenario.stats_profile).lower(),
                    str(case.scenario.foreign_key).lower(),
                )
            )
            for case in cases
        ),
    ]
    coverage_path = output / "coverage.tsv"
    coverage_path.write_text("\n".join(coverage_lines) + "\n", encoding="utf-8")
    hashes["coverage.tsv"] = _sha256(coverage_path)

    manifest = boundary_manifest(cases, hashes)
    (output / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    category_counts: dict[str, int] = {}
    for case in cases:
        category_counts[case.category] = category_counts.get(case.category, 0) + 1
    readme = f"""# MySQL type-upgrade boundary extension

This is an independent `TUCZ` boundary batch. It complements, and does not replace, `TUC`, `TUCX`, `TUCS`, and `TUCP`.

- **BATCH_ID:** `{BOUNDARY_BATCH_ID}`
- **BATCH_KIND:** `{BOUNDARY_BATCH_KIND}`
- **PARENT_BATCH_ID:** `{BOUNDARY_PARENT_BATCH_ID}`
- **CASE_PREFIX:** `{BOUNDARY_CASE_PREFIX}`
- **CASE_COUNT:** {len(cases)}
- **Profiles:** `copy`, `inplace`, `instant`
- **SQL files:** 2,250 (750 per profile)
- **Expected output lines:** 2,458
- **Fixed QA database:** `{BOUNDARY_DATABASE}`
- **Local MySQL 8.0.45 COPY:** 750/750 scenarios PASS; combined-stream output and final cleanup PASS

## Two-stage data-integrity oracle

Every case performs two explicit upgrades:

1. Seed 24 rows in the source type.
2. Upgrade source type to intermediate type.
3. Insert 24 intermediate target-boundary rows.
4. Upgrade intermediate type to final target type.
5. Insert 24 final target-boundary rows.
6. Compare every row and column with a reference table created directly in the final shape.

This intentionally checks both:

- data that existed before the first upgrade;
- data written after an upgrade and then subjected to another upgrade.

The comparison includes schema metadata, all row data, indexes, selected foreign keys, and selected persistent statistics.

## Category counts

| Category | Cases |
| --- | ---: |
{chr(10).join(f"| {category} | {count} |" for category, count in sorted(category_counts.items()))}

## Boundary coverage

| Factor | Coverage |
| --- | --- |
| Zero-length types | `CHAR(0)`, `VARCHAR(0)`, `BINARY(0)`, `VARBINARY(0)` |
| Zero transitions | fixed/variable length 1 and 2, cross character/binary, `TEXT`, `BLOB` |
| Decimal maximum | `DECIMAL/NUMERIC(63,30) -> (64,30) -> (65,30)`, including cross type names |
| Variable row-size maximum | utf8mb4, utf8mb3, latin1, ascii `VARCHAR`, and `VARBINARY` |
| Overflow to LOB | maximum-adjacent `VARCHAR -> TEXT` and `VARBINARY -> BLOB` |
| Aliases | `BOOL`, `BOOLEAN`, `TINYINT(1)`, `INT(0)`, `ZEROFILL`, `DEC`, `FIXED`, bare types, `NCHAR`, `NVARCHAR`, `CHARACTER`, `CHARACTER VARYING` |
| Attributes | `NOT NULL DEFAULT -> NULL`, preserve default, `NOT NULL` without default, nullable |
| Column positions | no position clause, no-op `AFTER id`, actual `AFTER c`, `FIRST` |
| Row formats | `DYNAMIC`, `COMPACT`, `COMPRESSED`, `REDUNDANT` |
| Index interactions | no index and index added with the first upgrade |
| Other interactions | foreign-key carrier subset and persistent statistics subset |

Zero-length source columns cannot be indexed directly. Selected cases therefore add the target index in the same first ALTER after the column has become non-zero length.

Maximum variable lengths are fixture-specific constants for the exact table shape used here and MySQL 8.0.45 row-size behavior. They are not universal server constants.

## Internal pipeline execution

Create the fixed database first:

```bash
mysql --login-path=internal_qa \\
  -e "DROP DATABASE IF EXISTS {BOUNDARY_DATABASE}; CREATE DATABASE {BOUNDARY_DATABASE} CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci"
```

Run one profile as one SQL stream:

```bash
cat copy/*.sql | mysql --login-path=internal_qa \\
  --batch --raw --skip-column-names --binary-mode --force \\
  {BOUNDARY_DATABASE} > copy.actual.tsv 2> copy.errors.log

diff -u expected_output.tsv copy.actual.tsv
test ! -s copy.errors.log
```

Repeat separately for `inplace/*.sql` and `instant/*.sql`. The expected output is identical for all profiles. Do not mix profiles or batches.

A run passes only when:

1. stdout matches `expected_output.tsv` exactly;
2. stderr is empty;
3. no row is missing;
4. no row contains `|FAIL`;
5. there is no signal, assertion, timeout, MySQL 2013/2006, or lost connection.

This batch has no planned negative SQL errors. `ANALYZE TABLE` output is expected only in statistics cases.

## Regenerate, verify, and audit

```bash
PYTHONPATH=src .venv312/bin/python tools/generate_type_upgrade_boundary.py \\
  --output generated/type_upgrade_boundary_v1

PYTHONPATH=src .venv312/bin/python tools/run_type_upgrade_boundary.py \\
  --cases generated/type_upgrade_boundary_v1 \\
  --results generated/type_upgrade_boundary_v1/local_results.jsonl \\
  --summary generated/type_upgrade_boundary_v1/local_summary.json \\
  --profile copy

PYTHONPATH=src .venv312/bin/python tools/audit_type_upgrade_boundary.py \\
  --boundary generated/type_upgrade_boundary_v1 \\
  --parent generated/type_upgrade_consistency/cases.jsonl.gz \\
  --parent generated/type_upgrade_consistency_extension_v1/cases.jsonl.gz \\
  --parent generated/type_upgrade_statistics_v1/cases.jsonl.gz \\
  --parent generated/type_upgrade_pipeline_v1/cases.jsonl.gz
```
"""
    (output / "README.md").write_text(readme, encoding="utf-8")
    return manifest
