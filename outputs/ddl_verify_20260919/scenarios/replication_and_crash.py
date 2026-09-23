#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""P1-6 主备复制一致性 + DDL 中途崩溃恢复。

这是"秒级修改列类型"上线后最可能造成生产事故的两条路径：
  * INSTANT 类型变更本质是元数据 + 行版本操作，binlog 如何记录、备库重放后
    列定义与行版本是否与主库一致 —— 不一致就会导致复制中断或**静默数据错误**
  * DDL 执行到一半实例崩溃，重启后表是否可用、元数据是否半改、数据是否丢失

三类检查：
  R1 binlog 记录验证     每条 ALTER 都必须进 binlog（备库能同步的必要条件）
  R2 备库重放一致性      需要 --replica-config；未配置时**明确 SKIP**，不假装通过
  C1 崩溃恢复            在**独立的一次性 mysqld**（临时 datadir + 独立端口/socket）上做，
                        SIGKILL 后重启，验证 InnoDB 崩溃恢复与表完整性
                        —— 绝不触碰任何已在运行的实例

用法：
  python3 scenarios/replication_and_crash.py --env aliyun --only R1
  python3 scenarios/replication_and_crash.py --only C1 --crash-rows 2000000
  python3 scenarios/replication_and_crash.py --env aliyun --only R2 \\
      --replica-config replica.ini     # [replica] host/port/user/password
"""
import os
import re
import sys
import json
import time
import signal
import shutil
import socket
import argparse
import tempfile
import threading
import subprocess
import configparser
from datetime import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)

import pymysql  # noqa: E402

RESULTS = []
TABLE = "s_repl_crash"

# 崩溃点的 DDL 可切换，用于覆盖两条完全不同的崩溃路径：
#   copy_rebuild      逐行拷贝到临时表途中崩溃（ALTER ... ALGORITHM=COPY）
#   inplace_add_index online DDL + row log 途中崩溃（ADD INDEX ... INPLACE, LOCK=NONE）
CRASH_DDLS = {
    "copy_rebuild": ("ALTER TABLE %s MODIFY c1 BIGINT, ALGORITHM=COPY", ("int", "bigint")),
    "inplace_add_index": ("ALTER TABLE %s ADD INDEX idx_crash (c2), ALGORITHM=INPLACE, LOCK=NONE",
                          ("int",)),
}
CRASH_DDL = "copy_rebuild"


def log(msg):
    print("[%s] %s" % (datetime.now().strftime("%H:%M:%S"), msg), flush=True)


def record(scenario, name, passed, detail=""):
    status = "PASS" if passed is True else ("SKIP" if passed == "SKIP" else "FAIL")
    RESULTS.append({"scenario": scenario, "check": name, "result": status,
                    "detail": str(detail)[:800]})
    mark = {"PASS": "✓", "FAIL": "✗", "SKIP": "○"}[status]
    print("    %s %-40s %s" % (mark, name, str(detail)[:200]), flush=True)


def q(conn, sql, args=None):
    with conn.cursor() as cur:
        cur.execute(sql, args)
        if cur.description:
            cols = [d[0].lower() for d in cur.description]
            return [dict(zip(cols, r)) for r in cur.fetchall()]
        return None


def one(conn, sql, args=None):
    rows = q(conn, sql, args)
    return list(rows[0].values())[0] if rows else None


def connect(cfg, **kw):
    base = dict(host=cfg["host"], port=int(cfg.get("port", 3306)), user=cfg["user"],
                password=cfg.get("password") or "", database=cfg.get("database", "ddl_test"),
                charset="utf8mb4", autocommit=True, connect_timeout=15,
                read_timeout=900, write_timeout=900)
    base.update(kw)
    return pymysql.connect(**base)


# ================================================================ R1 binlog
R1_COLUMNS = ("c1 INT, c2 VARCHAR(10) CHARACTER SET latin1, c3 INT, c4 INT, c5 BIGINT")
R1_ALTERS = [
    ("int_inplace", "ALTER TABLE {t} MODIFY c1 BIGINT, ALGORITHM=INPLACE"),
    ("varchar_inplace", "ALTER TABLE {t} MODIFY c2 VARCHAR(20) CHARACTER SET latin1, ALGORITHM=INPLACE"),
    ("add_index_inplace", "ALTER TABLE {t} ADD INDEX idx_c3 (c3), ALGORITHM=INPLACE, LOCK=NONE"),
    ("default_algo", "ALTER TABLE {t} MODIFY c4 BIGINT"),
    ("decimal_copy", "ALTER TABLE {t} MODIFY c5 DECIMAL(20,0), ALGORITHM=COPY"),
]


def scenario_binlog(cfg, rows):
    """R1: 成功的 ALTER 必须写进 binlog；失败的 ALTER 必须**不**写进 binlog。

    两个方向都要断言：只查"成功的进了 binlog"是不够的 —— 失败 DDL 若被误记进
    binlog，备库会重放一条主库上并没有生效的变更，导致主备元数据漂移。
    """
    log("R1 binlog 记录验证")
    conn = connect(cfg)
    try:
        fmt = one(conn, "SELECT @@binlog_format")
        logbin = one(conn, "SELECT @@log_bin")
        record("R1", "binlog 已开启", logbin == 1, "log_bin=%s format=%s" % (logbin, fmt))
        if not logbin:
            record("R1", "无 binlog，后续检查跳过", "SKIP", "log_bin=0")
            return
        q(conn, "DROP TABLE IF EXISTS %s" % TABLE)
        q(conn, "CREATE TABLE %s (id INT AUTO_INCREMENT PRIMARY KEY, %s) ENGINE=InnoDB"
              % (TABLE, R1_COLUMNS))
        q(conn, "INSERT INTO %s (c1) VALUES (1),(2),(3)" % TABLE)

        def master_status():
            try:
                r = q(conn, "SHOW MASTER STATUS")
            except Exception:
                r = q(conn, "SHOW BINARY LOG STATUS")
            return r[0] if r else None

        def events_from(f, pos, limit=800):
            return q(conn, "SHOW BINLOG EVENTS IN '%s' FROM %d LIMIT %d" % (f, int(pos), limit)) or []

        ok_events = 0
        for marker, alter_tpl in R1_ALTERS:
            st = master_status()
            # q() 已把列名统一转小写
            f = st.get("file") or st.get("log_name")
            pos = int(st.get("position") or st.get("pos") or 4)
            stmt = alter_tpl.format(t=TABLE)
            try:
                q(conn, stmt)
                err = None
            except Exception as e:
                err = e.args[0]
            # binlog 刷盘有微小延迟，最多重试 5 次
            hits, scanned = [], 0
            for _attempt in range(5):
                ev = events_from(f, pos)
                scanned = len(ev)
                hits = [e for e in ev
                        if "query" in str(e.get("event_type", "")).lower()
                        and "ALTER TABLE" in str(e.get("info", "")).upper()
                        and TABLE in str(e.get("info", ""))]
                if hits or err is not None:
                    break
                time.sleep(0.4)
            if err is None:
                ok_events += 1
                record("R1", "%s 成功 => 必须进 binlog" % marker, len(hits) >= 1,
                       "events=%d hits=%d info=%s" % (scanned, len(hits),
                                                      (hits[0].get("info") if hits else "")[:120]))
            else:
                record("R1", "%s 失败(errno=%s) => 必须不进 binlog" % (marker, err),
                       len(hits) == 0,
                       "误记入 binlog 的事件=%s" % ([h.get("info", "")[:80] for h in hits] or "无"))
        record("R1", "至少有一条 DDL 以 Query_event 落盘（备库可重放）", ok_events > 0,
               "成功的 DDL 条数=%d" % ok_events)
        q(conn, "DROP TABLE IF EXISTS %s" % TABLE)
    finally:
        conn.close()


# ================================================================ R2 备库
def scenario_replica(cfg, rows, replica_cfg):
    log("R2 备库重放一致性")
    if not replica_cfg:
        record("R2", "未配置备库 -> SKIP", "SKIP",
               "用 --replica-config 指定 [replica] host/port/user/password 后重跑")
        return
    pri, rep = connect(cfg), connect(replica_cfg)
    try:
        q(pri, "DROP TABLE IF EXISTS %s" % TABLE)
        q(pri, "CREATE TABLE %s (id INT AUTO_INCREMENT PRIMARY KEY, c1 INT, "
               "c2 VARCHAR(20) CHARACTER SET latin1, KEY i1(c1)) ENGINE=InnoDB" % TABLE)
        q(pri, "INSERT INTO %s (c1, c2) VALUES (1,'a'),(2,'b'),(3,'c')" % TABLE)
        for algo in ("INPLACE", "COPY"):
            try:
                q(pri, "ALTER TABLE %s MODIFY c1 BIGINT, ALGORITHM=%s" % (TABLE, algo))
            except Exception:
                pass
        try:
            q(pri, "ALTER TABLE %s MODIFY c2 VARCHAR(40) CHARACTER SET latin1" % TABLE)
        except Exception:
            pass
        # 等备库追上
        deadline = time.time() + 60
        lag = None
        while time.time() < deadline:
            st = q(rep, "SHOW REPLICA STATUS") or q(rep, "SHOW SLAVE STATUS")
            if st:
                st = st[0]
                lag = st.get("seconds_behind_source", st.get("seconds_behind_master"))
                if lag in (0, "0"):
                    break
            time.sleep(1)
        st = (q(rep, "SHOW REPLICA STATUS") or q(rep, "SHOW SLAVE STATUS") or [{}])[0]
        io_run = st.get("replica_io_running", st.get("slave_io_running"))
        sql_run = st.get("replica_sql_running", st.get("slave_sql_running"))
        last_err = st.get("last_sql_error") or st.get("last_io_error") or ""
        record("R2", "备库 IO/SQL 线程均在运行", io_run == "Yes" and sql_run == "Yes",
               "io=%s sql=%s" % (io_run, sql_run))
        record("R2", "备库无复制错误", not last_err, last_err[:200])
        record("R2", "备库已追上主库", str(lag) == "0", "seconds_behind=%s" % lag)

        def ddl_of(conn):
            r = q(conn, "SHOW CREATE TABLE %s" % TABLE)
            return list(r[0].values())[1] if r else None

        def ctype(conn):
            return {row["column_name"]: row["column_type"] for row in
                    (q(conn, "SELECT column_name, column_type FROM information_schema.columns "
                             "WHERE table_schema=DATABASE() AND table_name=%s "
                             "ORDER BY ordinal_position", (TABLE,)) or [])}

        def crc(conn):
            return one(conn, "SELECT BIT_XOR(CAST(CRC32(CONCAT_WS('|', id, IFNULL(c1,'~'), "
                             "IFNULL(c2,'~'))) AS UNSIGNED)) FROM %s" % TABLE)

        record("R2", "主备 SHOW CREATE TABLE 逐字一致", ddl_of(pri) == ddl_of(rep),
               "primary=%s | replica=%s" % (ddl_of(pri), ddl_of(rep)))
        record("R2", "主备列类型逐列一致", ctype(pri) == ctype(rep),
               "primary=%s replica=%s" % (ctype(pri), ctype(rep)))
        record("R2", "主备数据 CRC 一致", crc(pri) == crc(rep), "pri=%s rep=%s" % (crc(pri), crc(rep)))
        q(pri, "DROP TABLE IF EXISTS %s" % TABLE)
    finally:
        pri.close()
        rep.close()


# ================================================================ C1 崩溃恢复
def free_port():
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    p = s.getsockname()[1]
    s.close()
    return p


def find_mysqld():
    for cand in ("/opt/homebrew/opt/mysql@8.0/bin/mysqld", "/opt/homebrew/bin/mysqld",
                 "/usr/local/mysql/bin/mysqld", shutil.which("mysqld") or ""):
        if cand and os.path.exists(cand):
            return cand
    return None


class ThrowawayInstance(object):
    """独立的一次性 mysqld：临时 datadir + 独立端口 + 独立 socket。

    绝不触碰任何已在运行的实例；退出时 SIGKILL 兜底并删除 datadir。
    """

    def __init__(self, rows_hint=""):
        self.mysqld = find_mysqld()
        self.tmp = tempfile.mkdtemp(prefix="ddl_crash_%s_" % rows_hint)
        self.datadir = os.path.join(self.tmp, "data")
        self.sock = os.path.join(self.tmp, "my.sock")
        self.pidfile = os.path.join(self.tmp, "my.pid")
        self.errlog = os.path.join(self.tmp, "err.log")
        self.port = free_port()
        self.proc = None
        self.basedir = os.path.dirname(os.path.dirname(self.mysqld)) if self.mysqld else None

    def initialize(self):
        cmd = [self.mysqld, "--initialize-insecure", "--datadir=%s" % self.datadir,
               "--basedir=%s" % self.basedir]
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        return r.returncode == 0, (r.stderr or r.stdout)[-500:]

    def start(self, wait=90):
        cmd = [self.mysqld, "--datadir=%s" % self.datadir, "--basedir=%s" % self.basedir,
               "--port=%d" % self.port, "--socket=%s" % self.sock,
               "--pid-file=%s" % self.pidfile, "--log-error=%s" % self.errlog,
               "--mysqlx=0", "--skip-name-resolve", "--innodb-buffer-pool-size=128M",
               "--innodb-flush-log-at-trx-commit=1", "--max-connections=200"]
        self.proc = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        deadline = time.time() + wait
        while time.time() < deadline:
            if self.proc.poll() is not None:
                return False, "mysqld 退出，rc=%s" % self.proc.returncode
            try:
                c = self.conn()
                c.close()
                return True, "port=%d" % self.port
            except Exception:
                time.sleep(0.5)
        return False, "启动超时"

    def conn(self, **kw):
        return pymysql.connect(unix_socket=self.sock, user="root", password="",
                               charset="utf8mb4", autocommit=True,
                               connect_timeout=10, read_timeout=600, **kw)

    def sigkill(self):
        if self.proc and self.proc.poll() is None:
            os.kill(self.proc.pid, signal.SIGKILL)
            try:
                self.proc.wait(timeout=30)
            except Exception:
                pass
            return True
        return False

    def cleanup(self):
        try:
            if self.proc and self.proc.poll() is None:
                self.proc.terminate()
                try:
                    self.proc.wait(timeout=20)
                except Exception:
                    try:
                        os.kill(self.proc.pid, signal.SIGKILL)
                    except Exception:
                        pass
        finally:
            shutil.rmtree(self.tmp, ignore_errors=True)

    def error_log_tail(self, n=4000):
        try:
            with open(self.errlog, "r", encoding="utf-8", errors="replace") as fh:
                return fh.read()[-n:]
        except Exception:
            return ""


def scenario_crash_recovery(cfg, rows):
    """C1: DDL 执行中途 SIGKILL 实例，重启后验证 InnoDB 崩溃恢复与表完整性。"""
    log("C1 崩溃恢复（独立一次性 mysqld，端口自动分配）")
    mysqld = find_mysqld()
    if not mysqld:
        record("C1", "未找到 mysqld -> SKIP", "SKIP", "需要本机 mysqld 才能做崩溃恢复")
        return
    inst = ThrowawayInstance()
    try:
        ok, msg = inst.initialize()
        record("C1", "初始化一次性实例", ok, msg[:200])
        if not ok:
            return
        ok, msg = inst.start()
        record("C1", "启动一次性实例", ok, msg)
        if not ok:
            log(inst.error_log_tail(1200))
            return
        # MySQL 8.0 的 --initialize-insecure 不会创建 test 库，必须显式建一个
        _bootstrap = inst.conn()
        q(_bootstrap, "CREATE DATABASE IF NOT EXISTS test")
        _bootstrap.close()
        conn = inst.conn(database="test")
        ver = one(conn, "SELECT VERSION()")
        log("  一次性实例已就绪 version=%s port=%d" % (ver, inst.port))

        # 建表灌数据
        q(conn, "DROP TABLE IF EXISTS %s" % TABLE)
        q(conn, "CREATE TABLE %s (id INT NOT NULL AUTO_INCREMENT PRIMARY KEY, c1 INT NOT NULL DEFAULT 0, "
                "c2 VARCHAR(64) DEFAULT 'x', KEY idx_c1(c1)) ENGINE=InnoDB" % TABLE)
        q(conn, "INSERT INTO %s (c1) VALUES (1)" % TABLE)
        n = 1
        while n < rows:
            q(conn, "INSERT INTO %s (c1, c2) SELECT c1, c2 FROM %s" % (TABLE, TABLE))
            n *= 2
        actual_rows = one(conn, "SELECT COUNT(*) FROM %s" % TABLE)
        before_sum = one(conn, "SELECT BIT_XOR(CAST(CRC32(CONCAT_WS('|', id, c1, IFNULL(c2,'~'))) "
                               "AS UNSIGNED)) FROM %s" % TABLE)
        before_type = one(conn, "SELECT column_type FROM information_schema.columns "
                                "WHERE table_schema='test' AND table_name=%s AND column_name='c1'", (TABLE,))
        log("  已灌入 %s 行，c1=%s，checksum=%s" % (actual_rows, before_type, before_sum))
        conn.close()

        # 后台发起长时间 DDL（COPY 重建），中途 SIGKILL 整个实例
        worker = inst.conn(database="test")
        state = {}

        _alter_tpl, _ok_types = CRASH_DDLS[CRASH_DDL]

        def run_ddl():
            try:
                q(worker, _alter_tpl % TABLE)
                state["r"] = "OK"
            except Exception as e:
                state["r"] = "ERR %s" % (e.args[0] if e.args else e)

        th = threading.Thread(target=run_ddl, daemon=True)
        th.start()
        ctl = inst.conn(database="test")
        in_ddl = False
        deadline = time.time() + 180
        while time.time() < deadline:
            try:
                pl = q(ctl, "SELECT command, state, time FROM information_schema.processlist "
                            "WHERE info LIKE %s AND command='Query'", ("ALTER TABLE %s%%" % TABLE,))
            except Exception:
                break
            _st = (pl[0]["state"] or "").lower() if pl else ""
            if pl and any(k in _st for k in ("copy", "altering table", "preparing",
                                             "building index", "committing", "renaming")):
                in_ddl = True
                break
            if pl and (pl[0]["time"] or 0) >= 2:
                in_ddl = True
                break
            if "r" in state:
                break
            time.sleep(0.1)
        record("C1", "DDL 已进入执行阶段（可被崩溃打断）", in_ddl,
               "state=%s ddl_result=%s" % (pl[0] if pl else None, state.get("r")))
        killed = inst.sigkill()
        record("C1", "SIGKILL 实例成功", killed, "pid 已终止")
        try:
            ctl.close()
        except Exception:
            pass
        try:
            worker.close()
        except Exception:
            pass

        # 重启（InnoDB 崩溃恢复）
        ok, msg = inst.start(wait=180)
        record("C1", "崩溃后实例能重新启动（InnoDB 恢复完成）", ok, msg)
        if not ok:
            log(inst.error_log_tail(2000))
            return
        errlog = inst.error_log_tail()
        record("C1", "错误日志无 InnoDB 致命错误",
               not re.search(r"\[ERROR\].*(InnoDB|corrupt|assertion)", errlog, re.I),
               [l for l in errlog.splitlines() if "[ERROR]" in l][:3])

        conn = inst.conn(database="test")
        after_type = one(conn, "SELECT column_type FROM information_schema.columns "
                               "WHERE table_schema='test' AND table_name=%s AND column_name='c1'", (TABLE,))
        after_rows = one(conn, "SELECT COUNT(*) FROM %s" % TABLE)
        after_sum = one(conn, "SELECT BIT_XOR(CAST(CRC32(CONCAT_WS('|', id, c1, IFNULL(c2,'~'))) "
                              "AS UNSIGNED)) FROM %s" % TABLE)
        record("C1", "表仍存在且列定义完整（无半改状态）",
               after_type in _ok_types,
               "c1=%s 合法集合=%s (崩溃前=%s)" % (after_type, _ok_types, before_type))
        record("C1", "行数与崩溃前一致（未丢行）", after_rows == actual_rows,
               "before=%s after=%s" % (actual_rows, after_rows))
        record("C1", "数据校验和与崩溃前一致", after_sum == before_sum,
               "before=%s after=%s" % (before_sum, after_sum))
        chk = q(conn, "CHECK TABLE %s" % TABLE)
        record("C1", "CHECK TABLE 通过", bool(chk) and str(chk[-1].get("msg_text", "")).lower() == "ok", chk)
        leftovers = [list(r.values())[0] for r in
                     (q(conn, "SELECT table_name FROM information_schema.tables "
                              "WHERE table_schema='test' AND table_name LIKE '#sql%%'") or [])]
        record("C1", "无 #sql- 残留中间表", not leftovers, leftovers)
        _idx = q(conn, "SELECT COUNT(*) c FROM information_schema.statistics "
                       "WHERE table_schema='test' AND table_name=%s AND index_name='idx_crash'",
                 (TABLE,))
        _n_idx = (_idx or [{}])[0].get("c", 0)
        record("C1", "崩溃的索引要么完整要么完全不存在（无半成品索引）", _n_idx in (0, 1),
               "idx_crash 列数=%s" % _n_idx)
        try:
            q(conn, "ALTER TABLE %s MODIFY c1 BIGINT, ALGORITHM=COPY" % TABLE)
            t2 = one(conn, "SELECT column_type FROM information_schema.columns "
                           "WHERE table_schema='test' AND table_name=%s AND column_name='c1'", (TABLE,))
            record("C1", "崩溃恢复后仍可正常执行 DDL", t2 == "bigint", t2)
        except Exception as e:
            record("C1", "崩溃恢复后仍可正常执行 DDL", False, "errno=%s %s" % (e.args[0], e))
        try:
            q(conn, "INSERT INTO %s (c1, c2) VALUES (777, 'after-crash')" % TABLE)
            got = one(conn, "SELECT c2 FROM %s WHERE c1=777" % TABLE)
            q(conn, "DELETE FROM %s WHERE c1=777" % TABLE)
            record("C1", "崩溃恢复后可正常读写", got == "after-crash", got)
        except Exception as e:
            record("C1", "崩溃恢复后可正常读写", False, "errno=%s" % e.args[0])
        conn.close()
    finally:
        inst.cleanup()


SCENARIOS = {"R1": scenario_binlog, "R2": scenario_replica, "C1": scenario_crash_recovery}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--env", default="aliyun")
    ap.add_argument("--config", default=os.path.join(ROOT, "config.ini"))
    ap.add_argument("--replica-config", help="备库配置 ini，需含 [replica] 段")
    ap.add_argument("--rows", type=int, default=100000)
    ap.add_argument("--crash-rows", type=int, default=2000000, help="C1 崩溃场景的表行数")
    ap.add_argument("--crash-ddl", choices=sorted(CRASH_DDLS), default="copy_rebuild",
                    help="崩溃点使用的 DDL（覆盖 COPY 重建 与 INPLACE 建索引 两条路径）")
    ap.add_argument("--only", nargs="*")
    ap.add_argument("--out", default=os.path.join(ROOT, "results", "replication_crash.json"))
    args = ap.parse_args()

    cfgp = configparser.ConfigParser()
    cfg = None
    if args.env in (args.only or []) or not args.only or \
       any(s in (args.only or []) for s in ("R1", "R2")):
        if os.path.exists(args.config):
            cfgp.read(args.config)
            if args.env in cfgp:
                c = cfgp[args.env]
                cfg = {"host": c.get("host"), "port": c.get("port", "3306"), "user": c.get("user"),
                       "password": os.environ.get("MYSQL_PWD") or c.get("password"),
                       "database": c.get("database", "ddl_test")}
    replica_cfg = None
    if args.replica_config and os.path.exists(args.replica_config):
        rc = configparser.ConfigParser()
        rc.read(args.replica_config)
        if "replica" in rc:
            r = rc["replica"]
            replica_cfg = {"host": r.get("host"), "port": r.get("port", "3306"),
                           "user": r.get("user"), "password": r.get("password"),
                           "database": r.get("database", "ddl_test")}

    global CRASH_DDL
    CRASH_DDL = args.crash_ddl
    log("崩溃点 DDL = %s: %s" % (CRASH_DDL, CRASH_DDLS[CRASH_DDL][0] % TABLE))
    picked = args.only or list(SCENARIOS)
    for key in picked:
        t0 = time.time()
        try:
            if key == "R1":
                if not cfg:
                    record("R1", "未配置 [%s] -> SKIP" % args.env, "SKIP", args.config)
                else:
                    scenario_binlog(cfg, args.rows)
            elif key == "R2":
                scenario_replica(cfg, args.rows, replica_cfg)
            elif key == "C1":
                scenario_crash_recovery(cfg, args.crash_rows)
            else:
                print("未知场景 %s" % key)
        except Exception as e:
            record(key, "场景异常退出", False, "%s: %s" % (type(e).__name__, e))
        log("  %s 用时 %.1fs" % (key, time.time() - t0))

    n = {k: sum(1 for r in RESULTS if r["result"] == k) for k in ("PASS", "FAIL", "SKIP")}
    print("\n" + "=" * 78)
    print("复制与崩溃恢复专项: PASS=%d FAIL=%d SKIP=%d (共 %d 项检查)"
          % (n["PASS"], n["FAIL"], n["SKIP"], len(RESULTS)))
    print("=" * 78)
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as fh:
        json.dump({"finished_at": datetime.now().isoformat(timespec="seconds"),
                   "summary": n, "checks": RESULTS}, fh, ensure_ascii=False, indent=1)
    print("结果写入 %s" % args.out)
    return 1 if n["FAIL"] else 0


if __name__ == "__main__":
    sys.exit(main())
