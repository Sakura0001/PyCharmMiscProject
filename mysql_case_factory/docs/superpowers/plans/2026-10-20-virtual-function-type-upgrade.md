# Virtual/function type-upgrade Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a 5,136-scenario batch that proves virtual generated columns, stored generated columns, and functional indexes do not corrupt data or change type-upgrade algorithm behavior.

**Architecture:** A deterministic scenario module reuses the existing 107 type transitions and expands them by dependency mode, algorithm, data state, and nullability. A PyMySQL runner creates control/candidate/reference tables, applies the selected DDL, compares successful upgrades against a direct target-type reference, and verifies failed upgrades leave data unchanged. An auditor validates artifacts and local evidence.

**Tech Stack:** Python 3.12, pytest, PyMySQL, MySQL 8.0 online DDL.

---

### Task 1: Scenario model

- Create `src/mysql_case_factory/virtual_function_type_upgrade.py`.
- Define constants and `VirtualFunctionScenario`.
- Implement the exact 5,136-case lazy iterator.
- Add unit tests for matrix completeness and IDs.

### Task 2: Runner

- Create `src/mysql_case_factory/virtual_function_type_upgrade_runner.py`.
- Implement control/candidate/reference table creation.
- Implement DDL execution, DML, schema/data comparison, and classification.
- Add `--smoke`, `--all`, `--case-id`, connection, and row-count options.
- Add unit tests for SQL rendering and classification.

### Task 3: Generator and artifacts

- Create `tools/generate_virtual_function_type_upgrade.py`.
- Write manifest, cases, coverage, and README.
- Add deterministic generation tests.

### Task 4: Auditor

- Create `src/mysql_case_factory/virtual_function_type_upgrade_audit.py`.
- Create `tools/audit_virtual_function_type_upgrade.py`.
- Validate 5,136 cases, 107 transitions, 4 dependencies, 3 algorithms, hashes, and local evidence.
- Add audit tests.

### Task 5: Documentation and regression integration

- Create `docs/virtual_function_type_upgrade_v1.md`.
- Update README and the full-regression inventory.
- Add the batch as the tenth mandatory batch.

### Task 6: Verification

- Generate artifacts.
- Run local smoke on MySQL 8.0.45.
- Run the auditor.
- Run the full test suite.
- Commit, merge, push, and clean the worktree.
