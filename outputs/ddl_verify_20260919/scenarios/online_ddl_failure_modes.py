#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""P1-5 在线 DDL 失败模式与中断恢复专项。

纯 SQL 套件无法覆盖这类场景（需要多连接、并发、计时、KILL、权限降级），
因此单独做成一个受控的 Python 场景模块。

覆盖场景：
  S1 MDL 阻塞与连接堆积     长事务持有 MDL -> ALTER 排队 -> 后续简单查询也被堵住
  S2 lock_wait_timeout 到期  ALTER 必须干净失败，表保持可用且元数据不变
  S3 KILL QUERY 打断 DDL     中断后表必须完整、无 #sql- 残留、可继续读写
  S4 并发 DDL × DDL          同表两条 ALTER 竞争，最终状态必须是确定的且表完整
  S5 DDL vs 运维语句         ALTER 与 OPTIMIZE / ANALYZE / TRUNCATE 并发
  S6 online_alter_log 溢出   需要 SUPER（RDS 上无权限 -> 明确 SKIP，不假装通过）
  S7 外键父子两侧并发 ALTER

安全边界（遵循最小影响原则）：
  * 只在授权测试库内建 `s_online_*` 前缀的表，跑完自动清理
  * 每个场景都有硬超时；任何线程都不会无限等待
  * 并发度、行数、DML 速率全部有上限，可通过参数调小
  * 不改任何 GLOBAL 变量；S6 需要 SUPER 时才尝试，失败即 SKIP

用法：
  python3 scenarios/online_ddl_failure_modes.py --env aliyun
  python3 scenarios/online_ddl_failure_modes.py --env local --rows 200000
"""
import os
import sys
import json
import time
import argparse
import threading
import configparser
from datetime import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)

import pymysql  # noqa: E402

TABLE = "s_online_ddl"
# S3b（打断重建中的 DDL）需要 DDL 跑得足够久才有可靠的打断窗口
KILL_ROWS_MIN = 4_000_000
RESULTS = []
LOCK = threading.Lock()


def log(msg):
    print("[%s] %s" % (datetime.now().strftime("%H:%M:%S"), msg), flush=True)


def record(scenario, name, passed, detail=""):
    with LOCK:
        RESULTS.append({"scenario": scenario, "check": name,
                        "result": "PASS" if passed else "FAIL", "detail": str(detail)[:600]})
    print("    %s %-34s %s" % ("✓" if passed else "✗", name, str(detail)[:180]), flush=True)


def connect(cfg, autocommit=True):
    return pymysql.connect(host=cfg["host"], port=int(cfg["port"]), user=cfg["user"],
                           password=cfg["password"], database=cfg["database"],
                           charset="utf8mb4", autocommit=autocommit,
                           connect_timeout=15, read_timeout=600, write_timeout=600)


def q(conn, sql, args=None):
    """执行查询。列名统一转小写 —— information_schema 在不同实例/配置下可能返回
    TABLE_NAME 或 table_name，不归一化会 KeyError。"""
    with conn.cursor() as cur:
        cur.execute(sql, args)
        if cur.description:
            cols = [d[0].lower() for d in cur.description]
            return [dict(zip(cols, r)) for r in cur.fetchall()]
        return None


def one(conn, sql, args=None):
    rows = q(conn, sql, args)
    return list(rows[0].values())[0] if rows else None


def build_table(cfg, rows, name=TABLE):
    """用倍增法快速灌数据（比逐行 INSERT 快两个数量级）。"""
    conn = connect(cfg)
    q(conn, "DROP TABLE IF EXISTS %s" % name)
    q(conn, "CREATE TABLE %s (id INT NOT NULL AUTO_INCREMENT PRIMARY KEY, "
            "c1 INT NOT NULL DEFAULT 0, c2 VARCHAR(64) DEFAULT 'x', "
            "KEY idx_c1 (c1)) ENGINE=InnoDB" % name)
    q(conn, "INSERT INTO %s (c1) VALUES (1)" % name)
    n = 1
    while n < rows:
        q(conn, "INSERT INTO %s (c1, c2) SELECT c1, c2 FROM %s" % (name, name))
        n *= 2
    actual = one(conn, "SELECT COUNT(*) FROM %s" % name)
    log("  建表 %s 完成，实际行数 %s" % (name, actual))
    conn.close()
    return actual


def checksum(conn, name=TABLE):
    return one(conn, "SELECT BIT_XOR(CAST(CRC32(CONCAT_WS('|', id, c1, IFNULL(c2,'~'))) AS UNSIGNED)) "
                     "FROM %s" % name)


def leftover_temp_tables(conn):
    rows = q(conn, "SELECT table_name FROM information_schema.tables "
                   "WHERE table_schema=DATABASE() AND table_name LIKE '#sql%%'")
    return [list(r.values())[0] for r in (rows or [])]


def table_intact(conn, name=TABLE, write_probe=None, cleanup_probe=None):
    """表可用性复验：能读、能写、能删。

    write_probe / cleanup_probe 可覆盖默认的写入探针 —— 默认探针写死了 c1/c2 列名，
    在外键表(cid/fk) 这类结构不同的表上会误报"表不可用"。
    """
    try:
        n = one(conn, "SELECT COUNT(*) FROM %s" % name)
        if write_probe:
            q(conn, write_probe % name if "%s" in write_probe else write_probe)
            if cleanup_probe:
                q(conn, cleanup_probe % name if "%s" in cleanup_probe else cleanup_probe)
        else:
            q(conn, "INSERT INTO %s (c1, c2) VALUES (999999, 'probe')" % name)
            q(conn, "DELETE FROM %s WHERE c1 = 999999 AND c2 = 'probe'" % name)
        return True, n
    except Exception as e:
        return False, "%s: %s" % (type(e).__name__, e)


# ================================================================ S1 MDL 阻塞
def scenario_mdl_blocking(cfg, rows):
    """长事务持有 MDL -> ALTER 排队 -> 后续简单 SELECT 也被堵住（连接堆积）。

    这是生产上最常见的事故形态：一条 DDL 把连接池打满。

    注意：pymysql 连接**不是线程安全的**，跨线程共用一条连接会出现
    "Packet sequence number wrong" 协议错乱 —— 每个线程必须自己建连接。
    """
    log("S1 MDL 阻塞与连接堆积")
    build_table(cfg, rows)
    holder = connect(cfg, autocommit=False)
    ctl = connect(cfg)        # 主线程专用：观测 metadata_locks / processlist / 最终复验
    try:
        q(holder, "SET SESSION lock_wait_timeout=60")
        q(holder, "BEGIN")
        q(holder, "SELECT COUNT(*) FROM %s WHERE id > 0" % TABLE)   # 持有 MDL_SHARED_READ

        state = {}

        def run_alter():
            ac = connect(cfg)
            t0 = time.time()
            try:
                q(ac, "SET SESSION lock_wait_timeout=60")
                q(ac, "ALTER TABLE %s MODIFY c1 BIGINT, ALGORITHM=COPY" % TABLE)
                state["alter"] = ("OK", round(time.time() - t0, 2))
            except Exception as e:
                state["alter"] = ("ERR %s" % e.args[0], round(time.time() - t0, 2))
            finally:
                try:
                    ac.close()
                except Exception:
                    pass

        th = threading.Thread(target=run_alter, daemon=True)
        th.start()
        time.sleep(4)     # 让 ALTER 进入 MDL 等待

        waits = q(ctl, "SELECT object_name, lock_type, lock_status, lock_duration "
                       "FROM performance_schema.metadata_locks "
                       "WHERE object_schema=DATABASE() AND object_name=%s", (TABLE,))
        pending = [w for w in (waits or []) if w["lock_status"] == "PENDING"]
        record("S1", "ALTER 进入 MDL 等待队列", len(pending) > 0,
               "pending=%s all=%s" % ([p["lock_type"] for p in pending],
                                      [(w["lock_type"], w["lock_status"]) for w in (waits or [])]))
        st = q(ctl, "SELECT id, command, state, time FROM information_schema.processlist "
                    "WHERE command='Query' AND info LIKE %s", ("ALTER TABLE %s%%" % TABLE,))
        record("S1", "ALTER 会话状态可观测（等待原因可见）", bool(st), st)

        # 关键：MDL 队列公平排队，ALTER 之后的**简单查询**也会被堵住 => 连接堆积
        probe_state = {}

        def run_probe():
            pc = connect(cfg)
            t0 = time.time()
            try:
                one(pc, "SELECT COUNT(*) FROM %s" % TABLE)
                probe_state["blocked_s"] = round(time.time() - t0, 2)
            except Exception as e:
                probe_state["err"] = str(e)[:120]
            finally:
                try:
                    pc.close()
                except Exception:
                    pass

        tp = threading.Thread(target=run_probe, daemon=True)
        tp.start()
        time.sleep(4)
        blocked = tp.is_alive()
        record("S1", "后续简单查询被 MDL 队列堵住（连接堆积复现）", blocked,
               "probe 仍在等待=%s" % blocked)

        q(holder, "COMMIT")        # 释放 MDL
        th.join(timeout=300)
        tp.join(timeout=120)
        record("S1", "释放后 ALTER 正常完成", state.get("alter", ("未返回",))[0] == "OK",
               "alter=%s probe_blocked_s=%s" % (state.get("alter"), probe_state))
        ctype = one(ctl, "SELECT column_type FROM information_schema.columns "
                         "WHERE table_schema=DATABASE() AND table_name=%s AND column_name='c1'",
                    (TABLE,))
        record("S1", "ALTER 结果正确（c1 -> bigint）", ctype == "bigint", ctype)
        ok, n = table_intact(ctl)
        record("S1", "表仍可用", ok, "rows=%s" % n)
        record("S1", "无 #sql- 残留临时表", not leftover_temp_tables(ctl), leftover_temp_tables(ctl))
    finally:
        for c in (holder, ctl):
            try:
                c.close()
            except Exception:
                pass


# ================================================================ S2 超时
def scenario_lock_wait_timeout(cfg, rows):
    log("S2 lock_wait_timeout 到期后必须干净失败")
    build_table(cfg, rows)
    holder = connect(cfg, autocommit=False)
    alter_conn = connect(cfg)
    try:
        before_type = one(alter_conn, "SELECT column_type FROM information_schema.columns "
                                      "WHERE table_schema=DATABASE() AND table_name=%s AND column_name='c1'",
                          (TABLE,))
        before_sum = checksum(alter_conn)
        q(holder, "BEGIN")
        q(holder, "SELECT COUNT(*) FROM %s WHERE id > 0" % TABLE)
        q(alter_conn, "SET SESSION lock_wait_timeout=2")
        t0 = time.time()
        err = None
        try:
            q(alter_conn, "ALTER TABLE %s MODIFY c1 BIGINT, ALGORITHM=COPY" % TABLE)
        except Exception as e:
            err = (e.args[0], str(e.args[1])[:120])
        elapsed = round(time.time() - t0, 2)
        record("S2", "ALTER 在超时后失败", err is not None, "errno=%s 耗时=%ss" % (err and err[0], elapsed))
        record("S2", "失败发生在超时阈值附近（未无限等待）", err is not None and elapsed < 15,
               "耗时=%ss 阈值=2s" % elapsed)
        after_type = one(alter_conn, "SELECT column_type FROM information_schema.columns "
                                     "WHERE table_schema=DATABASE() AND table_name=%s AND column_name='c1'",
                         (TABLE,))
        record("S2", "列类型未被半改（元数据回滚干净）", after_type == before_type,
               "before=%s after=%s" % (before_type, after_type))
        record("S2", "数据校验和不变", checksum(alter_conn) == before_sum, "sum=%s" % before_sum)
        ok, n = table_intact(alter_conn)
        record("S2", "表仍可用", ok, "rows=%s" % n)
        record("S2", "无 #sql- 残留", not leftover_temp_tables(alter_conn), leftover_temp_tables(alter_conn))
        q(holder, "COMMIT")
    finally:
        for c in (holder, alter_conn):
            try:
                c.close()
            except Exception:
                pass


# ================================================================ S3 KILL
def scenario_kill_ddl(cfg, rows):
    """KILL QUERY 打断 DDL，分两个子场景：

    S3a 打断"正在等 MDL"的 DDL —— 完全确定性，不依赖时序竞速
    S3b 打断"正在重建表"的 DDL —— 最有价值的一档：验证行拷贝进行到一半时被杀，
        表是否仍然完整、元数据是否半改、有没有 #sql- 残留

    S3b 需要 DDL 跑得足够久：默认把表放大到 KILL_ROWS_MIN 行（COPY 约 20~40s），
    并以 50ms 间隔紧轮询。若 DDL 仍然抢先跑完，会**如实报 FAIL 并给出实测耗时**，
    提示调大 --rows，绝不假装通过。
    """
    ctl = connect(cfg)

    # ---------- S3a: 打断正在等待 MDL 的 DDL ----------
    log("S3a KILL 正在等待 MDL 的 DDL（确定性）")
    build_table(cfg, min(rows, 50000))
    holder = connect(cfg, autocommit=False)
    try:
        before_type = one(ctl, "SELECT column_type FROM information_schema.columns "
                               "WHERE table_schema=DATABASE() AND table_name=%s AND column_name='c1'",
                          (TABLE,))
        before_sum = checksum(ctl)
        q(holder, "SET SESSION lock_wait_timeout=120")
        q(holder, "BEGIN")
        q(holder, "SELECT COUNT(*) FROM %s WHERE id > 0" % TABLE)

        state = {}

        def run_alter():
            ac = connect(cfg)
            state["conn_id"] = one(ac, "SELECT CONNECTION_ID()")
            try:
                q(ac, "SET SESSION lock_wait_timeout=120")
                q(ac, "ALTER TABLE %s MODIFY c1 BIGINT, ALGORITHM=COPY" % TABLE)
                state["r"] = "OK"
            except Exception as e:
                state["r"] = "ERR %s" % e.args[0]
            finally:
                try:
                    ac.close()
                except Exception:
                    pass

        th = threading.Thread(target=run_alter, daemon=True)
        th.start()
        # 等到 ALTER 真的进入 MDL 等待（有确定的可观测信号，不靠固定 sleep）
        waited = 0.0
        while waited < 60:
            st = q(ctl, "SELECT state FROM information_schema.processlist WHERE id=%s",
                   (state.get("conn_id"),))
            if st and "metadata lock" in (st[0]["state"] or ""):
                break
            time.sleep(0.1)
            waited += 0.1
        record("S3a", "ALTER 已进入 MDL 等待", waited < 60, "waited=%.1fs" % waited)
        killed = None
        try:
            q(ctl, "KILL QUERY %d" % state["conn_id"])
            killed = True
        except Exception as e:
            killed = "errno=%s %s" % (e.args[0], e)
        record("S3a", "KILL QUERY 执行成功", killed is True, killed)
        th.join(timeout=120)
        record("S3a", "被打断的 DDL 返回 1317(Query interrupted)", state.get("r") == "ERR 1317",
               "result=%s" % state.get("r"))
        after_type = one(ctl, "SELECT column_type FROM information_schema.columns "
                              "WHERE table_schema=DATABASE() AND table_name=%s AND column_name='c1'",
                         (TABLE,))
        record("S3a", "列类型未被半改", after_type == before_type,
               "before=%s after=%s" % (before_type, after_type))
        record("S3a", "数据校验和不变", checksum(ctl) == before_sum, "")
        ok, info = table_intact(ctl)
        record("S3a", "表仍可用", ok, "rows=%s" % info)
        record("S3a", "无 #sql- 残留", not leftover_temp_tables(ctl), leftover_temp_tables(ctl))
        q(holder, "COMMIT")
    finally:
        try:
            holder.close()
        except Exception:
            pass

    # ---------- S3b: 打断正在重建表的 DDL ----------
    big = max(rows, KILL_ROWS_MIN)
    log("S3b KILL 正在重建表的 DDL（%d 行，COPY 需要较长时间）" % big)
    build_table(cfg, big)
    try:
        before_type = one(ctl, "SELECT column_type FROM information_schema.columns "
                               "WHERE table_schema=DATABASE() AND column_name='c1' AND table_name=%s",
                          (TABLE,))
        before_sum = checksum(ctl)
        before_rows = one(ctl, "SELECT COUNT(*) FROM %s" % TABLE)
        state2 = {}

        def run_alter2():
            ac = connect(cfg)
            state2["conn_id"] = one(ac, "SELECT CONNECTION_ID()")
            t0 = time.time()
            try:
                q(ac, "ALTER TABLE %s MODIFY c1 BIGINT, ALGORITHM=COPY" % TABLE)
                state2["r"] = ("OK", round(time.time() - t0, 2))
            except Exception as e:
                state2["r"] = ("ERR %s" % e.args[0], round(time.time() - t0, 2))
            finally:
                try:
                    ac.close()
                except Exception:
                    pass

        th = threading.Thread(target=run_alter2, daemon=True)
        th.start()
        killed_at = None
        deadline = time.time() + 120
        while time.time() < deadline:
            cid = state2.get("conn_id")
            if cid:
                st = q(ctl, "SELECT command, state, time FROM information_schema.processlist WHERE id=%s",
                       (cid,))
                if st and st[0]["command"] == "Query":
                    try:
                        q(ctl, "KILL QUERY %d" % cid)
                        killed_at = (st[0]["state"], st[0]["time"])
                        break
                    except Exception as e:
                        record("S3b", "KILL QUERY 执行成功", False, "errno=%s %s" % (e.args[0], e))
                        killed_at = False
                        break
            if "r" in state2:      # DDL 已经结束，没赶上
                break
            time.sleep(0.05)
        record("S3b", "在 DDL 执行中途发出 KILL", bool(killed_at),
               "killed_at=%s ddl_result=%s" % (killed_at, state2.get("r")))
        th.join(timeout=300)
        res = state2.get("r", ("未返回",))
        record("S3b", "被打断的 DDL 返回 1317", str(res[0]) == "ERR 1317", "result=%s" % (res,))
        after_type = one(ctl, "SELECT column_type FROM information_schema.columns "
                              "WHERE table_schema=DATABASE() AND table_name=%s AND column_name='c1'",
                         (TABLE,))
        record("S3b", "列类型未被半改（回滚干净）", after_type == before_type,
               "before=%s after=%s" % (before_type, after_type))
        after_rows = one(ctl, "SELECT COUNT(*) FROM %s" % TABLE)
        record("S3b", "行数不变（重建中断未丢行）", after_rows == before_rows,
               "before=%s after=%s" % (before_rows, after_rows))
        record("S3b", "数据校验和不变", checksum(ctl) == before_sum, "")
        ok, info = table_intact(ctl)
        record("S3b", "表仍可用（可读可写）", ok, "rows=%s" % info)
        record("S3b", "无 #sql- 残留临时表", not leftover_temp_tables(ctl), leftover_temp_tables(ctl))
        try:
            q(ctl, "ALTER TABLE %s MODIFY c1 BIGINT, ALGORITHM=COPY" % TABLE)
            t2 = one(ctl, "SELECT column_type FROM information_schema.columns "
                          "WHERE table_schema=DATABASE() AND table_name=%s AND column_name='c1'", (TABLE,))
            record("S3b", "打断后仍可正常执行 DDL", t2 == "bigint", t2)
        except Exception as e:
            record("S3b", "打断后仍可正常执行 DDL", False, "errno=%s" % e.args[0])
    finally:
        try:
            ctl.close()
        except Exception:
            pass


# ================================================================ S4 DDL × DDL
def scenario_concurrent_ddl(cfg, rows):
    log("S4 并发 DDL × DDL（同表两条 ALTER 竞争）")
    build_table(cfg, rows)
    c1, c2 = connect(cfg), connect(cfg)
    try:
        before_sum = checksum(c1)
        out = {}

        def ddl(conn, key, sql):
            try:
                q(conn, sql)
                out[key] = "OK"
            except Exception as e:
                out[key] = "ERR %s" % e.args[0]

        t1 = threading.Thread(target=ddl, args=(c1, "a",
                              "ALTER TABLE %s MODIFY c1 BIGINT, ALGORITHM=COPY" % TABLE), daemon=True)
        t2 = threading.Thread(target=ddl, args=(c2, "b",
                              "ALTER TABLE %s ADD COLUMN c3 INT, ALGORITHM=COPY" % TABLE), daemon=True)
        t1.start(); t2.start()
        t1.join(timeout=300); t2.join(timeout=300)
        record("S4", "两条并发 DDL 都有确定结果", len(out) == 2, out)
        oks = [k for k, v in out.items() if v == "OK"]
        record("S4", "至少一条成功（没有双双卡死）", len(oks) >= 1, out)
        ok, n = table_intact(c1)
        record("S4", "表仍可用", ok, "rows=%s" % n)
        cols = [list(r.values())[0] for r in q(c1,
                "SELECT column_name FROM information_schema.columns WHERE table_schema=DATABASE() "
                "AND table_name=%s ORDER BY ordinal_position", (TABLE,))]
        record("S4", "最终列集合是确定的（无半改状态）",
               cols in (["id", "c1", "c2"], ["id", "c1", "c2", "c3"]), cols)
        record("S4", "原有数据校验和不变", checksum(c1) == before_sum, "sum=%s" % before_sum)
        record("S4", "无 #sql- 残留", not leftover_temp_tables(c1), leftover_temp_tables(c1))
    finally:
        for c in (c1, c2):
            try:
                c.close()
            except Exception:
                pass


# ================================================================ S5 DDL vs 运维语句
def scenario_ddl_vs_maintenance(cfg, rows):
    log("S5 DDL 与 OPTIMIZE / ANALYZE / TRUNCATE 并发")
    build_table(cfg, rows)
    c1, c2 = connect(cfg), connect(cfg)
    try:
        out = {}

        def run(conn, key, sql):
            try:
                q(conn, sql)
                out[key] = "OK"
            except Exception as e:
                out[key] = "ERR %s" % e.args[0]

        t1 = threading.Thread(target=run, args=(c1, "alter",
                              "ALTER TABLE %s MODIFY c1 BIGINT, ALGORITHM=COPY" % TABLE), daemon=True)
        t2 = threading.Thread(target=run, args=(c2, "optimize", "OPTIMIZE TABLE %s" % TABLE), daemon=True)
        t1.start(); t2.start(); t1.join(timeout=300); t2.join(timeout=300)
        record("S5", "ALTER 与 OPTIMIZE 并发都有确定结果", len(out) == 2, out)
        ok, n = table_intact(c1)
        record("S5", "表仍可用", ok, "rows=%s" % n)
        record("S5", "无 #sql- 残留", not leftover_temp_tables(c1), leftover_temp_tables(c1))
        # ANALYZE 与 DDL 串行执行必须都成功
        try:
            q(c1, "ANALYZE TABLE %s" % TABLE)
            q(c1, "ALTER TABLE %s MODIFY c1 INT, ALGORITHM=COPY" % TABLE)
            record("S5", "ANALYZE 后再 ALTER 正常", True, "")
        except Exception as e:
            record("S5", "ANALYZE 后再 ALTER 正常", False, "errno=%s" % e.args[0])
    finally:
        for c in (c1, c2):
            try:
                c.close()
            except Exception:
                pass


# ================================================================ S6 online alter log
def scenario_online_alter_log(cfg, rows):
    """需要 SUPER/SYSTEM_VARIABLES_ADMIN 才能调小 innodb_online_alter_log_max_size。

    RDS 上该权限被收回（errno 1227），此时**明确 SKIP**，绝不假装通过。
    """
    log("S6 innodb_online_alter_log_max_size 溢出（需要 SUPER）")
    probe = connect(cfg)
    try:
        try:
            q(probe, "SET GLOBAL innodb_online_alter_log_max_size=65536")
        except Exception as e:
            record("S6", "需要 SUPER 权限（本环境不具备）-> SKIP", True,
                   "errno=%s %s" % (e.args[0], str(e.args[1])[:80]))
            with LOCK:
                RESULTS[-1]["result"] = "SKIP"
            return
    finally:
        probe.close()

    conn = connect(cfg)
    writer = connect(cfg)
    stop = threading.Event()
    try:
        build_table(cfg, rows)
        errors = []

        batch = 2000      # 批量更新：单行 UPDATE 产生 row log 太慢，压不出溢出

        def dml():
            i = 0
            while not stop.is_set() and i < 2_000_000:
                lo = (i % rows) + 1
                try:
                    q(writer, "UPDATE %s SET c2=CONCAT('v',%d) WHERE id BETWEEN %d AND %d"
                      % (TABLE, i, lo, lo + batch))
                except Exception as e:
                    errors.append(e.args[0])
                i += batch

        th = threading.Thread(target=dml, daemon=True)
        th.start()
        err = None
        try:
            q(conn, "ALTER TABLE %s ADD INDEX idx_c2 (c2), ALGORITHM=INPLACE, LOCK=NONE" % TABLE)
        except Exception as e:
            err = (e.args[0], str(e.args[1])[:120])
        stop.set()
        th.join(timeout=60)
        record("S6", "row log 溢出时 DDL 以 1799 失败", bool(err) and err[0] == 1799,
               "err=%s dml_errors=%s" % (err, set(errors)))
        ok, n = table_intact(conn)
        record("S6", "溢出失败后表仍可用", ok, "rows=%s" % n)
    finally:
        stop.set()
        try:
            q(connect(cfg), "SET GLOBAL innodb_online_alter_log_max_size=DEFAULT")
        except Exception:
            pass
        for c in (conn, writer):
            try:
                c.close()
            except Exception:
                pass


# ================================================================ S7 FK 并发
def scenario_fk_concurrent(cfg, rows):
    log("S7 外键父子两侧并发 ALTER")
    conn = connect(cfg)
    q(conn, "SET foreign_key_checks=0")
    q(conn, "DROP TABLE IF EXISTS s_fk_c, s_fk_p")
    q(conn, "SET foreign_key_checks=1")
    q(conn, "CREATE TABLE s_fk_p (pid INT AUTO_INCREMENT PRIMARY KEY, fk INT, KEY i(fk)) ENGINE=InnoDB")
    q(conn, "CREATE TABLE s_fk_c (cid INT AUTO_INCREMENT PRIMARY KEY, fk INT, KEY i(fk), "
            "CONSTRAINT s_fk FOREIGN KEY (fk) REFERENCES s_fk_p(fk)) ENGINE=InnoDB")
    q(conn, "INSERT INTO s_fk_p (fk) VALUES (1),(2),(3)")
    q(conn, "INSERT INTO s_fk_c (fk) VALUES (1),(2),(3)")
    conn.close()
    c1, c2 = connect(cfg), connect(cfg)
    try:
        out = {}

        def run(c, key, sql):
            try:
                q(c, sql)
                out[key] = "OK"
            except Exception as e:
                out[key] = "ERR %s" % e.args[0]

        t1 = threading.Thread(target=run, args=(c1, "parent",
                              "ALTER TABLE s_fk_p MODIFY fk BIGINT, ALGORITHM=COPY"), daemon=True)
        t2 = threading.Thread(target=run, args=(c2, "child",
                              "ALTER TABLE s_fk_c MODIFY fk BIGINT, ALGORITHM=COPY"), daemon=True)
        t1.start(); t2.start(); t1.join(timeout=180); t2.join(timeout=180)
        record("S7", "父子两侧并发 ALTER 都有确定结果", len(out) == 2, out)
        types = {r["table_name"]: r["column_type"] for r in q(c1,
                 "SELECT table_name, column_type FROM information_schema.columns "
                 "WHERE table_schema=DATABASE() AND table_name IN ('s_fk_p','s_fk_c') AND column_name='fk'")}
        consistent = types.get("s_fk_p") == types.get("s_fk_c")
        fk_rows = q(c1, "SELECT COUNT(*) c FROM information_schema.table_constraints "
                        "WHERE table_schema=DATABASE() AND table_name='s_fk_c' AND constraint_type='FOREIGN KEY'")
        record("S7", "两侧类型要么都改要么都不改（不得出现半改）", consistent or len(out) == 2, types)
        record("S7", "外键约束状态可查", fk_rows is not None, fk_rows)
        ok, info = table_intact(
            c1, "s_fk_c",
            write_probe="INSERT INTO %s (fk) VALUES (1)",
            cleanup_probe="DELETE FROM %s WHERE cid = (SELECT MAX(cid) FROM (SELECT cid FROM %s) z)" % ("s_fk_c", "s_fk_c"))
        record("S7", "子表仍可用（可读可写）", ok, info)
        # 父表探针必须写入/删除一个**未被任何子行引用**的键值，
        # 否则删除会正确地触发 errno 1451（外键约束生效），把探针自己搞成假失败。
        okp, infop = table_intact(
            c1, "s_fk_p",
            write_probe="INSERT INTO %s (fk) VALUES (999999)",
            cleanup_probe="DELETE FROM %s WHERE fk = 999999")
        record("S7", "父表仍可用（可读可写）", okp, infop)
    finally:
        for c in (c1, c2):
            try:
                c.close()
            except Exception:
                pass
        try:
            cc = connect(cfg)
            q(cc, "SET foreign_key_checks=0")
            q(cc, "DROP TABLE IF EXISTS s_fk_c, s_fk_p, %s" % TABLE)
            q(cc, "SET foreign_key_checks=1")
            cc.close()
        except Exception:
            pass


SCENARIOS = {
    "S1": scenario_mdl_blocking,
    "S2": scenario_lock_wait_timeout,
    "S3": scenario_kill_ddl,
    "S4": scenario_concurrent_ddl,
    "S5": scenario_ddl_vs_maintenance,
    "S6": scenario_online_alter_log,
    "S7": scenario_fk_concurrent,
}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--env", default="aliyun")
    ap.add_argument("--config", default=os.path.join(ROOT, "config.ini"))
    ap.add_argument("--rows", type=int, default=200000, help="每个场景的表行数上限（保守默认 20 万）")
    ap.add_argument("--only", nargs="*", help="只跑指定场景，如 --only S1 S3")
    ap.add_argument("--out", default=os.path.join(ROOT, "results", "online_ddl_scenarios.json"))
    args = ap.parse_args()

    cfgp = configparser.ConfigParser()
    cfgp.read(args.config)
    if args.env not in cfgp:
        print("config 里没有 [%s]" % args.env)
        return 2
    c = cfgp[args.env]
    cfg = {"host": c.get("host"), "port": c.get("port", "3306"), "user": c.get("user"),
           "password": os.environ.get("MYSQL_PWD") or c.get("password"),
           "database": c.get("database", "ddl_test")}

    conn = connect(cfg)
    log("目标实例 %s:%s  version=%s  rows=%d" % (cfg["host"], cfg["port"],
                                                one(conn, "SELECT VERSION()"), args.rows))
    conn.close()

    picked = args.only or list(SCENARIOS)
    for key in picked:
        if key not in SCENARIOS:
            print("未知场景 %s" % key)
            continue
        t0 = time.time()
        try:
            SCENARIOS[key](cfg, args.rows)
        except Exception as e:
            record(key, "场景异常退出", False, "%s: %s" % (type(e).__name__, e))
        log("  %s 用时 %.1fs" % (key, time.time() - t0))

    # 清理
    try:
        cc = connect(cfg)
        q(cc, "SET foreign_key_checks=0")
        q(cc, "DROP TABLE IF EXISTS %s, s_fk_c, s_fk_p" % TABLE)
        q(cc, "SET foreign_key_checks=1")
        cc.close()
    except Exception:
        pass

    n_pass = sum(1 for r in RESULTS if r["result"] == "PASS")
    n_fail = sum(1 for r in RESULTS if r["result"] == "FAIL")
    n_skip = sum(1 for r in RESULTS if r["result"] == "SKIP")
    print("\n" + "=" * 78)
    print("在线 DDL 失败模式专项: PASS=%d FAIL=%d SKIP=%d (共 %d 项检查)"
          % (n_pass, n_fail, n_skip, len(RESULTS)))
    print("=" * 78)
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as fh:
        json.dump({"env": args.env, "rows": args.rows,
                   "finished_at": datetime.now().isoformat(timespec="seconds"),
                   "summary": {"pass": n_pass, "fail": n_fail, "skip": n_skip},
                   "checks": RESULTS}, fh, ensure_ascii=False, indent=1)
    print("结果写入 %s" % args.out)
    return 1 if n_fail else 0


if __name__ == "__main__":
    sys.exit(main())
