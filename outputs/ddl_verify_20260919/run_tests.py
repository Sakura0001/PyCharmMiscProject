#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RDS MySQL DDL 秒级/在线修改列类型 — 测试执行器 v2
================================================================
Uses mysql CLI with --force to execute SQL files, parses output for PASS/FAIL.
Much more robust than statement-by-statement execution.
"""

import os
import sys
import re
import csv
import time
import argparse
import configparser
import subprocess
from typing import List, Dict, Tuple, Optional

OUTPUT_DIR = os.path.dirname(os.path.abspath(__file__))
SQL_ALIYUN = os.path.join(OUTPUT_DIR, "sql_aliyun")
SQL_INTERNAL = os.path.join(OUTPUT_DIR, "sql_internal")
RESULTS_DIR = os.path.join(OUTPUT_DIR, "results")


def parse_metadata(sql_file: str) -> Dict[str, dict]:
    """Pre-parse SQL file to extract test case metadata from comments."""
    metadata = {}
    current_tc = None

    with open(sql_file, 'r', encoding='utf-8') as f:
        for line in f:
            # Match: -- Test Case: TC-XXX
            m = re.search(r'Test Case:\s*(TC-\S+)', line)
            if m:
                current_tc = m.group(1)
                metadata[current_tc] = {
                    "test_id": current_tc,
                    "type": "",
                    "algorithm": "",
                    "expected": "",
                    "partition_key": False,
                }
                continue

            if current_tc:
                # Match: -- Type: XXX, Algorithm: XXX, Expected: XXX
                m = re.search(r'Type:\s*(.+?),\s*Algorithm:\s*(\w+)(?:,\s*Expected:\s*(\w+))?', line)
                if m:
                    metadata[current_tc]["type"] = m.group(1).strip()
                    metadata[current_tc]["algorithm"] = m.group(2).lower()
                    if m.group(3):
                        metadata[current_tc]["expected"] = m.group(3).upper()

                # Match: -- Expected: ALTER SUCCESS/FAIL
                m = re.search(r'^--\s*Expected:\s*ALTER\s+(\w+)', line)
                if m:
                    metadata[current_tc]["expected"] = m.group(1).upper()
                # Match: -- Expected ALTER: FAIL
                elif re.search(r'Expected ALTER:\s*\w+', line):
                    m2 = re.search(r'Expected ALTER:\s*(\w+)', line)
                    if m2:
                        metadata[current_tc]["expected"] = m2.group(1).upper()
                # Match: -- Expected: FAIL/SUCCESS (standalone, not "ALTER")
                elif re.search(r'^--\s*Expected:\s*(?!ALTER)', line):
                    m2 = re.search(r'^--\s*Expected:\s*(\w+)', line)
                    if m2:
                        metadata[current_tc]["expected"] = m2.group(1).upper()

                # Match: -- Target is partition key: True
                m = re.search(r'Target is partition key:\s*(True|False)', line, re.IGNORECASE)
                if m:
                    metadata[current_tc]["partition_key"] = (m.group(1).lower() == "true")

    return metadata


def execute_sql_file(filepath: str, db_config: dict, timeout: int = 7200) -> Tuple[List[Dict], str]:
    """
    Execute SQL file using mysql CLI with --force.
    Returns (results_list, stderr_excerpt).
    """
    metadata = parse_metadata(filepath)

    cmd = [
        "mysql",
        f"--host={db_config['host']}",
        f"--port={db_config['port']}",
        f"--user={db_config['user']}",
        f"--password={db_config['password']}",
        "--default-character-set=utf8mb4",
        "--force",
        "--batch",
        "--skip-column-names",
        "--unbuffered",
        db_config['database'],
    ]

    with open(filepath, 'r', encoding='utf-8') as f:
        try:
            proc = subprocess.run(
                cmd,
                stdin=f,
                capture_output=True,
                text=True,
                timeout=timeout,
            )
        except subprocess.TimeoutExpired:
            return [], f"TIMEOUT after {timeout}s"

    stderr_excerpt = proc.stderr[-2000:] if proc.stderr else ""

    # Parse stdout for result rows
    results = []
    seen_test_ids = set()

    for line in proc.stdout.strip().split('\n'):
        line = line.strip()
        if not line:
            continue

        parts = line.split('\t')
        if len(parts) < 2:
            continue

        test_id = parts[0].strip()
        if not re.match(r'^TC-', test_id):
            continue

        result_val = parts[1].strip()
        mismatch = parts[2].strip() if len(parts) > 2 else ""

        seen_test_ids.add(test_id)
        meta = metadata.get(test_id, {})

        # Determine status
        if result_val == "PASS":
            status = "PASS"
        elif result_val == "FAIL":
            status = "FAIL"
        elif result_val in ("BUILD_OR_ALTER_FAIL_EXPECTED", "BUILD_FAIL_EXPECTED"):
            status = "MANUAL"
            result_val = "BUILD_OR_ALTER_FAIL_EXPECTED"
        else:
            status = "UNKNOWN"

        results.append({
            "test_id": test_id,
            "type": meta.get("type", ""),
            "algorithm": meta.get("algorithm", ""),
            "expected": meta.get("expected", ""),
            "result": result_val,
            "status": status,
            "mismatch": mismatch[:500] if mismatch else "",
        })

    # Find test cases that didn't produce output (likely execution errors)
    for tc_id, meta in metadata.items():
        if tc_id not in seen_test_ids:
            results.append({
                "test_id": tc_id,
                "type": meta.get("type", ""),
                "algorithm": meta.get("algorithm", ""),
                "expected": meta.get("expected", ""),
                "result": "NO_OUTPUT",
                "status": "ERROR",
                "mismatch": "No result SELECT in output - likely execution error",
            })

    return results, stderr_excerpt


def run_tests(config: configparser.ConfigParser, env: str, files: List[str] = None):
    """Run tests for the specified environment."""
    if env not in config:
        print(f"Error: No configuration for environment '{env}'")
        return []

    db_config = {
        "host": config[env].get("host", "127.0.0.1"),
        "port": str(config[env].get("port", 3306)),
        "user": config[env].get("user", "root"),
        "password": config[env].get("password", ""),
        "database": config[env].get("database", "ddl_test"),
    }

    sql_dir = SQL_ALIYUN if env == "aliyun" else SQL_INTERNAL

    # Determine which files to run
    if files:
        sql_files = []
        for f in files:
            path = os.path.join(sql_dir, f) if not os.path.isabs(f) else f
            if os.path.exists(path):
                sql_files.append(path)
            else:
                # Try with .sql extension
                path2 = path if path.endswith('.sql') else path + '.sql'
                if os.path.exists(path2):
                    sql_files.append(path2)
                else:
                    print(f"  WARNING: File not found: {f}")
    else:
        sql_files = sorted([
            os.path.join(sql_dir, f) for f in os.listdir(sql_dir)
            if f.endswith('.sql')
        ])

    if not sql_files:
        print(f"No SQL files found in {sql_dir}")
        return []

    # Ensure results dir exists
    os.makedirs(RESULTS_DIR, exist_ok=True)

    all_results = []
    total_pass = 0
    total_fail = 0
    total_error = 0
    total_manual = 0

    print(f"\n{'=' * 60}")
    print(f"Running {env.upper()} tests ({len(sql_files)} files)")
    print(f"{'=' * 60}\n")

    # Clear previous failures log
    failures_log = os.path.join(RESULTS_DIR, "failures.log")
    open(failures_log, 'w').close()

    for filepath in sql_files:
        filename = os.path.basename(filepath)
        file_size_mb = os.path.getsize(filepath) / (1024 * 1024)

        # Set timeout based on file size (partition files are huge)
        if file_size_mb > 10:
            timeout = 7200  # 2 hours for large partition files
        elif file_size_mb > 1:
            timeout = 1800  # 30 minutes for medium files
        else:
            timeout = 600  # 10 minutes for small files

        print(f"  Running: {filename} ({file_size_mb:.1f}MB)...", end=" ", flush=True)
        start_time = time.time()

        try:
            file_results, stderr = execute_sql_file(filepath, db_config, timeout)
            elapsed = time.time() - start_time

            file_pass = sum(1 for r in file_results if r.get("status") == "PASS")
            file_fail = sum(1 for r in file_results if r.get("status") == "FAIL")
            file_error = sum(1 for r in file_results if r.get("status") == "ERROR")
            file_manual = sum(1 for r in file_results if r.get("status") == "MANUAL")

            total_pass += file_pass
            total_fail += file_fail
            total_error += file_error
            total_manual += file_manual

            print(f"PASS={file_pass}, FAIL={file_fail}, ERROR={file_error}, MANUAL={file_manual} ({elapsed:.1f}s)")

            all_results.extend(file_results)

            # Log failures immediately
            failures = [r for r in file_results if r.get("status") in ("FAIL", "ERROR")]
            if failures:
                with open(failures_log, "a", encoding="utf-8") as flog:
                    flog.write(f"\n{'=' * 60}\n")
                    flog.write(f"File: {filename}\n")
                    flog.write(f"{'=' * 60}\n")
                    for fail in failures:
                        flog.write(f"\nTest ID: {fail.get('test_id', 'N/A')}\n")
                        flog.write(f"  Type: {fail.get('type', 'N/A')}\n")
                        flog.write(f"  Algorithm: {fail.get('algorithm', 'N/A')}\n")
                        flog.write(f"  Expected: {fail.get('expected', 'N/A')}\n")
                        flog.write(f"  Result: {fail.get('result', 'N/A')}\n")
                        flog.write(f"  Mismatch: {fail.get('mismatch', 'N/A')}\n")

            # Log stderr if there were errors
            if stderr and file_error > 0:
                with open(failures_log, "a", encoding="utf-8") as flog:
                    flog.write(f"\n--- stderr (last 2000 chars) ---\n")
                    flog.write(stderr[:2000])
                    flog.write("\n")

        except Exception as e:
            elapsed = time.time() - start_time
            print(f"ERROR: {str(e)[:200]} ({elapsed:.1f}s)")
            all_results.append({
                "test_id": filename,
                "type": "",
                "algorithm": "",
                "expected": "",
                "result": "FILE_ERROR",
                "status": "ERROR",
                "mismatch": str(e)[:500],
            })
            total_error += 1

    # Write summary CSV
    csv_path = os.path.join(RESULTS_DIR, f"summary_{env}.csv")
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "test_id", "type", "algorithm", "expected", "result", "status", "mismatch"
        ])
        writer.writeheader()
        writer.writerows(all_results)

    # Print summary
    print(f"\n{'=' * 60}")
    print(f"SUMMARY ({env})")
    print(f"{'=' * 60}")
    print(f"  Total test results: {len(all_results)}")
    print(f"  PASS:   {total_pass}")
    print(f"  FAIL:   {total_fail}")
    print(f"  ERROR:  {total_error}")
    print(f"  MANUAL: {total_manual}")
    print(f"  Results written to: {csv_path}")
    if total_fail > 0 or total_error > 0:
        print(f"  Failures logged to: {os.path.join(RESULTS_DIR, 'failures.log')}")
    print()

    return all_results


def main():
    parser = argparse.ArgumentParser(description="RDS MySQL DDL Test Runner v2")
    parser.add_argument("--config", default=os.path.join(OUTPUT_DIR, "config.ini"),
                        help="Path to config.ini file")
    parser.add_argument("--env", choices=["aliyun", "internal", "both"], default="aliyun",
                        help="Environment to test")
    parser.add_argument("--files", nargs="*", help="Specific SQL files to run (by name)")
    args = parser.parse_args()

    config = configparser.ConfigParser()
    if os.path.exists(args.config):
        config.read(args.config)
    else:
        print(f"Config file not found: {args.config}")
        print(f"Example config at: {os.path.join(OUTPUT_DIR, 'config.example.ini')}")
        sys.exit(1)

    all_results = []
    if args.env in ("aliyun", "both"):
        results = run_tests(config, "aliyun", args.files)
        all_results.extend(results)

    if args.env in ("internal", "both"):
        results = run_tests(config, "internal", args.files)
        all_results.extend(results)

    # Overall summary
    total = len(all_results)
    total_pass = sum(1 for r in all_results if r.get("status") == "PASS")
    total_fail = sum(1 for r in all_results if r.get("status") == "FAIL")
    total_error = sum(1 for r in all_results if r.get("status") == "ERROR")
    total_manual = sum(1 for r in all_results if r.get("status") == "MANUAL")

    print(f"\n{'=' * 60}")
    print(f"OVERALL SUMMARY")
    print(f"{'=' * 60}")
    print(f"  Total:  {total}")
    print(f"  PASS:   {total_pass}")
    print(f"  FAIL:   {total_fail}")
    print(f"  ERROR:  {total_error}")
    print(f"  MANUAL: {total_manual}")
    if total > 0:
        pass_rate = total_pass / total * 100
        print(f"  Pass Rate: {pass_rate:.1f}%")


if __name__ == "__main__":
    main()
