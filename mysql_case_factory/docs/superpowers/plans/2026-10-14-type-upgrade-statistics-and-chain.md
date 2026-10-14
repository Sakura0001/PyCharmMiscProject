# Type-upgrade statistics and chain implementation plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a `TUCS` batch covering optimizer statistics and consecutive type upgrades without modifying the verified `TUC`/`TUCX` batches.

**Architecture:** Extend the shared case model with pre-DDL statements, statistics phases, and analyze statements. Add a dedicated statistics/chain generator and audit tool. Generalize the runner to execute pre-DDL, stats checks, analyze, and post-analyze checks while preserving existing behavior.

**Tech Stack:** Python 3.10+, PyMySQL, pytest, gzip/JSON deterministic artifacts, MySQL 8.0.45.

---

### Task 1: Extend case model and runner phases

**Files:**
- Modify: `mysql_case_factory/src/mysql_case_factory/type_upgrade_consistency.py`
- Modify: `mysql_case_factory/src/mysql_case_factory/type_upgrade_runner.py`
- Test: `mysql_case_factory/tests/test_type_upgrade_runner.py`

- [ ] Add fields: `pre_ddl_sql`, `stats_pre_analyze_sql`, `analyze_sql`, `stats_post_analyze_sql`.
- [ ] Serialize and load the new fields.
- [ ] Render them in generated SQL suites.
- [ ] Execute `pre_ddl_sql` before the main DDL.
- [ ] Execute stats checks, analyze statements, and post-analyze checks in order.
- [ ] Preserve crash classification and interrupt propagation.
- [ ] Run focused tests and commit.

### Task 2: Statistics and chain generator

**Files:**
- Create: `mysql_case_factory/src/mysql_case_factory/type_upgrade_statistics.py`
- Create: `mysql_case_factory/tools/generate_type_upgrade_statistics.py`
- Test: `mysql_case_factory/tests/test_type_upgrade_statistics.py`

- [ ] Define the `TUCS` batch identity and parent link.
- [ ] Generate representative cases across integer, DECIMAL, character, binary, and BIT.
- [ ] Cover table stats, index stats, information schema, EXPLAIN, and partitions.
- [ ] Generate chained `SMALLINT -> INT -> BIGINT` cases.
- [ ] Generate duplicate-MODIFY negative cases.
- [ ] Emit deterministic `cases.jsonl.gz` and three profile suites.
- [ ] Run focused tests and commit.

### Task 3: Audit and documentation

**Files:**
- Create: `mysql_case_factory/src/mysql_case_factory/type_upgrade_statistics_audit.py`
- Create: `mysql_case_factory/tools/audit_type_upgrade_statistics.py`
- Create: `mysql_case_factory/docs/type_upgrade_statistics_and_chain_v1.md`
- Modify: `mysql_case_factory/README.md`

- [ ] Audit batch identity, parent link, artifact hashes, profile counts, case uniqueness, and semantic coverage.
- [ ] Require statistics constructs and chain constructs.
- [ ] Document `TUC` / `TUCX` / `TUCS` separation and internal-AI execution rules.
- [ ] Run tests and commit.

### Task 4: Full verification

- [ ] Run `pytest -q`.
- [ ] Run every `TUCS` case with local MySQL 8.0.45 `COPY`.
- [ ] Verify all results are PASS.
- [ ] Verify `TUC` and `TUCX` artifacts remain unchanged.
- [ ] Independent review.
- [ ] Merge into `codex/ddl-verify-20260919`.
- [ ] Push.
