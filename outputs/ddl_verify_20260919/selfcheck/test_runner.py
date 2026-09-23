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

def test_discover_finds_gz_files():
    files, dups = R.discover_sql_files(ALIYUN)
    names = [os.path.basename(p) for p, _ in files]
    assert "07_varchar_instant.sql.gz" in names
    assert "12_partition_64.sql.gz" in names
    assert "01_integer_signed_instant.sql" in names
    assert len(files) == 12
    assert dups == []


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

def test_real_partition_file_has_known_defects_documented():
    """记录 P0-4/P0-2 的基线事实，修复后这些断言必须被更新（防回归哨兵）。"""
    man = R.build_manifest([(os.path.join(ALIYUN, "12_partition_64.sql.gz"), True)])
    f = man["files"][0]
    assert f["cases"] == 8192
    assert f["duplicate_case_ids"] == 4096, "P0-4 未修复时每个分区 ID 出现 2 次"


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
