# ALTER FUNCTION Factor-Value Loop Regress Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Generate and locally verify one complete PostgreSQL 18.4 `ALTER FUNCTION` regress program for every applicable factor-value obligation, without expanding the global Cartesian product.

**Architecture:** Reuse the shared `applicability` canonical loader for the 85 `SFV` obligations. Add a statement-specific grammar catalog (5 synopsis branches, 19 action sub-clauses, optional-keyword axes) for `GRM`, plus `RISK` transaction obligations. `ALTER FUNCTION` declares `column_type_coverage`, `table_coverage` and `target_relation_coverage` all `not_applicable` in `alter_function.yaml`, so there is **no column/table/relation `INV` sweep** — signatures are consumed via `factor_contract.argtype_specification` plus the `routine_signature_resolution_manifest` dynamic input, never as a free type catalog. The renderer emits complete function/support schema/role/table fixture, one target statement, a success or expected-failure oracle, idempotent cleanup, and a residual check.

**Tech Stack:** Python 3.11+, dataclasses, PyYAML, `unittest`, PostgreSQL 18.4 `psql`, existing `remaining_statement_regress` publication utilities, and `regress-output-script-style` validation.

---

## Scope discipline (why this statement is smaller than ALTER FOREIGN TABLE)

`skills/pg-sql-generation/references/combinations/ddl/function/alter_function.yaml` `coverage_scope`:

| scope | required | mode | reason |
|---|---|---|---|
| target_object_coverage | true | explicit | routine lifecycle/signature/privilege/dependency |
| target_relation_coverage | false | not_applicable | no pg_class relation target |
| table_coverage | false | not_applicable | no table variant |
| column_type_coverage | false | not_applicable | arg/return types identify signatures, not column defs |

Therefore the formal ledger has **no 1,557-row column `INV` block**. Quantity is driven by `GRM` + `85 SFV` + small `RISK`. The exact total is **compiled, not pre-assumed**; this plan never targets a number first.

---

## File map

| Path | Responsibility |
|---|---|
| `src/pg_case_factory/alter_function_regress.py` | Frozen 5-branch grammar catalog, grammar actions/axes, PG18.4 outcome helpers |
| `src/pg_case_factory/alter_function_factor_loop.py` | Compile obligations, split local programs from delegated records, assign IDs and baselines |
| `src/pg_case_factory/alter_function_factor_render.py` | Render a complete SQL program for each planned obligation |
| `src/pg_case_factory/alter_function_factor_validate.py` | Extract primary witnesses from final bytes and prove conservation |
| `src/pg_case_factory/alter_function_factor_runtime.py` | Run every SQL twice on isolated PG18.4 and write runtime evidence |
| `src/pg_case_factory/remaining_statement_regress.py` | Register plan, renderer, target pattern, package evidence, output path |
| `tests/test_alter_function_regress.py` | grammar actions/axes and applicability diagnostics |
| `tests/test_alter_function_factor_loop.py` | ledger, IDs, dispositions, baseline, conservation |
| `tests/test_alter_function_factor_render.py` | branch renderer and complete-program tests |
| `tests/test_alter_function_factor_validate.py` | actual witness and mutation gate tests |
| `tests/test_alter_function_factor_runtime.py` | two-run, SQLSTATE, cleanup, determinism tests |
| `artifacts/regress/by-factor/ddl/function/alter_function/` | numbered SQL files and schedules |
| `artifacts/intermediates/remaining-statement-factor-cycle/alter_function/` | plan, coverage, handoff, package, validation, runtime evidence |

## Frozen arithmetic (SFV certain; GRM/RISK frozen in Task 1 after compilation)

```text
SFV canonical obligations                   85   (24 factors / 85 values, inventory §012)
GRM official obligations                  compiled (5 branches, 19 action sub-clauses, RESTRICT/EXTERNAL/SET-form/depends/list axes)
INV column/table/relation obligations       0   (all not_applicable per alter_function.yaml)
RISK transaction obligations               compiled (commit/rollback transactional-DDL boundary)
delegated handoffs                           0   (T5 boundaries are real ALTER FUNCTION errors → expected_failure; SUPPORT is a fixture dependency)
------------------------------------------------
local SQL programs                       GRM + 85 + RISK  (exact count frozen in Task 1)
```

The compiler must derive these counts from repository inputs and fail closed on drift. Constants are assertions, not replacement inputs.

## Grammar model (faithful to PG18 `sql-alterfunction.html`)

Official synopsis (5 forms):

```sql
ALTER FUNCTION name [ ( [ [ argmode ] [ argname ] argtype [, ...] ] ) ]
    action [ ... ] [ RESTRICT ]                       -- branch_1
ALTER FUNCTION name ( ... ) RENAME TO new_name        -- branch_2
ALTER FUNCTION name ( ... ) OWNER TO { new_owner | CURRENT_ROLE | CURRENT_USER | SESSION_USER }  -- branch_3
ALTER FUNCTION name ( ... ) SET SCHEMA new_schema     -- branch_4
ALTER FUNCTION name ( ... ) [ NO ] DEPENDS ON EXTENSION extension_name  -- branch_5
```

`action` sub-clauses (branch_1, one GRM target action each):

```sql
CALLED ON NULL INPUT | RETURNS NULL ON NULL INPUT | STRICT
IMMUTABLE | STABLE | VOLATILE
[ NOT ] LEAKPROOF
[ EXTERNAL ] SECURITY INVOKER | [ EXTERNAL ] SECURITY DEFINER
PARALLEL { UNSAFE | RESTRICTED | SAFE }
COST execution_cost
ROWS result_rows
SUPPORT support_function
SET configuration_parameter { TO | = } { value | DEFAULT }
RESET configuration_parameter
RESET ALL
```

Grammar axes (one GRM obligation per `(axis, value)`), modeling only true syntactic optionality/alternatives/list boundaries:

```text
branch_1 / __outer_action__:  restrict_clause (absent, present)
                               action_list_cardinality (one_action, multiple_actions)
branch_1 / set_parameter:     set_assignment_form (to_value, equals_value, to_default)
branch_1 / security_invoker:  external_keyword (omitted, present)
branch_1 / security_definer:  external_keyword (omitted, present)
branch_5 / depends_on_extension: depends_polarity (depends, no_depends)
```

Target actions: `called_on_null_input, returns_null_on_null_input, strict, immutable, stable, volatile, leakproof, not_leakproof, security_invoker, security_definer, parallel_unsafe, parallel_restricted, parallel_safe, cost, rows, support, set_parameter, reset_parameter, reset_all, rename, owner, set_schema, depends_on_extension` (23).

Signature identity (`argmode`/`argname`/list-cardinality) is consumed by `argtype_specification` (SFV) and the dynamic `routine_signature_resolution_manifest`, not modeled as a free GRM axis — same-name different-signature functions use a stable identity argument oracle.

---

### Task 1: Compile the factor-loop obligation ledger

**Files:**
- Create: `src/pg_case_factory/alter_function_regress.py`
- Create: `src/pg_case_factory/alter_function_factor_loop.py`
- Create: `tests/test_alter_function_factor_loop.py`

- [ ] **Step 1: Write the failing ledger-count and identity test**

Assert: every obligation has a unique id; `SFV == 85`; `INV == 0`; `delegated == 0`; dispositions ⊆ {covered, expected_failure, delegated}; local count == covered + expected_failure. Exact `GRM`/`RISK`/total are filled from the first successful compile then frozen.

- [ ] **Step 2: Run the test and verify RED** — `ModuleNotFoundError: pg_case_factory.alter_function_factor_loop`.

- [ ] **Step 3: Implement the immutable obligation record and compiler**

```python
@dataclass(frozen=True)
class AlterFunctionFactorObligation:
    ordinal: int
    obligation_id: str
    kind: str            # GRM | SFV | RISK
    factor_key: str
    value: str
    consumer_action_id: str
    disposition: str    # covered | expected_failure | delegated
    source_locator: str
    delegated_statement_key: str | None = None
```

Compile order: `_compile_grammar_obligations()` + `_compile_canonical_obligations(root)` (shared `load_shipped_applicability_universe(root).rows_for_statement("alter_function")`, assert 85) + `_compile_risk_obligations()` (commit/rollback). No column/topology compilation.

Stable identities:
```text
AF-GRM|branch|action|factor|value
AF-SFV|canonical-row-id|branch-context
AF-RISK|transaction|commit-or-rollback
```

- [ ] **Step 4: Freeze counts, run GREEN** — all Task 1 tests pass in under five seconds.

- [ ] **Step 5: Commit Task 1** — `feat: compile alter function factor loop`.

### Task 2: Plan one local case per local obligation

**Files:** modify `alter_function_factor_loop.py`; modify `test_alter_function_factor_loop.py`.

- [ ] **Step 1: Write the failing one-to-one plan test** — one case per non-delegated obligation; ordinals `1..N`; filenames `ALTERFUNCTION0001.sql..N`; unique `primary_obligation_id`; unique `sql_filename`; `object_prefix = alterfunction_{ordinal:04d}_`; baseline has exactly one value per action-applicable key and never a second value for `case.factor_key`.
- [ ] **Step 2: Run RED.**
- [ ] **Step 3: Implement plan records and deterministic numbering** — `AlterFunctionFactorCase` + `AlterFunctionFactorLoopPlan` with `obligation_multiset_sha256`.
- [ ] **Step 4: Add assignment-driven failure tests** — `expected_failure` disposition drives `outcome`/`expected_sqlstate`/`expected_failure_reason`; `covered` → `00000`.
- [ ] **Step 5: Run GREEN; commit** — `feat: plan one alter function case per factor`.

### Task 3: Render complete SQL programs

**Files:** create `alter_function_factor_render.py`; create `test_alter_function_factor_render.py`.

- [ ] **Step 1: Write the failing complete-program test** — each rendered file has fixed header, idempotent pre-cleanup, complete fixture (stable function object + support object + schema/role/table as needed), exactly one target `ALTER FUNCTION`, oracle, unconditional cleanup, residual probe.
- [ ] **Step 2: Run RED.**
- [ ] **Step 3: Implement branch renderers** — branch_1 action sub-clauses; RENAME; OWNER; SET SCHEMA; DEPENDS ON EXTENSION. Same-name different-signature uses stable identity argument oracle.
- [ ] **Step 4: Add oracle + cleanup tests** — success `00000`; expected-failure fixed 5-digit SQLSTATE; no aborted-transaction leakage; deterministic output (no bare OID/PID/random).
- [ ] **Step 5: Run GREEN; commit** — `feat: render alter function factor programs`.

### Task 4: Byte-level witness + conservation

**Files:** create `alter_function_factor_validate.py`; create `test_alter_function_factor_validate.py`.

- [ ] **Step 1: Write the failing conservation test** — `Bag(required covered|expected_failure) == Bag(primary ids from bytes)`; missing/duplicate/unknown/semantic-mismatch == 0.
- [ ] **Step 2: Run RED.**
- [ ] **Step 3: Implement the byte-level witness extractor** — re-derive `primary_obligation_id` from final SQL/harness bytes, never trust planner metadata alone.
- [ ] **Step 4: Run GREEN; commit** — `feat: validate alter function factor witnesses`.

### Task 5: Static gate

- [ ] style validator `PASS`; `python -m compileall src`; `git diff --check`; existing suite (`Ran 117 tests … OK`) non-regressing.

### Task 6: PG18.4 double-run + evidence

**Files:** create `alter_function_factor_runtime.py`; create `test_alter_function_factor_runtime.py`.

- [ ] **Step 1: Write the failing two-run test** — isolated socket `/tmp/pgcf-pg18-af-sock-20260819`, port distinct from 5432; run-01 + cleanup + residual-zero + run-02 + normalized comparison.
- [ ] **Step 2: Run RED.**
- [ ] **Step 3: Implement the serial two-run runner** — per-file 30s timeout, serial, clean baseline restore between runs.
- [ ] **Step 4: Calibrate real PG18 behavior** — fix oracle/SQLSTATE mismatches found by the double-run (expected-failure SQLSTATE, owner/schema/extension/dependency boundaries, signature identity). Iterate until mismatch/failure == 0.
- [ ] **Step 5: Freeze evidence** — `runtime-run-01.json`, `runtime-run-02.json`, `runtime-two-run-comparison.json`, `runtime-validation.json`; `package.json` + `validation.json` keep `runtime_status = not_run_static_sql_only` (static boundary intentional); runtime conclusion lives in `runtime-validation.json`.
- [ ] **Step 6: Run GREEN; commit** — `test: add alter function pg18 runtime`.

### Task 7: Register, mark complete, advance, notify

- [ ] Register `alter_function` in `remaining_statement_regress.py` (mirror L694–1391 AFT block: lazy plan builder, renderer dispatch, validator dispatch, evidence doc).
- [ ] Mark `progress.json` `alter_function = completed`; advance `next_pending_statement` → `alter_group`.
- [ ] Stage only this statement's implementation/tests/plan + `git add -f` its precise `artifacts/` SQL/evidence paths; do not touch the user's other dirty files; count staged files before commit.
- [ ] Update `docs/superpowers/context/2026-08-18-current-thread-memory.md` §8/§9-style entry for ALTER FUNCTION.
- [ ] Commit — `test: publish alter function factor regress`.
- [ ] Notify the user to inspect generation quality before starting `alter_group`.

---

## Completion gate (memory §16, all must hold)

ledger frozen → every obligation has a disposition → program/handoff conservation (missing/duplicate/unknown == 0) → actual primary witness from final bytes → numbering/prefix/setup/oracle/cleanup compliant → style PASS → PG18.4 two-run complete → all mismatch/failure == 0 → runtime evidence bound to current package SHA → docs/progress/commit on disk.
