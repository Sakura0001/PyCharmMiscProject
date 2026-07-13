# MySQL Dual-Version Case Factory Parity Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Deliver complete, independently packageable MySQL Community Server 8.0.22 and 8.0.41 editions on one PG-v0.2-parity control plane.

**Architecture:** Port the proven PG v0.2 control-plane boundaries, replace PostgreSQL execution semantics with a version-bound MySQL CLI runner, and keep all SQL knowledge in two closed edition snapshots. Every formal artifact binds the edition and execution-profile digests.

**Tech Stack:** Python 3.10+, setuptools, PyYAML, pytest, MySQL 8.0 CLI, optional Docker Compose smoke harness.

---

### Task 1: Commit the approved design and executable plan

**Files:**
- Create: `mysql_case_factory/docs/superpowers/specs/2026-07-13-mysql-dual-version-parity-design.md`
- Create: `mysql_case_factory/docs/superpowers/plans/2026-07-13-mysql-dual-version-parity.md`

- [ ] **Step 1: Scan both documents for incomplete language**

Run: `rg -n 'T''BD|T''ODO|implement'' later|fill'' in|place''holder' mysql_case_factory/docs/superpowers`

Expected: no matches.

- [ ] **Step 2: Commit and push the approved documents**

```bash
git add mysql_case_factory/docs/superpowers
git commit -m "docs(mysql-case-factory): design dual-version parity"
git push -u origin codex/mysql-8022-8041-parity
```

Expected: commit and new remote branch succeed.

### Task 2: Define edition discovery and closed contracts with TDD

**Files:**
- Create: `mysql_case_factory/tests/test_editions.py`
- Create: `mysql_case_factory/src/mysql_case_factory/editions.py`
- Create: `mysql_case_factory/editions/mysql_8_0_22/edition.yaml`
- Create: `mysql_case_factory/editions/mysql_8_0_41/edition.yaml`

- [ ] **Step 1: Write tests for exact edition IDs, versions, contained paths, unknown-key rejection, digest/count verification, and cross-edition rejection**

The public API is:

```python
edition = load_edition(path, repository_root=root, verify_files=True)
assert edition.edition_id == "mysql-community-8.0.22"
assert edition.target_version == "8.0.22"
assert edition.target_version_num == 80022
assert resolve_edition(root, "8.0.22") == edition_root
```

- [ ] **Step 2: Run the focused test and verify RED**

Run: `PYTHONPATH=mysql_case_factory/src python3 -m pytest -q mysql_case_factory/tests/test_editions.py`

Expected: import failure for `mysql_case_factory.editions`.

- [ ] **Step 3: Implement immutable edition dataclasses, YAML loading, schema validation, containment, digest/count checks, and aliases**

Edition aliases are only `8.0.22`, `80022`, `mysql-community-8.0.22`, `8.0.41`, `80041`, and `mysql-community-8.0.41`. Ambiguous or rolling aliases such as `8.0` and `latest` are rejected.

- [ ] **Step 4: Run focused and existing tests**

Run: `PYTHONPATH=mysql_case_factory/src python3 -m pytest -q mysql_case_factory/tests/test_editions.py mysql_case_factory/tests/test_*audit.py`

Expected: all selected tests pass.

### Task 3: Port PG v0.2 contracts, coverage, artifacts, jobs, applicability, and regression behavior

**Files:**
- Create or replace: `mysql_case_factory/tests/test_feature_contracts.py`
- Create or replace: `mysql_case_factory/tests/test_inventory.py`
- Create or replace: `mysql_case_factory/tests/test_coverage.py`
- Create or replace: `mysql_case_factory/tests/test_artifact_runs.py`
- Create or replace: `mysql_case_factory/tests/test_jobs.py`
- Create or replace: `mysql_case_factory/tests/test_applicability.py`
- Create or replace: `mysql_case_factory/tests/test_regression_style.py`
- Create: `mysql_case_factory/src/mysql_case_factory/contracts.py`
- Create: `mysql_case_factory/src/mysql_case_factory/feature_plan.py`
- Create: `mysql_case_factory/src/mysql_case_factory/inventory.py`
- Create: `mysql_case_factory/src/mysql_case_factory/coverage.py`
- Replace: `mysql_case_factory/src/mysql_case_factory/artifact_store.py`
- Create: `mysql_case_factory/src/mysql_case_factory/jobs.py`
- Create: `mysql_case_factory/src/mysql_case_factory/applicability.py`
- Create: `mysql_case_factory/src/mysql_case_factory/regression_style.py`

- [ ] **Step 1: Port tests first and replace PG constants with explicit edition fixtures**

All formal manifest fixtures use:

```yaml
compatibility_target:
  engine: mysql-community-server
  edition_id: mysql-community-8.0.22
  version: 8.0.22
  version_num: 80022
```

- [ ] **Step 2: Run the ported tests and verify RED**

Run: `PYTHONPATH=mysql_case_factory/src python3 -m pytest -q mysql_case_factory/tests/test_feature_contracts.py mysql_case_factory/tests/test_inventory.py mysql_case_factory/tests/test_coverage.py mysql_case_factory/tests/test_artifact_runs.py mysql_case_factory/tests/test_jobs.py mysql_case_factory/tests/test_applicability.py mysql_case_factory/tests/test_regression_style.py`

Expected: missing-module and missing-behavior failures.

- [ ] **Step 3: Port the generic implementations, parameterize edition semantics, and remove PostgreSQL-only branches**

Required invariants are strict unknown-key rejection, unresolved-question gate,
complete inventory provenance, stable obligation IDs, exact case/SQL
reconciliation, atomic run creation, evidence-hash state transitions, dependency
DAG validation, and edition digest revalidation.

- [ ] **Step 4: Run the focused suite until GREEN, then the whole MySQL suite**

Run: `PYTHONPATH=mysql_case_factory/src python3 -m pytest -q mysql_case_factory/tests`

Expected: all tests pass without collection errors.

### Task 4: Implement the MySQL differential runner and SQL safety layer

**Files:**
- Create: `mysql_case_factory/tests/test_execution_profile.py`
- Create: `mysql_case_factory/tests/test_differential.py`
- Create: `mysql_case_factory/tests/test_sql_safety.py`
- Create: `mysql_case_factory/src/mysql_case_factory/differential.py`
- Create: `mysql_case_factory/src/mysql_case_factory/formal_run.py`
- Create: `mysql_case_factory/src/mysql_case_factory/sql_safety.py`

- [ ] **Step 1: Write failing tests for login-path profiles, patch parsing, UUID identity, exact comparison, SQLSTATE oracle, lock collisions, and dangerous SQL routing**

The identity query returns one tab-separated row in this order:

```sql
SELECT VERSION(), @@server_uuid, DATABASE(), CURRENT_USER(), @@version_comment;
```

An accepted terminal diagnostic has this shape:

```text
ERROR 1064 (42000) at line 1: syntax error text
```

- [ ] **Step 2: Run and verify RED**

Run: `PYTHONPATH=mysql_case_factory/src python3 -m pytest -q mysql_case_factory/tests/test_execution_profile.py mysql_case_factory/tests/test_differential.py mysql_case_factory/tests/test_sql_safety.py`

Expected: missing MySQL runner/profile/safety behavior.

- [ ] **Step 3: Implement the minimal runner and safety gates**

The runner command contains `--login-path=<name>`, `--database=<name>`,
`--batch`, `--raw`, `--skip-column-names`, `--show-warnings`, and
`--default-character-set=utf8mb4`; it never contains a password, host, port, or
credential URI from the run profile.

- [ ] **Step 4: Run focused and full suites**

Run: `PYTHONPATH=mysql_case_factory/src python3 -m pytest -q mysql_case_factory/tests`

Expected: all tests pass.

### Task 5: Add the CLI and deterministic edition packaging

**Files:**
- Create: `mysql_case_factory/tests/test_cli.py`
- Create: `mysql_case_factory/tests/test_skill_packaging.py`
- Create: `mysql_case_factory/src/mysql_case_factory/cli.py`
- Create: `mysql_case_factory/src/mysql_case_factory/__main__.py`
- Create: `mysql_case_factory/src/mysql_case_factory/skill_packaging.py`
- Modify: `mysql_case_factory/src/mysql_case_factory/__init__.py`
- Modify: `mysql_case_factory/pyproject.toml`

- [ ] **Step 1: Write failing CLI and deterministic-archive tests**

Required scripts are:

```toml
[project.scripts]
mysql-case = "mysql_case_factory.cli:main"
mysql-case-8022 = "mysql_case_factory.cli:main_8022"
mysql-case-8041 = "mysql_case_factory.cli:main_8041"
```

- [ ] **Step 2: Run and verify RED**

Run: `PYTHONPATH=mysql_case_factory/src python3 -m pytest -q mysql_case_factory/tests/test_cli.py mysql_case_factory/tests/test_skill_packaging.py`

Expected: missing entry-point and command failures.

- [ ] **Step 3: Implement doctor, applicability, plan, run, and skill command groups plus deterministic ZIP verification**

Dedicated version entry points inject their exact edition and reject a
conflicting explicit edition.

- [ ] **Step 4: Run the complete suite**

Run: `PYTHONPATH=mysql_case_factory/src python3 -m pytest -q mysql_case_factory/tests`

Expected: all tests pass.

### Task 6: Migrate and complete the 8.0.22 edition

**Files:**
- Move: `mysql_case_factory/skills/mysql-sql-generation/**` to `mysql_case_factory/editions/mysql_8_0_22/skills/mysql-8-0-22-sql-generation/**`
- Create: `mysql_case_factory/editions/mysql_8_0_22/README.md`
- Create: `mysql_case_factory/editions/mysql_8_0_22/skills/mysql-8-0-22-sql-generation/references/common/statement_support_inventory.yaml`
- Create: `mysql_case_factory/editions/mysql_8_0_22/skills/mysql-8-0-22-sql-generation/references/common/mysql_8_0_22_factor_audit.tsv`
- Create missing matrices under: `mysql_case_factory/editions/mysql_8_0_22/skills/mysql-8-0-22-sql-generation/references/combinations/`
- Create: `mysql_case_factory/tests/test_edition_8022_knowledge.py`

- [ ] **Step 1: Write failing audits requiring exact statement/reference/matrix mappings, complete value bindings, no incomplete markers, official locators, and zero unreviewed rows**

Run: `PYTHONPATH=mysql_case_factory/src python3 -m pytest -q mysql_case_factory/tests/test_edition_8022_knowledge.py`

Expected: failures for the old location and incomplete one-matrix inventory.

- [ ] **Step 2: Preserve existing references with Git moves, build the MySQL-native support inventory, and complete matrices and audit rows**

Unsupported, Enterprise-only, NDB-only, privileged, multi-session, restart, and
file-system statements remain in the universe with explicit classification and
reasons; they are not silently deleted.

- [ ] **Step 3: Regenerate edition counts/digests and run all edition audits**

Run: `PYTHONPATH=mysql_case_factory/src python3 -m pytest -q mysql_case_factory/tests/test_edition_8022_knowledge.py mysql_case_factory/tests/test_editions.py`

Expected: all selected tests pass and report zero missing/unreviewed rows.

### Task 7: Build and audit the 8.0.41 edition

**Files:**
- Create: `mysql_case_factory/editions/mysql_8_0_41/README.md`
- Create: `mysql_case_factory/editions/mysql_8_0_41/skills/mysql-8-0-41-sql-generation/**`
- Create: `mysql_case_factory/editions/mysql_8_0_41/version_delta_from_8_0_22.tsv`
- Create: `mysql_case_factory/tests/test_edition_8041_knowledge.py`
- Create: `mysql_case_factory/tests/test_version_delta.py`

- [ ] **Step 1: Write failing tests that require a closed 8.0.22-to-8.0.41 delta and reject implicit inheritance**

Every inherited item has one ledger row. `changed`, `added`, and `removed` rows
must bind an official locator and a nonempty review note.

- [ ] **Step 2: Run and verify RED**

Run: `PYTHONPATH=mysql_case_factory/src python3 -m pytest -q mysql_case_factory/tests/test_edition_8041_knowledge.py mysql_case_factory/tests/test_version_delta.py`

Expected: missing-edition and missing-ledger failures.

- [ ] **Step 3: Create the independent snapshot and apply all reviewed 8.0.23-8.0.41 deltas**

The edition must include post-8.0.22 syntax/factor changes only where the ledger
binds their official introduction/removal release. Its matrices and value audit
are regenerated from its own snapshot, not read through the 8.0.22 directory.

- [ ] **Step 4: Run both edition suites together**

Run: `PYTHONPATH=mysql_case_factory/src python3 -m pytest -q mysql_case_factory/tests/test_edition_8022_knowledge.py mysql_case_factory/tests/test_edition_8041_knowledge.py mysql_case_factory/tests/test_version_delta.py mysql_case_factory/tests/test_editions.py`

Expected: both editions pass with no cross-edition paths.

### Task 8: Documentation, tools, and end-to-end fixtures

**Files:**
- Replace: `mysql_case_factory/README.md`
- Replace: `mysql_case_factory/PROJECT_STRUCTURE.md`
- Create: `mysql_case_factory/tools/audit_editions.py`
- Create: `mysql_case_factory/tools/package_skills.py`
- Create: `mysql_case_factory/tests/test_end_to_end_run.py`
- Create: `mysql_case_factory/tests/fixtures/fake_mysql.py`
- Create: `mysql_case_factory/docker-compose.smoke.yml`

- [ ] **Step 1: Write the failing end-to-end run test**

The fixture initializes an 8.0.22 run, advances one job with hash-bound evidence,
executes a manifest-bound SQL file through fake reference/DUT clients, publishes
an exact comparison, and verifies that an 8.0.41 case/profile is rejected.

- [ ] **Step 2: Run and verify RED, then add the minimal fixtures/tools/docs**

Run: `PYTHONPATH=mysql_case_factory/src python3 -m pytest -q mysql_case_factory/tests/test_end_to_end_run.py`

Expected before implementation: fixture or workflow failure. Expected after implementation: pass.

- [ ] **Step 3: Run documentation and edition audits**

```bash
PYTHONPATH=mysql_case_factory/src python3 mysql_case_factory/tools/audit_editions.py
PYTHONPATH=mysql_case_factory/src python3 mysql_case_factory/tools/package_skills.py --verify-only
```

Expected: both commands report both editions valid.

### Task 9: Review, verification, commit, and push

**Files:**
- Review: all changed files under `mysql_case_factory/`

- [ ] **Step 1: Perform the code-review checklist**

Review correctness, version isolation, traversal/symlink defenses, credential
leaks, subprocess argument safety, race/collision behavior, evidence hashes,
resource cleanup, incomplete inventories, missing tests, and misleading runtime
claims. Fix every Critical or Important issue with a failing regression test.

- [ ] **Step 2: Run fresh final verification**

```bash
PYTHONPATH=mysql_case_factory/src python3 -m pytest -q mysql_case_factory/tests
PYTHONPATH=mysql_case_factory/src python3 mysql_case_factory/tools/audit_editions.py
python3 -m compileall -q mysql_case_factory/src mysql_case_factory/tools
uv build --project mysql_case_factory
```

Expected: zero test failures, both editions valid, compile succeeds, and wheel/sdist build succeeds.

- [ ] **Step 3: Attempt the real Docker smoke test**

Run: `docker compose -f mysql_case_factory/docker-compose.smoke.yml up --build --abort-on-container-exit`

Expected: 8.0.22 and 8.0.41 reference/DUT identity and exact-comparison smoke checks pass. If image/platform availability blocks this, preserve the exact output in the final report and keep runtime-verified flags false.

- [ ] **Step 4: Inspect scope, commit only MySQL project files, and push**

```bash
git status --short
git diff --check
git add mysql_case_factory
git commit -m "feat(mysql-case-factory): add 8.0.22 and 8.0.41 editions"
git push origin codex/mysql-8022-8041-parity
```

Expected: clean scoped commit and successful remote push.
