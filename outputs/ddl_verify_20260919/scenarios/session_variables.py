#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""需要 SESSION_VARIABLES_ADMIN / SUPER 的会话变量因子（从纯 SQL 矩阵移出）。

为什么要单独做：这三个变量在阿里云 RDS 上 `SET SESSION` 直接 errno 1227
（Access denied; you need SUPER / SYSTEM_VARIABLES_ADMIN / SESSION_VARIABLES_ADMIN）。
放在纯 SQL 套件里，SET 失败后用例照样往下跑 —— **因子根本没生效却报告"通过"**，
是典型的假覆盖。这里先探权限：无权限就明确 SKIP 并给出 errno，有权限才真正验证。

覆盖：
  V1 sql_generate_invisible_primary_key=ON + 无显式主键  -> 必须自动生成不可见主键
  V2 sql_require_primary_key=ON       + 无显式主键      -> 建表必须被拒(3750)
  V3 innodb_strict_mode=OFF           + 行宽超限         -> 从报错降级为告警，建表成功
  V4 对照：同样三条在权限可用/不可用下的差异都如实记录

用法：
  python3 scenarios/session_variables.py --env aliyun
  python3 scenarios/session_variables.py --env local
"""
import os
import sys
import json
import argparse
import configparser
from datetime import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)

import pymysql  # noqa: E402

RESULTS = []
T = "s_sessvar"


def record(name, passed, detail=""):
    status = "PASS" if passed is True else ("SKIP" if passed == "SKIP" else "FAIL")
    RESULTS.append({"check": name, "result": status, "detail": str(detail)[:600]})
    print("    %s %-46s %s" % ({"PASS": "✓", "FAIL": "✗", "SKIP": "○"}[status],
                               name, str(detail)[:190]), flush=True)


def q(conn, sql, args=None):
    with conn.cursor() as cur:
        cur.execute(sql, args)
        if cur.description:
            cols = [d[0].lower() for d in cur.description]
            return [dict(zip(cols, r)) for r in cur.fetchall()]
        return None


def one(conn, sql, args=None):
    r = q(conn, sql, args)
    return list(r[0].values())[0] if r else None


def try_sql(conn, sql):
    try:
        q(conn, sql)
        return None
    except Exception as e:
        return (e.args[0], str(e.args[1])[:160])


def connect(cfg):
    return pymysql.connect(host=cfg["host"], port=int(cfg.get("port", 3306)),
                           user=cfg["user"], password=cfg.get("password") or "",
                           database=cfg.get("database", "ddl_test"), charset="utf8mb4",
                           autocommit=True, connect_timeout=15, read_timeout=300)


def can_set(conn, var, value):
    err = try_sql(conn, "SET SESSION %s=%s" % (var, value))
    if err is None:
        cur = one(conn, "SELECT @@session.%s" % var)
        return True, cur
    return False, err


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--env", default="aliyun")
    ap.add_argument("--config", default=os.path.join(ROOT, "config.ini"))
    ap.add_argument("--out", default=os.path.join(ROOT, "results", "session_variables.json"))
    args = ap.parse_args()

    cp = configparser.ConfigParser()
    cp.read(args.config)
    if args.env not in cp:
        print("config 里没有 [%s]" % args.env)
        return 2
    c = cp[args.env]
    cfg = {"host": c.get("host"), "port": c.get("port", "3306"), "user": c.get("user"),
           "password": os.environ.get("MYSQL_PWD") or c.get("password"),
           "database": c.get("database", "ddl_test")}
    conn = connect(cfg)
    print("目标 %s:%s version=%s" % (cfg["host"], cfg["port"], one(conn, "SELECT VERSION()")))
    q(conn, "DROP TABLE IF EXISTS %s" % T)

    # ---------------- V1 GIPK ----------------
    ok, info = can_set(conn, "sql_generate_invisible_primary_key", "ON")
    if not ok:
        record("V1 GIPK: SET SESSION 权限", "SKIP", "errno=%s %s" % info)
    else:
        record("V1 GIPK: SET SESSION 生效", one(conn, "SELECT @@session.sql_generate_invisible_primary_key") == 1,
               "@@session=%s" % one(conn, "SELECT @@session.sql_generate_invisible_primary_key"))
        err = try_sql(conn, "CREATE TABLE %s (a INT, b VARCHAR(10)) ENGINE=InnoDB" % T)
        record("V1 GIPK: 无显式主键建表成功", err is None, err)
        cols = [r["column_name"] for r in (q(conn,
                "SELECT column_name FROM information_schema.columns WHERE table_schema=DATABASE() "
                "AND table_name=%s ORDER BY ordinal_position", (T,)) or [])]
        record("V1 GIPK: 自动生成了不可见主键列", "my_row_id" in cols, cols)
        extra = {r["column_name"]: r["extra"] for r in (q(conn,
                 "SELECT column_name, extra FROM information_schema.columns WHERE table_schema=DATABASE() "
                 "AND table_name=%s", (T,)) or [])}
        record("V1 GIPK: 该列为 auto_increment", "auto_increment" in str(extra.get("my_row_id", "")), extra)
        pk = q(conn, "SELECT column_name FROM information_schema.key_column_usage "
                     "WHERE table_schema=DATABASE() AND table_name=%s AND constraint_name='PRIMARY'", (T,))
        record("V1 GIPK: PRIMARY KEY 建在该列上", bool(pk), pk)
        # 差分断言（与引擎能力无关）：有 GIPK 与无 GIPK 时，同一条 ALTER 的结果必须一致。
        # 直接断言"INSTANT 必须成功"是错的 —— 那是 RDS 增强特性，社区版本来就 1845。
        alter = "ALTER TABLE {} MODIFY b VARCHAR(20), ALGORITHM=INSTANT".format(T)
        err_with = try_sql(conn, alter)
        q(conn, "DROP TABLE IF EXISTS %s" % T)
        q(conn, "SET SESSION sql_generate_invisible_primary_key=OFF")
        err_wo = try_sql(conn, "CREATE TABLE %s (a INT PRIMARY KEY, b VARCHAR(10)) ENGINE=InnoDB" % T)
        err_wo = err_wo or try_sql(conn, alter)
        same = (err_with is None) == (err_wo is None) and \
               (err_with or (0,))[0] == (err_wo or (0,))[0]
        record("V1 GIPK: 改列类型的结果与无 GIPK 时一致（差分）", same,
               "with_gipk=%s without_gipk=%s" % (err_with, err_wo))
        q(conn, "SET SESSION sql_generate_invisible_primary_key=OFF")
        q(conn, "DROP TABLE IF EXISTS %s" % T)

    # ---------------- V2 sql_require_primary_key ----------------
    ok, info = can_set(conn, "sql_require_primary_key", "ON")
    if not ok:
        record("V2 require_pk: SET SESSION 权限", "SKIP", "errno=%s %s" % info)
    else:
        err = try_sql(conn, "CREATE TABLE %s (a INT, b VARCHAR(10)) ENGINE=InnoDB" % T)
        record("V2 require_pk: 无主键建表被拒(3750)", err is not None and err[0] == 3750, err)
        err2 = try_sql(conn, "CREATE TABLE %s (a INT PRIMARY KEY, b VARCHAR(10)) ENGINE=InnoDB" % T)
        record("V2 require_pk: 有主键建表成功", err2 is None, err2)
        err3 = try_sql(conn, "ALTER TABLE %s MODIFY b VARCHAR(20), ALGORITHM=INPLACE" % T)
        record("V2 require_pk: 改列类型不受影响", err3 is None, err3)
        q(conn, "SET SESSION sql_require_primary_key=OFF")
        q(conn, "DROP TABLE IF EXISTS %s" % T)

    # ---------------- V3 innodb_strict_mode ----------------
    ok, info = can_set(conn, "innodb_strict_mode", "OFF")
    if not ok:
        record("V3 strict_off: SET SESSION 权限", "SKIP", "errno=%s %s" % info)
    else:
        # innodb_strict_mode 管的是 InnoDB 自己的**半页(8126 字节)内联限制**，
        # 不是 server 级 65535 行宽上限 —— 后者两种模式都报 1118（实测）。
        halfpage = ("CREATE TABLE %s (id INT PRIMARY KEY, %s) ENGINE=InnoDB ROW_FORMAT=COMPACT"
                    % (T, ", ".join("c%d VARCHAR(255) CHARACTER SET utf8mb4" % i for i in range(40))))
        server_limit = ("CREATE TABLE %s (a VARCHAR(65520) CHARACTER SET latin1, "
                        "b VARCHAR(100) CHARACTER SET latin1) ENGINE=InnoDB ROW_FORMAT=COMPACT" % T)

        q(conn, "SET SESSION innodb_strict_mode=ON")
        err_on = try_sql(conn, halfpage)
        record("V3 strict=ON: 内联超半页(>8126)报错 1118", err_on is not None and err_on[0] == 1118, err_on)
        q(conn, "DROP TABLE IF EXISTS %s" % T)
        q(conn, "SET SESSION innodb_strict_mode=OFF")
        err_off = try_sql(conn, halfpage)
        record("V3 strict=OFF: 同样的表被允许（降级为告警）", err_off is None, err_off)
        exists = one(conn, "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema=DATABASE() "
                           "AND table_name=%s", (T,))
        record("V3 strict=OFF: 表确实建出来了", exists == 1, "exists=%s" % exists)
        q(conn, "DROP TABLE IF EXISTS %s" % T)
        # 对照：server 级 65535 限制不受 innodb_strict_mode 影响
        err_srv_off = try_sql(conn, server_limit)
        record("V3 对照: server 级 65535 限制不受 strict_mode 影响",
               err_srv_off is not None and err_srv_off[0] == 1118, err_srv_off)
        q(conn, "DROP TABLE IF EXISTS %s" % T)
        q(conn, "SET SESSION innodb_strict_mode=ON")
        err_srv_on = try_sql(conn, server_limit)
        record("V3 对照: strict=ON 时同样报 1118", err_srv_on is not None and err_srv_on[0] == 1118,
               err_srv_on)
        q(conn, "DROP TABLE IF EXISTS %s" % T)
        q(conn, "SET SESSION innodb_strict_mode=DEFAULT")
        q(conn, "DROP TABLE IF EXISTS %s" % T)

    q(conn, "DROP TABLE IF EXISTS %s" % T)
    conn.close()
    n = {k: sum(1 for r in RESULTS if r["result"] == k) for k in ("PASS", "FAIL", "SKIP")}
    print("\n" + "=" * 78)
    print("会话变量因子专项: PASS=%d FAIL=%d SKIP=%d (共 %d 项)" % (n["PASS"], n["FAIL"], n["SKIP"], len(RESULTS)))
    print("=" * 78)
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as fh:
        json.dump({"env": args.env, "finished_at": datetime.now().isoformat(timespec="seconds"),
                   "summary": n, "checks": RESULTS}, fh, ensure_ascii=False, indent=1)
    print("结果写入 %s" % args.out)
    return 1 if n["FAIL"] else 0


if __name__ == "__main__":
    sys.exit(main())
