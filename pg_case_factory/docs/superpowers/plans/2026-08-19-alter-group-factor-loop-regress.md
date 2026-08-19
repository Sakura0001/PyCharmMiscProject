# ALTER GROUP Factor-Value Loop Regress Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Generate and locally verify one complete PostgreSQL 18.4 `ALTER GROUP` regress program for every applicable factor-value obligation, without expanding the global Cartesian product.

**Architecture:** Reuse the shared `applicability` canonical loader for the 57 `SFV` obligations. `ALTER GROUP` has **no grammar axis beyond the canonical factors** — every syntactic alternative (`statement_branch`, `role_specification`, `multi_user`, `group_name_shape`/`user_name_shape`/`new_name_shape`) is already a canonical `SFV` row, so `GRM` compiles to **0**. Add a small `RISK` transaction block (commit/rollback — role membership and role rename are transactional DDL). `ALTER GROUP` declares `target_relation_coverage`, `table_coverage` and `column_type_coverage` all `not_applicable` in `alter_group.yaml`, so there is **no column/table/relation `INV` sweep**. The renderer emits complete group/user role fixture, one target `ALTER GROUP` statement, a success or expected-failure oracle, idempotent cleanup, and a residual probe.

**Tech Stack:** Python 3.11+, dataclasses, PyYAML, `unittest`, PostgreSQL 18.4 `psql`, existing `remaining_statement_regress` publication utilities, and `regress-output-script-style` validation.

---

## Scope discipline (why this statement has no GRM block and no INV block)

`skills/pg-sql-generation/references/combinations/ddl/group/alter_group.yaml` `coverage_scope`:

| scope | required | mode | reason |
|---|---|---|---|
| target_object_coverage | true | explicit | role/group catalog lifecycle/membership/rename (object_kinds: group, role) |
| target_relation_coverage | false | not_applicable | no pg_class relation target |
| table_coverage | false | not_applicable | no table variant |
| column_type_coverage | false | not_applicable | role DDL is independent of column data types |

`ALTER GROUP` official synopsis (3 forms):

```sql
ALTER GROUP role_specification ADD USER user_name [, ... ]
ALTER GROUP role_specification DROP USER user_name [, ... ]
    -- role_specification := role_name | CURRENT_ROLE | CURRENT_USER | SESSION_USER
ALTER GROUP group_name RENAME TO new_name
```

Every syntactic alternative in these 3 forms is already a canonical factor value:
- `statement_branch` ∈ {branch_add_user, branch_drop_user, branch_rename} — SFV;
- `role_specification` ∈ {role_name, current_role, current_user, session_user} — SFV (applies only to ADD/DROP USER, **not** RENAME);
- `multi_user` ∈ {single_user, multiple_users} — SFV (applies only to ADD/DROP USER);
- `group_name_shape` / `user_name_shape` / `new_name_shape` — SFV.

Therefore the formal ledger has **no `GRM` block** (0 grammar-axis obligations) and **no column/table/relation `INV` block**. Quantity is driven by `57 SFV` + `2 RISK`. The exact total is **compiled, not pre-assumed**; this plan never targets a number first.

---

## File map

| Path | Responsibility |
|---|---|
| `src/pg_case_factory/alter_group_regress.py` | Frozen branch/action constants, PG18.4 outcome/SQLSTATE helpers |
| `src/pg_case_factory/alter_group_factor_loop.py` | Compile obligations, split local programs from delegated records, assign IDs and baselines |
| `src/pg_case_factory/alter_group_factor_render.py` | Render a complete SQL program for each planned obligation |
| `src/pg_case_factory/alter_group_factor_validate.py` | Extract primary witnesses from final bytes and prove conservation |
| `src/pg_case_factory/alter_group_factor_runtime.py` | Run every SQL twice on isolated PG18.4 and write runtime evidence |
| `src/pg_case_factory/remaining_statement_regress.py` | Register plan, renderer, target pattern, package evidence, output path |
| `tests/test_alter_group_factor_loop.py` | ledger, IDs, dispositions, baseline, conservation, grammar |
| `tests/test_alter_group_factor_render.py` | branch renderer and complete-program tests |
| `tests/test_alter_group_factor_validate.py` | actual witness and mutation gate tests |
| `tests/test_alter_group_factor_runtime.py` | two-run, SQLSTATE, cleanup, determinism tests |
| `artifacts/regress/by-factor/ddl/group/alter_group/` | numbered SQL files and schedules |
| `artifacts/intermediates/remaining-statement-factor-cycle/alter_group/` | plan, coverage, handoff, package, validation, runtime evidence |

## Frozen arithmetic (SFV certain; GRM/RISK frozen in Task 1 after compilation)

```text
SFV canonical obligations                   57   (23 factors / 57 values, inventory §013)
GRM official obligations                     0   (every syntax alternative is already an SFV canonical factor)
INV column/table/relation obligations        0   (all not_applicable per alter_group.yaml)
RISK transaction obligations                  2   (commit/rollback transactional role DDL boundary)
delegated handoffs                            0   (all negative boundaries are real ALTER GROUP errors → expected_failure)
------------------------------------------------
local SQL programs                         57 + 2 = 59  (exact count frozen in Task 1)
```

The compiler must derive these counts from repository inputs and fail closed on drift. Constants are assertions, not replacement inputs.

## Grammar model (faithful to PG18 `sql-altergroup.html`)

Official synopsis (3 forms) — see Scope discipline above. `role_specification` and `multi_user` are **branch-local**: they apply only to the ADD USER / DROP USER forms, never to RENAME TO (which takes a bare `group_name`). The renderer derives the branch from the `statement_branch` factor value and gates `role_specification`/`multi_user` accordingly.

`deprecated_equivalence` annotates the modern-command equivalence (ADD USER ≡ GRANT, DROP USER ≡ REVOKE, RENAME TO ≡ ALTER ROLE RENAME) — a documentation/behavior annotation, not a separate syntax axis; it is consumed as an SFV factor value on the relevant branch.

`deprecated_command_note` (single value `deprecated_no_warning`) marks that `ALTER GROUP` is a deprecated command that emits no warning — consumed as an SFV factor value annotated on every sample.

Signature identity is irrelevant here (no routine signatures); same-name different-kind conflicts are modeled via `rename_to_existing_name` / `new_name_shape=duplicate_name`.

---

## Disposition model (frozen in Task 1; SQLSTATEs verified in Task 6)

Reachable expected-failure `(factor, value)` pairs (each is its own primary case, attributed to its own factor — runtime behavior may overlap but the obligation identity does not):

```text
(expected_status, failure)                 42704  role_does_not_exist   (default failure_reason = target_role_missing)
(object_state, not_exists)                 42704  role_does_not_exist
(group_name_shape, nonexistent_name)       42704  role_does_not_exist
(user_name_shape, nonexistent_user)        42704  role_does_not_exist
(user_existence, user_not_exists)          42704  role_does_not_exist
(nonexistent_group, group_missing)         42704  role_does_not_exist
(nonexistent_user, user_missing)           42704  role_does_not_exist
(new_name_shape, duplicate_name)           42710  role_already_exists
(rename_to_existing_name, same_name_conflict) 42710  role_already_exists
(privilege_level, non_admin)               42501  permission_denied
(insufficient_privilege, insufficient_privilege) 42501  permission_denied
(non_admin_attempt, non_admin_execution)   42501  permission_denied
(target_role_admin, lacks_admin)           42501  permission_denied
```

**Not** expected-failure (covered / success-with-NOTICE, verified in Task 6):
- `(duplicate_add_user, existing_member)` — `ALTER GROUP ... ADD USER` of an already-member is a NOTICE, not an error (exit 0);
- `(drop_non_member_user, non_member)` — `DROP USER` of a non-member is a NOTICE, not an error (exit 0);
- `(deprecated_command_note, deprecated_no_warning)` — annotation only, success.

All remaining SFV values are `covered` (success). `RISK` obligations are `covered` (commit succeeds; rollback undoes). The exact SQLSTATEs are probed against the isolated PG18.4 cluster in Task 6 and the table above is corrected there if any drift is found (e.g. RENAME-to-existing may surface as 42710 vs another code under the deprecated path).

---

### Task 1: Compile the factor-loop obligation ledger

**Files:**
- Create: `src/pg_case_factory/alter_group_regress.py`
- Create: `src/pg_case_factory/alter_group_factor_loop.py`
- Create: `tests/test_alter_group_factor_loop.py`

- [ ] **Step 1: Write the failing ledger-count and identity test**

Assert: every obligation has a unique id; `SFV == 57`; `GRM == 0`; `INV == 0`; `delegated == 0`; dispositions ⊆ {covered, expected_failure}; local count == covered + expected_failure == 59. Exact `RISK`/total are filled from the first successful compile then frozen.

- [ ] **Step 2: Run the test and verify RED** — `ModuleNotFoundError: pg_case_factory.alter_group_factor_loop`.

- [ ] **Step 3: Implement the immutable obligation record and compiler**

```python
@dataclass(frozen=True)
class AlterGroupFactorObligation:
    ordinal: int
    obligation_id: str
    kind: str            # SFV | RISK  (GRM compiles to 0)
    factor_key: str
    value: str
    consumer_action_id: str
    disposition: str     # covered | expected_failure | delegated
    source_locator: str
    delegated_statement_key: str | None = None
```

Compile order: `_compile_canonical_obligations(root)` (shared `load_shipped_applicability_universe(root).rows_for_statement("alter_group")`, assert 57) + `_compile_risk_obligations()` (commit/rollback). No grammar compilation, no column/topology compilation.

Stable identities:
```text
AG-SFV|canonical-row-id|consumer-action
AG-RISK|transaction|commit-or-rollback
```

- [ ] **Step 4: Freeze counts, run GREEN** — all Task 1 tests pass in under five seconds.

- [ ] **Step 5: Commit Task 1** — `feat: compile alter group factor loop`.

### Task 2: Plan one local case per local obligation

**Files:** modify `alter_group_factor_loop.py`; modify `test_alter_group_factor_loop.py`.

- [ ] **Step 1: Write the failing one-to-one plan test** — one case per non-delegated obligation; ordinals `1..N`; filenames `ALTERGROUP0001.sql..N`; unique `primary_obligation_id`; unique `sql_filename`; `object_prefix = altergroup_{ordinal:04d}_`; baseline has exactly one value per action-applicable key and never a second value for `case.factor_key`.
- [ ] **Step 2: Run RED.**
- [ ] **Step 3: Implement plan records and deterministic numbering** — `AlterGroupFactorCase` + `AlterGroupFactorLoopPlan` with `obligation_multiset_sha256`.
- [ ] **Step 4: Add assignment-driven failure tests** — `expected_failure` disposition drives `outcome`/`expected_sqlstate`/`expected_failure_reason`; `covered` → `00000`.
- [ ] **Step 5: Run GREEN; commit** — `feat: plan one alter group case per factor`.

### Task 3: Render complete SQL programs

**Files:** create `alter_group_factor_render.py`; create `test_alter_group_factor_render.py`.

- [ ] **Step 1: Write the failing complete-program test** — each rendered file has fixed header, idempotent pre-cleanup, complete fixture (stable group role + member/user role + admin grant as needed), exactly one target `ALTER GROUP`, oracle, unconditional cleanup, residual probe.
- [ ] **Step 2: Run RED.**
- [ ] **Step 3: Implement branch renderers** — ADD USER (single/multiple, role_specification forms), DROP USER (single/multiple, role_specification forms), RENAME TO. `role_specification`/`multi_user` gated to ADD/DROP USER only. Each sample annotates the deprecated-command note + modern equivalent.
- [ ] **Step 4: Add oracle + cleanup tests** — success `00000`; expected-failure fixed 5-digit SQLSTATE; NOTICE-boundary cases (duplicate_add_user existing_member, drop_non_member_user non_member) assert membership end-state, not error; no aborted-transaction leakage; deterministic output (no bare OID/PID/random).
- [ ] **Step 5: Run GREEN; commit** — `feat: render alter group factor programs`.

### Task 4: Byte-level witness + conservation

**Files:** create `alter_group_factor_validate.py`; create `test_alter_group_factor_validate.py`.

- [ ] **Step 1: Write the failing conservation test** — `Bag(required covered|expected_failure) == Bag(primary ids from bytes)`; missing/duplicate/unknown/semantic-mismatch == 0.
- [ ] **Step 2: Run RED.**
- [ ] **Step 3: Implement the byte-level witness extractor** — re-derive `primary_obligation_id` from final SQL/harness bytes, never trust planner metadata alone.
- [ ] **Step 4: Run GREEN; commit** — `feat: validate alter group factor witnesses`.

### Task 5: Static gate

- [ ] style validator `PASS`; `python -m compileall src`; `git diff --check`; existing suite non-regressing.

### Task 6: PG18.4 double-run + evidence

**Files:** create `alter_group_factor_runtime.py`; create `test_alter_group_factor_runtime.py`.

- [ ] **Step 1: Write the failing two-run test** — isolated socket `/tmp/pgcf-pg18-ag-sock-20260819`, port distinct from 5432 and from the AF socket; run-01 + cleanup + residual-zero + run-02 + normalized comparison.
- [ ] **Step 2: Run RED.**
- [ ] **Step 3: Implement the serial two-run runner** — per-file 30s timeout, serial, clean baseline restore between runs; reuse the AF runtime cleanup/safety-net pattern (section 1 idempotent pre-cleanup superset, safety-net ON_ERROR_STOP=0, post-clean probe).
- [ ] **Step 4: Calibrate real PG18 behavior** — fix oracle/SQLSTATE mismatches found by the double-run (RENAME-to-existing SQLSTATE, NOTICE-boundary attribution, privilege/admin-option boundaries). Iterate until mismatch/failure == 0.
- [ ] **Step 5: Implement runtime evidence-collection** — the runner exposes `to_dict` projections on `AlterGroupSuiteRun`/`AlterGroupTwoRunComparison`; a representative-case PG18.4 live test produces passing run-01/run-02/comparison evidence. The frozen N-case JSON artifacts (`runtime-run-01.json`, `runtime-run-02.json`, `runtime-two-run-comparison.json`, `runtime-validation.json`) and `package.json`+`validation.json` (`runtime_status = not_run_static_sql_only`, static boundary intentional; runtime conclusion lives in `runtime-validation.json`) are emitted by the Task 7 publication pipeline and committed with `git add -f`.
- [ ] **Step 6: Run GREEN; commit** — `test: add alter group pg18 runtime`.

### Task 7: Register, mark complete, advance, notify

- [ ] Register `alter_group` in `remaining_statement_regress.py` (mirror the alter_function 10-site block: cached factor-plan helper, lazy plan builder, `_PLAN_BUILDERS` entry, renderer/coverage/factor-documents/package/generate/validate dispatches, and the `ALTER GROUP` SQL-header regex).
- [ ] Mark `progress.json` `alter_group = completed`; advance `next_pending_statement` → `alter_index`.
- [ ] Stage only this statement's implementation/tests/plan + `git add -f` its precise `artifacts/` SQL/evidence paths; do not touch the user's other dirty files; count staged files before commit.
- [ ] Update `docs/superpowers/context/2026-08-18-current-thread-memory.md` §8 progress table + §13 history + §15 completion record + §17/§18 (mirror the ALTER FUNCTION entry; keep §16 gate at section 16 — no renumbering).
- [ ] Commit — `test: publish alter group factor regress`.
- [ ] Notify the user to inspect generation quality before starting `alter_index`.

---

## Completion gate (memory §16, all must hold)

ledger frozen → every obligation has a disposition → program/handoff conservation (missing/duplicate/unknown == 0) → actual primary witness from final bytes → numbering/prefix/setup/oracle/cleanup compliant → style PASS → PG18.4 two-run complete → all mismatch/failure == 0 → runtime evidence bound to current package SHA → docs/progress/commit on disk.
