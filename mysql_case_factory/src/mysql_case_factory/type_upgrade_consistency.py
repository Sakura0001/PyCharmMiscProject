"""Deterministic MySQL type-upgrade consistency case generation.

The suite intentionally excludes temporal, floating point, ENUM/SET, JSON,
spatial, and vector factors.  Local runs use ``ALGORITHM=COPY`` to validate the
generator and its data oracle; the same case IDs can be rendered for internal
``INPLACE`` and ``INSTANT`` validation.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from hashlib import sha256
import json
from itertools import count
from typing import Any, Iterable, Sequence


FORBIDDEN_TYPE_TOKENS: tuple[str, ...] = (
    "FLOAT",
    "DOUBLE",
    "REAL(",
    " DATE",
    " TIME(",
    "DATETIME",
    "TIMESTAMP",
    " YEAR(",
    "ENUM(",
    "SET(",
    " JSON",
    "GEOMETRY",
    "POINT(",
    "LINESTRING",
    "POLYGON",
    "MULTIPOINT",
    "MULTILINESTRING",
    "MULTIPOLYGON",
    "GEOMETRYCOLLECTION",
    "VECTOR",
    "FULLTEXT",
    "SPATIAL",
)

_ALLOWED_PROFILES = {"copy", "inplace", "instant"}
TYPE_UPGRADE_BATCH_ID = "2026-10-13-type-upgrade-consistency"
TYPE_UPGRADE_BATCH_KIND = "new_merge"
TYPE_UPGRADE_CASE_PREFIX = "TUC"


def effective_sql_mode(sql_mode: str) -> str:
    if sql_mode in {"STRICT_ALL_TABLES", "STRICT_TRANS_TABLES"}:
        return sql_mode
    return f"STRICT_ALL_TABLES,{sql_mode}"


def _sql_string(value: str) -> str:
    return "'" + value.replace("\\", "\\\\").replace("'", "''") + "'"


def _hex_byte(char: str) -> str:
    return f"x'{ord(char):02x}'"


@dataclass(frozen=True)
class TypeTransition:
    family: str
    source_type: str
    target_type: str
    positive: bool
    seed_values: tuple[str, ...]
    post_values: tuple[str, ...]
    invalid_values: tuple[str, ...]
    reason: str
    charset: str | None = None
    collation: str | None = None


@dataclass(frozen=True)
class BitTransition:
    source_width: int
    target_width: int

    @property
    def source_type(self) -> str:
        return f"BIT({self.source_width})"

    @property
    def target_type(self) -> str:
        return f"BIT({self.target_width})"


@dataclass(frozen=True)
class DecimalTransition:
    source_precision: int
    target_precision: int
    scale: int
    target_scale: int
    positive: bool

    @property
    def source_type(self) -> str:
        return f"DECIMAL({self.source_precision},{self.scale})"

    @property
    def target_type(self) -> str:
        return f"DECIMAL({self.target_precision},{self.target_scale})"


@dataclass(frozen=True)
class FactorCatalog:
    integer_transitions: tuple[TypeTransition, ...]
    decimal_transitions: tuple[DecimalTransition, ...]
    character_transitions: tuple[TypeTransition, ...]
    binary_transitions: tuple[TypeTransition, ...]
    bit_transitions: tuple[BitTransition, ...]
    data_profiles: tuple[str, ...] = (
        "boundary",
        "null_and_default",
        "post_target",
        "collation_sensitive",
    )
    column_attributes: tuple[str, ...] = (
        "nullable",
        "not_null_default",
        "expression_default",
        "comment",
        "invisible",
        "first",
        "auto_increment",
    )
    index_profiles: tuple[str, ...] = (
        "none",
        "secondary",
        "unique",
        "composite",
        "prefix",
        "descending",
        "invisible_index",
        "functional",
        "generated",
    )
    foreign_key_profiles: tuple[str, ...] = (
        "none",
        "parent",
        "child",
        "self_reference",
        "composite",
        "cascade",
        "set_null",
        "restrict",
        "no_action",
        "multi_level",
    )
    dependency_profiles: tuple[str, ...] = (
        "none",
        "view",
        "trigger_before_insert",
        "trigger_after_insert",
        "trigger_before_update",
        "trigger_after_update",
        "trigger_before_delete",
        "trigger_after_delete",
        "function_read",
        "procedure_write",
        "prepared_statement",
    )
    table_forms: tuple[str, ...] = (
        "ordinary",
        "temporary",
        "range_partition",
        "list_partition",
        "hash_partition",
        "key_partition",
        "compact",
        "redundant",
        "compressed",
        "instant_history",
    )
    sql_modes: tuple[str, ...] = (
        "STRICT_ALL_TABLES",
        "STRICT_TRANS_TABLES",
        "PAD_CHAR_TO_FULL_LENGTH",
        "ANSI_QUOTES",
        "NO_BACKSLASH_ESCAPES",
    )

    def to_json(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "integer_transitions": [
                {
                    "source": item.source_type,
                    "target": item.target_type,
                    "positive": item.positive,
                    "reason": item.reason,
                }
                for item in self.integer_transitions
            ],
            "decimal_transitions": [
                {
                    "source": item.source_type,
                    "target": item.target_type,
                    "scale": item.scale,
                    "target_scale": item.target_scale,
                    "positive": item.positive,
                }
                for item in self.decimal_transitions
            ],
            "character_transitions": [
                {
                    "source": item.source_type,
                    "target": item.target_type,
                    "charset": item.charset,
                    "collation": item.collation,
                    "positive": item.positive,
                }
                for item in self.character_transitions
            ],
            "binary_transitions": [
                {
                    "source": item.source_type,
                    "target": item.target_type,
                    "positive": item.positive,
                }
                for item in self.binary_transitions
            ],
            "bit_transitions": [
                {"source": item.source_type, "target": item.target_type}
                for item in self.bit_transitions
            ],
            "data_profiles": list(self.data_profiles),
            "column_attributes": list(self.column_attributes),
            "index_profiles": list(self.index_profiles),
            "foreign_key_profiles": list(self.foreign_key_profiles),
            "dependency_profiles": list(self.dependency_profiles),
            "table_forms": list(self.table_forms),
            "sql_modes": list(self.sql_modes),
        }


@dataclass(frozen=True)
class TypeUpgradeCase:
    case_id: str
    batch_id: str
    batch_kind: str
    cluster: str
    family: str
    source_type: str
    target_type: str
    expected_outcome: str
    data_profile: str
    column_attribute: str
    index_profile: str
    foreign_key_profile: str
    dependency_profile: str
    table_form: str
    sql_mode: str
    charset: str | None
    collation: str | None
    seed_values: tuple[str, ...]
    post_ddl_values: tuple[str, ...]
    invalid_values: tuple[str, ...]
    reason: str
    setup_sql: tuple[str, ...]
    ddl_sql: str
    post_ddl_sql: tuple[str, ...]
    invalid_post_ddl_sql: tuple[str, ...]
    verify_sql: tuple[str, ...]
    cleanup_sql: tuple[str, ...]
    parent_batch_id: str | None = None
    priority: str | None = None
    gap_id: str | None = None
    coverage_tags: tuple[str, ...] = ()
    interaction_rank: int | None = None
    query_plans: tuple[tuple[str, str], ...] = ()

    def to_json(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "case_id": self.case_id,
            "batch_id": self.batch_id,
            "batch_kind": self.batch_kind,
            "cluster": self.cluster,
            "family": self.family,
            "source_type": self.source_type,
            "target_type": self.target_type,
            "expected_outcome": self.expected_outcome,
            "data_profile": self.data_profile,
            "column_attribute": self.column_attribute,
            "index_profile": self.index_profile,
            "foreign_key_profile": self.foreign_key_profile,
            "dependency_profile": self.dependency_profile,
            "table_form": self.table_form,
            "sql_mode": self.sql_mode,
            "charset": self.charset,
            "collation": self.collation,
            "seed_values": list(self.seed_values),
            "post_ddl_values": list(self.post_ddl_values),
            "invalid_values": list(self.invalid_values),
            "reason": self.reason,
            "setup_sql": list(self.setup_sql),
            "ddl_sql": self.ddl_sql,
            "post_ddl_sql": list(self.post_ddl_sql),
            "invalid_post_ddl_sql": list(self.invalid_post_ddl_sql),
            "verify_sql": list(self.verify_sql),
            "cleanup_sql": list(self.cleanup_sql),
        }
        if self.parent_batch_id is not None:
            payload["parent_batch_id"] = self.parent_batch_id
        if self.priority is not None:
            payload["priority"] = self.priority
        if self.gap_id is not None:
            payload["gap_id"] = self.gap_id
        if self.coverage_tags:
            payload["coverage_tags"] = list(self.coverage_tags)
        if self.interaction_rank is not None:
            payload["interaction_rank"] = self.interaction_rank
        if self.query_plans:
            payload["query_plans"] = [
                {"sql": sql, "expected_index": expected_index}
                for sql, expected_index in self.query_plans
            ]
        return payload


_INTEGER_RANKS = {
    "TINYINT": 1,
    "SMALLINT": 2,
    "MEDIUMINT": 3,
    "INT": 4,
    "BIGINT": 5,
}
_INTEGER_LIMITS = {
    ("TINYINT", True): (-128, 127),
    ("TINYINT", False): (0, 255),
    ("SMALLINT", True): (-32768, 32767),
    ("SMALLINT", False): (0, 65535),
    ("MEDIUMINT", True): (-8388608, 8388607),
    ("MEDIUMINT", False): (0, 16777215),
    ("INT", True): (-2147483648, 2147483647),
    ("INT", False): (0, 4294967295),
    ("BIGINT", True): (-9223372036854775808, 9223372036854775807),
    ("BIGINT", False): (0, 18446744073709551615),
}


def _integer_seed(source: str, signed: bool, nonnegative: bool) -> tuple[str, ...]:
    low, high = _INTEGER_LIMITS[(source, signed)]
    if nonnegative:
        return ("0", str(high), str(high // 2), "1")
    return (str(low), "-1", "0", str(high))


def _integer_post(source: str, target: str, signed: bool) -> tuple[str, ...]:
    _, source_high = _INTEGER_LIMITS[(source, signed)]
    target_low, target_high = _INTEGER_LIMITS[(target, signed)]
    if signed:
        return (str(source_high + 1), str(target_high), str(target_low))
    return (str(source_high + 1), str(target_high), str(target_high - 1))


def _build_integer_transitions() -> tuple[TypeTransition, ...]:
    result: list[TypeTransition] = []
    names = list(_INTEGER_RANKS)
    for source in names:
        for target in names:
            if _INTEGER_RANKS[source] >= _INTEGER_RANKS[target]:
                continue
            for signed in (True, False):
                sign = "" if signed else " UNSIGNED"
                source_type = source + sign
                target_type = target + sign
                result.append(
                    TypeTransition(
                        family="integer",
                        source_type=source_type,
                        target_type=target_type,
                        positive=True,
                        seed_values=_integer_seed(source, signed, not signed),
                        post_values=_integer_post(source, target, signed),
                        invalid_values=(str(_INTEGER_LIMITS[(target, signed)][1] + 1),),
                        reason="same-sign rank widening",
                    )
                )

            # SIGNED -> UNSIGNED is valid only when the fixture contains no negative rows.
            result.append(
                TypeTransition(
                    family="integer",
                    source_type=source,
                    target_type=target + " UNSIGNED",
                    positive=True,
                    seed_values=_integer_seed(source, True, True),
                    post_values=_integer_post(source, target, False),
                    invalid_values=("-1",),
                    reason="nonnegative current data and wider unsigned target",
                )
            )

            # UNSIGNED -> SIGNED is domain-containing only when the signed target is larger.
            unsigned_high = _INTEGER_LIMITS[(source, False)][1]
            signed_high = _INTEGER_LIMITS[(target, True)][1]
            if unsigned_high <= signed_high:
                result.append(
                    TypeTransition(
                        family="integer",
                        source_type=source + " UNSIGNED",
                        target_type=target,
                        positive=True,
                        seed_values=_integer_seed(source, False, True),
                        post_values=_integer_post(source, target, True),
                        invalid_values=(str(signed_high + 1),),
                        reason="unsigned source fits in larger signed target",
                    )
                )

    # Representative negative transitions: narrowing and sign changes that cannot preserve data.
    negative_pairs = [
        ("BIGINT", "INT"),
        ("INT", "SMALLINT"),
        ("SMALLINT", "TINYINT"),
        ("MEDIUMINT", "SMALLINT"),
        ("BIGINT", "MEDIUMINT"),
    ]
    for source, target in negative_pairs:
        for signed in (True, False):
            sign = "" if signed else " UNSIGNED"
            low, high = _INTEGER_LIMITS[(source, signed)]
            result.append(
                TypeTransition(
                    family="integer",
                    source_type=source + sign,
                    target_type=target + sign,
                    positive=False,
                    seed_values=(str(low), str(high), "0", str(high - 1)),
                    post_values=(),
                    invalid_values=(str(high),),
                    reason="narrowing integer conversion",
                )
            )
    for source, target in [("INT", "BIGINT"), ("SMALLINT", "INT"), ("TINYINT", "SMALLINT")]:
        result.append(
            TypeTransition(
                family="integer",
                source_type=source,
                target_type=target + " UNSIGNED",
                positive=False,
                seed_values=("-1", str(_INTEGER_LIMITS[(source, True)][1])),
                post_values=(),
                invalid_values=("-1",),
                reason="negative signed data cannot fit unsigned target",
            )
        )
    return tuple(result)


_DECIMAL_BASES = (
    (1, 0),
    (4, 2),
    (9, 0),
    (9, 4),
    (10, 2),
    (18, 0),
    (18, 9),
    (27, 12),
    (36, 18),
    (65, 30),
)


def _decimal_value(precision: int, scale: int, sign: int = 1) -> str:
    prefix = "-" if sign < 0 else ""
    if scale == 0:
        return f"{prefix}{'9' * precision}"
    return f"{prefix}{'9' * (precision - scale)}.{'9' * scale}"


def _build_decimal_transitions() -> tuple[DecimalTransition, ...]:
    result: list[DecimalTransition] = []
    for precision, scale in _DECIMAL_BASES:
        for target_precision in (precision + 1, precision + 9, 65):
            if target_precision > 65:
                continue
            if target_precision <= precision:
                continue
            result.append(
                DecimalTransition(
                    source_precision=precision,
                    target_precision=target_precision,
                    scale=scale,
                    target_scale=scale,
                    positive=True,
                )
            )
        if precision > 1:
            result.append(
                DecimalTransition(
                    source_precision=precision,
                    target_precision=precision - 1,
                    scale=scale,
                    target_scale=scale,
                    positive=False,
                )
            )
    return tuple(result)


_CHAR_LENGTHS = (1, 2, 7, 8, 15, 16, 31, 32, 63, 64, 85, 86, 127, 128, 255, 256, 511, 512, 1023, 1024, 2047, 2048, 4095, 4096)
_CHARSETS = ("latin1", "ascii", "utf8mb3", "utf8mb4")
_COLLATIONS = {
    "latin1": ("latin1_swedish_ci", "latin1_bin"),
    "ascii": ("ascii_general_ci", "ascii_bin"),
    "utf8mb3": ("utf8mb3_general_ci", "utf8mb3_bin"),
    "utf8mb4": ("utf8mb4_0900_ai_ci", "utf8mb4_0900_as_cs", "utf8mb4_bin"),
}


def _string_values(length: int, charset: str) -> tuple[str, ...]:
    ascii_value = "a" * length
    values = [_sql_string(ascii_value), "NULL"]
    if charset == "utf8mb4":
        values.append(_sql_string(("汉" * length)[: max(1, length // 2)]))
        values.append(_sql_string(("😀" * length)[: max(1, length // 2)]))
    elif charset == "utf8mb3":
        values.append(_sql_string(("汉" * length)[: max(1, length // 2)]))
    else:
        values.append(_sql_string(("A" * length)))
    values.append(_sql_string("a" * max(0, length - 1) + "b"))
    return tuple(values)


def _large_object_invalid_value(target_type: str, family: str) -> tuple[str, ...]:
    if target_type in {"LONGTEXT", "LONGBLOB"}:
        return ()
    if target_type in {"MEDIUMTEXT", "MEDIUMBLOB"}:
        return ("REPEAT('z', 17000000)",) if family == "character" else ("REPEAT(x'ff', 17000000)",)
    return ("REPEAT('z', 70000)",) if family == "character" else ("REPEAT(x'ff', 70000)",)


def _character_length(type_name: str, default: int = 16) -> int:
    if "(" not in type_name:
        return default
    return int(type_name.split("(", 1)[1].split(")", 1)[0])


def _collation_distinct_values(length: int, letters: str) -> tuple[str, ...]:
    return tuple(_sql_string(letter * length) for letter in letters)


def _unique_binary_post_values(length: int) -> tuple[str, ...]:
    patterns = ("1234", "5678", "9abc", "def0", "1357", "2468")
    values = []
    for pattern in patterns:
        byte_count = length
        repeated = (pattern * ((byte_count + len(pattern) // 2 - 1) // (len(pattern) // 2)))[: byte_count * 2]
        values.append(f"x'{repeated}'")
    return tuple(values)

def _build_character_transitions() -> tuple[TypeTransition, ...]:
    result: list[TypeTransition] = []
    for charset in _CHARSETS:
        for source_length, target_length in zip(_CHAR_LENGTHS, _CHAR_LENGTHS[1:]):
            for source_kind, target_kind in (
                ("CHAR", "CHAR"),
                ("VARCHAR", "VARCHAR"),
                ("CHAR", "VARCHAR"),
                ("VARCHAR", "CHAR"),
            ):
                # MySQL CHAR(M) is capped at 255 characters.
                if source_kind == "CHAR" and source_length > 255:
                    continue
                if target_kind == "CHAR" and target_length > 255:
                    continue
                source_type = f"{source_kind}({source_length})"
                target_type = f"{target_kind}({target_length})"
                result.append(
                    TypeTransition(
                        family="character",
                        source_type=source_type,
                        target_type=target_type,
                        positive=True,
                        seed_values=_string_values(source_length, charset),
                        post_values=_string_values(target_length, charset),
                        invalid_values=(_sql_string("z" * (target_length + 1)),),
                        reason="character length widening",
                        charset=charset,
                        collation=_COLLATIONS[charset][0],
                    )
                )
        for source, target in (
            ("VARCHAR(255)", "TINYTEXT"),
            ("TINYTEXT", "TEXT"),
            ("TEXT", "MEDIUMTEXT"),
            ("MEDIUMTEXT", "LONGTEXT"),
            ("VARCHAR(1024)", "TEXT"),
        ):
            result.append(
                TypeTransition(
                    family="character",
                    source_type=source,
                    target_type=target,
                    positive=True,
                    seed_values=_string_values(16, charset),
                    post_values=_string_values(32, charset),
                    invalid_values=_large_object_invalid_value(target, "character"),
                    reason="text family widening",
                    charset=charset,
                    collation=_COLLATIONS[charset][0],
                )
            )
    # A few shrinking cases must reject and preserve the old state.
    for source_length, target_length in ((256, 255), (128, 127), (64, 63), (32, 31), (16, 15)):
        result.append(
            TypeTransition(
                family="character",
                source_type=f"VARCHAR({source_length})",
                target_type=f"VARCHAR({target_length})",
                positive=False,
                seed_values=(_sql_string("a" * source_length),),
                post_values=(),
                invalid_values=(_sql_string("a" * source_length),),
                reason="character length narrowing",
                charset="utf8mb4",
                collation="utf8mb4_0900_ai_ci",
            )
        )
    return tuple(result)


_BINARY_LENGTHS = (1, 2, 7, 8, 15, 16, 31, 32, 63, 64, 127, 128, 255, 256, 511, 512, 1023, 1024, 2047, 2048, 4095, 4096)


def _binary_values(length: int) -> tuple[str, ...]:
    values = [
        f"x'{'00' * length}'",
        f"x'{'ff' * length}'",
        f"x'{'01' * length}'",
        f"x'{'ab' * length}'",
        "NULL",
    ]
    if length > 1:
        values.append(f"x'{'00' * (length - 1)}ff'")
    return tuple(values)


def _build_binary_transitions() -> tuple[TypeTransition, ...]:
    result: list[TypeTransition] = []
    for source_length, target_length in zip(_BINARY_LENGTHS, _BINARY_LENGTHS[1:]):
        for source_kind, target_kind in (
            ("BINARY", "BINARY"),
            ("VARBINARY", "VARBINARY"),
            ("BINARY", "VARBINARY"),
            ("VARBINARY", "BINARY"),
        ):
            # MySQL BINARY(M) is capped at 255 bytes.
            if source_kind == "BINARY" and source_length > 255:
                continue
            if target_kind == "BINARY" and target_length > 255:
                continue
            result.append(
                TypeTransition(
                    family="binary",
                    source_type=f"{source_kind}({source_length})",
                    target_type=f"{target_kind}({target_length})",
                    positive=True,
                    seed_values=_binary_values(source_length),
                    post_values=_binary_values(target_length),
                    invalid_values=(f"x'{'ff' * (target_length + 1)}'",),
                    reason="binary length widening",
                )
            )
    for source, target in (
        ("VARBINARY(255)", "TINYBLOB"),
        ("TINYBLOB", "BLOB"),
        ("BLOB", "MEDIUMBLOB"),
        ("MEDIUMBLOB", "LONGBLOB"),
        ("VARBINARY(1024)", "BLOB"),
    ):
        result.append(
            TypeTransition(
                family="binary",
                source_type=source,
                target_type=target,
                positive=True,
                seed_values=_binary_values(16),
                post_values=_binary_values(32),
                invalid_values=_large_object_invalid_value(target, "binary"),
                reason="blob family widening",
            )
        )
    for source_length, target_length in ((256, 255), (128, 127), (64, 63), (32, 31), (16, 15)):
        result.append(
            TypeTransition(
                family="binary",
                source_type=f"VARBINARY({source_length})",
                target_type=f"VARBINARY({target_length})",
                positive=False,
                seed_values=(f"x'{'ff' * source_length}'",),
                post_values=(),
                invalid_values=(f"x'{'ff' * source_length}'",),
                reason="binary length narrowing",
            )
        )
    return tuple(result)


_BIT_PAIRS = (
    (1, 2), (1, 8), (1, 16), (1, 32), (1, 64),
    (7, 8), (8, 9), (8, 16), (8, 32), (8, 64),
    (11, 12), (11, 16), (11, 32), (11, 64),
    (15, 16), (16, 17), (16, 32), (16, 64),
    (20, 21), (20, 32), (31, 32), (32, 33), (32, 64),
    (33, 34), (33, 64), (48, 49), (48, 64), (63, 64),
)


def _bit_values(width: int) -> tuple[str, ...]:
    return (
        f"b'{'0' * width}'",
        f"b'{'1' * width}'",
        f"b'{'0' * (width - 1)}1'",
        f"b'1{'0' * (width - 1)}'",
        f"b'{('01' * width)[:width]}'",
    )


def _unique_bit_values(width: int, start: int = 0, count: int = 5) -> tuple[str, ...]:
    available = max(0, (1 << width) - start)
    return tuple(f"b'{value:0{width}b}'" for value in range(start, start + min(count, available)))


def _build_bit_transitions() -> tuple[BitTransition, ...]:
    return tuple(BitTransition(source, target) for source, target in _BIT_PAIRS)


def build_factor_catalog() -> FactorCatalog:
    integer = _build_integer_transitions()
    decimal = _build_decimal_transitions()

    character = _build_character_transitions()
    binary = _build_binary_transitions()
    bit = _build_bit_transitions()

    return FactorCatalog(
        integer_transitions=integer,
        decimal_transitions=decimal,
        character_transitions=character,
        binary_transitions=binary,
        bit_transitions=bit,
    )


# Keep generic transition accessors close to the catalog for generation.
def _all_positive_transitions(catalog: FactorCatalog) -> tuple[TypeTransition, ...]:
    decimal_generic = _decimal_as_generic(catalog.decimal_transitions)
    bit_generic = _bit_as_generic(catalog.bit_transitions)
    return tuple(
        item
        for item in (
            *catalog.integer_transitions,
            *decimal_generic,
            *catalog.character_transitions,
            *catalog.binary_transitions,
            *bit_generic,
        )
        if item.positive
    )


def _all_negative_transitions(catalog: FactorCatalog) -> tuple[TypeTransition, ...]:
    decimal_generic = _decimal_as_generic(catalog.decimal_transitions)
    return tuple(
        item
        for item in (
            *catalog.integer_transitions,
            *decimal_generic,
            *catalog.character_transitions,
            *catalog.binary_transitions,
        )
        if not item.positive
    )


def _decimal_as_generic(items: Iterable[DecimalTransition]) -> tuple[TypeTransition, ...]:
    result: list[TypeTransition] = []
    spellings = (("DECIMAL", "DECIMAL"), ("NUMERIC", "NUMERIC"), ("DECIMAL", "NUMERIC"), ("NUMERIC", "DECIMAL"))
    for item in items:
        for source_spelling, target_spelling in spellings:
            result.append(
                TypeTransition(
                    family="decimal",
                    source_type=f"{source_spelling}({item.source_precision},{item.scale})",
                    target_type=f"{target_spelling}({item.target_precision},{item.target_scale})",
                    positive=item.positive,
                    seed_values=(
                        _decimal_value(item.source_precision, item.scale, 1),
                        _decimal_value(item.source_precision, item.scale, -1),
                        "0",
                        f"0.{'0' * (item.scale - 1)}1" if item.scale else "1",
                    ),
                    post_values=(
                        _decimal_value(item.target_precision, item.target_scale, 1),
                        _decimal_value(item.target_precision, item.target_scale, -1),
                    )
                    if item.positive
                    else (),
                    invalid_values=(_decimal_value(item.target_precision + 1, item.target_scale, 1),),
                    reason="decimal/numeric precision widening with unchanged scale"
                    if item.positive
                    else "decimal/numeric precision narrowing",
                )
            )
    return tuple(result)


def _bit_as_generic(items: Iterable[BitTransition]) -> tuple[TypeTransition, ...]:
    return tuple(
        TypeTransition(
            family="bit",
            source_type=item.source_type,
            target_type=item.target_type,
            positive=True,
            seed_values=_bit_values(item.source_width),
            post_values=_bit_values(item.target_width),
            invalid_values=(f"b'{'1' * (item.target_width + 1)}'",),
            reason="bit width widening",
        )
        for item in items
    )


def _quote_identifier(identifier: str) -> str:
    return "`" + identifier.replace("`", "``") + "`"


def _column_definition(
    type_name: str,
    attribute: str,
    charset: str | None,
    collation: str | None,
    family: str,
) -> str:
    pieces: list[str] = [type_name]
    if family == "character" and charset:
        pieces.append(f"CHARACTER SET {charset}")
        if collation:
            pieces.append(f"COLLATE {collation}")
    if attribute in {"nullable", "first", "comment", "invisible"}:
        pieces.append("NULL")
    else:
        pieces.append("NOT NULL")
    if attribute == "not_null_default" and not type_name.endswith(("TEXT", "BLOB")):
        if family in {"integer", "decimal", "bit"}:
            pieces.append("DEFAULT 0")
        elif family == "character":
            pieces.append("DEFAULT 'x'")
        else:
            pieces.append("DEFAULT x'00'")
    if attribute == "expression_default" and not type_name.endswith(("TEXT", "BLOB")):
        if family in {"integer", "decimal", "bit"}:
            pieces.append("DEFAULT (1+1)")
        elif family == "character":
            pieces.append("DEFAULT (CONCAT('x','y'))")
        else:
            pieces.append("DEFAULT (UNHEX('01'))")
    if attribute == "comment":
        pieces.append("COMMENT 'type upgrade canary'")
    if attribute == "invisible":
        pieces.append("INVISIBLE")
    if attribute == "first":
        pieces.append("FIRST")
    if attribute == "auto_increment" and family == "integer":
        pieces.append("AUTO_INCREMENT")
    return " ".join(pieces)


def _index_definitions(profile: str, family: str, source_type: str) -> tuple[str, ...]:
    if profile == "none":
        return ()
    if profile == "secondary":
        return ("KEY idx_target (target_col)",)
    if profile == "unique":
        return ("UNIQUE KEY uk_target (target_col)",)
    if profile == "composite":
        return ("KEY idx_composite (canary_int, target_col, canary_varchar(16))",)
    if profile == "prefix" and family in {"character", "binary"}:
        if not source_type.startswith(("CHAR(", "VARCHAR(", "BINARY(", "VARBINARY(")):
            return ("KEY idx_prefix (target_col(16))",)
        current = int(source_type.split("(", 1)[1].split(")", 1)[0])
        if current <= 1:
            return ()
        length = min(16, current - 1)
        return (f"KEY idx_prefix (target_col({length}))",)
    if profile == "descending":
        return ("KEY idx_desc (target_col DESC)",)
    if profile == "invisible_index":
        return ("KEY idx_invisible (target_col) INVISIBLE",)
    if profile == "functional":
        return ("KEY idx_functional ((MD5(CAST(target_col AS CHAR))))",)
    return ()


def _table_suffix(form: str) -> str:
    if form == "range_partition":
        return " PARTITION BY RANGE (part_key) (PARTITION p0 VALUES LESS THAN (50), PARTITION p1 VALUES LESS THAN MAXVALUE)"
    if form == "list_partition":
        return " PARTITION BY LIST (part_key) (PARTITION p0 VALUES IN (0,1,2), PARTITION p1 VALUES IN (3,4,5))"
    if form == "hash_partition":
        return " PARTITION BY HASH (part_key) PARTITIONS 4"
    if form == "key_partition":
        return " PARTITION BY KEY (part_key) PARTITIONS 4"
    if form == "compact":
        return " ROW_FORMAT=COMPACT"
    if form == "redundant":
        return " ROW_FORMAT=REDUNDANT"
    if form == "compressed":
        return " ROW_FORMAT=COMPRESSED"
    return ""


def _value_expression(family: str, value: str) -> str:
    if family == "character":
        return f"HEX(CAST(target_col AS BINARY))"
    if family == "binary":
        return "HEX(target_col)"
    if family == "bit":
        return "BIN(target_col)"
    return "CAST(target_col AS CHAR)"


def _setup_statements(
    case_no: int,
    transition: TypeTransition,
    attribute: str,
    index_profile: str,
    table_form: str,
    foreign_key_profile: str = "none",
    dependency_profile: str = "none",
    temporary: bool = False,
) -> tuple[tuple[str, str, str], tuple[str, ...], tuple[str, ...]]:
    old_table = f"tuc_old_{case_no}"
    ref_table = f"tuc_ref_{case_no}"
    algo_table = f"tuc_algo_{case_no}"

    create_attribute = "nullable" if attribute == "first" else attribute
    source_col = _column_definition(
        transition.source_type, create_attribute, transition.charset, transition.collation, transition.family
    )
    target_col = _column_definition(
        transition.target_type, create_attribute, transition.charset, transition.collation, transition.family
    )
    indexes = list(_index_definitions(index_profile, transition.family, transition.source_type))

    leading_columns = [
        f"target_col {source_col}",
        "id BIGINT NOT NULL",
    ] if attribute == "first" else [
        "id BIGINT NOT NULL",
        f"target_col {source_col}",
    ]
    common_columns = [
        *leading_columns,
        "part_key INT NOT NULL DEFAULT 0",
        "canary_int BIGINT NOT NULL DEFAULT 7",
        "canary_varchar VARCHAR(64) NOT NULL DEFAULT 'canary'",
        "canary_varbinary VARBINARY(64) NOT NULL DEFAULT x'00'",
        "canary_decimal DECIMAL(20,4) NOT NULL DEFAULT 12.5000",
    ]
    if index_profile == "generated":
        if transition.family in {"integer", "decimal"}:
            common_columns.append("gen_col DECIMAL(65,0) GENERATED ALWAYS AS (CAST(target_col AS DECIMAL(65,0))) STORED")
            indexes.append("KEY idx_generated (gen_col)")
        elif transition.family == "bit":
            common_columns.append("gen_col BIGINT UNSIGNED GENERATED ALWAYS AS (target_col + 0) STORED")
            indexes.append("KEY idx_generated (gen_col)")
        else:
            common_columns.append("gen_col VARCHAR(130) GENERATED ALWAYS AS (CONCAT(CAST(target_col AS CHAR), 'x')) STORED")
            indexes.append("KEY idx_generated (gen_col)")
    if attribute == "auto_increment" and transition.family == "integer":
        indexes.append("KEY idx_auto (target_col)")
    if foreign_key_profile != "none":
        if "idx_target" not in " ".join(indexes):
            indexes.append("KEY idx_fk_target (target_col)")

    primary_key = "(id,part_key)" if table_form in {"range_partition", "list_partition", "hash_partition", "key_partition"} else "(id)"
    columns_sql = ", ".join(common_columns + [f"PRIMARY KEY {primary_key}"] + indexes)
    table_options = _table_suffix(table_form)
    temporary_sql = "TEMPORARY " if temporary else ""

    def create(table: str, coldef: str) -> str:
        table_columns = columns_sql.replace(source_col, coldef, 1)
        return f"CREATE {temporary_sql}TABLE {table} ({table_columns}){table_options}"

    reference_col = target_col if transition.positive else source_col
    setup = [create(old_table, source_col), create(ref_table, reference_col), create(algo_table, source_col)]
    cleanup = [old_table, ref_table, algo_table]
    if table_form == "instant_history":
        setup.append(f"ALTER TABLE {ref_table} ADD COLUMN instant_history_col INT DEFAULT 1")
        setup.append(f"ALTER TABLE {algo_table} ADD COLUMN instant_history_col INT DEFAULT 1, ALGORITHM=INSTANT")

    # Foreign-key objects are created after the DDL so COPY can validate the
    # upgraded type without confusing a pre-existing one-side type mismatch
    # with a type-conversion failure.
    if foreign_key_profile == "child":
        cleanup[:] = [f"tuc_fk_parent_ref_{case_no}", f"tuc_fk_parent_algo_{case_no}", *cleanup]
    elif foreign_key_profile == "multi_level":
        cleanup.extend(
            [
                f"tuc_fk_level1_ref_{case_no}",
                f"tuc_fk_level1_algo_{case_no}",
                f"tuc_fk_level2_ref_{case_no}",
                f"tuc_fk_level2_algo_{case_no}",
            ]
        )
    elif foreign_key_profile != "none" and foreign_key_profile != "self_reference":
        cleanup.extend([f"tuc_fk_child_ref_{case_no}", f"tuc_fk_child_algo_{case_no}"])

    # Real dependency objects.  REF and ALGO each receive an equivalent object.
    if dependency_profile == "view":
        for prefix, table in (("ref", ref_table), ("algo", algo_table)):
            setup.append(f"CREATE VIEW tuc_view_{prefix}_{case_no} AS SELECT id, target_col, part_key, canary_int, canary_varchar, canary_varbinary, canary_decimal FROM {table}")
            cleanup.append(f"tuc_view_{prefix}_{case_no}")
    elif dependency_profile.startswith("trigger_"):
        for prefix, table in (("ref", ref_table), ("algo", algo_table)):
            audit = f"tuc_audit_{prefix}_{case_no}"
            setup.append(
                f"CREATE TABLE {audit} (id BIGINT NOT NULL PRIMARY KEY, op VARCHAR(24) NOT NULL, "
                f"old_value MEDIUMTEXT NULL, new_value MEDIUMTEXT NULL)"
            )
            action, event = dependency_profile.removeprefix("trigger_").split("_", 1)
            timing = action.upper()
            event_name = event.upper()
            if event_name == "INSERT":
                old_value, new_value = "NULL", "CAST(NEW.target_col AS CHAR)"
            elif event_name == "UPDATE":
                old_value, new_value = "CAST(OLD.target_col AS CHAR)", "CAST(NEW.target_col AS CHAR)"
            else:
                old_value, new_value = "CAST(OLD.target_col AS CHAR)", "NULL"
            trigger_name = f"tuc_trg_{action}_{event}_{prefix}_{case_no}"
            if event_name == "DELETE":
                setup.append(
                    f"CREATE TRIGGER {trigger_name} {timing} {event_name} ON {table} FOR EACH ROW "
                    f"INSERT INTO {audit} VALUES (OLD.id, '{timing} {event_name}', {old_value}, {new_value})"
                )
            else:
                setup.append(
                    f"CREATE TRIGGER {trigger_name} {timing} {event_name} ON {table} FOR EACH ROW "
                    f"INSERT INTO {audit} VALUES (NEW.id, '{timing} {event_name}', {old_value}, {new_value})"
                )
            cleanup.extend([trigger_name, audit])
    elif dependency_profile == "function_read":
        for prefix, table in (("ref", ref_table), ("algo", algo_table)):
            setup.append(
                f"CREATE FUNCTION tuc_fn_{prefix}_{case_no}(p_id BIGINT) RETURNS MEDIUMTEXT "
                f"DETERMINISTIC READS SQL DATA RETURN (SELECT CAST(target_col AS CHAR) FROM {table} WHERE id=p_id)"
            )
            setup.append(f"CREATE TABLE tuc_fn_result_{prefix}_{case_no} (id BIGINT NOT NULL PRIMARY KEY, value MEDIUMTEXT NULL)")
            cleanup.extend([f"tuc_fn_{prefix}_{case_no}", f"tuc_fn_result_{prefix}_{case_no}"])
    elif dependency_profile == "procedure_write":
        for prefix, table in (("ref", ref_table), ("algo", algo_table)):
            setup.append(
                f"CREATE PROCEDURE tuc_proc_{prefix}_{case_no}(p_id BIGINT, p_value MEDIUMTEXT) "
                f"INSERT INTO {table} (id,target_col,part_key,canary_int,canary_varchar,canary_varbinary,canary_decimal) "
                f"VALUES (p_id, {transition.post_values[0] if transition.post_values else transition.seed_values[0]}, 0, p_id, 'proc', x'03', p_id)"
            )
            cleanup.append(f"tuc_proc_{prefix}_{case_no}")

    return (old_table, ref_table, algo_table), tuple(setup), tuple(cleanup)


def _seed_statement(table: str, values: Sequence[str], nullable: bool) -> str:
    rows = []
    selected = values if nullable else tuple(value for value in values if value != "NULL")
    for idx, value in enumerate(selected, 1):
        rows.append(f"({idx}, {value}, {idx % 4}, {idx}, 'seed-{idx}', x'01', {idx}.5000)")
    return f"INSERT INTO {table} (id,target_col,part_key,canary_int,canary_varchar,canary_varbinary,canary_decimal) VALUES {', '.join(rows)}"


def _post_statement(table: str, values: Sequence[str], start_id: int) -> str:
    rows = []
    for offset, value in enumerate(values, start_id):
        if value == "NULL":
            continue
        rows.append(f"({offset}, {value}, {offset % 4}, {offset}, 'post-{offset}', x'02', {offset}.2500)")
    if not rows:
        return f"SELECT 1 FROM {table}"
    return f"INSERT INTO {table} (id,target_col,part_key,canary_int,canary_varchar,canary_varbinary,canary_decimal) VALUES {', '.join(rows)}"


def _data_check(ref_table: str, algo_table: str, family: str) -> str:
    value_expr = _value_expression(family, "unused")
    return (
        f"SELECT CASE WHEN NOT EXISTS ("
        f"SELECT 1 FROM {ref_table} r LEFT JOIN {algo_table} a USING(id) WHERE a.id IS NULL "
        f"UNION ALL SELECT 1 FROM {algo_table} a LEFT JOIN {ref_table} r USING(id) WHERE r.id IS NULL "
        f"UNION ALL SELECT 1 FROM {ref_table} r JOIN {algo_table} a USING(id) "
        f"WHERE NOT ({value_expr.replace('target_col', 'r.target_col')} <=> {value_expr.replace('target_col', 'a.target_col')} "
        f"AND r.part_key <=> a.part_key AND r.canary_int <=> a.canary_int "
        f"AND r.canary_varchar <=> a.canary_varchar AND r.canary_varbinary <=> a.canary_varbinary "
        f"AND r.canary_decimal <=> a.canary_decimal) LIMIT 1) THEN 'OK' ELSE 'FAIL' END"
    )


def _generic_table_check(ref_table: str, algo_table: str) -> str:
    return (
        f"SELECT CASE WHEN NOT EXISTS ("
        f"SELECT 1 FROM {ref_table} r LEFT JOIN {algo_table} a USING(id) WHERE a.id IS NULL "
        f"UNION ALL SELECT 1 FROM {algo_table} a LEFT JOIN {ref_table} r USING(id) WHERE r.id IS NULL "
        f"UNION ALL SELECT 1 FROM {ref_table} r JOIN {algo_table} a USING(id) "
        f"WHERE NOT (r.op <=> a.op AND r.old_value <=> a.old_value AND r.new_value <=> a.new_value) LIMIT 1) "
        "THEN 'OK' ELSE 'FAIL' END"
    )


def _schema_check(ref_table: str, algo_table: str) -> str:
    columns = (
        "column_name, ordinal_position, column_type, is_nullable, column_default, extra, "
        "character_set_name, collation_name, column_comment"
    )
    return (
        "SELECT CASE WHEN NOT EXISTS ("
        f"(SELECT {columns} FROM information_schema.columns WHERE table_schema=DATABASE() AND table_name='{ref_table}' "
        f"EXCEPT SELECT {columns} FROM information_schema.columns WHERE table_schema=DATABASE() AND table_name='{algo_table}') "
        f"UNION ALL "
        f"(SELECT {columns} FROM information_schema.columns WHERE table_schema=DATABASE() AND table_name='{algo_table}' "
        f"EXCEPT SELECT {columns} FROM information_schema.columns WHERE table_schema=DATABASE() AND table_name='{ref_table}') "
        "LIMIT 1) THEN 'OK' ELSE 'FAIL' END"
    )


def _value_table_check(ref_table: str, algo_table: str) -> str:
    return (
        f"SELECT CASE WHEN NOT EXISTS ("
        f"SELECT 1 FROM {ref_table} r LEFT JOIN {algo_table} a USING(id) WHERE a.id IS NULL "
        f"UNION ALL SELECT 1 FROM {algo_table} a LEFT JOIN {ref_table} r USING(id) WHERE r.id IS NULL "
        f"UNION ALL SELECT 1 FROM {ref_table} r JOIN {algo_table} a USING(id) "
        f"WHERE NOT (r.value <=> a.value) LIMIT 1) THEN 'OK' ELSE 'FAIL' END"
    )


def _index_check(ref_table: str, algo_table: str) -> str:
    columns = (
        "index_name, non_unique, seq_in_index, column_name, collation, sub_part, "
        "packed, nullable, index_type, comment, index_comment, expression"
    )
    return (
        "SELECT CASE WHEN NOT EXISTS ("
        f"(SELECT {columns} FROM information_schema.statistics WHERE table_schema=DATABASE() AND table_name='{ref_table}' "
        f"EXCEPT SELECT {columns} FROM information_schema.statistics WHERE table_schema=DATABASE() AND table_name='{algo_table}') "
        f"UNION ALL "
        f"(SELECT {columns} FROM information_schema.statistics WHERE table_schema=DATABASE() AND table_name='{algo_table}' "
        f"EXCEPT SELECT {columns} FROM information_schema.statistics WHERE table_schema=DATABASE() AND table_name='{ref_table}') "
        "LIMIT 1) THEN 'OK' ELSE 'FAIL' END"
    )


def _fk_check(ref_table: str, algo_table: str) -> str:
    ref_constraints = (
        f"SELECT REPLACE(constraint_name,'_ref_','_side_'), update_rule, delete_rule, "
        f"REPLACE(referenced_table_name,'_ref_','_side_') "
        f"FROM information_schema.referential_constraints "
        f"WHERE constraint_schema=DATABASE() AND table_name='{ref_table}'"
    )
    algo_constraints = (
        f"SELECT REPLACE(constraint_name,'_algo_','_side_'), update_rule, delete_rule, "
        f"REPLACE(referenced_table_name,'_algo_','_side_') "
        f"FROM information_schema.referential_constraints "
        f"WHERE constraint_schema=DATABASE() AND table_name='{algo_table}'"
    )
    ref_usage = (
        f"SELECT REPLACE(constraint_name,'_ref_','_side_'), column_name, ordinal_position, "
        f"REPLACE(referenced_table_name,'_ref_','_side_'), referenced_column_name "
        f"FROM information_schema.key_column_usage "
        f"WHERE table_schema=DATABASE() AND table_name='{ref_table}' AND referenced_column_name IS NOT NULL"
    )
    algo_usage = (
        f"SELECT REPLACE(constraint_name,'_algo_','_side_'), column_name, ordinal_position, "
        f"REPLACE(referenced_table_name,'_algo_','_side_'), referenced_column_name "
        f"FROM information_schema.key_column_usage "
        f"WHERE table_schema=DATABASE() AND table_name='{algo_table}' AND referenced_column_name IS NOT NULL"
    )
    return (
        "SELECT CASE WHEN NOT EXISTS ("
        f"({ref_constraints} EXCEPT {algo_constraints}) "
        f"UNION ALL ({algo_constraints} EXCEPT {ref_constraints}) "
        "LIMIT 1) AND NOT EXISTS ("
        f"({ref_usage} EXCEPT {algo_usage}) "
        f"UNION ALL ({algo_usage} EXCEPT {ref_usage}) "
        "LIMIT 1) THEN 'OK' ELSE 'FAIL' END"
    )


def _build_case(
    case_no: int,
    cluster: str,
    transition: TypeTransition,
    data_profile: str,
    attribute: str,
    index_profile: str,
    foreign_key_profile: str = "none",
    dependency_profile: str = "none",
    table_form: str = "ordinary",
    sql_mode: str = "STRICT_ALL_TABLES",
) -> TypeUpgradeCase:
    tables, base_setup, cleanup_tables_tuple = _setup_statements(
        case_no,
        transition,
        attribute,
        index_profile,
        table_form,
        foreign_key_profile,
        dependency_profile,
        temporary=table_form == "temporary",
    )
    old_table, ref_table, algo_table = tables
    cleanup_tables = list(cleanup_tables_tuple)
    nullable = attribute in {"nullable", "comment", "invisible", "first"}
    seed_values = transition.seed_values
    post_values = transition.post_values if transition.positive else ()
    if index_profile == "unique" and transition.family == "character":
        seed_values = _collation_distinct_values(_character_length(transition.source_type), "abcd")
        if transition.positive:
            post_values = _collation_distinct_values(_character_length(transition.target_type), "efgh")
    if index_profile == "unique" and transition.family == "binary" and transition.positive:
        post_values = _unique_binary_post_values(_character_length(transition.target_type))
    if index_profile == "unique" and transition.family == "bit":
        source_width = int(transition.source_type[4:-1])
        target_width = int(transition.target_type[4:-1])
        seed_values = _unique_bit_values(source_width, 0)
        if transition.positive:
            post_values = _unique_bit_values(target_width, len(seed_values))

    seed_statements = [
        _seed_statement(old_table, seed_values, nullable),
        _seed_statement(ref_table, seed_values, nullable),
        _seed_statement(algo_table, seed_values, nullable),
    ]

    ddl_sql = (
        f"ALTER TABLE {algo_table} MODIFY target_col "
        f"{_column_definition(transition.target_type, attribute, transition.charset, transition.collation, transition.family)}, "
        "ALGORITHM=${ALGORITHM}"
    )
    post_statements: list[str] = []
    invalid_statements: list[str] = []
    if transition.positive and post_values:
        post_statements.extend(
            [
                _post_statement(ref_table, post_values, 100),
                _post_statement(algo_table, post_values, 100),
            ]
        )
        if transition.invalid_values:
            invalid_statements.extend(
                [
                    _post_statement(ref_table, transition.invalid_values, 200),
                    _post_statement(algo_table, transition.invalid_values, 200),
                ]
            )

    if foreign_key_profile != "none" and transition.positive:
        action = "ON DELETE CASCADE"
        if foreign_key_profile == "set_null":
            action = "ON DELETE SET NULL"
        elif foreign_key_profile in {"restrict", "no_action", "parent", "child", "composite", "self_reference", "multi_level"}:
            action = "ON DELETE RESTRICT"
        fk_type = transition.target_type
        if transition.family == "character" and transition.charset:
            fk_type += f" CHARACTER SET {transition.charset} COLLATE {transition.collation}"
        for prefix in ("ref", "algo"):
            table = ref_table if prefix == "ref" else algo_table
            if foreign_key_profile == "multi_level":
                level1 = f"tuc_fk_level1_{prefix}_{case_no}"
                level2 = f"tuc_fk_level2_{prefix}_{case_no}"
                post_statements.extend(
                    [
                        f"CREATE TABLE {level1} (id BIGINT NOT NULL PRIMARY KEY, parent_id {fk_type} NOT NULL, part_key INT NOT NULL, KEY idx_parent_id (parent_id), KEY idx_parent_part (part_key,parent_id))",
                        f"ALTER TABLE {level1} ADD CONSTRAINT fk_level1_{prefix}_{case_no} FOREIGN KEY (parent_id) REFERENCES {table} (target_col) ON DELETE RESTRICT",
                        f"INSERT INTO {level1} (id,parent_id,part_key) SELECT id+1000,target_col,part_key FROM {table} WHERE target_col IS NOT NULL",
                        f"CREATE TABLE {level2} (id BIGINT NOT NULL PRIMARY KEY, parent_id {fk_type} NOT NULL, part_key INT NOT NULL, KEY idx_parent_id (parent_id), KEY idx_parent_part (part_key,parent_id))",
                        f"ALTER TABLE {level2} ADD CONSTRAINT fk_level2_{prefix}_{case_no} FOREIGN KEY (parent_id) REFERENCES {level1} (parent_id) ON DELETE RESTRICT",
                        f"INSERT INTO {level2} (id,parent_id,part_key) SELECT id+1000,parent_id,part_key FROM {level1}",
                    ]
                )
            elif foreign_key_profile == "self_reference":
                post_statements.extend(
                    [
                        f"ALTER TABLE {table} ADD COLUMN parent_id {fk_type} NULL",
                        f"ALTER TABLE {table} ADD KEY idx_self_parent_{case_no} (parent_id)",
                        f"ALTER TABLE {table} ADD CONSTRAINT fk_self_{prefix}_{case_no} FOREIGN KEY (parent_id) REFERENCES {table} (target_col) {action}",
                        f"UPDATE {table} SET parent_id=(SELECT target_col FROM (SELECT target_col FROM {table} WHERE id=1) AS seed_parent) WHERE id=2",
                    ]
                )
            elif foreign_key_profile == "child":
                parent = f"tuc_fk_parent_{prefix}_{case_no}"
                post_statements.extend(
                    [
                        f"CREATE TABLE {parent} (id BIGINT NOT NULL PRIMARY KEY, target_col {fk_type} NOT NULL, KEY idx_fk_target (target_col))",
                        f"INSERT INTO {parent} (id,target_col) SELECT id,target_col FROM {table} WHERE target_col IS NOT NULL",
                        f"ALTER TABLE {table} ADD CONSTRAINT fk_child_{prefix}_{case_no} FOREIGN KEY (target_col) REFERENCES {parent} (target_col) {action}",
                    ]
                )
                if foreign_key_profile in {"cascade", "set_null"}:
                    post_statements.append(f"DELETE FROM {parent} WHERE id=1")
            else:
                child = f"tuc_fk_child_{prefix}_{case_no}"
                nullable = "NULL"
                if foreign_key_profile == "composite":
                    post_statements.append(f"ALTER TABLE {table} ADD KEY idx_fk_composite_{case_no} (part_key,target_col)")
                post_statements.extend(
                    [
                        f"CREATE TABLE {child} (id BIGINT NOT NULL PRIMARY KEY, parent_id {fk_type} {nullable}, part_key INT NOT NULL, KEY idx_parent_id (parent_id), KEY idx_parent_part (part_key,parent_id))",
                    ]
                )
                if foreign_key_profile == "composite":
                    post_statements.append(
                        f"ALTER TABLE {child} ADD CONSTRAINT fk_composite_{prefix}_{case_no} FOREIGN KEY (part_key,parent_id) REFERENCES {table} (part_key,target_col) {action}"
                    )
                else:
                    post_statements.append(
                        f"ALTER TABLE {child} ADD CONSTRAINT fk_parent_{prefix}_{case_no} FOREIGN KEY (parent_id) REFERENCES {table} (target_col) {action}"
                    )
                post_statements.append(
                    f"INSERT INTO {child} (id,parent_id,part_key) SELECT id+1000,target_col,part_key FROM {table} WHERE target_col IS NOT NULL"
                )
                if foreign_key_profile in {"cascade", "set_null"}:
                    post_statements.append(f"DELETE FROM {table} WHERE id=1")

    if dependency_profile.startswith("trigger_") and dependency_profile.endswith("_insert") and transition.positive:
        for prefix in ("ref", "algo"):
            table = ref_table if prefix == "ref" else algo_table
            post_statements.append(
                f"INSERT INTO {table} "
                f"(id,target_col,part_key,canary_int,canary_varchar,canary_varbinary,canary_decimal) "
                f"VALUES (300, {post_values[0] if post_values else transition.seed_values[0]}, 0, 300, 'trg', x'04', 300.0000)"
            )
    elif dependency_profile.startswith("trigger_") and dependency_profile.endswith("_update") and transition.positive:
        for prefix in ("ref", "algo"):
            table = ref_table if prefix == "ref" else algo_table
            post_statements.append(
                f"UPDATE {table} SET target_col={post_values[0] if post_values else transition.seed_values[0]} WHERE id=1"
            )
    elif dependency_profile.startswith("trigger_") and dependency_profile.endswith("_delete") and transition.positive:
        for prefix in ("ref", "algo"):
            table = ref_table if prefix == "ref" else algo_table
            post_statements.append(f"DELETE FROM {table} WHERE id=1")
    elif dependency_profile == "function_read" and transition.positive:
        for prefix in ("ref", "algo"):
            table = ref_table if prefix == "ref" else algo_table
            post_statements.append(
                f"INSERT INTO tuc_fn_result_{prefix}_{case_no} "
                f"SELECT id, tuc_fn_{prefix}_{case_no}(id) FROM {table}"
            )
    elif dependency_profile == "procedure_write" and transition.positive:
        value = post_values[0] if post_values else transition.seed_values[0]
        for prefix in ("ref", "algo"):
            post_statements.append(f"CALL tuc_proc_{prefix}_{case_no}(301, CAST({value} AS CHAR))")
    elif dependency_profile == "prepared_statement" and transition.positive:
        value = post_values[0] if post_values else transition.seed_values[0]
        for prefix in ("ref", "algo"):
            table = ref_table if prefix == "ref" else algo_table
            post_statements.extend(
                [
                    f"SET @tuc_value_{prefix}_{case_no} = {value}",
                    f"PREPARE tuc_stmt_{prefix}_{case_no} FROM "
                    f"'INSERT INTO {table} (id,target_col,part_key,canary_int,canary_varchar,canary_varbinary,canary_decimal) "
                    f"VALUES (302, ?, 0, 302, ''prepare'', x''05'', 302.0000)'",
                    f"EXECUTE tuc_stmt_{prefix}_{case_no} USING @tuc_value_{prefix}_{case_no}",
                    f"DEALLOCATE PREPARE tuc_stmt_{prefix}_{case_no}",
                ]
            )

    if table_form == "temporary":
        meta_ref = f"tuc_meta_ref_{case_no}"
        meta_algo = f"tuc_meta_algo_{case_no}"
        data_ref = f"tuc_data_ref_{case_no}"
        data_algo = f"tuc_data_algo_{case_no}"
        cleanup_tables.extend([meta_ref, meta_algo, data_ref, data_algo])
        post_statements.extend(
            [
                f"CREATE TABLE {meta_ref} LIKE {ref_table}",
                f"CREATE TABLE {meta_algo} LIKE {algo_table}",
                f"CREATE TABLE {data_ref} AS SELECT id,target_col,part_key,canary_int,canary_varchar,canary_varbinary,canary_decimal FROM {ref_table}",
                f"CREATE TABLE {data_algo} AS SELECT id,target_col,part_key,canary_int,canary_varchar,canary_varbinary,canary_decimal FROM {algo_table}",
            ]
        )
        verify = [_schema_check(meta_ref, meta_algo), _data_check(data_ref, data_algo, transition.family)]
    else:
        verify = [_schema_check(ref_table, algo_table), _data_check(ref_table, algo_table, transition.family)]
        verify.append(_index_check(ref_table, algo_table))
    if table_form == "temporary":
        verify.append(_index_check(f"tuc_meta_ref_{case_no}", f"tuc_meta_algo_{case_no}"))
    if foreign_key_profile in {"parent", "cascade", "set_null", "restrict", "no_action", "composite"}:
        child_ref = f"tuc_fk_child_ref_{case_no}"
        child_algo = f"tuc_fk_child_algo_{case_no}"
        verify.extend([_fk_check(child_ref, child_algo), _index_check(child_ref, child_algo)])
    elif foreign_key_profile in {"child", "self_reference"}:
        verify.append(_fk_check(ref_table, algo_table))
    elif foreign_key_profile == "multi_level":
        level1_ref = f"tuc_fk_level1_ref_{case_no}"
        level1_algo = f"tuc_fk_level1_algo_{case_no}"
        level2_ref = f"tuc_fk_level2_ref_{case_no}"
        level2_algo = f"tuc_fk_level2_algo_{case_no}"
        verify.extend(
            [
                _fk_check(level1_ref, level1_algo),
                _index_check(level1_ref, level1_algo),
                _fk_check(level2_ref, level2_algo),
                _index_check(level2_ref, level2_algo),
            ]
        )
    if dependency_profile.startswith("trigger_"):
        verify.append(_generic_table_check(f"tuc_audit_ref_{case_no}", f"tuc_audit_algo_{case_no}"))
    elif dependency_profile == "function_read":
        verify.append(_value_table_check(f"tuc_fn_result_ref_{case_no}", f"tuc_fn_result_algo_{case_no}"))
    elif dependency_profile == "view":
        verify.append(_data_check(f"tuc_view_ref_{case_no}", f"tuc_view_algo_{case_no}", transition.family))

    cleanup_statements = []
    for table in reversed(cleanup_tables):
        if table_form == "temporary":
            cleanup_statements.append(f"DROP TEMPORARY TABLE IF EXISTS {table}")
        else:
            cleanup_statements.append(f"DROP TABLE IF EXISTS {table}")
    # Views/functions/procedures use non-table DROP statements.
    for prefix in ("ref", "algo"):
        if dependency_profile == "view":
            cleanup_statements.append(f"DROP VIEW IF EXISTS tuc_view_{prefix}_{case_no}")
        elif dependency_profile.startswith("trigger_"):
            action, event = dependency_profile.removeprefix("trigger_").split("_", 1)
            cleanup_statements.append(f"DROP TRIGGER IF EXISTS tuc_trg_{action}_{event}_{prefix}_{case_no}")
        elif dependency_profile == "function_read":
            cleanup_statements.append(f"DROP FUNCTION IF EXISTS tuc_fn_{prefix}_{case_no}")
        elif dependency_profile == "procedure_write":
            cleanup_statements.append(f"DROP PROCEDURE IF EXISTS tuc_proc_{prefix}_{case_no}")

    return TypeUpgradeCase(
        case_id=f"{TYPE_UPGRADE_CASE_PREFIX}-{case_no:06d}",
        batch_id=TYPE_UPGRADE_BATCH_ID,
        batch_kind=TYPE_UPGRADE_BATCH_KIND,
        cluster=cluster,
        family=transition.family,
        source_type=transition.source_type,
        target_type=transition.target_type,
        expected_outcome="success" if transition.positive else "reject",
        data_profile=data_profile,
        column_attribute=attribute,
        index_profile=index_profile,
        foreign_key_profile=foreign_key_profile,
        dependency_profile=dependency_profile,
        table_form=table_form,
        sql_mode=sql_mode,
        charset=transition.charset,
        collation=transition.collation,
        seed_values=seed_values,
        post_ddl_values=post_values,
        invalid_values=transition.invalid_values,
        reason=transition.reason,
        setup_sql=tuple(base_setup) + tuple(seed_statements),
        ddl_sql=ddl_sql,
        post_ddl_sql=tuple(post_statements),
        invalid_post_ddl_sql=tuple(invalid_statements),
        verify_sql=tuple(verify),
        cleanup_sql=tuple(cleanup_statements),
    )


def _full_key_index_supported(transition: TypeTransition) -> bool:
    if transition.family not in {"character", "binary"}:
        return True
    if transition.source_type.endswith("TEXT") or transition.source_type.endswith("BLOB"):
        return False
    if transition.target_type.endswith("TEXT") or transition.target_type.endswith("BLOB"):
        return False

    def length(type_name: str) -> int:
        return int(type_name.split("(", 1)[1].split(")", 1)[0])

    multiplier = {"latin1": 1, "ascii": 1, "utf8mb3": 3, "utf8mb4": 4}.get(transition.charset or "", 1)
    return max(length(transition.source_type), length(transition.target_type)) * multiplier <= 2816


def _compatible_index_profiles(family: str, source_type: str) -> tuple[str, ...]:
    if family in {"character", "binary"} and not source_type.endswith("TEXT") and not source_type.endswith("BLOB"):
        profiles = ["secondary", "unique", "composite", "prefix", "descending", "invisible_index"]
        if source_type.startswith(("CHAR(", "VARCHAR(", "BINARY(", "VARBINARY(")):
            length = int(source_type.split("(", 1)[1].split(")", 1)[0])
            if length <= 1:
                profiles.remove("prefix")
        return tuple(profiles)
    if family in {"integer", "decimal"}:
        return ("secondary", "unique", "composite", "descending", "invisible_index", "functional", "generated")
    if family == "bit":
        return ("secondary", "unique", "composite", "descending", "invisible_index")
    return ("secondary", "unique", "composite", "descending", "invisible_index")


def generate_cases() -> list[TypeUpgradeCase]:
    catalog = build_factor_catalog()
    positive = _all_positive_transitions(catalog)
    negative = _all_negative_transitions(catalog)
    cases: list[TypeUpgradeCase] = []
    case_counter = count(1)

    def add(**kwargs: Any) -> None:
        cases.append(_build_case(next(case_counter), **kwargs))

    # Base cluster: every positive transition with two data profiles.
    for transition in positive:
        add(
            cluster=f"{transition.family}_base",
            transition=transition,
            data_profile="boundary",
            attribute="nullable" if transition.family != "integer" else "nullable",
            index_profile="none",
        )
        add(
            cluster=f"{transition.family}_base",
            transition=transition,
            data_profile="null_and_default",
            attribute="not_null_default",
            index_profile="none",
        )
    for transition in negative:
        add(
            cluster=f"{transition.family}_base",
            transition=transition,
            data_profile="boundary",
            attribute="nullable",
            index_profile="none",
        )

    # Attribute interactions: every positive transition with five attribute profiles.
    for transition in positive:
        for attribute in ("nullable", "not_null_default", "expression_default", "comment", "invisible", "first", "auto_increment"):
            add(
                cluster="column_attribute",
                transition=transition,
                data_profile="boundary",
                attribute=attribute,
                index_profile="none",
            )
            if attribute == "auto_increment" and transition.family != "integer":
                cases.pop()
            if attribute == "expression_default" and (
                transition.source_type.endswith(("TEXT", "BLOB"))
                or transition.target_type.endswith(("TEXT", "BLOB"))
            ):
                cases.pop()

    # Index interactions: every positive transition with compatible index profiles.
    for transition in positive:
        index_profiles = _compatible_index_profiles(transition.family, transition.source_type)
        if transition.family in {"character", "binary"} and not _full_key_index_supported(transition):
            index_profiles = ("prefix",)
        for index_profile in index_profiles:
            add(
                cluster="index",
                transition=transition,
                data_profile="boundary",
                attribute="nullable",
                index_profile=index_profile,
            )

    # Foreign key interactions use representative compatible transitions.
    fk_anchors = tuple(
        transition
        for transition in positive
        if (
            transition.family == "integer"
            and transition.source_type in {"TINYINT", "SMALLINT", "INT", "BIGINT"}
            and transition.target_type in {"SMALLINT", "INT", "BIGINT"}
        )
        or (
            transition.family == "character"
            and transition.source_type == "VARCHAR(255)"
            and transition.target_type == "VARCHAR(256)"
        )
        or (
            transition.family == "binary"
            and transition.source_type == "VARBINARY(255)"
            and transition.target_type == "VARBINARY(256)"
        )
    )
    for transition in fk_anchors:
        for profile in ("parent", "child", "self_reference", "composite", "cascade", "set_null", "restrict", "no_action", "multi_level"):
            add(
                cluster="foreign_key",
                transition=transition,
                data_profile="boundary",
                attribute="not_null_default" if profile in {"parent", "child", "composite"} else "nullable",
                index_profile="secondary",
                foreign_key_profile=profile,
            )

    # Dependency object interactions use one anchor per family and type shape.
    dependency_anchors: list[TypeTransition] = []
    for family in ("integer", "decimal", "character", "binary", "bit"):
        dependency_anchors.extend(
            transition for transition in positive if transition.family == family
        )
    dependency_anchors = dependency_anchors[:: max(1, len(dependency_anchors) // 20)]
    for transition in dependency_anchors:
        dependency_index_profile = "secondary" if _full_key_index_supported(transition) else "prefix"
        for profile in ("view", "trigger_before_insert", "trigger_after_insert", "trigger_before_update", "trigger_after_update", "trigger_before_delete", "trigger_after_delete", "function_read", "procedure_write", "prepared_statement"):
            add(
                cluster="dependency",
                transition=transition,
                data_profile="boundary",
                attribute="nullable",
                index_profile=dependency_index_profile,
                dependency_profile=profile,
            )

    # Table form interactions use a deterministic sample across families.
    table_anchors: list[TypeTransition] = []
    for family in ("integer", "decimal", "character", "binary", "bit"):
        family_items = [item for item in positive if item.family == family]
        table_anchors.extend(family_items[:: max(1, len(family_items) // 12)])
    for transition in table_anchors:
        for form in ("temporary", "range_partition", "list_partition", "hash_partition", "key_partition", "compact", "redundant", "compressed", "instant_history"):
            add(
                cluster="table_form",
                transition=transition,
                data_profile="boundary",
                attribute="nullable",
                index_profile="none",
                table_form=form,
            )

    # SQL mode interactions are limited to modes that change the retained type semantics.
    mode_anchors = table_anchors[:: max(1, len(table_anchors) // 20)]
    for transition in mode_anchors:
        for mode in ("STRICT_TRANS_TABLES", "PAD_CHAR_TO_FULL_LENGTH", "ANSI_QUOTES", "NO_BACKSLASH_ESCAPES"):
            if (
                mode == "PAD_CHAR_TO_FULL_LENGTH"
                and transition.family == "character"
                and not (
                    (transition.source_type.startswith("CHAR") and transition.target_type.startswith("CHAR"))
                    or (transition.source_type.startswith("VARCHAR") and transition.target_type.startswith("VARCHAR"))
                )
            ):
                continue
            add(
                cluster="sql_mode",
                transition=transition,
                data_profile="boundary",
                attribute="nullable",
                index_profile="none",
                sql_mode=mode,
            )

    return cases


def render_case_sql(case: TypeUpgradeCase, profile: str) -> str:
    if profile not in _ALLOWED_PROFILES:
        raise ValueError(f"unsupported profile: {profile}")
    statements: list[str] = [
        f"-- CASE_ID: {case.case_id}",
        f"-- BATCH_ID: {case.batch_id}",
        f"-- BATCH_KIND: {case.batch_kind}",
        "SET foreign_key_checks=ON",
        f"SET SESSION sql_mode='{effective_sql_mode(case.sql_mode)}'",
    ]
    statements.extend(case.cleanup_sql)
    statements.extend(case.setup_sql)
    statements.append(case.ddl_sql.replace("${ALGORITHM}", profile.upper()))
    statements.extend(case.post_ddl_sql)
    statements.extend(sql for sql, _ in case.query_plans)
    statements.extend(case.verify_sql)
    statements.extend(case.cleanup_sql)
    statements.append("SET SESSION sql_mode=DEFAULT")
    return ";\n".join(statement.rstrip(";") for statement in statements) + ";\n"


def render_suite(cases: Sequence[TypeUpgradeCase], profile: str) -> str:
    if profile not in _ALLOWED_PROFILES:
        raise ValueError(f"unsupported profile: {profile}")
    header = (
        f"-- Generated MySQL type-upgrade consistency suite; profile={profile}\n"
        "-- This file is deterministic and intended for an isolated QA database.\n"
    )
    return header + "\n".join(render_case_sql(case, profile) for case in cases)


def suite_manifest(cases: Sequence[TypeUpgradeCase], profile: str) -> dict[str, Any]:
    if profile not in _ALLOWED_PROFILES:
        raise ValueError(f"unsupported profile: {profile}")
    payload = json.dumps([case.to_json() for case in cases], sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    digest = sha256(payload.encode("utf-8")).hexdigest()
    clusters: dict[str, int] = {}
    families: dict[str, int] = {}
    for case in cases:
        clusters[case.cluster] = clusters.get(case.cluster, 0) + 1
        families[case.family] = families.get(case.family, 0) + 1
    serialized = payload
    forbidden_absent = all(token not in serialized for token in FORBIDDEN_TYPE_TOKENS)
    return {
        "profile": profile,
        "batch_id": TYPE_UPGRADE_BATCH_ID,
        "batch_kind": TYPE_UPGRADE_BATCH_KIND,
        "case_id_prefix": TYPE_UPGRADE_CASE_PREFIX,
        "case_count": len(cases),
        "sha256": digest,
        "clusters": clusters,
        "families": families,
        "forbidden_types_absent": forbidden_absent,
    }
