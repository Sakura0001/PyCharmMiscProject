# Unique-DDL expected-error Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a 192-scenario concurrent runner that proves unique secondary-index DDL fails with 1062 when duplicate-producing DML overlaps the DDL.

**Architecture:** A deterministic scenario module defines the 4 × 6 × 8 matrix. A PyMySQL runner seeds one large table per index shape, reuses it across scenarios, starts DDL and DML on separate connections, records timing and errors, and restores the baseline after every case. An auditor validates the artifact and result evidence.

**Tech Stack:** Python 3.12, pytest, PyMySQL, MySQL 8.0 online DDL.

---

### Task 1: Scenario model

- Create `src/mysql_case_factory/unique_ddl_expected_error.py`.
- Define constants and `UniqueDDLErrorScenario`.
- Implement the exact 192-case lazy iterator.
- Add unit tests for matrix completeness, IDs, and expected SQL.

### Task 2: Runner

- Create `src/mysql_case_factory/unique_ddl_expected_error_runner.py`.
- Implement shape table creation, seeding, reset, DDL, DML, timing, classification, and result output.
- Add `--smoke`, `--all`, `--case-id`, connection, row-count, and delay options.
- Add unit tests for SQL rendering, DML generation, and classification.

### Task 3: Generator and artifacts

- Create `tools/generate_unique_ddl_expected_error.py`.
- Write manifest, cases, coverage, and README.
- Add deterministic generation tests.

### Task 4: Auditor

- Create `src/mysql_case_factory/unique_ddl_expected_error_audit.py`.
- Create `tools/audit_unique_ddl_expected_error.py`.
- Validate 192 cases, 4 DDL forms, 6 shapes, 8 DML types, hashes, and local evidence.
- Add audit tests.

### Task 5: Documentation and regression integration

- Create `docs/unique_ddl_expected_error_v1.md`.
- Update README and the full-regression inventory.
- Add the batch as the ninth mandatory batch.

### Task 6: Verification

- Generate artifacts.
- Run local smoke on MySQL 8.0.45.
- Run the auditor.
- Run the full test suite.
- Commit, merge, push, and clean the worktree.
