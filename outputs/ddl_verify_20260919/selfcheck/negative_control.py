#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""反向对照：故意注入 6 类缺陷，验证执行器**必须**把它们判出来。

一套全绿的测试如果没有反向对照，就无法区分"实现正确"和"断言恒过"。
本脚本在临时目录里生成 6 个被故意改坏的用例，跑真实实例，
然后断言每一个都被对应的机制抓到；有任何一个漏抓即退出码非 0。

用法:
    python3 selfcheck/negative_control.py --env aliyun
    python3 selfcheck/negative_control.py --env local
"""
import os
import sys
import json
import shutil
import hashlib
import argparse
import tempfile
import subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)

BASE = """-- Test Case: {tid}
-- Type: TINYINT -> SMALLINT, Algorithm: {algo}, Expected: {exp}
-- Transition ID: NC
-- Factors: data_scale=S1, sql_mode=STRICT
-- @expect alter={exp} build=SUCCESS assertions={nassert}{errno}{sha}
DROP TABLE IF EXISTS {t1}, {t2};
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE {t1} (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target TINYINT{idx},
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id)
) ENGINE=InnoDB;
INSERT INTO {t1} (target) VALUES (1), (127), (-128);
ALTER TABLE {t1} MODIFY target SMALLINT, ALGORITHM={algo};
{extra_t1}
CREATE TABLE {t2} (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target {t2type},
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id)
) ENGINE=InnoDB;
INSERT INTO {t2} (target) VALUES {t2vals};
{probes}
SELECT '{tid}' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM {t1} WHERE id NOT IN (SELECT id FROM {t2})
  UNION ALL
  SELECT 't2_extra' AS src, id FROM {t2} WHERE id NOT IN (SELECT id FROM {t1})
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM {t1} a JOIN {t2} b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;
{meta}
"""

META_SQL = """SELECT '{tid}#META' AS test_id,
       IF(COUNT(*)=1 AND MAX(column_type)={ct} AND MAX(is_nullable)='YES','PASS','FAIL') AS result,
       CONCAT('actual[type=',IFNULL(MAX(column_type),'<missing>'),'] want[',{ct},']') AS mismatch
FROM information_schema.columns
WHERE table_schema=DATABASE() AND table_name='{t1}' AND column_name='target';
"""


def sha1_12(stmt):
    return hashlib.sha1(stmt.rstrip().rstrip(";").encode("utf-8")).hexdigest()[:12]


def build_cases():
    cases = []

    # NC1: 声明 alter=FAIL，但 ALTER 实际会成功 -> ALTER_OUTCOME 必须判 FAIL
    tid = "TC-90-NC1-IP"
    alter = "ALTER TABLE t1_%s MODIFY target SMALLINT, ALGORITHM=inplace" % tid.lower().replace("-", "_")
    cases.append(("NC1_alter_declared_fail_but_succeeds", tid, BASE.format(
        tid=tid, algo="inplace", exp="FAIL", nassert=2, errno=" errno=[1845,1846]",
        sha=" alter_sha=%s" % sha1_12(alter + ";"),
        t1="t1_" + tid.lower().replace("-", "_"), t2="t2_" + tid.lower().replace("-", "_"),
        idx="", extra_t1="", t2type="TINYINT", t2vals="(1), (127), (-128)",
        probes="", meta=META_SQL.format(tid=tid, ct="'smallint'",
                                        t1="t1_" + tid.lower().replace("-", "_")))))

    # NC2: 声明 alter=SUCCESS，但目标列在索引里 -> INSTANT 实际失败(1845)
    tid = "TC-90-NC2-IT"
    t1 = "t1_" + tid.lower().replace("-", "_")
    alter = "ALTER TABLE %s MODIFY target SMALLINT, ALGORITHM=instant" % t1
    cases.append(("NC2_alter_declared_success_but_fails", tid, BASE.format(
        tid=tid, algo="instant", exp="SUCCESS", nassert=2, errno="",
        sha=" alter_sha=%s" % sha1_12(alter + ";"),
        t1=t1, t2="t2_" + tid.lower().replace("-", "_"),
        idx=", INDEX idx_target (target)", extra_t1="", t2type="SMALLINT",
        t2vals="(1), (127), (-128)", probes="",
        meta=META_SQL.format(tid=tid, ct="'smallint'", t1=t1))))

    # NC3: META 断言里写错期望列类型 -> META 必须判 FAIL
    tid = "TC-90-NC3-IP"
    t1 = "t1_" + tid.lower().replace("-", "_")
    alter = "ALTER TABLE %s MODIFY target SMALLINT, ALGORITHM=inplace" % t1
    cases.append(("NC3_wrong_expected_column_type", tid, BASE.format(
        tid=tid, algo="inplace", exp="SUCCESS", nassert=2, errno="",
        sha=" alter_sha=%s" % sha1_12(alter + ";"),
        t1=t1, t2="t2_" + tid.lower().replace("-", "_"),
        idx="", extra_t1="", t2type="SMALLINT", t2vals="(1), (127), (-128)",
        probes="", meta=META_SQL.format(tid=tid, ct="'bigint'", t1=t1))))

    # NC4: 声明探针应被接受(ACCEPTED)，但 STRICT 下它必然报错 -> NEG_ERRNO 必须判 FAIL
    tid = "TC-90-NC4-IP"
    t1 = "t1_" + tid.lower().replace("-", "_")
    t2 = "t2_" + tid.lower().replace("-", "_")
    alter = "ALTER TABLE %s MODIFY target SMALLINT, ALGORITHM=inplace" % t1
    probe1 = "INSERT INTO %s (target) VALUES (999999999999)" % t1
    probes = ("SET @nb1 = (SELECT COUNT(*) FROM %s);\n"
              "SET @nb2 = (SELECT COUNT(*) FROM %s);\n%s;\n%s;\n"
              "SELECT '%s#NEG_REJECTED' AS test_id,\n"
              "       IF((SELECT COUNT(*) FROM %s)-@nb1 = (SELECT COUNT(*) FROM %s)-@nb2,'PASS','FAIL') AS result,\n"
              "       CONCAT('t1=',(SELECT COUNT(*) FROM %s)-@nb1,' t2=',(SELECT COUNT(*) FROM %s)-@nb2) AS mismatch;\n"
              % (t1, t2, probe1, probe1.replace(t1, t2), tid, t1, t2, t1, t2))
    cases.append(("NC4_probe_declared_accepted_but_rejected", tid, BASE.format(
        tid=tid, algo="inplace", exp="SUCCESS", nassert=3, errno="",
        sha=" alter_sha=%s neg_probe=%s=ACCEPTED neg_probe=%s=ACCEPTED"
            % (sha1_12(alter + ";"), sha1_12(probe1), sha1_12(probe1.replace(t1, t2))),
        t1=t1, t2=t2, idx="", extra_t1="", t2type="SMALLINT",
        t2vals="(1), (127), (-128)", probes=probes,
        meta=META_SQL.format(tid=tid, ct="'smallint'", t1=t1))))

    # NC5: 声明 assertions=2 但只产出 1 条判定行 -> ASSERTION_COUNT 必须判 ERROR
    tid = "TC-90-NC5-IP"
    t1 = "t1_" + tid.lower().replace("-", "_")
    alter = "ALTER TABLE %s MODIFY target SMALLINT, ALGORITHM=inplace" % t1
    cases.append(("NC5_missing_assertion_row", tid, BASE.format(
        tid=tid, algo="inplace", exp="SUCCESS", nassert=2, errno="",
        sha=" alter_sha=%s" % sha1_12(alter + ";"),
        t1=t1, t2="t2_" + tid.lower().replace("-", "_"),
        idx="", extra_t1="", t2type="SMALLINT", t2vals="(1), (127), (-128)",
        probes="", meta="")))

    # NC6: 对照表故意少一行 -> PRIMARY 必须判 FAIL（数据 oracle 有效）
    tid = "TC-90-NC6-IP"
    t1 = "t1_" + tid.lower().replace("-", "_")
    alter = "ALTER TABLE %s MODIFY target SMALLINT, ALGORITHM=inplace" % t1
    cases.append(("NC6_oracle_data_mismatch", tid, BASE.format(
        tid=tid, algo="inplace", exp="SUCCESS", nassert=2, errno="",
        sha=" alter_sha=%s" % sha1_12(alter + ";"),
        t1=t1, t2="t2_" + tid.lower().replace("-", "_"),
        idx="", extra_t1="", t2type="SMALLINT", t2vals="(1), (127)",   # 少一行
        probes="", meta=META_SQL.format(tid=tid, ct="'smallint'", t1=t1))))

    return cases


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--env", default="aliyun")
    ap.add_argument("--config", default=os.path.join(ROOT, "config.ini"))
    ap.add_argument("--workers", type=int, default=2)
    args = ap.parse_args()

    tmp = tempfile.mkdtemp(prefix="ddl_nc_")
    sql_dir = os.path.join(tmp, "sql")
    out_dir = os.path.join(tmp, "results")
    os.makedirs(sql_dir)
    os.makedirs(out_dir)
    cases = build_cases()
    path = os.path.join(sql_dir, "90_negative_control.sql")
    with open(path, "w", encoding="utf-8") as fh:
        fh.write("SET SESSION sql_mode = 'STRICT_TRANS_TABLES';\n\n")
        for _name, _tid, text in cases:
            fh.write(text + "\n\n")

    cmd = [sys.executable, os.path.join(ROOT, "run_tests.py"), "--env", args.env,
           "--config", args.config, "--sql-dir", sql_dir, "--out-dir", out_dir,
           "--workers", str(args.workers)]
    print("运行反向对照: %s" % " ".join(cmd))
    proc = subprocess.run(cmd, capture_output=True, text=True)
    print(proc.stdout[-2500:])

    details = os.path.join(out_dir, "details_%s.jsonl" % args.env)
    if not os.path.exists(details):
        print("!! 没有产出结果文件，反向对照无法判定")
        shutil.rmtree(tmp, ignore_errors=True)
        return 2
    by_id = {}
    with open(details) as fh:
        for line in fh:
            r = json.loads(line)
            by_id[r["test_id"]] = r

    expect_caught = {
        "TC-90-NC1-IP": ("FAIL", "ALTER_OUTCOME"),
        "TC-90-NC2-IT": ("FAIL", "ALTER_OUTCOME"),
        "TC-90-NC3-IP": ("FAIL", "META"),
        "TC-90-NC4-IP": ("FAIL", "NEG_ERRNO"),
        "TC-90-NC5-IP": ("ERROR", None),
        "TC-90-NC6-IP": ("FAIL", "PRIMARY"),
    }
    ok = True
    print("=" * 78)
    print("反向对照结果（每一项都必须被抓到，否则说明断言恒过）")
    print("=" * 78)
    for tid, (want_status, want_assert) in expect_caught.items():
        r = by_id.get(tid)
        name = next((n for n, t, _x in cases if t == tid), tid)
        if r is None:
            print("  ✗ %-42s 用例根本没执行" % name)
            ok = False
            continue
        hit = r["status"] == want_status
        if want_assert:
            hit = hit and any(a["name"].startswith(want_assert) and a["result"] != "PASS"
                              for a in r.get("assertions") or [])
        print("  %s %-42s status=%-6s 期望=%-6s 触发断言=%s"
              % ("✓" if hit else "✗", name, r["status"], want_status,
                 [a["name"] for a in (r.get("assertions") or []) if a["result"] != "PASS"]))
        if not hit:
            ok = False
            print("      mismatch: %s" % r.get("mismatch", "")[:200])
    shutil.rmtree(tmp, ignore_errors=True)
    print("=" * 78)
    print("反向对照: %s" % ("全部 6 类缺陷均被捕获 ✅" if ok else "存在漏抓 ❌"))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
