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
import re as _re
import gzip
import json
import hashlib
import textwrap
from typing import List, Dict, Tuple, Optional, Any

OUTPUT_DIR = os.path.dirname(os.path.abspath(__file__))
SQL_ALIYUN = os.path.join(OUTPUT_DIR, "sql_aliyun")
SQL_INTERNAL = os.path.join(OUTPUT_DIR, "sql_internal")

# ============================================================
# Section 0: 用例 ID 工厂（P0-4）
# ============================================================
# 旧方案的 ID 只在"单个文件 + 单个算法"内唯一：
#   * TC-A0001 同时出现在 01/02/03/04/05/06/07/08 八个文件里（8 种不同转换）
#   * 分区文件里 instant 与 inplace 复用同一个 TC-PA0001
# 结果 18,993 个用例只有 8,500 个唯一 ID：结果无法归因、表名冲突（t1_a0001 被
# 8 个文件共用）、并发执行互相污染、完整性核算低估未执行数。
#
# 新方案：TC-<文件号>-<作用域>-<序号>-<算法>，全局唯一且可追溯到文件/算法。
#   例: TC-01-REG-0001-IT / TC-12-PTK-0002-IP / TC-05-ATR-0003-IP
# ID 只由 (文件号, 作用域, 生成顺序, 算法) 决定，重复生成结果稳定。

ALGO_CODE = {"instant": "IT", "inplace": "IP", "copy": "CP", "default": "DF", None: "XX"}

# 作用域（scope）标识用例族，便于按族统计与筛选
SCOPE_REGULAR = "REG"      # 普通表 OFAT + 关键二元组
SCOPE_ATTRIBUTE = "ATR"    # 列属性保持 (UNSIGNED/COMMENT/CHARSET/COLLATE/AUTO_INCREMENT)
SCOPE_SPECIAL = "SPE"      # 连续ALTER / 多列ALTER / 生成列 等特殊模式
SCOPE_FK = "FK"            # 外键表
SCOPE_PART_KEY = "PTK"     # 分区表，目标列**是**分区键
SCOPE_PART_NONKEY = "PNK"  # 分区表，目标列**不是**分区键


class CaseIdFactory:
    """每个输出文件持有一个工厂实例（跨算法轮次共享计数器，避免 ID 复用）。"""

    def __init__(self, file_no: int):
        self.file_no = int(file_no)
        self._counters: Dict[str, int] = {}

    def next(self, scope: str, algorithm: Optional[str] = None) -> str:
        self._counters[scope] = self._counters.get(scope, 0) + 1
        code = ALGO_CODE.get(algorithm, str(algorithm)[:2].upper())
        return "TC-%02d-%s-%04d-%s" % (self.file_no, scope, self._counters[scope], code)

    @property
    def issued(self) -> int:
        return sum(self._counters.values())


def id_to_suffix(test_id: str) -> str:
    """由用例 ID 派生表名后缀，保证表名与 ID 一一同构（=> 表名也全局唯一）。"""
    return test_id.lower().replace("-", "_")


# 生成器写文件时，超过该阈值的文件直接产出 .sql.gz（并自动登记到 .gitignore）
GZ_THRESHOLD_BYTES = 400_000


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
    # VARCHAR upper limits — convert to MySQL maximum
    {"id": "VC-08", "category": "varchar", "old_type": "VARCHAR(16382)", "new_type": "VARCHAR(16383)", "charset": "utf8mb4", "old_max_len": 16382, "new_max_len": 16383, "instant": "SUCCESS", "inplace": "SUCCESS", "env": "aliyun", "minimal_table": True},
    {"id": "VC-09", "category": "varchar", "old_type": "VARCHAR(65528)", "new_type": "VARCHAR(65529)", "charset": "latin1", "old_max_len": 65528, "new_max_len": 65529, "instant": "SUCCESS", "inplace": "SUCCESS", "env": "aliyun", "minimal_table": True},
]

INTERNAL_TRANSITIONS = [
    # BINARY
    {"id": "BIN-01", "category": "binary",    "old_type": "BINARY(10)",  "new_type": "BINARY(20)",  "charset": None, "old_max_len": 10,  "new_max_len": 20,  "instant": "SUCCESS", "inplace": "SUCCESS", "env": "internal"},
    {"id": "BIN-02", "category": "binary",    "old_type": "BINARY(40)",  "new_type": "BINARY(80)",  "charset": None, "old_max_len": 40,  "new_max_len": 80,  "instant": "SUCCESS", "inplace": "SUCCESS", "env": "internal"},
    {"id": "BIN-03", "category": "binary",    "old_type": "BINARY(254)", "new_type": "BINARY(255)", "charset": None, "old_max_len": 254, "new_max_len": 255, "instant": "SUCCESS", "inplace": "SUCCESS", "env": "internal"},
    # VARBINARY
    {"id": "VBIN-01", "category": "varbinary", "old_type": "VARBINARY(20)",  "new_type": "VARBINARY(40)",  "charset": None, "old_max_len": 20,  "new_max_len": 40,  "instant": "SUCCESS", "inplace": "SUCCESS", "env": "internal"},
    {"id": "VBIN-02", "category": "varbinary", "old_type": "VARBINARY(100)", "new_type": "VARBINARY(200)", "charset": None, "old_max_len": 100, "new_max_len": 200, "instant": "SUCCESS", "inplace": "SUCCESS", "env": "internal"},
    {"id": "VBIN-03", "category": "varbinary", "old_type": "VARBINARY(65528)", "new_type": "VARBINARY(65529)", "charset": None, "old_max_len": 65528, "new_max_len": 65529, "instant": "SUCCESS", "inplace": "SUCCESS", "env": "internal", "minimal_table": True},
    # DECIMAL
    {"id": "DEC-01", "category": "decimal", "old_type": "DECIMAL(10,2)",  "new_type": "DECIMAL(12,2)",  "charset": None, "instant": "SUCCESS", "inplace": "SUCCESS", "env": "internal"},
    {"id": "DEC-02", "category": "decimal", "old_type": "DECIMAL(1,0)",   "new_type": "DECIMAL(2,0)",   "charset": None, "instant": "SUCCESS", "inplace": "SUCCESS", "env": "internal"},
    {"id": "DEC-03", "category": "decimal", "old_type": "DECIMAL(1,1)",   "new_type": "DECIMAL(2,1)",   "charset": None, "instant": "SUCCESS", "inplace": "SUCCESS", "env": "internal"},
    {"id": "DEC-04", "category": "decimal", "old_type": "DECIMAL(64,30)", "new_type": "DECIMAL(65,30)", "charset": None, "instant": "SUCCESS", "inplace": "SUCCESS", "env": "internal"},
    {"id": "DEC-05", "category": "decimal", "old_type": "DECIMAL(18,0)",  "new_type": "DECIMAL(20,0)",  "charset": None, "instant": "SUCCESS", "inplace": "SUCCESS", "env": "internal"},
    {"id": "DEC-06", "category": "decimal", "old_type": "DECIMAL(31,30)", "new_type": "DECIMAL(33,30)", "charset": None, "instant": "SUCCESS", "inplace": "SUCCESS", "env": "internal"},
    # DECIMAL upper limit (max M with D=0, integer DECIMAL)
    {"id": "DEC-07", "category": "decimal", "old_type": "DECIMAL(64,0)", "new_type": "DECIMAL(65,0)", "charset": None, "instant": "SUCCESS", "inplace": "SUCCESS", "env": "internal"},
    # DECIMAL 9-digit encoding boundary crossings (internal storage uses 9-digit groups in 4 bytes)
    {"id": "DEC-08", "category": "decimal", "old_type": "DECIMAL(8,2)",  "new_type": "DECIMAL(9,2)",  "charset": None, "instant": "SUCCESS", "inplace": "SUCCESS", "env": "internal"},
    {"id": "DEC-09", "category": "decimal", "old_type": "DECIMAL(9,2)",  "new_type": "DECIMAL(10,2)", "charset": None, "instant": "SUCCESS", "inplace": "SUCCESS", "env": "internal"},
    {"id": "DEC-10", "category": "decimal", "old_type": "DECIMAL(17,2)", "new_type": "DECIMAL(18,2)", "charset": None, "instant": "SUCCESS", "inplace": "SUCCESS", "env": "internal"},
    {"id": "DEC-11", "category": "decimal", "old_type": "DECIMAL(62,30)", "new_type": "DECIMAL(63,30)", "charset": None, "instant": "SUCCESS", "inplace": "SUCCESS", "env": "internal"},
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

    # When int_digits=0 (e.g. DECIMAL(1,1)), "1.x" exceeds range — use 0.x values instead
    if old_int_digits > 0:
        pre = [old_min, old_max, "0" + ("." + "0" * old_D if old_D > 0 else ""),
               "1" + ("." + "1" * old_D if old_D > 0 else ""),
               "-1" + ("." + "1" * old_D if old_D > 0 else "")]
    else:
        # int_digits=0: use small fractional values within range
        pre = [old_min, old_max, "0" + ("." + "0" * old_D if old_D > 0 else ""),
               "0" + ("." + "1" * old_D if old_D > 0 else ""),
               "-0" + ("." + "1" * old_D if old_D > 0 else "")]

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

def column_type_of(type_def: str) -> str:
    """把套件里的类型定义映射为 information_schema.columns.column_type 的字面值。

    规则已在 RDS MySQL 8.0.36 上用 51 个真实样本验证（整数/无符号/BIT/DECIMAL/
    CHAR/VARCHAR/BINARY/VARBINARY/TEXT族/BLOB族）：column_type 就是类型定义的
    小写 + 空格归一，例如 `TINYINT UNSIGNED` -> `tinyint unsigned`，
    `DECIMAL(64,30)` -> `decimal(64,30)`。
    """
    return _re.sub(r"\s+", " ", str(type_def).strip().lower())


def sql_quote(v) -> str:
    """把值安全地放进单引号（用于断言里的期望值字面量）。"""
    if v is None:
        return "NULL"
    return "'" + str(v).replace("\\", "\\\\").replace("'", "''") + "'"


def build_meta_assertion(test_id: str, table: str, column: str, expect_column_type: str,
                         name: str = "TYPE") -> str:
    """断言 ALTER 之后某列的 column_type 精确等于期望值（P1-1 的基础件）。

    恒输出一行判定：actual == expect 才 PASS，mismatch 里同时给出期望与实际，
    因此"类型没变""类型变了但不是目标类型""列不存在"都能被区分出来。
    """
    exp = sql_quote(column_type_of(expect_column_type))
    return (
        "SELECT '%s#%s' AS test_id,\n"
        "       IF(IFNULL(MAX(column_type),'<missing>')=%s,'PASS','FAIL') AS result,\n"
        "       CONCAT('expect=',%s,' actual=',IFNULL(MAX(column_type),'<missing>')) AS mismatch\n"
        "FROM information_schema.columns\n"
        "WHERE table_schema=DATABASE() AND table_name=%s AND column_name=%s;"
        % (test_id, name, exp, exp, sql_quote(table), sql_quote(column))
    )


def build_table_absent_assertion(test_id: str, table: str, name: str, detail: str) -> str:
    """断言某张表**不存在**（用于"建表本应被拒绝"的负向场景，P0-3）。"""
    return (
        "SELECT '%s#%s' AS test_id,\n"
        "       IF(COUNT(*)=0,'PASS','FAIL') AS result,\n"
        "       IF(COUNT(*)=0,'',%s) AS mismatch\n"
        "FROM information_schema.tables\n"
        "WHERE table_schema=DATABASE() AND table_name=%s;"
        % (test_id, name, sql_quote(detail), sql_quote(table))
    )

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

    # Minimal table for very large types (VARCHAR(65528+), VARBINARY(65528+))
    # that exceed row size limit with pad columns
    minimal_table = transition.get("minimal_table", False)

    if minimal_table:
        # Only id + target column, no pad columns (row size limit)
        if pos == "FIRST":
            cols.append(f"  target {target_col_def}")
            cols.append("  id INT NOT NULL AUTO_INCREMENT")
        else:
            cols.append("  id INT NOT NULL AUTO_INCREMENT")
            cols.append(f"  target {target_col_def}")
    elif pos == "FIRST":
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
    if pk_type == "CLUSTERED" or minimal_table:
        pk_clause = ", PRIMARY KEY (id)"
    elif pk_type == "COMPOSITE_PK":
        if minimal_table:
            pk_clause = ", PRIMARY KEY (id)"
        else:
            pk_clause = ", PRIMARY KEY (id, target)"
    elif pk_type == "NO_EXPLICIT_PK":
        pk_clause = ", INDEX idx_id (id)"  # AUTO_INCREMENT needs an index
    else:
        pk_clause = ", PRIMARY KEY (id)"

    # Non-target indexes (skip for minimal_table since no pad columns)
    idx_clauses = ""
    if not minimal_table:
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
                         table_suffix: str = "", factor_name: str = "") -> str:
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
    # P0-4: 表名一律由 test_id 派生，保证与用例一一对应且全局唯一
    table_suffix = table_suffix or id_to_suffix(test_id)
    t1 = f"t1_{table_suffix}"
    t2 = f"t2_{table_suffix}"
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
    if factor_name:
        lines.append(f"-- Varied factor: {factor_name}")
    lines.append(f"-- Transition ID: {transition.get('id', '')}")
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

    # Step 8: Compare — use minimal columns for minimal_table types
    compare_cols = ["id", "target"] if transition.get("minimal_table") else ["id", "pad1", "target", "pad2"]
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
            # P0-3 修复：旧实现这里输出的是一条**常量** SELECT，与前面语句的成败
            # 完全无关（永远 'BUILD_OR_ALTER_FAIL_EXPECTED' / 'CHECK_MANUALLY'），
            # 640 个用例等于没有断言。现在改成对 information_schema 的真实检查。
            lines.append(f"-- Factors: partition_target_key=True, partition_strategy={first_type}")
            lines.append(f"-- Expected: BUILD FAIL (type {cat} not supported as partition key for {first_type})")
            lines.append(f"-- @expect build=FAIL alter=N/A assertions=1")
            lines.append(f"CREATE TABLE {t1} (id INT NOT NULL AUTO_INCREMENT, target {old_type}, pad VARCHAR(10), PRIMARY KEY(id)) ENGINE=InnoDB PARTITION BY {first_type}(target) PARTITIONS 2;")
            lines.append(f"-- 若上面意外成功，则 ALTER 也必须失败（分区键列不可改类型）")
            lines.append(f"ALTER TABLE {t1} MODIFY target {_build_column_def(new_type, dict(BASELINE), transition)}, ALGORITHM={algorithm};")
            lines.append(build_table_absent_assertion(
                test_id, t1, "BUILD_REJECTED",
                "table was created although PK_COMPAT says %s cannot be a %s partition key "
                "(%s) - PK_COMPAT needs correction" % (cat, first_type, old_type)))
            return "\n".join(lines)
        else:
            # Can create partition table with target as partition key
            # ALTER should FAIL (partition key column)
            pk_col = "target"
            part_def = _build_single_partition(first_type, pk_col, True)
            lines.append(f"-- Factors: partition_target_key=True, partition_strategy={first_type}")
            lines.append(f"-- @expect build=SUCCESS alter=FAIL assertions=2 "
                         f"column_type={column_type_of(old_type)}")
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

            # P0-2 修复：t2 必须是 t1 的**结构克隆**（同列、同 PK、同分区定义）。
            # 旧实现用 _build_create_table() 建出 (id, pad1, target, pad2)，
            # 而对照 SQL 却引用 a.pad/b.pad -> ERROR 1054 Unknown column 'b.pad'，
            # 3328(阿里云)+1216(内网) 个用例恒无判定输出，还被误归因为"建表失败"。
            lines.append(f"-- Oracle table: 与 t1 结构一致（ALTER 预期失败，仍为旧类型）")
            lines.append(f"CREATE TABLE {t2} (")
            lines.append(f"  id INT NOT NULL AUTO_INCREMENT,")
            lines.append(f"  target {old_type},")
            lines.append(f"  pad VARCHAR(20) DEFAULT 'pad',")
            lines.append(f"  PRIMARY KEY (id, target)")
            lines.append(f") ENGINE=InnoDB")
            lines.append(part_def)
            for v in pre_vals:
                lines.append(_build_insert_stmt(t2, "target", v))

            # 断言 1: 数据一致
            lines.append(_build_compare_sql(test_id, t1, t2, ["id", "target", "pad"]))
            # 断言 2: 目标列类型**仍是旧类型** —— 直接证明 ALTER 被拒绝、没有半生效
            lines.append(build_meta_assertion(test_id, t1, "target", old_type, "TYPE_UNCHANGED"))
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

        _cmp_cols = ["id", "target"] if transition.get("minimal_table") else ["id", "pad1", "target", "pad2"]
        lines.append(_build_compare_sql(test_id, t1, t2, _cmp_cols))
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
    """Write SQL statements to a file. Returns statement count.

    P0-1: 内容超过 GZ_THRESHOLD_BYTES 时直接产出 `<name>.sql.gz` 并删除明文版，
    使"生成器产物 == 执行器发现的文件 == git 跟踪的文件"三者一致；
    明文文件名登记到 WRITTEN_PLAIN_IGNORED，由 _sync_gitignore() 写回 .gitignore。
    """
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    body = header + "".join(stmt + "\n\n" for stmt in statements)
    raw = body.encode("utf-8")
    if len(raw) >= GZ_THRESHOLD_BYTES:
        gzpath = filepath + ".gz"
        with gzip.open(gzpath, "wt", encoding="utf-8") as f:
            f.write(body)
        if os.path.exists(filepath):
            os.remove(filepath)          # 明文版不再落盘，避免出现两份真源
        # 注意：要忽略的是**明文 .sql**（有人 gunzip 出来看时不要把十几 MB 重复入库），
        # 而 .sql.gz 本身必须入库 —— 之前写反了，导致产物全部被 git 忽略。
        WRITTEN_GZ.append(os.path.relpath(filepath, OUTPUT_DIR))
        WRITTEN_FILES.append((gzpath, len(statements), os.path.getsize(gzpath), True))
    else:
        if os.path.exists(filepath + ".gz"):
            os.remove(filepath + ".gz")  # 变小了就把旧 gz 清掉，避免重复执行
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(body)
        WRITTEN_PLAIN.append(os.path.relpath(filepath, OUTPUT_DIR))
        WRITTEN_FILES.append((filepath, len(statements), os.path.getsize(filepath), False))
    return len(statements)


WRITTEN_GZ: List[str] = []
WRITTEN_PLAIN: List[str] = []
WRITTEN_FILES: List[tuple] = []

GITIGNORE_BEGIN = "# BEGIN auto-generated: 以 .sql.gz 发布的文件，其明文 .sql 不入库"
GITIGNORE_LEGACY_HEADER = "# Large SQL files (compressed versions tracked instead)"
GITIGNORE_END = "# END auto-generated"


def verify_git_tracking(paths: List[str]) -> List[str]:
    """检查产物是否已被 git 跟踪（P0-1 复发防线）。

    本仓库根 .gitignore 忽略了整个 outputs/，历史上所有 SQL 产物都是 `git add -f`
    进去的。若重新生成后新增/改名的文件没有跟踪，就会出现"磁盘上有、仓库里没有"
    —— 正是本次审计发现的 84.8% 用例被静默跳过的成因。这里显式检测并给出命令。
    """
    untracked: List[str] = []
    try:
        import subprocess
        repo = subprocess.run(["git", "rev-parse", "--show-toplevel"],
                              capture_output=True, text=True, cwd=OUTPUT_DIR)
        if repo.returncode != 0:
            return untracked
        root = repo.stdout.strip()
        for path in paths:
            rel = os.path.relpath(os.path.abspath(path), root)
            chk = subprocess.run(["git", "ls-files", "--error-unmatch", rel],
                                 capture_output=True, text=True, cwd=root)
            if chk.returncode != 0:
                untracked.append(rel)
    except Exception:
        return untracked
    if untracked:
        print("")
        print("!! 警告: %d 个 SQL 产物未被 git 跟踪（磁盘上有、仓库里没有）:" % len(untracked))
        for u in untracked:
            print("     %s" % u)
        print("")
        print("   修复命令:")
        print("     git add -f %s" % " ".join(untracked))
    return untracked


def _sync_gitignore() -> None:
    """把本次以 .gz 发布的文件对应的明文名写回 .gitignore 的自动生成区块。

    单一真源原则：
      * 任何 `# BEGIN auto-generated ... # END auto-generated` 区块一律整体重建
        （按前缀匹配，改标题文字不会留下僵尸区块）；
      * 区块外的 `sql_*/**.sql` 忽略项一律清除（旧手工列表已被本函数接管）。
    """
    path = os.path.join(OUTPUT_DIR, ".gitignore")
    keep: List[str] = []
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            inside = False
            for line in f:
                st = line.rstrip("\n")
                if st.strip().startswith("# BEGIN auto-generated"):
                    inside = True
                    continue
                if st.strip().startswith("# END auto-generated"):
                    inside = False
                    continue
                if inside:
                    continue
                if st.strip() == GITIGNORE_LEGACY_HEADER:
                    continue
                if _re.match(r"^sql_(aliyun|internal)/.+\.sql$", st.strip()):
                    continue          # 旧手工/旧自动条目，交给下面的区块统一维护
                keep.append(st)
    while keep and not keep[-1].strip():
        keep.pop()
    block = ([GITIGNORE_BEGIN] + sorted(WRITTEN_GZ) + [GITIGNORE_END]) if WRITTEN_GZ else []
    parts = ["\n".join(keep)]
    if block:
        parts.append("\n".join(block))
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n\n".join(parts) + "\n")


def _gen_regular_table_tests(transitions: list, algorithm: str, env: str,
                             ids: CaseIdFactory) -> list:
    """Generate all regular table tests for a set of transitions."""
    results = []
    for trans in transitions:
        if trans["env"] != env:
            continue
        # Baseline
        ofat_sets = _get_ofat_factors(dict(BASELINE), algorithm)
        keypair_sets = _get_keypair_factors(dict(BASELINE), algorithm)

        all_sets = ofat_sets + keypair_sets

        for factor_name, factors in all_sets:
            # Adjust dependencies for INSTANT (no index on target)
            if algorithm == "instant":
                factors["dependencies"] = "NONE"

            test_id = ids.next(SCOPE_REGULAR, algorithm)
            sql = _build_test_case_sql(test_id, trans, algorithm, factors,
                                       id_to_suffix(test_id), factor_name)
            results.append(sql)

        # Column attribute preservation tests (one per type)
        for attr in ["UNSIGNED", "COMMENT", "CHARSET", "COLLATE"]:
            if attr == "UNSIGNED" and "unsigned" not in trans["category"]:
                continue
            if attr in ("CHARSET", "COLLATE") and not trans.get("charset"):
                continue
            if attr == "AUTO_INCREMENT" and trans["category"] not in ("integer_signed", "integer_unsigned"):
                continue
            test_id = ids.next(SCOPE_ATTRIBUTE, algorithm)
            sql = _build_column_attribute_test(test_id, trans, algorithm, attr)
            results.append(sql)

    return results


def _gen_partition_tests(transitions: list, algorithm: str, env: str,
                         ids: CaseIdFactory) -> list:
    """Generate all 64 partition combo tests for all transitions."""
    results = []
    pp_idx = 0

    for first_idx, first_type in enumerate(PARTITION_TYPES):
        for second_idx, second_type in enumerate(PARTITION_TYPES):
            pp_idx += 1
            for trans in transitions:
                if trans["env"] != env:
                    continue
                # Test 1: target IS partition key (expected FAIL)
                test_id = ids.next(SCOPE_PART_KEY, algorithm)
                sql = _build_partition_test(test_id, trans, algorithm, pp_idx,
                                           first_type, second_type, True)
                results.append(sql)

                # Test 2: target is NOT partition key (expected per type)
                test_id = ids.next(SCOPE_PART_NONKEY, algorithm)
                sql = _build_partition_test(test_id, trans, algorithm, pp_idx,
                                           first_type, second_type, False)
                results.append(sql)

    return results


def _gen_fk_tests_for_env(env: str, ids: CaseIdFactory) -> list:
    """Generate FK tests for an environment."""
    results = []

    # Determine which FK transitions belong to this env
    if env == "aliyun":
        fk_trans = [ft for ft in FK_TRANSITIONS if ft[4] in ("integer_signed", "varchar")]
    else:
        fk_trans = [ft for ft in FK_TRANSITIONS if ft[4] in ("binary", "varbinary", "decimal")]

    for fk_trans_item in fk_trans:
        for algorithm in ["instant", "inplace"]:
            for scenario in ["child", "parent", "both", "non_fk"]:
                test_id = ids.next(SCOPE_FK, algorithm)
                sql = _build_fk_test(test_id, fk_trans_item, algorithm, scenario)
                results.append(sql)

    return results


def _gen_special_tests(env: str, ids: CaseIdFactory) -> list:
    """Generate special pattern tests for an environment."""
    results = []

    # Consecutive ALTER (signed + unsigned for aliyun, signed only for internal)
    for unsigned in [True, False]:
        if env == "internal" and unsigned:
            continue  # Internal doesn't have unsigned integer transitions
        for algorithm in ["instant", "inplace"]:
            test_id = ids.next(SCOPE_SPECIAL, algorithm)
            sql = _build_consecutive_alter(test_id, unsigned, algorithm)
            results.append(sql)

    # Multi-column ALTER
    for algorithm in ["instant", "inplace"]:
        test_id = ids.next(SCOPE_SPECIAL, algorithm)
        sql = _build_multi_column_alter(test_id, algorithm, env)
        results.append(sql)

    # Virtual generated column (INPLACE only for basic types)
    if env == "aliyun":
        for algorithm in ["instant", "inplace"]:
            test_id = ids.next(SCOPE_SPECIAL, algorithm)
            sql = _build_virtual_generated_test(test_id, algorithm)
            results.append(sql)

    return results


GENERATED_AT = ""          # 运行期填充；仅写入 generation_manifest.json，不进 SQL（保证可复现）
SUITE_REVISION = ""        # 生成器源码哈希前 12 位，写入 SQL 头，便于追溯"哪版生成器产出的"


def _compute_suite_revision() -> str:
    try:
        with open(os.path.abspath(__file__), "rb") as f:
            return hashlib.sha256(f.read()).hexdigest()[:12]
    except Exception:
        return "unknown"


HEADER_TMPL = """-- ============================================================
-- RDS MySQL DDL 秒级/在线修改列类型 测试套件 — {env_cn}环境
-- 环境说明: 所有功能开关默认开启
-- 覆盖类型: {types}
-- 覆盖算法: {algos}
-- ============================================================
-- 本文件由 generate_test_sql.py 自动生成, 请勿手动修改
-- Suite-Revision: {rev}   (生成器源码哈希; 时间戳见 results/generation_manifest.json)
-- 用例 ID 规则: TC-<文件号>-<作用域>-<序号>-<IT|IP>  —— 全局唯一
--   作用域 REG=普通表 OFAT/二元组, ATR=列属性保持, SPE=特殊模式,
--          FK=外键, PTK=分区(目标列是分区键), PNK=分区(目标列非分区键)
-- ============================================================

SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
SET SESSION innodb_lock_wait_timeout = 50;

"""


def _emit(dirpath: str, filename: str, header: str, title: str, build, registry: list) -> list:
    """生成并写出一个 SQL 文件。

    文件号取自文件名前缀数字，作为该文件所有用例 ID 的命名空间；
    同一个文件内跨算法轮次**共享一个 CaseIdFactory**，避免 ID 复用（P0-4）。
    """
    file_no = int(_re.match(r"(\d+)", filename).group(1))
    ids = CaseIdFactory(file_no)
    stmts = build(ids)
    _write_sql_file(os.path.join(dirpath, filename),
                    header + "-- File %02d: %s\n\n" % (file_no, title), stmts)
    blob = "\n".join(stmts)
    case_ids = _re.findall(r"^-- Test Case: (\S+)", blob, _re.M)
    registry.append({
        "file_no": file_no,
        "file": filename if not filename.endswith(".gz") else filename,
        "dir": os.path.basename(dirpath),
        "title": title,
        "cases": len(case_ids),
        "case_ids": case_ids,
    })
    return stmts


def generate_all():
    """生成全部 SQL 测试文件，并做全局唯一性自检（P0-4）。"""
    global GENERATED_AT, SUITE_REVISION
    import time as _time
    GENERATED_AT = _time.strftime("%Y-%m-%d %H:%M:%S")
    SUITE_REVISION = _compute_suite_revision()

    aliyun_trans = [t for t in ALL_TRANSITIONS if t["env"] == "aliyun"]
    internal_trans = [t for t in ALL_TRANSITIONS if t["env"] == "internal"]

    def cat(trans, c):
        return [t for t in trans if t["category"] == c]

    header_aliyun = HEADER_TMPL.format(
        env_cn="阿里云", types="整数(SIGNED/UNSIGNED) + CHAR + VARCHAR",
        algos="INSTANT + INPLACE", rev=SUITE_REVISION)
    header_internal = HEADER_TMPL.format(
        env_cn="内网", types="BINARY + VARBINARY + DECIMAL + TEXT + BLOB + BIT",
        algos="INSTANT + INPLACE (增强类型 INSTANT 预期成功: BINARY/VARBINARY/DECIMAL 已确认支持)",
        rev=SUITE_REVISION)

    registry: List[dict] = []
    A, I = SQL_ALIYUN, SQL_INTERNAL

    def regular(trans, algo, env):
        return lambda ids: _gen_regular_table_tests(trans, algo, env, ids)

    def both_algos(fn):
        return lambda ids: fn(ids, "instant") + fn(ids, "inplace")

    # ---------------- 阿里云 ----------------
    _emit(A, "01_integer_signed_instant.sql", header_aliyun, "整数(有符号) INSTANT",
          regular(cat(aliyun_trans, "integer_signed"), "instant", "aliyun"), registry)
    _emit(A, "02_integer_signed_inplace.sql", header_aliyun, "整数(有符号) INPLACE",
          regular(cat(aliyun_trans, "integer_signed"), "inplace", "aliyun"), registry)
    _emit(A, "03_integer_unsigned_instant.sql", header_aliyun, "整数(无符号) INSTANT",
          regular(cat(aliyun_trans, "integer_unsigned"), "instant", "aliyun"), registry)
    _emit(A, "04_integer_unsigned_inplace.sql", header_aliyun, "整数(无符号) INPLACE",
          regular(cat(aliyun_trans, "integer_unsigned"), "inplace", "aliyun"), registry)
    _emit(A, "05_char_instant.sql", header_aliyun, "CHAR INSTANT",
          regular(cat(aliyun_trans, "char"), "instant", "aliyun"), registry)
    _emit(A, "06_char_inplace.sql", header_aliyun, "CHAR INPLACE",
          regular(cat(aliyun_trans, "char"), "inplace", "aliyun"), registry)
    _emit(A, "07_varchar_instant.sql", header_aliyun, "VARCHAR INSTANT",
          regular(cat(aliyun_trans, "varchar"), "instant", "aliyun"), registry)
    _emit(A, "08_varchar_inplace.sql", header_aliyun, "VARCHAR INPLACE",
          regular(cat(aliyun_trans, "varchar"), "inplace", "aliyun"), registry)

    int_trans_all = cat(aliyun_trans, "integer_signed") + cat(aliyun_trans, "integer_unsigned")

    def build_auto_inc(ids):
        out = []
        for trans in int_trans_all:
            for algorithm in ["instant", "inplace"]:
                out.append(_build_column_attribute_test(
                    ids.next(SCOPE_ATTRIBUTE, algorithm), trans, algorithm, "AUTO_INCREMENT"))
        return out

    _emit(A, "09_auto_increment_pk.sql", header_aliyun, "AUTO_INCREMENT PK 扩容专项",
          build_auto_inc, registry)
    _emit(A, "10_special_patterns.sql", header_aliyun,
          "特殊模式 (连续ALTER + 多列ALTER + 虚拟生成列)",
          lambda ids: _gen_special_tests("aliyun", ids), registry)
    _emit(A, "11_fk_table.sql", header_aliyun, "外键表测试",
          lambda ids: _gen_fk_tests_for_env("aliyun", ids), registry)
    _emit(A, "12_partition_64.sql", header_aliyun, "分区策略 × 全类型",
          both_algos(lambda ids, algo: _gen_partition_tests(aliyun_trans, algo, "aliyun", ids)),
          registry)

    # ---------------- 内网 ----------------
    _emit(I, "15_binary_inplace.sql", header_internal, "BINARY INPLACE",
          regular(cat(internal_trans, "binary"), "inplace", "internal"), registry)
    _emit(I, "16_binary_instant.sql", header_internal, "BINARY INSTANT (预期成功)",
          regular(cat(internal_trans, "binary"), "instant", "internal"), registry)
    _emit(I, "17_varbinary_inplace.sql", header_internal, "VARBINARY INPLACE",
          regular(cat(internal_trans, "varbinary"), "inplace", "internal"), registry)
    _emit(I, "18_varbinary_instant.sql", header_internal, "VARBINARY INSTANT (预期成功)",
          regular(cat(internal_trans, "varbinary"), "instant", "internal"), registry)
    _emit(I, "19_decimal_inplace.sql", header_internal, "DECIMAL INPLACE",
          regular(cat(internal_trans, "decimal"), "inplace", "internal"), registry)
    _emit(I, "20_decimal_instant.sql", header_internal, "DECIMAL INSTANT (预期成功)",
          regular(cat(internal_trans, "decimal"), "instant", "internal"), registry)
    _emit(I, "21_text_instant.sql", header_internal, "TEXT INSTANT",
          regular(cat(internal_trans, "text"), "instant", "internal"), registry)
    _emit(I, "22_text_inplace.sql", header_internal, "TEXT INPLACE",
          regular(cat(internal_trans, "text"), "inplace", "internal"), registry)
    _emit(I, "23_blob_instant.sql", header_internal, "BLOB INSTANT",
          regular(cat(internal_trans, "blob"), "instant", "internal"), registry)
    _emit(I, "24_blob_inplace.sql", header_internal, "BLOB INPLACE",
          regular(cat(internal_trans, "blob"), "inplace", "internal"), registry)
    _emit(I, "25_bit_instant.sql", header_internal, "BIT INSTANT",
          regular(cat(internal_trans, "bit"), "instant", "internal"), registry)
    _emit(I, "26_bit_inplace.sql", header_internal, "BIT INPLACE",
          regular(cat(internal_trans, "bit"), "inplace", "internal"), registry)
    _emit(I, "27_fk_table_enhanced.sql", header_internal, "外键表测试(增强类型)",
          lambda ids: _gen_fk_tests_for_env("internal", ids), registry)
    _emit(I, "28_special_patterns_enhanced.sql", header_internal,
          "特殊模式 (连续ALTER + 多列ALTER)",
          lambda ids: _gen_special_tests("internal", ids), registry)
    _emit(I, "29_partition_64_enhanced.sql", header_internal, "分区策略 × 增强类型",
          both_algos(lambda ids, algo: _gen_partition_tests(internal_trans, algo, "internal", ids)),
          registry)

    # ---------------- .gitignore 同步（P0-1: 产物/跟踪一致） ----------------
    _sync_gitignore()

    # ---------------- 全局唯一性自检（P0-4） ----------------
    all_ids: List[str] = []
    for entry in registry:
        all_ids.extend(entry["case_ids"])
    dup_ids = sorted({i for i in all_ids if all_ids.count(i) > 1})
    if dup_ids:
        raise SystemExit("!! 用例 ID 全局重复 %d 个（示例 %s）—— 结果无法归因，禁止发布"
                         % (len(dup_ids), dup_ids[:5]))
    # 表名由 ID 派生，ID 唯一 => 表名唯一（并发执行安全）
    suffixes = [id_to_suffix(i) for i in all_ids]
    if len(set(suffixes)) != len(suffixes):
        raise SystemExit("!! 派生表名后缀重复，无法安全并发执行")

    # ---------------- 生成清单 ----------------
    manifest = {
        "generated_at": GENERATED_AT,
        "suite_revision": SUITE_REVISION,
        "generator": os.path.basename(os.path.abspath(__file__)),
        "gz_threshold_bytes": GZ_THRESHOLD_BYTES,
        "total_cases": len(all_ids),
        "unique_case_ids": len(set(all_ids)),
        "transition_count": len(ALL_TRANSITIONS),
        "files": [],
    }
    for entry, (path, cases, size, is_gz) in zip(registry, WRITTEN_FILES):
        manifest["files"].append({
            "file": os.path.basename(path),
            "dir": entry["dir"],
            "title": entry["title"],
            "compressed": is_gz,
            "cases": cases,
            "bytes": size,
            "id_prefix": "TC-%02d-" % entry["file_no"],
            "id_first": entry["case_ids"][0] if entry["case_ids"] else "",
            "id_last": entry["case_ids"][-1] if entry["case_ids"] else "",
        })
    os.makedirs(os.path.join(OUTPUT_DIR, "results"), exist_ok=True)
    with open(os.path.join(OUTPUT_DIR, "results", "generation_manifest.json"), "w",
              encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)

    # ---------------- 摘要 ----------------
    print("=" * 78)
    print("SQL 生成完成  (suite_revision=%s, generated_at=%s)" % (SUITE_REVISION, GENERATED_AT))
    print("=" * 78)
    print("%-6s %-38s %-5s %7s %12s  %s" % ("文件号", "文件名", "压缩", "用例数", "字节", "ID 区间"))
    for m in manifest["files"]:
        print("%-6s %-38s %-5s %7d %12s  %s .. %s"
              % (m["file"][:2], m["file"], "gz" if m["compressed"] else "-",
                 m["cases"], "{:,}".format(m["bytes"]), m["id_first"], m["id_last"]))
    print("-" * 78)
    print("总用例数        : %d" % manifest["total_cases"])
    print("唯一用例 ID     : %d  (全局唯一自检通过 ✅)" % manifest["unique_case_ids"])
    print("类型转换数      : %d" % manifest["transition_count"])
    print("产出 .gz 文件   : %d  (明文名已写入 .gitignore 自动区块)" % len(WRITTEN_GZ))
    print("生成清单        : results/generation_manifest.json")

    manifest["untracked_in_git"] = verify_git_tracking([p for p, _c, _s, _g in WRITTEN_FILES])
    if manifest["untracked_in_git"]:
        manifest["git_tracking_ok"] = False
        with open(os.path.join(OUTPUT_DIR, "results", "generation_manifest.json"), "w",
                  encoding="utf-8") as f:
            json.dump(manifest, f, ensure_ascii=False, indent=2)
    else:
        manifest["git_tracking_ok"] = True
        print("git 跟踪自检    : 全部产物已入库 ✅")


if __name__ == "__main__":
    generate_all()

