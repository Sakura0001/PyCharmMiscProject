"""Deterministic condensed SQL artifacts for internal DDL-upgrade pipelines.

The batch deliberately uses individual SQL files rather than one giant suite so
an internal pipeline can run one scenario at a time or concatenate all files.
Output is restricted to stable assertion labels and deterministic ANALYZE TABLE
result rows.
"""

from __future__ import annotations

import gzip
import hashlib
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

PIPELINE_BATCH_ID = "2026-10-15-type-upgrade-pipeline-v1"
PIPELINE_BATCH_KIND = "pipeline_condensed_batch"
PIPELINE_PARENT_BATCH_ID = "2026-10-14-type-upgrade-statistics-and-chain-v1"
PIPELINE_CASE_PREFIX = "TUCP"
PIPELINE_PROFILES = ("copy", "inplace", "instant")
PIPELINE_ROW_COUNT = 192  # 96 rows in each of reference and algorithm tables.
PIPELINE_DATABASE = "qa_type_upgrade_pipeline"
PIPELINE_AUTHOR = "yuzhengwen y00938623"
PIPELINE_CREATE_AT = "2026-10-15"
PIPELINE_FE = "FE2026081100174"


@dataclass(frozen=True)
class PipelineScenario:
    case_no: int
    description: str
    family: str
    source_type: str
    target_type: str
    attribute: str = "NULL"
    index_profile: str = "secondary"
    partition_form: str = "ordinary"
    engine: str = "InnoDB"
    row_format: str | None = None
    charset: str | None = None
    collation: str | None = None
    dependency_profile: str = "none"
    foreign_key_action: str = ""
    stats_profile: str = ""
    chained: bool = False
    multi_column: bool = False
    target_is_primary: bool = False
    auto_increment: bool = False
    unique_values: bool = False

    @property
    def case_id(self) -> str:
        return f"{PIPELINE_CASE_PREFIX}-{self.case_no:06d}"

    @property
    def base(self) -> str:
        return f"tucp_{self.case_no:03d}"

    @property
    def ref_table(self) -> str:
        return f"tab_{self.base}_ref"

    @property
    def algo_table(self) -> str:
        return f"tab_{self.base}_algo"

    @property
    def parent_ref_table(self) -> str:
        return f"tab_{self.base}_parent_ref"

    @property
    def parent_algo_table(self) -> str:
        return f"tab_{self.base}_parent_algo"

    @property
    def audit_ref_table(self) -> str:
        return f"tab_{self.base}_audit_ref"

    @property
    def audit_algo_table(self) -> str:
        return f"tab_{self.base}_audit_algo"

    @property
    def index_name(self) -> str:
        prefix = {
            "secondary": "idx",
            "unique": "uk",
            "composite": "idx",
            "prefix": "idx",
            "descending": "idx",
            "functional": "idx",
        }.get(self.index_profile, "idx")
        return f"{prefix}_{self.base}_target"


@dataclass(frozen=True)
class PipelineCase:
    case_id: str
    batch_id: str
    batch_kind: str
    scenario: PipelineScenario
    sql: str
    expected_output: tuple[str, ...]

    @property
    def family(self) -> str:
        return self.scenario.family

    @property
    def source_type(self) -> str:
        return self.scenario.source_type

    @property
    def target_type(self) -> str:
        return self.scenario.target_type

    @property
    def index_profile(self) -> str:
        return self.scenario.index_profile

    @property
    def partition_form(self) -> str:
        return self.scenario.partition_form

    @property
    def engine(self) -> str:
        return self.scenario.engine

    @property
    def dependency_profile(self) -> str:
        return self.scenario.dependency_profile

    @property
    def foreign_key_action(self) -> str:
        return self.scenario.foreign_key_action

    @property
    def stats_profile(self) -> str:
        return self.scenario.stats_profile

    @property
    def chained(self) -> bool:
        return self.scenario.chained

    @property
    def multi_column(self) -> bool:
        return self.scenario.multi_column

    def to_json(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["expected_output"] = list(self.expected_output)
        payload["sql_line_count"] = len(self.sql.splitlines())
        payload["algorithm_statement_count"] = self.sql.upper().count("ALGORITHM=")
        return payload


def _scenario(
    case_no: int,
    description: str,
    family: str,
    source_type: str,
    target_type: str,
    **kwargs: Any,
) -> PipelineScenario:
    return PipelineScenario(
        case_no=case_no,
        description=description,
        family=family,
        source_type=source_type,
        target_type=target_type,
        **kwargs,
    )


def pipeline_scenarios() -> list[PipelineScenario]:
    """Return the 50 intentionally condensed core scenarios."""
    return [
        _scenario(1, "整数 TINYINT 升级 SMALLINT", "integer", "TINYINT", "SMALLINT"),
        _scenario(2, "整数 SMALLINT 升级 MEDIUMINT + 唯一索引", "integer", "SMALLINT", "MEDIUMINT", attribute="NOT NULL", index_profile="unique", unique_values=True),
        _scenario(3, "整数 MEDIUMINT 升级 INT + 组合索引", "integer", "MEDIUMINT", "INT", attribute="NOT NULL DEFAULT 0", index_profile="composite"),
        _scenario(4, "整数 INT 升级 BIGINT + 降序索引", "integer", "INT", "BIGINT", attribute="NOT NULL COMMENT 'target column'", index_profile="descending"),
        _scenario(5, "无符号 TINYINT 升级 SMALLINT", "integer", "TINYINT UNSIGNED", "SMALLINT UNSIGNED", attribute="NOT NULL"),
        _scenario(6, "无符号 SMALLINT 升级 INT + 函数索引", "integer", "SMALLINT UNSIGNED", "INT UNSIGNED", attribute="NOT NULL", index_profile="functional"),
        _scenario(7, "无符号 INT 升级 BIGINT + 唯一索引", "integer", "INT UNSIGNED", "BIGINT UNSIGNED", attribute="NOT NULL", index_profile="unique", unique_values=True),
        _scenario(8, "SMALLINT 主键升级 INT 并保留 AUTO_INCREMENT", "integer", "SMALLINT", "INT", attribute="NOT NULL AUTO_INCREMENT", index_profile="primary", target_is_primary=True, auto_increment=True, unique_values=True),
        _scenario(9, "DECIMAL(5,2) 扩精度保持标度", "decimal", "DECIMAL(5,2)", "DECIMAL(7,2)", attribute="NOT NULL DEFAULT 0.00"),
        _scenario(10, "DECIMAL(10,4) 扩精度保持标度", "decimal", "DECIMAL(10,4)", "DECIMAL(12,4)", attribute="NULL"),
        _scenario(11, "DECIMAL(18,6) 扩精度保持标度", "decimal", "DECIMAL(18,6)", "DECIMAL(20,6)", attribute="NOT NULL COMMENT 'decimal target'"),
        _scenario(12, "NUMERIC(24,8) 扩精度保持标度", "decimal", "NUMERIC(24,8)", "NUMERIC(26,8)", attribute="NOT NULL DEFAULT 0.00000000"),
        _scenario(13, "DECIMAL(38,12) 扩精度保持标度", "decimal", "DECIMAL(38,12)", "DECIMAL(40,12)", attribute="NULL"),
        _scenario(14, "DECIMAL(55,18) 扩精度保持标度", "decimal", "DECIMAL(55,18)", "DECIMAL(57,18)", attribute="NOT NULL"),
        _scenario(15, "CHAR(1) 升级 CHAR(4) + MyISAM", "character", "CHAR(1)", "CHAR(4)", attribute="NOT NULL", engine="MyISAM"),
        _scenario(16, "CHAR(8) 升级 VARCHAR(32)", "character", "CHAR(8)", "VARCHAR(32)", attribute="NOT NULL DEFAULT 'x'"),
        _scenario(17, "VARCHAR(16) 升级 VARCHAR(32) + 唯一索引", "character", "VARCHAR(16)", "VARCHAR(32)", attribute="NOT NULL", index_profile="unique", unique_values=True),
        _scenario(18, "VARCHAR(63) 升级 VARCHAR(64) + MEMORY", "character", "VARCHAR(63)", "VARCHAR(64)", attribute="NOT NULL", engine="MEMORY"),
        _scenario(19, "VARCHAR(191) 升级 VARCHAR(192)", "character", "VARCHAR(191)", "VARCHAR(192)", attribute="NOT NULL", charset="utf8mb4", collation="utf8mb4_0900_ai_ci"),
        _scenario(20, "VARCHAR(255) 升级 VARCHAR(256) + DYNAMIC 行格式", "character", "VARCHAR(255)", "VARCHAR(256)", attribute="NULL", row_format="DYNAMIC"),
        _scenario(21, "VARCHAR(1023) 升级 VARCHAR(1024) + 前缀索引", "character", "VARCHAR(1023)", "VARCHAR(1024)", attribute="NOT NULL", index_profile="prefix", row_format="COMPACT"),
        _scenario(22, "TINYTEXT 升级 TEXT + 前缀索引", "character", "TINYTEXT", "TEXT", attribute="NULL", index_profile="prefix"),
        _scenario(23, "BINARY(16) 升级 BINARY(32) + 前缀索引", "binary", "BINARY(16)", "BINARY(32)", attribute="NOT NULL", index_profile="prefix"),
        _scenario(24, "VARBINARY(16) 升级 VARBINARY(32) + 唯一索引", "binary", "VARBINARY(16)", "VARBINARY(32)", attribute="NOT NULL", index_profile="unique", unique_values=True),
        _scenario(25, "VARBINARY(127) 升级 VARBINARY(128)", "binary", "VARBINARY(127)", "VARBINARY(128)", attribute="NULL"),
        _scenario(26, "VARBINARY(255) 升级 VARBINARY(256)", "binary", "VARBINARY(255)", "VARBINARY(256)", attribute="NOT NULL"),
        _scenario(27, "VARBINARY(511) 升级 VARBINARY(512)", "binary", "VARBINARY(511)", "VARBINARY(512)", attribute="NOT NULL"),
        _scenario(28, "TINYBLOB 升级 BLOB + 前缀索引", "binary", "TINYBLOB", "BLOB", attribute="NULL", index_profile="prefix"),
        _scenario(29, "BIT(1) 升级 BIT(2)", "bit", "BIT(1)", "BIT(2)", attribute="NOT NULL"),
        _scenario(30, "BIT(4) 升级 BIT(8)", "bit", "BIT(4)", "BIT(8)", attribute="NOT NULL"),
        _scenario(31, "BIT(8) 升级 BIT(16)", "bit", "BIT(8)", "BIT(16)", attribute="NULL"),
        _scenario(32, "BIT(11) 升级 BIT(17)", "bit", "BIT(11)", "BIT(17)", attribute="NOT NULL"),
        _scenario(33, "BIT(16) 升级 BIT(24)", "bit", "BIT(16)", "BIT(24)", attribute="NOT NULL"),
        _scenario(34, "BIT(24) 升级 BIT(32)", "bit", "BIT(24)", "BIT(32)", attribute="NULL"),
        _scenario(35, "BIT(32) 升级 BIT(40)", "bit", "BIT(32)", "BIT(40)", attribute="NOT NULL"),
        _scenario(36, "BIT(40) 升级 BIT(48)", "bit", "BIT(40)", "BIT(48)", attribute="NOT NULL"),
        _scenario(37, "BIT(48) 升级 BIT(56)", "bit", "BIT(48)", "BIT(56)", attribute="NULL"),
        _scenario(38, "BIT(56) 升级 BIT(64)", "bit", "BIT(56)", "BIT(64)", attribute="NOT NULL"),
        _scenario(39, "BIT(63) 升级 BIT(64)", "bit", "BIT(63)", "BIT(64)", attribute="NOT NULL"),
        _scenario(40, "外键 ON DELETE CASCADE 升级子表", "foreign_key", "SMALLINT", "INT", attribute="NOT NULL", foreign_key_action="cascade_delete"),
        _scenario(41, "外键 ON UPDATE CASCADE 升级子表", "foreign_key", "MEDIUMINT", "BIGINT", attribute="NOT NULL", foreign_key_action="cascade_update"),
        _scenario(42, "外键 ON DELETE SET NULL 升级子表", "foreign_key", "INT", "BIGINT", attribute="NULL", foreign_key_action="set_null"),
        _scenario(43, "外键 NO ACTION 元数据保持", "foreign_key", "SMALLINT", "BIGINT", attribute="NOT NULL", foreign_key_action="no_action"),
        _scenario(44, "视图跨升级读取一致性", "dependency", "VARCHAR(32)", "VARCHAR(128)", attribute="NOT NULL", dependency_profile="view"),
        _scenario(45, "触发器跨升级写入审计", "dependency", "DECIMAL(12,4)", "DECIMAL(16,4)", attribute="NOT NULL", dependency_profile="trigger"),
        _scenario(46, "存储函数跨升级读取", "dependency", "VARBINARY(32)", "VARBINARY(128)", attribute="NOT NULL", dependency_profile="function"),
        _scenario(47, "存储过程跨升级写入", "dependency", "BIT(16)", "BIT(32)", attribute="NOT NULL", dependency_profile="procedure"),
        _scenario(48, "普通表升级后统计信息更新", "statistics", "INT", "BIGINT", attribute="NOT NULL", stats_profile="table_index"),
        _scenario(49, "分区表升级后统计信息更新", "statistics", "VARCHAR(64)", "VARCHAR(128)", attribute="NOT NULL", partition_form="range", stats_profile="partition"),
        _scenario(50, "连续升级 + 多列同时升级 + 全依赖组合", "table_form", "SMALLINT", "BIGINT", attribute="NOT NULL", chained=True, multi_column=True, dependency_profile="view_trigger_function_procedure"),
    ]


def _quote(value: str) -> str:
    return "'" + value.replace("\\", "\\\\").replace("'", "''") + "'"


def _type_family(scenario: PipelineScenario) -> str:
    source = scenario.source_type.upper()
    if source.startswith(("TINYINT", "SMALLINT", "MEDIUMINT", "INT", "BIGINT", "NUMERIC")):
        return "integer" if not source.startswith("NUMERIC") else "decimal"
    if source.startswith("DECIMAL"):
        return "decimal"
    if source.startswith(("CHAR", "VARCHAR", "TINYTEXT", "TEXT")):
        return "character"
    if source.startswith(("BINARY", "VARBINARY", "TINYBLOB", "BLOB")):
        return "binary"
    if source.startswith("BIT"):
        return "bit"
    return scenario.family


def _length(type_name: str) -> int:
    if "TINYTEXT" in type_name or "TINYBLOB" in type_name:
        return 255
    if type_name in {"TEXT", "BLOB"}:
        return 255
    start = type_name.find("(")
    end = type_name.find(")", start)
    if start < 0 or end < 0:
        return 0
    return int(type_name[start + 1 : end].split(",")[0])


def _integer_range(type_name: str) -> tuple[int, int]:
    unsigned = "UNSIGNED" in type_name
    base = type_name.split("(")[0].split()[0]
    signed = {
        "TINYINT": (-128, 127),
        "SMALLINT": (-32768, 32767),
        "MEDIUMINT": (-8388608, 8388607),
        "INT": (-2147483648, 2147483647),
        "BIGINT": (-9223372036854775808, 9223372036854775807),
    }[base]
    return (0, signed[1]) if unsigned else signed


def _integer_value(type_name: str, row: int, *, boundary: bool, unique: bool = False) -> int:
    low, high = _integer_range(type_name)
    if unique:
        return low + ((row - 1) % (high - low + 1))
    if boundary:
        choices = [low, high, 0, 1, low + 1, high - 1]
        return choices[(row - 1) % len(choices)]
    return row


def _character_value(type_name: str, row: int, *, boundary: bool, unique: bool) -> str:
    length = _length(type_name)
    if unique:
        width = max(1, min(length, 12))
        return f"u{row:0{width - 1}d}"[-width:]
    if boundary:
        # TEXT families are byte-limited; use only one-byte characters for boundary rows.
        if "TEXT" in type_name:
            fillers = ["a", "Z", "9", "_", "-"]
        else:
            fillers = ["a", "Z", "9", "中", "_", "-"]
        return (fillers[(row - 1) % len(fillers)] * ((row - 1) % max(1, length) + 1))[:length]
    return f"v{row:03d}"[:length] or "v"


def _binary_value(type_name: str, row: int, *, boundary: bool, unique: bool) -> str:
    length = _length(type_name)
    if unique:
        width = max(1, min(length, 16))
        return (row + 1).to_bytes(width, "big").hex()
    if boundary:
        value = (0xFF << ((row - 1) % 8)) & ((1 << (min(length, 8) * 8)) - 1)
        return value.to_bytes(max(1, min(length, 8)), "big").hex().ljust(length * 2, "0")[: length * 2]
    return ((row * 0x123456789ABCDEF) & ((1 << (min(length, 8) * 8)) - 1)).to_bytes(max(1, min(length, 8)), "big").hex().ljust(length * 2, "0")[: length * 2]


def _decimal_value(type_name: str, row: int, *, boundary: bool) -> str:
    precision, scale = map(int, type_name[type_name.find("(") + 1 : type_name.find(")")].split(","))
    if boundary:
        max_integer = 10 ** (precision - scale) - 1
        base = max_integer // 2
    else:
        base = row
    return f"{base}.{(row % (10 ** scale)):0{scale}d}"


def _bit_width(type_name: str) -> int:
    return _length(type_name)


def _bit_value(type_name: str, row: int, *, boundary: bool) -> str:
    width = _bit_width(type_name)
    if boundary:
        choices = [0, (1 << width) - 1, 1, (1 << (width - 1)), (1 << width) - 2]
        value = choices[(row - 1) % len(choices)]
    else:
        value = (row * 7919) & ((1 << width) - 1)
    return "b'" + format(value, f"0{width}b") + "'"


def _literal(scenario: PipelineScenario, type_name: str, row: int, *, boundary: bool, unique: bool = False) -> str:
    family = _type_family(scenario)
    source = type_name.upper()
    if source.startswith(("TINYINT", "SMALLINT", "MEDIUMINT", "INT", "BIGINT")):
        return str(_integer_value(source, row, boundary=boundary, unique=unique))
    if source.startswith(("DECIMAL", "NUMERIC")):
        return _decimal_value(source, row, boundary=boundary)
    if source.startswith(("CHAR", "VARCHAR", "TINYTEXT", "TEXT")):
        return _quote(_character_value(source, row, boundary=boundary, unique=unique))
    if source.startswith(("BINARY", "VARBINARY", "TINYBLOB", "BLOB")):
        return "x'" + _binary_value(source, row, boundary=boundary, unique=unique) + "'"
    if source.startswith("BIT"):
        return _bit_value(source, row, boundary=boundary)
    raise AssertionError(f"unsupported type: {type_name}")


def _default_literal(scenario: PipelineScenario) -> str:
    family = _type_family(scenario)
    if family == "integer":
        return "0"
    if family == "decimal":
        return "0." + "0" * int(scenario.target_type.split(",")[1].split(")")[0])
    if family == "character":
        return "'x'"
    if family == "binary":
        return "x'00'"
    if family == "bit":
        return "b'0'"
    raise AssertionError(family)


def _column_definition(scenario: PipelineScenario, type_name: str) -> str:
    column = "id" if scenario.target_is_primary else "target_col"
    attribute = scenario.attribute
    if "DEFAULT" in attribute:
        attribute = attribute.split(" DEFAULT ", 1)[0] + " DEFAULT " + _default_literal(scenario)
    charset = ""
    if _type_family(scenario) == "character" and scenario.charset:
        charset = f" CHARACTER SET {scenario.charset} COLLATE {scenario.collation}"
    return f"{column} {type_name}{charset} {attribute}".strip()


def _canary_columns(scenario: PipelineScenario, *, wide_length: int | None = None) -> str:
    if wide_length is not None:
        wide = f"VARCHAR({wide_length})"
    elif scenario.engine == "MEMORY":
        wide = "VARCHAR(512)"
    else:
        wide = "MEDIUMTEXT"
    return (
        "part_key INT NOT NULL DEFAULT 0, "
        "canary_int BIGINT NOT NULL DEFAULT 7, "
        f"canary_varchar VARCHAR(64) NOT NULL DEFAULT 'canary', "
        "canary_varbinary VARBINARY(64) NOT NULL DEFAULT x'00', "
        "canary_decimal DECIMAL(20,4) NOT NULL DEFAULT 12.5000, "
        f"wide_col {wide} NOT NULL"
    )


def _index_sql(scenario: PipelineScenario, table: str) -> str:
    column = "id" if scenario.target_is_primary else "target_col"
    if scenario.index_profile == "none" or scenario.target_is_primary:
        return ""
    name = scenario.index_name
    if scenario.index_profile == "secondary":
        return f"KEY {name} ({column})"
    if scenario.index_profile == "unique":
        return f"UNIQUE KEY {name} ({column})"
    if scenario.index_profile == "composite":
        return f"KEY {name} ({column}, canary_int)"
    if scenario.index_profile == "prefix":
        if _type_family(scenario) == "binary" and _length(scenario.source_type) <= 32:
            prefix_length = 8
        elif scenario.source_type == "TINYTEXT":
            prefix_length = 63
        else:
            prefix_length = 191
        return f"KEY {name} ({column}({prefix_length}))"
    if scenario.index_profile == "descending":
        return f"KEY {name} ({column} DESC)"
    if scenario.index_profile == "functional":
        return f"KEY {name} ((CAST({column} AS CHAR(32))))"
    raise AssertionError(scenario.index_profile)


def _partition_sql(scenario: PipelineScenario) -> str:
    if scenario.partition_form == "ordinary":
        return ""
    if scenario.partition_form == "range":
        return " PARTITION BY RANGE (part_key) (PARTITION p0 VALUES LESS THAN (32), PARTITION p1 VALUES LESS THAN (64), PARTITION p2 VALUES LESS THAN (96), PARTITION pmax VALUES LESS THAN MAXVALUE)"
    if scenario.partition_form == "list":
        return " PARTITION BY LIST (part_key) (PARTITION p0 VALUES IN (0,1,2), PARTITION p1 VALUES IN (3,4,5), PARTITION p2 VALUES IN (6,7,8), PARTITION p3 VALUES IN (9,10,11))"
    if scenario.partition_form == "hash":
        return " PARTITION BY HASH (part_key) PARTITIONS 4"
    if scenario.partition_form == "key":
        return " PARTITION BY KEY (part_key) PARTITIONS 4"
    raise AssertionError(scenario.partition_form)


def _table_options(scenario: PipelineScenario) -> str:
    options = [f"ENGINE={scenario.engine}"]
    if scenario.row_format and scenario.engine == "InnoDB":
        options.append(f"ROW_FORMAT={scenario.row_format}")
    if _type_family(scenario) == "character":
        charset = scenario.charset or "utf8mb4"
        collation = scenario.collation or "utf8mb4_0900_ai_ci"
        options.append(f"DEFAULT CHARSET={charset} COLLATE={collation}")
    return " " + " ".join(options)


def _create_table_sql(scenario: PipelineScenario, table: str, target_type: str) -> str:
    column = "id" if scenario.target_is_primary else "target_col"
    indexes = []
    if not scenario.partition_form or scenario.partition_form == "ordinary":
        if scenario.target_is_primary:
            indexes.append("PRIMARY KEY (id)")
        else:
            indexes.append("PRIMARY KEY (id)")
    else:
        indexes.append("KEY idx_" + scenario.base + "_id (id)")
    if scenario.foreign_key_action:
        indexes.append(f"KEY idx_{scenario.base}_fk (fk_col)")
    index_sql = _index_sql(scenario, table)
    if index_sql:
        indexes.append(index_sql)
    wide_length = 128 if scenario.multi_column else None
    first_column = (
        _column_definition(scenario, target_type)
        if scenario.target_is_primary
        else f"id BIGINT NOT NULL, {_column_definition(scenario, target_type)}"
    )
    if scenario.foreign_key_action:
        nullable_fk = "NULL" if scenario.foreign_key_action == "set_null" else "NOT NULL"
        first_column += f", fk_col BIGINT {nullable_fk}"
    return (
        f"CREATE TABLE {table} ("
        f"{first_column}, "
        f"{_canary_columns(scenario, wide_length=wide_length)}, "
        + ", ".join(indexes)
        + ")"
        + _table_options(scenario)
        + _partition_sql(scenario)
        + ";"
    )


def _row_values(scenario: PipelineScenario, row: int, type_name: str, *, boundary: bool) -> str:
    unique = scenario.unique_values or scenario.index_profile == "unique"
    target_value = _literal(scenario, type_name, row, boundary=boundary, unique=unique)
    if scenario.target_is_primary:
        prefix = target_value
    else:
        prefix = f"{row}, {target_value}"
        if scenario.foreign_key_action:
            prefix += f", {row}"
    return (
        f"({prefix}, {(row - 1) % 12}, {row}, "
        f"'row-{row:03d}', x'{row % 256:02X}', {(row % 1000) / 10:.4f}, "
        f"'wide-{row:03d}')"
    )


def _insert_rows(
    scenario: PipelineScenario,
    table: str,
    type_name: str,
    *,
    boundary: bool,
    row_offset: int = 0,
) -> list[str]:
    if scenario.target_is_primary:
        columns = "id,part_key,canary_int,canary_varchar,canary_varbinary,canary_decimal,wide_col"
    elif scenario.foreign_key_action:
        columns = "id,target_col,fk_col,part_key,canary_int,canary_varchar,canary_varbinary,canary_decimal,wide_col"
    else:
        columns = "id,target_col,part_key,canary_int,canary_varchar,canary_varbinary,canary_decimal,wide_col"
    return [
        f"INSERT INTO {table} ({columns}) VALUES {_row_values(scenario, row, type_name, boundary=boundary)};"
        for row in range(1 + row_offset, 97 + row_offset)
    ]


def _marker(scenario: PipelineScenario, check: str, ok: bool = True) -> str:
    status = "OK" if ok else "FAIL"
    return f"{scenario.case_id}|{check}|{status}"


def _assert_sql(scenario: PipelineScenario, check: str, condition: str) -> tuple[str, str]:
    return (
        f"SELECT CASE WHEN {condition} THEN '{_marker(scenario, check)}' ELSE '{_marker(scenario, check, False)}' END;",
        _marker(scenario, check),
    )


def _schema_check(scenario: PipelineScenario) -> tuple[str, str]:
    ref, algo = scenario.ref_table, scenario.algo_table
    columns = "column_name, ordinal_position, column_type, is_nullable, column_default, extra, character_set_name, collation_name, column_comment"
    condition = (
        "NOT EXISTS (("
        f"SELECT {columns} FROM information_schema.COLUMNS WHERE table_schema=DATABASE() AND table_name='{ref}' "
        f"EXCEPT SELECT {columns} FROM information_schema.COLUMNS WHERE table_schema=DATABASE() AND table_name='{algo}') "
        "UNION ALL ("
        f"SELECT {columns} FROM information_schema.COLUMNS WHERE table_schema=DATABASE() AND table_name='{algo}' "
        f"EXCEPT SELECT {columns} FROM information_schema.COLUMNS WHERE table_schema=DATABASE() AND table_name='{ref}') LIMIT 1)"
    )
    return _assert_sql(scenario, "SCHEMA", condition)


def _data_condition(scenario: PipelineScenario) -> str:
    ref, algo = scenario.ref_table, scenario.algo_table
    if scenario.target_is_primary:
        target_compare = "r.id <=> a.id"
    else:
        target_compare = "r.target_col <=> a.target_col"
    fk_compare = "r.fk_col <=> a.fk_col" if scenario.foreign_key_action else "TRUE"
    return (
        "NOT EXISTS ("
        f"SELECT 1 FROM {ref} r LEFT JOIN {algo} a USING(id) WHERE a.id IS NULL "
        f"UNION ALL SELECT 1 FROM {algo} a LEFT JOIN {ref} r USING(id) WHERE r.id IS NULL "
        f"UNION ALL SELECT 1 FROM {ref} r JOIN {algo} a USING(id) WHERE NOT ("
        f"{target_compare} AND {fk_compare} AND r.part_key <=> a.part_key AND r.canary_int <=> a.canary_int "
        "AND r.canary_varchar <=> a.canary_varchar AND r.canary_varbinary <=> a.canary_varbinary "
        "AND r.canary_decimal <=> a.canary_decimal AND r.wide_col <=> a.wide_col) LIMIT 1)"
    )


def _index_check(scenario: PipelineScenario) -> tuple[str, str]:
    ref, algo = scenario.ref_table, scenario.algo_table
    fields = "index_name, non_unique, seq_in_index, column_name, collation, sub_part, packed, nullable, index_type, comment, index_comment, expression"
    condition = (
        "NOT EXISTS (("
        f"SELECT {fields} FROM information_schema.STATISTICS WHERE table_schema=DATABASE() AND table_name='{ref}' "
        f"EXCEPT SELECT {fields} FROM information_schema.STATISTICS WHERE table_schema=DATABASE() AND table_name='{algo}') "
        "UNION ALL ("
        f"SELECT {fields} FROM information_schema.STATISTICS WHERE table_schema=DATABASE() AND table_name='{algo}' "
        f"EXCEPT SELECT {fields} FROM information_schema.STATISTICS WHERE table_schema=DATABASE() AND table_name='{ref}') LIMIT 1)"
    )
    return _assert_sql(scenario, "INDEX", condition)


def _stats_checks(scenario: PipelineScenario) -> list[tuple[str, str]]:
    checks: list[tuple[str, str]] = []
    if scenario.stats_profile == "table_index":
        for table in (scenario.ref_table, scenario.algo_table):
            condition = (
                "EXISTS (SELECT 1 FROM mysql.innodb_table_stats WHERE database_name=DATABASE() "
                f"AND table_name='{table}' AND n_rows >= 0 AND clustered_index_size >= 0 AND sum_of_other_index_sizes >= 0)"
            )
            checks.append(_assert_sql(scenario, f"TABLE_STATS_{table.upper()}", condition))
            condition = (
                "EXISTS (SELECT 1 FROM mysql.innodb_index_stats WHERE database_name=DATABASE() "
                f"AND table_name='{table}' AND index_name='PRIMARY' AND stat_name IN ('n_diff_pfx01','n_leaf_pages','size') "
                "AND stat_value >= 0 AND (sample_size IS NULL OR sample_size >= 0))"
            )
            checks.append(_assert_sql(scenario, f"INDEX_STATS_{table.upper()}", condition))
    if scenario.stats_profile == "partition":
        for table in (scenario.ref_table, scenario.algo_table):
            condition = (
                "NOT EXISTS (SELECT expected.suffix FROM (SELECT 'p0' AS suffix UNION SELECT 'p1' UNION SELECT 'p2' UNION SELECT 'pmax') expected "
                "WHERE NOT EXISTS (SELECT 1 FROM mysql.innodb_table_stats WHERE database_name=DATABASE() "
                f"AND table_name=CONCAT('{table}', '#p#', expected.suffix) AND n_rows >= 0))"
            )
            checks.append(_assert_sql(scenario, f"PARTITION_STATS_{table.upper()}", condition))
    return checks


def _foreign_key_objects(scenario: PipelineScenario) -> list[str]:
    if not scenario.foreign_key_action:
        return []
    action = {
        "cascade_delete": "ON DELETE CASCADE",
        "cascade_update": "ON UPDATE CASCADE",
        "set_null": "ON DELETE SET NULL",
        "no_action": "ON DELETE NO ACTION",
    }[scenario.foreign_key_action]
    return [
        f"CREATE TABLE {scenario.parent_ref_table} (parent_id BIGINT NOT NULL, payload VARCHAR(32) NOT NULL, PRIMARY KEY (parent_id)) ENGINE=InnoDB;",
        f"CREATE TABLE {scenario.parent_algo_table} (parent_id BIGINT NOT NULL, payload VARCHAR(32) NOT NULL, PRIMARY KEY (parent_id)) ENGINE=InnoDB;",
    ]


def _build_case(scenario: PipelineScenario) -> PipelineCase:
    statements: list[str] = []
    expected: list[str] = []

    header = [
        "-- --------------------------------------------------------",
        f"-- author       : {PIPELINE_AUTHOR}",
        f"-- create at    : {PIPELINE_CREATE_AT}",
        f"-- description  : 场景 {scenario.case_id} {scenario.description}",
        f"-- FE           : {PIPELINE_FE}",
        f"-- BATCH_ID: {PIPELINE_BATCH_ID}",
        f"-- BATCH_KIND: {PIPELINE_BATCH_KIND}",
        "-- --------------------------------------------------------",
        f"-- CASE_ID: {scenario.case_id}",
        "-- 判定：升级成功、表结构/索引/数据一致，依赖和统计信息检查输出固定 OK。",
        "-- 运行：mysql --batch --raw --skip-column-names --force，输出必须与 expected_output.tsv 一致。",
        "-- pre-cleanup：先删表，再清理非表依赖对象。",
    ]

    tables = [scenario.algo_table, scenario.ref_table]
    if scenario.foreign_key_action:
        tables.extend([scenario.parent_algo_table, scenario.parent_ref_table])
    if scenario.dependency_profile == "trigger" or scenario.dependency_profile == "combined":
        tables.extend([scenario.audit_algo_table, scenario.audit_ref_table])
    cleanup_tables = list(tables)

    statements.extend(header)
    statements.extend(f"DROP TABLE IF EXISTS {table};" for table in cleanup_tables)

    object_names: list[str] = []
    if scenario.dependency_profile in {"view", "combined"}:
        object_names.extend([f"view_{scenario.base}_ref", f"view_{scenario.base}_algo"])
    if scenario.dependency_profile in {"function", "combined"}:
        object_names.extend([f"fn_{scenario.base}_ref", f"fn_{scenario.base}_algo"])
    if scenario.dependency_profile in {"procedure", "combined"}:
        object_names.extend([f"proc_{scenario.base}_ref", f"proc_{scenario.base}_algo"])
    for name in object_names:
        kind = "VIEW" if name.startswith("view_") else "FUNCTION" if name.startswith("fn_") else "PROCEDURE"
        statements.append(f"DROP {kind} IF EXISTS {name};")

    statements.append("-- create objects")
    if scenario.foreign_key_action:
        statements.extend(_foreign_key_objects(scenario))
    if scenario.dependency_profile == "trigger" or scenario.dependency_profile == "combined":
        statements.append(f"CREATE TABLE {scenario.audit_ref_table} (id BIGINT NOT NULL, target_col {scenario.target_type}, PRIMARY KEY (id)) ENGINE=InnoDB;")
        statements.append(f"CREATE TABLE {scenario.audit_algo_table} (id BIGINT NOT NULL, target_col {scenario.target_type}, PRIMARY KEY (id)) ENGINE=InnoDB;")

    statements.append(_create_table_sql(scenario, scenario.ref_table, scenario.target_type))
    statements.append(_create_table_sql(scenario, scenario.algo_table, scenario.source_type))

    if scenario.foreign_key_action:
        action = {
            "cascade_delete": "ON DELETE CASCADE",
            "cascade_update": "ON UPDATE CASCADE",
            "set_null": "ON DELETE SET NULL",
            "no_action": "ON DELETE NO ACTION",
        }[scenario.foreign_key_action]
        for parent, child, constraint in (
            (scenario.parent_ref_table, scenario.ref_table, f"fk_{scenario.base}_ref"),
            (scenario.parent_algo_table, scenario.algo_table, f"fk_{scenario.base}_algo"),
        ):
            statements.append(
                f"ALTER TABLE {child} ADD CONSTRAINT {constraint} FOREIGN KEY (fk_col) REFERENCES {parent}(parent_id) {action};"
            )
        parent_values = ",".join(f"({row},'parent-{row:03d}')" for row in range(1, 193))
        for parent in (scenario.parent_ref_table, scenario.parent_algo_table):
            statements.append(f"INSERT INTO {parent} (parent_id,payload) VALUES {parent_values};")

    if scenario.dependency_profile in {"trigger", "combined"}:
        for table, trigger in ((scenario.ref_table, f"trg_{scenario.base}_ref"), (scenario.algo_table, f"trg_{scenario.base}_algo")):
            audit = scenario.audit_ref_table if table == scenario.ref_table else scenario.audit_algo_table
            statements.append(
                f"CREATE TRIGGER {trigger} AFTER INSERT ON {table} FOR EACH ROW INSERT INTO {audit} (id,target_col) VALUES (NEW.id,NEW.target_col);"
            )
    if scenario.dependency_profile in {"view", "combined"}:
        for table, view in ((scenario.ref_table, f"view_{scenario.base}_ref"), (scenario.algo_table, f"view_{scenario.base}_algo")):
            statements.append(f"CREATE VIEW {view} AS SELECT id,target_col,part_key,canary_int FROM {table};")
    if scenario.dependency_profile in {"function", "combined"}:
        for table, function in ((scenario.ref_table, f"fn_{scenario.base}_ref"), (scenario.algo_table, f"fn_{scenario.base}_algo")):
            statements.append(
                f"CREATE FUNCTION {function}(p_id BIGINT) RETURNS {scenario.target_type} DETERMINISTIC READS SQL DATA RETURN (SELECT target_col FROM {table} WHERE id=p_id);"
            )
    if scenario.dependency_profile in {"procedure", "combined"}:
        for table, procedure in ((scenario.ref_table, f"proc_{scenario.base}_ref"), (scenario.algo_table, f"proc_{scenario.base}_algo")):
            statements.append(
                f"CREATE PROCEDURE {procedure}(p_id BIGINT,p_value {scenario.target_type}) INSERT INTO {table} (id,target_col,part_key,canary_int,canary_varchar,canary_varbinary,canary_decimal,wide_col) VALUES (p_id,p_value,99,p_id,'proc',x'0F',p_id,'proc-wide');"
            )

    statements.append("-- seed deterministic boundary and pattern data")
    statements.extend(_insert_rows(scenario, scenario.ref_table, scenario.source_type, boundary=True))
    statements.extend(_insert_rows(scenario, scenario.algo_table, scenario.source_type, boundary=True))

    statements.append("-- target DDL")
    if scenario.chained:
        intermediate = "INT"
        statements.append(f"ALTER TABLE {scenario.algo_table} MODIFY target_col {intermediate} {scenario.attribute}, ALGORITHM=${{ALGORITHM}};")
        statements.append(f"ALTER TABLE {scenario.algo_table} MODIFY target_col {scenario.target_type} {scenario.attribute}, ALGORITHM=${{ALGORITHM}};")
    else:
        column = "id" if scenario.target_is_primary else "target_col"
        modify = f"MODIFY {column} {scenario.target_type} {scenario.attribute}"
        if scenario.multi_column:
            modify += f", MODIFY wide_col VARCHAR(128) NOT NULL"
        statements.append(f"ALTER TABLE {scenario.algo_table} {modify}, ALGORITHM=${{ALGORITHM}};")

    statements.append("-- post-DDL target-boundary data")
    post_rows_ref = _insert_rows(scenario, scenario.ref_table, scenario.target_type, boundary=True, row_offset=96)
    post_rows_algo = _insert_rows(scenario, scenario.algo_table, scenario.target_type, boundary=True, row_offset=96)
    # Post rows use a disjoint id range so pre/post rows are both retained.
    shifted_ref = [line.replace("VALUES (", "VALUES (1000+", 1) for line in post_rows_ref]
    shifted_algo = [line.replace("VALUES (", "VALUES (1000+", 1) for line in post_rows_algo]
    statements.extend(shifted_ref)
    statements.extend(shifted_algo)

    if scenario.dependency_profile in {"procedure", "combined"}:
        post_value = _literal(scenario, scenario.target_type, 96, boundary=False, unique=scenario.unique_values)
        statements.append(f"CALL proc_{scenario.base}_ref(2001,{post_value});")
        statements.append(f"CALL proc_{scenario.base}_algo(2001,{post_value});")
    if scenario.foreign_key_action in {"cascade_delete", "set_null"}:
        statements.append(f"DELETE FROM {scenario.parent_ref_table} WHERE parent_id=1;")
        statements.append(f"DELETE FROM {scenario.parent_algo_table} WHERE parent_id=1;")
    if scenario.foreign_key_action == "cascade_update":
        statements.append(f"UPDATE {scenario.parent_ref_table} SET parent_id=1001 WHERE parent_id=1;")
        statements.append(f"UPDATE {scenario.parent_algo_table} SET parent_id=1001 WHERE parent_id=1;")

    if scenario.stats_profile:
        statements.append("-- statistics refresh and stable checks")
        for table in (scenario.ref_table, scenario.algo_table):
            statements.append(f"ANALYZE TABLE {table};")
            expected.append(f"{PIPELINE_DATABASE}.{table}\tanalyze\tstatus\tOK")

    statements.append("-- deterministic assertions")
    checks = [_schema_check(scenario), _assert_sql(scenario, "DATA", _data_condition(scenario)), _index_check(scenario)]
    checks.extend(_stats_checks(scenario))

    if scenario.foreign_key_action:
        condition = (
            "EXISTS (SELECT 1 FROM information_schema.REFERENTIAL_CONSTRAINTS WHERE constraint_schema=DATABASE() "
            f"AND constraint_name='fk_{scenario.base}_algo' AND table_name='{scenario.algo_table}' "
            f"AND referenced_table_name='{scenario.parent_algo_table}')"
        )
        checks.append(_assert_sql(scenario, "FK", condition))
    if scenario.dependency_profile in {"view", "combined"}:
        condition = (
            "NOT EXISTS (SELECT 1 FROM view_" + scenario.base + "_ref r LEFT JOIN view_" + scenario.base + "_algo a USING(id) "
            "WHERE a.id IS NULL OR NOT (r.target_col <=> a.target_col AND r.part_key <=> a.part_key AND r.canary_int <=> a.canary_int) LIMIT 1)"
        )
        checks.append(_assert_sql(scenario, "VIEW", condition))
    if scenario.dependency_profile in {"trigger", "combined"}:
        condition = (
            "NOT EXISTS (SELECT 1 FROM " + scenario.audit_ref_table + " r LEFT JOIN " + scenario.audit_algo_table + " a USING(id) "
            "WHERE a.id IS NULL OR NOT (r.target_col <=> a.target_col) LIMIT 1)"
        )
        checks.append(_assert_sql(scenario, "TRIGGER", condition))
    if scenario.dependency_profile in {"function", "combined"}:
        sample_id = 1
        value = _literal(scenario, scenario.source_type, sample_id, boundary=True, unique=scenario.unique_values)
        condition = f"fn_{scenario.base}_ref({sample_id}) <=> {value} AND fn_{scenario.base}_algo({sample_id}) <=> {value}"
        checks.append(_assert_sql(scenario, "FUNCTION", condition))
    if scenario.dependency_profile in {"procedure", "combined"}:
        condition = f"EXISTS (SELECT 1 FROM {scenario.ref_table} WHERE id=2001) AND EXISTS (SELECT 1 FROM {scenario.algo_table} WHERE id=2001)"
        checks.append(_assert_sql(scenario, "PROCEDURE", condition))

    for sql, output in checks:
        statements.append(sql)
        expected.append(output)

    statements.append("-- final cleanup: non-table dependencies first, tables last")
    for name in object_names:
        kind = "VIEW" if name.startswith("view_") else "FUNCTION" if name.startswith("fn_") else "PROCEDURE"
        statements.append(f"DROP {kind} IF EXISTS {name};")
    statements.extend(f"DROP TABLE IF EXISTS {table};" for table in cleanup_tables)

    return PipelineCase(
        case_id=scenario.case_id,
        batch_id=PIPELINE_BATCH_ID,
        batch_kind=PIPELINE_BATCH_KIND,
        scenario=scenario,
        sql="\n".join(statements),
        expected_output=tuple(expected),
    )


def generate_pipeline_cases() -> list[PipelineCase]:
    return [_build_case(scenario) for scenario in pipeline_scenarios()]


def render_pipeline_case(case: PipelineCase, profile: str) -> str:
    if profile not in PIPELINE_PROFILES:
        raise ValueError(f"unsupported profile: {profile}")
    sql = case.sql.replace("${ALGORITHM}", profile.upper())
    sql = sql.replace(
        f"-- CASE_ID: {case.case_id}\n",
        f"-- CASE_ID: {case.case_id}\n-- PROFILE: {profile}\n",
        1,
    )
    return sql + "\n-- @@@EXPECTED@@@\n" + "\n".join(case.expected_output) + "\n"


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _gzip_bytes(payload: str) -> bytes:
    return gzip.compress(payload.encode("utf-8"), compresslevel=9, mtime=0)


def pipeline_manifest(cases: list[PipelineCase], artifact_hashes: dict[str, str] | None = None) -> dict[str, Any]:
    return {
        "batch_id": PIPELINE_BATCH_ID,
        "batch_kind": PIPELINE_BATCH_KIND,
        "parent_batch_id": PIPELINE_PARENT_BATCH_ID,
        "case_id_prefix": PIPELINE_CASE_PREFIX,
        "case_count": len(cases),
        "row_count": PIPELINE_ROW_COUNT,
        "profiles": list(PIPELINE_PROFILES),
        "profile_counts": {profile: len(cases) for profile in PIPELINE_PROFILES},
        "forbidden_types_absent": True,
        "database": PIPELINE_DATABASE,
        "artifacts_sha256": artifact_hashes or {},
    }


def write_pipeline_artifacts(output: Path) -> dict[str, Any]:
    output.mkdir(parents=True, exist_ok=True)
    (output / ".gitignore").write_text(
        "*.actual.tsv\n*.errors.log\n*.out\n",
        encoding="utf-8",
    )
    cases = generate_pipeline_cases()
    artifact_hashes: dict[str, str] = {}

    cases_payload = "".join(json.dumps(case.to_json(), sort_keys=True, separators=(",", ":")) + "\n" for case in cases)
    cases_path = output / "cases.jsonl.gz"
    cases_path.write_bytes(_gzip_bytes(cases_payload))
    artifact_hashes["cases.jsonl.gz"] = _sha256(cases_path)

    expected_lines: list[str] = []
    expected_dir = output / "expected"
    expected_dir.mkdir(exist_ok=True)
    for case in cases:
        per_case = list(case.expected_output)
        expected_lines.extend(per_case)
        (expected_dir / f"{case.case_id}.tsv").write_text("\n".join(per_case) + "\n", encoding="utf-8")
    expected_path = output / "expected_output.tsv"
    expected_path.write_text("\n".join(expected_lines) + "\n", encoding="utf-8")
    artifact_hashes["expected_output.tsv"] = _sha256(expected_path)

    for profile in PIPELINE_PROFILES:
        profile_dir = output / profile
        profile_dir.mkdir(exist_ok=True)
        for case in cases:
            sql = render_pipeline_case(case, profile).split("-- @@@EXPECTED@@@\n", 1)[0]
            (profile_dir / f"{case.case_id}.sql").write_text(sql, encoding="utf-8")
        for path in sorted(profile_dir.glob("*.sql")):
            artifact_hashes[f"{profile}/{path.name}"] = _sha256(path)

    coverage_lines = [
        "case_id\tfamily\tsource_type\ttarget_type\tindex_profile\tpartition_form\tengine\tdependency\tforeign_key_action\tstats\tchained\tmulti_column",
        *(
            "\t".join(
                (
                    case.case_id,
                    case.scenario.family,
                    case.scenario.source_type,
                    case.scenario.target_type,
                    case.scenario.index_profile,
                    case.scenario.partition_form,
                    case.scenario.engine,
                    case.scenario.dependency_profile,
                    case.scenario.foreign_key_action or "none",
                    case.scenario.stats_profile or "none",
                    str(case.scenario.chained).lower(),
                    str(case.scenario.multi_column).lower(),
                )
            )
            for case in cases
        ),
    ]
    coverage_path = output / "coverage.tsv"
    coverage_path.write_text("\n".join(coverage_lines) + "\n", encoding="utf-8")
    artifact_hashes["coverage.tsv"] = _sha256(coverage_path)

    manifest = pipeline_manifest(cases, artifact_hashes)
    manifest_path = output / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    readme = f"""# MySQL type-upgrade condensed pipeline batch

This is a **new, independent condensed batch** for internal pipeline use. It is separate from the earlier `TUC`, `TUCX`, and `TUCS` batches.

- **BATCH_ID:** `{PIPELINE_BATCH_ID}`
- **BATCH_KIND:** `{PIPELINE_BATCH_KIND}`
- **PARENT_BATCH_ID:** `{PIPELINE_PARENT_BATCH_ID}`
- **CASE_PREFIX:** `{PIPELINE_CASE_PREFIX}`
- **CASE_COUNT:** {len(cases)}
- **Profiles:** `copy`, `inplace`, `instant`
- **SQL files:** 150 (50 per profile)
- **Rows per scenario:** 96 reference rows + 96 algorithm rows = 192
- **SQL line range per file:** 413-426
- **Fixed QA database:** `{PIPELINE_DATABASE}`
- **Local MySQL 8.0.45 COPY:** 50/50 scenarios PASS; combined-stream output and final object cleanup PASS

## Output contract

The SQL sets no session or global variables. Each scenario:

1. Starts with `DROP TABLE IF EXISTS`.
2. Creates globally unique `tab_tucp_NNN_*` tables; `idx/uk_tucp_NNN_*` indexes are unique within each table and have globally unique qualified `table.index` identifiers.
3. Seeds deterministic boundary/pattern data.
4. Executes the target upgrade with one explicit `ALGORITHM=<profile>` statement (two statements for the chained case).
5. Inserts post-upgrade target-boundary data.
6. Emits only stable assertion labels such as `TUCP-000001|DATA|OK`.
7. Drops all tables last.

The expected output is identical for `COPY`, `INPLACE`, and `INSTANT`. `ANALYZE TABLE` result rows are included only in the two statistics scenarios; therefore the pipeline must use the fixed database name `{PIPELINE_DATABASE}`. Run the client with `--batch --raw --skip-column-names` so output can be compared byte-for-byte with `expected_output.tsv`.

## Internal pipeline execution

Run each profile separately and do not mix result files:

```bash
# Prepare the fixed schema before running SQL.
mysql --login-path=internal_qa \\
  -e "DROP DATABASE IF EXISTS {PIPELINE_DATABASE}; CREATE DATABASE {PIPELINE_DATABASE} CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci"

cat copy/*.sql | mysql --login-path=internal_qa \\
  --batch --raw --skip-column-names --binary-mode --force \\
  {PIPELINE_DATABASE} > copy.actual.tsv 2> copy.errors.log

diff -u expected_output.tsv copy.actual.tsv
test ! -s copy.errors.log
```

Repeat the same three commands with `inplace/*.sql` and `instant/*.sql`, writing `inplace.actual.tsv` / `instant.actual.tsv`. A run passes only when all three conditions hold:

1. `mysql` has no error output and does not report a nonzero execution status.
2. `diff` is empty.
3. No expected output row is missing and no actual row contains `|FAIL`.

A signal, assertion, MySQL 2013/2006, lost connection, timeout, or missing output is `FAIL_CRASH` or `FAIL_TIMEOUT`, never an expected negative result. This condensed batch intentionally contains no planned negative SQL errors.

For single-scene debugging, use `expected/TUCP-NNNNNN.tsv` as that scene's expected output.

## Core coverage

| Factor | Coverage |
| --- | --- |
| Type families | Integer 8, DECIMAL 6, character 8, binary 6, BIT 11 |
| Index forms | secondary, unique, composite, prefix, descending, functional, primary/AUTO_INCREMENT |
| Foreign keys | `ON DELETE CASCADE`, `ON UPDATE CASCADE`, `ON DELETE SET NULL`, `NO ACTION` |
| Dependencies | view, trigger, stored function, stored procedure, combined dependency scenario |
| Statistics | persistent table/index statistics and partition statistics |
| Special forms | chained `SMALLINT -> INT -> BIGINT`, multi-column upgrade, range partition, `MyISAM`, `MEMORY`, InnoDB row formats |
| BIT widths | 1, 4, 8, 11, 16, 24, 32, 40, 48, 56, 63, 64 (11 upgrade pairs) |

Excluded factors remain excluded: floating point, temporal types, `ENUM`/`SET`, JSON, spatial, vector, FULLTEXT, SPATIAL, backup/recovery, crash injection, and concurrency. This batch is a condensed core matrix, not a replacement for the full `TUC`/`TUCX`/`TUCS` matrices.

## Regenerate, verify, and audit

```bash
PYTHONPATH=src .venv312/bin/python tools/generate_type_upgrade_pipeline.py \\
  --output generated/type_upgrade_pipeline_v1

PYTHONPATH=src .venv312/bin/python tools/run_type_upgrade_pipeline.py \\
  --cases generated/type_upgrade_pipeline_v1 \\
  --results generated/type_upgrade_pipeline_v1/local_results.jsonl \\
  --summary generated/type_upgrade_pipeline_v1/local_summary.json \\
  --profile copy

PYTHONPATH=src .venv312/bin/python tools/audit_type_upgrade_pipeline.py \\
  --pipeline generated/type_upgrade_pipeline_v1 \\
  --parent generated/type_upgrade_consistency/cases.jsonl.gz \\
  --parent generated/type_upgrade_consistency_extension_v1/cases.jsonl.gz \\
  --parent generated/type_upgrade_statistics_v1/cases.jsonl.gz
```

The audit checks 50 case IDs, all 150 SQL files, exact expected output, artifact hashes, unique table names, index-name format and per-table uniqueness, no forbidden types, no session statements, parent-batch isolation, local COPY evidence, and 17 required semantic coverage checks.
"""
    (output / "README.md").write_text(readme, encoding="utf-8")
    return manifest
