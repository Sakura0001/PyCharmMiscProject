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
SCOPE_FORM = "FRM"         # DDL 语句形态专项 (DEFAULT/LOCKNONE/CHANGE/COPY)
SCOPE_TIMING = "TMG"       # 秒级差分计时专项
SCOPE_INDEX = "IDX"        # 索引与约束完整性专项


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
    # P0-8 修正：原值 VARCHAR(16382)->VARCHAR(16383) utf8mb4 / VARCHAR(65528)->VARCHAR(65529) latin1
    # 在 RDS 8.0.36 与社区版 8.0.45 上都**建不出表**（errno 1118 Row size too large），
    # 因为 minimal_table 里还有 id INT(4 字节)：16383*4+2+4 = 65538 > 65535。
    # 二分实测（id INT AUTO_INCREMENT PRIMARY KEY + target 两列表）真实上界：
    #   utf8mb4 VARCHAR = 16382、latin1 VARCHAR = 65528、VARBINARY = 65528
    # 故"转换到 MySQL 上限"的正确用例是 16381->16382 / 65527->65528；
    # 再 +1 就是超上限负向探针（应 errno 1118）。
    {"id": "VC-08", "category": "varchar", "old_type": "VARCHAR(16381)", "new_type": "VARCHAR(16382)", "charset": "utf8mb4", "old_max_len": 16381, "new_max_len": 16382, "instant": "SUCCESS", "inplace": "SUCCESS", "env": "aliyun", "minimal_table": True},
    {"id": "VC-09", "category": "varchar", "old_type": "VARCHAR(65527)", "new_type": "VARCHAR(65528)", "charset": "latin1", "old_max_len": 65527, "new_max_len": 65528, "instant": "SUCCESS", "inplace": "SUCCESS", "env": "aliyun", "minimal_table": True},
]

INTERNAL_TRANSITIONS = [
    # BINARY
    {"id": "BIN-01", "category": "binary",    "old_type": "BINARY(10)",  "new_type": "BINARY(20)",  "charset": None, "old_max_len": 10,  "new_max_len": 20,  "instant": "SUCCESS", "inplace": "SUCCESS", "env": "internal"},
    {"id": "BIN-02", "category": "binary",    "old_type": "BINARY(40)",  "new_type": "BINARY(80)",  "charset": None, "old_max_len": 40,  "new_max_len": 80,  "instant": "SUCCESS", "inplace": "SUCCESS", "env": "internal"},
    {"id": "BIN-03", "category": "binary",    "old_type": "BINARY(254)", "new_type": "BINARY(255)", "charset": None, "old_max_len": 254, "new_max_len": 255, "instant": "SUCCESS", "inplace": "SUCCESS", "env": "internal"},
    # VARBINARY
    {"id": "VBIN-01", "category": "varbinary", "old_type": "VARBINARY(20)",  "new_type": "VARBINARY(40)",  "charset": None, "old_max_len": 20,  "new_max_len": 40,  "instant": "SUCCESS", "inplace": "SUCCESS", "env": "internal"},
    {"id": "VBIN-02", "category": "varbinary", "old_type": "VARBINARY(100)", "new_type": "VARBINARY(200)", "charset": None, "old_max_len": 100, "new_max_len": 200, "instant": "SUCCESS", "inplace": "SUCCESS", "env": "internal"},
    # P0-8 修正：同上，VARBINARY(65529) 配 id INT 会超 65535 行宽上限（实测 errno 1118）
    {"id": "VBIN-03", "category": "varbinary", "old_type": "VARBINARY(65527)", "new_type": "VARBINARY(65528)", "charset": None, "old_max_len": 65527, "new_max_len": 65528, "instant": "SUCCESS", "inplace": "SUCCESS", "env": "internal", "minimal_table": True},
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
# Section 1b: 环境能力画像（Env Capability Profiles）
# ============================================================
# 不同实例（阿里云 RDS / 内网 RDS / 社区版）对同一转换的支持范围不同。
# 把这些差异表达成**数据**而不是散落在各处的 if：
#   * 换实例只改画像，不改生成逻辑
#   * 每条画像都注明实测/口径出处
#   * 差异可以 diff 审阅，报告里能直接引用
#
# CHARVARCHAR_MODE 的四种取值（对应"同字节/跨字节"口径）：
#   CROSS_ONLY  只支持**跨**长度字节桶的变更（如 VARCHAR(255)->(256) latin1、
#               VARCHAR(63)->(64) utf8mb4 即 252->256 字节）；同桶变更 => 预期 FAIL
#   SAME_ONLY   只支持**同**桶变更；跨桶 => 预期 FAIL
#   ALL         两种都支持（阿里云 RDS 8.0.36 实测行为，5228/5228 PASS）
#   NONE        两种都不支持
CROSS_ONLY, SAME_ONLY, ALL_SUPPORTED, NONE_SUPPORTED = "cross_only", "same_only", "all", "none"

# 长度字节桶：VARCHAR/VARBINARY 的最大字节数 <=255 用 1 字节长度前缀，否则 2 字节。
# CHAR 是定长存储、没有长度前缀，但其"字节宽度"同样以 255 为界（pack length 语义），
# 因此这里对 CHAR/VARCHAR 用同一个桶函数，保证口径一致。
LEN_BUCKET_BOUNDARY = 255

ENV_PROFILES = {
    # 阿里云 RDS MySQL 8.0.36：CHAR/VARCHAR 同桶与跨桶变更 INSTANT+INPLACE 均支持
    # （实测 5228/5228 PASS，见 FIX_LOG Step 5/7）
    "aliyun": {"charvarchar": ALL_SUPPORTED},
    # 内网实例：按测试同学口径"不支持 CHAR/VARCHAR 同字节变更，只支持跨字节变更"
    # => CROSS_ONLY。可用 --charvarchar-mode 覆盖，无需改代码。
    "internal": {"charvarchar": CROSS_ONLY},
    # 说明：其它实例（如社区版）尚未做完整画像实测，先不内置口径，
    # 需要时用 --charvarchar-mode 临时指定；实测清楚后再补进 ENV_PROFILES。
    # 已实测的社区版 8.0.45 片段：VARCHAR 同桶扩容 INPLACE 支持 / INSTANT 不支持(1845)，
    # 跨桶(255->256) INPLACE 也不支持(1846)，CHAR 改长度两种算法都不支持(1846)。
}
CHARVARCHAR_MODE_CLI = None      # 由 --charvarchar-mode 设置，覆盖 ENV_PROFILES


def len_bucket(max_bytes: Optional[int]) -> Optional[int]:
    if max_bytes is None:
        return None
    return 1 if max_bytes <= LEN_BUCKET_BOUNDARY else 2


def transition_len_bucket_change(transition: dict) -> Optional[str]:
    """返回 'same' / 'cross' / None（非 CHAR/VARCHAR 类）。"""
    if transition.get("category") not in ("char", "varchar"):
        return None
    ob = _type_max_bytes(transition["old_type"], transition.get("charset"))
    nb = _type_max_bytes(transition["new_type"], transition.get("charset"))
    bo, bn = len_bucket(ob), len_bucket(nb)
    if bo is None or bn is None:
        return None
    return "same" if bo == bn else "cross"


def charvarchar_mode(env: str) -> str:
    if CHARVARCHAR_MODE_CLI:
        return CHARVARCHAR_MODE_CLI
    return ENV_PROFILES.get(env, {}).get("charvarchar", ALL_SUPPORTED)


def resolve_expectation(transition: dict, algorithm: str, env: str) -> Tuple[str, list, str]:
    """解析某条转换在某环境/某算法下的期望结果。

    返回 (SUCCESS|FAIL, [允许的 errno], 命中的画像规则 id)。
    """
    base = transition.get(algorithm.lower(), "SUCCESS")
    mode = charvarchar_mode(env)
    kind = transition_len_bucket_change(transition)
    if kind and mode != ALL_SUPPORTED:
        unsupported = (kind == "same" and mode == CROSS_ONLY) or \
                      (kind == "cross" and mode == SAME_ONLY) or (mode == NONE_SUPPORTED)
        if unsupported and base == "SUCCESS":
            return "FAIL", [1846, 1845], "PROFILE:%s/charvarchar=%s(%s桶不支持)" % (env, mode, kind)
    if base == "FAIL":
        return "FAIL", [1846, 1845], ""
    return "SUCCESS", [], ""


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


# 字符集 -> 默认排序规则（RDS 8.0.36 实测；注意 utf8 在 information_schema 里叫 utf8mb3）
DEFAULT_COLLATIONS = {
    "latin1": "latin1_swedish_ci",
    "utf8": "utf8mb3_general_ci",
    "utf8mb3": "utf8mb3_general_ci",
    "utf8mb4": "utf8mb4_0900_ai_ci",
}
# information_schema 里 utf8 一律显示为 utf8mb3
IS_CHARSET_NAME = {"utf8": "utf8mb3", "utf8mb3": "utf8mb3",
                   "utf8mb4": "utf8mb4", "latin1": "latin1"}


def expected_meta(transition: dict, factors: dict, final_type: str,
                  overrides: Optional[dict] = None) -> dict:
    """推导 ALTER 之后目标列在 information_schema 里应有的元数据（P1-1）。

    每一项都在 RDS 8.0.36 上实测过表示形式：
      is_nullable YES/NO；column_default 有值为字符串、无值为 NULL；
      extra 对 INVISIBLE 列为 'INVISIBLE'；非字符串列 charset/collation 为 NULL；
      utf8 在 information_schema 中显示为 utf8mb3。
    """
    cat = transition.get("category", "")
    attrs = factors.get("target_attributes", "NULL_NO_DEFAULT")
    minimal = bool(transition.get("minimal_table"))
    pk = factors.get("primary_key", "CLUSTERED")
    pos = factors.get("target_position", "MIDDLE")

    not_null = attrs in ("NOT_NULL_NO_DEFAULT", "NOT_NULL_DEFAULT")
    if pk == "COMPOSITE_PK" and not minimal:
        not_null = True                      # 进了 PK 就隐式 NOT NULL
    has_default = attrs in ("CONSTANT_DEFAULT", "NOT_NULL_DEFAULT")
    extra = "INVISIBLE" if attrs == "INVISIBLE" else ""

    cs = transition.get("charset") if cat in ("char", "varchar", "text") else None
    cs_is = IS_CHARSET_NAME.get(cs) if cs else None
    coll = DEFAULT_COLLATIONS.get(cs) if cs else None

    if minimal:
        ordinal = 1 if pos == "FIRST" else 2
    else:
        ordinal = {"FIRST": 1, "MIDDLE": 3, "LAST": 4}.get(pos, 3)

    meta = {
        "column_type": column_type_of(final_type),
        "is_nullable": "NO" if not_null else "YES",
        "has_default": 1 if has_default else 0,
        "charset": cs_is,
        "collation": coll,
        "extra": extra,
        "ordinal_position": ordinal,
    }
    if overrides:
        meta.update(overrides)
    return meta


def _lit_or_null(v):
    return "NULL" if v is None else sql_quote(v)


# 字符集/排序规则标 "*" 表示"不校验"：用于列字符集继承自库默认值的场景
# （不同实例的 character_set_database 可能不同，硬编码期望会造成环境相关的假失败）
DONT_CARE = "*"


def build_meta_assertion_full(test_id: str, table: str, column: str, meta: dict,
                              name: str = "META") -> str:
    """一次性断言列类型 + 可空性 + 默认值有无 + 字符集 + 排序规则 + extra + 列序。

    恒输出一行（聚合查询），mismatch 同时给出 actual 与 want，便于定位。
    这是 P1-1 的核心：旧套件 238 条元数据断言里，**没有一条**断言 ALTER 后的列类型。
    """
    cs_cond = "1=1" if meta["charset"] == DONT_CARE else \
        "(MAX(character_set_name) <=> %s)" % _lit_or_null(meta["charset"])
    coll_cond = "1=1" if meta["collation"] == DONT_CARE else \
        "(MAX(collation_name) <=> %s)" % _lit_or_null(meta["collation"])
    return (
        "SELECT '%s#%s' AS test_id,\n"
        "       IF(COUNT(*)=1\n"
        "          AND MAX(column_type)=%s\n"
        "          AND MAX(is_nullable)=%s\n"
        "          AND ((MAX(column_default) IS NOT NULL) = %d)\n"
        "          AND %s\n"
        "          AND %s\n"
        "          AND (MAX(extra) <=> %s)\n"
        "          AND MAX(ordinal_position)=%d,'PASS','FAIL') AS result,\n"
        "       CONCAT('rows=',COUNT(*),\n"
        "              ' actual[type=',IFNULL(MAX(column_type),'<missing>'),\n"
        "                     ' nullable=',IFNULL(MAX(is_nullable),'<missing>'),\n"
        "                     ' has_default=',(MAX(column_default) IS NOT NULL),\n"
        "                     ' charset=',IFNULL(MAX(character_set_name),'NULL'),\n"
        "                     ' collation=',IFNULL(MAX(collation_name),'NULL'),\n"
        "                     ' extra=',IFNULL(MAX(extra),'NULL'),\n"
        "                     ' pos=',IFNULL(MAX(ordinal_position),-1),']',\n"
        "              ' want[type=%s nullable=%s has_default=%d charset=%s collation=%s"
        " extra=%s pos=%d]') AS mismatch\n"
        "FROM information_schema.columns\n"
        "WHERE table_schema=DATABASE() AND table_name=%s AND column_name=%s;"
        % (test_id, name,
           sql_quote(meta["column_type"]), sql_quote(meta["is_nullable"]),
           meta["has_default"], cs_cond, coll_cond,
           sql_quote(meta["extra"]), meta["ordinal_position"],
           meta["column_type"], meta["is_nullable"], meta["has_default"],
           (meta["charset"] if meta["charset"] == DONT_CARE else (meta["charset"] or "NULL")),
           (meta["collation"] if meta["collation"] == DONT_CARE else (meta["collation"] or "NULL")),
           meta["extra"] or "", meta["ordinal_position"],
           sql_quote(table), sql_quote(column))
    )


def alter_sha(stmt: str) -> str:
    """ALTER 语句文本的短哈希，供执行器把"声明的期望"与"实际报错的语句"对上（P0-7）。"""
    return hashlib.sha1(stmt.rstrip().rstrip(";").encode("utf-8")).hexdigest()[:12]


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


# InnoDB 单个索引键上限（8.0 默认 DYNAMIC/COMPRESSED 行格式 = 3072 字节）。
# RDS 8.0.36 实测二分确认：latin1 VARCHAR 作分区键/索引列最大 3068 字节
# （3068 + 4 字节 id = 3072），utf8mb4 最大 VARCHAR(767)；再大 1 字节即 errno 1071。
INDEX_KEY_LIMIT_BYTES = 3072


def factor_needs_full_target_index(factors: dict, transition: dict) -> bool:
    """该因子组合是否要求在目标列上建**整列**索引（而非前缀索引）。

    注意 minimal_table 的降级规则（见 _build_create_table）：
      * dependencies=SECONDARY_INDEX/UNIQUE_INDEX -> `INDEX idx_target(target)`
        **不受** minimal_table 影响，照样会建整列索引 => 超 3072 字节必 errno 1071
      * primary_key=COMPOSITE_PK 在 minimal_table 下被降级成 `PRIMARY KEY (id)`，
        目标列上并没有索引 => 建表可行，不能判为 infeasible
    """
    minimal = bool(transition.get("minimal_table"))
    if factors.get("dependencies") in ("SECONDARY_INDEX", "UNIQUE_INDEX"):
        return True
    if factors.get("primary_key") == "COMPOSITE_PK" and not minimal:
        return True
    return False


def target_index_bytes(transition: dict) -> Optional[int]:
    """目标列（新旧类型取大者）的最大字节数；非字符/二进制类型返回 None。"""
    vals = [v for v in (_type_max_bytes(transition["old_type"], transition.get("charset")),
                        _type_max_bytes(transition["new_type"], transition.get("charset"))) if v]
    return max(vals) if vals else None


def check_case_feasible(transition: dict, factors: dict) -> Optional[str]:
    """返回 None 表示该 (转换 × 因子) 组合可建表；否则返回不可行原因。

    用途：把"物理上不可能建出来的表"从**静默 ERROR** 变成**显式负向用例**。
    旧实现对这类组合照样生成 CREATE，跑出来是一片 errno 1071/1118，
    被记成 NO_OUTPUT，既没验证任何东西，也污染了通过率统计。
    """
    idx_bytes = target_index_bytes(transition)
    if (idx_bytes and idx_bytes > INDEX_KEY_LIMIT_BYTES
            and factor_needs_full_target_index(factors, transition)):
        return ("target %s->%s needs %d bytes but the InnoDB index key limit is %d bytes; "
                "factor combination %s requires a FULL-column index on target "
                "(expect CREATE to fail with errno 1071)"
                % (transition["old_type"], transition["new_type"], idx_bytes,
                   INDEX_KEY_LIMIT_BYTES, _format_factors(factors)))
    return None


def _build_infeasible_case(test_id: str, transition: dict, algorithm: str, factors: dict,
                           reason: str, expect_errno: int = 1071) -> str:
    """生成一个"建表本应被拒绝"的显式负向用例（带真断言）。"""
    t1 = "t1_%s" % id_to_suffix(test_id)
    lines = []
    lines.append("-- Test Case: %s" % test_id)
    lines.append("-- Type: %s -> %s, Algorithm: %s, Expected: BUILD_FAIL"
                 % (transition["old_type"], transition["new_type"], algorithm))
    lines.append("-- Transition ID: %s" % transition.get("id", ""))
    lines.append("-- Varied factor: INFEASIBLE_COMBINATION")
    lines.append("-- Factors: %s" % _format_factors(factors))
    lines.append("-- @expect build=FAIL errno=[%d] alter=N/A assertions=1" % expect_errno)
    lines.append("-- Infeasible: %s" % reason)
    lines.append("DROP TABLE IF EXISTS %s;" % t1)
    sql_mode = "STRICT_TRANS_TABLES" if factors.get("sql_mode", "STRICT") == "STRICT" else ""
    lines.append("SET SESSION sql_mode = '%s';" % sql_mode)
    lines.append(_build_create_table(t1, transition["old_type"], factors, transition))
    lines.append(build_table_absent_assertion(
        test_id, t1, "BUILD_REJECTED",
        "table was created although the combination is physically infeasible: %s" % reason))
    return "\n".join(lines)


# 超上限值在 STRICT 模式下应被拒绝的错误码集合（实测 RDS 8.0.36）
NEG_ERRNOS = [1406, 1264, 1265, 167, 1264]


def _probe_sha1(stmt: str) -> str:
    """探针语句文本的短哈希，供执行器把"声明的期望"与"实际报错的语句"精确对上。"""
    return hashlib.sha1(stmt.encode("utf-8")).hexdigest()[:12]


def build_negative_probes(test_id: str, t1: str, t2: str, values: list,
                          strict: bool) -> Tuple[list, list, int]:
    """P0-6：把"超出新类型上限的值"真正插进去，并断言其行为。

    旧实现生成的是 `-- INSERT INTO ...`（整条被注释），全套件 2,623 条负向探针
    从未执行，而 upper_limit_coverage_report.md 却写着"插入超上限值(预期FAIL)"。

    新实现：
      1. 同一个超限值**同时**插入 t1 与对照表 t2 —— 两表类型相同，
         因此无论 STRICT(拒绝) 还是非 STRICT(截断+告警)，行为都必须完全一致；
      2. 用会话变量记录插入前后行数，断言:
           STRICT     -> t1_added = 0 且 t2_added = 0（超限值绝不能落库）
           非 STRICT  -> t1_added = t2_added（截断行为必须与对照表一致）
         两种模式都同时断言 t1 与 t2 完全对称；
      3. 每条探针语句的 sha1 写进 `@expect neg_probe=<sha1>=<errno|ACCEPTED>`，
         执行器据此把声明的期望与实际报错的语句精确对上（长字面量被截断也不受影响）。

    返回 (SQL 行列表, neg_probe 标记列表, 探针条数)。
    """
    lines: List[str] = []
    probes: List[str] = []
    if not values:
        return lines, probes, 0

    lines.append("-- Negative probes: 超出新类型上限的值（STRICT 必须拒绝 / 非 STRICT 必须与对照表一致）")
    lines.append("SET @neg_before_t1 = (SELECT COUNT(*) FROM %s);" % t1)
    lines.append("SET @neg_before_t2 = (SELECT COUNT(*) FROM %s);" % t2)
    n = 0
    for v in values:
        n += 1
        for tbl in (t1, t2):
            stmt = "INSERT INTO %s (target) VALUES (%s)" % (tbl, v)
            lines.append("-- probe %d/%d -> %s" % (n, len(values), tbl))
            lines.append(stmt + ";")
            probes.append("%s=%s" % (_probe_sha1(stmt),
                                     ("|".join(str(e) for e in sorted(set(NEG_ERRNOS)))
                                      if strict else "ACCEPTED")))
    added_t1 = "(SELECT COUNT(*) FROM %s) - @neg_before_t1" % t1
    added_t2 = "(SELECT COUNT(*) FROM %s) - @neg_before_t2" % t2
    if strict:
        cond = "%s = 0 AND %s = 0" % (added_t1, added_t2)
        expect_desc = "0 (STRICT: 超限值必须被拒绝)"
    else:
        cond = "%s = %s" % (added_t1, added_t2)
        expect_desc = "t1_added = t2_added (非 STRICT: 截断行为必须与对照表一致)"
    lines.append(
        "SELECT '%s#NEG_REJECTED' AS test_id,\n"
        "       IF(%s,'PASS','FAIL') AS result,\n"
        "       CONCAT('t1_added=',%s,' t2_added=',%s,"
        "' expect=%s sql_mode=',@@session.sql_mode) AS mismatch;"
        % (test_id, cond, added_t1, added_t2, expect_desc.replace("'", "")))
    return lines, probes, n


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
                         table_suffix: str = "", factor_name: str = "",
                         env: str = "aliyun") -> str:
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
    # P0-7/画像：期望值先过环境能力画像，再叠加因子交互调整
    expected, expected_errnos, profile_rule = resolve_expectation(transition, algorithm, env)

    # Adjust expected based on factor interactions
    # INSTANT fails when target is part of any index (PK, secondary, unique)
    #
    # P0-8: minimal_table 会把 COMPOSITE_PK **降级**成 PRIMARY KEY(id)
    # （见 _build_create_table），此时目标列不在任何索引里 => INSTANT 实际会成功。
    # 旧期望模型没考虑这个降级，一律判 FAIL，于是对照表按旧类型建，
    # 而 t1 的 ALTER 真的成功了 => 数据不一致，4 个 VC-08/VC-09 用例报 FAIL。
    minimal = bool(transition.get("minimal_table"))
    if algorithm.lower() == "instant":
        pk_type = factors.get("primary_key", "CLUSTERED")
        if pk_type == "COMPOSITE_PK" and not minimal:
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
    
    # P0-8: 物理不可行的 (转换 × 因子) 组合 => 显式负向用例，而不是静默 ERROR
    infeasible = check_case_feasible(transition, factors)
    if infeasible:
        return _build_infeasible_case(test_id, transition, algorithm, factors, infeasible)

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
    lines.append(f"-- @header_placeholder@")
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

    # Step 7b: 负向探针（P0-6）—— t2 建好之后才能同时探两边
    neg_lines, neg_probes, neg_n = build_negative_probes(
        test_id, t1, t2, data.get("post_fail", []),
        strict=(sql_mode_factor == "STRICT"))
    lines.extend(neg_lines)

    # Step 8: Compare — use minimal columns for minimal_table types
    compare_cols = ["id", "target"] if transition.get("minimal_table") else ["id", "pad1", "target", "pad2"]
    lines.append(_build_compare_sql(test_id, t1, t2, compare_cols))

    # Step 9: META 断言（P1-1）—— ALTER 之后目标列的元数据必须精确符合预期。
    # 成功路径 => 新类型；失败路径 => 仍是旧类型；两种情况都同时校验
    # 可空性 / 默认值有无 / 字符集 / 排序规则 / extra(INVISIBLE) / 列序。
    meta = expected_meta(transition, factors, t2_type)
    lines.append(build_meta_assertion_full(test_id, t1, "target", meta))

    # P0-7: 机读期望头（占位符在 neg_probes / alter_sha 已知后回填）
    n_assertions = 2 + (1 if neg_n else 0)      # PRIMARY 对照 + META (+ NEG_REJECTED)
    tag = ("-- @expect alter=%s build=SUCCESS assertions=%d neg_probes=%d alter_sha=%s"
           % (alter_expected, n_assertions, neg_n, alter_sha(alter_stmt)))
    if alter_expected == "FAIL":
        _en = sorted(set(expected_errnos or [1845, 1846, 1659, 3780]))
        tag += " errno=[%s]" % ",".join(str(e) for e in _en)
    if profile_rule:
        tag += " profile_rule=%s" % profile_rule.replace(" ", "_")
    tag += " column_type=%s" % sql_quote(meta["column_type"]).strip("'")
    for pr in neg_probes:
        tag += " neg_probe=%s" % pr
    text = "\n".join(lines)
    return text.replace("-- @header_placeholder@", tag)


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
# Section 5: Partition Strategy Generator（类型感知 + 真 SUBPARTITION）
# ============================================================
# P0-5 / P0-9 修复说明
# ------------------------------------------------------------
# 旧实现宣称"64 种分区组合"，但 _build_partition_def() 把二级分区类型直接丢弃
# （`return first, True`），实测两个分区文件里 SUBPARTITION 出现 **0 次**，
# PP-33(HASH+RANGE) 与 PP-37..PP-40 生成的 SQL 逐字相同 —— 64 组合实为 8 种、
# 每种重复 8 次；同时 _build_single_partition() 的分区界是硬编码整数字面量
# (100/200/300)：对 TINYINT(上限 127) 越界、对 VARCHAR 类型不符 -> errno 1654/1697，
# 建表直接失败（RDS 实测 30/103 抽样用例中招）。
#
# 新实现：
#   * 24 种**互不相同**的策略 = 8 种一级 + 16 种组合分区（真正的 SUBPARTITION BY）
#   * 分区界 / LIST 取值按列类型分派（整数、字符串、二进制各用各自的字面量）
#   * 兼容性矩阵 PARTITION_COMPAT 由 tools/probe_partition_compat.py 实测得出，
#     不再靠猜（旧 PK_COMPAT 对 decimal/text/blob 的 KEY 分区判断是错的）
#   * 目标列是分区键时，插入值必须落在分区定义内（LIST 用分组代表值）
#   * MySQL 语法要求 SUBPARTITION BY 写在分区定义列表**之前**

PARTITION_STRATEGIES = [
    ("RANGE", "RANGE", None),
    ("RANGE+SUB HASH", "RANGE", "HASH"),
    ("RANGE+SUB LINEAR HASH", "RANGE", "LINEAR HASH"),
    ("RANGE+SUB KEY", "RANGE", "KEY"),
    ("RANGE+SUB LINEAR KEY", "RANGE", "LINEAR KEY"),
    ("RANGE COLUMNS", "RANGE COLUMNS", None),
    ("RANGE COLUMNS+SUB HASH", "RANGE COLUMNS", "HASH"),
    ("RANGE COLUMNS+SUB LINEAR HASH", "RANGE COLUMNS", "LINEAR HASH"),
    ("RANGE COLUMNS+SUB KEY", "RANGE COLUMNS", "KEY"),
    ("RANGE COLUMNS+SUB LINEAR KEY", "RANGE COLUMNS", "LINEAR KEY"),
    ("LIST", "LIST", None),
    ("LIST+SUB HASH", "LIST", "HASH"),
    ("LIST+SUB LINEAR HASH", "LIST", "LINEAR HASH"),
    ("LIST+SUB KEY", "LIST", "KEY"),
    ("LIST+SUB LINEAR KEY", "LIST", "LINEAR KEY"),
    ("LIST COLUMNS", "LIST COLUMNS", None),
    ("LIST COLUMNS+SUB HASH", "LIST COLUMNS", "HASH"),
    ("LIST COLUMNS+SUB LINEAR HASH", "LIST COLUMNS", "LINEAR HASH"),
    ("LIST COLUMNS+SUB KEY", "LIST COLUMNS", "KEY"),
    ("LIST COLUMNS+SUB LINEAR KEY", "LIST COLUMNS", "LINEAR KEY"),
    ("HASH", "HASH", None),
    ("LINEAR HASH", "LINEAR HASH", None),
    ("KEY", "KEY", None),
    ("LINEAR KEY", "LINEAR KEY", None),
]
STRATEGY_MAP = {name: (first, sub) for name, first, sub in PARTITION_STRATEGIES}
ALL_STRATEGIES = [n for n, _f, _s in PARTITION_STRATEGIES]

# 实测兼容性矩阵（阿里云 RDS MySQL 8.0.36，2026-09-23，tools/probe_partition_compat.py）
PARTITION_COMPAT = {
    "integer_signed": ALL_STRATEGIES,
    "integer_unsigned": ALL_STRATEGIES,
    "char": ["RANGE COLUMNS", "RANGE COLUMNS+SUB KEY", "RANGE COLUMNS+SUB LINEAR KEY",
             "LIST COLUMNS", "LIST COLUMNS+SUB KEY", "LIST COLUMNS+SUB LINEAR KEY",
             "KEY", "LINEAR KEY"],
    "varchar": ["RANGE COLUMNS", "RANGE COLUMNS+SUB KEY", "RANGE COLUMNS+SUB LINEAR KEY",
                "LIST COLUMNS", "LIST COLUMNS+SUB KEY", "LIST COLUMNS+SUB LINEAR KEY",
                "KEY", "LINEAR KEY"],
    "binary": ["RANGE COLUMNS", "RANGE COLUMNS+SUB KEY", "RANGE COLUMNS+SUB LINEAR KEY",
               "LIST COLUMNS", "LIST COLUMNS+SUB KEY", "LIST COLUMNS+SUB LINEAR KEY",
               "KEY", "LINEAR KEY"],
    "varbinary": ["RANGE COLUMNS", "RANGE COLUMNS+SUB KEY", "RANGE COLUMNS+SUB LINEAR KEY",
                  "LIST COLUMNS", "LIST COLUMNS+SUB KEY", "LIST COLUMNS+SUB LINEAR KEY",
                  "KEY", "LINEAR KEY"],
    "decimal": ["KEY", "LINEAR KEY"],
    "bit": ["RANGE", "RANGE+SUB HASH", "RANGE+SUB LINEAR HASH", "RANGE+SUB KEY",
            "RANGE+SUB LINEAR KEY", "LIST", "LIST+SUB HASH", "LIST+SUB LINEAR HASH",
            "LIST+SUB KEY", "LIST+SUB LINEAR KEY", "HASH", "LINEAR HASH", "KEY", "LINEAR KEY"],
    "text": [],
    "blob": [],
}

# RANGE / RANGE COLUMNS 的界：必须与列类型匹配，且落在列值域内（TINYINT 上限 127！）
PARTITION_BOUNDS = {
    "integer_signed": ("0", "64"), "integer_unsigned": ("0", "64"),
    "char": ("''", "'m'"), "varchar": ("''", "'m'"),
    "binary": ("X'00'", "X'80'"), "varbinary": ("X'00'", "X'80'"),
    "bit": ("0", "64"), "decimal": ("0", "64"),
    # text/blob 实测对**任何**分区策略都不可作分区键(errno 1170 BLOB/TEXT used in key
    # specification without a key length / 1697 VALUES must have type INT)。
    # 这里仍给类型正确的字面量，让 BUILD_REJECTED 用例失败在**语义正确**的原因上。
    "text": ("''", "'m'"), "blob": ("X'00'", "X'80'"),
}
# LIST / LIST COLUMNS 的取值分组
PARTITION_LIST_GROUPS = {
    "integer_signed": [("-1", "0", "1"), ("2", "3", "4"), ("5", "6", "7")],
    "integer_unsigned": [("0", "1", "2"), ("3", "4", "5"), ("6", "7", "8")],
    "char": [("''", "'a'", "'b'"), ("'c'", "'d'"), ("'e'", "'f'")],
    "varchar": [("''", "'a'", "'b'"), ("'c'", "'d'"), ("'e'", "'f'")],
    "binary": [("X'00'", "X'01'"), ("X'02'", "X'03'"), ("X'04'", "X'05'")],
    "varbinary": [("X'00'", "X'01'"), ("X'02'", "X'03'"), ("X'04'", "X'05'")],
    "bit": [("0", "1"), ("2", "3"), ("4", "5")],
    "decimal": [("0", "1"), ("2", "3"), ("4", "5")],
    "text": [("''", "'a'", "'b'"), ("'c'", "'d'"), ("'e'", "'f'")],
    "blob": [("X'00'", "X'01'"), ("X'02'", "X'03'"), ("X'04'", "X'05'")],
}
# PNK 分支的分区键是自增 id：LIST 必须覆盖所有可能出现的 id（单用例 INSERT < 128 次）
ID_BOUNDS = ("0", "64")
ID_LIST_GROUPS = [tuple(str(i) for i in range(a, a + 32)) for a in (0, 32, 64, 96)]
KIND_INT_ID = "int_id"

CHARSET_MBMAXLEN = {"latin1": 1, "utf8mb3": 3, "utf8": 3, "utf8mb4": 4,
                    "ascii": 1, "binary": 1}


def _bounds_and_groups(kind: str):
    if kind == KIND_INT_ID:
        return ID_BOUNDS, ID_LIST_GROUPS
    return (PARTITION_BOUNDS.get(kind, ID_BOUNDS),
            PARTITION_LIST_GROUPS.get(kind, ID_LIST_GROUPS))


def build_partition_clause(strategy: str, kind: str) -> str:
    """按策略与列类型构造**类型正确**的分区子句（含真 SUBPARTITION）。"""
    first, sub = STRATEGY_MAP[strategy]
    col = "id" if kind == KIND_INT_ID else "target"
    bounds, groups = _bounds_and_groups(kind)

    if first in ("HASH", "LINEAR HASH", "KEY", "LINEAR KEY"):
        assert sub is None, "%s 不允许再带 SUBPARTITION" % first
        return "PARTITION BY %s (%s) PARTITIONS 4;" % (first, col)

    # 注意语法差异：RANGE/LIST 用 `PARTITION BY RANGE (col)`，
    # 而 RANGE COLUMNS/LIST COLUMNS 用 `PARTITION BY RANGE COLUMNS(col)`。
    # 之前统一拼成 "%s %s" 会生成 `RANGE COLUMNS COLUMNS(target)`（关键字重复）。
    if " " in first:
        head = "PARTITION BY %s(%s)" % (first, col)
    else:
        head = "PARTITION BY %s (%s)" % (first, col)
    if first in ("RANGE", "RANGE COLUMNS"):
        body = ("(\n  PARTITION p0 VALUES LESS THAN (%s),\n"
                "  PARTITION p1 VALUES LESS THAN (%s),\n"
                "  PARTITION p2 VALUES LESS THAN MAXVALUE)" % (bounds[0], bounds[1]))
    else:  # LIST / LIST COLUMNS
        parts = ["  PARTITION p%d VALUES IN (%s)" % (i, ", ".join(g))
                 for i, g in enumerate(groups)]
        body = "(\n%s)" % ",\n".join(parts)

    if sub:
        # MySQL: SUBPARTITION BY 必须写在分区定义列表之前
        head += "\nSUBPARTITION BY %s (%s) SUBPARTITIONS 2" % (sub, col)
    return head + "\n" + body + ";"


# 分区键列会进入 PRIMARY KEY(id, target)，因此受 InnoDB 3072 字节索引键上限约束。
# RDS 8.0.36 实测二分确认：latin1 VARCHAR 最大 3068、utf8mb4 VARCHAR 最大 767
# （767*4 = 3068），3068 + 4(id INT) = 3072 恰好达上限；再大 1 字节即 errno 1071。
PARTITION_KEY_MAX_BYTES = 3072
PARTITION_PK_ID_BYTES = 4


def partition_is_buildable(kind: str, strategy: str) -> bool:
    """该 category 是否允许用此策略分区（类型维度，来自实测矩阵）。"""
    return strategy in PARTITION_COMPAT.get(kind, [])


def partition_key_len_ok(transition: dict) -> Tuple[bool, Optional[int]]:
    """目标列长度是否允许进入分区键（长度维度）。返回 (是否可行, 目标列最大字节数)。"""
    mb = _type_max_bytes(transition["old_type"], transition.get("charset"))
    if mb is None:
        return True, None          # 整数/DECIMAL/BIT 等定长小类型不受此限
    return (mb + PARTITION_PK_ID_BYTES) <= PARTITION_KEY_MAX_BYTES, mb


def _partition_col_def(type_def: str, transition: dict) -> str:
    """分区表里目标列的定义 —— **必须带字符集**。

    之前 PTK 分支直接写 `target VARCHAR(1)`，用的是库默认字符集(utf8mb3)，
    而 ALTER 语句里写的是 `VARCHAR(2) CHARACTER SET latin1`：于是"改长度"
    变成了"改长度 + 改字符集"，INPLACE 被拒(1846)，11 个用例的
    TYPE_AFTER_ALTER 断言据此正确地判了 FAIL。
    """
    return _build_column_def(type_def, dict(BASELINE), transition)


def partition_fit_values(strategy: str, kind: str, data_values: list) -> list:
    """LIST/LIST COLUMNS 没有 MAXVALUE 兜底，只能插入分组里列出的值。

    旧实现对分区键列灌"类型边界值"（如 TINYINT 的 -128/127），在 LIST 分区上
    必然 errno 1526 "Table has no partition for value" —— 插入静默失败，
    用例退化成"空表对照"，什么也没验证。
    """
    first, _sub = STRATEGY_MAP[strategy]
    if first in ("LIST", "LIST COLUMNS"):
        _bounds, groups = _bounds_and_groups(kind)
        return [g[0] for g in groups]
    return list(data_values)


def _type_max_bytes(type_def: str, charset: Optional[str]) -> Optional[int]:
    td = _re.sub(r"\s+", "", str(type_def).upper())
    m = _re.match(r"^(VARBINARY|BINARY)\((\d+)\)$", td)
    if m:
        return int(m.group(2))
    m = _re.match(r"^(VARCHAR|CHAR)\((\d+)\)$", td)
    if m:
        mb = CHARSET_MBMAXLEN.get((charset or "latin1").lower(), 1)
        return int(m.group(2)) * mb
    return None


def crosses_len_prefix(transition: dict) -> bool:
    """VARCHAR/VARBINARY 扩容是否跨越 255 字节的长度前缀边界（1 字节 -> 2 字节）。

    跨越就必须重写行 => INPLACE 不可用；不跨越则是纯元数据变更。
    """
    ob = _type_max_bytes(transition["old_type"], transition.get("charset"))
    nb = _type_max_bytes(transition["new_type"], transition.get("charset"))
    if ob is None or nb is None:
        return False
    return (ob <= 255) != (nb <= 255)


def expected_partition_key_alter(transition: dict, algorithm: str,
                                 env: str = "aliyun") -> Tuple[str, list]:
    """目标列**是**分区键时，ALTER 的预期结果。返回 (SUCCESS|FAIL, [允许的 errno])。

    RDS MySQL 8.0.36 实测（tools/probe_partition_compat.py + 定向复核）：
      * 绝大多数类型改分区键列 => INSTANT 与 INPLACE 均 errno 1846
        （Cannot change column type INPLACE / Need to rebuild the table）
      * 唯一例外：VARCHAR / VARBINARY 且**不跨** 255 字节长度前缀边界的扩容，
        属纯元数据变更 => INPLACE 成功，INSTANT 仍被拒(1845)
      * ALGORITHM=COPY 在分区键上**可以**成功改类型（另有 COPY 对照组专项覆盖）
    旧实现一律假定"分区键不可改 => ALTER 预期失败"，与实测不符。
    """
    cat = transition.get("category", "")
    # 先看环境画像：该实例根本不支持这类 CHAR/VARCHAR 变更时，分区键场景自然也失败
    prof, prof_errnos, _rule = resolve_expectation(transition, algorithm, env)
    if prof == "FAIL":
        return "FAIL", sorted(set(prof_errnos + [1846, 3780, 1659]))
    if cat in ("varchar", "varbinary") and not crosses_len_prefix(transition):
        if algorithm == "inplace":
            return "SUCCESS", []
        return "FAIL", [1845, 1846]
    return "FAIL", [1846, 1845, 1659]


def _build_partition_test(test_id: str, transition: dict, algorithm: str,
                          pp_idx: int, strategy: str,
                          target_is_partition_key: bool, env: str = "aliyun") -> str:
    """生成一个分区表用例。

    target_is_partition_key=True  (PTK): 目标列是分区键
    target_is_partition_key=False (PNK): 分区键是自增 id，目标列是普通列
    """
    old_type = transition["old_type"]
    new_type = transition["new_type"]
    cat = transition["category"]
    data = gen_test_data(transition)

    t1 = "t1_%s" % id_to_suffix(test_id)
    t2 = "t2_%s" % id_to_suffix(test_id)

    lines = []
    lines.append("-- Test Case: %s" % test_id)
    lines.append("-- Type: %s -> %s, Algorithm: %s" % (old_type, new_type, algorithm))
    lines.append("-- Transition ID: %s" % transition.get("id", ""))
    lines.append("-- Partition: %s (#%02d/%d)" % (strategy, pp_idx, len(PARTITION_STRATEGIES)))
    lines.append("-- Target is partition key: %s" % target_is_partition_key)
    lines.append("DROP TABLE IF EXISTS %s, %s;" % (t1, t2))

    if not target_is_partition_key:
        # ---------------- PNK: 分区键是自增 id ----------------
        part_def = build_partition_clause(strategy, KIND_INT_ID)
        expected, _pnk_errnos, _pnk_rule = resolve_expectation(transition, algorithm, env)
        lines.append("-- Factors: partition_target_key=False, partition_strategy=%s" % strategy)
        lines.append("-- @pnk_expect_placeholder@")
        lines.append("-- Expected: CREATE OK, ALTER %s" % expected)
        lines.append(_build_create_table(t1, old_type, dict(BASELINE), transition,
                                         partition_def=part_def))
        pre_vals = list(data["pre_values"][:5])
        for v in pre_vals:
            lines.append(_build_insert_stmt(t1, "target", v))
        lines.append("-- ALTER expected %s" % expected)
        _pnk_alter = _build_alter_stmt(t1, "target",
                                       _build_column_def(new_type, dict(BASELINE), transition),
                                       algorithm)
        lines[lines.index("-- @pnk_expect_placeholder@")] = (
            "-- @expect build=SUCCESS alter=%s%s assertions=2 alter_sha=%s column_type=%s"
            % (expected, " errno=[1845,1846,1659]" if expected == "FAIL" else "",
               alter_sha(_pnk_alter),
               column_type_of(new_type if expected == "SUCCESS" else old_type)))
        lines.append(_pnk_alter)
        post_new = list(data["post_new_range"][:3])
        post_old = list(data["post_old_range"][:2])
        for v in post_new + post_old:
            lines.append(_build_insert_stmt(t1, "target", v))
        t2_type = new_type if expected == "SUCCESS" else old_type
        lines.append("-- Oracle table (%s, 非分区): %s" % ("新类型" if expected == "SUCCESS" else "旧类型", t2_type))
        lines.append(_build_create_table(t2, t2_type, dict(BASELINE), transition))
        for v in pre_vals + post_new + post_old:
            lines.append(_build_insert_stmt(t2, "target", v))
        cmp_cols = ["id", "target"] if transition.get("minimal_table") else ["id", "pad1", "target", "pad2"]
        lines.append(_build_compare_sql(test_id, t1, t2, cmp_cols))
        # 断言 2: ALTER 后的完整列元数据（类型 + 可空性 + 默认值 + 字符集 +
        # 排序规则 + extra + 列序）。PNK 的 t1 由 _build_create_table 按 BASELINE 建，
        # 形态是 (id, pad1, target, pad2) => target 在第 3 位、可空性由因子决定。
        lines.append(build_meta_assertion_full(
            test_id, t1, "target",
            expected_meta(transition, dict(BASELINE), t2_type), name="META"))
        return "\n".join(lines)

    # ---------------- PTK: 目标列是分区键 ----------------
    part_def = build_partition_clause(strategy, cat)
    buildable = partition_is_buildable(cat, strategy)
    len_ok, len_bytes = partition_key_len_ok(transition)

    if not (buildable and len_ok):
        # 建表本应被拒绝。用**类型正确**的分区定义去建，失败原因才是
        # "该类型不能作此类分区键"（1659/1697/1170/1491），而不是语法错(1064/1654)。
        lines.append("-- Factors: partition_target_key=True, partition_strategy=%s" % strategy)
        if not len_ok:
            reason = ("%s is %d bytes; partition key must fit the 3072-byte index limit "
                      "(%d + %d for id) - expect errno 1071"
                      % (old_type, len_bytes, len_bytes, PARTITION_PK_ID_BYTES))
            why = "target too long for partition key"
        else:
            reason = ("%s is not a legal partition key column for %s "
                      "(measured matrix: expect errno 1659/1697/1170/1491)" % (cat, strategy))
            why = "category incompatible with strategy"
        lines.append("-- @expect build=FAIL alter=N/A assertions=1")
        lines.append("-- Expected: BUILD FAIL (%s)" % why)
        lines.append("CREATE TABLE %s (\n  id INT NOT NULL AUTO_INCREMENT,\n  target %s,\n"
                     "  pad VARCHAR(20) DEFAULT 'pad',\n  PRIMARY KEY (id, target)\n) ENGINE=InnoDB"
                     % (t1, _partition_col_def(old_type, transition)))
        lines.append(part_def)
        lines.append(build_table_absent_assertion(
            test_id, t1, "BUILD_REJECTED",
            "table was created although %s - PARTITION_COMPAT/length rule needs correction"
            % reason))
        return "\n".join(lines)

    exp_alter, exp_errnos = expected_partition_key_alter(transition, algorithm, env)
    after_type = new_type if exp_alter == "SUCCESS" else old_type
    lines.append("-- Factors: partition_target_key=True, partition_strategy=%s" % strategy)
    lines.append("-- @ptk_expect_placeholder@")
    lines.append("-- Expected: CREATE OK, ALTER %s%s"
                 % (exp_alter, " (errno %s)" % "/".join(str(e) for e in exp_errnos) if exp_errnos else ""))
    create_body = ("CREATE TABLE %s (\n  id INT NOT NULL AUTO_INCREMENT,\n  target %s,\n"
                   "  pad VARCHAR(20) DEFAULT 'pad',\n  PRIMARY KEY (id, target)\n) ENGINE=InnoDB"
                   % (t1, _partition_col_def(old_type, transition)))
    lines.append(create_body)
    lines.append(part_def)

    # LIST/LIST COLUMNS 没有 MAXVALUE 兜底：只插入分组代表值，保证一定落进某个分区
    fit = partition_fit_values(strategy, cat, [v for v in data["pre_values"] if v != "NULL"])
    pre_vals = fit[:3] if fit else [v for v in data["pre_values"][:3] if v != "NULL"]
    for v in pre_vals:
        lines.append(_build_insert_stmt(t1, "target", v))

    lines.append("-- ALTER expected %s" % exp_alter)
    _ptk_alter = _build_alter_stmt(t1, "target",
                                   _build_column_def(new_type, dict(BASELINE), transition),
                                   algorithm)
    lines[lines.index("-- @ptk_expect_placeholder@")] = (
        "-- @expect build=SUCCESS alter=%s%s assertions=2 alter_sha=%s column_type=%s"
        % (exp_alter,
           (" errno=[%s]" % ",".join(str(e) for e in exp_errnos)) if exp_errnos else "",
           alter_sha(_ptk_alter), column_type_of(after_type)))
    lines.append(_ptk_alter)

    # Oracle: t1 的**结构克隆**（同列/同 PK/同分区定义），类型为 after_type
    lines.append("-- Oracle table: 与 t1 结构一致，类型 %s" % after_type)
    lines.append("CREATE TABLE %s (\n  id INT NOT NULL AUTO_INCREMENT,\n  target %s,\n"
                 "  pad VARCHAR(20) DEFAULT 'pad',\n  PRIMARY KEY (id, target)\n) ENGINE=InnoDB"
                 % (t2, _partition_col_def(after_type, transition)))
    lines.append(part_def)
    for v in pre_vals:
        lines.append(_build_insert_stmt(t2, "target", v))
    if exp_alter == "SUCCESS":
        # 分区键改类型成功（VARCHAR/VARBINARY 纯元数据扩容）=> 复验改后仍可写。
        # 注意：LIST/LIST COLUMNS 没有 MAXVALUE 兜底，post_new_range 里的值
        # （如 255 字符长串）不在任何分组里，插入必然 errno 1526；
        # 所以这里继续用一定落在分组内的 pre_vals。
        for v in pre_vals:
            lines.append(_build_insert_stmt(t1, "target", v))
            lines.append(_build_insert_stmt(t2, "target", v))

    lines.append(_build_compare_sql(test_id, t1, t2, ["id", "target", "pad"]))
    lines.append(build_meta_assertion_full(
        test_id, t1, "target",
        expected_meta(transition, dict(BASELINE), after_type,
                      overrides={"is_nullable": "NO", "ordinal_position": 2}),
        name="META"))
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


# 外键列改类型的实测规律（RDS MySQL 8.0.36，tools/fk_matrix_aliyun.json，66 条组合）：
#   R1 ALGORITHM=INSTANT 改 fk_col **一律失败**：MySQL 强制 fk_col 上有索引，
#      而目标列在索引里就不允许 INSTANT => errno 1845（DECIMAL/BIT 因类型本身不支持 => 1846）
#   R2 ALGORITHM=INPLACE 改 CHAR/VARCHAR/BINARY/VARBINARY 的 fk_col **一律成功**，
#      连"只改单侧"也成功 => 改完 parent=varchar(50) 与 child=varchar(100) 能和活的
#      外键约束共存，MySQL 对这类扩容**不做外键类型兼容性复核**（重要且反直觉）
#   R3 ALGORITHM=INPLACE 改整数（需 rebuild）：外键在 => errno 3780
#      "Referencing column and referenced column are incompatible"；
#      只有先 DROP FOREIGN KEY 才能成功
#   R4 SET foreign_key_checks=0 **不能**绕过 3780（常见误解，实测无效）
#   R5 DECIMAL/BIT 在该实例上任何算法都 1846（类型本身不支持），内网实例需另行实测
FK_STRING_CATEGORIES = ("char", "varchar", "binary", "varbinary")


def expected_fk_alter(cat: str, algorithm: str, scenario: str) -> Tuple[str, list]:
    """按实测规律推导外键场景下 ALTER 的预期结果（errno 取自实测，不做放宽）。

    注意错误码的**先后顺序**差异（实测）：
      * 整数 + INSTANT -> 3780：外键类型兼容性校验先于算法可行性校验触发
      * 字符串 + INSTANT -> 1845：算法可行性校验先失败，轮不到外键校验
      * DECIMAL/BIT -> 1846：该实例根本不支持这类改类型
    """
    is_int = cat.startswith("integer")
    is_str = cat in FK_STRING_CATEGORIES
    fk_gone = (scenario == "both_drop_fk")   # 外键已摘除，只剩"索引列不允许 INSTANT"
    if algorithm == "instant":
        if is_int:
            # 外键在 => 兼容性校验先失败(3780)；外键已摘 => 算法可行性校验失败(1845)
            return "FAIL", ([1845] if fk_gone else [3780])
        if is_str:
            return "FAIL", [1845]
        return "FAIL", [1846]                # decimal/bit/text/blob
    # INPLACE
    if is_str:
        return "SUCCESS", []                 # R2：连单侧改都成功，MySQL 不复核外键兼容性
    if is_int:
        return ("SUCCESS", []) if scenario == "both_drop_fk" else ("FAIL", [3780])   # R3
    return "FAIL", [1846]                    # R5


def _build_fk_test(test_id: str, fk_trans: tuple, algorithm: str, scenario: str) -> str:
    """Build FK test case. scenario: child/parent/both/non_fk"""
    fk_id, old_type, new_type, fk_col_type, cat, instant_exp, inplace_exp, single_exp, _notes = fk_trans
    expected = inplace_exp if algorithm == "inplace" else instant_exp

    # 期望模型（RDS MySQL 8.0.36 实测，见 FIX_LOG Step 7）：
    #   * 只要外键约束还在，改任一侧 fk_col 的类型都会 errno 3780
    #     "Referencing column and referenced column ... are incompatible"
    #   * `SET foreign_key_checks=0` **并不能**绕过（实测仍 3780）—— 常见误解
    #   * 唯一可行序列：DROP FOREIGN KEY -> 改两侧 -> ADD FOREIGN KEY
    if scenario == "non_fk":
        # 改的是非外键列 data，不涉及 R1~R3
        alter_expected, alter_errnos = expected, []
        if alter_expected == "FAIL":
            alter_errnos = [1845, 1846]
    else:
        alter_expected, alter_errnos = expected_fk_alter(cat, algorithm, scenario)

    t_parent = f"tp_{test_id.lower().replace(chr(45), chr(95))}"
    t_child = f"tc_{test_id.lower().replace(chr(45), chr(95))}"
    t2 = f"t2_{test_id.lower().replace(chr(45), chr(95))}"

    lines = []
    lines.append(f"-- Test Case: {test_id}")
    lines.append(f"-- FK Scenario: {scenario}, Algorithm: {algorithm}")
    lines.append(f"-- Type: {old_type} -> {new_type}")
    lines.append(f"-- FK Transition: {fk_id}")
    lines.append(f"-- Expected: {alter_expected}")
    lines.append(f"-- @fk_placeholder@")
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
    _fk_shas = []

    def _emit_alter(tbl, col, typ, comment):
        _cs = (" CHARACTER SET %s" % cs) if (cs and col == "fk_col") else ""
        _dflt = " DEFAULT 'child'" if col == "data" else ""
        _st = "ALTER TABLE %s MODIFY %s %s%s%s, ALGORITHM=%s;" % (tbl, col, typ, _cs, _dflt, algorithm)
        lines.append(comment)
        lines.append(_st)
        _fk_shas.append(alter_sha(_st))

    if scenario == "child":
        _emit_alter(t_child, "fk_col", new_type, "-- ALTER child table only")
    elif scenario == "parent":
        _emit_alter(t_parent, "fk_col", new_type, "-- ALTER parent table only")
    elif scenario == "both":
        _emit_alter(t_parent, "fk_col", new_type, "-- ALTER both tables (parent first, then child)")
        _emit_alter(t_child, "fk_col", new_type, "")
    elif scenario == "both_fkc0":
        # 反直觉结论的固化用例：关掉外键检查也**不能**改 FK 列类型
        lines.append("-- 实测: foreign_key_checks=0 并不能绕过 errno 3780")
        lines.append("SET foreign_key_checks=0;")
        _emit_alter(t_parent, "fk_col", new_type, "-- ALTER parent with fk_checks=0")
        _emit_alter(t_child, "fk_col", new_type, "")
        lines.append("SET foreign_key_checks=1;")
    elif scenario == "both_drop_fk":
        # 唯一可行的操作序列
        _cname = "%s_fk" % test_id.lower().replace("-", "_")
        lines.append("-- 正确序列: DROP FOREIGN KEY -> 改两侧 -> ADD FOREIGN KEY")
        lines.append("ALTER TABLE %s DROP FOREIGN KEY %s;" % (t_child, _cname))
        _emit_alter(t_parent, "fk_col", new_type, "-- ALTER parent (FK 已摘除)")
        _emit_alter(t_child, "fk_col", new_type, "")
        lines.append("ALTER TABLE %s ADD CONSTRAINT %s FOREIGN KEY (fk_col) REFERENCES %s(fk_col);"
                     % (t_child, _cname, t_parent))
    else:  # non_fk - modify a non-FK column
        _emit_alter(t_child, "data", "VARCHAR(50)", "-- ALTER non-FK column (data column)")

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

    # P1-1: FK 用例同样必须断言 ALTER 之后的列类型（子表 fk_col / data，父表 fk_col）
    _succ = (alter_expected == "SUCCESS")
    _n_meta = 0
    _fk_meta = {"category": cat, "charset": cs}
    if scenario == "child":
        _child_fk = new_type if _succ else old_type
        _parent_fk = old_type
        _child_data = "VARCHAR(20)"
    elif scenario == "parent":
        _child_fk = old_type
        _parent_fk = new_type if _succ else old_type
        _child_data = "VARCHAR(20)"
    elif scenario in ("both", "both_fkc0", "both_drop_fk"):
        # 两侧同改：结果取决于 expected_fk_alter 的实测结论 ——
        # 整数(需 rebuild)在外键还在时 3780 改不动；字符串扩容一律成功。
        # 之前把"整数场景改不动"错误地推广到了字符串，导致 4 个 META 断言假失败。
        _child_fk = new_type if _succ else old_type
        _parent_fk = new_type if _succ else old_type
        _child_data = "VARCHAR(20)"
    else:
        _child_fk = old_type
        _parent_fk = old_type
        _child_data = "VARCHAR(50)" if _succ else "VARCHAR(20)"
    lines.append(build_meta_assertion_full(
        test_id, t_child, "fk_col",
        expected_meta(_fk_meta, dict(BASELINE), _child_fk,
                      overrides={"ordinal_position": 2}), name="META_CHILD_FK"))
    _n_meta += 1
    lines.append(build_meta_assertion_full(
        test_id, t_child, "data",
        expected_meta({"category": "varchar", "charset": None}, dict(BASELINE), _child_data,
                      overrides={"ordinal_position": 3, "has_default": 1,
                                 # data 列没有显式字符集，继承 character_set_database，
                                 # 不同实例可能不同（RDS=utf8mb3 / 本机=utf8mb4）=> 不做硬断言
                                 "charset": DONT_CARE, "collation": DONT_CARE}),
        name="META_CHILD_DATA"))
    _n_meta += 1
    lines.append(build_meta_assertion_full(
        test_id, t_parent, "fk_col",
        expected_meta(_fk_meta, dict(BASELINE), _parent_fk,
                      overrides={"ordinal_position": 2}), name="META_PARENT_FK"))
    _n_meta += 1
    # both_drop_fk 场景：外键必须真的加回来了（否则"改成功"是靠永久丢约束换来的）
    _extra_assert = 0
    if scenario in ("both_drop_fk", "both", "both_fkc0", "child", "parent"):
        _cname = "%s_fk" % test_id.lower().replace("-", "_")
        lines.append(
            "SELECT '%s#FK_CONSTRAINT_PRESENT' AS test_id,\n"
            "       IF(COUNT(*)=1,'PASS','FAIL') AS result,\n"
            "       CONCAT('foreign key %s on %s: found=',COUNT(*)) AS mismatch\n"
            "FROM information_schema.table_constraints\n"
            "WHERE table_schema=DATABASE() AND table_name=%s AND constraint_type='FOREIGN KEY'\n"
            "  AND constraint_name=%s;"
            % (test_id, _cname, t_child, sql_quote(t_child), sql_quote(_cname)))
        _extra_assert += 1

    _text = "\n".join(lines)
    _tag = ("-- @expect alter=%s%s build=SUCCESS assertions=%d %s"
            % (alter_expected,
               (" errno=[%s]" % ",".join(str(e) for e in alter_errnos)) if alter_errnos else "",
               1 + _n_meta + _extra_assert, " ".join("alter_sha=%s" % x for x in _fk_shas)))
    return _text.replace("-- @fk_placeholder@", _tag)


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
    lines.append(f"-- @spe_chain_placeholder@")
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
    chain_shas = []
    for i in range(1, len(types)):
        lines.append(f"-- Step {i}: ALTER to {types[i]}")
        _st = f"ALTER TABLE {t1} MODIFY target {types[i]}, ALGORITHM={algorithm};"
        chain_shas.append(alter_sha(_st))
        lines.append(_st)
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
    # P1-1: 链式升级后必须断言最终列类型（表结构 id, target, pad => 第 2 位）
    lines.append(build_meta_assertion_full(
        test_id, t1, "target",
        expected_meta({"category": "integer_unsigned" if unsigned else "integer_signed",
                       "charset": None}, dict(BASELINE), final_type,
                      overrides={"ordinal_position": 2}),
        name="META"))
    _text = "\n".join(lines)
    _tag = ("-- @expect alter=SUCCESS build=SUCCESS assertions=2 column_type=%s %s"
            % (column_type_of(final_type),
               " ".join("alter_sha=%s" % x for x in chain_shas)))
    return _text.replace("-- @spe_chain_placeholder@", _tag)


def _build_multi_column_alter(test_id: str, algorithm: str, env: str) -> str:
    """Build multi-column ALTER test."""
    t1 = f"t1_{test_id.lower().replace(chr(45), chr(95))}"
    t2 = f"t2_{test_id.lower().replace(chr(45), chr(95))}"

    lines = []
    lines.append(f"-- Test Case: {test_id}")
    lines.append(f"-- Multi-column ALTER, Algorithm: {algorithm}")
    lines.append(f"-- @spe_multi_placeholder@")
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
    # P1-1: 多列同时改类型 => 每一列都要断言最终类型与列序
    _multi_final = {"col_int": "BIGINT", "col_char": "CHAR(20)",
                    "col_varchar": "VARCHAR(100)"}
    if env == "internal":
        _multi_final.update({"col_decimal": "DECIMAL(20,2)", "col_binary": "BINARY(20)",
                             "col_blob": "MEDIUMBLOB", "col_bit": "BIT(16)"})
    _n_meta = 0
    for _i, (_col, _typ) in enumerate(sorted(_multi_final.items(),
                                             key=lambda kv: compare_cols.index(kv[0])
                                             if kv[0] in compare_cols else 99)):
        _cat = ("char" if _col == "col_char" else "varchar" if _col == "col_varchar"
                else "decimal" if _col == "col_decimal" else "binary" if _col == "col_binary"
                else "blob" if _col == "col_blob" else "bit" if _col == "col_bit"
                else "integer_signed")
        _cs = "utf8mb4" if _col in ("col_char", "col_varchar") else None
        lines.append(build_meta_assertion_full(
            test_id, t1, _col,
            expected_meta({"category": _cat, "charset": _cs}, dict(BASELINE), _typ,
                          overrides={"ordinal_position": (compare_cols.index(_col) + 1)
                                     if _col in compare_cols else _i + 2}),
            name="META_%s" % _col.upper()))
        _n_meta += 1
    _text = "\n".join(lines)
    _tag = ("-- @expect alter=SUCCESS build=SUCCESS assertions=%d alter_sha=%s"
            % (1 + _n_meta, alter_sha(alter_stmt)))
    return _text.replace("-- @spe_multi_placeholder@", _tag)


def _build_virtual_generated_test(test_id: str, algorithm: str) -> str:
    """Build virtual generated column / function index test."""
    t1 = f"t1_{test_id.lower().replace(chr(45), chr(95))}"
    t2 = f"t2_{test_id.lower().replace(chr(45), chr(95))}"

    lines = []
    lines.append(f"-- Test Case: {test_id}")
    lines.append(f"-- Virtual generated column + function index, Algorithm: {algorithm}")
    lines.append(f"-- @spe_vcol_placeholder@")
    lines.append(f"DROP TABLE IF EXISTS {t1}, {t2};")

    # 实测（RDS 8.0.36）：即使目标列被 VIRTUAL 生成列引用、且生成列上有索引，
    # INSTANT 与 INPLACE 改类型**都成功**。旧模型假定 INSTANT 必失败，
    # 于是对照表按旧类型建、且跳过 post-ALTER 插入 => 用例恒 PASS，什么也没验证。
    expected = "SUCCESS"

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
    _vcol_alter = f"ALTER TABLE {t1} MODIFY base_col BIGINT, ALGORITHM={algorithm};"
    lines.append(_vcol_alter)

    # 注意：vcol = base_col * 2，因此 base_col 不能超过 BIGINT 的一半，
    # 否则 errno 1690 "BIGINT value is out of range" 会让整条多行 INSERT 失败、
    # 3 行数据全部丢失（旧实现灌 9223372036854775807，实测就是这么挂的）。
    _VMAX = 4611686018427387903      # 2^62 - 1
    _VMIN = -4611686018427387904     # -2^62
    if expected == "SUCCESS":
        lines.append(f"INSERT INTO {t1} (base_col) VALUES (2147483648), ({_VMAX}), ({_VMIN});")

    # Oracle table
    lines.append(f"CREATE TABLE {t2} (")
    lines.append(f"  id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,")
    lines.append(f"  base_col {'BIGINT' if expected == 'SUCCESS' else 'INT'},")
    lines.append(f"  vcol BIGINT AS (base_col * 2) VIRTUAL")
    lines.append(f") ENGINE=InnoDB;")
    lines.append(f"INSERT INTO {t2} (base_col) VALUES (0), (1), (-1), (2147483647), (42), (-42), (NULL);")
    if expected == "SUCCESS":
        lines.append(f"INSERT INTO {t2} (base_col) VALUES (2147483648), ({_VMAX}), ({_VMIN});")

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
    # P1-1: 断言 base_col 的最终类型（成功=>bigint，失败=>仍是 int）
    lines.append(build_meta_assertion_full(
        test_id, t1, "base_col",
        expected_meta({"category": "integer_signed", "charset": None}, dict(BASELINE),
                      "BIGINT" if expected == "SUCCESS" else "INT",
                      overrides={"ordinal_position": 2}),
        name="META"))
    _text = "\n".join(lines)
    _tag = ("-- @expect alter=%s%s build=SUCCESS assertions=2 alter_sha=%s column_type=%s"
            % (expected, " errno=[1845,1846]" if expected == "FAIL" else "",
               alter_sha(_vcol_alter),
               column_type_of("BIGINT" if expected == "SUCCESS" else "INT")))
    return _text.replace("-- @spe_vcol_placeholder@", _tag)


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
    lines.append(f"-- Transition ID: {transition.get('id', '')}")
    lines.append(f"-- @atr_placeholder@")
    lines.append(f"DROP TABLE IF EXISTS {t1}, {t2};")

    # Build column definition with specific attribute
    # P0-8: 之前只有 CHARSET/COLLATE 分支带字符集，UNSIGNED/COMMENT 分支写的是裸
    # `VARCHAR(65528)` -> 按库默认 utf8mb3 解析 -> errno 1074 "max = 21845"。
    base_old = _build_column_def(old_type, dict(BASELINE), transition)
    base_new = _build_column_def(new_type, dict(BASELINE), transition)
    if attr_type == "UNSIGNED":
        old_def = base_old
        new_def = base_new
    elif attr_type == "AUTO_INCREMENT":
        old_def = f"{old_type} NOT NULL AUTO_INCREMENT"
        new_def = f"{new_type} NOT NULL AUTO_INCREMENT"
    elif attr_type == "COMMENT":
        old_def = f"{base_old} COMMENT 'test_comment'"
        new_def = f"{base_new} COMMENT 'test_comment'"
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
        old_def = base_old
        new_def = base_new

    # minimal_table（VARCHAR(16381)+ / VARBINARY(65527)+ 这类逼近 65535 行宽上限的
    # 类型）不能再带 pad 列，否则 CREATE 直接 errno 1118。
    minimal = bool(transition.get("minimal_table"))
    cs = transition.get("charset")
    tbl_cs = ""
    if cs and transition["category"] in ("char", "varchar", "text"):
        tbl_cs = " DEFAULT CHARSET=%s" % ("utf8" if cs == "utf8mb3" else cs)
    if attr_type == "AUTO_INCREMENT":
        lines.append(f"CREATE TABLE {t1} (")
        lines.append(f"  id {old_def} PRIMARY KEY,")
        lines.append(f"  pad VARCHAR(20) DEFAULT 'pad'")
        lines.append(f") ENGINE=InnoDB{tbl_cs};")
    elif minimal:
        lines.append(f"CREATE TABLE {t1} (")
        lines.append(f"  id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,")
        lines.append(f"  target {old_def}")
        lines.append(f") ENGINE=InnoDB{tbl_cs};")
    else:
        lines.append(f"CREATE TABLE {t1} (")
        lines.append(f"  id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,")
        lines.append(f"  target {old_def},")
        lines.append(f"  pad VARCHAR(20) DEFAULT 'pad'")
        lines.append(f") ENGINE=InnoDB{tbl_cs};")

    data = gen_test_data(transition)
    for v in data["pre_values"][:5]:
        if attr_type == "AUTO_INCREMENT":
            lines.append(f"INSERT INTO {t1} (id) VALUES ({v});")
        else:
            lines.append(_build_insert_stmt(t1, "target", v))

    # Build alter with column def (may include COMMENT, CHARACTER SET, etc.)
    alter_col = "target" if attr_type != "AUTO_INCREMENT" else "id"
    # 实测（RDS MySQL 8.0.36，可复现）：AUTO_INCREMENT 列的类型加宽**不支持 INSTANT**，
    # 一律 errno 1845 "ALGORITHM=INSTANT is not supported for this operation"，
    # 与 SIGNED/UNSIGNED、是 PK 还是 UNIQUE 键都无关；INPLACE 与 COPY 均正常，
    # 普通列（非 AUTO_INCREMENT）的 INSTANT 加宽也正常。
    # 旧套件对本文件只断言 `extra LIKE '%auto_increment%'`（无论 ALTER 成败都为真），
    # 因此把这 20 个实际失败的用例报成了 PASS。
    _atr_exp_alter = "SUCCESS"
    _atr_exp_errno = []
    _atr_final_type = new_type
    if attr_type == "AUTO_INCREMENT" and algorithm == "instant":
        _atr_exp_alter = "FAIL"
        _atr_exp_errno = [1845]
        _atr_final_type = old_type
    lines.append("-- Expected: ALTER %s%s"
                 % (_atr_exp_alter,
                    (" (errno %s)" % "/".join(str(e) for e in _atr_exp_errno)) if _atr_exp_errno else ""))
    _atr_alter = _build_alter_stmt(t1, alter_col, new_def, algorithm)
    lines.append(_atr_alter)
    if data["post_new_range"]:
        for v in data["post_new_range"][:3]:
            if attr_type == "AUTO_INCREMENT":
                lines.append(f"INSERT INTO {t1} (id) VALUES ({v});")
            else:
                lines.append(_build_insert_stmt(t1, "target", v))

    # Verify attribute preserved
    if attr_type == "COMMENT":
        lines.append(f"SELECT '{test_id}' AS test_id, IF(COUNT(*)>0,'PASS','FAIL') AS result FROM information_schema.columns WHERE table_schema=DATABASE() AND table_name='{t1}' AND column_name='target' AND column_comment='test_comment';")
    elif attr_type == "CHARSET":
        # MySQL 8.0 reports utf8mb3 in information_schema (utf8 is an alias)
        if cs == "utf8mb3":
            cs_str = "utf8mb3"
        elif cs == "utf8mb4":
            cs_str = "utf8mb4"
        else:
            cs_str = cs or "latin1"
        lines.append(f"SELECT '{test_id}' AS test_id, IF(COUNT(*)>0,'PASS','FAIL') AS result FROM information_schema.columns WHERE table_schema=DATABASE() AND table_name='{t1}' AND column_name='target' AND character_set_name='{cs_str}';")
    elif attr_type == "COLLATE":
        # MySQL 8.0 stores utf8 as utf8mb3 in information_schema
        if cs == "utf8mb3":
            cs_str = "utf8mb3"
        elif cs and cs != "utf8mb3":
            cs_str = cs
        else:
            cs_str = "latin1"
        lines.append(f"SELECT '{test_id}' AS test_id, IF(COUNT(*)>0,'PASS','FAIL') AS result FROM information_schema.columns WHERE table_schema=DATABASE() AND table_name='{t1}' AND column_name='target' AND collation_name='{cs_str}_bin';")
    elif attr_type == "UNSIGNED":
        lines.append(f"SELECT '{test_id}' AS test_id, IF(COUNT(*)>0,'PASS','FAIL') AS result FROM information_schema.columns WHERE table_schema=DATABASE() AND table_name='{t1}' AND column_name='target' AND column_type LIKE '%unsigned%';")
    elif attr_type == "AUTO_INCREMENT":
        lines.append(f"SELECT '{test_id}' AS test_id, IF(COUNT(*)>0,'PASS','FAIL') AS result FROM information_schema.columns WHERE table_schema=DATABASE() AND table_name='{t1}' AND column_name='id' AND extra LIKE '%auto_increment%';")
    else:
        # Data comparison
        if minimal:
            lines.append(f"CREATE TABLE {t2} (id INT NOT NULL AUTO_INCREMENT PRIMARY KEY, target {new_def}) ENGINE=InnoDB{tbl_cs};")
        else:
            lines.append(f"CREATE TABLE {t2} (id INT NOT NULL AUTO_INCREMENT PRIMARY KEY, target {new_def}, pad VARCHAR(20) DEFAULT 'pad') ENGINE=InnoDB{tbl_cs};")
        for v in data["pre_values"][:5]:
            lines.append(_build_insert_stmt(t2, "target", v))
        if data["post_new_range"]:
            for v in data["post_new_range"][:3]:
                lines.append(_build_insert_stmt(t2, "target", v))
        lines.append(_build_compare_sql(test_id, t1, t2,
                                        ["id", "target"] if minimal else ["id", "target", "pad"]))

    # P1-1: 属性保持用例同样必须断言"列类型确实变成了新类型"。
    # 旧实现只查单个属性（column_comment / character_set_name / ...），从不断言
    # column_type，因此"ALTER 静默没生效"这类缺陷发现不了。
    if attr_type == "AUTO_INCREMENT":
        _meta = expected_meta(transition, dict(BASELINE), _atr_final_type, overrides={
            "is_nullable": "NO", "has_default": 0, "charset": None,
            "collation": None, "extra": "auto_increment", "ordinal_position": 1})
        _col = "id"
    else:
        # ATR 用例的表结构是 (id, target, pad) => target 在第 2 位，
        # 与常规用例的 (id, pad1, target, pad2) 第 3 位不同。
        _ov = {"ordinal_position": 2}
        if attr_type == "COLLATE":
            # 该变体显式声明 `<charset>_bin`，不是字符集的默认排序规则
            _cs_is = IS_CHARSET_NAME.get(transition.get("charset"))
            if _cs_is:
                _ov["collation"] = "%s_bin" % _cs_is
        _meta = expected_meta(transition, dict(BASELINE), _atr_final_type, overrides=_ov)
        _col = "target"
    lines.append(build_meta_assertion_full(test_id, t1, _col, _meta))

    _text = "\n".join(lines)
    _tag = ("-- @expect alter=%s%s build=SUCCESS assertions=2 alter_sha=%s column_type=%s"
            % (_atr_exp_alter,
               (" errno=[%s]" % ",".join(str(e) for e in _atr_exp_errno)) if _atr_exp_errno else "",
               alter_sha(_atr_alter), _meta["column_type"]))
    return _text.replace("-- @atr_placeholder@", _tag)



# ============================================================
# Section 7b: DDL 语句形态 / 秒级差分计时 / 索引完整性 专项
#             (P1-3 在线性与语句形态, P1-4 索引与约束复验)
# ============================================================
# 为什么需要这一节：
#   * 旧套件 19,021 条 ALTER **全部**显式写 ALGORITHM=，`LOCK=` 出现 0 次、`CHANGE` 0 次。
#     于是"在线(不阻塞 DML)"和"秒级(用户不写 ALGORITHM 时自动走 INSTANT)"这两个
#     PRD 核心卖点在纯 SQL 套件里没有任何直接证据。
#   * 旧套件对带索引的用例只比对数据行，ALTER 之后二级索引/唯一索引/前缀索引是否
#     被正确重建、唯一约束是否仍然生效，完全没有复验。

DDL_FORMS = [
    ("DEFAULT", "不写 ALGORITHM，由服务器自选（用户真实写法；不支持秒级时应回退 COPY 并仍然成功）"),
    ("LOCKNONE", "ALGORITHM=INPLACE, LOCK=NONE（在线性硬证明：必须能在不阻塞 DML 的前提下完成）"),
    ("CHANGE", "CHANGE 同时改名 + 改类型（旧套件 0 覆盖）"),
    ("COPY", "ALGORITHM=COPY（结果对照组：数据与元数据必须与秒级路径完全一致）"),
]

INDEX_KINDS = [
    ("SECONDARY", "INDEX idx_target (target)"),
    ("UNIQUE", "UNIQUE INDEX uq_target (target)"),
]


def _std_table_shape(transition):
    """专项用例统一采用 (id, pad1, target, pad2) 形态；minimal_table 时退化为 (id, target)。"""
    return not bool(transition.get("minimal_table"))


def _form_alter(form, t1, col_old, col_new, new_def, algorithm_hint):
    if form == "DEFAULT":
        return "ALTER TABLE %s MODIFY %s %s;" % (t1, col_old, new_def)
    if form == "LOCKNONE":
        return "ALTER TABLE %s MODIFY %s %s, ALGORITHM=INPLACE, LOCK=NONE;" % (t1, col_old, new_def)
    if form == "CHANGE":
        return "ALTER TABLE %s CHANGE %s %s %s;" % (t1, col_old, col_new, new_def)
    if form == "COPY":
        return "ALTER TABLE %s MODIFY %s %s, ALGORITHM=COPY;" % (t1, col_old, new_def)
    raise ValueError(form)


def build_ddl_form_case(test_id: str, transition: dict, env: str, form: str) -> str:
    """生成一个 DDL 语句形态用例（DEFAULT / LOCKNONE / CHANGE / COPY）。"""
    old_type, new_type = transition["old_type"], transition["new_type"]
    suf = id_to_suffix(test_id)
    t1, t2 = "t1_" + suf, "t2_" + suf
    minimal = not _std_table_shape(transition)

    inst_exp, inst_err, _r1 = resolve_expectation(transition, "instant", env)
    inplace_exp, inplace_err, _r2 = resolve_expectation(transition, "inplace", env)

    col_final = "target2" if form == "CHANGE" else "target"
    old_def = _build_column_def(old_type, dict(BASELINE), transition)
    new_def = _build_column_def(new_type, dict(BASELINE), transition)

    # 各形态的期望：
    #   DEFAULT  服务器自选算法；不支持秒级时回退 COPY，只要转换合法就应成功
    #   LOCKNONE 只有 INPLACE 被支持时才可能成功
    #   CHANGE   改名 + 改类型，用默认算法 => 应成功
    #   COPY     对照组，合法转换必成功
    if form == "LOCKNONE":
        exp, errnos = ("SUCCESS", []) if inplace_exp == "SUCCESS" else ("FAIL", sorted(set(inplace_err) | {1846, 1845}))
    else:
        exp, errnos = "SUCCESS", []
    final_type = new_type if exp == "SUCCESS" else old_type

    lines = []
    lines.append("-- Test Case: %s" % test_id)
    lines.append("-- DDL form: %s" % form)
    lines.append("-- Type: %s -> %s, Algorithm: %s, Expected: %s"
                 % (old_type, new_type, form.lower(), exp))
    lines.append("-- Transition ID: %s" % transition.get("id", ""))
    lines.append("-- Form note: %s" % dict((k, v) for k, v in DDL_FORMS)[form])
    lines.append("-- @form_placeholder@")
    lines.append("DROP TABLE IF EXISTS %s, %s;" % (t1, t2))
    lines.append("SET SESSION sql_mode = 'STRICT_TRANS_TABLES';")

    # t1
    if minimal:
        lines.append("CREATE TABLE %s (\n  id INT NOT NULL AUTO_INCREMENT,\n  target %s,"
                     " PRIMARY KEY (id)\n) ENGINE=InnoDB;" % (t1, old_def))
        cmp_cols = ["id", "target"]
    else:
        lines.append("CREATE TABLE %s (\n  id INT NOT NULL AUTO_INCREMENT,\n"
                     "  pad1 VARCHAR(20) DEFAULT 'pad1',\n  target %s,\n"
                     "  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id)\n) ENGINE=InnoDB;"
                     % (t1, old_def))
        cmp_cols = ["id", "pad1", "target", "pad2"]

    data = gen_test_data(transition)
    pre = [v for v in data["pre_values"] if v != "NULL"][:6] + ["NULL"]
    for v in pre:
        lines.append(_build_insert_stmt(t1, "target", v))

    alter_stmt = _form_alter(form, t1, "target", col_final, new_def, form)
    lines.append("-- ALTER (form=%s) expected %s" % (form, exp))
    lines.append(alter_stmt)

    post = ([v for v in data["post_new_range"] if v != "NULL"][:3]
            if exp == "SUCCESS" else [])
    for v in post:
        lines.append(_build_insert_stmt(t1, col_final, v))

    # t2: 期望的最终形态（CHANGE 形态下列名也变）
    t2_def = _build_column_def(final_type, dict(BASELINE), transition)
    if minimal:
        lines.append("CREATE TABLE %s (\n  id INT NOT NULL AUTO_INCREMENT,\n  %s %s,"
                     " PRIMARY KEY (id)\n) ENGINE=InnoDB;" % (t2, col_final, t2_def))
        cmp_cols2 = ["id", col_final]
    else:
        lines.append("CREATE TABLE %s (\n  id INT NOT NULL AUTO_INCREMENT,\n"
                     "  pad1 VARCHAR(20) DEFAULT 'pad1',\n  %s %s,\n"
                     "  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id)\n) ENGINE=InnoDB;"
                     % (t2, col_final, t2_def))
        cmp_cols2 = ["id", "pad1", col_final, "pad2"]
    for v in pre + post:
        lines.append(_build_insert_stmt(t2, col_final, v))

    # 断言 1: 数据对照（CHANGE 形态下两边列名都变成 target2）
    a_cols = ["id"] + (["pad1"] if not minimal else []) + [col_final] + \
             (["pad2"] if not minimal else [])
    lines.append(_build_compare_sql_named(test_id, t1, t2, a_cols, col_final))

    n_assert = 1
    # 断言 2: 最终列元数据
    meta = expected_meta(transition, dict(BASELINE), final_type,
                         overrides={"ordinal_position": (3 if not minimal else 2)})
    lines.append(build_meta_assertion_full(test_id, t1, col_final, meta, name="META"))
    n_assert += 1

    # 断言 3（仅 CHANGE）: 旧列名必须消失，证明改名真的发生
    if form == "CHANGE":
        lines.append(
            "SELECT '%s#OLD_COL_GONE' AS test_id,\n"
            "       IF(COUNT(*)=0,'PASS','FAIL') AS result,\n"
            "       CONCAT('old column `target` still present, count=',COUNT(*)) AS mismatch\n"
            "FROM information_schema.columns\n"
            "WHERE table_schema=DATABASE() AND table_name=%s AND column_name='target';"
            % (test_id, sql_quote(t1)))
        n_assert += 1

    tag = ("-- @expect alter=%s%s build=SUCCESS assertions=%d alter_sha=%s column_type=%s ddl_form=%s"
           % (exp, (" errno=[%s]" % ",".join(str(e) for e in errnos)) if errnos else "",
              n_assert, alter_sha(alter_stmt), meta["column_type"], form))
    return "\n".join(lines).replace("-- @form_placeholder@", tag)


def _build_compare_sql_named(test_id, t1, t2, columns, join_col):
    """对照 SELECT，可指定用于 JOIN 的列名（CHANGE 形态下目标列改名了）。"""
    col_cmp = " AND ".join("a.%s <=> b.%s" % (c, c) for c in columns)
    col_list = ", ".join(columns)
    return """SELECT '%s' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM %s
   WHERE id NOT IN (SELECT id FROM %s)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM %s
   WHERE id NOT IN (SELECT id FROM %s)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM %s a JOIN %s b ON a.id = b.id
   WHERE NOT (%s)
) AS mismatches;""" % (test_id, t1, t2, t2, t1, t1, t2, col_cmp)


# ---------------------------------------------------------------- 秒级差分计时
# 8192 行时 DDL 固定开销(约 80ms：MDL + 数据字典事务 + binlog + redo fsync)会淹没
# "改元数据 vs 重建表"的差异，实测比值只有 1.3~1.5，断言没有分辨力。
# 提到 2^19 = 524,288 行后 COPY 需要数秒，比值可达两个数量级。
TIMING_ROWS_POW = 19
TIMING_MARGIN = 3             # 默认算法路径必须比强制 COPY 快至少 3 倍
TIMING_ABS_BUDGET_US = 2_000_000   # 且默认路径必须在 2 秒内完成（"秒级"的字面含义）


def build_timing_case(test_id: str, transition: dict, env: str) -> str:
    """秒级证据：同一转换、同样数据量，比较"默认算法"与"强制 COPY"的耗时。

    这是"秒级修改列类型"唯一可自动化的硬证据：元数据级变更应当比重建表快
    至少一个数量级；如果服务器悄悄退化成重建，比值会掉下来并被这条断言抓住。
    """
    old_type, new_type = transition["old_type"], transition["new_type"]
    suf = id_to_suffix(test_id)
    t_fast, t_slow = "t1_" + suf, "t2_" + suf
    old_def = _build_column_def(old_type, dict(BASELINE), transition)
    new_def = _build_column_def(new_type, dict(BASELINE), transition)
    data = gen_test_data(transition)
    seed = [v for v in data["pre_values"] if v != "NULL"][0]

    lines = []
    lines.append("-- Test Case: %s" % test_id)
    lines.append("-- Timing: default-algorithm vs forced COPY, %d rows" % (2 ** TIMING_ROWS_POW))
    lines.append("-- Type: %s -> %s, Algorithm: default_vs_copy, Expected: SUCCESS" % (old_type, new_type))
    lines.append("-- Transition ID: %s" % transition.get("id", ""))
    lines.append("-- @timing_placeholder@")
    lines.append("DROP TABLE IF EXISTS %s, %s;" % (t_fast, t_slow))
    lines.append("SET SESSION sql_mode = 'STRICT_TRANS_TABLES';")
    for t in (t_fast, t_slow):
        lines.append("CREATE TABLE %s (id INT NOT NULL AUTO_INCREMENT PRIMARY KEY, target %s) ENGINE=InnoDB;"
                     % (t, old_def))
        lines.append("INSERT INTO %s (target) VALUES (%s);" % (t, seed))
        for _i in range(TIMING_ROWS_POW):
            lines.append("INSERT INTO %s (target) SELECT target FROM %s;" % (t, t))
        lines.append("ANALYZE TABLE %s;" % t)

    a_fast = "ALTER TABLE %s MODIFY target %s;" % (t_fast, new_def)
    a_slow = "ALTER TABLE %s MODIFY target %s, ALGORITHM=COPY;" % (t_slow, new_def)
    lines.append("SET @t0 = NOW(6);")
    lines.append(a_fast)
    lines.append("SET @t1 = NOW(6);")
    lines.append("SET @t2 = NOW(6);")
    lines.append(a_slow)
    lines.append("SET @t3 = NOW(6);")
    lines.append(
        "SELECT '%s#FAST_PATH' AS test_id,\n"
        "       IF(TIMESTAMPDIFF(MICROSECOND,@t0,@t1) * %d < TIMESTAMPDIFF(MICROSECOND,@t2,@t3)\n"
        "          AND TIMESTAMPDIFF(MICROSECOND,@t0,@t1) < %d,'PASS','FAIL') AS result,\n"
        "       CONCAT('default_us=',TIMESTAMPDIFF(MICROSECOND,@t0,@t1),"
        "' copy_us=',TIMESTAMPDIFF(MICROSECOND,@t2,@t3),"
        "' ratio=',ROUND(TIMESTAMPDIFF(MICROSECOND,@t2,@t3)/GREATEST(TIMESTAMPDIFF(MICROSECOND,@t0,@t1),1),1),"
        "' need_ratio>%d and default_us<%d') AS mismatch;"
        % (test_id, TIMING_MARGIN, TIMING_ABS_BUDGET_US, TIMING_MARGIN, TIMING_ABS_BUDGET_US))
    lines.append(build_meta_assertion_full(
        test_id, t_fast, "target",
        expected_meta(transition, dict(BASELINE), new_type,
                      overrides={"ordinal_position": 2}), name="META"))
    tag = ("-- @expect alter=SUCCESS build=SUCCESS assertions=2 alter_sha=%s column_type=%s"
           % (alter_sha(a_fast), column_type_of(new_type)))
    return "\n".join(lines).replace("-- @timing_placeholder@", tag)


# ---------------------------------------------------------------- 索引完整性
_B62 = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"


def _b62_fixed(i: int, width: int) -> str:
    """定宽 base62 编码：width=1 也能给出 62 个互不相同的值。

    旧写法 ("v%d" % i).ljust(width,"_")[:width] 在 width=1 时对任何 i 都得到 'v'，
    于是 CHAR(1)/VARCHAR(1) 的唯一索引用例只插得进 1 行 —— 用例"通过"了，
    但唯一约束、索引一致性、CRC 对照全都退化成单行比较，等于没测。
    """
    if width <= 0:
        return ""
    digits = []
    v = max(0, int(i))
    while v and len(digits) < width:
        digits.append(_B62[v % 62])
        v //= 62
    while len(digits) < width:
        digits.append(_B62[0])
    return "".join(reversed(digits))


def unique_values_for(transition: dict, n: int) -> list:
    """为索引完整性用例生成 n 个**互不相同**且落在旧类型值域内的字面量。"""
    cat = transition.get("category", "")
    old = transition["old_type"].upper()
    n = max(2, min(n, 62))
    if cat.startswith("integer"):
        unsigned = "UNSIGNED" in old
        return [str(i if unsigned else i - n // 2) for i in range(n)]
    if cat == "decimal":
        m = _re.match(r"DECIMAL\((\d+),(\d+)\)", old)
        prec = int(m.group(1)) if m else 10
        scale = int(m.group(2)) if m else 0
        cap = min(n, 10 ** min(prec, 6))          # 10^M 个可表示值，取样即可
        out = []
        for i in range(max(2, cap)):
            out.append(("%d.%s" % (i // (10 ** scale), str(i % (10 ** scale)).rjust(scale, "0")))
                       if scale else str(i))
        return out
    if cat == "bit":
        w = int(_re.match(r"BIT\((\d+)\)", old).group(1))
        cap = max(2, min(n, 2 ** min(w, 16)))
        return [str(i) for i in range(cap)]
    if cat in ("binary", "varbinary", "blob"):
        # 必须用真正的十六进制编码：base62 的 g~z / A~Z 不是合法 hex 字符，
        # n>15 时会生成 X'000000000000000g' 这种非法字面量。
        m = _re.match(r"(?:VAR)?BINARY\((\d+)\)", old)
        width = max(1, min(int(m.group(1)) if m else 4, 8))
        hexw = width * 2
        cap = min(n, 16 ** hexw)
        return ["X'%s'" % ("%0*X" % (hexw, i)) for i in range(cap)]
    # char / varchar / text
    m = _re.search(r"\((\d+)\)", old)
    cap = int(m.group(1)) if m else 20
    width = max(1, min(cap, 8))
    return ["'%s'" % _b62_fixed(i, width) for i in range(n)]


def index_def_for(transition: dict, kind: str) -> Tuple[str, str]:
    """按目标列宽度选择整列索引或前缀索引，返回 (索引名, 索引 DDL)。

    InnoDB 单索引键上限 3072 字节：VARCHAR(16381) utf8mb4 = 65,524 字节，
    建整列索引必然 errno 1071。此时改用前缀索引 —— 既保住覆盖，
    也顺带验证"前缀索引在类型变更后是否被正确重建"。
    """
    name = "idx_target" if kind == "SECONDARY" else "uq_target"
    kw = "INDEX" if kind == "SECONDARY" else "UNIQUE INDEX"
    mb = target_index_bytes(transition)
    if mb and mb > INDEX_KEY_LIMIT_BYTES:
        return name, "%s %s (target(64))" % (kw, name)
    return name, "%s %s (target)" % (kw, name)


def build_index_integrity_case(test_id: str, transition: dict, env: str, kind: str) -> str:
    """ALTER 之后复验索引与约束（P1-4）。

    断言集合：
      IDX_PRESENT    索引仍然存在、列与序号正确
      IDX_CONSISTENT FORCE INDEX 与 IGNORE INDEX 的行数一致（索引与表物理一致）
      IDX_SCAN_HASH  索引扫描与全表扫描的有序哈希一致
      CRC_ORACLE     与"用新类型全新建的对照表"逐行哈希一致
      UNIQ_ENFORCED  唯一索引仍然拒绝重复值（负向探针，errno 1062）
      META           列元数据
    """
    old_type, new_type = transition["old_type"], transition["new_type"]
    suf = id_to_suffix(test_id)
    t1, t2 = "t1_" + suf, "t2_" + suf
    idx_name, idx_def = index_def_for(transition, kind)
    old_def = _build_column_def(old_type, dict(BASELINE), transition)
    new_def = _build_column_def(new_type, dict(BASELINE), transition)
    vals = unique_values_for(transition, 32)

    inst_exp, _ie, _r1 = resolve_expectation(transition, "instant", env)
    inplace_exp, inplace_err, _r2 = resolve_expectation(transition, "inplace", env)
    # 目标列在索引里 => INSTANT 不可用；用 INPLACE（不支持则退回 COPY）
    if inplace_exp == "SUCCESS":
        algo_clause, exp, errnos = ", ALGORITHM=INPLACE, LOCK=NONE", "SUCCESS", []
    else:
        algo_clause, exp, errnos = ", ALGORITHM=COPY", "SUCCESS", []

    def hash_expr(tbl):
        return ("(SELECT BIT_XOR(CAST(CRC32(CONCAT_WS(0x7C, id, IFNULL(target,'~N~'))) AS UNSIGNED))"
                " FROM %s)" % tbl)

    lines = []
    lines.append("-- Test Case: %s" % test_id)
    lines.append("-- Index integrity: %s index on target" % kind)
    lines.append("-- Type: %s -> %s, Algorithm: %s, Expected: %s"
                 % (old_type, new_type, "inplace" if algo_clause.startswith(", ALGORITHM=INPLACE") else "copy", exp))
    lines.append("-- Transition ID: %s" % transition.get("id", ""))
    lines.append("-- @idx_placeholder@")
    lines.append("DROP TABLE IF EXISTS %s, %s;" % (t1, t2))
    lines.append("SET SESSION sql_mode = 'STRICT_TRANS_TABLES';")
    # minimal_table（VARCHAR(16381)+ / VARCHAR(65527)+ 这类逼近 65535 行宽的类型）
    # 不能再带 pad 列，否则 CREATE 直接 errno 1118，索引用例一个都跑不起来。
    minimal = bool(transition.get("minimal_table"))
    if minimal:
        create = ("CREATE TABLE %s (\n  id INT NOT NULL AUTO_INCREMENT,\n  target %s,\n"
                  "  PRIMARY KEY (id),\n  %s\n) ENGINE=InnoDB;")
    else:
        create = ("CREATE TABLE %s (\n  id INT NOT NULL AUTO_INCREMENT,\n  target %s,\n"
                  "  pad VARCHAR(20) DEFAULT 'pad',\n  PRIMARY KEY (id),\n  %s\n) ENGINE=InnoDB;")
    lines.append(create % (t1, old_def, idx_def))
    for v in vals:
        lines.append("INSERT INTO %s (target) VALUES (%s);" % (t1, v))
    lines.append("ANALYZE TABLE %s;" % t1)

    alter_stmt = "ALTER TABLE %s MODIFY target %s%s;" % (t1, new_def, algo_clause)
    lines.append("-- ALTER expected %s" % exp)
    lines.append(alter_stmt)

    # 对照表：新类型 + 同样的索引
    lines.append(create % (t2, new_def, idx_def))
    for v in vals:
        lines.append("INSERT INTO %s (target) VALUES (%s);" % (t2, v))
    lines.append("ANALYZE TABLE %s;" % t2)

    n_assert = 0
    # IDX_PRESENT
    lines.append(
        "SELECT '%s#IDX_PRESENT' AS test_id,\n"
        "       IF(COUNT(*)=1,'PASS','FAIL') AS result,\n"
        "       CONCAT('index %s on ',%s,' columns found=',COUNT(*)) AS mismatch\n"
        "FROM information_schema.statistics\n"
        "WHERE table_schema=DATABASE() AND table_name=%s AND index_name=%s AND column_name='target';"
        % (test_id, idx_name, sql_quote(t1), sql_quote(t1), sql_quote(idx_name)))
    n_assert += 1
    # IDX_CONSISTENT
    lines.append(
        "SELECT '%s#IDX_CONSISTENT' AS test_id,\n"
        "       IF((SELECT COUNT(*) FROM %s FORCE INDEX(%s)) = (SELECT COUNT(*) FROM %s IGNORE INDEX(%s)),"
        "'PASS','FAIL') AS result,\n"
        "       CONCAT('force=',(SELECT COUNT(*) FROM %s FORCE INDEX(%s)),"
        "' ignore=',(SELECT COUNT(*) FROM %s IGNORE INDEX(%s))) AS mismatch;"
        % (test_id, t1, idx_name, t1, idx_name, t1, idx_name, t1, idx_name))
    n_assert += 1
    # IDX_SCAN_HASH：走索引的顺序扫描 vs 走主键的顺序扫描，哈希必须一致
    lines.append(
        "SELECT '%s#IDX_SCAN_HASH' AS test_id,\n"
        "       IF((SELECT BIT_XOR(CAST(CRC32(CONCAT_WS(0x7C, id, IFNULL(target,'~N~'))) AS UNSIGNED))\n"
        "             FROM (SELECT id, target FROM %s FORCE INDEX(%s) ORDER BY id) x)\n"
        "          = (SELECT BIT_XOR(CAST(CRC32(CONCAT_WS(0x7C, id, IFNULL(target,'~N~'))) AS UNSIGNED))\n"
        "             FROM (SELECT id, target FROM %s IGNORE INDEX(%s) ORDER BY id) y),"
        "'PASS','FAIL') AS result,\n"
        "       'index-scan hash != table-scan hash' AS mismatch;"
        % (test_id, t1, idx_name, t1, idx_name))
    n_assert += 1
    # CRC_ORACLE
    lines.append(
        "SELECT '%s#CRC_ORACLE' AS test_id,\n"
        "       IF(%s <=> %s,'PASS','FAIL') AS result,\n"
        "       CONCAT('t1=',IFNULL(%s,'NULL'),' t2=',IFNULL(%s,'NULL')) AS mismatch;"
        % (test_id, hash_expr(t1), hash_expr(t2), hash_expr(t1), hash_expr(t2)))
    n_assert += 1
    # META
    lines.append(build_meta_assertion_full(
        test_id, t1, "target",
        expected_meta(transition, dict(BASELINE), new_type,
                      overrides={"ordinal_position": 2}), name="META"))
    n_assert += 1

    probes = []
    if kind == "UNIQUE":
        dup = vals[0]
        probe = "INSERT INTO %s (target) VALUES (%s)" % (t1, dup)
        lines.append("-- 负向探针：唯一约束必须仍然生效（重复值必须被拒 1062）")
        lines.append(probe + ";")
        probes.append("%s=1062" % _probe_sha1(probe))
        n_assert += 0    # runner 合成断言，不计入 SQL 判定行

    tag = ("-- @expect alter=%s%s build=SUCCESS assertions=%d alter_sha=%s column_type=%s index_kind=%s%s"
           % (exp, (" errno=[%s]" % ",".join(str(e) for e in errnos)) if errnos else "",
              n_assert, alter_sha(alter_stmt), column_type_of(new_type), kind,
              (" " + " ".join("neg_probe=%s" % p for p in probes)) if probes else ""))
    return "\n".join(lines).replace("-- @idx_placeholder@", tag)



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
STALE_PRUNED: List[str] = []

GITIGNORE_BEGIN = "# BEGIN auto-generated: 以 .sql.gz 发布的文件，其明文 .sql 不入库"
GITIGNORE_LEGACY_HEADER = "# Large SQL files (compressed versions tracked instead)"
GITIGNORE_END = "# END auto-generated"


def _prune_stale_sql(written: List[str]) -> List[str]:
    """删除 SQL_ALIYUN / SQL_INTERNAL 里本轮没有产出的 .sql / .sql.gz。"""
    keep = {os.path.abspath(p) for p in written}
    removed: List[str] = []
    for d in (SQL_ALIYUN, SQL_INTERNAL):
        if not os.path.isdir(d):
            continue
        for name in sorted(os.listdir(d)):
            if not (name.endswith(".sql") or name.endswith(".sql.gz")):
                continue
            path = os.path.abspath(os.path.join(d, name))
            if path in keep:
                continue
            try:
                os.remove(path)
                removed.append(path)
            except OSError:
                pass
    return removed


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
                                       id_to_suffix(test_id), factor_name, env)
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
    """遍历 24 种真实分区策略 × 每个转换，生成 PTK / PNK 两类用例。

    旧实现遍历 8×8=64 个"组合"，但二级分区类型被丢弃 -> 实际只有 8 种、
    每种重复 8 次，且 SUBPARTITION 覆盖为 0。
    """
    results = []
    for pp_idx, (strategy, _first, _sub) in enumerate(PARTITION_STRATEGIES, start=1):
        for trans in transitions:
            if trans["env"] != env:
                continue
            results.append(_build_partition_test(
                ids.next(SCOPE_PART_KEY, algorithm), trans, algorithm,
                pp_idx, strategy, True, env))
            results.append(_build_partition_test(
                ids.next(SCOPE_PART_NONKEY, algorithm), trans, algorithm,
                pp_idx, strategy, False, env))
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
            for scenario in ["child", "parent", "both", "both_fkc0",
                             "both_drop_fk", "non_fk"]:
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
    if len(case_ids) != len(stmts):
        raise SystemExit(
            "!! %s: 语句块 %d 个但用例头 %d 个 —— 生成器有块没有用例头，"
            "或某个块被错误拼接（例如 '\\n'.join(<str>) 会把字符串按字符炸开）"
            % (filename, len(stmts), len(case_ids)))
    # 粗粒度体积哨兵：VC-08/VC-09 这类上限用例本身就带 65KB 级字面量（约 900KB/用例），
    # 因此阈值放到 4MB；真正抓"字符串被按字符炸开"的是上面的用例头数量校验。
    _oversized = [(i, len(b)) for i, b in enumerate(stmts) if len(b) > 4_000_000]
    if _oversized:
        raise SystemExit("!! %s: %d 个用例体积异常 (>4MB)，示例 %s"
                         % (filename, len(_oversized), _oversized[:3]))
    registry.append({
        "file_no": file_no,
        "file": filename if not filename.endswith(".gz") else filename,
        "dir": os.path.basename(dirpath),
        "title": title,
        "cases": len(case_ids),
        "case_ids": case_ids,
    })
    return stmts


def generate_all(profile_report: Optional[list] = None):
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
    _emit(A, "12_partition_strategies.sql", header_aliyun, "24 种分区策略(含 16 种组合分区) × 全类型",
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
    _emit(I, "29_partition_strategies_enhanced.sql", header_internal, "24 种分区策略(含 16 种组合分区) × 增强类型",
          both_algos(lambda ids, algo: _gen_partition_tests(internal_trans, algo, "internal", ids)),
          registry)

    # ---------------- 清理过期产物 ----------------
    # 文件改名或数量变化后，旧产物若留在目录里会被执行器当成有效用例跑，
    # 造成"跑了已经不存在的覆盖"。这里按本轮实际写入清单做差集清理。
    stale = _prune_stale_sql([p for p, _c, _sz, _g in WRITTEN_FILES])
    global STALE_PRUNED
    STALE_PRUNED = stale
    if stale:
        print("清理过期产物    : %d 个 %s" % (len(stale), [os.path.basename(x) for x in stale]))

    # ---------------- 专项：DDL 语句形态 / 秒级计时 / 索引完整性 ----------------
    def forms(env, trans):
        def build(ids):
            out = []
            for t in trans:
                for form, _desc in DDL_FORMS:
                    out.append(build_ddl_form_case(ids.next(SCOPE_FORM, None), t, env, form))
            return out
        return build

    def timing(env, trans):
        def build(ids):
            # 只对"该环境支持 INSTANT"的转换做秒级差分，并取代表性子集控制耗时
            picked = [t for t in trans
                      if resolve_expectation(t, "instant", env)[0] == "SUCCESS"]
            step = max(1, len(picked) // 8)
            return [build_timing_case(ids.next(SCOPE_TIMING, None), t, env)
                    for t in picked[::step][:8]]
        return build

    def index_integrity(env, trans):
        def build(ids):
            out = []
            for t in trans:
                for kind, _d in INDEX_KINDS:
                    out.append(build_index_integrity_case(ids.next(SCOPE_INDEX, None), t, env, kind))
            return out
        return build

    _emit(A, "30_ddl_forms.sql", header_aliyun,
          "DDL 语句形态 (默认算法 / LOCK=NONE / CHANGE 改名 / COPY 对照组)",
          forms("aliyun", aliyun_trans), registry)
    _emit(A, "32_ddl_timing.sql", header_aliyun,
          "秒级差分计时 (默认算法 vs 强制 COPY, %d 行)" % (2 ** TIMING_ROWS_POW),
          timing("aliyun", aliyun_trans), registry)
    _emit(A, "34_index_integrity.sql", header_aliyun,
          "索引与约束完整性复验 (SECONDARY / UNIQUE)",
          index_integrity("aliyun", aliyun_trans), registry)
    _emit(I, "31_ddl_forms_enhanced.sql", header_internal,
          "DDL 语句形态 (默认算法 / LOCK=NONE / CHANGE 改名 / COPY 对照组)",
          forms("internal", internal_trans), registry)
    _emit(I, "33_ddl_timing_enhanced.sql", header_internal,
          "秒级差分计时 (默认算法 vs 强制 COPY, %d 行)" % (2 ** TIMING_ROWS_POW),
          timing("internal", internal_trans), registry)
    _emit(I, "35_index_integrity_enhanced.sql", header_internal,
          "索引与约束完整性复验 (SECONDARY / UNIQUE)",
          index_integrity("internal", internal_trans), registry)

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
        "stale_pruned": [os.path.basename(x) for x in STALE_PRUNED],
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
    print("")
    print("环境能力画像    : %s" % {e: charvarchar_mode(e) for e in ENV_PROFILES})
    if CHARVARCHAR_MODE_CLI:
        print("  (由 --charvarchar-mode=%s 全局覆盖)" % CHARVARCHAR_MODE_CLI)

    manifest["untracked_in_git"] = verify_git_tracking([p for p, _c, _s, _g in WRITTEN_FILES])
    if manifest["untracked_in_git"]:
        manifest["git_tracking_ok"] = False
        with open(os.path.join(OUTPUT_DIR, "results", "generation_manifest.json"), "w",
                  encoding="utf-8") as f:
            json.dump(manifest, f, ensure_ascii=False, indent=2)
    else:
        manifest["git_tracking_ok"] = True
        print("git 跟踪自检    : 全部产物已入库 ✅")


def _main():
    import argparse
    ap = argparse.ArgumentParser(description="RDS MySQL DDL 测试套件生成器")
    ap.add_argument("--charvarchar-mode", choices=[CROSS_ONLY, SAME_ONLY, ALL_SUPPORTED, NONE_SUPPORTED],
                    help="覆盖所有环境的 CHAR/VARCHAR 同字节桶/跨字节桶支持口径")
    args = ap.parse_args()
    global CHARVARCHAR_MODE_CLI
    CHARVARCHAR_MODE_CLI = args.charvarchar_mode
    generate_all()


if __name__ == "__main__":
    _main()

