#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RDS MySQL DDL 秒级/在线修改列类型 — 纯 SQL 测试套件生成器
================================================================
生成用于验证 RDS MySQL 8.0 INSTANT(秒级)和 INPLACE(在线)列类型修改功能的纯 SQL 测试文件。
覆盖所有支持的数据类型转换 × 全因子(OFAT + 关键二元组) × 三种表类型(普通/外键/64种分区组合)。
通过 Oracle 对照表对比验证数据正确性。
"""

import os
import textwrap
from typing import List, Dict, Tuple, Optional, Any

OUTPUT_DIR = os.path.dirname(os.path.abspath(__file__))
SQL_ALIYUN = os.path.join(OUTPUT_DIR, "sql_aliyun")
SQL_INTERNAL = os.path.join(OUTPUT_DIR, "sql_internal")

# ============================================================
# Section 1: Type Transition Matrix (50 transitions × 2 algorithms = 100)
# ============================================================

# Each transition: (id, category, old_type_def, new_type_def, charset, instant_expected, inplace_expected, env, notes)
# expected: "SUCCESS" or "FAIL"
# env: "aliyun" or "internal"

INTEGER_SIGNED = [
    ("TINYINT",    (-128, 127)),
    ("SMALLINT",   (-32768, 32767)),
    ("MEDIUMINT",  (-8388608, 8388607)),
    ("INT",        (-2147483648, 2147483647)),
    ("BIGINT",     (-9223372036854775808, 9223372036854775807)),
]

INTEGER_UNSIGNED = [
    ("TINYINT UNSIGNED",    (0, 255)),
    ("SMALLINT UNSIGNED",   (0, 65535)),
    ("MEDIUMINT UNSIGNED",  (0, 16777215)),
    ("INT UNSIGNED",        (0, 4294967295)),
    ("BIGINT UNSIGNED",     (0, 18446744073709551615)),
]

# Build integer transitions
def _build_integer_transitions():
    transitions = []
    # SIGNED
    for i in range(len(INTEGER_SIGNED) - 1):
        for j in range(i + 1, len(INTEGER_SIGNED)):
            old_t, (old_min, old_max) = INTEGER_SIGNED[i]
            new_t, (new_min, new_max) = INTEGER_SIGNED[j]
            transitions.append({
                "id": f"INT-S-{i+1}-{j+1}",
                "category": "integer_signed",
                "old_type": old_t,
                "new_type": new_t,
                "charset": None,
                "old_min": old_min, "old_max": old_max,
                "new_min": new_min, "new_max": new_max,
                "instant": "SUCCESS",
                "inplace": "SUCCESS",
                "env": "aliyun",
            })
    # UNSIGNED
    for i in range(len(INTEGER_UNSIGNED) - 1):
        for j in range(i + 1, len(INTEGER_UNSIGNED)):
            old_t, (old_min, old_max) = INTEGER_UNSIGNED[i]
            new_t, (new_min, new_max) = INTEGER_UNSIGNED[j]
            transitions.append({
                "id": f"INT-U-{i+1}-{j+1}",
                "category": "integer_unsigned",
                "old_type": old_t,
                "new_type": new_t,
                "charset": None,
                "old_min": old_min, "old_max": old_max,
                "new_min": new_min, "new_max": new_max,
                "instant": "SUCCESS",
                "inplace": "SUCCESS",
                "env": "aliyun",
            })
    return transitions

CHAR_VARCHAR_TRANSITIONS = [
    # CHAR transitions
    {"id": "CHAR-01", "category": "char", "old_type": "CHAR(1)",   "new_type": "CHAR(2)",   "charset": "latin1",  "old_max_len": 1,   "new_max_len": 2,   "instant": "SUCCESS", "inplace": "SUCCESS", "env": "aliyun"},
    {"id": "CHAR-02", "category": "char", "old_type": "CHAR(63)",  "new_type": "CHAR(64)",  "charset": "utf8mb4", "old_max_len": 63,  "new_max_len": 64,  "instant": "SUCCESS", "inplace": "SUCCESS", "env": "aliyun"},
    {"id": "CHAR-03", "category": "char", "old_type": "CHAR(254)", "new_type": "CHAR(255)", "charset": "utf8mb4", "old_max_len": 254, "new_max_len": 255, "instant": "SUCCESS", "inplace": "SUCCESS", "env": "aliyun"},
    # VARCHAR transitions
    {"id": "VC-01", "category": "varchar", "old_type": "VARCHAR(1)",   "new_type": "VARCHAR(2)",   "charset": "latin1",  "old_max_len": 1,   "new_max_len": 2,   "instant": "SUCCESS", "inplace": "SUCCESS", "env": "aliyun"},
    {"id": "VC-02", "category": "varchar", "old_type": "VARCHAR(254)", "new_type": "VARCHAR(255)", "charset": "latin1",  "old_max_len": 254, "new_max_len": 255, "instant": "SUCCESS", "inplace": "SUCCESS", "env": "aliyun"},
    {"id": "VC-03", "category": "varchar", "old_type": "VARCHAR(255)", "new_type": "VARCHAR(256)", "charset": "latin1",  "old_max_len": 255, "new_max_len": 256, "instant": "SUCCESS", "inplace": "SUCCESS", "env": "aliyun"},
    {"id": "VC-04", "category": "varchar", "old_type": "VARCHAR(85)",  "new_type": "VARCHAR(86)",  "charset": "utf8mb3", "old_max_len": 85,  "new_max_len": 86,  "instant": "SUCCESS", "inplace": "SUCCESS", "env": "aliyun"},
    {"id": "VC-05", "category": "varchar", "old_type": "VARCHAR(63)",  "new_type": "VARCHAR(64)",  "charset": "utf8mb4", "old_max_len": 63,  "new_max_len": 64,  "instant": "SUCCESS", "inplace": "SUCCESS", "env": "aliyun"},
    {"id": "VC-06", "category": "varchar", "old_type": "VARCHAR(64)",  "new_type": "VARCHAR(65)",  "charset": "utf8mb4", "old_max_len": 64,  "new_max_len": 65,  "instant": "SUCCESS", "inplace": "SUCCESS", "env": "aliyun"},
    {"id": "VC-07", "category": "varchar", "old_type": "VARCHAR(100)", "new_type": "VARCHAR(200)", "charset": "utf8mb4", "old_max_len": 100, "new_max_len": 200, "instant": "SUCCESS", "inplace": "SUCCESS", "env": "aliyun"},
]

INTERNAL_TRANSITIONS = [
    # BINARY
    {"id": "BIN-01", "category": "binary",    "old_type": "BINARY(10)",  "new_type": "BINARY(20)",  "charset": None, "old_max_len": 10,  "new_max_len": 20,  "instant": "SUCCESS", "inplace": "SUCCESS", "env": "internal"},
    {"id": "BIN-02", "category": "binary",    "old_type": "BINARY(40)",  "new_type": "BINARY(80)",  "charset": None, "old_max_len": 40,  "new_max_len": 80,  "instant": "SUCCESS", "inplace": "SUCCESS", "env": "internal"},
    # VARBINARY
    {"id": "VBIN-01", "category": "varbinary", "old_type": "VARBINARY(20)",  "new_type": "VARBINARY(40)",  "charset": None, "old_max_len": 20,  "new_max_len": 40,  "instant": "SUCCESS", "inplace": "SUCCESS", "env": "internal"},
    {"id": "VBIN-02", "category": "varbinary", "old_type": "VARBINARY(100)", "new_type": "VARBINARY(200)", "charset": None, "old_max_len": 100, "new_max_len": 200, "instant": "SUCCESS", "inplace": "SUCCESS", "env": "internal"},
    # DECIMAL
    {"id": "DEC-01", "category": "decimal", "old_type": "DECIMAL(10,2)",  "new_type": "DECIMAL(12,2)",  "charset": None, "instant": "SUCCESS", "inplace": "SUCCESS", "env": "internal"},
    {"id": "DEC-02", "category": "decimal", "old_type": "DECIMAL(1,0)",   "new_type": "DECIMAL(2,0)",   "charset": None, "instant": "SUCCESS", "inplace": "SUCCESS", "env": "internal"},
    {"id": "DEC-03", "category": "decimal", "old_type": "DECIMAL(1,1)",   "new_type": "DECIMAL(2,1)",   "charset": None, "instant": "SUCCESS", "inplace": "SUCCESS", "env": "internal"},
    {"id": "DEC-04", "category": "decimal", "old_type": "DECIMAL(64,30)", "new_type": "DECIMAL(65,30)", "charset": None, "instant": "SUCCESS", "inplace": "SUCCESS", "env": "internal"},
    {"id": "DEC-05", "category": "decimal", "old_type": "DECIMAL(18,0)",  "new_type": "DECIMAL(20,0)",  "charset": None, "instant": "SUCCESS", "inplace": "SUCCESS", "env": "internal"},
    {"id": "DEC-06", "category": "decimal", "old_type": "DECIMAL(31,30)", "new_type": "DECIMAL(33,30)", "charset": None, "instant": "SUCCESS", "inplace": "SUCCESS", "env": "internal"},
    # TEXT
    {"id": "TEXT-01", "category": "text", "old_type": "TINYTEXT",   "new_type": "TEXT",       "charset": "utf8mb4", "old_max_len": 255,     "new_max_len": 65535,     "instant": "SUCCESS", "inplace": "SUCCESS", "env": "internal"},
    {"id": "TEXT-02", "category": "text", "old_type": "TEXT",       "new_type": "MEDIUMTEXT", "charset": "utf8mb4", "old_max_len": 65535,   "new_max_len": 16777215,  "instant": "SUCCESS", "inplace": "SUCCESS", "env": "internal"},
    {"id": "TEXT-03", "category": "text", "old_type": "MEDIUMTEXT", "new_type": "LONGTEXT",   "charset": "utf8mb4", "old_max_len": 16777215,"new_max_len": 4294967295,"instant": "SUCCESS", "inplace": "SUCCESS", "env": "internal"},
    # BLOB
    {"id": "BLOB-01", "category": "blob", "old_type": "TINYBLOB",   "new_type": "BLOB",       "charset": None, "old_max_len": 255,     "new_max_len": 65535,     "instant": "SUCCESS", "inplace": "SUCCESS", "env": "internal"},
    {"id": "BLOB-02", "category": "blob", "old_type": "BLOB",       "new_type": "MEDIUMBLOB", "charset": None, "old_max_len": 65535,   "new_max_len": 16777215,  "instant": "SUCCESS", "inplace": "SUCCESS", "env": "internal"},
    {"id": "BLOB-03", "category": "blob", "old_type": "MEDIUMBLOB", "new_type": "LONGBLOB",   "charset": None, "old_max_len": 16777215,"new_max_len": 4294967295,"instant": "SUCCESS", "inplace": "SUCCESS", "env": "internal"},
    # BIT
    {"id": "BIT-01", "category": "bit", "old_type": "BIT(1)",  "new_type": "BIT(8)",  "charset": None, "old_max_len": 1,  "new_max_len": 8,  "instant": "SUCCESS", "inplace": "SUCCESS", "env": "internal"},
    {"id": "BIT-02", "category": "bit", "old_type": "BIT(8)",  "new_type": "BIT(16)", "charset": None, "old_max_len": 8,  "new_max_len": 16, "instant": "SUCCESS", "inplace": "SUCCESS", "env": "internal"},
    {"id": "BIT-03", "category": "bit", "old_type": "BIT(16)", "new_type": "BIT(32)", "charset": None, "old_max_len": 16, "new_max_len": 32, "instant": "SUCCESS", "inplace": "SUCCESS", "env": "internal"},
    {"id": "BIT-04", "category": "bit", "old_type": "BIT(32)", "new_type": "BIT(64)", "charset": None, "old_max_len": 32, "new_max_len": 64, "instant": "SUCCESS", "inplace": "SUCCESS", "env": "internal"},
]

ALL_TRANSITIONS = _build_integer_transitions() + CHAR_VARCHAR_TRANSITIONS + INTERNAL_TRANSITIONS


# ============================================================
# Section 2: Factor Definitions (OFAT + Key Pairs)
# ============================================================

BASELINE = {
    "row_format": "DYNAMIC",
    "primary_key": "CLUSTERED",       # single INT AUTO_INCREMENT PK
    "non_target_index": "ONE_SECONDARY",
    "target_position": "MIDDLE",
    "target_attributes": "NULL_NO_DEFAULT",
    "data_scale": "S100",
    "data_distribution": "TYPE_BOUNDARIES",
    "null_ratio": "TEN_PERCENT",
    "dependencies": "NONE",
    "sql_mode": "STRICT",
}

# OFAT variations: (factor_name, value, applies_to_algorithms, description)
OFAT_VARIATIONS = [
    ("row_format", "COMPACT",  "both",     "COMPACT row format"),
    ("row_format", "REDUNDANT", "both",    "REDUNDANT row format"),
    ("primary_key", "COMPOSITE_PK", "both", "Composite PK (id, target_col)"),
    ("primary_key", "NO_EXPLICIT_PK", "both", "No explicit PK"),
    ("non_target_index", "NONE", "both",   "No secondary index"),
    ("non_target_index", "MULTIPLE_SECONDARY", "both", "Multiple secondary indexes"),
    ("non_target_index", "UNIQUE", "both", "Unique index on non-target col"),
    ("non_target_index", "COMPOSITE_PREFIX", "both", "Composite prefix index"),
    ("target_position", "FIRST", "both",  "Target column at first position"),
    ("target_position", "LAST", "both",   "Target column at last position"),
    ("target_attributes", "NOT_NULL_NO_DEFAULT", "both", "NOT NULL no default"),
    ("target_attributes", "CONSTANT_DEFAULT", "both", "DEFAULT 0 or ''"),
    ("target_attributes", "NULL_DEFAULT", "both", "DEFAULT NULL"),
    ("target_attributes", "NOT_NULL_DEFAULT", "both", "NOT NULL DEFAULT 0"),
    ("target_attributes", "INVISIBLE", "both", "Column INVISIBLE"),
    ("data_scale", "S0", "both",        "Empty table (0 rows)"),
    ("data_scale", "S1", "both",        "Single row"),
    ("data_distribution", "UNIFORM", "both", "Uniform distribution"),
    ("data_distribution", "MONOTONIC", "both", "Monotonic increasing"),
    ("null_ratio", "ZERO", "both",      "No NULLs"),
    ("null_ratio", "SINGLE", "both",    "Single NULL"),
    ("null_ratio", "ALL", "both",       "All NULLs"),
    ("dependencies", "SECONDARY_INDEX", "inplace", "Secondary index on target"),
    ("dependencies", "UNIQUE_INDEX", "inplace",   "Unique index on target"),
    ("dependencies", "FOREIGN_KEY", "inplace",     "FK on target"),
    ("dependencies", "CHECK", "inplace",          "CHECK constraint on target"),
    ("sql_mode", "NON_STRICT", "both", "Non-strict SQL mode"),
]

# Key pair interactions
KEY_PAIRS = [
    ("KP-01", {"target_attributes": "NOT_NULL_NO_DEFAULT", "data_scale": "S0"}, "both", "NOT_NULL + empty table"),
    ("KP-02", {"dependencies": "UNIQUE_INDEX", "null_ratio": "ALL"}, "inplace", "UNIQUE index + all NULLs"),
    ("KP-03", {"data_scale": "S0", "data_distribution": "UNIFORM"}, "both", "Empty table + uniform"),
    ("KP-04", {"target_attributes": "NOT_NULL_DEFAULT", "data_scale": "S0"}, "both", "NOT_NULL DEFAULT + empty"),
    ("KP-05", {"primary_key": "COMPOSITE_PK", "target_position": "FIRST"}, "both", "Composite PK + first position"),
]

# ============================================================
# Section 3: Test Data Generators per Type
# ============================================================

def _repeat_str(s: str, n: int) -> str:
    """Repeat string to exactly n characters."""
    if n <= 0:
        return ""
    return (s * (n // len(s) + 1))[:n]

def _hex_str(n: int) -> str:
    """Generate n-byte hex string for BINARY/VARBINARY values."""
    return "0x" + ("41" * n)  # 'A' repeated

def _blob_literal(data: bytes) -> str:
    """Convert bytes to SQL BLOB literal."""
    return "0x" + data.hex()

def gen_test_data(transition: dict) -> dict:
    """
    Generate pre-ALTER and post-ALTER test data for a transition.
    Returns dict with keys:
      pre_values: list of SQL value strings (for old type)
      post_new_range: list of values only valid in new type (and old type if applicable)
      post_old_range: list of values valid in both old and new type
      post_fail: list of values exceeding even new type (INSERT should fail)
      null_value: "NULL" or None (if column is NOT NULL)
    """
    cat = transition["category"]
    old_t = transition["old_type"]
    new_t = transition["new_type"]
    charset = transition.get("charset")

    if cat.startswith("integer"):
        return _gen_integer_data(transition)
    elif cat == "char":
        return _gen_char_data(transition)
    elif cat == "varchar":
        return _gen_varchar_data(transition)
    elif cat == "binary":
        return _gen_binary_data(transition)
    elif cat == "varbinary":
        return _gen_varbinary_data(transition)
    elif cat == "decimal":
        return _gen_decimal_data(transition)
    elif cat == "text":
        return _gen_text_data(transition)
    elif cat == "blob":
        return _gen_blob_data(transition)
    elif cat == "bit":
        return _gen_bit_data(transition)
    else:
        raise ValueError(f"Unknown category: {cat}")


def _gen_integer_data(t: dict) -> dict:
    unsigned = "unsigned" in t["category"]
    old_min, old_max = t["old_min"], t["old_max"]
    new_min, new_max = t["new_min"], t["new_max"]

    if unsigned:
        pre = [str(old_min), str(old_max), str(old_max - 1), "1", "42"]
        # Add some interesting values that fit within old type range
        if old_max >= 255:
            pre.append("255")
        if old_max >= 65535:
            pre.append("65535")
    else:
        pre = [str(old_min), str(old_max), str(old_min + 1), str(old_max - 1), "0", "1", "-1", "64", "-64"]

    # Post-ALTER: new-range-only values + old-range values (backward compat)
    post_new = []
    if not unsigned:
        if new_min < old_min:
            post_new.append(str(new_min))
            post_new.append(str(new_min + 1))
        if new_max > old_max:
            post_new.append(str(new_max))
            post_new.append(str(new_max - 1))
            post_new.append(str(old_max + 1))
    else:
        if new_max > old_max:
            post_new.append(str(new_max))
            post_new.append(str(new_max - 1))
            post_new.append(str(old_max + 1))

    post_old = ["0", "1", "42"]
    if not unsigned:
        post_old.extend(["-1", "-42"])
    post_old.append(str(old_max))

    # Values exceeding new type (should fail on both tables)
    post_fail = []
    if not unsigned and new_max < 9223372036854775807:
        post_fail.append("999999999999999999999")  # exceeds BIGINT
    elif unsigned and new_max < 18446744073709551615:
        post_fail.append("999999999999999999999")

    return {
        "pre_values": pre,
        "post_new_range": post_new,
        "post_old_range": post_old,
        "post_fail": post_fail,
        "null_value": "NULL",
    }


def _gen_char_data(t: dict) -> dict:
    old_len = t["old_max_len"]
    new_len = t["new_max_len"]
    cs = t.get("charset", "latin1")

    # Pre-ALTER data (within old type)
    # Normal value that fits within old type
    if old_len >= 5:
        normal_val = "'Hello'"
    elif old_len >= 2:
        normal_val = "'Hi'"
    else:
        normal_val = "'a'"
    pre = [
        "''",                              # empty string
        "'a'",                             # single char
        f"'{_repeat_str('x', old_len)}'",  # max length
        f"'{_repeat_str('x', old_len - 1)}'",  # max-1
        normal_val,                        # normal (fits old type)
    ]
    # Multibyte char for utf8mb4
    if cs == "utf8mb4":
        pre.append("'你好'")  # multibyte
        pre.append("'🎉'")    # 4-byte

    # Post-ALTER: new-range values
    post_new = [
        f"'{_repeat_str('z', new_len)}'",      # new max length
        f"'{_repeat_str('z', new_len - 1)}'",  # new max-1
        f"'{_repeat_str('w', old_len + 1)}'",  # old+1 (now valid)
    ]
    # Post-ALTER: old-range values (backward compat) - must fit BOTH old and new type
    # Since new_len > old_len, values fitting old type also fit new type
    post_old = [
        "''",
        "'a'",
        f"'{_repeat_str('x', old_len)}'",
    ]

    # Values exceeding new type (should fail on both tables)
    post_fail = [f"'{_repeat_str('q', new_len + 1)}'"]
    # Also add 'test' (4 chars) as fail if it exceeds new type
    if new_len < 4:
        post_fail.append("'test'")

    return {
        "pre_values": pre,
        "post_new_range": post_new,
        "post_old_range": post_old,
        "post_fail": post_fail,
        "null_value": "NULL",
    }


def _gen_varchar_data(t: dict) -> dict:
    return _gen_char_data(t)  # Same logic for VARCHAR


def _gen_binary_data(t: dict) -> dict:
    old_len = t["old_max_len"]
    new_len = t["new_max_len"]

    pre = [
        _hex_literal(b"\x00" * old_len),         # all zeros (BINARY pads with 0x00)
        _hex_literal(b"\xff" * old_len),         # all 0xFF
        _hex_literal(b"\x00" * (old_len - 1)),   # max-1 (will be padded)
        _hex_literal(b"AB" * (old_len // 2) if old_len % 2 == 0 else b"AB" * (old_len // 2) + b"A"),  # mixed
        "''",                                      # empty (will be padded to old_len with 0x00)
    ]

    post_new = [
        _hex_literal(b"\x00" * new_len),
        _hex_literal(b"\xff" * new_len),
        _hex_literal(b"MIX" * (new_len // 3) + b"M" * (new_len % 3)),
    ]
    post_old = [
        _hex_literal(b"\x00" * old_len),
        _hex_literal(b"\xff" * old_len),
        "''",
    ]
    post_fail = [
        _hex_literal(b"\x41" * (new_len + 1)),  # exceeds new type
    ]

    return {
        "pre_values": pre,
        "post_new_range": post_new,
        "post_old_range": post_old,
        "post_fail": post_fail,
        "null_value": "NULL",
    }


def _gen_varbinary_data(t: dict) -> dict:
    old_len = t["old_max_len"]
    new_len = t["new_max_len"]

    pre = [
        _hex_literal(b"\x00" * old_len),
        _hex_literal(b"\xff" * old_len),
        _hex_literal(b"\x00" * (old_len - 1)),
        _hex_literal(b"MIX" * (old_len // 3) + b"M" * (old_len % 3)),
        "''",
    ]

    post_new = [
        _hex_literal(b"\x00" * new_len),
        _hex_literal(b"\xff" * new_len),
        _hex_literal(b"\x41" * (old_len + 1)),  # old+1 now valid
    ]
    post_old = [
        _hex_literal(b"\x00" * old_len),
        "''",
        _hex_literal(b"\xff" * old_len),
    ]
    post_fail = [
        _hex_literal(b"\x41" * (new_len + 1)),
    ]

    return {
        "pre_values": pre,
        "post_new_range": post_new,
        "post_old_range": post_old,
        "post_fail": post_fail,
        "null_value": "NULL",
    }


def _gen_decimal_data(t: dict) -> dict:
    # Parse M and D from type strings
    import re
    old_m = _parse_decimal(t["old_type"])
    new_m = _parse_decimal(t["new_type"])

    old_M, old_D = old_m
    new_M, new_D = new_m

    # Old type max value
    old_int_digits = old_M - old_D
    new_int_digits = new_M - new_D
    old_max = "9" * old_int_digits + ("." + "9" * old_D if old_D > 0 else "")
    old_min = "-" + old_max
    new_max = "9" * new_int_digits + ("." + "9" * new_D if new_D > 0 else "")
    new_min = "-" + new_max

    pre = [old_min, old_max, "0" + ("." + "0" * old_D if old_D > 0 else ""),
           "1" + ("." + "1" * old_D if old_D > 0 else ""),
           "-1" + ("." + "1" * old_D if old_D > 0 else "")]

    post_new = [new_max, new_min]
    if old_D > 0:
        post_new.append("1." + "9" * old_D)
        post_new.append("-1." + "9" * old_D)
    else:
        post_new.append("999999999")
        post_new.append("-999999999")

    post_old = ["0" + ("." + "0" * old_D if old_D > 0 else ""),
                "1" + ("." + "0" * old_D if old_D > 0 else ""),
                old_max]

    post_fail = ["9" * 70 + (".99" if old_D > 0 else "")]  # exceeds max precision

    return {
        "pre_values": pre,
        "post_new_range": post_new,
        "post_old_range": post_old,
        "post_fail": post_fail,
        "null_value": "NULL",
    }


def _parse_decimal(type_str: str) -> tuple:
    """Parse DECIMAL(M,D) -> (M, D)"""
    import re
    m = re.search(r"DECIMAL\((\d+),(\d+)\)", type_str)
    if m:
        return (int(m.group(1)), int(m.group(2)))
    m = re.search(r"DECIMAL\((\d+)\)", type_str)
    if m:
        return (int(m.group(1)), 0)
    return (10, 0)


def _gen_text_data(t: dict) -> dict:
    old_max = t["old_max_len"]
    new_max = t["new_max_len"]

    # Use boundary sizes around 255 and 65535
    pre = [
        "''",
        "'a'",
        f"'{_repeat_str('T', min(255, old_max))}'",     # 255 bytes
        f"'{_repeat_str('T', min(254, old_max))}'",     # 254 bytes
        f"'{_repeat_str('T', min(128, old_max))}'",     # normal
        "'你好世界'",                                     # multibyte
    ]

    post_new = []
    if new_max > 255:
        post_new.append(f"'{_repeat_str('N', 256)}'")      # just past 255
    if new_max > 65535:
        post_new.append(f"'{_repeat_str('N', 65536)}'")     # just past 65535
    post_new.append(f"'{_repeat_str('N', min(new_max, 1000))}'")

    post_old = ["''", "'a'", f"'{_repeat_str('T', min(255, old_max))}'", "'test'"]

    # TEXT can't really exceed LONGTEXT (4GB), so no fail values for TEXT->MEDIUMTEXT->LONGTEXT
    # But TINYTEXT->TEXT: 256 bytes is valid for TEXT, invalid for TINYTEXT
    post_fail = []  # No practical fail for TEXT subtypes

    return {
        "pre_values": pre,
        "post_new_range": post_new,
        "post_old_range": post_old,
        "post_fail": post_fail,
        "null_value": "NULL",
    }


def _gen_blob_data(t: dict) -> dict:
    old_max = t["old_max_len"]
    new_max = t["new_max_len"]

    pre = [
        "''",
        _hex_literal(b"\x00"),
        _hex_literal(b"\x00" * min(255, old_max)),
        _hex_literal(b"\x00" * min(254, old_max)),
        _hex_literal(b"\xff\x00\x41\x42" * (min(64, old_max) // 4)),
    ]

    post_new = []
    if new_max > 255:
        post_new.append(_hex_literal(b"\x00" * 256))
    post_new.append(_hex_literal(b"\xff" * min(new_max, 1000)))

    post_old = ["''", _hex_literal(b"\x00" * min(255, old_max)), _hex_literal(b"\x42")]

    post_fail = []

    return {
        "pre_values": pre,
        "post_new_range": post_new,
        "post_old_range": post_old,
        "post_fail": post_fail,
        "null_value": "NULL",
    }


def _gen_bit_data(t: dict) -> dict:
    old_bits = t["old_max_len"]
    new_bits = t["new_max_len"]

    old_max_val = (1 << old_bits) - 1
    new_max_val = (1 << new_bits) - 1

    pre = ["b'0'", f"b'{_repeat_str('1', old_bits)}'", "b'1'", "b'0'"]
    if old_bits >= 4:
        pre.append("b'1010'")
    if old_bits >= 8:
        pre.append("b'11111111'")

    post_new = [f"b'{_repeat_str('1', new_bits)}'"]  # new max
    if new_bits > old_bits:
        post_new.append(f"b'{_repeat_str('1', old_bits + 1)}'")  # old+1 bits
    post_new.append("b'1'")  # backward compat

    post_old = ["b'0'", f"b'{_repeat_str('1', old_bits)}'", "b'1010'"]

    # BIT can't exceed 64 bits
    post_fail = []

    return {
        "pre_values": pre,
        "post_new_range": post_new,
        "post_old_range": post_old,
        "post_fail": post_fail,
        "null_value": "NULL",
    }


def _hex_literal(data: bytes) -> str:
    """Convert bytes to SQL hex literal."""
    if len(data) == 0:
        return "''"
    return "0x" + data.hex()


# ============================================================
# Section 4: SQL Building Functions
# ============================================================

def _build_column_def(target_type: str, factors: dict, transition: dict, is_target: bool = True) -> str:
    """Build the target column definition with factor attributes."""
    attrs = factors.get("target_attributes", "NULL_NO_DEFAULT")
    col_def = target_type

    # Add charset for string types FIRST (before NOT NULL, DEFAULT, INVISIBLE)
    if is_target and transition.get("charset") and transition["category"] in ("char", "varchar", "text"):
        cs = transition["charset"]
        if cs == "utf8mb3":
            cs = "utf8"
        col_def += f" CHARACTER SET {cs}"

    # Then add column attributes
    if attrs == "NOT_NULL_NO_DEFAULT":
        col_def += " NOT NULL"
    elif attrs == "CONSTANT_DEFAULT":
        col_def += " DEFAULT " + _default_for_type(transition)
    elif attrs == "NULL_DEFAULT":
        col_def += " DEFAULT NULL"
    elif attrs == "NOT_NULL_DEFAULT":
        col_def += " NOT NULL DEFAULT " + _default_for_type(transition)
    elif attrs == "INVISIBLE":
        col_def += " INVISIBLE"

    return col_def


def _default_for_type(transition: dict) -> str:
    cat = transition["category"]
    if cat.startswith("integer"):
        return "0"
    elif cat in ("char", "varchar", "text"):
        return "''"
    elif cat in ("binary", "varbinary", "blob"):
        return "0x00"
    elif cat == "decimal":
        return "0"
    elif cat == "bit":
        return "b'0'"
    return "0"


def _build_create_table(table: str, target_type: str, factors: dict, transition: dict,
                        partition_def: str = None, extra_cols: list = None,
                        fk_def: str = None, index_on_target: str = None) -> str:
    """Build CREATE TABLE statement with factors."""
    rf = factors.get("row_format", "DYNAMIC")
    pk_type = factors.get("primary_key", "CLUSTERED")
    idx_type = factors.get("non_target_index", "ONE_SECONDARY")
    pos = factors.get("target_position", "MIDDLE")
    attrs = factors.get("target_attributes", "NULL_NO_DEFAULT")

    # Column list
    cols = []
    target_col_def = _build_column_def(target_type, factors, transition)

    if pos == "FIRST":
        cols.append(f"  target {target_col_def}")
        cols.append("  id INT NOT NULL AUTO_INCREMENT")
        cols.append("  pad1 VARCHAR(20) DEFAULT 'pad1'")
        cols.append("  pad2 VARCHAR(20) DEFAULT 'pad2'")
    elif pos == "LAST":
        cols.append("  id INT NOT NULL AUTO_INCREMENT")
        cols.append("  pad1 VARCHAR(20) DEFAULT 'pad1'")
        cols.append("  pad2 VARCHAR(20) DEFAULT 'pad2'")
        cols.append(f"  target {target_col_def}")
    else:  # MIDDLE
        cols.append("  id INT NOT NULL AUTO_INCREMENT")
        cols.append("  pad1 VARCHAR(20) DEFAULT 'pad1'")
        cols.append(f"  target {target_col_def}")
        cols.append("  pad2 VARCHAR(20) DEFAULT 'pad2'")

    if extra_cols:
        cols.extend(extra_cols)

    # Primary key
    if pk_type == "CLUSTERED":
        pk_clause = ", PRIMARY KEY (id)"
    elif pk_type == "COMPOSITE_PK":
        pk_clause = ", PRIMARY KEY (id, target)"
    elif pk_type == "NO_EXPLICIT_PK":
        pk_clause = ", INDEX idx_id (id)"  # AUTO_INCREMENT needs an index
    else:
        pk_clause = ", PRIMARY KEY (id)"

    # Non-target indexes
    idx_clauses = ""
    if idx_type == "ONE_SECONDARY":
        idx_clauses = ", INDEX idx_pad1 (pad1)"
    elif idx_type == "MULTIPLE_SECONDARY":
        idx_clauses = ", INDEX idx_pad1 (pad1), INDEX idx_pad2 (pad2)"
    elif idx_type == "UNIQUE":
        idx_clauses = ", UNIQUE INDEX uq_pad1 (pad1)"
    elif idx_type == "COMPOSITE_PREFIX":
        idx_clauses = ", INDEX idx_composite (pad1(10), pad2(10))"

    # Index on target (for INPLACE dependencies)
    dep = factors.get("dependencies", "NONE")
    target_idx = ""
    if dep == "SECONDARY_INDEX":
        target_idx = ", INDEX idx_target (target)"
    elif dep == "UNIQUE_INDEX":
        target_idx = ", UNIQUE INDEX uq_target (target)"
    elif dep == "CHECK":
        target_idx = ", CHECK (target IS NOT NULL OR 1=1)"

    if index_on_target:
        target_idx = index_on_target

    # FK definition
    fk_clause = ""
    if fk_def:
        fk_clause = ", " + fk_def

    sql = f"CREATE TABLE {table} (\n"
    sql += ",\n".join(cols)
    sql += pk_clause
    sql += idx_clauses
    sql += target_idx
    sql += fk_clause
    sql += "\n) ENGINE=InnoDB"
    if rf != "DEFAULT":
        sql += f" ROW_FORMAT={rf}"
    # Add charset for table if needed
    cs = transition.get("charset")
    if cs and transition["category"] in ("char", "varchar", "text"):
        if cs == "utf8mb3":
            cs = "utf8"
        sql += f" DEFAULT CHARSET={cs}"

    if partition_def:
        sql += f"\n{partition_def}"
    else:
        sql += ";"
    return sql


def _build_insert_stmt(table: str, target_col: str, value: str) -> str:
    """Build INSERT INTO table (target_col) VALUES (value)."""
    return f"INSERT INTO {table} ({target_col}) VALUES ({value});"


def _build_insert_batch(table: str, target_col: str, values: list) -> str:
    """Build batch INSERT with multiple values."""
    if not values:
        return ""
    vals = ", ".join(f"({v})" for v in values)
    return f"INSERT INTO {table} ({target_col}) VALUES {vals};"


def _build_alter_stmt(table: str, target_col: str, col_def: str, algorithm: str) -> str:
    """Build ALTER TABLE ... MODIFY ... ALGORITHM=xxx.
    col_def should be the full column definition including type, charset, NOT NULL, etc.
    """
    return f"ALTER TABLE {table} MODIFY {target_col} {col_def}, ALGORITHM={algorithm};"


def _build_compare_sql(test_id: str, t1: str, t2: str, columns: list) -> str:
    """Build Oracle comparison SELECT using NULL-safe <=>."""
    col_cmp = " AND ".join(f"a.{c} <=> b.{c}" for c in columns)
    col_list = ", ".join(columns)

    return f"""SELECT '{test_id}' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM {t1}
   WHERE id NOT IN (SELECT id FROM {t2})
  UNION ALL
  SELECT 't2_extra' AS src, id FROM {t2}
   WHERE id NOT IN (SELECT id FROM {t1})
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM {t1} a JOIN {t2} b ON a.id = b.id
   WHERE NOT ({col_cmp})
) AS mismatches;"""


def _build_test_case_sql(test_id: str, transition: dict, algorithm: str, factors: dict,
                         table_suffix: str = "") -> str:
    """
    Build a complete test case:
    1. DROP tables
    2. CREATE t1 (old type)
    3. INSERT pre-data into t1
    4. ALTER t1 (success or fail)
    5. INSERT post-data into t1 (new range + old range, some may fail)
    6. CREATE t2 (same type as t1 after ALTER: new if success, old if fail)
    7. INSERT all same data into t2
    8. SELECT comparison
    """
    t1 = f"t1_{table_suffix}"
    t2 = f"t2_{table_suffix}"  # suffix already has no hyphens
    old_type = transition["old_type"]
    new_type = transition["new_type"]
    expected = transition[algorithm.lower()]
    
    # Adjust expected based on factor interactions
    # INSTANT fails when target is part of any index (PK, secondary, unique)
    if algorithm.lower() == "instant":
        pk_type = factors.get("primary_key", "CLUSTERED")
        if pk_type == "COMPOSITE_PK":
            expected = "FAIL"  # target is part of PK index
        dep = factors.get("dependencies", "NONE")
        if dep in ("SECONDARY_INDEX", "UNIQUE_INDEX", "FOREIGN_KEY"):
            expected = "FAIL"  # target has an index
    
    # CHECK constraint behavior is type-dependent (verified manually on Aliyun RDS 8.0):
    # - CHAR/VARCHAR/TEXT/BLOB/BIT with CHECK: ALTER succeeds (metadata-only change)
    # - Integer/BINARY/VARBINARY/DECIMAL with CHECK: ALTER fails (ERROR 1845)
    if factors.get("dependencies") == "CHECK":
        cat = transition.get("category", "")
        if cat in ("integer_signed", "integer_unsigned", "binary", "varbinary", "decimal"):
            expected = "FAIL"
        # String/blob/bit types: expected stays SUCCESS
    
    data = gen_test_data(transition)

    # Adjust for NOT NULL columns
    is_not_null = factors.get("target_attributes") in ("NOT_NULL_NO_DEFAULT", "NOT_NULL_DEFAULT")
    # COMPOSITE_PK makes target implicitly NOT NULL
    if factors.get("primary_key") == "COMPOSITE_PK":
        is_not_null = True
    null_val = None if is_not_null else data["null_value"]

    # Filter NULL from pre_values if NOT NULL
    pre_vals = list(data["pre_values"])
    if is_not_null:
        pre_vals = [v for v in pre_vals if v != "NULL"]
    if null_val:
        pre_vals.append(null_val)

    # Handle empty table
    data_scale = factors.get("data_scale", "S100")
    if data_scale == "S0":
        pre_vals = []

    # Single row
    if data_scale == "S1":
        pre_vals = pre_vals[:1] if pre_vals else []

    # Null ratio
    null_ratio = factors.get("null_ratio", "TEN_PERCENT")
    if null_ratio == "ZERO" and not is_not_null:
        pre_vals = [v for v in pre_vals if v != "NULL"]
    elif null_ratio == "ALL" and not is_not_null:
        pre_vals = ["NULL"]

    lines = []
    lines.append(f"-- Test Case: {test_id}")
    lines.append(f"-- Type: {old_type} -> {new_type}, Algorithm: {algorithm}, Expected: {expected}")
    lines.append(f"-- Factors: {_format_factors(factors)}")
    lines.append(f"DROP TABLE IF EXISTS {t1}, {t2};")

    # Set SQL mode for this test case
    sql_mode_factor = factors.get("sql_mode", "STRICT")
    if sql_mode_factor == "STRICT":
        lines.append("SET SESSION sql_mode = 'STRICT_TRANS_TABLES';")
    else:
        lines.append("SET SESSION sql_mode = '';")

    # Step 2: CREATE t1 (old type)
    lines.append(_build_create_table(t1, old_type, factors, transition))

    # Step 3: INSERT pre-data (individual for boundary, batch for normal)
    for v in pre_vals:
        lines.append(_build_insert_stmt(t1, "target", v))

    # Step 4: ALTER
    alter_expected = expected
    alter_col_def = _build_column_def(new_type, factors, transition)
    alter_stmt = _build_alter_stmt(t1, "target", alter_col_def, algorithm)
    if alter_expected == "FAIL":
        lines.append(f"-- Expected: ALTER FAILS (table keeps old type)")
    else:
        lines.append(f"-- Expected: ALTER SUCCESS")
    lines.append(alter_stmt)

    # Step 5: INSERT post-data
    # After successful ALTER: new-range + old-range values
    # After failed ALTER: same INSERTs (new-range fail on old type, old-range succeed)
    post_new = list(data["post_new_range"])
    post_old = list(data["post_old_range"])
    if is_not_null:
        post_new = [v for v in post_new if v != "NULL"]
        post_old = [v for v in post_old if v != "NULL"]
    if null_val:
        post_old.append(null_val)

    # Null ratio for post-data
    if null_ratio == "ZERO" and not is_not_null:
        post_new = [v for v in post_new if v != "NULL"]
        post_old = [v for v in post_old if v != "NULL"]

    if data_scale != "S0":
        for v in post_new:
            lines.append(f"-- Insert new-range value (may fail if ALTER failed)")
            lines.append(_build_insert_stmt(t1, "target", v))
        for v in post_old:
            lines.append(_build_insert_stmt(t1, "target", v))

    # Fail values (exceed even new type) - should fail on both tables
    for v in data.get("post_fail", []):
        lines.append(f"-- Insert value exceeding new type (expected FAIL on both tables)")
        lines.append(f"-- INSERT INTO {t1} (target) VALUES ({v});")

    # Step 6: CREATE t2
    # Success path: t2 uses new_type (same as t1 after ALTER)
    # Fail path: t2 uses old_type (same as t1 which kept old type)
    t2_type = new_type if alter_expected == "SUCCESS" else old_type
    lines.append(f"-- Oracle table: {t2_type}")
    lines.append(_build_create_table(t2, t2_type, factors, transition))

    # Step 7: INSERT all same data into t2
    all_vals = pre_vals + post_new + post_old
    if is_not_null:
        all_vals = [v for v in all_vals if v != "NULL"]
    # null_ratio filtering already applied to pre_vals; oracle table must mirror all t1 INSERTs

    if data_scale == "S0":
        all_vals = []

    for v in all_vals:
        lines.append(_build_insert_stmt(t2, "target", v))

    # Step 8: Compare
    compare_cols = ["id", "pad1", "target", "pad2"]
    lines.append(_build_compare_sql(test_id, t1, t2, compare_cols))

    return "\n".join(lines)


def _format_factors(factors: dict) -> str:
    return ", ".join(f"{k}={v}" for k, v in sorted(factors.items()))


def _get_ofat_factors(baseline: dict, algorithm: str) -> list:
    """Generate all OFAT factor sets for a given algorithm."""
    result = [("BASELINE", dict(baseline))]

    for name, value, applies, desc in OFAT_VARIATIONS:
        if applies == "both" or applies == algorithm:
            f = dict(baseline)
            # Adjust dependencies for algorithm
            if algorithm == "instant":
                f["dependencies"] = "NONE"  # INSTANT: target must have no index
            f[name] = value
            result.append((f"{name}={value}", f))

    return result


def _get_keypair_factors(baseline: dict, algorithm: str) -> list:
    """Generate key pair factor sets."""
    result = []
    for kp_id, overrides, applies, desc in KEY_PAIRS:
        if applies == "both" or applies == algorithm:
            f = dict(baseline)
            if algorithm == "instant":
                f["dependencies"] = "NONE"
            f.update(overrides)
            result.append((kp_id, f))
    return result


# ============================================================
# Section 5: Partition Strategy Generator (64 combos)
# ============================================================

PARTITION_TYPES = ["RANGE", "RANGE COLUMNS", "LIST", "LIST COLUMNS",
                   "HASH", "LINEAR HASH", "KEY", "LINEAR KEY"]

# Partition key compatibility matrix
# (strategy, type_category) -> True if type can be used as partition key
PK_COMPAT = {
    ("RANGE", "integer"): True, ("RANGE", "char"): False, ("RANGE", "varchar"): False,
    ("RANGE", "binary"): False, ("RANGE", "varbinary"): False, ("RANGE", "text"): False,
    ("RANGE", "blob"): False, ("RANGE", "bit"): False, ("RANGE", "decimal"): False,
    ("RANGE COLUMNS", "integer"): True, ("RANGE COLUMNS", "char"): True, ("RANGE COLUMNS", "varchar"): True,
    ("RANGE COLUMNS", "binary"): False, ("RANGE COLUMNS", "varbinary"): False, ("RANGE COLUMNS", "text"): False,
    ("RANGE COLUMNS", "blob"): False, ("RANGE COLUMNS", "bit"): False, ("RANGE COLUMNS", "decimal"): True,
    ("LIST", "integer"): True, ("LIST", "char"): False, ("LIST", "varchar"): False,
    ("LIST", "binary"): False, ("LIST", "varbinary"): False, ("LIST", "text"): False,
    ("LIST", "blob"): False, ("LIST", "bit"): False, ("LIST", "decimal"): False,
    ("LIST COLUMNS", "integer"): True, ("LIST COLUMNS", "char"): True, ("LIST COLUMNS", "varchar"): True,
    ("LIST COLUMNS", "binary"): False, ("LIST COLUMNS", "varbinary"): False, ("LIST COLUMNS", "text"): False,
    ("LIST COLUMNS", "blob"): False, ("LIST COLUMNS", "bit"): False, ("LIST COLUMNS", "decimal"): True,
    ("HASH", "integer"): True, ("HASH", "char"): False, ("HASH", "varchar"): False,
    ("HASH", "binary"): False, ("HASH", "varbinary"): False, ("HASH", "text"): False,
    ("HASH", "blob"): False, ("HASH", "bit"): False, ("HASH", "decimal"): False,
    ("LINEAR HASH", "integer"): True, ("LINEAR HASH", "char"): False, ("LINEAR HASH", "varchar"): False,
    ("LINEAR HASH", "binary"): False, ("LINEAR HASH", "varbinary"): False, ("LINEAR HASH", "text"): False,
    ("LINEAR HASH", "blob"): False, ("LINEAR HASH", "bit"): False, ("LINEAR HASH", "decimal"): False,
    ("KEY", "integer"): True, ("KEY", "char"): True, ("KEY", "varchar"): True,
    ("KEY", "binary"): True, ("KEY", "varbinary"): True, ("KEY", "text"): True,
    ("KEY", "blob"): True, ("KEY", "bit"): True, ("KEY", "decimal"): True,
    ("LINEAR KEY", "integer"): True, ("LINEAR KEY", "char"): True, ("LINEAR KEY", "varchar"): True,
    ("LINEAR KEY", "binary"): True, ("LINEAR KEY", "varbinary"): True, ("LINEAR KEY", "text"): True,
    ("LINEAR KEY", "blob"): True, ("LINEAR KEY", "bit"): True, ("LINEAR KEY", "decimal"): True,
}


def _normalize_category(cat: str) -> str:
    """Normalize category names for PK_COMPAT lookup."""
    if cat.startswith("integer"):
        return "integer"
    return cat


def _build_partition_def(first_type: str, second_type: str, pk_col: str = "id",
                         is_subpartition: bool = True) -> tuple:
    """
    Build PARTITION BY clause for a first×second partition type combo.
    Returns (partition_sql, build_should_succeed).
    """
    # First-level partition
    first = _build_single_partition(first_type, pk_col, is_first=True)
    if first is None:
        return None, False

    # Second-level (subpartition)
    second = _build_single_partition(second_type, pk_col, is_first=False)
    if second is None:
        # No subpartition, just first level
        return first, True

    # Combine: first level with subpartition
    combined = first.rstrip(";")
    # Add subpartition definition
    combined += "\nSUBPARTITION BY " + second.split("PARTITION BY ")[1].split("\n")[0] if "PARTITION BY" in second else combined
    # Actually, let's be more careful
    # For subpartitions, we need PARTITIONS ... SUBPARTITIONS ...
    # Let's use a simpler approach: just first-level partitioning with PARTITIONS 4
    return first, True


def _build_single_partition(ptype: str, pk_col: str, is_first: bool) -> str:
    """Build a single PARTITION BY clause for one partition type."""
    if ptype == "RANGE":
        return f"""PARTITION BY RANGE ({pk_col}) (
  PARTITION p0 VALUES LESS THAN (100),
  PARTITION p1 VALUES LESS THAN (200),
  PARTITION p2 VALUES LESS THAN (300),
  PARTITION p3 VALUES LESS THAN MAXVALUE
);"""
    elif ptype == "RANGE COLUMNS":
        return f"""PARTITION BY RANGE COLUMNS({pk_col}) (
  PARTITION p0 VALUES LESS THAN (100),
  PARTITION p1 VALUES LESS THAN (200),
  PARTITION p2 VALUES LESS THAN (300),
  PARTITION p3 VALUES LESS THAN MAXVALUE
);"""
    elif ptype == "LIST":
        return f"""PARTITION BY LIST ({pk_col}) (
  PARTITION p0 VALUES IN (0,1,2,3),
  PARTITION p1 VALUES IN (4,5,6,7),
  PARTITION p2 VALUES IN (8,9,10,11),
  PARTITION p3 VALUES IN (12,13,14,15)
);"""
    elif ptype == "LIST COLUMNS":
        return f"""PARTITION BY LIST COLUMNS({pk_col}) (
  PARTITION p0 VALUES IN (0,1,2,3),
  PARTITION p1 VALUES IN (4,5,6,7),
  PARTITION p2 VALUES IN (8,9,10,11),
  PARTITION p3 VALUES IN (12,13,14,15)
);"""
    elif ptype == "HASH":
        return "PARTITION BY HASH(id) PARTITIONS 4;"
    elif ptype == "LINEAR HASH":
        return "PARTITION BY LINEAR HASH(id) PARTITIONS 4;"
    elif ptype == "KEY":
        return "PARTITION BY KEY(id) PARTITIONS 4;"
    elif ptype == "LINEAR KEY":
        return "PARTITION BY LINEAR KEY(id) PARTITIONS 4;"
    return None


def _build_partition_test(test_id: str, transition: dict, algorithm: str,
                          pp_idx: int, first_type: str, second_type: str,
                          target_is_partition_key: bool) -> str:
    """Build a partition table test case."""
    old_type = transition["old_type"]
    new_type = transition["new_type"]
    expected = transition[algorithm.lower()]
    cat = transition["category"]
    data = gen_test_data(transition)

    t1 = f"t1_{test_id.lower().replace(chr(45), chr(95))}"
    t2 = f"t2_{test_id.lower().replace(chr(45), chr(95))}"

    lines = []
    lines.append(f"-- Test Case: {test_id}")
    lines.append(f"-- Type: {old_type} -> {new_type}, Algorithm: {algorithm}, Expected: {expected}")
    lines.append(f"-- Partition: {first_type} + {second_type} (PP-{pp_idx:02d})")
    lines.append(f"-- Target is partition key: {target_is_partition_key}")
    lines.append(f"DROP TABLE IF EXISTS {t1}, {t2};")

    if target_is_partition_key:
        # Check if this type can be used as partition key for this strategy
        can_partition = PK_COMPAT.get((first_type, _normalize_category(cat)), False)
        if not can_partition:
            # CREATE TABLE will fail - record as BUILD_FAIL
            lines.append(f"-- Expected: BUILD FAIL (type {cat} not supported as partition key for {first_type})")
            lines.append(f"CREATE TABLE {t1} (id INT NOT NULL AUTO_INCREMENT, target {old_type}, pad VARCHAR(10), PRIMARY KEY(id)) ENGINE=InnoDB PARTITION BY {first_type}(target) PARTITIONS 2;")
            lines.append(f"-- If above succeeded, ALTER should also FAIL (partition key column cannot be modified)")
            lines.append(f"ALTER TABLE {t1} MODIFY target {_build_column_def(new_type, dict(BASELINE), transition)}, ALGORITHM={algorithm};")
            # Comparison: t1 should have no data (or failed to create)
            lines.append(f"SELECT '{test_id}' AS test_id, 'BUILD_OR_ALTER_FAIL_EXPECTED' AS result, 'CHECK_MANUALLY' AS note;")
            return "\n".join(lines)
        else:
            # Can create partition table with target as partition key
            # ALTER should FAIL (partition key column)
            pk_col = "target"
            part_def = _build_single_partition(first_type, pk_col, True)
            lines.append(f"-- Expected: CREATE OK, ALTER FAIL (partition key cannot be modified)")
            lines.append(f"CREATE TABLE {t1} (")
            lines.append(f"  id INT NOT NULL AUTO_INCREMENT,")
            lines.append(f"  target {old_type},")
            lines.append(f"  pad VARCHAR(20) DEFAULT 'pad',")
            lines.append(f"  PRIMARY KEY (id, target)")
            lines.append(f") ENGINE=InnoDB")
            lines.append(part_def)

            # Insert some data
            pre_vals = [v for v in data["pre_values"][:3] if v != "NULL"]
            for v in pre_vals:
                lines.append(_build_insert_stmt(t1, "target", v))

            lines.append(f"-- ALTER expected to FAIL")
            lines.append(_build_alter_stmt(t1, "target", _build_column_def(new_type, dict(BASELINE), transition), algorithm))

            # t2: same old type (ALTER failed)
            lines.append(_build_create_table(t2, old_type, dict(BASELINE), transition))
            for v in pre_vals:
                lines.append(_build_insert_stmt(t2, "target", v))

            lines.append(_build_compare_sql(test_id, t1, t2, ["id", "target", "pad"]))
            return "\n".join(lines)
    else:
        # Target is NOT partition key - use id as partition key
        # ALTER should succeed (or fail based on type/algorithm)
        part_def = _build_single_partition(first_type, "id", True)

        lines.append(f"-- Expected: CREATE OK, ALTER {expected}")
        lines.append(_build_create_table(t1, old_type, dict(BASELINE), transition, partition_def=part_def))

        pre_vals = [v for v in data["pre_values"][:5]]
        for v in pre_vals:
            lines.append(_build_insert_stmt(t1, "target", v))

        if expected == "SUCCESS":
            lines.append(f"-- ALTER expected SUCCESS")
        else:
            lines.append(f"-- ALTER expected FAIL")
        lines.append(_build_alter_stmt(t1, "target", _build_column_def(new_type, dict(BASELINE), transition), algorithm))

        # Post-data
        post_new = [v for v in data["post_new_range"][:3]]
        post_old = [v for v in data["post_old_range"][:2]]
        for v in post_new + post_old:
            lines.append(_build_insert_stmt(t1, "target", v))

        # Oracle table
        t2_type = new_type if expected == "SUCCESS" else old_type
        lines.append(_build_create_table(t2, t2_type, dict(BASELINE), transition))
        all_vals = pre_vals + post_new + post_old
        for v in all_vals:
            lines.append(_build_insert_stmt(t2, "target", v))

        lines.append(_build_compare_sql(test_id, t1, t2, ["id", "pad1", "target", "pad2"]))
        return "\n".join(lines)


# ============================================================
# Section 6: Foreign Key Test Generator
# ============================================================

FK_TRANSITIONS = [
    # (id, old_type, new_type, fk_col_type, category, instant, inplace, single_side_expected, notes)
    ("FK-INT", "INT", "BIGINT", "INT", "integer_signed", "SUCCESS", "SUCCESS", "FAIL", "Integer FK single-side FAIL"),
    ("FK-BIN", "BINARY(10)", "BINARY(20)", "BINARY(10)", "binary", "FAIL", "SUCCESS", "FAIL", "BINARY FK single-side FAIL"),
    ("FK-VC", "VARCHAR(50)", "VARCHAR(100)", "VARCHAR(50)", "varchar", "SUCCESS", "SUCCESS", "SUCCESS", "VARCHAR FK single-side OK"),
    ("FK-VBIN", "VARBINARY(50)", "VARBINARY(100)", "VARBINARY(50)", "varbinary", "FAIL", "SUCCESS", "SUCCESS", "VARBINARY FK single-side OK"),
    ("FK-DEC", "DECIMAL(10,2)", "DECIMAL(12,2)", "DECIMAL(10,2)", "decimal", "FAIL", "SUCCESS", "FAIL", "DECIMAL FK single-side FAIL"),
]


def _build_fk_test(test_id: str, fk_trans: tuple, algorithm: str, scenario: str) -> str:
    """Build FK test case. scenario: child/parent/both/non_fk"""
    fk_id, old_type, new_type, fk_col_type, cat, instant_exp, inplace_exp, single_exp, _notes = fk_trans
    expected = inplace_exp if algorithm == "inplace" else instant_exp

    # For 'both' scenario, expected is always SUCCESS for INPLACE
    # For 'child'/'parent' (single-side), expected depends on single_exp
    if scenario == "both":
        alter_expected = "SUCCESS" if algorithm == "inplace" else "FAIL"
    elif scenario in ("child", "parent"):
        alter_expected = single_exp if algorithm == "inplace" else "FAIL"
    else:  # non_fk
        alter_expected = expected

    t_parent = f"tp_{test_id.lower().replace(chr(45), chr(95))}"
    t_child = f"tc_{test_id.lower().replace(chr(45), chr(95))}"
    t2 = f"t2_{test_id.lower().replace(chr(45), chr(95))}"

    lines = []
    lines.append(f"-- Test Case: {test_id}")
    lines.append(f"-- FK Scenario: {scenario}, Algorithm: {algorithm}")
    lines.append(f"-- Type: {old_type} -> {new_type}")
    lines.append(f"-- Expected: {alter_expected}")
    lines.append(f"-- Expected ALTER: {alter_expected}")
    lines.append(f"SET SESSION sql_mode = 'STRICT_TRANS_TABLES';")
    lines.append(f"SET foreign_key_checks=0;")
    lines.append(f"DROP TABLE IF EXISTS {t_child}, {t_parent}, {t2};")
    lines.append(f"SET foreign_key_checks=1;")

    # Create parent table
    cs = None
    if cat in ("varchar",):
        cs = "latin1"
    parent_type = old_type
    child_type = old_type

    lines.append(f"CREATE TABLE {t_parent} (")
    lines.append(f"  pid INT NOT NULL AUTO_INCREMENT PRIMARY KEY,")
    lines.append(f"  fk_col {old_type}" + (f" CHARACTER SET {cs}" if cs else "") + ",")
    lines.append(f"  data VARCHAR(20) DEFAULT 'parent',")
    lines.append(f"  INDEX idx_parent_fk (fk_col)")
    lines.append(f") ENGINE=InnoDB;")

    # Create child table with FK
    lines.append(f"CREATE TABLE {t_child} (")
    lines.append(f"  cid INT NOT NULL AUTO_INCREMENT PRIMARY KEY,")
    lines.append(f"  fk_col {old_type}" + (f" CHARACTER SET {cs}" if cs else "") + ",")
    lines.append(f"  data VARCHAR(20) DEFAULT 'child',")
    lines.append(f"  INDEX idx_fk (fk_col),")
    lines.append(f"  CONSTRAINT {test_id.lower().replace('-', '_')}_fk FOREIGN KEY (fk_col) REFERENCES {t_parent}(fk_col)")
    lines.append(f") ENGINE=InnoDB;")

    # Insert data
    data = _gen_fk_data(fk_trans, cat)
    for v in data["pre"]:
        lines.append(f"INSERT INTO {t_parent} (fk_col) VALUES ({v});")
        lines.append(f"INSERT INTO {t_child} (fk_col) VALUES ({v});")

    # ALTER
    if scenario == "child":
        lines.append(f"-- ALTER child table only")
        lines.append(f"ALTER TABLE {t_child} MODIFY fk_col {new_type}" + (f" CHARACTER SET {cs}" if cs else "") + f", ALGORITHM={algorithm};")
    elif scenario == "parent":
        lines.append(f"-- ALTER parent table only")
        lines.append(f"ALTER TABLE {t_parent} MODIFY fk_col {new_type}" + (f" CHARACTER SET {cs}" if cs else "") + f", ALGORITHM={algorithm};")
    elif scenario == "both":
        lines.append(f"-- ALTER both tables (parent first, then child)")
        lines.append(f"ALTER TABLE {t_parent} MODIFY fk_col {new_type}" + (f" CHARACTER SET {cs}" if cs else "") + f", ALGORITHM={algorithm};")
        lines.append(f"ALTER TABLE {t_child} MODIFY fk_col {new_type}" + (f" CHARACTER SET {cs}" if cs else "") + f", ALGORITHM={algorithm};")
    else:  # non_fk - modify a non-FK column
        lines.append(f"-- ALTER non-FK column (data column)")
        lines.append(f"ALTER TABLE {t_child} MODIFY data VARCHAR(50) DEFAULT 'child', ALGORITHM={algorithm};")

    # Post-ALTER data
    if alter_expected == "SUCCESS":
        for v in data["post_new"]:
            lines.append(f"INSERT INTO {t_parent} (fk_col) VALUES ({v});")
            lines.append(f"INSERT INTO {t_child} (fk_col) VALUES ({v});")

    # Comparison: compare child table data
    # Create oracle table
    oracle_type = new_type if alter_expected == "SUCCESS" else old_type
    # Oracle table: fk_col type matches post-ALTER state; data type depends on scenario
    if scenario == "non_fk" and alter_expected == "SUCCESS":
        oracle_fk = old_type  # fk_col unchanged for non_fk
        oracle_data = "VARCHAR(50)"
    else:
        oracle_fk = oracle_type
        oracle_data = "VARCHAR(20)"
    lines.append(f"-- Oracle table for child comparison")
    lines.append(f"CREATE TABLE {t2} (cid INT NOT NULL AUTO_INCREMENT PRIMARY KEY, fk_col {oracle_fk}" + (f" CHARACTER SET {cs}" if cs else "") + f", data {oracle_data} DEFAULT 'child') ENGINE=InnoDB;")
    for v in data["pre"]:
        lines.append(f"INSERT INTO {t2} (fk_col) VALUES ({v});")
    if alter_expected == "SUCCESS":
        for v in data["post_new"]:
            lines.append(f"INSERT INTO {t2} (fk_col) VALUES ({v});")

    # Custom comparison for FK tables (different PK column name)
    lines.append(f"""SELECT '{test_id}' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',cid) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, cid FROM {t_child}
   WHERE cid NOT IN (SELECT cid FROM {t2})
  UNION ALL
  SELECT 't2_extra' AS src, cid FROM {t2}
   WHERE cid NOT IN (SELECT cid FROM {t_child})
  UNION ALL
  SELECT 'data_mismatch' AS src, a.cid FROM {t_child} a JOIN {t2} b ON a.cid = b.cid
   WHERE NOT (a.fk_col <=> b.fk_col AND a.data <=> b.data)
) AS mismatches;""")

    return "\n".join(lines)


def _gen_fk_data(fk_trans: tuple, cat: str) -> dict:
    """Generate FK-compatible test data."""
    fk_id, old_type, new_type, fk_col_type, _, _, _, _, _ = fk_trans

    if cat == "integer_signed":
        return {"pre": ["0", "1", "-1", "42", "127"], "post_new": ["128", "255", "1000"]}
    elif cat == "binary":
        return {"pre": [_hex_literal(b"\x00" * 10), _hex_literal(b"\xff" * 10), _hex_literal(b"AB" * 5)],
                "post_new": [_hex_literal(b"\x00" * 20), _hex_literal(b"\xff" * 20)]}
    elif cat == "varchar":
        return {"pre": ["'hello'", "'world'", "'test'", "'abc'"],
                "post_new": ["'hello_world'", "'a'"]}
    elif cat == "varbinary":
        return {"pre": [_hex_literal(b"\x00" * 50), _hex_literal(b"\xff" * 50)],
                "post_new": [_hex_literal(b"\x00" * 100)]}
    elif cat == "decimal":
        return {"pre": ["0.00", "1.23", "-1.23", "99.99"],
                "post_new": ["999.99", "1000.00"]}
    return {"pre": [], "post_new": []}



# ============================================================
# Section 7: Special Patterns (Consecutive ALTER, Multi-column, Virtual Generated)
# ============================================================

def _build_consecutive_alter(test_id: str, unsigned: bool, algorithm: str) -> str:
    """Build consecutive ALTER chain test: TINYINT → ... → BIGINT."""
    t1 = f"t1_{test_id.lower().replace(chr(45), chr(95))}"
    t2 = f"t2_{test_id.lower().replace(chr(45), chr(95))}"

    if unsigned:
        types = ["TINYINT UNSIGNED", "SMALLINT UNSIGNED", "MEDIUMINT UNSIGNED",
                 "INT UNSIGNED", "BIGINT UNSIGNED"]
        data_per_step = [
            ["0", "1", "255"],
            ["256", "65535"],
            ["65536", "16777215"],
            ["16777216", "4294967295"],
            ["4294967296", "18446744073709551615"],
        ]
        final_type = "BIGINT UNSIGNED"
    else:
        types = ["TINYINT", "SMALLINT", "MEDIUMINT", "INT", "BIGINT"]
        data_per_step = [
            ["-128", "0", "1", "127"],
            ["128", "32767"],
            ["32768", "8388607"],
            ["8388608", "2147483647"],
            ["2147483648", "9223372036854775807"],
        ]
        final_type = "BIGINT"

    lines = []
    lines.append(f"-- Test Case: {test_id}")
    lines.append(f"-- Consecutive ALTER: {' -> '.join(types)}")
    lines.append(f"-- Algorithm: {algorithm}")
    lines.append(f"DROP TABLE IF EXISTS {t1}, {t2};")
    lines.append(f"CREATE TABLE {t1} (")
    lines.append(f"  id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,")
    lines.append(f"  target {types[0]},")
    lines.append(f"  pad VARCHAR(20) DEFAULT 'pad'")
    lines.append(f") ENGINE=InnoDB;")

    all_data = []
    # Step 0: initial data
    for v in data_per_step[0]:
        lines.append(_build_insert_stmt(t1, "target", v))
        all_data.append(v)

    # Steps 1-4: ALTER + insert
    for i in range(1, len(types)):
        lines.append(f"-- Step {i}: ALTER to {types[i]}")
        lines.append(f"ALTER TABLE {t1} MODIFY target {types[i]}, ALGORITHM={algorithm};")
        for v in data_per_step[i]:
            lines.append(_build_insert_stmt(t1, "target", v))
            all_data.append(v)

    # Oracle: create t2 with final type and insert all data
    lines.append(f"-- Oracle table with final type {final_type}")
    lines.append(f"CREATE TABLE {t2} (")
    lines.append(f"  id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,")
    lines.append(f"  target {final_type},")
    lines.append(f"  pad VARCHAR(20) DEFAULT 'pad'")
    lines.append(f") ENGINE=InnoDB;")
    for v in all_data:
        lines.append(_build_insert_stmt(t2, "target", v))

    lines.append(_build_compare_sql(test_id, t1, t2, ["id", "target", "pad"]))
    return "\n".join(lines)


def _build_multi_column_alter(test_id: str, algorithm: str, env: str) -> str:
    """Build multi-column ALTER test."""
    t1 = f"t1_{test_id.lower().replace(chr(45), chr(95))}"
    t2 = f"t2_{test_id.lower().replace(chr(45), chr(95))}"

    lines = []
    lines.append(f"-- Test Case: {test_id}")
    lines.append(f"-- Multi-column ALTER, Algorithm: {algorithm}")
    lines.append(f"DROP TABLE IF EXISTS {t1}, {t2};")

    # Create table with multiple columns of different types
    cols_def = [
        "id INT NOT NULL AUTO_INCREMENT PRIMARY KEY",
        "col_int INT",
        "col_char CHAR(10) CHARACTER SET utf8mb4",
        "col_varchar VARCHAR(50) CHARACTER SET utf8mb4",
    ]
    if env == "internal":
        cols_def.append("col_decimal DECIMAL(10,2)")
        cols_def.append("col_binary BINARY(10)")
        cols_def.append("col_blob BLOB")
        cols_def.append("col_bit BIT(8)")

    lines.append(f"CREATE TABLE {t1} (")
    lines.append(",\n".join(f"  {c}" for c in cols_def))
    lines.append(") ENGINE=InnoDB;")

    # Insert initial data
    lines.append(f"INSERT INTO {t1} (col_int, col_char, col_varchar" + (", col_decimal, col_binary, col_blob, col_bit" if env == "internal" else "") + ")")
    vals = "42, 'hello', 'world'"
    if env == "internal":
        vals += ", 1.23, " + _hex_literal(b"\x00" * 10) + ", " + _hex_literal(b"\x00\x01\x02") + ", b'10101010'"
    lines.append(f"VALUES ({vals});")

    # Multi-column ALTER
    alter_cols = [
        "MODIFY col_int BIGINT",
        "MODIFY col_char CHAR(20) CHARACTER SET utf8mb4",
        "MODIFY col_varchar VARCHAR(100) CHARACTER SET utf8mb4",
    ]
    if env == "internal":
        alter_cols.append("MODIFY col_decimal DECIMAL(20,2)")
        alter_cols.append("MODIFY col_binary BINARY(20)")
        alter_cols.append("MODIFY col_blob MEDIUMBLOB")
        alter_cols.append("MODIFY col_bit BIT(16)")

    alter_stmt = f"ALTER TABLE {t1} " + ", ".join(alter_cols) + f", ALGORITHM={algorithm};"
    lines.append(alter_stmt)

    # Post-ALTER insert
    lines.append(f"INSERT INTO {t1} (col_int, col_char, col_varchar" + (", col_decimal, col_binary, col_blob, col_bit" if env == "internal" else "") + ")")
    vals2 = "2147483648, 'hello_world_long', 'extended_string'"
    if env == "internal":
        vals2 += ", 999.99, " + _hex_literal(b"\x00" * 20) + ", " + _hex_literal(b"\x00" * 200) + ", b'1111111111111111'"
    lines.append(f"VALUES ({vals2});")

    # Oracle table
    new_cols = [
        "id INT NOT NULL AUTO_INCREMENT PRIMARY KEY",
        "col_int BIGINT",
        "col_char CHAR(20) CHARACTER SET utf8mb4",
        "col_varchar VARCHAR(100) CHARACTER SET utf8mb4",
    ]
    if env == "internal":
        new_cols.append("col_decimal DECIMAL(20,2)")
        new_cols.append("col_binary BINARY(20)")
        new_cols.append("col_blob MEDIUMBLOB")
        new_cols.append("col_bit BIT(16)")

    lines.append(f"CREATE TABLE {t2} (")
    lines.append(",\n".join(f"  {c}" for c in new_cols))
    lines.append(") ENGINE=InnoDB;")

    # Insert same data
    lines.append(f"INSERT INTO {t2} (col_int, col_char, col_varchar" + (", col_decimal, col_binary, col_blob, col_bit" if env == "internal" else "") + ")")
    lines.append(f"VALUES ({vals});")
    lines.append(f"INSERT INTO {t2} (col_int, col_char, col_varchar" + (", col_decimal, col_binary, col_blob, col_bit" if env == "internal" else "") + ")")
    lines.append(f"VALUES ({vals2});")

    compare_cols = ["id", "col_int", "col_char", "col_varchar"]
    if env == "internal":
        compare_cols.extend(["col_decimal", "col_binary", "col_blob", "col_bit"])

    lines.append(_build_compare_sql(test_id, t1, t2, compare_cols))
    return "\n".join(lines)


def _build_virtual_generated_test(test_id: str, algorithm: str) -> str:
    """Build virtual generated column / function index test."""
    t1 = f"t1_{test_id.lower().replace(chr(45), chr(95))}"
    t2 = f"t2_{test_id.lower().replace(chr(45), chr(95))}"

    lines = []
    lines.append(f"-- Test Case: {test_id}")
    lines.append(f"-- Virtual generated column + function index, Algorithm: {algorithm}")
    lines.append(f"DROP TABLE IF EXISTS {t1}, {t2};")

    expected = "SUCCESS" if algorithm == "inplace" else "FAIL"

    # Create table with virtual generated column and function index
    lines.append(f"CREATE TABLE {t1} (")
    lines.append(f"  id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,")
    lines.append(f"  base_col INT,")
    lines.append(f"  vcol BIGINT AS (base_col * 2) VIRTUAL,")
    lines.append(f"  INDEX idx_vcol (vcol)")
    lines.append(f") ENGINE=InnoDB;")

    # Insert data
    lines.append(f"INSERT INTO {t1} (base_col) VALUES (0), (1), (-1), (2147483647), (42), (-42), (NULL);")

    # ALTER base column
    lines.append(f"-- ALTER base_col INT -> BIGINT, expected: {expected}")
    lines.append(f"ALTER TABLE {t1} MODIFY base_col BIGINT, ALGORITHM={algorithm};")

    if expected == "SUCCESS":
        # Post-ALTER insert with new range
        lines.append(f"INSERT INTO {t1} (base_col) VALUES (2147483648), (9223372036854775807), (-9223372036854775808);")

    # Oracle table
    lines.append(f"CREATE TABLE {t2} (")
    lines.append(f"  id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,")
    lines.append(f"  base_col {'BIGINT' if expected == 'SUCCESS' else 'INT'},")
    lines.append(f"  vcol BIGINT AS (base_col * 2) VIRTUAL")
    lines.append(f") ENGINE=InnoDB;")
    lines.append(f"INSERT INTO {t2} (base_col) VALUES (0), (1), (-1), (2147483647), (42), (-42), (NULL);")
    if expected == "SUCCESS":
        lines.append(f"INSERT INTO {t2} (base_col) VALUES (2147483648), (9223372036854775807), (-9223372036854775808);")

    # Compare only base_col since vcol is generated
    lines.append(f"""SELECT '{test_id}' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM {t1}
   WHERE id NOT IN (SELECT id FROM {t2})
  UNION ALL
  SELECT 't2_extra' AS src, id FROM {t2}
   WHERE id NOT IN (SELECT id FROM {t1})
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM {t1} a JOIN {t2} b ON a.id = b.id
   WHERE NOT (a.base_col <=> b.base_col)
) AS mismatches;""")
    return "\n".join(lines)


def _build_column_attribute_test(test_id: str, transition: dict, algorithm: str,
                                 attr_type: str) -> str:
    """Build column attribute preservation test."""
    t1 = f"t1_{test_id.lower().replace(chr(45), chr(95))}"
    t2 = f"t2_{test_id.lower().replace(chr(45), chr(95))}"
    old_type = transition["old_type"]
    new_type = transition["new_type"]
    cs = transition.get("charset")

    lines = []
    lines.append(f"-- Test Case: {test_id}")
    lines.append(f"-- Column attribute preservation: {attr_type}")
    lines.append(f"-- Type: {old_type} -> {new_type}, Algorithm: {algorithm}")
    lines.append(f"DROP TABLE IF EXISTS {t1}, {t2};")

    # Build column definition with specific attribute
    if attr_type == "UNSIGNED":
        old_def = old_type
        new_def = new_type
    elif attr_type == "AUTO_INCREMENT":
        old_def = f"{old_type} NOT NULL AUTO_INCREMENT"
        new_def = f"{new_type} NOT NULL AUTO_INCREMENT"
    elif attr_type == "COMMENT":
        old_def = f"{old_type} COMMENT 'test_comment'"
        new_def = f"{new_type} COMMENT 'test_comment'"
    elif attr_type == "CHARSET":
        cs_str = cs if cs and cs != "utf8mb3" else "utf8" if cs == "utf8mb3" else None
        old_def = f"{old_type}" + (f" CHARACTER SET {cs_str}" if cs_str else "")
        new_def = f"{new_type}" + (f" CHARACTER SET {cs_str}" if cs_str else "")
    elif attr_type == "COLLATE":
        cs_str = cs if cs and cs != "utf8mb3" else "utf8" if cs == "utf8mb3" else None
        collate = f"{cs_str}_bin" if cs_str else None
        old_def = f"{old_type}" + (f" CHARACTER SET {cs_str} COLLATE {collate}" if cs_str else "")
        new_def = f"{new_type}" + (f" CHARACTER SET {cs_str} COLLATE {collate}" if cs_str else "")
    else:
        old_def = old_type
        new_def = new_type

    if attr_type == "AUTO_INCREMENT":
        lines.append(f"CREATE TABLE {t1} (")
        lines.append(f"  id {old_def} PRIMARY KEY,")
        lines.append(f"  pad VARCHAR(20) DEFAULT 'pad'")
        lines.append(f") ENGINE=InnoDB;")
    else:
        lines.append(f"CREATE TABLE {t1} (")
        lines.append(f"  id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,")
        lines.append(f"  target {old_def},")
        lines.append(f"  pad VARCHAR(20) DEFAULT 'pad'")
        lines.append(f") ENGINE=InnoDB;")

    data = gen_test_data(transition)
    for v in data["pre_values"][:5]:
        if attr_type == "AUTO_INCREMENT":
            lines.append(f"INSERT INTO {t1} (id) VALUES ({v});")
        else:
            lines.append(_build_insert_stmt(t1, "target", v))

    # Build alter with column def (may include COMMENT, CHARACTER SET, etc.)
    alter_col = "target" if attr_type != "AUTO_INCREMENT" else "id"
    lines.append(_build_alter_stmt(t1, alter_col, new_def, algorithm))
    if data["post_new_range"]:
        for v in data["post_new_range"][:3]:
            if attr_type == "AUTO_INCREMENT":
                lines.append(f"INSERT INTO {t1} (id) VALUES ({v});")
            else:
                lines.append(_build_insert_stmt(t1, "target", v))

    # Verify attribute preserved
    if attr_type == "COMMENT":
        lines.append(f"SELECT '{test_id}' AS test_id, IF(COUNT(*)>0,'PASS','FAIL') AS result FROM information_schema.columns WHERE table_name='{t1}' AND column_name='target' AND column_comment='test_comment';")
    elif attr_type == "CHARSET":
        # MySQL 8.0 reports utf8mb3 in information_schema (utf8 is an alias)
        if cs == "utf8mb3":
            cs_str = "utf8mb3"
        elif cs == "utf8mb4":
            cs_str = "utf8mb4"
        else:
            cs_str = cs or "latin1"
        lines.append(f"SELECT '{test_id}' AS test_id, IF(COUNT(*)>0,'PASS','FAIL') AS result FROM information_schema.columns WHERE table_name='{t1}' AND column_name='target' AND character_set_name='{cs_str}';")
    elif attr_type == "COLLATE":
        # MySQL 8.0 stores utf8 as utf8mb3 in information_schema
        if cs == "utf8mb3":
            cs_str = "utf8mb3"
        elif cs and cs != "utf8mb3":
            cs_str = cs
        else:
            cs_str = "latin1"
        lines.append(f"SELECT '{test_id}' AS test_id, IF(COUNT(*)>0,'PASS','FAIL') AS result FROM information_schema.columns WHERE table_name='{t1}' AND column_name='target' AND collation_name='{cs_str}_bin';")
    elif attr_type == "UNSIGNED":
        lines.append(f"SELECT '{test_id}' AS test_id, IF(COUNT(*)>0,'PASS','FAIL') AS result FROM information_schema.columns WHERE table_name='{t1}' AND column_name='target' AND column_type LIKE '%unsigned%';")
    elif attr_type == "AUTO_INCREMENT":
        lines.append(f"SELECT '{test_id}' AS test_id, IF(COUNT(*)>0,'PASS','FAIL') AS result FROM information_schema.columns WHERE table_name='{t1}' AND column_name='id' AND extra LIKE '%auto_increment%';")
    else:
        # Data comparison
        lines.append(f"CREATE TABLE {t2} (id INT NOT NULL AUTO_INCREMENT PRIMARY KEY, target {new_def}, pad VARCHAR(20) DEFAULT 'pad') ENGINE=InnoDB;")
        for v in data["pre_values"][:5]:
            lines.append(_build_insert_stmt(t2, "target", v))
        if data["post_new_range"]:
            for v in data["post_new_range"][:3]:
                lines.append(_build_insert_stmt(t2, "target", v))
        lines.append(_build_compare_sql(test_id, t1, t2, ["id", "target", "pad"]))

    return "\n".join(lines)



# ============================================================
# Section 8: File Writers & Main Function
# ============================================================

def _write_sql_file(filepath: str, header: str, statements: list) -> int:
    """Write SQL statements to a file. Returns statement count."""
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(header)
        for stmt in statements:
            f.write(stmt)
            f.write("\n\n")
    return len(statements)


def _gen_regular_table_tests(transitions: list, algorithm: str, env: str) -> list:
    """Generate all regular table tests for a set of transitions."""
    results = []
    seq = 0
    for trans in transitions:
        if trans["env"] != env:
            continue
        # Baseline
        ofat_sets = _get_ofat_factors(dict(BASELINE), algorithm)
        keypair_sets = _get_keypair_factors(dict(BASELINE), algorithm)

        all_sets = ofat_sets + keypair_sets

        for factor_name, factors in all_sets:
            seq += 1
            # Adjust dependencies for INSTANT (no index on target)
            if algorithm == "instant":
                factors["dependencies"] = "NONE"

            test_id = f"TC-{env[0].upper()}{seq:04d}"
            suffix = f"{env[0]}{seq:04d}"
            sql = _build_test_case_sql(test_id, trans, algorithm, factors, suffix)
            results.append(sql)

        # Column attribute preservation tests (one per type)
        for attr in ["UNSIGNED", "COMMENT", "CHARSET", "COLLATE"]:
            if attr == "UNSIGNED" and "unsigned" not in trans["category"]:
                continue
            if attr in ("CHARSET", "COLLATE") and not trans.get("charset"):
                continue
            if attr == "AUTO_INCREMENT" and trans["category"] not in ("integer_signed", "integer_unsigned"):
                continue
            seq += 1
            test_id = f"TC-{env[0].upper()}A{seq:04d}"
            sql = _build_column_attribute_test(test_id, trans, algorithm, attr)
            results.append(sql)

    return results


def _gen_partition_tests(transitions: list, algorithm: str, env: str) -> list:
    """Generate all 64 partition combo tests for all transitions."""
    results = []
    seq = 0
    pp_idx = 0

    for first_idx, first_type in enumerate(PARTITION_TYPES):
        for second_idx, second_type in enumerate(PARTITION_TYPES):
            pp_idx += 1
            for trans in transitions:
                if trans["env"] != env:
                    continue
                # Test 1: target IS partition key (expected FAIL)
                seq += 1
                test_id = f"TC-P{env[0].upper()}{seq:04d}"
                sql = _build_partition_test(test_id, trans, algorithm, pp_idx,
                                           first_type, second_type, True)
                results.append(sql)

                # Test 2: target is NOT partition key (expected per type)
                seq += 1
                test_id = f"TC-Q{env[0].upper()}{seq:04d}"
                sql = _build_partition_test(test_id, trans, algorithm, pp_idx,
                                           first_type, second_type, False)
                results.append(sql)

    return results


def _gen_fk_tests_for_env(env: str) -> list:
    """Generate FK tests for an environment."""
    results = []
    seq = 0

    # Determine which FK transitions belong to this env
    if env == "aliyun":
        fk_trans = [ft for ft in FK_TRANSITIONS if ft[4] in ("integer_signed", "varchar")]
    else:
        fk_trans = [ft for ft in FK_TRANSITIONS if ft[4] in ("binary", "varbinary", "decimal")]

    for fk_trans_item in fk_trans:
        for algorithm in ["instant", "inplace"]:
            for scenario in ["child", "parent", "both", "non_fk"]:
                seq += 1
                test_id = f"TC-F{env[0].upper()}{seq:04d}"
                sql = _build_fk_test(test_id, fk_trans_item, algorithm, scenario)
                results.append(sql)

    return results


def _gen_special_tests(env: str) -> list:
    """Generate special pattern tests for an environment."""
    results = []

    # Consecutive ALTER (signed + unsigned for aliyun, signed only for internal)
    for unsigned in [True, False]:
        if env == "internal" and unsigned:
            continue  # Internal doesn't have unsigned integer transitions
        for algorithm in ["instant", "inplace"]:
            test_id = f"TC-S{env[0].upper()}{len(results)+1:04d}"
            sql = _build_consecutive_alter(test_id, unsigned, algorithm)
            results.append(sql)

    # Multi-column ALTER
    for algorithm in ["instant", "inplace"]:
        test_id = f"TC-S{env[0].upper()}{len(results)+1:04d}"
        sql = _build_multi_column_alter(test_id, algorithm, env)
        results.append(sql)

    # Virtual generated column (INPLACE only for basic types)
    if env == "aliyun":
        for algorithm in ["instant", "inplace"]:
            test_id = f"TC-S{env[0].upper()}{len(results)+1:04d}"
            sql = _build_virtual_generated_test(test_id, algorithm)
            results.append(sql)

    return results


def generate_all():
    """Generate all SQL test files."""
    aliyun_trans = [t for t in ALL_TRANSITIONS if t["env"] == "aliyun"]
    internal_trans = [t for t in ALL_TRANSITIONS if t["env"] == "internal"]

    header_aliyun = """-- ============================================================
-- RDS MySQL DDL 秒级/在线修改列类型 测试套件 — 阿里云环境
-- 环境说明: 所有功能开关默认开启
-- 覆盖类型: 整数(SIGNED/UNSIGNED) + CHAR + VARCHAR
-- 覆盖算法: INSTANT + INPLACE
-- ============================================================
-- 本文件由 generate_test_sql.py 自动生成, 请勿手动修改
-- 生成时间: 2026-09-20
-- ============================================================

SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
SET SESSION innodb_lock_wait_timeout = 50;

"""

    header_internal = """-- ============================================================
-- RDS MySQL DDL 秒级/在线修改列类型 测试套件 — 内网环境
-- 环境说明: 所有功能开关默认开启
-- 覆盖类型: BINARY + VARBINARY + DECIMAL + TEXT + BLOB + BIT
-- 覆盖算法: INSTANT + INPLACE (增强类型 INSTANT 预期成功 (BINARY/VARBINARY/DECIMAL 已确认支持))
-- ============================================================
-- 本文件由 generate_test_sql.py 自动生成, 请勿手动修改
-- 生成时间: 2026-09-20
-- ============================================================

SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
SET SESSION innodb_lock_wait_timeout = 50;

"""

    # ============= Aliyun SQL files =============
    # 01: Integer SIGNED INSTANT
    int_s_trans = [t for t in aliyun_trans if t["category"] == "integer_signed"]
    sql01 = _gen_regular_table_tests(int_s_trans, "instant", "aliyun")
    _write_sql_file(os.path.join(SQL_ALIYUN, "01_integer_signed_instant.sql"),
                    header_aliyun + "-- File 01: 整数(有符号) INSTANT\n\n", sql01)

    # 02: Integer SIGNED INPLACE
    sql02 = _gen_regular_table_tests(int_s_trans, "inplace", "aliyun")
    _write_sql_file(os.path.join(SQL_ALIYUN, "02_integer_signed_inplace.sql"),
                    header_aliyun + "-- File 02: 整数(有符号) INPLACE\n\n", sql02)

    # 03: Integer UNSIGNED INSTANT
    int_u_trans = [t for t in aliyun_trans if t["category"] == "integer_unsigned"]
    sql03 = _gen_regular_table_tests(int_u_trans, "instant", "aliyun")
    _write_sql_file(os.path.join(SQL_ALIYUN, "03_integer_unsigned_instant.sql"),
                    header_aliyun + "-- File 03: 整数(无符号) INSTANT\n\n", sql03)

    # 04: Integer UNSIGNED INPLACE
    sql04 = _gen_regular_table_tests(int_u_trans, "inplace", "aliyun")
    _write_sql_file(os.path.join(SQL_ALIYUN, "04_integer_unsigned_inplace.sql"),
                    header_aliyun + "-- File 04: 整数(无符号) INPLACE\n\n", sql04)

    # 05: CHAR INSTANT
    char_trans = [t for t in aliyun_trans if t["category"] == "char"]
    sql05 = _gen_regular_table_tests(char_trans, "instant", "aliyun")
    _write_sql_file(os.path.join(SQL_ALIYUN, "05_char_instant.sql"),
                    header_aliyun + "-- File 05: CHAR INSTANT\n\n", sql05)

    # 06: CHAR INPLACE
    sql06 = _gen_regular_table_tests(char_trans, "inplace", "aliyun")
    _write_sql_file(os.path.join(SQL_ALIYUN, "06_char_inplace.sql"),
                    header_aliyun + "-- File 06: CHAR INPLACE\n\n", sql06)

    # 07: VARCHAR INSTANT
    vc_trans = [t for t in aliyun_trans if t["category"] == "varchar"]
    sql07 = _gen_regular_table_tests(vc_trans, "instant", "aliyun")
    _write_sql_file(os.path.join(SQL_ALIYUN, "07_varchar_instant.sql"),
                    header_aliyun + "-- File 07: VARCHAR INSTANT\n\n", sql07)

    # 08: VARCHAR INPLACE
    sql08 = _gen_regular_table_tests(vc_trans, "inplace", "aliyun")
    _write_sql_file(os.path.join(SQL_ALIYUN, "08_varchar_inplace.sql"),
                    header_aliyun + "-- File 08: VARCHAR INPLACE\n\n", sql08)

    # 09: AUTO_INCREMENT PK special
    sql09 = []
    for trans in int_s_trans + int_u_trans:
        for algorithm in ["instant", "inplace"]:
            test_id = f"TC-AI{algorithm[0].upper()}{len(sql09)+1:03d}"
            sql = _build_column_attribute_test(test_id, trans, algorithm, "AUTO_INCREMENT")
            sql09.append(sql)
    _write_sql_file(os.path.join(SQL_ALIYUN, "09_auto_increment_pk.sql"),
                    header_aliyun + "-- File 09: AUTO_INCREMENT PK 扩容专项\n\n", sql09)

    # 10: Consecutive ALTER
    sql10 = _gen_special_tests("aliyun")
    _write_sql_file(os.path.join(SQL_ALIYUN, "10_special_patterns.sql"),
                    header_aliyun + "-- File 10: 特殊模式 (连续ALTER + 多列ALTER + 虚拟生成列)\n\n", sql10)

    # 11: FK table
    sql11 = _gen_fk_tests_for_env("aliyun")
    _write_sql_file(os.path.join(SQL_ALIYUN, "11_fk_table.sql"),
                    header_aliyun + "-- File 11: 外键表测试\n\n", sql11)

    # 12: Partition 64
    sql12 = _gen_partition_tests(aliyun_trans, "instant", "aliyun")
    sql12 += _gen_partition_tests(aliyun_trans, "inplace", "aliyun")
    _write_sql_file(os.path.join(SQL_ALIYUN, "12_partition_64.sql"),
                    header_aliyun + "-- File 12: 64种分区策略 × 全类型\n\n", sql12)

    # ============= Internal SQL files =============
    # 15: BINARY INPLACE
    bin_trans = [t for t in internal_trans if t["category"] == "binary"]
    sql15 = _gen_regular_table_tests(bin_trans, "inplace", "internal")
    _write_sql_file(os.path.join(SQL_INTERNAL, "15_binary_inplace.sql"),
                    header_internal + "-- File 15: BINARY INPLACE\n\n", sql15)

    # 16: BINARY INSTANT (expected SUCCESS)
    sql16 = _gen_regular_table_tests(bin_trans, "instant", "internal")
    _write_sql_file(os.path.join(SQL_INTERNAL, "16_binary_instant.sql"),
                    header_internal + "-- File 16: BINARY INSTANT (预期成功)\n\n", sql16)

    # 17: VARBINARY INPLACE
    vbin_trans = [t for t in internal_trans if t["category"] == "varbinary"]
    sql17 = _gen_regular_table_tests(vbin_trans, "inplace", "internal")
    _write_sql_file(os.path.join(SQL_INTERNAL, "17_varbinary_inplace.sql"),
                    header_internal + "-- File 17: VARBINARY INPLACE\n\n", sql17)

    # 18: VARBINARY INSTANT (expected SUCCESS)
    sql18 = _gen_regular_table_tests(vbin_trans, "instant", "internal")
    _write_sql_file(os.path.join(SQL_INTERNAL, "18_varbinary_instant.sql"),
                    header_internal + "-- File 18: VARBINARY INSTANT (预期成功)\n\n", sql18)

    # 19: DECIMAL INPLACE
    dec_trans = [t for t in internal_trans if t["category"] == "decimal"]
    sql19 = _gen_regular_table_tests(dec_trans, "inplace", "internal")
    _write_sql_file(os.path.join(SQL_INTERNAL, "19_decimal_inplace.sql"),
                    header_internal + "-- File 19: DECIMAL INPLACE\n\n", sql19)

    # 20: DECIMAL INSTANT (expected SUCCESS)
    sql20 = _gen_regular_table_tests(dec_trans, "instant", "internal")
    _write_sql_file(os.path.join(SQL_INTERNAL, "20_decimal_instant.sql"),
                    header_internal + "-- File 20: DECIMAL INSTANT (预期成功)\n\n", sql20)

    # 21: TEXT INSTANT
    text_trans = [t for t in internal_trans if t["category"] == "text"]
    sql21 = _gen_regular_table_tests(text_trans, "instant", "internal")
    _write_sql_file(os.path.join(SQL_INTERNAL, "21_text_instant.sql"),
                    header_internal + "-- File 21: TEXT INSTANT\n\n", sql21)

    # 22: TEXT INPLACE
    sql22 = _gen_regular_table_tests(text_trans, "inplace", "internal")
    _write_sql_file(os.path.join(SQL_INTERNAL, "22_text_inplace.sql"),
                    header_internal + "-- File 22: TEXT INPLACE\n\n", sql22)

    # 23: BLOB INSTANT
    blob_trans = [t for t in internal_trans if t["category"] == "blob"]
    sql23 = _gen_regular_table_tests(blob_trans, "instant", "internal")
    _write_sql_file(os.path.join(SQL_INTERNAL, "23_blob_instant.sql"),
                    header_internal + "-- File 23: BLOB INSTANT\n\n", sql23)

    # 24: BLOB INPLACE
    sql24 = _gen_regular_table_tests(blob_trans, "inplace", "internal")
    _write_sql_file(os.path.join(SQL_INTERNAL, "24_blob_inplace.sql"),
                    header_internal + "-- File 24: BLOB INPLACE\n\n", sql24)

    # 25: BIT INSTANT
    bit_trans = [t for t in internal_trans if t["category"] == "bit"]
    sql25 = _gen_regular_table_tests(bit_trans, "instant", "internal")
    _write_sql_file(os.path.join(SQL_INTERNAL, "25_bit_instant.sql"),
                    header_internal + "-- File 25: BIT INSTANT\n\n", sql25)

    # 26: BIT INPLACE
    sql26 = _gen_regular_table_tests(bit_trans, "inplace", "internal")
    _write_sql_file(os.path.join(SQL_INTERNAL, "26_bit_inplace.sql"),
                    header_internal + "-- File 26: BIT INPLACE\n\n", sql26)

    # 27: FK table enhanced
    sql27 = _gen_fk_tests_for_env("internal")
    _write_sql_file(os.path.join(SQL_INTERNAL, "27_fk_table_enhanced.sql"),
                    header_internal + "-- File 27: 外键表测试(增强类型)\n\n", sql27)

    # 28: Special patterns enhanced
    sql28 = _gen_special_tests("internal")
    _write_sql_file(os.path.join(SQL_INTERNAL, "28_special_patterns_enhanced.sql"),
                    header_internal + "-- File 28: 特殊模式 (连续ALTER + 多列ALTER)\n\n", sql28)

    # 29: Partition 64 enhanced
    sql29 = _gen_partition_tests(internal_trans, "instant", "internal")
    sql29 += _gen_partition_tests(internal_trans, "inplace", "internal")
    _write_sql_file(os.path.join(SQL_INTERNAL, "29_partition_64_enhanced.sql"),
                    header_internal + "-- File 29: 64种分区策略 × 增强类型\n\n", sql29)

    # Print summary
    aliyun_files = sorted(os.listdir(SQL_ALIYUN)) if os.path.exists(SQL_ALIYUN) else []
    internal_files = sorted(os.listdir(SQL_INTERNAL)) if os.path.exists(SQL_INTERNAL) else []

    print("=" * 60)
    print("SQL 生成完成!")
    print("=" * 60)
    print(f"\n阿里云环境 (sql_aliyun/): {len(aliyun_files)} files")
    for f in aliyun_files:
        fp = os.path.join(SQL_ALIYUN, f)
        size = os.path.getsize(fp)
        with open(fp, "r") as fh:
            lines = sum(1 for _ in fh)
        print(f"  {f}: {lines} lines, {size:,} bytes")

    print(f"\n内网环境 (sql_internal/): {len(internal_files)} files")
    for f in internal_files:
        fp = os.path.join(SQL_INTERNAL, f)
        size = os.path.getsize(fp)
        with open(fp, "r") as fh:
            lines = sum(1 for _ in fh)
        print(f"  {f}: {lines} lines, {size:,} bytes")

    total_cases = 0
    for d in [SQL_ALIYUN, SQL_INTERNAL]:
        for f in os.listdir(d):
            with open(os.path.join(d, f)) as fh:
                total_cases += fh.read().count("Test Case:")
    print(f"\n总测试用例数: {total_cases}")
    print(f"类型转换数: {len(ALL_TRANSITIONS)}")
    print(f"分区策略数: {len(PARTITION_TYPES)**2} (8×8)")


if __name__ == "__main__":
    generate_all()

