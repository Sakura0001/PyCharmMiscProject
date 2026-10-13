# Type-upgrade consistency extension v1 implementation plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add an independent `TUCX` extension batch that closes the current P0 type-upgrade interaction gaps without modifying the verified 8,270-case `TUC` baseline.

**Architecture:** Reuse the existing type-upgrade case model and runner while adding a separate extension module and generator. The extension generator emits a distinct batch identity, P0 gap tags, richer data/index/FK/query oracles, and its own artifact directory. The runner is generalized to validate any declared batch manifest rather than hard-coding only the baseline batch.

**Tech Stack:** Python 3.10+, PyMySQL, pytest, gzip/JSON deterministic artifacts, MySQL 8.0.45.

---

### Task 1: Extension batch model and manifest

**Files:**
- Modify: `mysql_case_factory/src/mysql_case_factory/type_upgrade_consistency.py`
- Create: `mysql_case_factory/src/mysql_case_factory/type_upgrade_extension.py`
- Create: `mysql_case_factory/tools/generate_type_upgrade_extension.py`
- Test: `mysql_case_factory/tests/test_type_upgrade_extension.py`

- [ ] Write failing tests for extension constants, case identity, parent batch link, `TUCX` prefix, priority, gap ID, coverage tags, and deterministic manifest.
- [ ] Add extension constants and a dataclass or factory that reuses the existing case shape.
- [ ] Add a generator that writes `cases.jsonl.gz`, three profile suites, `manifest.json`, `coverage.tsv`, and `README.md` under `generated/type_upgrade_consistency_extension_v1/`.
- [ ] Verify baseline artifacts remain unchanged.
- [ ] Run the focused tests and commit.

### Task 2: Generalize runner batch validation

**Files:**
- Modify: `mysql_case_factory/src/mysql_case_factory/type_upgrade_runner.py`
- Test: `mysql_case_factory/tests/test_type_upgrade_runner.py`

- [ ] Write failing tests proving the runner accepts the extension manifest and rejects a mismatched or missing batch identity.
- [ ] Replace hard-coded baseline batch checks with manifest-driven batch validation.
- [ ] Preserve crash classification, interrupt propagation, artifact integrity checks, and live MySQL version recording.
- [ ] Run focused runner tests and commit.

### Task 3: P0 data behavior profiles

**Files:**
- Modify: `mysql_case_factory/src/mysql_case_factory/type_upgrade_extension.py`
- Test: `mysql_case_factory/tests/test_type_upgrade_extension.py`

- [ ] Write failing tests for all eight P0 data profiles.
- [ ] Generate cases that execute target-only boundary values, default omission, collation-equivalent values, duplicate conflicts, old-to-new updates, delete/reinsert, commit, and rollback.
- [ ] Add transaction ledgers and post-DDL result checks.
- [ ] Run a local COPY smoke subset, then the full extension run.
- [ ] Commit.

### Task 4: P0 primary-key and overlapping-index matrix

**Files:**
- Modify: `mysql_case_factory/src/mysql_case_factory/type_upgrade_extension.py`
- Test: `mysql_case_factory/tests/test_type_upgrade_extension.py`

- [ ] Write failing tests for target-column primary keys and overlapping indexes.
- [ ] Cover target as single PK and as first/middle/last composite-PK member.
- [ ] Cover PK plus secondary, PK plus unique, and multi-index overlap.
- [ ] Add FORCE INDEX and EXPLAIN query oracles.
- [ ] Run full local COPY and commit.

### Task 5: P0 multi-column ALTER matrix

**Files:**
- Modify: `mysql_case_factory/src/mysql_case_factory/type_upgrade_extension.py`
- Test: `mysql_case_factory/tests/test_type_upgrade_extension.py`

- [ ] Write failing tests for two-column, three-column, five-column, composite-index-member, and atomic-reject multi-column ALTERs.
- [ ] Generate old/reference/algorithm tables with multiple target columns.
- [ ] Verify all target and non-target columns after DDL and post-DDL writes.
- [ ] Run full local COPY and commit.

### Task 6: P0 foreign-key action matrix

**Files:**
- Modify: `mysql_case_factory/src/mysql_case_factory/type_upgrade_extension.py`
- Test: `mysql_case_factory/tests/test_type_upgrade_extension.py`

- [ ] Write failing tests for orphan rejection, delete/update actions, and two-level propagation.
- [ ] Create matching reference/algorithm parent-child table pairs after type upgrade.
- [ ] Execute real child/parent DML and compare final row sets.
- [ ] Run full local COPY and commit.

### Task 7: Coverage audit and internal-AI documentation

**Files:**
- Create: `mysql_case_factory/tools/audit_type_upgrade_extension.py`
- Modify: `mysql_case_factory/README.md`
- Create: `mysql_case_factory/docs/type_upgrade_consistency_extension_v1.md`
- Create: `mysql_case_factory/generated/type_upgrade_consistency_extension_v1/README.md`

- [ ] Write failing tests for the audit tool.
- [ ] Audit baseline and extension manifests, case-ID uniqueness, parent link, P0 gap coverage, forbidden factors, and profile case-count equality.
- [ ] Generate a coverage gap report.
- [ ] Document that `TUC` is the 8,270-case baseline and `TUCX` is extension v1.
- [ ] Add internal-AI execution instructions that prohibit mixing batches.
- [ ] Commit.

### Task 8: Final verification and merge

**Files:**
- All extension files.

- [ ] Run `pytest -q`; expected: all tests pass.
- [ ] Run full local COPY for every `TUCX` case; expected: all PASS.
- [ ] Verify artifact hashes and byte sizes.
- [ ] Verify baseline `TUC` artifacts remain unchanged.
- [ ] Have an independent reviewer inspect P0 coverage and artifacts.
- [ ] Merge `codex/type-upgrade-extension-v1` into `codex/ddl-verify-20260919`.
- [ ] Push the target branch.
