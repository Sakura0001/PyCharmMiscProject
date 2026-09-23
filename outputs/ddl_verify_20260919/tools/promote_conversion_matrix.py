#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把 MEASURE 模式的实测兼容矩阵冻结为 golden 基线。

流程：
  1. python3 run_tests.py --env aliyun --files 40_conversion_matrix.sql
     -> results/conversion_matrix_aliyun.json（实测）
  2. 人工复核这份实测结果（哪些该支持、哪些该拒绝、errno 是否合理）
  3. python3 tools/promote_conversion_matrix.py --env aliyun
     -> tools/conversion_matrix_aliyun.json（golden）
  4. python3 generate_test_sql.py 重新生成 -> 之后每轮都按 golden 硬断言，
     任何行为变化都会被 ALTER_OUTCOME 判 FAIL

只 promote 明确一致的条目：alter=INCONSISTENT 的会被拒绝并打印出来。
"""
import os
import sys
import json
import argparse

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--env", default="aliyun")
    ap.add_argument("--src", default=None)
    ap.add_argument("--dst", default=None)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    src = args.src or os.path.join(ROOT, "results", "conversion_matrix_%s.json" % args.env)
    dst = args.dst or os.path.join(HERE, "conversion_matrix_%s.json" % args.env)
    if not os.path.exists(src):
        print("找不到实测矩阵 %s（先跑 --files 40_conversion_matrix.sql）" % src)
        return 2
    with open(src) as fh:
        data = json.load(fh)
    matrix = data.get("matrix", {})
    good, bad = {}, []
    for k, v in matrix.items():
        if v.get("alter") == "INCONSISTENT":
            bad.append((k, v))
            continue
        good[k] = {"alter": v["alter"], "errno": v.get("errnos") or []}
    print("实测条目 %d，可冻结 %d，不一致需人工排查 %d" % (len(matrix), len(good), len(bad)))
    for k, v in bad:
        print("  !! %s -> %s" % (k, v))
    if args.dry_run:
        return 0
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    with open(dst, "w", encoding="utf-8") as fh:
        json.dump({"env": args.env, "source": os.path.basename(src),
                   "promoted_at": data.get("generated_at"), "count": len(good),
                   "matrix": good}, fh, ensure_ascii=False, indent=1)
    print("已写入 golden: %s（%d 条）" % (dst, len(good)))
    print("下一步：python3 generate_test_sql.py 重新生成，之后按 golden 硬断言")
    return 0


if __name__ == "__main__":
    sys.exit(main())
