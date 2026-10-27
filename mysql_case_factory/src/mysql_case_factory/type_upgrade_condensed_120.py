from __future__ import annotations

import gzip
import hashlib
import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Iterable, Sequence

CONDENSED_120_BATCH_ID = "2026-10-27-type-upgrade-condensed-120-v1"
CONDENSED_120_BATCH_KIND = "type_upgrade_condensed_sql"
CONDENSED_120_CASE_PREFIX = "TUCR"
CONDENSED_120_DATABASE = "qa_type_upgrade_condensed_120"
CONDENSED_120_AUTHOR = "yuzhengwen y00938623"
CONDENSED_120_CREATE_AT = "2026-10-27"
CONDENSED_120_FE = "FE2026081100174"

ALGORITHMS = ("INPLACE", "INSTANT")


@dataclass(frozen=True)
class UpgradeColumn:
    name: str
    source_type: str
    target_type: str
    attribute: str = "NULL"
    auto_increment: bool = False
    generated_expression: str | None = None
    generated_type: str | None = None
    stored: bool = False


@dataclass(frozen=True)
class CondensedScenario:
    case_no: int
    description: str
    family: str
    columns: tuple[UpgradeColumn, ...]
    category: str = "core"
    engine: str = "InnoDB"
    row_format: str | None = None
    partition: str | None = None
    index_profile: str = "secondary"
    dependency: str = "none"
    foreign_key_action: str = ""
    chained_types: tuple[str, ...] = ()
    minimal: bool = False

    @property
    def case_id(self) -> str:
        return f"{CONDENSED_120_CASE_PREFIX}-{self.case_no:06d}"

    @property
    def base(self) -> str:
        return f"tucr_{self.case_no:06d}"

    @property
    def inplace_table(self) -> str:
        return f"tab_{self.base}_inplace"

    @property
    def instant_table(self) -> str:
        return f"tab_{self.base}_instant"

    @property
    def reference_table(self) -> str:
        return f"tab_{self.base}_ref"

    @property
    def parent_inplace_table(self) -> str:
        return f"tab_{self.base}_parent_inplace"

    @property
    def parent_instant_table(self) -> str:
        return f"tab_{self.base}_parent_instant"

    @property
    def parent_reference_table(self) -> str:
        return f"tab_{self.base}_parent_ref"

    @property
    def index_name(self) -> str:
        return f"idx_{self.base}_target"

    @property
    def unique_name(self) -> str:
        return f"uk_{self.base}_target"

    @property
    def audit_inplace_table(self) -> str:
        return f"tab_{self.base}_audit_inplace"

    @property
    def audit_instant_table(self) -> str:
        return f"tab_{self.base}_audit_instant"

    @property
    def audit_reference_table(self) -> str:
        return f"tab_{self.base}_audit_ref"

    @property
    def view_name(self) -> str:
        return f"v_{self.base}"

    @property
    def trigger_name(self) -> str:
        return f"trg_{self.base}"

    @property
    def function_name(self) -> str:
        return f"fn_{self.base}"

    @property
    def procedure_name(self) -> str:
        return f"pr_{self.base}"

    def to_json(self) -> dict[str, Any]:
        payload = asdict(self)
        payload.update(
            {
                "batch_id": CONDENSED_120_BATCH_ID,
                "batch_kind": CONDENSED_120_BATCH_KIND,
                "case_id": self.case_id,
                "database": CONDENSED_120_DATABASE,
                "algorithms": list(ALGORITHMS),
                "inplace_table": self.inplace_table,
                "instant_table": self.instant_table,
                "reference_table": self.reference_table,
            }
        )
        return payload


def _col(
    source: str,
    target: str,
    *,
    attribute: str = "NULL",
    **kwargs: Any,
) -> UpgradeColumn:
    return UpgradeColumn("target_col", source, target, attribute, **kwargs)


def _scenario(
    case_no: int,
    description: str,
    family: str,
    source: str,
    target: str,
    *,
    attribute: str = "NULL",
    **kwargs: Any,
) -> CondensedScenario:
    return CondensedScenario(
        case_no=case_no,
        description=description,
        family=family,
        columns=(_col(source, target, attribute=attribute),),
        **kwargs,
    )


def condensed_120_scenarios() -> tuple[CondensedScenario, ...]:
    scenarios: list[CondensedScenario] = []

    # Integer: 16 cases.
    scenarios.extend(
        [
            _scenario(1, "Signed TINYINT widening", "integer", "TINYINT", "SMALLINT", attribute="NULL"),
            _scenario(2, "Signed SMALLINT widening with unique index", "integer", "SMALLINT", "MEDIUMINT", attribute="NOT NULL", index_profile="unique"),
            _scenario(3, "Signed MEDIUMINT widening with composite index", "integer", "MEDIUMINT", "INT", attribute="NOT NULL DEFAULT 0", index_profile="composite"),
            _scenario(4, "Signed INT widening with descending index", "integer", "INT", "BIGINT", attribute="NOT NULL COMMENT 'target column'", index_profile="descending"),
            _scenario(5, "Unsigned TINYINT widening", "integer", "TINYINT UNSIGNED", "SMALLINT UNSIGNED", attribute="NOT NULL"),
            _scenario(6, "Unsigned SMALLINT widening with functional index", "integer", "SMALLINT UNSIGNED", "INT UNSIGNED", attribute="NOT NULL", index_profile="functional"),
            _scenario(7, "Unsigned MEDIUMINT widening with unique index", "integer", "MEDIUMINT UNSIGNED", "INT UNSIGNED", attribute="NOT NULL", index_profile="unique"),
            _scenario(8, "Unsigned INT widening", "integer", "INT UNSIGNED", "BIGINT UNSIGNED", attribute="NOT NULL"),
            _scenario(9, "BIGINT same-type control", "integer", "BIGINT", "BIGINT", attribute="NULL"),
            _scenario(10, "BIGINT UNSIGNED same-type control", "integer", "BIGINT UNSIGNED", "BIGINT UNSIGNED", attribute="NOT NULL"),
            _scenario(11, "TINYINT widening with expression default", "integer", "TINYINT", "SMALLINT", attribute="NOT NULL DEFAULT (1+1)"),
            _scenario(12, "SMALLINT widening with column comment", "integer", "SMALLINT", "INT", attribute="NOT NULL COMMENT 'condensed comment'"),
            _scenario(13, "INT widening with invisible column", "integer", "INT", "BIGINT", attribute="NOT NULL INVISIBLE"),
            _scenario(14, "TINYINT widening with FIRST position", "integer", "TINYINT", "SMALLINT", attribute="NULL", category="position"),
            _scenario(15, "SMALLINT widening with AFTER id position", "integer", "SMALLINT", "INT", attribute="NULL", category="position"),
            _scenario(16, "INT widening with NOT NULL and no default", "integer", "INT", "BIGINT", attribute="NOT NULL"),
        ]
    )

    # Decimal: 10 cases.
    decimal_specs = [
        (17, "DECIMAL minimum precision expansion", "DECIMAL(1,0)", "DECIMAL(2,0)", "NULL", "secondary"),
        (18, "DECIMAL common precision expansion", "DECIMAL(5,2)", "DECIMAL(10,2)", "NOT NULL DEFAULT 0.00", "secondary"),
        (19, "DECIMAL medium precision expansion", "DECIMAL(10,2)", "DECIMAL(18,2)", "NULL", "unique"),
        (20, "DECIMAL high scale expansion", "DECIMAL(18,6)", "DECIMAL(28,6)", "NOT NULL", "secondary"),
        (21, "DECIMAL higher scale expansion", "DECIMAL(28,10)", "DECIMAL(38,10)", "NULL", "composite"),
        (22, "DECIMAL near maximum precision", "DECIMAL(38,18)", "DECIMAL(50,18)", "NOT NULL", "secondary"),
        (23, "DECIMAL maximum precision expansion", "DECIMAL(50,30)", "DECIMAL(65,30)", "NOT NULL", "secondary"),
        (24, "DECIMAL maximum precision control", "DECIMAL(65,30)", "DECIMAL(65,30)", "NULL", "secondary"),
        (25, "Integer DECIMAL expansion", "DECIMAL(10,0)", "DECIMAL(20,0)", "NOT NULL", "secondary"),
        (26, "DECIMAL to NUMERIC alias normalization", "DECIMAL(18,6)", "NUMERIC(19,6)", "NOT NULL", "secondary"),
    ]
    scenarios.extend(
        _scenario(no, desc, "decimal", source, target, attribute=attr, index_profile=index)
        for no, desc, source, target, attr, index in decimal_specs
    )

    # BIT: 10 cases.
    bit_specs = [
        (27, "BIT(1) widening", "BIT(1)", "BIT(2)"),
        (28, "BIT(2) widening", "BIT(2)", "BIT(4)"),
        (29, "BIT(4) widening", "BIT(4)", "BIT(8)"),
        (30, "BIT(8) widening", "BIT(8)", "BIT(16)"),
        (31, "BIT(16) widening", "BIT(16)", "BIT(24)"),
        (32, "BIT(24) widening", "BIT(24)", "BIT(32)"),
        (33, "BIT(32) widening", "BIT(32)", "BIT(40)"),
        (34, "BIT(40) widening", "BIT(40)", "BIT(48)"),
        (35, "BIT(48) widening", "BIT(48)", "BIT(56)"),
        (36, "BIT(63) to maximum width", "BIT(63)", "BIT(64)"),
    ]
    scenarios.extend(
        _scenario(no, desc, "bit", source, target, attribute="NOT NULL")
        for no, desc, source, target in bit_specs
    )

    # Character: 12 cases.
    character_specs = [
        (37, "CHAR(0) to CHAR(1)", "CHAR(0)", "CHAR(1)", "NULL", "none"),
        (38, "CHAR(1) expansion", "CHAR(1)", "CHAR(2)", "NOT NULL", "secondary"),
        (39, "CHAR(10) expansion with unique index", "CHAR(10)", "CHAR(20)", "NOT NULL", "unique"),
        (40, "CHAR(50) expansion", "CHAR(50)", "CHAR(100)", "NULL", "secondary"),
        (41, "CHAR(100) expansion with composite index", "CHAR(100)", "CHAR(200)", "NOT NULL", "composite"),
        (42, "CHAR(255) crossing 256", "CHAR(255)", "VARCHAR(256)", "NULL", "secondary"),
        (43, "VARCHAR(0) to VARCHAR(1)", "VARCHAR(0)", "VARCHAR(1)", "NULL", "none"),
        (44, "VARCHAR(1) expansion with unique index", "VARCHAR(1)", "VARCHAR(2)", "NOT NULL", "unique"),
        (45, "VARCHAR(10) expansion", "VARCHAR(10)", "VARCHAR(20)", "NULL", "secondary"),
        (46, "VARCHAR(60) expansion with prefix index", "VARCHAR(60)", "VARCHAR(100)", "NOT NULL", "prefix"),
        (47, "VARCHAR(255) crossing 256 with unique index", "VARCHAR(255)", "VARCHAR(256)", "NOT NULL", "unique"),
        (48, "VARCHAR(512) expansion", "VARCHAR(512)", "VARCHAR(1024)", "NULL", "prefix"),
    ]
    scenarios.extend(
        _scenario(no, desc, "character", source, target, attribute=attr, index_profile=index)
        for no, desc, source, target, attr, index in character_specs
    )

    # Binary: 12 cases.
    binary_specs = [
        (49, "BINARY(0) to BINARY(1)", "BINARY(0)", "BINARY(1)", "NULL", "none"),
        (50, "BINARY(1) expansion", "BINARY(1)", "BINARY(2)", "NOT NULL", "secondary"),
        (51, "BINARY(10) expansion with unique index", "BINARY(10)", "BINARY(20)", "NOT NULL", "unique"),
        (52, "BINARY(50) expansion", "BINARY(50)", "BINARY(100)", "NULL", "secondary"),
        (53, "BINARY(100) expansion with composite index", "BINARY(100)", "BINARY(200)", "NOT NULL", "composite"),
        (54, "BINARY(255) crossing 256", "BINARY(255)", "VARBINARY(256)", "NULL", "secondary"),
        (55, "VARBINARY(0) to VARBINARY(1)", "VARBINARY(0)", "VARBINARY(1)", "NULL", "none"),
        (56, "VARBINARY(1) expansion with unique index", "VARBINARY(1)", "VARBINARY(2)", "NOT NULL", "unique"),
        (57, "VARBINARY(10) expansion", "VARBINARY(10)", "VARBINARY(20)", "NULL", "secondary"),
        (58, "VARBINARY(60) expansion with prefix index", "VARBINARY(60)", "VARBINARY(100)", "NOT NULL", "prefix"),
        (59, "VARBINARY(255) crossing 256 with unique index", "VARBINARY(255)", "VARBINARY(256)", "NOT NULL", "unique"),
        (60, "VARBINARY(512) expansion", "VARBINARY(512)", "VARBINARY(1024)", "NULL", "secondary"),
    ]
    scenarios.extend(
        _scenario(no, desc, "binary", source, target, attribute=attr, index_profile=index)
        for no, desc, source, target, attr, index in binary_specs
    )

    # TEXT/BLOB: 8 cases.
    text_blob_specs = [
        (61, "TINYTEXT to TEXT", "TINYTEXT", "TEXT", "NULL", "prefix"),
        (62, "TEXT to MEDIUMTEXT", "TEXT", "MEDIUMTEXT", "NULL", "prefix"),
        (63, "MEDIUMTEXT to LONGTEXT", "MEDIUMTEXT", "LONGTEXT", "NULL", "prefix"),
        (64, "TINYBLOB to BLOB", "TINYBLOB", "BLOB", "NULL", "prefix"),
        (65, "BLOB to MEDIUMBLOB", "BLOB", "MEDIUMBLOB", "NULL", "prefix"),
        (66, "MEDIUMBLOB to LONGBLOB", "MEDIUMBLOB", "LONGBLOB", "NULL", "prefix"),
        (67, "VARCHAR row-size overflow to TEXT", "VARCHAR(16307)", "TEXT", "NULL", "prefix"),
        (68, "VARBINARY row-size overflow to BLOB", "VARBINARY(65231)", "BLOB", "NULL", "prefix"),
    ]
    scenarios.extend(
        _scenario(no, desc, "text_blob", source, target, attribute=attr, index_profile=index, minimal=True, row_format="DYNAMIC")
        for no, desc, source, target, attr, index in text_blob_specs
    )

    # Zero-length cross-family: 10 cases.
    zero_specs = [
        (69, "CHAR(0) to BINARY(1)", "CHAR(0)", "BINARY(1)", "NULL"),
        (70, "BINARY(0) to CHAR(1)", "BINARY(0)", "CHAR(1)", "NULL"),
        (71, "VARCHAR(0) to CHAR(1)", "VARCHAR(0)", "CHAR(1)", "NULL"),
        (72, "VARBINARY(0) to BINARY(1)", "VARBINARY(0)", "BINARY(1)", "NULL"),
        (73, "NCHAR(0) to NCHAR(1)", "NCHAR(0)", "NCHAR(1)", "NULL"),
        (74, "NVARCHAR(0) to NVARCHAR(1)", "NVARCHAR(0)", "NVARCHAR(1)", "NULL"),
        (75, "CHARACTER(0) to CHARACTER(1)", "CHARACTER(0)", "CHARACTER(1)", "NULL"),
        (76, "CHARACTER VARYING(0) to CHARACTER VARYING(1)", "CHARACTER VARYING(0)", "CHARACTER VARYING(1)", "NULL"),
        (77, "CHAR(0) to TEXT", "CHAR(0)", "TEXT", "NULL"),
        (78, "BINARY(0) to BLOB", "BINARY(0)", "BLOB", "NULL"),
    ]
    scenarios.extend(
        _scenario(no, desc, "zero_length", source, target, attribute=attr, minimal=True, index_profile="none")
        for no, desc, source, target, attr in zero_specs
    )

    # Auto-increment primary key: 6 cases.
    auto_specs = [
        (79, "TINYINT auto-increment primary key widening", "TINYINT", "SMALLINT"),
        (80, "SMALLINT auto-increment primary key widening", "SMALLINT", "INT"),
        (81, "MEDIUMINT auto-increment primary key widening", "MEDIUMINT", "BIGINT"),
        (82, "INT auto-increment primary key widening", "INT", "BIGINT"),
        (83, "BIGINT auto-increment primary key control", "BIGINT", "BIGINT"),
        (84, "INT UNSIGNED auto-increment primary key widening", "INT UNSIGNED", "BIGINT UNSIGNED"),
    ]
    for no, desc, source, target in auto_specs:
        scenarios.append(
            CondensedScenario(
                case_no=no,
                description=desc,
                family="integer",
                columns=(
                    UpgradeColumn(
                        "target_col",
                        source,
                        target,
                        "NOT NULL AUTO_INCREMENT",
                        auto_increment=True,
                    ),
                ),
                category="auto_increment",
                index_profile="primary",
            )
        )

    # Foreign key: 8 cases.
    fk_specs = [
        (85, "SMALLINT foreign key RESTRICT", "SMALLINT", "INT", "RESTRICT"),
        (86, "SMALLINT foreign key NO ACTION", "SMALLINT", "INT", "NO ACTION"),
        (87, "MEDIUMINT foreign key CASCADE", "MEDIUMINT", "BIGINT", "CASCADE"),
        (88, "INT foreign key SET NULL", "INT", "BIGINT", "SET NULL"),
        (89, "CHAR(10) foreign key RESTRICT", "CHAR(10)", "CHAR(20)", "RESTRICT"),
        (90, "VARCHAR(60) foreign key CASCADE", "VARCHAR(60)", "VARCHAR(100)", "CASCADE"),
        (91, "BINARY(10) foreign key RESTRICT", "BINARY(10)", "BINARY(20)", "RESTRICT"),
        (92, "VARBINARY(10) foreign key SET NULL", "VARBINARY(10)", "VARBINARY(20)", "SET NULL"),
    ]
    for no, desc, source, target, action in fk_specs:
        attr = "NULL" if action == "SET NULL" else "NOT NULL"
        scenarios.append(
            _scenario(
                no,
                desc,
                "foreign_key",
                source,
                target,
                attribute=attr,
                category="foreign_key",
                foreign_key_action=action,
            )
        )

    # Dependencies and generated/function objects: 8 cases.
    dependency_specs = [
        (93, "Virtual generated column depends on base column", "INT", "BIGINT", "virtual_generated"),
        (94, "Stored generated column depends on base column", "INT", "BIGINT", "stored_generated"),
        (95, "Functional index depends on base column", "VARCHAR(60)", "VARCHAR(100)", "functional_index"),
        (96, "View depends on base column", "DECIMAL(10,2)", "DECIMAL(18,2)", "view"),
        (97, "Trigger depends on base column", "VARBINARY(32)", "VARBINARY(128)", "trigger"),
        (98, "Stored function depends on base column", "BIT(16)", "BIT(32)", "function"),
        (99, "Stored procedure depends on base column", "INT", "BIGINT", "procedure"),
        (100, "Prepared statement depends on base column", "VARCHAR(32)", "VARCHAR(128)", "prepared"),
    ]
    for no, desc, source, target, dependency in dependency_specs:
        attr = "NULL" if dependency in {"virtual_generated", "stored_generated"} else "NOT NULL"
        scenarios.append(
            _scenario(
                no,
                desc,
                "dependency",
                source,
                target,
                attribute=attr,
                category="dependency",
                dependency=dependency,
            )
        )

    # Table forms: 10 cases.
    table_form_specs = [
        (101, "InnoDB DYNAMIC row format", "INT", "BIGINT", "InnoDB", "DYNAMIC", None, "secondary"),
        (102, "InnoDB COMPACT row format crossing 256", "VARCHAR(255)", "VARCHAR(256)", "InnoDB", "COMPACT", None, "prefix"),
        (103, "InnoDB COMPRESSED row format crossing 256", "VARBINARY(255)", "VARBINARY(256)", "InnoDB", "COMPRESSED", None, "secondary"),
        (104, "InnoDB REDUNDANT row format", "CHAR(100)", "CHAR(200)", "InnoDB", "REDUNDANT", None, "prefix"),
        (105, "RANGE partitioned table", "INT", "BIGINT", "InnoDB", "DYNAMIC", "range", "secondary"),
        (106, "LIST partitioned table", "VARCHAR(64)", "VARCHAR(128)", "InnoDB", "DYNAMIC", "list", "secondary"),
        (107, "HASH partitioned table", "SMALLINT", "INT", "InnoDB", "DYNAMIC", "hash", "secondary"),
        (108, "KEY partitioned table", "INT", "BIGINT", "InnoDB", "DYNAMIC", "key", "secondary"),
        (109, "MyISAM table", "CHAR(16)", "CHAR(32)", "MyISAM", None, None, "secondary"),
        (110, "MEMORY table", "VARCHAR(63)", "VARCHAR(64)", "MEMORY", None, None, "secondary"),
    ]
    for no, desc, source, target, engine, row_format, partition, index_profile in table_form_specs:
        scenarios.append(
            _scenario(
                no,
                desc,
                "table_form",
                source,
                target,
                attribute="NOT NULL" if partition in {"range", "hash", "key"} else "NULL",
                engine=engine,
                row_format=row_format,
                partition=partition,
                index_profile=index_profile,
                category="table_form",
            )
        )

    # Chain, multi-column, and statistics-related metadata: 10 cases.
    scenarios.extend(
        [
            CondensedScenario(
                case_no=111,
                description="Chained SMALLINT to INT to BIGINT",
                family="integer",
                columns=(_col("SMALLINT", "BIGINT", attribute="NOT NULL"),),
                chained_types=("INT", "BIGINT"),
                category="chain",
            ),
            CondensedScenario(
                case_no=112,
                description="Multi-column simultaneous upgrade",
                family="multi_column",
                columns=(
                    UpgradeColumn("int_col", "INT", "BIGINT", "NOT NULL"),
                    UpgradeColumn("char_col", "VARCHAR(60)", "VARCHAR(120)", "NULL"),
                    UpgradeColumn("binary_col", "VARBINARY(60)", "VARBINARY(120)", "NULL"),
                ),
                category="multi_column",
                index_profile="composite",
            ),
            _scenario(113, "Table statistics metadata after upgrade", "integer", "INT", "BIGINT", attribute="NOT NULL", category="statistics", index_profile="secondary"),
            _scenario(114, "Index statistics metadata after upgrade", "integer", "SMALLINT", "INT", attribute="NOT NULL", category="statistics", index_profile="secondary"),
            _scenario(115, "Partition statistics metadata after upgrade", "character", "VARCHAR(64)", "VARCHAR(128)", attribute="NOT NULL", category="statistics", partition="list"),
            _scenario(116, "EXPLAIN uses expected index after upgrade", "integer", "INT", "BIGINT", attribute="NOT NULL", category="statistics", index_profile="secondary"),
            _scenario(117, "All dependency objects combined", "integer", "SMALLINT", "BIGINT", attribute="NOT NULL", category="dependency", dependency="all"),
            CondensedScenario(
                case_no=118,
                description="Composite unique index after multi-column upgrade",
                family="multi_column",
                columns=(
                    UpgradeColumn("int_col", "INT", "BIGINT", "NOT NULL"),
                    UpgradeColumn("char_col", "VARCHAR(60)", "VARCHAR(120)", "NOT NULL"),
                ),
                category="multi_column",
                index_profile="composite_unique",
            ),
            CondensedScenario(
                case_no=119,
                description="Composite prefix index after multi-column upgrade",
                family="multi_column",
                columns=(
                    UpgradeColumn("char_col", "VARCHAR(255)", "VARCHAR(512)", "NOT NULL"),
                    UpgradeColumn("binary_col", "VARBINARY(255)", "VARBINARY(512)", "NOT NULL"),
                ),
                category="multi_column",
                index_profile="composite_prefix",
            ),
            CondensedScenario(
                case_no=120,
                description="Composite descending index after multi-column upgrade",
                family="multi_column",
                columns=(
                    UpgradeColumn("int_col", "INT", "BIGINT", "NOT NULL"),
                    UpgradeColumn("char_col", "VARCHAR(60)", "VARCHAR(120)", "NOT NULL"),
                ),
                category="multi_column",
                index_profile="composite_descending",
            ),
        ]
    )

    if len(scenarios) != 120:
        raise AssertionError(f"expected 120 scenarios, got {len(scenarios)}")
    if [s.case_no for s in scenarios] != list(range(1, 121)):
        raise AssertionError("scenario numbering is not contiguous")
    return tuple(scenarios)


def _type_length(type_name: str) -> int:
    match = re.search(r"\((\d+)", type_name.upper())
    if match:
        return int(match.group(1))
    upper = type_name.upper()
    if upper in {"TINYTEXT", "TINYBLOB"}:
        return 255
    if upper in {"TEXT", "BLOB"}:
        return 65_535
    if upper in {"MEDIUMTEXT", "MEDIUMBLOB"}:
        return 16_777_215
    if upper in {"LONGTEXT", "LONGBLOB"}:
        return 4_294_967_295
    if upper.startswith("CHAR") or upper.startswith("BINARY") or upper.startswith("NCHAR"):
        return 1
    if upper.startswith("VARCHAR") or upper.startswith("VARBINARY") or upper.startswith("NVARCHAR"):
        return 1
    if upper.startswith("BIT"):
        return 1
    return 0


def _integer_bounds(type_name: str) -> tuple[int, int]:
    unsigned = "UNSIGNED" in type_name.upper()
    base = type_name.upper().replace(" UNSIGNED", "")
    signed = {
        "TINYINT": (-128, 127),
        "SMALLINT": (-32768, 32767),
        "MEDIUMINT": (-8388608, 8388607),
        "INT": (-2147483648, 2147483647),
        "BIGINT": (-(2**63), 2**63 - 1),
    }[base]
    unsigned_max = {
        "TINYINT": 255,
        "SMALLINT": 65535,
        "MEDIUMINT": 16777215,
        "INT": 4294967295,
        "BIGINT": 2**64 - 1,
    }[base]
    return (0, unsigned_max) if unsigned else signed


def _decimal_extreme(type_name: str, *, negative: bool) -> str:
    match = re.search(r"\((\d+),(\d+)\)", type_name.upper())
    if not match:
        return "-9999999999" if negative else "9999999999"
    precision, scale = int(match.group(1)), int(match.group(2))
    digits = "9" * (precision - scale) + ("." + "9" * scale if scale else "")
    return ("-" + digits) if negative else digits


def _bit_literal(width: int, value: int) -> str:
    if width <= 0:
        width = 1
    return f"b'{value & ((1 << width) - 1):0{width}b}'"


def _text_repeat(prefix: str, length: int, character: str) -> str:
    if length <= 0:
        return "''" if prefix == "char" else "x''"
    return f"REPEAT('{character}', {length})"


def _binary_repeat(length: int, byte: str) -> str:
    if length <= 0:
        return "x''"
    return f"REPEAT(x'{byte}', {length})"


def _literal(type_name: str, row_no: int, *, target: bool, nullable: bool) -> str:
    upper = type_name.upper()
    if upper.startswith(("TINYINT", "SMALLINT", "MEDIUMINT", "INT", "BIGINT")):
        minimum, maximum = _integer_bounds(type_name)
        if row_no == 1:
            return "0"
        if row_no == 2:
            return str(maximum)
        if row_no == 3:
            return str(max(maximum - 1, minimum) if minimum == 0 else minimum)
        if row_no == 4:
            return "NULL" if nullable else "2"
        if row_no == 5:
            return "1"
        if row_no == 6:
            return str(maximum if target else maximum)
        if row_no == 7:
            return str(max(maximum - 2, minimum))
        if row_no == 8:
            return "2"
        raise AssertionError(row_no)
    if upper.startswith(("DECIMAL", "NUMERIC")):
        if row_no == 1:
            return "0"
        if row_no == 2:
            return _decimal_extreme(type_name, negative=False)
        if row_no == 3:
            return _decimal_extreme(type_name, negative=True)
        if row_no == 4:
            return "NULL" if nullable else "2"
        if row_no == 5:
            return "1"
        if row_no == 6:
            return _decimal_extreme(type_name, negative=False)
        if row_no == 7:
            return _decimal_extreme(type_name, negative=True)
        if row_no == 8:
            return "2"
        raise AssertionError(row_no)
    if upper.startswith("BIT"):
        width = _type_length(type_name)
        maximum = (1 << width) - 1
        values = [0, maximum, 0, 0 if nullable else 0, 1, maximum, max(maximum - 1, 0), 2]
        return "NULL" if row_no == 4 and nullable else _bit_literal(width, values[row_no - 1])
    if upper.startswith(("CHAR", "VARCHAR", "NCHAR", "NVARCHAR", "CHARACTER")):
        length = _type_length(type_name)
        if length == 0:
            return "NULL" if row_no == 4 and nullable else "''"
        if row_no == 1:
            return "'a'"
        if row_no == 2:
            return _text_repeat("char", length, "b")
        if row_no == 3:
            return _text_repeat("char", length, "c")
        if row_no == 4:
            return "NULL" if nullable else "''"
        if row_no == 5:
            return _text_repeat("char", length, "d")
        if row_no == 6:
            return _text_repeat("char", length, "e")
        if row_no == 7:
            return _text_repeat("char", max(length - 1, 0), "f")
        if row_no == 8:
            return "'g'"
        raise AssertionError(row_no)
    if upper.startswith(("BINARY", "VARBINARY")) or upper.endswith("BLOB"):
        length = _type_length(type_name)
        if length == 0:
            return "NULL" if row_no == 4 and nullable else "x''"
        length = min(length, 4096)
        if row_no == 1:
            return "x'01'"
        if row_no == 2:
            return _binary_repeat(length, "02")
        if row_no == 3:
            return _binary_repeat(length, "03")
        if row_no == 4:
            return "NULL" if nullable else "x''"
        if row_no == 5:
            return _binary_repeat(length, "04")
        if row_no == 6:
            return _binary_repeat(length, "05")
        if row_no == 7:
            return _binary_repeat(max(length - 1, 0), "06")
        if row_no == 8:
            return "x'07'"
        raise AssertionError(row_no)
    if upper.endswith("TEXT"):
        length = min(_type_length(type_name), 4096)
        if row_no == 1:
            return "'a'"
        if row_no == 2:
            return _text_repeat("char", length, "b")
        if row_no == 3:
            return _text_repeat("char", max(length // 2, 0), "c")
        if row_no == 4:
            return "NULL" if nullable else "''"
        if row_no == 5:
            return _text_repeat("char", max(length // 3, 0), "d")
        if row_no == 6:
            return _text_repeat("char", length, "e")
        if row_no == 7:
            return _text_repeat("char", max(length - 1, 0), "f")
        if row_no == 8:
            return "'g'"
        raise AssertionError(row_no)
    raise AssertionError(type_name)


def _attribute_for_ddl(column: UpgradeColumn) -> str:
    return column.attribute


def _column_definition(column: UpgradeColumn, *, target: bool) -> str:
    type_name = column.target_type if target else column.source_type
    return f"`{column.name}` {type_name} {_attribute_for_ddl(column)}"


def _index_sql(scenario: CondensedScenario, table: str) -> str:
    profile = scenario.index_profile
    if profile == "none":
        return ""
    if profile == "primary":
        return f"PRIMARY KEY (`target_col`)"
    if profile == "secondary":
        return f"KEY `{scenario.index_name}` (`target_col`)"
    if profile == "unique":
        return f"UNIQUE KEY `{scenario.unique_name}` (`target_col`)"
    if profile == "composite":
        first = scenario.columns[0].name
        return f"KEY `{scenario.index_name}` (`{first}`, `canary_int`)"
    if profile == "descending":
        return f"KEY `{scenario.index_name}` (`target_col` DESC)"
    if profile == "prefix":
        length = min(_type_length(scenario.columns[0].source_type), 32) or 1
        return f"KEY `{scenario.index_name}` (`target_col`({max(length, 1)}))"
    if profile == "functional":
        return f"KEY `{scenario.index_name}` ((`target_col` + 0))"
    if profile == "composite_unique":
        return f"UNIQUE KEY `{scenario.unique_name}` (`{scenario.columns[0].name}`, `{scenario.columns[1].name}`)"
    if profile == "composite_prefix":
        return f"KEY `{scenario.index_name}` (`{scenario.columns[0].name}`(32), `{scenario.columns[1].name}`(32))"
    if profile == "composite_descending":
        return f"KEY `{scenario.index_name}` (`{scenario.columns[0].name}` DESC, `{scenario.columns[1].name}` DESC)"
    raise AssertionError(profile)


def _partition_sql(scenario: CondensedScenario) -> str:
    if scenario.partition == "range":
        return "\nPARTITION BY RANGE (`target_col`) (\n  PARTITION p0 VALUES LESS THAN (0),\n  PARTITION p1 VALUES LESS THAN MAXVALUE\n)"
    if scenario.partition == "list":
        return "\nPARTITION BY LIST (`id`) (\n  PARTITION p0 VALUES IN (1, 2, 3, 4),\n  PARTITION p1 VALUES IN (5, 6, 7, 8)\n)"
    if scenario.partition == "hash":
        return "\nPARTITION BY HASH (`target_col`) PARTITIONS 2"
    if scenario.partition == "key":
        return "\nPARTITION BY KEY (`target_col`) PARTITIONS 2"
    return ""


def _table_options(scenario: CondensedScenario) -> str:
    options = [f"ENGINE={scenario.engine}"]
    if scenario.row_format:
        options.append(f"ROW_FORMAT={scenario.row_format}")
    options.append("DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci")
    return " ".join(options)


def _create_table_sql(
    scenario: CondensedScenario,
    table: str,
    *,
    target: bool,
    parent: bool = False,
    parent_table: str | None = None,
) -> str:
    columns = ["`id` BIGINT NOT NULL"]
    if parent:
        columns.append(_column_definition(scenario.columns[0], target=target))
        columns.append("`payload` VARCHAR(64) NOT NULL")
        columns.append("PRIMARY KEY (`id`)")
        columns.append(f"UNIQUE KEY `uk_{scenario.base}_parent` (`target_col`)")
        return f"CREATE TABLE `{table}` (\n  " + ",\n  ".join(columns) + "\n) " + _table_options(scenario) + ";"
    if scenario.columns[0].auto_increment:
        columns.append(_column_definition(scenario.columns[0], target=target))
        columns.extend([
            "`canary_int` BIGINT NULL",
            "`canary_varchar` VARCHAR(64) NULL",
            "`canary_varbinary` VARBINARY(64) NULL",
            "`canary_decimal` DECIMAL(20,4) NULL",
        ])
        columns.append("PRIMARY KEY (`id`)")
        columns.append(f"UNIQUE KEY `{scenario.unique_name}` (`target_col`)")
    else:
        for column in scenario.columns:
            columns.append(_column_definition(column, target=target))
        if not scenario.minimal:
            columns.extend(
                [
                    "`canary_int` BIGINT NULL",
                    "`canary_varchar` VARCHAR(64) NULL",
                    "`canary_varbinary` VARBINARY(64) NULL",
                    "`canary_decimal` DECIMAL(20,4) NULL",
                ]
            )
        if scenario.partition in {"range", "hash", "key"}:
            columns.append("PRIMARY KEY (`id`, `target_col`)")
        else:
            columns.append("PRIMARY KEY (`id`)")
        if scenario.foreign_key_action and parent_table:
            action_sql = {
                "RESTRICT": "ON DELETE RESTRICT ON UPDATE RESTRICT",
                "NO ACTION": "ON DELETE NO ACTION ON UPDATE NO ACTION",
                "CASCADE": "ON DELETE CASCADE ON UPDATE CASCADE",
                "SET NULL": "ON DELETE SET NULL ON UPDATE SET NULL",
            }[scenario.foreign_key_action]
            columns.append(
                f"CONSTRAINT `fk_{scenario.base}_{table}` FOREIGN KEY (`target_col`) "
                f"REFERENCES `{parent_table}` (`target_col`) {action_sql}"
            )
        if scenario.dependency in {"virtual_generated", "stored_generated"}:
            stored = "STORED" if scenario.dependency == "stored_generated" else "VIRTUAL"
            columns.append(f"`gen` DECIMAL(65,0) AS (CAST(`target_col` AS DECIMAL(65,0)) + 1) {stored}")
        index_sql = _index_sql(scenario, table)
        if index_sql:
            columns.append(index_sql)
    return f"CREATE TABLE `{table}` (\n  " + ",\n  ".join(columns) + "\n) " + _table_options(scenario) + _partition_sql(scenario) + ";"


def _insert_rows_sql(
    scenario: CondensedScenario,
    table: str,
    *,
    target: bool,
    rows: Sequence[int],
) -> str:
    omit_auto_values = bool(scenario.columns[0].auto_increment and any(row_no > 5 for row_no in rows))
    columns = ["`id`"] + [
        f"`{column.name}`" for column in scenario.columns if not (omit_auto_values and column.auto_increment)
    ]
    if not scenario.minimal:
        columns.extend(["`canary_int`", "`canary_varchar`", "`canary_varbinary`", "`canary_decimal`"])
    quoted = ", ".join(columns)
    row_sql: list[str] = []
    for row_no in rows:
        row_values: list[str] = [str(row_no)]
        for column in scenario.columns:
            if column.auto_increment:
                if row_no in {6, 7, 8}:
                    continue
                row_values.append(str(row_no))
                continue
            type_name = column.target_type if target else column.source_type
            nullable = not column.attribute.upper().startswith("NOT NULL")
            row_values.append(_literal(type_name, row_no, target=target, nullable=nullable))
        if not scenario.minimal:
            row_values.extend([str(row_no), f"'c{row_no}'", f"x'{row_no % 256:02x}'", f"{row_no}.0000"])
        row_sql.append("(" + ", ".join(row_values) + ")")
    return f"INSERT INTO `{table}` ({quoted}) VALUES\n  " + ",\n  ".join(row_sql) + ";"
def _update_literal(type_name: str, row_no: int) -> str:
    upper = type_name.upper()
    if upper.startswith(("TINYINT", "SMALLINT", "MEDIUMINT", "INT", "BIGINT")):
        return str(row_no + 2)
    if upper.startswith(("DECIMAL", "NUMERIC")):
        return str(row_no + 2)
    if upper.startswith("BIT"):
        width = _type_length(type_name)
        maximum = (1 << width) - 1
        return _bit_literal(width, row_no + 2)
    if upper.startswith(("BINARY", "VARBINARY")) or upper.endswith("BLOB"):
        return f"x'{row_no + 16:02x}'"
    return "'" + chr(ord('x') + row_no - 1) + "'"


def _insert_parent_rows_sql(
    scenario: CondensedScenario,
    table: str,
    *,
    target: bool,
    rows: Sequence[int],
) -> str:
    row_sql: list[str] = []
    column = scenario.columns[0]
    for row_no in rows:
        type_name = column.target_type if target else column.source_type
        nullable = not column.attribute.upper().startswith("NOT NULL")
        row_sql.append(f"({row_no}, {_literal(type_name, row_no, target=target, nullable=nullable)}, 'p{row_no}')")
    return f"INSERT INTO `{table}` (`id`, `target_col`, `payload`) VALUES\n  " + ",\n  ".join(row_sql) + ";"


def _update_parent_rows_sql(
    scenario: CondensedScenario,
    table: str,
    *,
    target: bool,
) -> str:
    column = scenario.columns[0]
    type_name = column.target_type if target else column.source_type
    assignments = [
        f"`target_col` = CASE `id` WHEN 1 THEN {_update_literal(type_name, 1)} WHEN 3 THEN {_update_literal(type_name, 3)} ELSE `target_col` END"
    ]
    return f"UPDATE `{table}` SET {', '.join(assignments)} WHERE `id` IN (1, 3, 5);"


def _reinsert_parent_sql(
    scenario: CondensedScenario,
    table: str,
    *,
    target: bool,
) -> str:
    return _insert_parent_rows_sql(scenario, table, target=target, rows=(8,))


def _update_rows_sql(
    scenario: CondensedScenario,
    table: str,
    *,
    target: bool,
) -> str:
    assignments: list[str] = []
    for column in scenario.columns:
        type_name = column.target_type if target else column.source_type
        nullable = not column.attribute.upper().startswith("NOT NULL")
        if column.auto_increment:
            continue
        assignments.append(f"`{column.name}` = CASE `id` WHEN 1 THEN {_update_literal(type_name, 1)} WHEN 3 THEN {_update_literal(type_name, 3)} ELSE `{column.name}` END")
    if not scenario.minimal:
        assignments.append("`canary_int` = `canary_int` + 100")
    return f"UPDATE `{table}` SET {', '.join(assignments)} WHERE `id` IN (1, 3, 5);"


def _delete_rows_sql(table: str, parent_table: str | None = None, action: str = "") -> str:
    if parent_table and action in {"CASCADE", "SET NULL"}:
        return f"DELETE FROM `{parent_table}` WHERE `id` IN (2, 4);"
    if parent_table and action in {"RESTRICT", "NO ACTION"}:
        return f"DELETE FROM `{table}` WHERE `id` IN (2, 4);\nDELETE FROM `{parent_table}` WHERE `id` IN (2, 4);"
    return f"DELETE FROM `{table}` WHERE `id` IN (2, 4);"


def _reinsert_sql(
    scenario: CondensedScenario,
    table: str,
    *,
    target: bool,
) -> str:
    return _insert_rows_sql(scenario, table, target=target, rows=(8,))


def _ddl_sql(
    scenario: CondensedScenario,
    table: str,
    algorithm: str,
) -> tuple[str, ...]:
    modifications = ", ".join(
        f"MODIFY `{column.name}` {column.target_type} {_attribute_for_ddl(column)}"
        for column in scenario.columns
    )
    if algorithm == "INPLACE":
        suffix = "ALGORITHM=INPLACE, LOCK=NONE"
    elif algorithm == "INSTANT":
        suffix = "ALGORITHM=INSTANT"
    else:
        raise AssertionError(algorithm)
    statements = [f"ALTER TABLE `{table}` {modifications}, {suffix};"]
    if scenario.chained_types:
        intermediate, final = scenario.chained_types
        statements.insert(0, f"ALTER TABLE `{table}` MODIFY `{scenario.columns[0].name}` {intermediate} {_attribute_for_ddl(scenario.columns[0])}, {suffix};")
        statements[-1] = f"ALTER TABLE `{table}` MODIFY `{scenario.columns[0].name}` {final} {_attribute_for_ddl(scenario.columns[0])}, {suffix};"
    return tuple(statements)


def _create_audit_table_sql(scenario: CondensedScenario, table: str) -> str:
    audit_table = f"tab_{scenario.base}_audit_{table.removeprefix(f'tab_{scenario.base}_')}"
    return (
        f"CREATE TABLE `{audit_table}` (\n"
        "  `id` BIGINT NOT NULL,\n"
        "  `canary_int` BIGINT NULL,\n"
        "  PRIMARY KEY (`id`)\n"
        ") ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;"
    )


def _prepared_statement_sql(scenario: CondensedScenario, table: str) -> list[str]:
    statement_name = f"stmt_{scenario.base}_{table}"
    return [
        f"PREPARE `{statement_name}` FROM 'UPDATE `{table}` SET `canary_int` = `id` + 1 WHERE `id` = 1';",
        f"EXECUTE `{statement_name}`;",
        f"DEALLOCATE PREPARE `{statement_name}`;",
    ]


def _dependency_objects_sql(scenario: CondensedScenario, table: str, *, target: bool) -> list[str]:
    objects: list[str] = []
    dependency = scenario.dependency
    if dependency in {"view", "all"}:
        objects.append(f"CREATE VIEW `{scenario.view_name}_{table}` AS SELECT `id`, `target_col` FROM `{table}`;")
    if dependency in {"trigger", "all"}:
        suffix = table.removeprefix(f"tab_{scenario.base}_")
        audit_table = f"tab_{scenario.base}_audit_{suffix}"
        objects.append(
            f"CREATE TRIGGER `{scenario.trigger_name}_{table}` AFTER INSERT ON `{table}` "
            f"FOR EACH ROW INSERT INTO `{audit_table}` VALUES (NEW.`id`, NEW.`canary_int`);"
        )
    if dependency in {"procedure", "all"}:
        objects.append(
            f"CREATE PROCEDURE `{scenario.procedure_name}_{table}`(IN p_id BIGINT) UPDATE `{table}` SET `canary_int` = p_id + 1 WHERE `id` = p_id;"
        )
    if dependency == "prepared":
        objects.append(f"PREPARE stmt_{scenario.base} FROM 'UPDATE `{table}` SET `canary_int` = `id` + 1 WHERE `id` = 1';")
        objects.append(f"EXECUTE stmt_{scenario.base};")
        objects.append(f"DEALLOCATE PREPARE stmt_{scenario.base};")
    return objects


def _schema_diff_sql(scenario: CondensedScenario, candidate: str, reference: str) -> str:
    columns = "column_name, ordinal_position, column_type, is_nullable, column_default, extra, character_set_name, collation_name, column_comment, generation_expression"
    base = (
        f"(SELECT {columns} FROM information_schema.COLUMNS WHERE table_schema=DATABASE() AND table_name='{reference}' "
        f"EXCEPT SELECT {columns} FROM information_schema.COLUMNS WHERE table_schema=DATABASE() AND table_name='{candidate}') "
        f"UNION ALL (SELECT {columns} FROM information_schema.COLUMNS WHERE table_schema=DATABASE() AND table_name='{candidate}' "
        f"EXCEPT SELECT {columns} FROM information_schema.COLUMNS WHERE table_schema=DATABASE() AND table_name='{reference}')"
    )
    return f"SELECT COUNT(*) FROM ({base}) AS schema_diff"


def _data_diff_sql(scenario: CondensedScenario, candidate: str, reference: str) -> tuple[str, str, str]:
    compare_columns = ["`id`"] + [f"`{column.name}`" for column in scenario.columns]
    if not scenario.minimal:
        compare_columns.extend(["`canary_int`", "`canary_varchar`", "`canary_varbinary`", "`canary_decimal`"])
    if scenario.dependency in {"virtual_generated", "stored_generated"}:
        compare_columns.append("`gen`")
    candidate_columns = ", ".join(f"c.{column.strip('`')}" for column in compare_columns)
    reference_columns = ", ".join(f"r.{column.strip('`')}" for column in compare_columns)
    condition = " AND ".join(f"(c.{column.strip('`')} <=> r.{column.strip('`')})" for column in compare_columns)
    mismatch = (
        f"SELECT COUNT(*) FROM `{candidate}` c LEFT JOIN `{reference}` r ON r.`id`=c.`id` "
        f"WHERE r.`id` IS NULL OR NOT ({condition})"
    )
    extra = (
        f"SELECT COUNT(*) FROM `{reference}` r LEFT JOIN `{candidate}` c ON c.`id`=r.`id` "
        "WHERE c.`id` IS NULL"
    )
    row_count = f"SELECT ABS((SELECT COUNT(*) FROM `{candidate}`) - (SELECT COUNT(*) FROM `{reference}`))"
    return mismatch, extra, row_count


def _result_row_sql(
    scenario: CondensedScenario,
    candidate: str,
    reference: str,
    algorithm: str,
) -> str:
    mismatch, extra, row_count = _data_diff_sql(scenario, candidate, reference)
    schema_diff = _schema_diff_sql(scenario, candidate, reference)
    return (
        f"SELECT '{scenario.case_id}' AS case_id, '{algorithm}' AS algorithm, "
        f"({schema_diff}) AS schema_diff_count, ({row_count}) AS row_count_diff, "
        f"({mismatch}) AS mismatch_count, ({extra}) AS extra_count, "
        "CASE WHEN "
        f"({schema_diff})=0 AND ({row_count})=0 AND ({mismatch})=0 AND ({extra})=0 "
        "THEN 'PASS' ELSE 'FAIL' END AS result;"
    )


def _cleanup_sql(scenario: CondensedScenario) -> list[str]:
    objects = [
        scenario.inplace_table,
        scenario.instant_table,
        scenario.reference_table,
    ]
    if scenario.foreign_key_action:
        objects.extend(
            [
                scenario.parent_inplace_table,
                scenario.parent_instant_table,
                scenario.parent_reference_table,
            ]
        )
    if scenario.dependency in {"trigger", "all"}:
        objects.extend(
            [
                scenario.audit_inplace_table,
                scenario.audit_instant_table,
                scenario.audit_reference_table,
            ]
        )
    if scenario.dependency in {"view", "all"}:
        objects.extend(
            [
                f"{scenario.view_name}_{scenario.inplace_table}",
                f"{scenario.view_name}_{scenario.instant_table}",
                f"{scenario.view_name}_{scenario.reference_table}",
            ]
        )
    view_objects = [name for name in objects if name.startswith(f"v_{scenario.base}_")]
    table_objects = [name for name in objects if name not in view_objects]
    statements = [f"DROP TABLE IF EXISTS `{table}`;" for table in table_objects]
    statements.extend(f"DROP VIEW IF EXISTS `{view}`;" for view in view_objects)
    if scenario.dependency in {"trigger", "all"}:
        for table in (scenario.inplace_table, scenario.instant_table, scenario.reference_table):
            statements.append(f"DROP TRIGGER IF EXISTS `{scenario.trigger_name}_{table}`;")
    if scenario.dependency in {"function", "all"}:
        statements.append(f"DROP FUNCTION IF EXISTS `{scenario.function_name}`;")
    if scenario.dependency in {"procedure", "all"}:
        for table in (scenario.inplace_table, scenario.instant_table, scenario.reference_table):
            statements.append(f"DROP PROCEDURE IF EXISTS `{scenario.procedure_name}_{table}`;")
    return statements


def _header(scenario: CondensedScenario) -> str:
    return (
        "-- --------------------------------------------------------\n"
        f"-- author       : {CONDENSED_120_AUTHOR}\n"
        f"-- create at    : {CONDENSED_120_CREATE_AT}\n"
        f"-- description  : {scenario.description}\n"
        f"-- FE           : {CONDENSED_120_FE}\n"
        "-- --------------------------------------------------------\n"
    )


def render_condensed_case(scenario: CondensedScenario) -> str:
    statements: list[str] = [_header(scenario)]
    statements.append("-- pre-cleanup")
    statements.extend(_cleanup_sql(scenario))
    if scenario.foreign_key_action:
        statements.append("-- create source and target parent tables")
        statements.append(_create_table_sql(scenario, scenario.parent_inplace_table, target=False, parent=True))
        statements.append(_create_table_sql(scenario, scenario.parent_instant_table, target=False, parent=True))
        statements.append(_create_table_sql(scenario, scenario.parent_reference_table, target=True, parent=True))
    statements.append("-- create inplace and instant source candidates")
    statements.append(_create_table_sql(scenario, scenario.inplace_table, target=False, parent_table=scenario.parent_inplace_table if scenario.foreign_key_action else None))
    statements.append(_create_table_sql(scenario, scenario.instant_table, target=False, parent_table=scenario.parent_instant_table if scenario.foreign_key_action else None))
    statements.append("-- create direct target reference")
    statements.append(_create_table_sql(scenario, scenario.reference_table, target=True, parent_table=scenario.parent_reference_table if scenario.foreign_key_action else None))
    statements.append("-- seed deterministic rows")
    for table in (scenario.inplace_table, scenario.instant_table, scenario.reference_table):
        statements.append(_insert_rows_sql(scenario, table, target=False, rows=(1, 2, 3, 4, 5)))
    if scenario.foreign_key_action:
        for table in (scenario.parent_inplace_table, scenario.parent_instant_table, scenario.parent_reference_table):
            statements.append(_insert_parent_rows_sql(scenario, table, target=False, rows=(1, 2, 3, 4, 5)))
    if scenario.dependency in {"function", "all"}:
        statements.append(
            f"CREATE FUNCTION `{scenario.function_name}`(v BIGINT) RETURNS BIGINT DETERMINISTIC RETURN v + 1;"
        )
    if scenario.dependency in {"view", "trigger", "procedure", "all"}:
        for table in (scenario.inplace_table, scenario.instant_table, scenario.reference_table):
            if scenario.dependency in {"trigger", "all"}:
                statements.append(_create_audit_table_sql(scenario, table))
            statements.extend(_dependency_objects_sql(scenario, table, target=True))
    statements.append("-- direct reference deterministic DML (executed once)")
    if scenario.foreign_key_action:
        statements.append(_insert_parent_rows_sql(scenario, scenario.parent_reference_table, target=True, rows=(6, 7)))
    statements.append(_insert_rows_sql(scenario, scenario.reference_table, target=True, rows=(6, 7)))
    if scenario.foreign_key_action:
        statements.append(_update_parent_rows_sql(scenario, scenario.parent_reference_table, target=True))
    statements.append(_update_rows_sql(scenario, scenario.reference_table, target=True))
    statements.append(_delete_rows_sql(scenario.reference_table, scenario.parent_reference_table if scenario.foreign_key_action else None, scenario.foreign_key_action))
    if scenario.foreign_key_action:
        statements.append(_reinsert_parent_sql(scenario, scenario.parent_reference_table, target=True))
    statements.append(_reinsert_sql(scenario, scenario.reference_table, target=True))
    for algorithm, candidate in (("INPLACE", scenario.inplace_table), ("INSTANT", scenario.instant_table)):
        statements.append(f"-- {algorithm} DDL")
        if scenario.foreign_key_action:
            statements.extend(_ddl_sql(scenario, scenario.parent_inplace_table if algorithm == "INPLACE" else scenario.parent_instant_table, algorithm))
        statements.extend(_ddl_sql(scenario, candidate, algorithm))
        statements.append(f"-- {algorithm} post-DDL deterministic DML")
        candidate_parent = (
            scenario.parent_inplace_table if algorithm == "INPLACE" else scenario.parent_instant_table
        )
        if scenario.foreign_key_action:
            statements.append(_insert_parent_rows_sql(scenario, candidate_parent, target=True, rows=(6, 7)))
        statements.append(_insert_rows_sql(scenario, candidate, target=True, rows=(6, 7)))
        if scenario.foreign_key_action:
            statements.append(_update_parent_rows_sql(scenario, candidate_parent, target=True))
        statements.append(_update_rows_sql(scenario, candidate, target=True))
        statements.append(_delete_rows_sql(candidate, candidate_parent if scenario.foreign_key_action else None, scenario.foreign_key_action))
        if scenario.foreign_key_action:
            statements.append(_reinsert_parent_sql(scenario, candidate_parent, target=True))
        statements.append(_reinsert_sql(scenario, candidate, target=True))
        if scenario.dependency in {"function", "all"}:
            statements.append(f"UPDATE `{candidate}` SET `canary_int` = `{scenario.function_name}`(`id`) WHERE `id` IN (1, 3, 5);")
            statements.append(f"UPDATE `{scenario.reference_table}` SET `canary_int` = `{scenario.function_name}`(`id`) WHERE `id` IN (1, 3, 5);")
        if scenario.dependency in {"prepared", "all"}:
            statements.extend(_prepared_statement_sql(scenario, candidate))
            statements.extend(_prepared_statement_sql(scenario, scenario.reference_table))
        if scenario.dependency in {"procedure", "all"}:
            statements.append(f"CALL `{scenario.procedure_name}_{candidate}`(1);")
            statements.append(f"CALL `{scenario.procedure_name}_{scenario.reference_table}`(1);")
        statements.append(f"-- {algorithm} stable result")
        statements.append(_result_row_sql(scenario, candidate, scenario.reference_table, algorithm))
    statements.append("-- final cleanup")
    statements.extend(_cleanup_sql(scenario))
    return "\n".join(statements) + "\n"


def condensed_120_manifest(output: Path) -> dict[str, Any]:
    scenarios = condensed_120_scenarios()
    hashes = {
        "coverage.tsv": hashlib.sha256((output / "coverage.tsv").read_bytes()).hexdigest(),
        "expected_output.tsv": hashlib.sha256((output / "expected_output.tsv").read_bytes()).hexdigest(),
    }
    hashes.update(
        {
            f"sql/{path.name}": hashlib.sha256(path.read_bytes()).hexdigest()
            for path in sorted((output / "sql").glob("TUCR-*.sql"))
        }
    )
    return {
        "artifacts_sha256": hashes,
        "batch_id": CONDENSED_120_BATCH_ID,
        "batch_kind": CONDENSED_120_BATCH_KIND,
        "case_count": len(scenarios),
        "case_id_prefix": CONDENSED_120_CASE_PREFIX,
        "database": CONDENSED_120_DATABASE,
        "materialization": "sql_directory",
        "profiles": ["inplace", "instant"],
        "profile_counts": {"inplace": len(scenarios), "instant": len(scenarios)},
        "sql_file_count": len(scenarios),
        "expected_output_line_count": len(scenarios) * 2,
    }


def write_condensed_120_artifacts(output: Path) -> dict[str, Any]:
    output.mkdir(parents=True, exist_ok=True)
    scenarios = condensed_120_scenarios()
    (output / "sql").mkdir(parents=True, exist_ok=True)
    for scenario in scenarios:
        (output / "sql" / f"{scenario.case_id}.sql").write_text(
            render_condensed_case(scenario),
            encoding="utf-8",
            newline="\n",
        )
    expected_lines = [
        f"{scenario.case_id}\t{algorithm}\t0\t0\t0\t0\tPASS"
        for scenario in scenarios
        for algorithm in ALGORITHMS
    ]
    (output / "expected_output.tsv").write_text(
        "\n".join(expected_lines) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    coverage_lines = [
        "case_id\tfamily\tcategory\tsource_type\ttarget_type\tdependency\tindex_profile",
        *[
            "\t".join(
                (
                    scenario.case_id,
                    scenario.family,
                    scenario.category,
                    scenario.columns[0].source_type,
                    scenario.columns[0].target_type,
                    scenario.dependency,
                    scenario.index_profile,
                )
            )
            for scenario in scenarios
        ],
    ]
    (output / "coverage.tsv").write_text(
        "\n".join(coverage_lines) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    readme = f"""# Type-upgrade condensed 120 SQL batch

This batch contains exactly 120 individual SQL files. Each file contains both
`INPLACE` and `INSTANT` candidates and compares each candidate with a directly
created target-type reference table.

- **BATCH_ID:** `{CONDENSED_120_BATCH_ID}`
- **BATCH_KIND:** `{CONDENSED_120_BATCH_KIND}`
- **CASE_PREFIX:** `{CONDENSED_120_CASE_PREFIX}`
- **Database:** `{CONDENSED_120_DATABASE}`
- **SQL files:** 120
- **Expected output lines:** 240
- **Algorithms per file:** `INPLACE`, `INSTANT`

## Execution

Create the database:

```bash
mysql --login-path=internal_qa \\
  -e "DROP DATABASE IF EXISTS {CONDENSED_120_DATABASE}; CREATE DATABASE {CONDENSED_120_DATABASE} CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci"
```

Run one file:

```bash
mysql --login-path=internal_qa \\
  --batch --raw --skip-column-names --binary-mode --force \\
  {CONDENSED_120_DATABASE} \\
  < generated/type_upgrade_condensed_120_v1/sql/TUCR-000001.sql
```

Run all files:

```bash
for file in generated/type_upgrade_condensed_120_v1/sql/*.sql; do
  mysql --login-path=internal_qa \\
    --batch --raw --skip-column-names --binary-mode --force \\
    {CONDENSED_120_DATABASE} \\
    < "$file"
done > generated/type_upgrade_condensed_120_v1/actual_output.tsv
```

Compare:

```bash
diff -u generated/type_upgrade_condensed_120_v1/expected_output.tsv \\
  generated/type_upgrade_condensed_120_v1/actual_output.tsv
```

Use `--force` because each file intentionally executes both algorithms. A
natural algorithm rejection must not prevent the other algorithm and the data
comparison from running.
"""
    (output / "README.md").write_text(readme, encoding="utf-8", newline="\n")
    manifest = condensed_120_manifest(output)
    (output / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    return manifest
