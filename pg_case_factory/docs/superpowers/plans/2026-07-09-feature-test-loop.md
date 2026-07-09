# Feature Test Loop Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a repository-backed loop layer that can execute generated SQL, audit execution reports, diagnose failures, and produce feedback promotion candidates.

**Architecture:** Keep expert knowledge in skill references, keep deterministic report checks and transformations in Python tools, and wire the loop through a mainflow reference. Artifacts remain under `artifacts/evaluations/` and `artifacts/intermediates/` so each test iteration is inspectable.

**Tech Stack:** Python standard library, PyYAML, pytest/unittest, existing pg_case_factory skill references.

---

### Task 1: Loop Policy References

**Files:**
- Create: `skills/pg-sql-generation/references/common/execution_loop_policy.md`
- Create: `skills/pg-sql-generation/references/common/query_oracle_policy.md`
- Create: `skills/pg-sql-generation/references/common/failure_diagnosis_policy.md`
- Create: `skills/pg-sql-generation/references/common/feedback_promotion_policy.md`
- Create: `skills/pg-sql-generation/references/templates/feature_test_intake_template.md`
- Create: `skills/pg-sql-generation/references/mainflow/run_feature_test_loop.md`
- Modify: `skills/pg-sql-generation/SKILL.md`
- Modify: `README.md`

- [ ] Add policy references that define loop stages, query oracle rules, failure categories, and feedback promotion rules.
- [ ] Add a mainflow that ties feature intake, factor association, SQL generation, execution, diagnosis, and promotion into one repeatable loop.

### Task 2: Deterministic Loop Tools

**Files:**
- Create: `tools/run_generated_sql.py`
- Create: `tools/audit_execution_report.py`
- Create: `tools/diagnose_execution_failures.py`
- Create: `tools/promote_execution_feedback.py`
- Test: `tests/test_feature_test_loop_tools.py`

- [ ] Write failing tests for execution report audit, diagnosis classification, promotion candidates, and runner behavior with a fake SQL executor.
- [ ] Implement small deterministic CLIs that read/write YAML artifacts.

### Task 3: Verification

**Commands:**
- `env PYTHONDONTWRITEBYTECODE=1 python3 -m pytest -q -p no:cacheprovider`
- `env PYTHONDONTWRITEBYTECODE=1 python3 tools/audit_combination_matrix.py --root .`
- `env PYTHONDONTWRITEBYTECODE=1 python3 tools/audit_factor_catalog_mapping.py --root .`
- `git diff --check`

- [ ] Run all commands and only commit after successful output.
