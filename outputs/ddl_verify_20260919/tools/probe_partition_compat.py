#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""实测"分区策略 × 目标列类型"兼容性矩阵（P0-9 / P0-5）。

为什么需要它：
  旧生成器里的 PK_COMPAT 是**猜的**，而且 _build_single_partition() 的分区界是
  硬编码整数字面量 (100/200/300)：对 TINYINT(上限127) 越界、对 VARCHAR 类型不符，
  实测 errno 1654 "Partition column values of incorrect type"。
  本脚本按类型生成分区定义，逐个 CREATE 探测，得到可信矩阵。

用法:
  python3 tools/probe_partition_compat.py --env aliyun       # 探 RDS
  python3 tools/probe_partition_compat.py --env local        # 探本机社区版做对照
  输出: tools/partition_compat_<env>.json

只在授权测试实例的 ddl_test 库里建/删 probe_pt_* 临时表，跑完自动清理。
"""
import os
import sys
import json
import argparse
import configparser

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)

import pymysql  # noqa: E402

# ---------------------------------------------------------------- 探测用列类型
PROBE_TYPES = [
    # (category, type_def, wider_type_def, 代表数据值[必须落在 LIST 分组里])
    ("integer_signed",   "TINYINT",          "SMALLINT",          ["-1", "0", "5"]),
    ("integer_signed",   "SMALLINT",         "INT",               ["-1", "0", "5"]),
    ("integer_signed",   "INT",              "BIGINT",            ["-1", "0", "5"]),
    ("integer_signed",   "BIGINT",           "DECIMAL(20,0)",     ["-1", "0", "5"]),
    ("integer_unsigned", "TINYINT UNSIGNED", "SMALLINT UNSIGNED", ["0", "3", "7"]),
    ("integer_unsigned", "INT UNSIGNED",     "BIGINT UNSIGNED",   ["0", "3", "7"]),
    ("integer_unsigned", "BIGINT UNSIGNED",  "DECIMAL(20,0) UNSIGNED", ["0", "3", "7"]),
    ("char",             "CHAR(63) CHARACTER SET utf8mb4",  "CHAR(64) CHARACTER SET utf8mb4",  ["'a'", "'c'", "'e'"]),
    ("char",             "CHAR(254) CHARACTER SET latin1",  "CHAR(255) CHARACTER SET latin1",  ["'a'", "'c'", "'e'"]),
    ("varchar",          "VARCHAR(63) CHARACTER SET utf8mb4", "VARCHAR(64) CHARACTER SET utf8mb4", ["'a'", "'c'", "'e'"]),
    ("varchar",          "VARCHAR(254) CHARACTER SET latin1", "VARCHAR(255) CHARACTER SET latin1", ["'a'", "'c'", "'e'"]),
    ("binary",           "BINARY(20)",       "BINARY(40)",        ["X'00'", "X'02'", "X'04'"]),
    ("varbinary",        "VARBINARY(20)",    "VARBINARY(40)",     ["X'00'", "X'02'", "X'04'"]),
    ("decimal",          "DECIMAL(10,2)",    "DECIMAL(12,2)",     ["0", "2", "4"]),
    ("text",             "TEXT CHARACTER SET utf8mb4", "MEDIUMTEXT CHARACTER SET utf8mb4", ["'a'", "'c'", "'e'"]),
    ("blob",             "BLOB",             "MEDIUMBLOB",        ["X'00'", "X'02'", "X'04'"]),
    ("bit",              "BIT(8)",           "BIT(16)",           ["0", "1", "2"]),
]

# 类型感知的分区界 / LIST 取值（按 category 分派）
INT_BOUNDS = ("0", "64")
STR_BOUNDS = ("''", "'m'")
BIN_BOUNDS = ("X'00'", "X'80'")
DEC_BOUNDS = ("0", "64")
# BIT 是整数语义类型：RANGE/HASH 的界必须用整数字面量（1697），
# 且 bit 字面量 b'..' 只能含 0/1 —— 上一版写成 b'2' 直接 1064 语法错。
BIT_BOUNDS = ("0", "64")

LIST_INT_S = [("-1", "0", "1"), ("2", "3", "4"), ("5", "6", "7")]
LIST_INT_U = [("0", "1", "2"), ("3", "4", "5"), ("6", "7", "8")]
LIST_STR = [("''", "'a'", "'b'"), ("'c'", "'d'"), ("'e'", "'f'")]
LIST_BIN = [("X'00'", "X'01'"), ("X'02'", "X'03'"), ("X'04'", "X'05'")]
LIST_DEC = [("0", "1"), ("2", "3"), ("4", "5")]
LIST_BIT = [("0", "1"), ("2", "3"), ("4", "5")]


def bounds_for(category):
    if category.startswith("integer"):
        return INT_BOUNDS
    if category in ("char", "varchar"):
        return STR_BOUNDS
    if category in ("binary", "varbinary"):
        return BIN_BOUNDS
    if category == "decimal":
        return DEC_BOUNDS
    if category == "bit":
        return BIT_BOUNDS
    return STR_BOUNDS


def list_groups_for(category):
    if category == "integer_signed":
        return LIST_INT_S
    if category == "integer_unsigned":
        return LIST_INT_U
    if category in ("char", "varchar", "text"):
        return LIST_STR
    if category in ("binary", "varbinary", "blob"):
        return LIST_BIN
    if category == "decimal":
        return LIST_DEC
    if category == "bit":
        return LIST_BIT
    return LIST_STR


FIRST_LEVEL = ["RANGE", "RANGE COLUMNS", "LIST", "LIST COLUMNS",
               "HASH", "LINEAR HASH", "KEY", "LINEAR KEY"]
SUB_LEVEL = ["HASH", "LINEAR HASH", "KEY", "LINEAR KEY"]


def first_clause(strategy, category, with_sub=None):
    """构造分区子句。

    MySQL 语法要求 `SUBPARTITION BY ...` 必须出现在**分区定义列表之前**：
        PARTITION BY RANGE (c)
        SUBPARTITION BY HASH (c) SUBPARTITIONS 2
        (PARTITION p0 VALUES LESS THAN (0), ...);
    写反了会报 errno 1064 语法错误 —— 上一版探测脚本就栽在这里，
    导致 16 个组合分区策略被误判为"不兼容"。
    """
    b = bounds_for(category)
    head = ""
    body = ""
    if strategy == "RANGE":
        head = "PARTITION BY RANGE (target)"
        body = ("(\n  PARTITION p0 VALUES LESS THAN (%s),\n"
                "  PARTITION p1 VALUES LESS THAN (%s),\n"
                "  PARTITION p2 VALUES LESS THAN MAXVALUE)" % (b[0], b[1]))
    elif strategy == "RANGE COLUMNS":
        head = "PARTITION BY RANGE COLUMNS(target)"
        body = ("(\n  PARTITION p0 VALUES LESS THAN (%s),\n"
                "  PARTITION p1 VALUES LESS THAN (%s),\n"
                "  PARTITION p2 VALUES LESS THAN MAXVALUE)" % (b[0], b[1]))
    elif strategy in ("LIST", "LIST COLUMNS"):
        head = "PARTITION BY %s(target)" % strategy
        parts = ["  PARTITION p%d VALUES IN (%s)" % (i, ", ".join(grp))
                 for i, grp in enumerate(list_groups_for(category))]
        body = "(\n%s)" % ",\n".join(parts)
    elif strategy in ("HASH", "LINEAR HASH", "KEY", "LINEAR KEY"):
        return "%s (target) PARTITIONS 4" % ("PARTITION BY " + strategy)
    else:
        raise ValueError(strategy)
    if with_sub:
        head += "\nSUBPARTITION BY %s (target) SUBPARTITIONS 2" % with_sub
    return head + "\n" + body


def probe(conn, typedef, wider, category, strategy, sub=None):
    """返回该 (类型, 策略) 组合的建表 / 插入 / 分区键改类型 三步实测结果。"""
    cur = conn.cursor()
    cur.execute("DROP TABLE IF EXISTS probe_pt")
    clause = first_clause(strategy, category, sub)
    sql = ("CREATE TABLE probe_pt (id INT NOT NULL AUTO_INCREMENT, target %s, "
           "pad VARCHAR(20) DEFAULT 'pad', PRIMARY KEY (id, target)) "
           "ENGINE=InnoDB\n%s" % (typedef, clause))
    out = {"sql_clause": clause.replace("\n", " ")}
    try:
        cur.execute(sql)
    except Exception as e:
        out.update({"build": False, "build_errno": e.args[0],
                    "build_msg": str(e.args[1])[:160]})
        return out
    out["build"] = True

    vals = list_groups_for(category)
    ins_ok, ins_errno, ins_msg, ins_sql = True, None, "", ""
    try:
        for grp in vals:
            ins_sql = "INSERT INTO probe_pt (target) VALUES (%s)" % grp[0]
            cur.execute(ins_sql)
    except Exception as e:
        ins_ok, ins_errno, ins_msg = False, e.args[0], str(e.args[1])[:160]
    out.update({"insert": ins_ok, "insert_errno": ins_errno, "insert_msg": ins_msg,
                "insert_sql": ins_sql})

    # 分区键列**真的改类型**（旧探测用同类型 = no-op，测不出 errno）
    alt = {}
    for algo in ("instant", "inplace", "copy"):
        asql = "ALTER TABLE probe_pt MODIFY target %s, ALGORITHM=%s" % (wider, algo.upper())
        try:
            cur.execute(asql)
            alt[algo] = {"ok": True}
            # 改成功后恢复原类型，保证三种算法探测条件一致
            try:
                cur.execute("ALTER TABLE probe_pt MODIFY target %s, ALGORITHM=COPY" % typedef)
            except Exception:
                pass
        except Exception as e:
            alt[algo] = {"ok": False, "errno": e.args[0], "msg": str(e.args[1])[:160]}
    out["alter"] = alt
    cur.execute("DROP TABLE IF EXISTS probe_pt")
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--env", default="aliyun")
    ap.add_argument("--config", default=os.path.join(ROOT, "config.ini"))
    ap.add_argument("--out", default=None)
    args = ap.parse_args()

    cfg = configparser.ConfigParser()
    cfg.read(args.config)
    if args.env not in cfg:
        print("config 里没有 [%s]" % args.env)
        return 2
    c = cfg[args.env]
    conn = pymysql.connect(host=c.get("host"), port=int(c.get("port", 3306)),
                           user=c.get("user"), password=os.environ.get("MYSQL_PWD") or c.get("password"),
                           database=c.get("database", "ddl_test"), charset="utf8mb4", autocommit=True)
    cur = conn.cursor()
    cur.execute("SELECT VERSION()")
    version = cur.fetchone()[0]
    print("探测目标: %s:%s  MySQL %s" % (c.get("host"), c.get("port"), version))

    results = {"env": args.env, "version": version, "matrix": {}, "types": {}}
    for category, typedef, wider, _vals in PROBE_TYPES:
        key = typedef
        results["types"][key] = {"category": category, "wider": wider}
        per_strategy = {}
        for strategy in FIRST_LEVEL:
            per_strategy[strategy] = probe(conn, typedef, wider, category, strategy)
            # 组合分区：仅 RANGE*/LIST* 一级允许 SUBPARTITION
            if strategy in ("RANGE", "RANGE COLUMNS", "LIST", "LIST COLUMNS"):
                for sub in SUB_LEVEL:
                    per_strategy["%s+SUB %s" % (strategy, sub)] = probe(
                        conn, typedef, wider, category, strategy, sub)
        results["matrix"][key] = per_strategy
        okc = sum(1 for v in per_strategy.values() if v.get("build"))
        print("  %-40s %-16s 可建 %2d/%2d" % (typedef, category, okc, len(per_strategy)))

    out = args.out or os.path.join(HERE, "partition_compat_%s.json" % args.env)
    with open(out, "w", encoding="utf-8") as fh:
        json.dump(results, fh, ensure_ascii=False, indent=1)
    print("\n写出: %s" % out)
    conn.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
