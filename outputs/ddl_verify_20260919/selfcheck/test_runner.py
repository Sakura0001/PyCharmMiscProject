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

GEN_MANIFEST = os.path.join(ROOT, "results", "generation_manifest.json")


def _expected_total_cases():
    """用例总数以生成器清单为准，避免测试里写死数字（覆盖变化时会误报）。"""
    with open(GEN_MANIFEST) as fh:
        return json.load(fh)["total_cases"]


def test_real_partition_file_ids_are_unique():
    """P0-4 回归守卫：分区文件曾有 4096 个重复 ID（instant/inplace 共用），修复后必须为 0。"""
    files, _ = R.discover_sql_files(ALIYUN)
    part = [(p, g) for p, g in files if os.path.basename(p).startswith("12_")]
    assert part, "分区文件不存在"
    man = R.build_manifest(part, use_cache=True)
    f = man["files"][0]
    assert f["duplicate_case_ids"] == 0, "分区用例 ID 又出现重复（P0-4 回归）"
    assert f["unique_case_ids"] == f["cases"]
    assert f["cases"] > 0


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
    assert total == _expected_total_cases(), \
        "执行器解析出的用例数(%d) 与生成器清单(%d) 不一致" % (total, _expected_total_cases())


def test_derived_table_names_unique(all_cases):
    """表名由 ID 派生 => 表名同样全局唯一，--workers>1 才安全。"""
    ids = {"t1_" + c.test_id.lower().replace("-", "_") for _f, c in all_cases}
    assert len(ids) == _expected_total_cases()
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
        assert "needs correction" in c.text, c.test_id
    assert n > 100, "BUILD_REJECTED 断言用例数异常: %d" % n


def test_target_key_branch_asserts_meta(all_cases):
    """P0-2：PTK 分支必须断言 ALTER 后的完整列元数据（预期失败=>仍是旧类型；
    预期成功=>已是新类型）。没有这条断言就无法证明 ALTER 被拒/生效。"""
    n = 0
    for fname, c in all_cases:
        if "-PTK-" not in c.test_id or "#META" not in c.text:
            continue
        n += 1
        assert "information_schema.columns" in c.text, c.test_id
        assert "IFNULL(MAX(column_type)" in c.text, c.test_id
        assert "want[type=" in c.text, c.test_id
    assert n > 1000, "PTK META 断言用例数异常: %d" % n


def test_no_legacy_type_only_assertion_left(all_cases):
    """分区分支已升级为完整 META，不应再残留只查 column_type 的简版断言。"""
    bad = [(f, c.test_id) for f, c in all_cases if "#TYPE_AFTER_ALTER" in c.text]
    assert not bad, "仍有简版断言: %d 处，示例 %s" % (len(bad), bad[:3])


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

def _agg(rows):
    """旧 API 适配：判定行 -> (status, result, mismatch, assertions)。"""
    a = R.collect_sql_assertions(rows)
    st, res, mis = R.aggregate(a)
    return st, res, mis, a


def test_aggregate_all_pass():
    st, res, mis, a = _agg([
        {"test_id": "TC-X", "result": "PASS", "mismatch": ""},
        {"test_id": "TC-X#TYPE_AFTER_ALTER", "result": "PASS", "mismatch": ""}])
    assert st == "PASS" and len(a) == 2
    assert a[1]["name"] == "TYPE_AFTER_ALTER"
    assert all(x["source"] == "sql" for x in a)


def test_aggregate_any_fail_wins_regardless_of_order():
    rows_pass_first = [{"test_id": "TC-X", "result": "PASS", "mismatch": ""},
                       {"test_id": "TC-X#TYPE_AFTER_ALTER", "result": "FAIL",
                        "mismatch": "expect=tinyint actual=smallint"}]
    for rows in (rows_pass_first, list(reversed(rows_pass_first))):
        st, res, mis, a = _agg(rows)
        assert st == "FAIL", "旧实现只看最后一行，先失败后通过会被掩盖"
        assert "TYPE_AFTER_ALTER=FAIL" in mis
        assert "actual=smallint" in mis


def test_aggregate_manual_only_when_no_fail():
    st, _r, _m, _a = _agg([{"test_id": "TC-X", "result": "BUILD_FAIL_EXPECTED", "mismatch": ""}])
    assert st == "MANUAL"
    st, _r, _m, _a = _agg([{"test_id": "TC-X", "result": "BUILD_FAIL_EXPECTED", "mismatch": ""},
                           {"test_id": "TC-X#A", "result": "FAIL", "mismatch": "x"}])
    assert st == "FAIL"


def test_aggregate_empty():
    assert R.aggregate([]) == (None, "", "")


# ---------------- P0-6 负向探针的 errno 级校验 ----------------

def _probe_case(specs, assertions_n=None):
    tags = " ".join("neg_probe=%s" % sp for sp in specs)
    head = ("-- @expect alter=SUCCESS assertions=%d %s" % (assertions_n or 1, tags))
    text = SAMPLE_CASE.replace(
        "-- @expect alter=SUCCESS column_type=smallint nullable=YES", head)
    p = "/tmp/_probe.sql"
    _write(p, text)
    _pre, cases = R.split_cases(p, False)
    return cases[0]


def _err(sha, errno):
    return {"stmt_index": 3, "errno": errno, "error": "Data too long",
            "statement": "INSERT ...", "stmt_sha1": sha, "duration_ms": 1}


def test_neg_probe_strict_must_fail_with_declared_errno():
    c = _probe_case(["abc123=1406|1264"])
    st, res, mis, a, e = R.classify_case(c, {
        "verdict_rows": [{"test_id": c.test_id, "result": "PASS", "mismatch": ""}],
        "errors": [_err("abc123", 1406)], "duration_ms": 1, "statement_count": 5})
    assert st == "PASS"
    assert [x["name"] for x in a] == ["PRIMARY", "NEG_ERRNO#1"]
    assert a[1]["source"] == "runner"


def test_neg_probe_silent_accept_is_fail():
    """STRICT 下超限值被静默接受 = 数据正确性缺陷，必须判 FAIL。"""
    c = _probe_case(["abc123=1406|1264"])
    st, res, mis, a, e = R.classify_case(c, {
        "verdict_rows": [{"test_id": c.test_id, "result": "PASS", "mismatch": ""}],
        "errors": [], "duration_ms": 1, "statement_count": 5})
    assert st == "FAIL"
    assert "SILENTLY ACCEPTED" in mis


def test_neg_probe_wrong_errno_is_fail():
    c = _probe_case(["abc123=1406|1264"])
    st, res, mis, a, e = R.classify_case(c, {
        "verdict_rows": [{"test_id": c.test_id, "result": "PASS", "mismatch": ""}],
        "errors": [_err("abc123", 1062)], "duration_ms": 1, "statement_count": 5})
    assert st == "FAIL" and "not in declared" in mis


def test_neg_probe_accepted_mode():
    c = _probe_case(["abc123=ACCEPTED"])
    st, _r, _m, a, _e = R.classify_case(c, {
        "verdict_rows": [{"test_id": c.test_id, "result": "PASS", "mismatch": ""}],
        "errors": [], "duration_ms": 1, "statement_count": 5})
    assert st == "PASS"
    st, _r, mis, _a, _e = R.classify_case(c, {
        "verdict_rows": [{"test_id": c.test_id, "result": "PASS", "mismatch": ""}],
        "errors": [_err("abc123", 1406)], "duration_ms": 1, "statement_count": 5})
    assert st == "FAIL" and "should have been accepted" in mis


def test_assertion_count_ignores_runner_synthesized():
    """assertions=N 只数 SQL 判定行，runner 合成的负向探针校验不计入。"""
    c = _probe_case(["abc123=1406"], assertions_n=1)
    st, res, mis, a, e = R.classify_case(c, {
        "verdict_rows": [{"test_id": c.test_id, "result": "PASS", "mismatch": ""}],
        "errors": [_err("abc123", 1406)], "duration_ms": 1, "statement_count": 5})
    assert st == "PASS", mis
    assert len([x for x in a if x["source"] == "sql"]) == 1
    assert len(a) == 2


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


# ================================================================
# Step 4 (P0-5 / P0-9) 分区生成器：类型感知 + 真 SUBPARTITION + 实测矩阵
# ================================================================

sys.path.insert(0, ROOT)
import generate_test_sql as G  # noqa: E402

PROBE_JSON = os.path.join(ROOT, "tools", "partition_compat_aliyun.json")


def test_24_partition_strategies_are_distinct():
    """P0-5：必须是 24 种**互不相同**的策略（8 一级 + 16 组合），不是 64 种里的 8 种重复 8 次。"""
    names = [n for n, _f, _s in G.PARTITION_STRATEGIES]
    assert len(names) == len(set(names)) == 24
    composite = [n for n, f, sb in G.PARTITION_STRATEGIES if sb]
    assert len(composite) == 16, composite
    # 组合分区只能是一级 RANGE*/LIST* + 二级 HASH/KEY 家族
    for n, f, sb in G.PARTITION_STRATEGIES:
        if sb:
            assert f in ("RANGE", "RANGE COLUMNS", "LIST", "LIST COLUMNS"), n
            assert sb in ("HASH", "LINEAR HASH", "KEY", "LINEAR KEY"), n


def test_subpartition_really_generated(all_cases):
    """P0-5：SUBPARTITION 必须真实出现在 SQL 里（旧实现出现 0 次）。"""
    n_sub = sum(c.text.count("SUBPARTITION BY") for f, c in all_cases if "-PTK-" in c.test_id or "-PNK-" in c.test_id)
    assert n_sub > 1000, "SUBPARTITION BY 只出现 %d 次" % n_sub


def test_no_duplicated_partition_keyword(all_cases):
    """回归守卫：曾生成 `PARTITION BY RANGE COLUMNS COLUMNS(target)`。"""
    bad = []
    for f, c in all_cases:
        # 只看真正的 PARTITION BY 子句，不看 `-- Partition: RANGE COLUMNS (#01/24)` 这类注释
        for clause in _re.findall(r"PARTITION BY [^\n]*", c.text):
            if "COLUMNS COLUMNS" in clause or "COLUMNS (" in clause:
                bad.append((f, c.test_id, clause))
    assert not bad, "分区关键字拼接错误: %d 处，示例 %s" % (len(bad), bad[:3])


def test_partition_bounds_match_column_type(all_cases):
    """P0-9：字符串/二进制列的分区界必须是字符串/十六进制字面量，不能是裸整数。

    旧实现对所有类型硬编码 `VALUES LESS THAN (100)/(200)/(300)`：
    TINYINT 上限 127 -> 越界；VARCHAR -> 类型不符，实测 errno 1654/1697。
    """
    bad = []
    for fname, c in all_cases:
        if "-PTK-" not in c.test_id and "-PNK-" not in c.test_id:
            continue
        ttype = (c.meta.get("type") or "").split(" -> ")[0].strip().upper()
        is_str = ttype.startswith(("CHAR", "VARCHAR", "BINARY", "VARBINARY",
                                   "TEXT", "TINYTEXT", "MEDIUMTEXT", "LONGTEXT",
                                   "BLOB", "TINYBLOB", "MEDIUMBLOB", "LONGBLOB"))
        for m in _re.finditer(r"PARTITION BY (RANGE COLUMNS|LIST COLUMNS)\(target\)(.*?)(?:;|\n\n)",
                              c.text, _re.S):
            body = m.group(2)
            lits = _re.findall(r"VALUES (?:LESS THAN )?\(([^)]*)\)", body)
            for lit in lits:
                if lit.strip() == "MAXVALUE":
                    continue
                for one in lit.split(","):
                    one = one.strip()
                    if not one:
                        continue
                    quoted = one.startswith(("'", "X'", "x'", "0x"))
                    if is_str and not quoted:
                        bad.append((fname, c.test_id, ttype, one))
                    if (not is_str) and quoted and not one.startswith("X'"):
                        bad.append((fname, c.test_id, ttype, one))
    assert not bad, "分区界与列类型不匹配: %d 处，示例 %s" % (len(bad), bad[:5])


def test_partition_compat_matrix_matches_measured_probe():
    """生成器内嵌的 PARTITION_COMPAT 必须与实测探针结果一致（按 category 归并）。"""
    if not os.path.exists(PROBE_JSON):
        pytest.skip("未找到实测探针结果 tools/partition_compat_aliyun.json")
    with open(PROBE_JSON) as fh:
        probe = json.load(fh)
    strategies = [n for n, _f, _s in G.PARTITION_STRATEGIES]
    measured = {}
    for typedef, info in probe["types"].items():
        cat = info["category"]
        ok = {s for s in strategies if probe["matrix"][typedef].get(s, {}).get("build")}
        measured.setdefault(cat, set()).update(ok)
        # 同一 category 内不同具体类型的可建策略集合必须一致，否则矩阵不能按 category 归并
        assert measured[cat] == ok, "%s 内 %s 的可建策略与其它类型不一致" % (cat, typedef)
    for cat, ok in measured.items():
        embedded = set(G.PARTITION_COMPAT.get(cat, []))
        assert embedded == ok, ("category=%s 内嵌矩阵与实测不符\n  内嵌: %s\n  实测: %s"
                                % (cat, sorted(embedded), sorted(ok)))


def test_list_partition_data_fits_partitions(all_cases):
    """LIST/LIST COLUMNS 没有 MAXVALUE 兜底：插入值必须来自分组，否则 errno 1526 静默丢数据。"""
    bad = []
    for fname, c in all_cases:
        if "-PTK-" not in c.test_id:
            continue
        if not _re.search(r"PARTITION BY LIST( COLUMNS)?\(target\)", c.text):
            continue
        groups = _re.findall(r"VALUES IN \(([^)]*)\)", c.text)
        allowed = {v.strip() for g in groups for v in g.split(",")}
        for ins in _re.findall(r"^INSERT INTO t1_\w+ \(target\) VALUES \((.+?)\);$",
                               c.text, _re.M):
            v = ins.strip()
            if v == "NULL":
                continue
            if v not in allowed:
                bad.append((fname, c.test_id, v, sorted(allowed)[:4]))
    assert not bad, "LIST 分区插入了不在任何分组里的值: %d 处，示例 %s" % (len(bad), bad[:4])


def _parse_factors(text):
    """从 `-- Factors: k=v, k=v` 行还原因子字典。"""
    m = _re.search(r"^-- Factors: (.*)$", text, _re.M)
    if not m:
        return {}
    out = {}
    for kv in m.group(1).split(", "):
        if "=" in kv:
            k, v = kv.split("=", 1)
            out[k.strip()] = v.strip()
    return out


def test_build_rejected_cases_are_justified(all_cases):
    """每个 BUILD_REJECTED 负向用例都必须有可核对的依据，不能凭空造负向覆盖。

    依据只有两种：
      (a) PTK: (category, strategy) 不在实测 PARTITION_COMPAT 里，或目标列超索引键上限
      (b) REG: 因子要求整列索引，但目标列超 InnoDB 3072 字节键上限
    """
    by_id = {t["id"]: t for t in G.ALL_TRANSITIONS}
    n_part = n_reg = 0
    bad = []
    for fname, c in all_cases:
        if "#BUILD_REJECTED" not in c.text:
            continue
        m = _re.search(r"^-- Transition ID: (\S+)$", c.text, _re.M)
        trans = by_id.get(m.group(1)) if m else None
        if trans is None:
            bad.append((fname, c.test_id, "缺少可追溯的 Transition ID"))
            continue
        if "-PTK-" in c.test_id:
            n_part += 1
            sm = _re.search(r"^-- Partition: (.+?) \(#", c.text, _re.M)
            if not sm:
                bad.append((fname, c.test_id, "缺少 Partition 策略标注"))
                continue
            strat = sm.group(1)
            len_ok, _bytes = G.partition_key_len_ok(trans)
            if G.partition_is_buildable(trans["category"], strat) and len_ok:
                bad.append((fname, c.test_id,
                            "%s/%s 实测可建却被判为不可建" % (trans["category"], strat)))
        else:
            n_reg += 1
            if "INFEASIBLE_COMBINATION" not in c.text:
                bad.append((fname, c.test_id, "非 PTK 的 BUILD_REJECTED 必须标 INFEASIBLE_COMBINATION"))
            elif G.check_case_feasible(trans, _parse_factors(c.text)) is None:
                bad.append((fname, c.test_id, "check_case_feasible 判可行，却生成了负向用例"))
    assert not bad, "无依据的 BUILD_REJECTED: %d 处，示例 %s" % (len(bad), bad[:4])
    assert n_part > 100, "PTK 负向用例数异常: %d" % n_part
    assert n_reg > 0, "REG 负向用例数异常: %d" % n_reg


# ================================================================
# Step 5 (P0-8) 行宽/索引键上限：上限转换必须真的建得出来
# ================================================================

ROW_SIZE_LIMIT = 65535          # MySQL 服务器级行宽上限（不含 BLOB/TEXT）
INDEX_KEY_LIMIT = 3072          # InnoDB 单索引键上限
BIG_TYPE_RE = r"VARCHAR\(1638[123]\)|VARCHAR\(6552[789]\)|VARBINARY\(6552[789]\)"


def _mb(transition):
    cs = transition.get("charset")
    return G.CHARSET_MBMAXLEN.get((cs or "latin1").lower(), 1)


def _est_row_bytes(transition, minimal):
    """按生成器的两种表结构估算行宽（与 MySQL 的 65535 计算口径一致）。"""
    tb = G._type_max_bytes(transition["new_type"], transition.get("charset"))
    if tb is None:
        return 0                       # 整数/DECIMAL/BIT 远小于上限
    total = 4                          # id INT
    total += tb + (2 if tb > 255 else 1)
    if not minimal:
        pad = 20 * _mb(transition) if transition["category"] in ("char", "varchar", "text") else 20
        total += 2 * (pad + 1)         # pad1 + pad2 VARCHAR(20)
    return total


def test_upper_limit_transitions_match_measured_maxima():
    """P0-8：三条"转换到 MySQL 上限"的用例必须等于二分实测上界，而不是理论值。"""
    by_id = {t["id"]: t for t in G.ALL_TRANSITIONS}
    expect = {"VC-08": ("VARCHAR(16381)", "VARCHAR(16382)"),
              "VC-09": ("VARCHAR(65527)", "VARCHAR(65528)"),
              "VBIN-03": ("VARBINARY(65527)", "VARBINARY(65528)")}
    for tid, (o, n) in expect.items():
        t = by_id[tid]
        assert (t["old_type"], t["new_type"]) == (o, n), \
            "%s = %s->%s，二分实测上界应为 %s->%s" % (tid, t["old_type"], t["new_type"], o, n)
        assert t.get("minimal_table") is True, tid


def test_no_transition_exceeds_row_size_budget():
    """P0-8 根因守卫：任何转换在其表结构下都不得超过 65535 行宽上限。

    旧实现 VC-08 用 VARCHAR(16383) utf8mb4 = 65532 + 2 + id 4 = 65538 > 65535，
    CREATE/ALTER 直接 errno 1118，200 个用例变成 ERROR。
    """
    bad = []
    for t in G.ALL_TRANSITIONS:
        minimal = bool(t.get("minimal_table"))
        for shape in ({True, minimal} if not minimal else {True}):
            n = _est_row_bytes(t, shape)
            if n and n > ROW_SIZE_LIMIT:
                bad.append((t["id"], "minimal" if shape else "normal", n))
    assert not bad, "行宽超上限的转换: %s" % bad[:6]


def test_infeasible_combinations_are_explicit_negative_cases(all_cases):
    """超过 3072 字节的目标列若需要整列索引，必须走显式负向用例（BUILD_REJECTED）。"""
    n = 0
    for fname, c in all_cases:
        if "INFEASIBLE_COMBINATION" not in c.text:
            continue
        n += 1
        assert "#BUILD_REJECTED" in c.text, c.test_id
        assert "build=FAIL" in c.text, c.test_id
        assert "errno=[1071]" in c.text, c.test_id
        assert "information_schema.tables" in c.text, c.test_id
    assert n > 0, "没有任何 infeasible 负向用例"


def test_minimal_table_composite_pk_is_not_marked_infeasible(all_cases):
    """回归守卫：minimal_table 下 COMPOSITE_PK 被降级为 PRIMARY KEY(id)，
    目标列上没有索引 => 组合可行，不能判 infeasible（曾误判 8 例）。"""
    n = 0
    for fname, c in all_cases:
        if "primary_key=COMPOSITE_PK" not in c.text:
            continue
        if not _re.search(BIG_TYPE_RE, c.text):
            continue
        n += 1
        assert "INFEASIBLE_COMBINATION" not in c.text, c.test_id
        assert "PRIMARY KEY (id, target)" not in c.text, "%s COMPOSITE_PK 未降级" % c.test_id
    assert n > 0


def test_instant_expectation_accounts_for_minimal_pk_downgrade(all_cases):
    """回归守卫：minimal_table + COMPOSITE_PK + INSTANT 的期望必须是 SUCCESS。

    目标列不在任何索引里 => INSTANT 实际成功；旧期望模型判 FAIL、对照表按旧类型建，
    结果 4 个 VC-08/VC-09 用例数据不一致报 FAIL。
    """
    n = 0
    for fname, c in all_cases:
        if not c.test_id.endswith("-IT") or "primary_key=COMPOSITE_PK" not in c.text:
            continue
        if not _re.search(BIG_TYPE_RE, c.text):
            continue
        if "INFEASIBLE_COMBINATION" in c.text:
            continue
        n += 1
        assert ", Expected: SUCCESS" in c.text, \
            "%s: minimal_table+COMPOSITE_PK+INSTANT 期望应为 SUCCESS" % c.test_id
        assert _re.search(r"-- Oracle table: (VARCHAR\(16382\)|VARCHAR\(65528\)|VARBINARY\(65528\))",
                          c.text), "%s: 对照表应按新类型建" % c.test_id
    assert n > 0


def test_atr_cases_respect_minimal_table(all_cases):
    """P0-8：列属性保持用例也必须认 minimal_table，否则超大类型 + pad 列 errno 1118。"""
    n = 0
    for fname, c in all_cases:
        if "-ATR-" not in c.test_id or not _re.search(BIG_TYPE_RE, c.text):
            continue
        n += 1
        assert "pad VARCHAR(20)" not in c.text, "%s: minimal_table 用例不应有 pad 列" % c.test_id
    assert n > 0, "未找到 minimal_table 的 ATR 用例"


def test_charset_present_on_every_string_column(all_cases):
    """P0-8：字符集必须在**所有**建表点显式写出。

    漏写时列会按库默认字符集解析（utf8mb3）=> VARCHAR(65528) 直接 errno 1074
    "max = 21845"；或 CREATE 不带而 ALTER 带 CHARACTER SET => 变成"改字符集"，
    INPLACE 被拒(1846)，11 个分区用例因此误判 FAIL。
    """
    bad = []
    for fname, c in all_cases:
        if not _re.search(r"-- Type: (CHAR|VARCHAR)\(", c.text):
            continue
        for tname, create in _re.findall(r"CREATE TABLE (\w+) \((.*?)\) ENGINE[^;]*", c.text, _re.S):
            tbl_cs = _re.search(r"DEFAULT CHARSET=(\w+)", create)
            for col in _re.findall(r"^\s*(?:target|id)\s+((?:VAR)?CHAR\(\d+\)[^,\n]*)$",
                                   create, _re.M):
                if "CHARACTER SET" not in col.upper() and not tbl_cs:
                    bad.append((fname, c.test_id, tname, "target 无字符集且表无 DEFAULT CHARSET"))
    # ALTER 与 CREATE 的字符集必须一致，否则 ALTER 语义变成"改字符集"，INPLACE 会被拒(1846)
    for fname, c in all_cases:
        if not _re.search(r"-- Type: (?:CHAR|VARCHAR)", c.text):
            continue
        creates = _re.findall(r"target\s+((?:VAR)?CHAR\(\d+\)(?:\s+CHARACTER SET\s+\w+)?)", c.text)
        alters = _re.findall(r"MODIFY (?:target|id) ((?:VAR)?CHAR\(\d+\)(?:\s+CHARACTER SET\s+\w+)?)", c.text)
        cs_create = {x.split("CHARACTER SET")[-1].strip().lower() for x in creates if "CHARACTER SET" in x}
        cs_alter = {x.split("CHARACTER SET")[-1].strip().lower() for x in alters if "CHARACTER SET" in x}
        if cs_alter and cs_create and (cs_alter - cs_create):
            bad.append((fname, c.test_id,
                        "ALTER 字符集 %s 不在 CREATE 字符集 %s 中" % (sorted(cs_alter), sorted(cs_create))))
    assert not bad, "字符集缺失/不一致: %d 处，示例 %s" % (len(bad), bad[:5])


# ================================================================
# Step 6 (P0-6) 负向探针真正执行
# ================================================================

def test_no_commented_out_inserts_remain(all_cases):
    """P0-6：旧实现生成 `-- INSERT INTO ...`，2623 条超上限负向探针从未执行。"""
    bad = [(f, c.test_id) for f, c in all_cases if "\n-- INSERT INTO" in c.text]
    assert not bad, "仍有被注释掉的 INSERT: %d 处，示例 %s" % (len(bad), bad[:3])


def test_negative_probes_are_real_and_symmetric(all_cases):
    """每条超限值必须**同时**插入 t1 与对照表 t2，并配一条 NEG_REJECTED 断言。"""
    n_cases = n_probes = 0
    bad = []
    for fname, c in all_cases:
        if "#NEG_REJECTED" not in c.text:
            continue
        n_cases += 1
        p1 = _re.findall(r"^-- probe \d+/\d+ -> (t1_\w+)$", c.text, _re.M)
        p2 = _re.findall(r"^-- probe \d+/\d+ -> (t2_\w+)$", c.text, _re.M)
        n_probes += len(p1)
        if len(p1) != len(p2) or not p1:
            bad.append((fname, c.test_id, len(p1), len(p2)))
        # 声明的 neg_probe 数量必须与实际探针语句数一致
        declared = c.meta.get("expect_tags", {}).get("neg_probe") or []
        if len(declared) != len(p1) + len(p2):
            bad.append((fname, c.test_id, "declared=%d actual=%d"
                        % (len(declared), len(p1) + len(p2))))
    assert n_cases > 2000, "带负向探针的用例数异常: %d" % n_cases
    assert n_probes > 2000, "负向探针语句数异常: %d" % n_probes
    assert not bad, "探针不成对/声明不符: %d 处，示例 %s" % (len(bad), bad[:3])


def test_strict_and_nonstrict_expectations_differ(all_cases):
    """STRICT 断言"必须 0 行落库"，非 STRICT 断言"t1 与 t2 行为对称"。"""
    strict = nonstrict = 0
    bad = []
    for fname, c in all_cases:
        if "#NEG_REJECTED" not in c.text:
            continue
        is_strict = "sql_mode=STRICT" in c.text or "sql_mode = 'STRICT_TRANS_TABLES'" in c.text
        sel = _re.search(r"SELECT '[^']*#NEG_REJECTED'.*?;", c.text, _re.S)
        body = sel.group(0) if sel else ""
        if "= 0 AND" in body:
            strict += 1
            if not is_strict:
                bad.append((fname, c.test_id, "非 STRICT 却断言 0 行"))
        elif _re.search(r"- @neg_before_t1 = \(SELECT COUNT\(\*\) FROM \w+\) - @neg_before_t2", body):
            nonstrict += 1
        else:
            bad.append((fname, c.test_id, "无法识别的 NEG 断言形态"))
    # NON_STRICT 是 OFAT 的单因子变体：每个 (转换 × 算法) 各一条，
    # 再扣掉没有 post_fail 值的类型（TEXT/BLOB/BIT），实测量级约 80 条
    assert strict > 1000, "STRICT 负向断言数异常: %d" % strict
    assert nonstrict > 50, "非 STRICT 负向断言数异常: %d" % nonstrict
    assert not bad, "NEG 断言与 sql_mode 不匹配: %s" % bad[:3]


def test_every_statement_has_balanced_quotes(all_cases):
    """静态语法守卫：每条语句的单引号必须成对（不配对 => 语句被吞、分割错乱）。

    这条守卫是为了抓住实际发生过的缺陷：NEG_REJECTED 的 CONCAT 里多写了一个 `'`，
    导致 543 个用例报 errno 1064 且把后面的对照 SELECT 一起截断。
    """
    bad = []
    for fname, c in all_cases:
        for i, st in enumerate(c.statements):
            # 去掉 '' 转义与反斜杠转义后，单引号必须成对
            t = st.replace("''", "").replace("\\'", "")
            if t.count("'") % 2 != 0:
                bad.append((fname, c.test_id, i, st[:110]))
            if st.count("(") != st.count(")"):
                bad.append((fname, c.test_id, i, "括号不配对: " + st[:90]))
    assert not bad, "语句引号/括号不配对: %d 处，示例 %s" % (len(bad), bad[:3])


# ================================================================
# Step 7 (P0-7 + P1-1) 期望值机读化 + 每用例列类型断言
# ================================================================

import hashlib as _hashlib  # noqa: E402

META_PROPS = ["column_type", "is_nullable", "column_default",
              "character_set_name", "collation_name", "extra", "ordinal_position"]


def test_every_regular_case_has_meta_assertion(all_cases):
    """P1-1：REG / ATR / PTK / PNK 用例都必须断言 ALTER 之后的列元数据。

    旧套件 238 条元数据断言里**没有一条**断言 column_type，
    因此"类型对了但 NOT NULL/DEFAULT/charset/collation/COMMENT 被改坏"发现不了。
    """
    missing = []
    n = 0
    for fname, c in all_cases:
        scope = c.test_id.split("-")[2]
        if scope not in ("REG", "ATR", "PTK", "PNK", "SPE", "FK"):
            continue
        # BUILD_REJECTED 类用例根本不建表、不 ALTER，没有列可断言
        if "#BUILD_REJECTED" in c.text:
            continue
        n += 1
        if "#META" not in c.text and "#TYPE_AFTER_ALTER" not in c.text:
            missing.append((fname, c.test_id))
    total = _expected_total_cases()
    n_rejected = sum(1 for _f, c in all_cases if "#BUILD_REJECTED" in c.text)
    # 除"建表本应被拒绝"的负向用例外，其余每一个用例都必须有列元数据断言
    assert n == total - n_rejected, \
        "受检用例数 %d != 总数 %d - BUILD_REJECTED %d" % (n, total, n_rejected)
    assert not missing, "缺少列元数据断言: %d 处，示例 %s" % (len(missing), missing[:4])


def test_meta_assertion_covers_all_properties(all_cases):
    """META 断言必须一次性校验 7 个属性，并给出 actual vs want。"""
    bad = []
    n = 0
    for fname, c in all_cases:
        m = _re.search(r"SELECT '[^']*#META' AS test_id,.*?;", c.text, _re.S)
        if not m:
            continue
        n += 1
        body = m.group(0)
        for prop in META_PROPS:
            if prop not in body:
                bad.append((fname, c.test_id, "缺 %s" % prop))
                break
        if "actual[" not in body or "want[" not in body:
            bad.append((fname, c.test_id, "mismatch 未同时给出 actual 与 want"))
    total = _expected_total_cases()
    assert n > total * 0.8, "META 断言数异常: %d / %d" % (n, total)
    assert not bad, "META 断言不完整: %d 处，示例 %s" % (len(bad), bad[:4])


def test_every_alter_case_declares_machine_readable_expectation(all_cases):
    """P0-7：每条含 ALTER 的用例都必须声明 alter=SUCCESS|FAIL 与 alter_sha。"""
    bad = []
    n = 0
    for fname, c in all_cases:
        alters = [st for st in c.statements if st.upper().startswith("ALTER TABLE")]
        if not alters:
            continue
        n += 1
        tags = c.meta.get("expect_tags", {})
        if not tags.get("alter") or not tags.get("alter_sha"):
            bad.append((fname, c.test_id, "缺 alter=/alter_sha=", sorted(tags)))
            continue
        if tags["alter"][0].upper() == "FAIL" and not tags.get("errno"):
            bad.append((fname, c.test_id, "alter=FAIL 但未声明允许的 errno"))
    assert n > 8000, "含 ALTER 的用例数异常: %d" % n
    assert not bad, "机读期望缺失: %d 处，示例 %s" % (len(bad), bad[:4])


def test_declared_alter_sha_matches_actual_statement(all_cases):
    """声明的 alter_sha 必须真的等于用例里那条 ALTER 语句的哈希（防止生成器漂移）。"""
    bad = []
    n = 0
    for fname, c in all_cases:
        sha = (c.meta.get("expect_tags", {}).get("alter_sha") or [None])[0]
        if not sha:
            continue
        alters = [st for st in c.statements if st.upper().startswith("ALTER TABLE")]
        if not alters:
            bad.append((fname, c.test_id, "声明了 alter_sha 但没有 ALTER 语句"))
            continue
        n += 1
        real = {_hashlib.sha1(a.rstrip().rstrip(";").encode("utf-8")).hexdigest()[:12]
                for a in alters}
        if sha not in real:
            bad.append((fname, c.test_id, "sha %s 不在 %s" % (sha, sorted(real))))
    assert n > 8000, "校验的 alter_sha 数异常: %d" % n
    assert not bad, "alter_sha 与语句不匹配: %d 处，示例 %s" % (len(bad), bad[:3])


# ---------------- runner: ALTER_OUTCOME 期望 vs 实际 ----------------

def _alter_case(alter_decl, errno_decl=None):
    sha = "deadbeef0001"
    tag = "-- @expect alter=%s alter_sha=%s" % (alter_decl, sha)
    if errno_decl:
        tag += " errno=[%s]" % errno_decl
    text = SAMPLE_CASE.replace(
        "-- @expect alter=SUCCESS column_type=smallint nullable=YES", tag)
    p = "/tmp/_alter.sql"
    _write(p, text)
    _pre, cases = R.split_cases(p, False)
    return cases[0], sha


def _alter_err(sha, errno=1846):
    return {"stmt_index": 4, "errno": errno, "error": "ALGORITHM=INSTANT is not supported",
            "statement": "ALTER TABLE ...", "stmt_sha1": sha, "duration_ms": 2}


def test_alter_outcome_success_as_declared():
    c, sha = _alter_case("SUCCESS")
    a, errno = R.check_alter_outcome(c, [])
    assert a[0]["result"] == "PASS" and errno is None


def test_alter_outcome_declared_success_but_failed():
    """P0-7 的核心：声明 SUCCESS 而实际失败，必须判 FAIL（旧执行器只写 CSV 从不比对）。"""
    c, sha = _alter_case("SUCCESS")
    a, errno = R.check_alter_outcome(c, [_alter_err(sha)])
    assert a[0]["result"] == "FAIL"
    assert "declared SUCCESS but actually FAIL" in a[0]["mismatch"]
    assert errno == 1846


def test_alter_outcome_declared_fail_but_succeeded():
    c, sha = _alter_case("FAIL", "1845,1846")
    a, errno = R.check_alter_outcome(c, [])
    assert a[0]["result"] == "FAIL"
    assert "declared FAIL but actually SUCCESS" in a[0]["mismatch"]


def test_alter_outcome_wrong_errno():
    c, sha = _alter_case("FAIL", "1845,1846")
    a, errno = R.check_alter_outcome(c, [_alter_err(sha, 1064)])
    assert a[0]["result"] == "FAIL"
    assert "not in" in a[0]["mismatch"]


def test_alter_outcome_right_errno():
    c, sha = _alter_case("FAIL", "1845,1846")
    a, errno = R.check_alter_outcome(c, [_alter_err(sha, 1845)])
    assert a[0]["result"] == "PASS" and errno == 1845


def test_alter_outcome_ignores_other_statement_errors():
    """只有 alter_sha 那条语句的成败才算数，其它语句（负向探针等）报错不干扰。"""
    c, sha = _alter_case("SUCCESS")
    other = {"stmt_index": 9, "errno": 1406, "error": "Data too long",
             "statement": "INSERT ...", "stmt_sha1": "ffff00001111", "duration_ms": 1}
    a, errno = R.check_alter_outcome(c, [other])
    assert a[0]["result"] == "PASS" and errno is None
