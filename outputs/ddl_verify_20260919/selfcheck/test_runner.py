#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Step 1 (P0-1) 自检：执行器的文件发现 / 用例切分 / manifest / 完整性核算。

运行:  python3 -m pytest selfcheck/test_runner.py -v
不连数据库，全部为纯本地静态验证。
"""
import os
import sys
import gzip
import json
import shutil
import textwrap

import re as _re

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)

import run_tests as R  # noqa: E402

ALIYUN = os.path.join(ROOT, "sql_aliyun")
INTERNAL = os.path.join(ROOT, "sql_internal")

SAMPLE_CASE = """-- Test Case: TC-X0001
-- Type: TINYINT -> SMALLINT, Algorithm: instant, Expected: SUCCESS
-- Factors: data_scale=S100, sql_mode=STRICT
-- @expect alter=SUCCESS column_type=smallint nullable=YES
DROP TABLE IF EXISTS t1_x, t2_x;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_x (id INT AUTO_INCREMENT PRIMARY KEY, target TINYINT) ENGINE=InnoDB;
INSERT INTO t1_x (target) VALUES ('a;b'), (NULL);
ALTER TABLE t1_x MODIFY target SMALLINT, ALGORITHM=instant;
SELECT 'TC-X0001' AS test_id, IF(COUNT(*)=0,'PASS','FAIL') AS result, '' AS mismatch FROM t1_x;
"""


def _write(path, text, compress=False):
    if compress:
        with gzip.open(path, "wt", encoding="utf-8") as fh:
            fh.write(text)
    else:
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(text)


# ---------------------------------------------------------------- discovery

def test_discover_finds_all_files_whatever_the_extension():
    """P0-1 核心：不管生成器把文件写成 .sql 还是 .sql.gz，都必须被发现，一个不漏。"""
    for d, expect in ((ALIYUN, 12), (INTERNAL, 15)):
        files, dups = R.discover_sql_files(d)
        names = [os.path.basename(p) for p, _ in files]
        on_disk = [f for f in os.listdir(d)
                   if f.endswith(".sql") or f.endswith(".sql.gz")]
        assert len(files) == expect == len(on_disk), (d, names, on_disk)
        assert dups == []
        # 分区大文件必然是 gz，用来证明 gz 分支真的被走到
        assert any(n.startswith("12_") and n.endswith(".gz") for n in names) \
            if d == ALIYUN else True
        assert all(os.path.exists(p) for p, _ in files)


def test_discover_prefers_plain_over_gz(tmp_path):
    d = tmp_path / "sql"
    d.mkdir()
    _write(str(d / "a.sql"), SAMPLE_CASE)
    _write(str(d / "a.sql.gz"), SAMPLE_CASE, compress=True)
    _write(str(d / "b.sql.gz"), SAMPLE_CASE, compress=True)
    files, dups = R.discover_sql_files(str(d))
    names = [os.path.basename(p) for p, _ in files]
    assert names == ["a.sql", "b.sql.gz"]
    assert dups == ["a.sql"]


def test_discover_ignores_bak(tmp_path):
    d = tmp_path / "sql"
    d.mkdir()
    _write(str(d / "a.sql"), SAMPLE_CASE)
    _write(str(d / "a.sql.bak"), SAMPLE_CASE)
    files, _ = R.discover_sql_files(str(d))
    assert [os.path.basename(p) for p, _ in files] == ["a.sql"]


# ---------------------------------------------------------------- splitting

def test_split_cases_reads_gz():
    path = os.path.join(ALIYUN, "07_varchar_instant.sql.gz")
    pre, cases = R.split_cases(path, True)
    assert len(cases) == 279
    assert all(c.test_id.startswith("TC-") for c in cases)
    assert cases[0].meta["algorithm"] == "instant"
    assert "VARCHAR" in cases[0].meta["type"]


def test_split_cases_meta_and_statements(tmp_path):
    p = tmp_path / "s.sql"
    _write(str(p), "SET SESSION sql_mode='';\n" + SAMPLE_CASE + SAMPLE_CASE.replace("X0001", "X0002"))
    pre, cases = R.split_cases(str(p), False)
    assert "SET SESSION sql_mode" in pre
    assert [c.test_id for c in cases] == ["TC-X0001", "TC-X0002"]
    c = cases[0]
    assert c.meta["type"] == "TINYINT -> SMALLINT"
    assert c.meta["algorithm"] == "instant"
    assert c.meta["expected_norm"] == "SUCCESS"
    assert c.meta["factors"].startswith("data_scale=")
    assert c.meta["expect_tags"]["alter"] == ["SUCCESS"]
    assert c.meta["expect_tags"]["column_type"] == ["smallint"]
    assert len(c.statements) == 6
    assert not any(s.startswith("--") for s in c.statements)


def test_split_statements_semicolon_in_string_and_comments():
    sql = textwrap.dedent("""
        -- leading comment
        CREATE TABLE t (a VARCHAR(10) DEFAULT 'x;y', b INT);  # trailing comment
        INSERT INTO t VALUES ('it''s;ok', 1);
        INSERT INTO t VALUES ("dq;sq", 2);
        SELECT `we;ird` FROM t;
    """)
    stmts = R.split_statements(sql)
    assert len(stmts) == 4
    assert "'x;y'" in stmts[0]
    assert "it''s;ok" in stmts[1]
    assert "dq;sq" in stmts[2]
    assert "`we;ird`" in stmts[3]


def test_split_statements_backslash_escape():
    stmts = R.split_statements(r"INSERT INTO t VALUES ('a\';b', 1); SELECT 1;")
    assert len(stmts) == 2


# ---------------------------------------------------------------- expectations

@pytest.mark.parametrize("raw,exp", [
    ("SUCCESS", "SUCCESS"), ("FAIL", "FAIL"), ("FAILS", "FAIL"),
    ("FAILED", "FAIL"), ("SUCCEED", "SUCCESS"), ("OK", "SUCCESS"),
    ("CREATE", ""), ("BUILD", ""), ("MANUAL", ""), ("", ""),
])
def test_normalize_expected(raw, exp):
    assert R.normalize_expected(raw) == exp


def test_parse_expect_tags_multi():
    text = ("-- @expect alter=FAIL errno=[1846,1845] build=SUCCESS\n"
            "-- @expect column_type=\"varchar(16383)\" nullable=NO default=NULL\n"
            "-- @expect negative=probe1:1265 verdict=PASS\n")
    tags = R.parse_expect_tags(text)
    assert tags["alter"] == ["FAIL"]
    assert tags["errno"] == ["[1846,1845]"]
    assert tags["column_type"] == ["varchar(16383)"]
    assert tags["nullable"] == ["NO"]
    assert tags["default"] == ["NULL"]
    assert tags["negative"] == ["probe1:1265"]


# ---------------------------------------------------------------- manifest

def test_manifest_sha_identical_for_plain_and_gz(tmp_path):
    d = tmp_path / "sql"
    d.mkdir()
    _write(str(d / "a.sql"), SAMPLE_CASE)
    _write(str(d / "b.sql.gz"), SAMPLE_CASE, compress=True)
    files, _ = R.discover_sql_files(str(d))
    man = R.build_manifest(files, use_cache=False)
    shas = {i["file"]: i["sha256_content"] for i in man["files"]}
    assert shas["a.sql"] == shas["b.sql.gz"]
    assert man["total_cases"] == 2


def test_manifest_detects_duplicate_ids(tmp_path):
    d = tmp_path / "sql"
    d.mkdir()
    dup = SAMPLE_CASE + SAMPLE_CASE.replace("Algorithm: instant", "Algorithm: inplace")
    _write(str(d / "a.sql"), dup)
    files, _ = R.discover_sql_files(str(d))
    man = R.build_manifest(files, use_cache=False)
    assert man["files"][0]["cases"] == 2
    assert man["files"][0]["unique_case_ids"] == 1
    assert man["files"][0]["duplicate_case_ids"] == 1


def test_manifest_cache_roundtrip(tmp_path, monkeypatch):
    d = tmp_path / "sql"
    d.mkdir()
    _write(str(d / "a.sql"), SAMPLE_CASE)
    monkeypatch.setattr(R, "RESULTS_DIR", str(tmp_path / "results"))
    monkeypatch.setattr(R, "MANIFEST_CACHE_PATH", str(tmp_path / "results" / ".manifest_cache.json"))
    monkeypatch.setattr(R, "_manifest_cache", None)
    files, _ = R.discover_sql_files(str(d))
    m1 = R.build_manifest(files)
    m2 = R.build_manifest(files)          # 命中缓存
    assert m1["files"][0]["sha256_content"] == m2["files"][0]["sha256_content"]
    os.utime(str(d / "a.sql"), (0, 1))    # 改 mtime → 缓存失效
    _write(str(d / "a.sql"), SAMPLE_CASE + "\nSELECT 1;\n")
    monkeypatch.setattr(R, "_manifest_cache", None)
    m3 = R.build_manifest(files)
    assert m3["files"][0]["sha256_content"] != m1["files"][0]["sha256_content"]


# ---------------------------------------------------------------- classification

def _case(text=SAMPLE_CASE, cid="TC-X0001"):
    p = "/tmp/_fake.sql"
    _write(p, text.replace("TC-X0001", cid))
    _pre, cases = R.split_cases(p, False)
    return cases[0]


def test_classify_pass():
    c = _case()
    st, res, _m, _v, errs = R.classify_case(c, {
        "verdict_rows": [{"test_id": c.test_id, "result": "PASS", "mismatch": ""}],
        "errors": [], "duration_ms": 1, "statement_count": 6})
    assert (st, res, errs) == ("PASS", "PASS", [])


def test_classify_fail_keeps_mismatch():
    c = _case()
    st, res, mis, _v, _e = R.classify_case(c, {
        "verdict_rows": [{"test_id": c.test_id, "result": "FAIL", "mismatch": "data_mismatch:id=3"}],
        "errors": [], "duration_ms": 1, "statement_count": 6})
    assert (st, res) == ("FAIL", "FAIL")
    assert "data_mismatch" in mis


def test_classify_error_is_attributed_with_errno():
    c = _case()
    st, res, mis, _v, errs = R.classify_case(c, {
        "verdict_rows": [],
        "errors": [{"stmt_index": 4, "errno": 1118, "error": "Row size too large",
                    "statement": "ALTER TABLE t1_x MODIFY ...", "duration_ms": 3}],
        "duration_ms": 5, "statement_count": 6})
    assert st == "ERROR" and res == "NO_VERDICT"
    assert "1118" in mis and "Row size too large" in mis
    assert errs[0]["errno"] == 1118


def test_classify_manual_legacy_constant():
    c = _case()
    st, res, _m, _v, _e = R.classify_case(c, {
        "verdict_rows": [{"test_id": c.test_id, "result": "BUILD_OR_ALTER_FAIL_EXPECTED",
                          "mismatch": "CHECK_MANUALLY"}],
        "errors": [], "duration_ms": 1, "statement_count": 6})
    assert (st, res) == ("MANUAL", "BUILD_OR_ALTER_FAIL_EXPECTED")


# ---------------------------------------------------------------- real files

PART_FILE = "12_partition_64.sql.gz"


def test_real_partition_file_ids_are_unique():
    """P0-4 回归守卫：分区文件曾有 4096 个重复 ID（instant/inplace 共用），修复后必须为 0。"""
    files, _ = R.discover_sql_files(ALIYUN)
    part = [(p, g) for p, g in files if os.path.basename(p).startswith("12_")]
    assert part, "分区文件不存在"
    man = R.build_manifest(part, use_cache=True)
    f = man["files"][0]
    assert f["cases"] == 8192
    assert f["duplicate_case_ids"] == 0, "分区用例 ID 又出现重复（P0-4 回归）"
    assert f["unique_case_ids"] == f["cases"]


@pytest.fixture(scope="session")
def all_cases():
    """一次性解析全部 27 个文件（~47MB 解压后），供多个断言复用。"""
    out = []
    for d in (ALIYUN, INTERNAL):
        files, _ = R.discover_sql_files(d)
        for p, g in files:
            _pre, cases = R.split_cases(p, g)
            for c in cases:
                out.append((os.path.basename(p), c))
    return out


def test_all_case_ids_globally_unique(all_cases):
    """全 27 个文件、18993 个用例的 ID 必须全局唯一（跨文件也不能撞）。

    旧实现里 TC-A0001 同时是 8 个文件中 8 种不同的类型转换，结果无法归因、
    且派生表名 t1_a0001 被 8 个文件共用 -> 并发执行互相污染。
    """
    seen = {}
    total = 0
    for fname, c in all_cases:
        total += 1
        assert c.test_id not in seen, "ID 冲突: %s (%s vs %s)" % (
            c.test_id, seen.get(c.test_id), fname)
        seen[c.test_id] = fname
        # ID 必须自带文件号与算法，便于归因
        parts = c.test_id.split("-")
        assert len(parts) == 5 and parts[0] == "TC", c.test_id
        assert parts[4] in ("IT", "IP", "CP", "DF", "XX"), c.test_id
        assert parts[1] == fname[:2], (c.test_id, fname)
    assert total == 18993, "用例总数变化，请确认是否为预期（当前 %d）" % total


def test_derived_table_names_unique(all_cases):
    """表名由 ID 派生 => 表名同样全局唯一，--workers>1 才安全。"""
    ids = {"t1_" + c.test_id.lower().replace("-", "_") for _f, c in all_cases}
    assert len(ids) == 18993
    assert max(len(i) for i in ids) <= 64, "表名超出 MySQL 64 字符上限"


def test_every_case_has_a_verdict_select(all_cases):
    """每个用例必须至少有一条会输出判定行的 SELECT（否则必然记为 ERROR/NO_VERDICT）。"""
    bad = []
    for fname, c in all_cases:
        if not any(st.lstrip().upper().startswith("SELECT") and c.test_id in st
                   for st in c.statements):
            bad.append((fname, c.test_id))
    assert not bad, "缺少判定 SELECT 的用例: %d 个，示例 %s" % (len(bad), bad[:5])


def test_oracle_compare_columns_exist_in_both_tables(all_cases):
    """P0-2 回归守卫：对照 SELECT 里引用的列必须在 t1/t2 中都真实存在。

    旧实现里分区分支生成 `a.pad <=> b.pad`，而 t2 只有 pad1/pad2 =>
    ERROR 1054 Unknown column 'b.pad'，3328+1216 个用例恒无判定输出。
    """
    bad = []
    for fname, c in all_cases:
        text = c.text
        creates = _re.findall(r"CREATE TABLE (t[12]_\w+) \((.*?)\n\) ENGINE", text, _re.S)
        cols = {}
        for tname, body in creates:
            cols[tname] = set(_re.findall(r"^\s*(?:`?)(\w+)(?:`?)\s+(?=[A-Za-z])", body, _re.M))
        for m in _re.finditer(r"(a|b)\.(\w+)\s*<=>\s*(a|b)\.(\w+)", text):
            for alias, col in ((m.group(1), m.group(2)), (m.group(3), m.group(4))):
                want = "t1_" if alias == "a" else "t2_"
                tbl = next((t for t in cols if t.startswith(want)), None)
                if tbl is None:
                    continue
                if col not in cols[tbl] and col != "id":
                    bad.append((fname, c.test_id, alias, col, sorted(cols[tbl])))
    assert not bad, "对照 SQL 引用了不存在的列: %d 处，示例 %s" % (len(bad), bad[:3])


def test_no_gz_file_is_silently_dropped():
    for d in (ALIYUN, INTERNAL):
        files, _ = R.discover_sql_files(d)
        on_disk = [f for f in os.listdir(d) if f.endswith(".sql") or f.endswith(".sql.gz")]
        assert len(files) == len(on_disk), "存在被静默丢弃的 SQL 文件"


# ---------------------------------------------------------------- completeness (P0-4)

class _PartialRunner(R.Runner):
    """故意让某个用例不产出记录，用来验证完整性核算能抓到 MISSING。"""

    def __init__(self, *a, **kw):
        self.skip_id = kw.pop("skip_id", None)
        super().__init__(*a, **kw)

    def run_one(self, case):
        if case.test_id == self.skip_id:
            return None
        return super().run_one(case)


def test_missing_case_is_accounted(tmp_path, monkeypatch):
    d = tmp_path / "sql"
    d.mkdir()
    body = "".join(SAMPLE_CASE.replace("X0001", "X%04d" % i) for i in range(1, 4))
    _write(str(d / "a.sql.gz"), body, compress=True)
    out = tmp_path / "results"
    out.mkdir()
    monkeypatch.setattr(R, "RESULTS_DIR", str(out))

    captured = {}

    def fake_exec(case, conn, per_stmt_timeout=None):
        return {"errors": [], "duration_ms": 1, "statement_count": len(case.statements),
                "verdict_rows": [{"test_id": case.test_id, "result": "PASS", "mismatch": ""}]}

    monkeypatch.setattr(R, "execute_case_pymysql", fake_exec)
    monkeypatch.setattr(R.Runner, "conn", lambda self: None)

    files, _ = R.discover_sql_files(str(d))
    runner = _PartialRunner({"host": "x", "port": "3306", "user": "u", "password": "p",
                             "database": "db"}, "unittest", str(out), skip_id="TC-X0002")
    runner._jsonl = open(runner.jsonl_path, "w", encoding="utf-8")
    _n, _s, missing = runner.run_file(files[0][0], True)
    runner._jsonl.close()
    captured["missing"] = missing
    assert captured["missing"] == ["TC-X0002"]
    assert runner.counters["MISSING"] == 1
    assert runner.counters["PASS"] == 2
    statuses = {r["test_id"]: r["status"] for r in runner.results}
    assert statuses == {"TC-X0001": "PASS", "TC-X0002": "MISSING", "TC-X0003": "PASS"}


def test_resume_skips_completed_cases(tmp_path, monkeypatch):
    d = tmp_path / "sql"
    d.mkdir()
    body = "".join(SAMPLE_CASE.replace("X0001", "X%04d" % i) for i in range(1, 4))
    _write(str(d / "a.sql"), body)
    out = tmp_path / "results"
    out.mkdir()
    monkeypatch.setattr(R, "RESULTS_DIR", str(out))
    monkeypatch.setattr(R, "execute_case_pymysql",
                        lambda case, conn, per_stmt_timeout=None: {
                            "errors": [], "duration_ms": 1, "statement_count": 1,
                            "verdict_rows": [{"test_id": case.test_id, "result": "PASS", "mismatch": ""}]})
    monkeypatch.setattr(R.Runner, "conn", lambda self: None)

    files, _ = R.discover_sql_files(str(d))
    r1 = R.Runner({}, "unittest", str(out))
    r1._jsonl = open(r1.jsonl_path, "w", encoding="utf-8")
    r1.run_file(files[0][0], False)
    r1._jsonl.close()
    r1.flush_state()
    assert r1.counters["PASS"] == 3

    r2 = R.Runner({}, "unittest", str(out), resume=True, verbose=False)
    r2.load_resume_state()
    r2._jsonl = open(r2.jsonl_path, "a", encoding="utf-8")
    _n, sel, _m = r2.run_file(files[0][0], False)
    r2._jsonl.close()
    assert sel == 0
    assert r2.counters["SKIPPED"] == 3
    assert r2.counters["PASS"] == 0


# ---------------------------------------------------------------- manifest drift (CLI)

def test_check_manifest_detects_drift(tmp_path):
    import subprocess
    d = tmp_path / "sql"
    d.mkdir()
    out = tmp_path / "results"
    out.mkdir()
    _write(str(d / "a.sql"), SAMPLE_CASE)
    base = str(tmp_path / "base_manifest.json")

    def run(*extra):
        return subprocess.run(
            [sys.executable, os.path.join(ROOT, "run_tests.py"), "--env", "aliyun",
             "--sql-dir", str(d), "--out-dir", str(out), "--dry-run", *extra],
            capture_output=True, text=True, cwd=ROOT)

    r1 = run("--manifest", base)
    assert r1.returncode == 0, r1.stderr
    r2 = run("--manifest", str(out / "run2.json"), "--check-manifest", base)
    assert "MANIFEST 对账一致" in r2.stdout

    # 改内容 → 必须报不一致
    _write(str(d / "a.sql"), SAMPLE_CASE + "\n-- Test Case: TC-X9999\nSELECT 'TC-X9999','PASS','';\n")
    r3 = run("--manifest", str(out / "run3.json"), "--check-manifest", base)
    assert "对账不一致" in r3.stdout
    assert "内容变化" in r3.stdout or "新增文件" in r3.stdout
    assert "总用例数 1 -> 2" in r3.stdout


def test_partial_run_does_not_clobber_full_baseline_manifest(tmp_path):
    """--files 局部运行必须保留全量基线 manifest_<env>.json（回归守卫）。"""
    import subprocess
    d = tmp_path / "sql"
    d.mkdir()
    out = tmp_path / "results"
    out.mkdir()
    _write(str(d / "a.sql"), SAMPLE_CASE)
    _write(str(d / "b.sql"), SAMPLE_CASE.replace("X0001", "X0002").replace("X0002", "X0002"))

    def run(*extra):
        return subprocess.run(
            [sys.executable, os.path.join(ROOT, "run_tests.py"), "--env", "aliyun",
             "--sql-dir", str(d), "--out-dir", str(out), *extra],
            capture_output=True, text=True, cwd=ROOT,
            env=dict(os.environ, MYSQL_PWD="unused", DDL_TEST_NO_DB="1"))

    r = run("--dry-run")
    assert r.returncode == 0, r.stderr
    base = json.load(open(str(out / "manifest_aliyun.json")))
    assert base["file_count"] == 2 and base["total_cases"] == 2

    # 局部运行（不连库：用 --dry-run 无法触发 write_outputs，这里直接调用函数验证）
    sys.path.insert(0, ROOT)
    import run_tests as RR
    files, _ = RR.discover_sql_files(str(d))
    picked = RR.select_files(["a.sql"], files, str(d))
    assert len(picked) == 1
    run_man = RR.build_manifest(picked, use_cache=False)

    class _FakeRunner:
        results = []
        jsonl_path = str(out / "details_aliyun.jsonl")
        state_path = str(out / "state_aliyun.json")

        def flush_state(self):
            pass

    open(_FakeRunner.jsonl_path, "w").close()
    RR.write_outputs(_FakeRunner(), "aliyun", run_man, {"version": "fake"}, str(out))
    base2 = json.load(open(str(out / "manifest_aliyun.json")))
    assert base2["file_count"] == 2, "全量基线被本轮 run_manifest 覆盖"
    rm = json.load(open(str(out / "run_manifest_aliyun.json")))
    assert rm["file_count"] == 1


# ================================================================
# Step 3 (P0-2 / P0-3) 分区分支修复
# ================================================================

def _creates_in(text):
    """抽取 CREATE TABLE 的列名集合，返回 {表名: {列名}}。"""
    out = {}
    for tname, body in _re.findall(r"CREATE TABLE (\w+) \((.*?)\n\) ENGINE", text, _re.S):
        out[tname] = set(_re.findall(r"^\s*`?(\w+)`?\s+(?=[A-Za-z])", body, _re.M))
    return out


def test_partition_target_key_oracle_is_structurally_identical(all_cases):
    """P0-2：PTK 分支的对照表 t2 必须与 t1 结构一致（同列名集合）。

    旧实现 t1=(id,target,pad) 而 t2=(id,pad1,target,pad2)，对照 SQL 却写
    a.pad<=>b.pad -> ERROR 1054，3328+1216 个用例恒无判定输出。
    """
    checked = 0
    bad = []
    for fname, c in all_cases:
        if "-PTK-" not in c.test_id:
            continue
        creates = _creates_in(c.text)
        t1 = next((t for t in creates if t.startswith("t1_")), None)
        t2 = next((t for t in creates if t.startswith("t2_")), None)
        if t1 is None or t2 is None:
            continue          # BUILD 被拒分支：本来就不该有 t2
        checked += 1
        if creates[t1] != creates[t2]:
            bad.append((fname, c.test_id, sorted(creates[t1]), sorted(creates[t2])))
    assert checked > 1000, "PTK 可建表分支用例数异常: %d" % checked
    assert not bad, "t1/t2 结构不一致: %d 处，示例 %s" % (len(bad), bad[:2])


def test_no_constant_manual_verdict_left(all_cases):
    """P0-3：不再存在"无条件通过"的常量判定行。"""
    bad = [(f, c.test_id) for f, c in all_cases
           if "BUILD_OR_ALTER_FAIL_EXPECTED" in c.text or "CHECK_MANUALLY" in c.text]
    assert not bad, "仍有 %d 个空断言用例，示例 %s" % (len(bad), bad[:3])


def test_build_rejected_branch_asserts_table_absent(all_cases):
    """P0-3：BUILD 预期失败的分支必须真的去查 information_schema.tables。"""
    n = 0
    for fname, c in all_cases:
        if "-PTK-" not in c.test_id or "#BUILD_REJECTED" not in c.text:
            continue
        n += 1
        assert "information_schema.tables" in c.text, c.test_id
        assert "PK_COMPAT needs correction" in c.text, c.test_id
    assert n > 500, "BUILD_REJECTED 断言用例数异常: %d" % n


def test_target_key_branch_asserts_type_unchanged(all_cases):
    """P0-2：ALTER 预期失败的分支必须断言列类型仍是旧类型（否则无法证明 ALTER 被拒）。"""
    n = 0
    for fname, c in all_cases:
        if "-PTK-" not in c.test_id or "#TYPE_UNCHANGED" not in c.text:
            continue
        n += 1
        assert "information_schema.columns" in c.text
        assert _re.search(r"column_type\)\s*,\s*'<missing>'\)=", c.text) or \
               "IFNULL(MAX(column_type)" in c.text, c.test_id
    assert n > 1000, "TYPE_UNCHANGED 断言用例数异常: %d" % n


def test_multi_assertion_cases_declare_count(all_cases):
    """多条断言的用例必须声明 assertions=N，runner 才能发现某条断言静默消失。"""
    bad = []
    for fname, c in all_cases:
        n_verdict = len(_re.findall(r"^SELECT '(TC-[^']+)' AS test_id", c.text, _re.M))
        declared = c.meta.get("expect_tags", {}).get("assertions")
        if n_verdict > 1 and not declared:
            bad.append((fname, c.test_id, n_verdict))
        if declared and int(declared[0]) != n_verdict:
            bad.append((fname, c.test_id, "declared=%s actual=%d" % (declared[0], n_verdict)))
    assert not bad, "断言条数声明缺失/不符: %d 处，示例 %s" % (len(bad), bad[:3])


# ================================================================
# Step 3: runner 侧多断言聚合
# ================================================================

def test_aggregate_all_pass():
    st, res, mis, a = R.aggregate_assertions([
        {"test_id": "TC-X", "result": "PASS", "mismatch": ""},
        {"test_id": "TC-X#TYPE_UNCHANGED", "result": "PASS", "mismatch": ""}])
    assert st == "PASS" and len(a) == 2
    assert a[1]["name"] == "TYPE_UNCHANGED"


def test_aggregate_any_fail_wins_regardless_of_order():
    rows_pass_first = [{"test_id": "TC-X", "result": "PASS", "mismatch": ""},
                       {"test_id": "TC-X#TYPE_UNCHANGED", "result": "FAIL",
                        "mismatch": "expect=tinyint actual=smallint"}]
    rows_fail_first = list(reversed(rows_pass_first))
    for rows in (rows_pass_first, rows_fail_first):
        st, res, mis, a = R.aggregate_assertions(rows)
        assert st == "FAIL", "旧实现只看最后一行，先失败后通过会被掩盖"
        assert "TYPE_UNCHANGED=FAIL" in mis
        assert "actual=smallint" in mis


def test_aggregate_manual_only_when_no_fail():
    st, _r, _m, _a = R.aggregate_assertions([
        {"test_id": "TC-X", "result": "BUILD_FAIL_EXPECTED", "mismatch": ""}])
    assert st == "MANUAL"
    st, _r, _m, _a = R.aggregate_assertions([
        {"test_id": "TC-X", "result": "BUILD_FAIL_EXPECTED", "mismatch": ""},
        {"test_id": "TC-X#A", "result": "FAIL", "mismatch": "x"}])
    assert st == "FAIL"


def test_assertion_count_mismatch_is_error():
    """声明了 assertions=2 却只产出 1 条 => 必须判 ERROR，不能当 PASS。"""
    case = _case(SAMPLE_CASE.replace(
        "-- @expect alter=SUCCESS column_type=smallint nullable=YES",
        "-- @expect alter=SUCCESS assertions=2"))
    st, res, mis, a, e = R.classify_case(case, {
        "verdict_rows": [{"test_id": case.test_id, "result": "PASS", "mismatch": ""}],
        "errors": [{"stmt_index": 9, "errno": 1054, "error": "Unknown column 'b.pad'",
                    "statement": "SELECT ...", "duration_ms": 1}],
        "duration_ms": 5, "statement_count": 7})
    assert st == "ERROR" and res == "ASSERTION_COUNT"
    assert "expected 2 assertion rows, got 1" in mis


def test_assertion_count_match_passes():
    case = _case(SAMPLE_CASE.replace(
        "-- @expect alter=SUCCESS column_type=smallint nullable=YES",
        "-- @expect alter=SUCCESS assertions=2"))
    st, res, mis, a, e = R.classify_case(case, {
        "verdict_rows": [{"test_id": case.test_id, "result": "PASS", "mismatch": ""},
                         {"test_id": case.test_id + "#TYPE", "result": "PASS", "mismatch": ""}],
        "errors": [], "duration_ms": 5, "statement_count": 7})
    assert st == "PASS" and len(a) == 2
