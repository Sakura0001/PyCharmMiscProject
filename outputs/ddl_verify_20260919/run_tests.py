#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RDS MySQL DDL 秒级/在线修改列类型 — 测试执行器 v3
================================================================
v3 相对 v2 的变更（对应审计报告 test_gap_audit_20260923.md）:

  P0-1  同时发现 `*.sql` 与 `*.sql.gz`（v2 静默跳过 8 个 gz 文件 = 84.8% 用例）
  P0-4  按用例切分执行，用例 ID 全集与产出结果全集做完整性核算（缺失 => MISSING）
  P3-5  每条语句的 errno/errmsg 按用例归因落盘（v2 只保留文件级 stderr 尾巴 2000 字符）
  P3-2  支持 --workers 并发 / --retry 重试 / --resume 断点续跑 / --case-filter / --sample
  P3-3  运行前采集环境快照（VERSION + 关键 variables），写入结果目录
  P3-4  支持 --defaults-extra-file / MYSQL_PWD，避免密码出现在命令行与 ps 中
  P0-1b 生成/校验 manifest（文件清单 + 用例数 + 内容哈希），报告与产物强绑定

执行引擎:
  默认 pymysql（逐语句执行，可精确归因错误）；无 pymysql 时用 --use-cli 回退到
  mysql 客户端整文件执行（此时错误归因粒度下降，会打印告警）。

用法:
  python3 run_tests.py --env local --dry-run                 # 只出 manifest，不连库
  python3 run_tests.py --env local --files 10_special_patterns.sql
  python3 run_tests.py --env aliyun --workers 4
  python3 run_tests.py --env internal --resume               # 断点续跑
"""

import os
import sys
import re
import csv
import json
import time
import gzip
import hashlib
import shutil
import argparse
import threading
import configparser
import subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed

OUTPUT_DIR = os.path.dirname(os.path.abspath(__file__))
SQL_ALIYUN = os.path.join(OUTPUT_DIR, "sql_aliyun")
SQL_INTERNAL = os.path.join(OUTPUT_DIR, "sql_internal")
RESULTS_DIR = os.path.join(OUTPUT_DIR, "results")

# 用例头注释里可机读的期望标记（P0-7 由生成器写出，此处负责解析）
RE_CASE = re.compile(r"^--\s*Test Case:\s*(\S+)")
RE_TYPE = re.compile(r"^--\s*Type:\s*(.+?),\s*Algorithm:\s*(\w+)(?:,\s*Expected:\s*(\w+))?")
RE_EXPECT_TAG = re.compile(r"^--\s*@expect\s+(.*)$")
RE_FACTOR = re.compile(r"^--\s*Factors:\s*(.*)$")
RE_PARTITION = re.compile(r"^--\s*Partition:\s*(.*)$")
RE_PARTKEY = re.compile(r"^--\s*Target is partition key:\s*(True|False)", re.I)
# 判定行 ID：主判定就是用例 ID；子断言形如 <用例ID>#<断言名>
RE_VERDICT_ID = re.compile(r"^(TC-[A-Za-z0-9_.\-]+(?:#[A-Za-z0-9_]+)?)$")
RE_SUB_ASSERT = re.compile(r"^(TC-[^#]+)#([A-Za-z0-9_]+)$")

# 环境快照采集的变量（结果可复现性）
SNAPSHOT_VARS = [
    "version", "version_comment", "sql_mode", "sql_require_primary_key",
    "innodb_strict_mode", "innodb_default_row_format", "innodb_autoinc_lock_mode",
    "innodb_online_alter_log_max_size", "innodb_lock_wait_timeout", "lock_wait_timeout",
    "transaction_isolation", "autocommit", "character_set_server", "collation_server",
    "character_set_client", "collation_connection", "time_zone", "system_time_zone",
    "lower_case_table_names", "max_allowed_packet", "binlog_format", "log_bin",
    "foreign_key_checks", "unique_checks", "performance_schema",
]


# ============================================================
# Section 1: 文件发现（P0-1）
# ============================================================

def discover_sql_files(sql_dir):
    """返回 [(path, is_gz)]，同时匹配 .sql 与 .sql.gz，忽略 .bak / 隐藏文件。

    若同一编号同时存在 .sql 与 .sql.gz，优先使用 .sql（明文），并在返回的
    duplicates 中记录，避免同一批用例被执行两次。
    """
    if not os.path.isdir(sql_dir):
        return [], []
    entries = sorted(os.listdir(sql_dir))
    plain = [f for f in entries if f.endswith(".sql") and not f.endswith(".bak")]
    gz = [f for f in entries if f.endswith(".sql.gz")]
    gz_stems = {f[:-3] for f in gz}          # xxx.sql
    duplicates = sorted(gz_stems & set(plain))
    files = []
    for f in plain:
        files.append((os.path.join(sql_dir, f), False))
    for f in gz:
        if f[:-3] in set(plain):
            continue                          # 明文版优先，gz 跳过（已记入 duplicates）
        files.append((os.path.join(sql_dir, f), True))
    files.sort(key=lambda x: os.path.basename(x[0]))
    return files, duplicates


def open_sql(path, is_gz):
    if is_gz:
        return gzip.open(path, "rt", encoding="utf-8", errors="replace")
    return open(path, "r", encoding="utf-8", errors="replace")


def sha256_file(path, is_gz):
    """对**解压后**的内容求哈希，保证 .sql 与 .sql.gz 的同一份内容哈希一致。"""
    h = hashlib.sha256()
    with open_sql(path, is_gz) as fh:
        for chunk in iter(lambda: fh.read(1 << 20), ""):
            h.update(chunk.encode("utf-8", "replace"))
    return h.hexdigest()


# ============================================================
# Section 2: 用例切分与元数据解析（P0-4）
# ============================================================

class Case(object):
    __slots__ = ("test_id", "file", "idx", "text", "meta", "statements")

    def __init__(self, test_id, file, idx, text):
        self.test_id = test_id
        self.file = file
        self.idx = idx
        self.text = text
        self.meta = {}
        self.statements = []

    def __repr__(self):
        return "<Case %s #%d %s>" % (self.test_id, self.idx, os.path.basename(self.file))


def split_statements(text):
    """把一段 SQL 文本切成语句列表。

    引号/反引号感知，`--` 行注释与 `#` 注释剥离，空语句丢弃。
    生成器不使用 DELIMITER / 存储过程，因此无需处理复合语句。
    """
    stmts = []
    buf = []
    in_s = in_d = in_bt = False
    in_line_comment = False
    i = 0
    n = len(text)
    while i < n:
        ch = text[i]
        nxt = text[i + 1] if i + 1 < n else ""
        if in_line_comment:
            if ch == "\n":
                in_line_comment = False
                buf.append(ch)
            i += 1
            continue
        if not (in_s or in_d or in_bt):
            if ch == "-" and nxt == "-":
                in_line_comment = True
                i += 2
                continue
            if ch == "#":
                in_line_comment = True
                i += 1
                continue
        if ch == "'" and not (in_d or in_bt):
            if in_s and nxt == "'":
                buf.append("''"); i += 2; continue
            in_s = not in_s
        elif ch == '"' and not (in_s or in_bt):
            if in_d and nxt == '"':
                buf.append('""'); i += 2; continue
            in_d = not in_d
        elif ch == "`" and not (in_s or in_d):
            in_bt = not in_bt
        elif ch == "\\" and (in_s or in_d):
            buf.append(ch)
            if nxt:
                buf.append(nxt)
            i += 2
            continue
        if ch == ";" and not (in_s or in_d or in_bt):
            s = "".join(buf).strip()
            if s:
                stmts.append(s)
            buf = []
            i += 1
            continue
        buf.append(ch)
        i += 1
    tail = "".join(buf).strip()
    if tail:
        stmts.append(tail)
    return stmts


def parse_expect_tags(text):
    """解析 `-- @expect key=value ...` 机读期望（P0-7）。

    支持的 key:
      alter=SUCCESS|FAIL          ALTER 语句的期望结果
      errno=1846[,1845]           alter=FAIL 时允许的错误码集合
      build=SUCCESS|FAIL          建表期望（分区键类型不兼容时为 FAIL）
      column_type=smallint        ALTER 后 information_schema.column_type 期望
      nullable=YES|NO             ALTER 后 is_nullable 期望
      default=<str|NULL>          ALTER 后 column_default 期望
      rows=N                      最终 t1 行数期望
      negative=<probe_id>:errno   负向探针必须失败的错误码
      verdict=PASS|FAIL|MANUAL    兼容旧套件的显式判定
    """
    tags = {}
    for line in text.splitlines():
        m = RE_EXPECT_TAG.match(line)
        if not m:
            continue
        for kv in re.findall(r"(\w+)=((?:\[?[^\s\]]+\]?)|\"[^\"]*\")", m.group(1)):
            k, v = kv[0], kv[1].strip('"')
            tags.setdefault(k, []).append(v)
    return tags


def parse_case_meta(text):
    """从用例头注释解析元数据（type / algorithm / expected / factors / partition）。"""
    meta = {
        "type": "", "algorithm": "", "expected": "", "expected_norm": "",
        "factors": "", "partition": "", "partition_key": "", "title": "",
    }
    for line in text.splitlines():
        if not line.startswith("--"):
            if line.strip() and not line.startswith("--"):
                break
        m = RE_TYPE.match(line)
        if m:
            meta["type"] = m.group(1).strip()
            meta["algorithm"] = m.group(2).lower()
            if m.group(3):
                meta["expected"] = m.group(3).upper()
            continue
        m = RE_FACTOR.match(line)
        if m:
            meta["factors"] = m.group(1).strip()
            continue
        m = RE_PARTITION.match(line)
        if m:
            meta["partition"] = m.group(1).strip()
            continue
        m = RE_PARTKEY.match(line)
        if m:
            meta["partition_key"] = m.group(1).lower() == "true"
            continue
        if line.startswith("-- ") and not meta["title"] and ":" not in line[:12]:
            meta["title"] = line[3:].strip()
    meta["expected_norm"] = normalize_expected(meta["expected"])
    return meta


def normalize_expected(raw):
    """把 v2 里被错抓成 CREATE/BUILD/FAILS/'' 的期望值规范化（P0-7）。"""
    if not raw:
        return ""
    r = raw.strip().upper()
    if r in ("FAILS", "FAILED", "FAILURE", "ERROR"):
        return "FAIL"
    if r in ("SUCCEED", "SUCCEEDS", "OK"):
        return "SUCCESS"
    if r in ("CREATE", "BUILD", "MANUAL", "CHECK"):
        # v2 从 "-- Expected: CREATE OK, ALTER FAIL ..." 之类注释里错抓的词，
        # 不是合法期望值；标记为不可用，交由 @expect 标签提供。
        return ""
    return r


def split_cases(path, is_gz):
    """把 SQL 文件切成 (preamble, [Case])。preamble 是首个用例之前的文件头语句。"""
    with open_sql(path, is_gz) as fh:
        content = fh.read()
    lines = content.splitlines(True)
    chunks = []          # [(test_id or None, text)]
    cur_id = None
    cur = []
    for line in lines:
        m = RE_CASE.match(line.rstrip("\n"))
        if m:
            if cur:
                chunks.append((cur_id, "".join(cur)))
            cur_id = m.group(1)
            cur = [line]
        else:
            cur.append(line)
    if cur:
        chunks.append((cur_id, "".join(cur)))

    preamble = ""
    cases = []
    idx = 0
    for cid, text in chunks:
        if cid is None:
            preamble += text
            continue
        idx += 1
        c = Case(cid, path, idx, text)
        c.meta = parse_case_meta(text)
        c.meta["expect_tags"] = parse_expect_tags(text)
        c.statements = split_statements(text)
        cases.append(c)
    return preamble, cases


# ============================================================
# Section 3: manifest（P0-1b）
# ============================================================

MANIFEST_CACHE_PATH = os.path.join(RESULTS_DIR, ".manifest_cache.json")
_manifest_cache = None


def _load_manifest_cache():
    global _manifest_cache
    if _manifest_cache is None:
        try:
            with open(MANIFEST_CACHE_PATH) as fh:
                _manifest_cache = json.load(fh)
        except Exception:
            _manifest_cache = {}
    return _manifest_cache


def _save_manifest_cache():
    if _manifest_cache is None:
        return
    try:
        os.makedirs(RESULTS_DIR, exist_ok=True)
        tmp = MANIFEST_CACHE_PATH + ".tmp"
        with open(tmp, "w") as fh:
            json.dump(_manifest_cache, fh)
        os.replace(tmp, MANIFEST_CACHE_PATH)
    except Exception:
        pass


def build_manifest(files, use_cache=True):
    """构建 manifest。sha256 对**解压后内容**计算，故 .sql 与 .sql.gz 同一内容哈希一致。

    结果按 (size, mtime_ns) 缓存到 results/.manifest_cache.json，避免每次 dry-run
    都重新解压 15MB 的分区文件。
    """
    cache = _load_manifest_cache() if use_cache else {}
    items = []
    total = 0
    dirty = False
    for path, is_gz in files:
        st = os.stat(path)
        key = os.path.abspath(path)
        hit = cache.get(key)
        if hit and hit.get("size") == st.st_size and hit.get("mtime_ns") == st.st_mtime_ns:
            entry = dict(hit["entry"])
            entry["path"] = path
            entry["compressed"] = bool(is_gz)
            items.append(entry)
            total += entry["cases"]
            continue
        _pre, cases = split_cases(path, is_gz)
        ids = [c.test_id for c in cases]
        uniq = len(set(ids))
        entry = {
            "file": os.path.basename(path),
            "path": path,
            "compressed": bool(is_gz),
            "bytes_on_disk": st.st_size,
            "sha256_content": sha256_file(path, is_gz),
            "cases": len(cases),
            "unique_case_ids": uniq,
            "duplicate_case_ids": len(ids) - uniq,
            "statements": sum(len(c.statements) for c in cases),
        }
        items.append(entry)
        total += len(cases)
        cache[key] = {"size": st.st_size, "mtime_ns": st.st_mtime_ns,
                      "entry": {k: v for k, v in entry.items() if k != "path"}}
        dirty = True
    if dirty and use_cache:
        _save_manifest_cache()
    return {
        "generated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "file_count": len(items),
        "total_cases": total,
        "total_unique_case_ids": sum(i["unique_case_ids"] for i in items),
        "total_duplicate_case_ids": sum(i["duplicate_case_ids"] for i in items),
        "files": items,
    }


# ============================================================
# Section 4: 环境快照（P3-3）
# ============================================================

def connect(db_config, use_ssl=False):
    import pymysql
    kwargs = dict(
        host=db_config["host"], port=int(db_config["port"]),
        user=db_config["user"], password=db_config["password"],
        database=db_config["database"], charset="utf8mb4",
        autocommit=True, connect_timeout=15, read_timeout=3600, write_timeout=3600,
        local_infile=False,
    )
    return pymysql.connect(**kwargs)


def take_snapshot(db_config):
    snap = {"host": db_config["host"], "port": db_config["port"],
            "database": db_config["database"], "taken_at": time.strftime("%Y-%m-%d %H:%M:%S")}
    try:
        conn = connect(db_config)
    except Exception as e:
        snap["error"] = "%s: %s" % (type(e).__name__, e)
        return snap
    try:
        with conn.cursor() as cur:
            for v in SNAPSHOT_VARS:
                try:
                    cur.execute("SELECT @@%s" % v)
                    row = cur.fetchone()
                    snap[v] = row[0] if row else None
                except Exception as e:
                    conn.rollback() if not conn.get_autocommit() else None
                    snap[v] = "ERR:%s" % e
            try:
                cur.execute("SHOW VARIABLES LIKE 'innodb_version'")
                r = cur.fetchone()
                snap["innodb_version"] = r[1] if r else None
            except Exception:
                pass
    finally:
        conn.close()
    return snap


# ============================================================
# Section 5: 单用例执行（pymysql，逐语句错误归因）
# ============================================================

def execute_case_pymysql(case, conn, per_stmt_timeout=None):
    """执行一个用例的全部语句，返回 detail dict。

    任何一条语句报错都不会中断用例（等价于 mysql --force），但错误会被完整记录，
    并按用例归因（修复 v2 只留文件级 stderr 尾巴 2000 字符的问题）。
    """
    errors = []
    verdict_rows = []
    started = time.time()
    with conn.cursor() as cur:
        for si, stmt in enumerate(case.statements):
            t0 = time.time()
            try:
                cur.execute(stmt)
                if cur.description:
                    cols = [d[0] for d in cur.description]
                    rows = cur.fetchall()
                    for row in rows:
                        rec = dict(zip(cols, [None if v is None else v for v in row]))
                        first = row[0] if row else None
                        if isinstance(first, str) and RE_VERDICT_ID.match(first.strip()):
                            verdict_rows.append(rec)
                else:
                    conn.commit()
            except Exception as e:
                errno = getattr(e, "args", [None])[0]
                msg = str(e)
                errors.append({
                    "stmt_index": si,
                    "errno": errno if isinstance(errno, int) else None,
                    "error": msg[:500],
                    "statement": stmt[:300],
                    # 完整语句的短哈希：负向探针的期望值按哈希对账，
                    # 因此 65529 字节的长字面量被截断展示也不影响匹配
                    "stmt_sha1": hashlib.sha1(stmt.encode("utf-8")).hexdigest()[:12],
                    "duration_ms": int((time.time() - t0) * 1000),
                })
                try:
                    conn.rollback()
                except Exception:
                    pass
    return {
        "errors": errors,
        "verdict_rows": verdict_rows,
        "duration_ms": int((time.time() - started) * 1000),
        "statement_count": len(case.statements),
    }


def execute_case_cli(cases, preamble, path, is_gz, db_config, timeout):
    """回退路径：整文件（或子集）交给 mysql 客户端执行，解析 stdout 判定行。"""
    defaults_extra = os.environ.get("MYSQL_DEFAULTS_EXTRA_FILE")
    cmd = ["mysql"]
    if defaults_extra and os.path.exists(defaults_extra):
        cmd.append("--defaults-extra-file=%s" % defaults_extra)
    else:
        cmd += [f"--host={db_config['host']}", f"--port={db_config['port']}",
                f"--user={db_config['user']}"]
        if db_config.get("password"):
            cmd.append(f"--password={db_config['password']}")
    cmd += ["--default-character-set=utf8mb4", "--force", "--batch",
            "--skip-column-names", "--unbuffered", db_config["database"]]

    body = preamble + "".join(c.text for c in cases)
    try:
        proc = subprocess.run(cmd, input=body.encode("utf-8"), capture_output=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        return {}, "TIMEOUT after %ss" % timeout
    out = proc.stdout.decode("utf-8", "replace")
    err = proc.stderr.decode("utf-8", "replace")
    verdicts = {}
    for line in out.splitlines():
        parts = line.split("\t")
        if len(parts) >= 2 and RE_VERDICT_ID.match(parts[0].strip()):
            verdicts[parts[0].strip()] = {
                "result": parts[1].strip(),
                "mismatch": parts[2].strip() if len(parts) > 2 else "",
            }
    return verdicts, err


# ============================================================
# Section 6: 判定（P0-4 完整性 + P0-7 期望比对入口）
# ============================================================

MANUAL_RESULTS = ("BUILD_OR_ALTER_FAIL_EXPECTED", "BUILD_FAIL_EXPECTED", "ALTER_FAIL_EXPECTED")
KNOWN_RESULTS = ("PASS", "FAIL") + MANUAL_RESULTS


def collect_sql_assertions(verdict_rows):
    """把 SQL 判定行转成断言记录（<用例ID>#<断言名>）。"""
    out = []
    for row in verdict_rows:
        vals = list(row.values())
        aid = str(vals[0]).strip() if vals else ""
        m = RE_SUB_ASSERT.match(aid)
        name = m.group(2) if m else "PRIMARY"
        result = str(vals[1]).strip() if len(vals) > 1 and vals[1] is not None else ""
        mismatch = str(vals[2]).strip() if len(vals) > 2 and vals[2] is not None else ""
        out.append({"name": name, "assert_id": aid, "result": result,
                    "mismatch": mismatch[:600], "source": "sql"})
    return out


def check_negative_probes(case, errors):
    """P0-6：校验生成器声明的每条负向探针是否按预期被拒绝 / 被接受。

    声明格式（写在用例头 `-- @expect` 里）:
        neg_probe=<stmt_sha1>=1264|1406|167      STRICT: 该语句必须报错且 errno 在集合内
        neg_probe=<stmt_sha1>=ACCEPTED           非 STRICT: 该语句必须**不**报错
    """
    specs = case.meta.get("expect_tags", {}).get("neg_probe") or []
    out = []
    for i, spec in enumerate(specs, start=1):
        sha, _, want = spec.partition("=")
        matched = [e for e in errors if e.get("stmt_sha1") == sha]
        if want == "ACCEPTED":
            ok = not matched
            detail = ("probe should have been accepted (non-strict truncation) but errored: errno=%s %s"
                      % (matched[0].get("errno"), matched[0].get("error"))) if matched else ""
        else:
            allowed = {int(x) for x in want.split("|") if x.strip().lstrip("-").isdigit()}
            if not matched:
                ok = False
                detail = ("over-limit value was SILENTLY ACCEPTED in STRICT mode "
                          "(no error for probe sha=%s)" % sha)
            else:
                got = matched[0].get("errno")
                ok = got in allowed
                detail = "" if ok else ("probe errno=%s not in declared %s" % (got, sorted(allowed)))
        out.append({"name": "NEG_ERRNO#%d" % i,
                    "assert_id": "%s#NEG_ERRNO%d" % (case.test_id, i),
                    "result": "PASS" if ok else "FAIL",
                    "mismatch": detail[:600], "source": "runner"})
    return out


def check_alter_outcome(case, errors):
    """P0-7 的核心：把用例声明的 ALTER 期望与实际结果对上。

    生成器声明 `@expect alter=SUCCESS|FAIL alter_sha=<sha> errno=[...]`；
    执行器按 sha 在错误记录里找那条 ALTER：
      alter=SUCCESS -> 该 sha 必须**没有**报错
      alter=FAIL    -> 该 sha 必须报错，且 errno 在声明集合内
    旧执行器只是把 expected 写进 CSV，从不比对，所以"0 FAIL"仅代表
    "产出了判定行的用例里数据对照没发现差异"。
    """
    tags = case.meta.get("expect_tags", {})
    shas = set(tags.get("alter_sha") or [])
    want = (tags.get("alter") or [None])[0]
    if not shas or not want:
        return [], None
    matched = [e for e in errors if e.get("stmt_sha1") in shas]
    # alter=SUCCESS -> 声明的所有 ALTER 都不能报错
    # alter=FAIL    -> 至少一条报错且 errno 在声明集合内
    actual = "FAIL" if matched else "SUCCESS"
    actual_errno = matched[0].get("errno") if matched else None
    want = want.upper()
    ok = (actual == want)
    detail = ""
    if not ok:
        detail = ("ALTER declared %s but actually %s%s"
                  % (want, actual,
                     (" (errno=%s %s)" % (actual_errno, (matched[0].get("error") or "")[:120]))
                     if matched else " (statement succeeded)"))
    elif want == "FAIL":
        allowed = set()
        for spec in tags.get("errno") or []:
            allowed |= {int(x) for x in spec.strip("[]").split(",") if x.strip().lstrip("-").isdigit()}
        if allowed and actual_errno not in allowed:
            ok = False
            detail = ("ALTER failed as declared but errno=%s not in %s: %s"
                      % (actual_errno, sorted(allowed), (matched[0].get("error") or "")[:150]))
    return [{"name": "ALTER_OUTCOME",
             "assert_id": "%s#ALTER_OUTCOME" % case.test_id,
             "result": "PASS" if ok else "FAIL",
             "mismatch": detail[:600], "source": "runner"}], actual_errno


def _declared_alter_shas(case):
    return set(case.meta.get("expect_tags", {}).get("alter_sha") or [])


def _alter_actual(case, errors):
    if not _declared_alter_shas(case):
        return ""
    shas = _declared_alter_shas(case)
    return "FAIL" if any(e.get("stmt_sha1") in shas for e in errors) else "SUCCESS"


def _alter_errno(case, errors):
    shas = _declared_alter_shas(case)
    return next((e.get("errno") for e in errors if e.get("stmt_sha1") in shas), None)


def aggregate(assertions):
    """聚合断言：任一 FAIL => FAIL；否则任一 MANUAL => MANUAL；否则任一未知 => UNKNOWN；全 PASS => PASS。"""
    if not assertions:
        return None, "", ""
    results = [a["result"] for a in assertions]
    if any(r == "FAIL" for r in results):
        status = "FAIL"
    elif any(r in MANUAL_RESULTS for r in results):
        status = "MANUAL"
    elif any(r not in KNOWN_RESULTS for r in results):
        status = "UNKNOWN"
    else:
        status = "PASS"
    failing = [a for a in assertions if a["result"] != "PASS"] or assertions
    mismatch = " | ".join("%s=%s%s" % (a["name"], a["result"],
                                       (": " + a["mismatch"]) if a["mismatch"] else "")
                          for a in failing)
    return status, failing[0]["result"], mismatch


def classify_case(case, detail):
    """把一个用例的执行明细收敛成 status/result/assertions。

    v3 语义:
      PASS     全部断言 PASS，且 SQL 断言条数与用例声明一致
      FAIL     任一断言 FAIL
      MANUAL   无断言 FAIL，但存在"需人工确认"的常量断言（P0-3 修复后应为 0）
      ERROR    有语句报错 / 断言缺失，没有可用判定
      MISSING  用例根本没被执行
    """
    verdict_rows = detail.get("verdict_rows") or []
    errors = detail.get("errors") or []
    assertions = collect_sql_assertions(verdict_rows)

    # 断言条数完整性：只数 SQL 产出的判定行（runner 合成的负向探针校验另计）
    want = case.meta.get("expect_tags", {}).get("assertions")
    if want:
        try:
            want_n = int(want[0])
        except (TypeError, ValueError):
            want_n = None
        if want_n is not None and len(assertions) != want_n:
            got = [a["name"] for a in assertions]
            return ("ERROR", "ASSERTION_COUNT",
                    "expected %d assertion rows, got %d %s（某条断言未产出，"
                    "通常是该断言语句本身报错）" % (want_n, len(assertions), got),
                    assertions, errors)

    assertions += check_negative_probes(case, errors)
    alter_asserts, actual_errno = check_alter_outcome(case, errors)
    assertions += alter_asserts
    status, result, mismatch = aggregate(assertions)
    if status is not None:
        return status, result, mismatch, assertions, errors
    if errors:
        first = errors[0]
        return ("ERROR", "NO_VERDICT",
                "errno=%s %s | stmt#%d: %s" % (first.get("errno"), first.get("error"),
                                               first.get("stmt_index"), first.get("statement")),
                assertions, errors)
    return ("ERROR", "NO_VERDICT",
            "no verdict row and no statement error (empty case?)", assertions, errors)


# ============================================================
# Section 7: 运行编排
# ============================================================

class Runner(object):
    def __init__(self, db_config, env, out_dir, workers=1, retry=2,
                 use_cli=False, cli_timeout=7200, resume=False, verbose=True):
        self.db_config = db_config
        self.env = env
        self.out_dir = out_dir
        self.workers = max(1, int(workers))
        self.retry = max(0, int(retry))
        self.use_cli = use_cli
        self.cli_timeout = cli_timeout
        self.resume = resume
        self.verbose = verbose
        self.lock = threading.Lock()
        self.results = []
        self.done_ids = set()
        self.counters = {"PASS": 0, "FAIL": 0, "ERROR": 0, "MANUAL": 0,
                         "UNKNOWN": 0, "MISSING": 0, "SKIPPED": 0}
        self.jsonl_path = os.path.join(out_dir, "details_%s.jsonl" % env)
        self.state_path = os.path.join(out_dir, "state_%s.json" % env)
        self.failures_path = os.path.join(out_dir, "failures_%s.log" % env)
        self._jsonl = None
        self._local = threading.local()

    # ---- resume -------------------------------------------------
    def load_resume_state(self):
        if not self.resume:
            return
        if os.path.exists(self.state_path):
            try:
                with open(self.state_path) as fh:
                    self.done_ids = set(json.load(fh).get("completed_case_ids", []))
                if self.verbose:
                    print("  [resume] %d 个用例已完成，将跳过" % len(self.done_ids))
            except Exception as e:
                print("  [resume] 状态文件不可用 (%s)，忽略" % e)

    def _append_state(self, case_id):
        self.done_ids.add(case_id)

    def flush_state(self):
        with open(self.state_path, "w") as fh:
            json.dump({"env": self.env, "updated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
                       "completed_case_ids": sorted(self.done_ids)}, fh)

    # ---- connection pool (one per worker thread) ----------------
    def conn(self):
        c = getattr(self._local, "conn", None)
        if c is None:
            c = connect(self.db_config)
            self._local.conn = c
        try:
            c.ping(reconnect=True)
        except Exception:
            try:
                c.close()
            except Exception:
                pass
            c = connect(self.db_config)
            self._local.conn = c
        return c

    # ---- single case with retry ---------------------------------
    def run_one(self, case):
        attempt = 0
        last_exc = None
        while attempt <= self.retry:
            attempt += 1
            try:
                conn = self.conn()
                detail = execute_case_pymysql(case, conn)
                break
            except Exception as e:      # 连接级故障：重连重试
                last_exc = e
                try:
                    self._local.conn.close()
                except Exception:
                    pass
                self._local.conn = None
                if attempt > self.retry:
                    detail = {"errors": [{"stmt_index": -1, "errno": None,
                                          "error": "CONNECTION: %s: %s" % (type(e).__name__, e),
                                          "statement": "", "duration_ms": 0}],
                              "verdict_rows": [], "duration_ms": 0, "statement_count": len(case.statements)}
                else:
                    time.sleep(min(5 * attempt, 15))
        status, result, mismatch, assertions, errors = classify_case(case, detail)
        rec = {
            "test_id": case.test_id,
            "file": os.path.basename(case.file),
            "case_index": case.idx,
            "type": case.meta.get("type", ""),
            "algorithm": case.meta.get("algorithm", ""),
            "expected": case.meta.get("expected_norm", "") or case.meta.get("expected", ""),
            "expect_tags": case.meta.get("expect_tags", {}),
            "factors": case.meta.get("factors", ""),
            "partition": case.meta.get("partition", ""),
            "partition_key": case.meta.get("partition_key", ""),
            "result": result,
            "status": status,
            "mismatch": mismatch[:1000],
            "assertions": assertions,
            "assertion_count": len(assertions),
            "alter_expected": (case.meta.get("expect_tags", {}).get("alter") or [""])[0],
            "alter_actual": _alter_actual(case, errors),
            "alter_errno": _alter_errno(case, errors),
            "statement_count": detail.get("statement_count", 0),
            "duration_ms": detail.get("duration_ms", 0),
            "error_count": len(errors),
            "errors": errors[:20],
            "attempts": attempt,
        }
        with self.lock:
            self.results.append(rec)
            self.counters[status] = self.counters.get(status, 0) + 1
            self._append_state(case.test_id)
            if self._jsonl:
                self._jsonl.write(json.dumps(rec, ensure_ascii=False, default=str) + "\n")
                self._jsonl.flush()
            if status in ("FAIL", "ERROR", "UNKNOWN", "MISSING"):
                with open(self.failures_path, "a", encoding="utf-8") as flog:
                    flog.write("\n" + "=" * 70 + "\n")
                    flog.write("Test ID : %s  (%s #%d)\n" % (rec["test_id"], rec["file"], rec["case_index"]))
                    flog.write("Type    : %s | Algorithm: %s | Expected: %s\n"
                               % (rec["type"], rec["algorithm"], rec["expected"]))
                    flog.write("Factors : %s\n" % rec["factors"])
                    flog.write("Status  : %s | Result: %s\n" % (status, result))
                    flog.write("Mismatch: %s\n" % rec["mismatch"])
                    for e in errors[:10]:
                        flog.write("  errno=%s stmt#%d: %s\n      SQL: %s\n"
                                   % (e.get("errno"), e.get("stmt_index"), e.get("error"), e.get("statement")))
        return rec

    # ---- file level ---------------------------------------------
    def run_file(self, path, is_gz, case_filter=None, sample=0):
        fname = os.path.basename(path)
        preamble, cases = split_cases(path, is_gz)
        ids = [c.test_id for c in cases]
        uniq = set(ids)
        if len(ids) != len(uniq):
            dups = sorted({i for i in uniq if ids.count(i) > 1})
            print("  !! %s: %d 个用例 ID 重复（示例 %s）—— 结果无法按算法归因，"
                  "完整性核算会低估未执行数" % (fname, len(dups), dups[:3]))

        selected = cases
        if case_filter:
            rx = re.compile(case_filter)
            selected = [c for c in cases if rx.search(c.test_id) or rx.search(c.meta.get("type", ""))]
        if sample and sample > 1:
            selected = selected[::sample]
        if self.resume:
            before = len(selected)
            selected = [c for c in selected if c.test_id not in self.done_ids]
            self.counters["SKIPPED"] += before - len(selected)

        print("  Running: %-42s %s cases=%d selected=%d" %
              (fname, "[gz]" if is_gz else "    ", len(cases), len(selected)), flush=True)
        t0 = time.time()
        open(self.failures_path, "a", encoding="utf-8").write(
            "\n\n########## FILE %s (%s) ##########\n" % (fname, time.strftime("%Y-%m-%d %H:%M:%S")))

        if self.use_cli:
            verdicts, stderr = execute_case_cli(selected, preamble, path, is_gz,
                                                self.db_config, self.cli_timeout)
            if stderr.strip():
                with open(self.failures_path, "a", encoding="utf-8") as flog:
                    flog.write("\n--- mysql CLI stderr (full) ---\n%s\n" % stderr)
            for c in selected:
                v = verdicts.get(c.test_id)
                if v is None:
                    detail = {"errors": [{"stmt_index": -1, "errno": None,
                                          "error": "NO_OUTPUT in CLI mode (see failures log stderr)",
                                          "statement": "", "duration_ms": 0}],
                              "verdict_rows": [], "duration_ms": 0,
                              "statement_count": len(c.statements)}
                else:
                    detail = {"errors": [], "duration_ms": 0, "statement_count": len(c.statements),
                              "verdict_rows": [{"test_id": c.test_id, "result": v["result"],
                                                "mismatch": v["mismatch"]}]}
                self.run_one_with_detail(c, detail)
        else:
            if self.workers <= 1:
                for c in selected:
                    self.run_one(c)
            else:
                with ThreadPoolExecutor(max_workers=self.workers) as ex:
                    futs = [ex.submit(self.run_one, c) for c in selected]
                    done = 0
                    for _ in as_completed(futs):
                        done += 1
                        if self.verbose and done % 500 == 0:
                            print("      ... %d/%d" % (done, len(selected)), flush=True)

        # 完整性核算（P0-4）：被选中的用例必须全部产出判定
        produced = {r["test_id"] for r in self.results if r["file"] == fname}
        missing = [c.test_id for c in selected if c.test_id not in produced]
        for cid in missing:
            rec = {"test_id": cid, "file": fname, "case_index": -1, "type": "", "algorithm": "",
                   "expected": "", "expect_tags": {}, "factors": "", "partition": "",
                   "partition_key": "", "result": "NOT_EXECUTED", "status": "MISSING",
                   "mismatch": "case selected but produced no record (runner bug / crash)",
                   "statement_count": 0, "duration_ms": 0, "error_count": 0,
                   "errors": [], "verdict_rows": [], "attempts": 0}
            self.results.append(rec)
            self.counters["MISSING"] += 1
        elapsed = time.time() - t0
        print("      done in %.1fs  (missing=%d)" % (elapsed, len(missing)), flush=True)
        return len(cases), len(selected), missing

    def run_one_with_detail(self, case, detail):
        status, result, mismatch, assertions, errors = classify_case(case, detail)
        rec = {"test_id": case.test_id, "file": os.path.basename(case.file), "case_index": case.idx,
               "type": case.meta.get("type", ""), "algorithm": case.meta.get("algorithm", ""),
               "expected": case.meta.get("expected_norm", "") or case.meta.get("expected", ""),
               "expect_tags": case.meta.get("expect_tags", {}), "factors": case.meta.get("factors", ""),
               "partition": case.meta.get("partition", ""), "partition_key": case.meta.get("partition_key", ""),
               "result": result, "status": status, "mismatch": mismatch[:1000],
               "assertions": assertions, "assertion_count": len(assertions),
               "statement_count": detail.get("statement_count", 0), "duration_ms": detail.get("duration_ms", 0),
               "error_count": len(errors), "errors": errors[:20],
               "attempts": 1}
        with self.lock:
            self.results.append(rec)
            self.counters[status] = self.counters.get(status, 0) + 1
            self._append_state(case.test_id)
            if self._jsonl:
                self._jsonl.write(json.dumps(rec, ensure_ascii=False, default=str) + "\n")
                self._jsonl.flush()
        return rec


# ============================================================
# Section 8: main
# ============================================================

def resolve_sql_dir(env, sql_dir_override):
    if sql_dir_override:
        return sql_dir_override
    return SQL_ALIYUN if env == "aliyun" else SQL_INTERNAL


def select_files(files_arg, all_files, sql_dir):
    if not files_arg:
        return list(all_files)
    wanted = set()
    for f in files_arg:
        b = os.path.basename(f)
        wanted.add(b)
        if not b.endswith(".gz"):
            wanted.add(b + ".gz")
        if b.endswith(".sql.gz"):
            wanted.add(b[:-3])
    picked = [(p, g) for p, g in all_files if os.path.basename(p) in wanted]
    found = {os.path.basename(p) for p, _ in picked}
    missing = []
    for f in files_arg:
        b = os.path.basename(f)
        cand = {b, b + ".gz"}
        if b.endswith(".gz"):
            cand.add(b[:-3])
        if not (cand & found):
            missing.append(f)
    for m in dict.fromkeys(missing):
        print("  !! 指定的文件在 %s 中不存在（.sql / .sql.gz 都没有）: %s" % (sql_dir, m))
    return picked


def write_outputs(runner, env, manifest, snapshot, out_dir):
    """写结果。summary_<env>.csv 是"最近一次"，同时把本轮结果**带时间戳归档**，
    历史证据永不被覆盖（v2 执行器会直接覆盖 summary_<env>.csv，已造成一次证据丢失）。
    """
    os.makedirs(out_dir, exist_ok=True)
    archive_dir = os.path.join(out_dir, "archive")
    os.makedirs(archive_dir, exist_ok=True)
    stamp = time.strftime("%Y%m%d_%H%M%S")
    csv_path = os.path.join(out_dir, "summary_%s.csv" % env)
    archive_csv = os.path.join(archive_dir, "summary_%s_%s.csv" % (env, stamp))
    cols = ["test_id", "file", "case_index", "type", "algorithm", "expected",
            "alter_expected", "alter_actual", "alter_errno", "result",
            "status", "assertion_count", "assertions", "error_count", "duration_ms",
            "mismatch", "factors", "partition", "partition_key"]
    ordered = sorted(runner.results, key=lambda x: (x["file"], x["case_index"], x["test_id"]))
    for target in (csv_path, archive_csv):
        with open(target, "w", newline="", encoding="utf-8") as fh:
            w = csv.DictWriter(fh, fieldnames=cols, extrasaction="ignore")
            w.writeheader()
            for r in ordered:
                row = dict(r)
                row["assertions"] = ";".join("%s=%s" % (a["name"], a["result"])
                                             for a in (r.get("assertions") or []))
                w.writerow(row)
    # 本轮详情/失败日志同样归档一份
    for src_name in ("details_%s.jsonl" % env, "failures_%s.log" % env,
                     "env_snapshot_%s.json" % env):
        src = os.path.join(out_dir, src_name)
        if os.path.exists(src):
            base, ext = os.path.splitext(src_name)
            shutil.copyfile(src, os.path.join(archive_dir, "%s_%s%s" % (base, stamp, ext)))
    # 注意: 全量基线 manifest_<env>.json 由 main() 写入且**不可**被本轮结果覆盖，
    # 否则 --files 局部运行会把基线污染成子集（已在 Step1 复现并修复）。
    with open(os.path.join(out_dir, "run_manifest_%s.json" % env), "w", encoding="utf-8") as fh:
        json.dump(manifest, fh, ensure_ascii=False, indent=2)
    with open(os.path.join(out_dir, "env_snapshot_%s.json" % env), "w", encoding="utf-8") as fh:
        json.dump(snapshot, fh, ensure_ascii=False, indent=2, default=str)
    runner.flush_state()
    print("  archive  %s" % archive_csv)
    return csv_path


def main():
    ap = argparse.ArgumentParser(description="RDS MySQL DDL Test Runner v3")
    ap.add_argument("--config", default=os.path.join(OUTPUT_DIR, "config.ini"))
    ap.add_argument("--env", choices=["aliyun", "internal", "local", "both"], default="aliyun")
    ap.add_argument("--files", nargs="*", help="只跑指定文件（.sql 或 .sql.gz 均可）")
    ap.add_argument("--sql-dir", help="覆盖 SQL 目录（自检/临时套件用）")
    ap.add_argument("--out-dir", default=RESULTS_DIR)
    ap.add_argument("--workers", type=int, default=1, help="并发执行用例的线程数（默认 1）")
    ap.add_argument("--retry", type=int, default=2, help="连接级故障重试次数")
    ap.add_argument("--resume", action="store_true", help="跳过 state 文件里已完成的用例")
    ap.add_argument("--case-filter", help="按 test_id / type 正则筛选用例")
    ap.add_argument("--sample", type=int, default=0, help="每 N 个用例取 1 个（快速冒烟）")
    ap.add_argument("--dry-run", action="store_true", help="只生成 manifest 与用例统计，不连库")
    ap.add_argument("--manifest", help="把 manifest 写到指定路径")
    ap.add_argument("--check-manifest", help="与已有 manifest 对账（文件清单/用例数/内容哈希）")
    ap.add_argument("--use-cli", action="store_true", help="回退到 mysql 客户端整文件执行")
    ap.add_argument("--cli-timeout", type=int, default=7200)
    args = ap.parse_args()

    envs = ["aliyun", "internal"] if args.env == "both" else [args.env]

    for env in envs:
        sql_dir = resolve_sql_dir(env, args.sql_dir)
        print("\n" + "=" * 72)
        print("ENV=%s  SQL_DIR=%s" % (env, sql_dir))
        print("=" * 72)
        all_discovered, dups = discover_sql_files(sql_dir)
        if dups:
            print("  NOTE: 同时存在明文与压缩版本，优先使用明文: %s" % ", ".join(dups))
        files = select_files(args.files, all_discovered, sql_dir)
        if not all_discovered:
            print("  没有找到任何 SQL 文件（.sql / .sql.gz）")
            continue

        # 全量基线 manifest（与 --files 无关），用于跨轮次对账
        full_manifest = build_manifest(all_discovered)
        os.makedirs(args.out_dir, exist_ok=True)
        full_man_path = os.path.join(args.out_dir, "manifest_%s.json" % env)
        with open(full_man_path, "w", encoding="utf-8") as fh:
            json.dump(full_manifest, fh, ensure_ascii=False, indent=2)
        if not files:
            print("  --files 指定的文件都不存在，未执行任何用例")
            continue

        manifest = build_manifest(files)
        print("\n  发现 %d 个文件，%d 个用例（唯一 ID %d，重复 %d）"
              % (manifest["file_count"], manifest["total_cases"],
                 manifest["total_unique_case_ids"], manifest["total_duplicate_case_ids"]))
        for it in manifest["files"]:
            flag = " [gz]" if it["compressed"] else ""
            dup = " DUP_ID=%d" % it["duplicate_case_ids"] if it["duplicate_case_ids"] else ""
            print("    %-44s%s cases=%-6d sha=%s%s"
                  % (it["file"], flag, it["cases"], it["sha256_content"][:12], dup))

        man_path = args.manifest or os.path.join(args.out_dir, "run_manifest_%s.json" % env)
        if args.check_manifest:
            if not os.path.exists(args.check_manifest):
                print("  !! --check-manifest 指定的文件不存在: %s" % args.check_manifest)
                sys.exit(2)
            with open(args.check_manifest) as fh:
                old = json.load(fh)
            diffs = []
            oldmap = {i["file"]: i for i in old.get("files", [])}
            for it in full_manifest["files"]:
                o = oldmap.get(it["file"])
                if o is None:
                    diffs.append("%s: 新增文件" % it["file"])
                elif o["sha256_content"] != it["sha256_content"]:
                    diffs.append("%s: 内容变化 sha %s -> %s (cases %s -> %s)"
                                 % (it["file"], o["sha256_content"][:12], it["sha256_content"][:12],
                                    o["cases"], it["cases"]))
            for f in oldmap:
                if f not in {i["file"] for i in full_manifest["files"]}:
                    diffs.append("%s: 已消失" % f)
            if old.get("total_cases") != full_manifest["total_cases"]:
                diffs.append("总用例数 %s -> %s" % (old.get("total_cases"), full_manifest["total_cases"]))
            if diffs:
                print("\n  !! MANIFEST 对账不一致（%d 项）:" % len(diffs))
                for d in diffs:
                    print("     - %s" % d)
                print("     => 已归档结果与当前 SQL 不匹配，历史报告结论不可直接引用")
            else:
                print("\n  MANIFEST 对账一致 ✅")

        with open(man_path, "w", encoding="utf-8") as fh:
            json.dump(manifest, fh, ensure_ascii=False, indent=2)
        print("  全量基线 manifest: %s (%d 文件 / %d 用例)"
              % (full_man_path, full_manifest["file_count"], full_manifest["total_cases"]))

        if args.dry_run:
            print("\n  [dry-run] manifest 已写入 %s，未连接数据库" % man_path)
            continue

        config = configparser.ConfigParser()
        if not os.path.exists(args.config):
            print("  Config file not found: %s" % args.config)
            sys.exit(1)
        config.read(args.config)
        if env not in config:
            print("  Error: config 里没有 [%s] 段" % env)
            continue
        db_config = {
            "host": config[env].get("host", "127.0.0.1"),
            "port": str(config[env].get("port", 3306)),
            "user": config[env].get("user", "root"),
            "password": os.environ.get("MYSQL_PWD") or config[env].get("password", ""),
            "database": config[env].get("database", "ddl_test"),
        }

        print("\n  采集环境快照 ...")
        snapshot = take_snapshot(db_config)
        if snapshot.get("error"):
            print("  !! 无法连接: %s" % snapshot["error"])
            continue
        print("     server=%s  sql_mode=%s" % (snapshot.get("version"), snapshot.get("sql_mode")))
        with open(os.path.join(args.out_dir, "env_snapshot_%s.json" % env), "w", encoding="utf-8") as fh:
            json.dump(snapshot, fh, ensure_ascii=False, indent=2, default=str)

        runner = Runner(db_config, env, args.out_dir, workers=args.workers, retry=args.retry,
                        use_cli=args.use_cli, cli_timeout=args.cli_timeout, resume=args.resume)
        runner.load_resume_state()
        runner._jsonl = open(runner.jsonl_path, "a" if args.resume else "w", encoding="utf-8")
        open(runner.failures_path, "a" if args.resume else "w", encoding="utf-8").close()
        try:
            total_missing = 0
            for path, is_gz in files:
                _c, _s, missing = runner.run_file(path, is_gz, args.case_filter, args.sample)
                total_missing += len(missing)
        finally:
            if runner._jsonl:
                runner._jsonl.close()

        csv_path = write_outputs(runner, env, manifest, snapshot, args.out_dir)
        print("\n" + "=" * 72)
        print("SUMMARY (%s)" % env)
        print("=" * 72)
        for k in ("PASS", "FAIL", "ERROR", "MANUAL", "UNKNOWN", "MISSING", "SKIPPED"):
            print("  %-8s %d" % (k, runner.counters.get(k, 0)))
        print("  total    %d" % len(runner.results))
        print("  csv      %s" % csv_path)
        print("  details  %s" % runner.jsonl_path)
        print("  failures %s" % runner.failures_path)
        if total_missing:
            print("  !! 完整性核算: %d 个用例未产出结果" % total_missing)
            sys.exit(3)
        bad = runner.counters["FAIL"] + runner.counters["ERROR"] + \
            runner.counters["UNKNOWN"] + runner.counters["MISSING"]
        if bad:
            sys.exit(1)


if __name__ == "__main__":
    main()
