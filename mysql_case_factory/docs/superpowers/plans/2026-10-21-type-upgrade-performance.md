# Type-upgrade performance Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build an adaptive large-table performance batch that measures all-inplace, all-instant, mixed, source, and reference performance across every SQL-direct upgradeable type family.

**Architecture:** A deterministic schema module defines source/target columns, data-generation SQL, full-scan SQL, and DDL scenarios. A PyMySQL runner calibrates row count, creates source/reference/candidate tables, executes each DDL scenario, records DDL/query/DML timing, and compares candidate/reference aggregates. An auditor validates artifacts and local smoke evidence.

**Tech Stack:** Python 3.12, pytest, PyMySQL, MySQL 8.0 online DDL, `EXPLAIN ANALYZE`.

---

### Task 1: Schema and scenario model

- Create `src/mysql_case_factory/type_upgrade_performance.py`.
- Define all source/target columns, noise columns, indexes, and six scenarios.
- Implement source/reference create SQL, data-generation SQL, full-scan SQL, and DDL SQL.
- Add unit tests for schema coverage and SQL rendering.

### Task 2: Runner

- Create `src/mysql_case_factory/type_upgrade_performance_runner.py`.
- Implement calibration, table creation, data generation, DDL, query timing,
  DML timing, aggregate comparison, result JSONL, and summary output.
- Add CLI options for rows, calibration rows, target scan seconds, max rows,
  scenario selection, and connection settings.
- Add unit tests for classification, calibration, SQL, and CLI.

### Task 3: Generator and artifacts

- Create `tools/generate_type_upgrade_performance.py`.
- Write manifest, cases, coverage, and README.
- Add deterministic generation tests.

### Task 4: Auditor

- Create `src/mysql_case_factory/type_upgrade_performance_audit.py`.
- Create `tools/audit_type_upgrade_performance.py`.
- Validate six scenarios, complete type coverage, hashes, and local evidence.
- Add audit tests.

### Task 5: Documentation and regression integration

- Create `docs/type_upgrade_performance_v1.md`.
- Update README and full-regression inventory.
- Add the batch as the eleventh mandatory batch.

### Task 6: Verification

- Generate artifacts.
- Run local smoke on MySQL 8.0.45.
- Run the auditor.
- Run the full test suite.
- Commit, merge, push, and clean the worktree.
