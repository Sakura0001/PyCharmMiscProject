# ALTER FUNCTION Fuller-Coverage Regress Implementation Plan (Redo — task #14)

> **For agentic workers:** REQUIRED SUB-SKILL: superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Redo `ALTER FUNCTION` (NON-TABLE) with the bounded post-coverage extension framework, growing the v1 marginal baseline (123 programs) to **thousands** by crossing the positive T1–T4 behavior axes × T6 verification/cleanup, at most one T5 negative per case. This PROVES the NON-TABLE template (proven on `alter_group`, 3,947) is reusable on a 2nd statement before the #15 mass fan-out.

**Architecture:** KEEP the frozen v1 marginal ledger (`alter_function_factor_loop.py`, 123 = GRM 36 + SFV 85 + RISK 2) UNCHANGED — it is the required baseline (coverage floor). ADD `alter_function_factor_extension.py` (bounded cross-factor expander). UPDATE render/validate/runtime to handle `baseline ∪ extension`. Mirror the `alter_group` reference implementation exactly (2-plan validate signature, 5-phase byte render, serial two-run runtime). Reference: `docs/superpowers/plans/2026-08-19-fuller-coverage-extension-framework.md`.

**Tech Stack:** Python 3.11+, frozen dataclasses, PyYAML, `unittest`, PostgreSQL 18.4 `psql`, `remaining_statement_regress` publication utilities, `regress-output-script-style` validation.

---

## Scope discipline (why this statement grows via extension, not cartesian)

`skills/pg-sql-generation/references/combinations/ddl/function/alter_function.yaml` `coverage_scope`: `target_object_coverage` explicit; `target_relation_coverage`/`table_coverage`/`column_type_coverage` all `not_applicable` — there is **no column/table/relation INV sweep**. Argument/return types identify signatures via `factor_contract.argtype_specification` + the `routine_signature_resolution_manifest`, never a free type catalog. Quantity growth comes ONLY from the bounded post-coverage extension cross (the yaml's `post_coverage_extension_policy.enabled: true`); the 2.7M cartesian interaction universe stays a diagnostic-only resolver artifact (never emitted).

## File map

| Path | Responsibility | Status |
|---|---|---|
| `src/pg_case_factory/alter_function_factor_loop.py` | marginal required baseline (123) | **KEEP unchanged** |
| `src/pg_case_factory/alter_function_regress.py` | frozen 5-branch grammar catalog | KEEP unchanged |
| `src/pg_case_factory/alter_function_factor_extension.py` | bounded cross-factor extension expander | **NEW** |
| `src/pg_case_factory/alter_function_factor_render.py` | unified renderer: baseline + extension → 5-phase byte SQL | UPDATE (extend to extension cases) |
| `src/pg_case_factory/alter_function_factor_validate.py` | 2-plan byte witness + baseline conservation + extension gate | UPDATE (to 2-plan signature) |
| `src/pg_case_factory/alter_function_factor_runtime.py` | PG18.4 double-run of ALL cases (baseline + extensions) | UPDATE (combine baseline+extension case set) |
| `src/pg_case_factory/remaining_statement_regress.py` | registration (2-plan, ~5k leaf) | UPDATE (alter_function block → 2-plan) |
| `tests/test_alter_function_factor_extension.py` | extension expander tests | NEW |
| `tests/test_alter_function_factor_render.py` | add extension-render tests | UPDATE |
| `tests/test_alter_function_factor_validate.py` | add 2-plan conservation tests | UPDATE |
| `tests/test_alter_function_factor_runtime.py` | double-run tests (incl. live 6-case) | UPDATE |
| `artifacts/regress/by-factor/ddl/function/alter_function/` | numbered SQL (ALTERFUNCTION0001..N) + schedules | REGENERATE |
| `artifacts/intermediates/remaining-statement-factor-cycle/alter_function/` | plan/coverage/package/validation/derived_extension_combinations/runtime evidence | REGENERATE |

## Frozen arithmetic

```text
v1 marginal baseline (KEEP)          123   (GRM 36 + SFV 85 + RISK 2)
bounded post-coverage extensions   ~4,500–6,000  (cross positive T1–T4 axes × T6, at-most-one T5 negative, cap)
------------------------------------------------
total leaf SQL                   ~4,600–6,100   (target: thousands; exact count frozen in Task 1 after first green compile)
```

Exact extension count is COMPILED + frozen in Task 1 (mirror `alter_group`'s frozen 3,888), not pre-assumed. Constants are assertions, not replacement inputs.

## Factor axes (from `alter_function.yaml` `factor_contract` + `combination_groups[].expansion`)

The extension cross uses **positive T1–T4 crossed × T6 crossed**, **at most one T5 negative per case** (the baseline owns each T5 negative in isolation; the extension crosses each with positive contexts, attribution-clean).

| tier | factor | values | role in extension |
|---|---|---|---|
| T1 | statement_branch | branch_1..5 (5) | consumer derivation (per-branch axes) |
| T1 | object_state | exists / not_exists / different_signature_exists (3) | crossed (not_exists, different_sig = negatives 42883) |
| T1 | expected_status | success / failure (2) | derived (meta flag from failure-unit count) |
| T2 | action_type | 19 (CALLED..RESET_ALL) | branch_1 consumer axis (crossed representative subset) |
| T2 | restrict_clause | present / absent (2) | crossed (branch_1) |
| T2 | rename_target | simple / quoted / reserved / duplicate (4) | crossed (branch_2; duplicate = negative 42723) |
| T2 | owner_target | new_owner_role / CURRENT_ROLE / CURRENT_USER / SESSION_USER / nonexistent_role (5) | crossed (branch_3; nonexistent_role = negative 42704) |
| T2 | schema_target | schema_exists / not_exists / pg_catalog_reserved / information_schema_reserved (4) | crossed (branch_4; not_exists=3F000, reserved=42501) |
| T2 | extension_target | extension_exists / not_exists / NO_DEPENDS (3) | crossed (branch_5; not_exists = negative 42704) |
| T2 | argtype_specification | with_full / with_partial / without (3) | crossed (with_partial = negative 42883; without = success-if-unique else 42725) |
| T3 | function_name_shape | simple / quoted / reserved / schema_qualified (4) | crossed (representative) |
| T3 | new_name_shape | simple / quoted / reserved (3) | crossed (branch_2) |
| T3 | configuration_parameter_shape | valid / invalid (2) | crossed (branch_1 set/reset actions only; invalid = negative 42704) |
| T4 | privilege_level | superuser / function_owner / non_owner_with_alter / non_owner_no_privilege (4) | crossed (cluster: non_owner_* = negative 42501, counted as ONE unit) |
| T4 | schema_dependency | target_schema_exists / not_exists / reserved (3) | crossed (branch_4) |
| T4 | role_dependency | owner_role_exists / not_exists (2) | crossed (branch_3) |
| T4 | extension_dependency | extension_installed / not_installed (2) | crossed (branch_5) |
| T5 | target_function_not_exists | name_not_found / signature_not_found (2) | at-most-one-per-case negative (42883) |
| T5 | target_function_different_type | same_name_is_aggregate / same_name_is_procedure (2) | at-most-one-per-case negative (42809) |
| T5 | permission_insufficient | no_alter / not_owner_OWNER_TO / not_owner_SET_SCHEMA (3) | at-most-one-per-case negative (42501) |
| T5 | conflicting_action | multiple_conflicting_volatility (1) | at-most-one-per-case negative (42601) |
| T5 | identifier_length_exceeded | over_63_chars (1) | **NOT a failure** (succeeds via NAMEDATALEN truncation) — success value |
| T6 | verification_mode | pg_proc_catalog_query / information_schema_routines / pg_get_functiondef (3) | CROSSED |
| T6 | cleanup_mode | DROP_FUNCTION / DROP_FUNCTION_IF_EXISTS / DROP_FUNCTION_CASCADE (3) | CROSSED |

### Per-branch crossed axes (branch-local applicability — mirror `alter_group` `_BRANCH_AXES`)

```text
branch_1 (action form, consumer = action_type representative subset):
  object_state(3) × action_type(rep ~6–8) × argtype_specification(3) × function_name_shape(4) × privilege_level(4) × restrict_clause(2)
  [configuration_parameter_shape(2) applies ONLY to set_parameter/reset_parameter/reset_all; held at baseline=valid otherwise]
branch_2 (rename): new_name_shape(3) × rename_target(4) × object_state(3) × function_name_shape(4) × privilege_level(4)
branch_3 (owner):  owner_target(5) × object_state(3) × function_name_shape(4) × privilege_level(4) × role_dependency(2)
branch_4 (set_schema): schema_target(4) × object_state(3) × function_name_shape(4) × privilege_level(4) × schema_dependency(3)
branch_5 (depends):  extension_target(3) × object_state(3) × function_name_shape(4) × privilege_level(4) × extension_dependency(2)
```

### Cross design

- `itertools.product` over each branch's crossed axes → full assignment (T6 at baseline).
- `_is_valid_combination(assignment)`: branch-local applicability + privilege cluster consistency (privilege_level=non_owner_* ↔ permission_insufficient cluster, counted as ONE failure unit) + **at most one T5 negative per case**.
- Derive `expected_status` = failure iff exactly one failure unit present, else success.
- Cross T6: `verification_mode`(3) × `cleanup_mode`(3) = 9 combos per behavior (CROSSED, not rotated).
- Deterministic cap (~5,000–6,000 extensions; `action_type`'s 19 values justify the upper end) + stable sort by assignment tuple + `log` the dropped count (no silent caps).

### Case-count arithmetic (estimate; freeze exact in Task 1)

```text
branch_1 behaviors ≈ 6×3×3×4×4×2 = 1,728 raw → ~1,200 after at-most-one-failure filter
branch_2 behaviors ≈ 3×4×3×4×4 = 576 raw → ~400
branch_3 behaviors ≈ 5×3×4×4×2 = 480 raw → ~340
branch_4 behaviors ≈ 4×3×4×4×3 = 576 raw → ~400
branch_5 behaviors ≈ 3×3×4×4×2 = 288 raw → ~200
total behaviors ≈ ~2,540  × T6(9) = ~22,860 raw → capped at ~5,000–6,000
+ 123 baseline = ~5,100–6,100 total leaf
```

The cap deterministically truncates the raw ~22,860 to the budget; the dropped count is logged. The exact frozen count is asserted in Task 1 after the first green compile (mirror `alter_group`'s frozen 3,888).

## expected_sqlstate map (reuse v1 `_SFV_FAILURE_SQLSTATE` for extensions)

```text
object_state=not_exists / different_signature_exists        42883 (function_does_not_exist / signature_does_not_exist)
argtype_specification=with_partial                          42883 (function_signature_does_not_exist)
rename_target=duplicate_name                                42723 (function_already_exists_in_schema)
owner_target=nonexistent_role                               42704 (role_does_not_exist)
schema_target=schema_not_exists                             3F000 (schema_does_not_exist)
schema_target=pg_catalog_reserved / information_schema_reserved  42501 (permission_denied_for_reserved_schema)
extension_target=extension_not_exists                       42704 (extension_does_not_exist)
configuration_parameter_shape=invalid_parameter             42704 (unrecognized_configuration_parameter)
privilege_level=non_owner_no_privilege / non_owner_with_alter  42501 (must_be_owner_of_function)
schema_dependency=target_schema_not_exists                  3F000 (schema_does_not_exist)
schema_dependency=reserved_schema                           42501 (permission_denied_for_reserved_schema)
role_dependency=owner_role_not_exists                       42704 (role_does_not_exist)
extension_dependency=extension_not_installed                42704 (extension_does_not_exist)
target_function_not_exists=name_not_found / signature_not_found  42883
target_function_different_type=same_name_is_aggregate / procedure  42809 (not_a_function)
permission_insufficient=no_alter_privilege / not_owner_*    42501 (must_be_owner_of_function)
conflicting_action=multiple_conflicting_volatility          42601 (conflicting_or_redundant_options)
identifier_length_exceeded=over_63_chars                    00000 (success via NAMEDATALEN truncation — NOT a failure)
expected_status=failure (meta)                             42883
```

## alter_function-specific gotchas (foreseen)

1. **Routine identity / signature matching** — ALTER FUNCTION matches by name + argument types. `argtype_specification`:
   - `with_full_signature` → exact match (success if the signature exists).
   - `with_partial_signature` → 42883 if the partial prefix does not resolve to exactly one overload.
   - `without_signature` → succeeds ONLY if the name is unique (no overload); on an overloaded name → 42725 (ambiguous_function). The extension must fixture BOTH a unique-name function AND an overloaded pair to cover the `without` branch's dual outcome. (The v1 baseline uses a stable identity-argument oracle; the extension reuses it.)
2. **RENAME / OWNER / SET SCHEMA / DEPENDS on an overloaded name** — must specify args (else 42725 ambiguous). The `function_name_shape=schema_qualified` + `argtype_specification` cross must fixture overloads for the unique-vs-ambiguous boundary.
3. **aggregate / procedure collision** — `target_function_different_type` (42809): ALTER FUNCTION on an aggregate (use `ALTER AGGREGATE`) or a procedure (use `ALTER PROCEDURE`). Fixture an aggregate + a procedure sharing the target name.
4. **reserved-schema SET SCHEMA** — `schema_target=pg_catalog_reserved` / `information_schema_reserved` → 42501 under a non-superuser owner. The privilege/owner fixture must be a non-superuser function owner for these to surface as 42501 (mirror `alter_group`'s privilege-state fixture).
5. **NAMEDATALEN truncation** — `identifier_length_exceeded=over_63_chars` succeeds (name truncated to 63 chars), so it is a SUCCESS value, not expected_failure. Do NOT put it in the failure map.
6. **only the owner can ALTER** — `GRANT ALTER ON FUNCTION` is not valid syntax; a non-owner granted EXECUTE still gets 42501. So `privilege_level=non_owner_with_alter` is a faithful non-owner-with-privilege fixture that still fails 42501 (must_be_owner_of_function).
7. **SUPPORT references a support function** — fixture must create the support function before `ALTER FUNCTION ... SUPPORT`. COST/ROWS take integers; SUPPORT takes a function name.
8. **catalog-audit oracle** — the phase-4 oracle MUST be `SELECT count(*) > 0/=0 AS alias FROM pg_catalog.pg_proc WHERE ... ORDER BY count(*)` (top-level FROM + ORDER BY count(*)), NOT `EXISTS(SELECT 1 ...)` (FROM inside the subquery fails `audit_catalog_observability`). Output-preserving (t/f under same alias). Mirror `alter_group`'s catalog-audit-compliant oracle exactly.
9. **RESET ROLE before catalog oracle** — when the fixture SET ROLE a non-superuser owner, the phase-4 catalog oracle must RESET ROLE first so the catalog is readable as superuser (mirror `alter_group` fix B). pg_proc IS publicly readable, but pg_authid (for `owner_target` verification) is NOT — RESET ROLE before any pg_authid probe.
10. **conflicting volatility** — `conflicting_action=multiple_conflicting_volatility` (IMMUTABLE + VOLATILE in one action list) → 42601 (conflicting_or_redundant_options).

## Implementation outline (mirror `alter_group` reference modules)

- **`alter_function_factor_extension.py`** (NEW):
  - frozen `AlterFunctionFactorExtensionCase` (ordinal, case_id `ALTERFUNCTION{ordinal:04d}`, sql_filename, object_prefix, derivation_id `AF-EXT|{ordinal:04d}|{action}|{verification}|{cleanup}`, derived_from_combination_group, derivation_reason, factor_assignment, consumer_action_id, outcome, expected_sqlstate, expected_failure_reason, is_extension=True) + `AlterFunctionFactorExtensionPlan` (cases, extension_multiset_sha256, derived_combinations_yaml, dropped_count, raw_combination_count).
  - `_BRANCH_AXES` (per-branch crossed axes above), `_CROSSED_BEHAVIOUR_NEGATIVES` (T5 + T1/T2 negatives), `_failure_unit_count` + `_present_failure_pair` (privilege cluster = 1 unit), `_behavior_combinations()` (`itertools.product` per branch, filter at-most-one-failure), `_outcome_for` (lookup `_SFV_FAILURE_SQLSTATE`).
  - `build_alter_function_factor_extension_plan(root)` → ordinal starts at 124 (baseline+1); behaviors × verification(3) × cleanup(3); cap + dropped log; emit `derived_combinations_yaml`.
- **`alter_function_factor_render.py`** (UPDATE): unified `render_alter_function_factor_case(case, root)` handling BOTH `AlterFunctionFactorCase` (baseline) + `AlterFunctionFactorExtensionCase` (extension); 5-phase byte contract (idempotent pre-clean DROP FUNCTION / support fn / roles / schemas → fixture CREATE FUNCTION [+ support fn + overload pair + aggregate + procedure + extension as the case's positive baseline requires] + GRANT/SET ROLE → `-- primary-target-begin/end` + `\set target_sqlstate :SQLSTATE` + `\echo PGCF_TARGET_SQLSTATE=` + [RESET ROLE before catalog oracle] → catalog-audit-compliant oracle → cleanup DROP). `AlterFunctionRenderCase.from_case` adapter (like `alter_group`'s). 2-arg signature (NOT 3-arg).
- **`alter_function_factor_validate.py`** (UPDATE): 2-plan `validate_alter_function_factor_programs(baseline_plan, extension_plan, programs, root, *, selected_case_ids=None)` — re-render canonical bytes + exact byte compare + semantic witness (primary-target-begin/end, fixture/oracle/cleanup loci, sqlstate oracle, derivation record for extensions) + coverage gaps (required factor pairs witnessed across baseline∪extension). Mirror `validate_alter_group_factor_programs` exactly.
- **`alter_function_factor_runtime.py`** (UPDATE): `build_alter_function_runtime_case_set(repo, sql_dir)` combines baseline+extension, sorts by ordinal; `AlterFunctionPg18Runner` (serial bounded psql executor); `compare_alter_function_runs(run_01, run_02)` (identical transcripts/SQLSTATEs/clean state). Constants: socket `/tmp/pgcf-pg18-af-sock-20260819`, distinct port (≠5432, ≠55486 alter_group), db `pgcf_af`, superuser `pgcf_superuser`.
- **`remaining_statement_regress.py`** (UPDATE): the existing alter_function registration (1-plan, v1) → 2-plan form (baseline 123 + extension plan), raising the leaf to the frozen ~5k count. 9 dispatch sites: `_PLAN_BUILDERS` + lazy plan builder (`@lru_cache(maxsize=4)` on BOTH plan wrappers — else ~2.2h uncached for ~5k), `render_statement_regress_case` dispatch, `_coverage_document`, `_alter_function_factor_documents`, `_package_document`, `generate_statement_regress_package`, `validate_statement_regress_package`, + a `target_patterns` entry. Mirror the `alter_group` registration (commit 2317fb0).

## PG18.4 runtime / double-run plan

Isolated per-statement cluster: PG18_BIN=/tmp/pgcf-postgresql-18.4-install/bin, socket `/tmp/pgcf-pg18-af-sock-20260819`, distinct port (≠5432, ≠55486), db `pgcf_af`, superuser `pgcf_superuser`, pg_hba=trust. Serial two-run: pre-clean probe (dirty → skip exit 125) → file phases 1–5 ON_ERROR_STOP=1 → safety-net cleanup subprocess ON_ERROR_STOP=0 (split on the `-- 5. 清理全部本编号对象。` phase-5 marker) → post-clean probe. Two-run comparison requires identical normalized transcripts / SQLSTATEs / clean state / boolean-oracle-failure-count=0. Evidence: `runtime-run-01.json`, `runtime-run-02.json`, `runtime-two-run-comparison.json`, `runtime-validation.json`, `package.json`, `validation.json`, `derived_extension_combinations.yaml`.

---

### Task 1: Compile the bounded extension expander (freeze the count)

**Files:** create `src/pg_case_factory/alter_function_factor_extension.py`; create `tests/test_alter_function_factor_extension.py`.

- [ ] **Step 1: Write the failing extension-count + identity + at-most-one-failure test** — `is_extension=True` for all; unique derivation_id; unique case_id `ALTERFUNCTION0124..N`; every case has ≤1 failure unit; `raw_combination_count > 0`; `dropped_count == max(0, raw - CAP)`; every required factor value (baseline) still witnessed across `baseline ∪ extension`; the frozen count asserted after the first green compile.
- [ ] **Step 2: Run RED.**
- [ ] **Step 3: Implement** the frozen `AlterFunctionFactorExtensionCase`/`Plan` + `_BRANCH_AXES` + `_CROSSED_BEHAVIOUR_NEGATIVES` + `_behavior_combinations()` + `build_alter_function_factor_extension_plan(root)`. Reuse `_SFV_FAILURE_SQLSTATE` + `_BASELINE_DEFAULTS` from `alter_function_factor_loop` (import, do not duplicate).
- [ ] **Step 4: Freeze the count; run GREEN** — Task 1 tests pass in under ten seconds.
- [ ] **Step 5: Commit** — `feat: compile alter function factor extension`.

### Task 2: Unified renderer (baseline + extension)

**Files:** UPDATE `alter_function_factor_render.py`; UPDATE `tests/test_alter_function_factor_render.py`.

- [ ] **Step 1: Write the failing extension-render test** — each extension program has the 5-phase byte contract, exactly one `-- primary-target-begin/end`, catalog-audit-compliant oracle (`SELECT count(*)>0/=0 … ORDER BY count(*)`), RESET ROLE before any pg_authid oracle, derivation-record header, no `{}` leakage, deterministic bytes.
- [ ] **Step 2: Run RED.**
- [ ] **Step 3: Extend the renderer** to handle `AlterFunctionFactorExtensionCase` (`AlterFunctionRenderCase.from_case` adapter + branch-local fixtures: overload pair, aggregate, procedure, support fn, extension, non-superuser owner).
- [ ] **Step 4: Add** the catalog-audit-oracle + RESET-ROLE-before-catalog tests.
- [ ] **Step 5: Run GREEN; commit** — `feat: render alter function extension programs`.

### Task 3: 2-plan byte witness + conservation

**Files:** UPDATE `alter_function_factor_validate.py`; UPDATE `tests/test_alter_function_factor_validate.py`.

- [ ] **Step 1: Write the failing 2-plan conservation test** — `validate_alter_function_factor_programs(baseline_plan, extension_plan, programs, root)`; missing=duplicate=unknown=0; every extension case `is_extension=True` + valid derivation record; coverage gaps=0 (every required factor value witnessed across `baseline ∪ extension`); byte-determinism (re-render == on-disk).
- [ ] **Step 2: Run RED.**
- [ ] **Step 3: Implement** the 2-plan validator (mirror `validate_alter_group_factor_programs`).
- [ ] **Step 4: Run GREEN; commit** — `feat: validate alter function 2-plan witnesses`.

### Task 4: PG18.4 double-run (baseline + extensions)

**Files:** UPDATE `alter_function_factor_runtime.py`; UPDATE `tests/test_alter_function_factor_runtime.py`.

- [ ] **Step 1: Write the failing two-run test** — isolated socket `/tmp/pgcf-pg18-af-sock-20260819`, distinct port; `build_alter_function_runtime_case_set` combines baseline+extension sorted by ordinal; run-01 + run-02 + comparison (`passed=True`, identical transcripts/SQLSTATEs, clean state).
- [ ] **Step 2: Run RED.**
- [ ] **Step 3: Implement** the serial two-run runner + case-set combiner (mirror `alter_group` runtime).
- [ ] **Step 4: Calibrate real PG18 behavior** — init/start the alter_function cluster, run the full double-run, fix oracle/SQLSTATE/fixture mismatches (signature matching, reserved-schema, owner privilege, aggregate/procedure collision, ambiguous 42725). Iterate until mismatch/failure == 0.
- [ ] **Step 5: Implement runtime evidence-collection** (`to_dict` projections; 6-case live PG18.4 test passing).
- [ ] **Step 6: Run GREEN; commit** — `test: add alter function fuller pg18 runtime`.

### Task 5: Static gate

- [ ] style validator PASS on the ~5k SQL; `python -m compileall src`; `git diff --check`; full alter_function suite non-regressing; the 81-test master suite (alter_group etc.) still green.

### Task 6: Register (2-plan) + tickoff + publish

- [ ] UPDATE the alter_function registration in `remaining_statement_regress.py` to the 2-plan form (baseline 123 + extension plan) — the 9 dispatch sites + `@lru_cache(maxsize=4)` on both plan wrappers + `target_patterns` entry. Mirror the `alter_group` registration (2317fb0).
- [ ] Fresh-leaf generate into a tmpdir → byte-verify committed leaf == validated leaf → copy 7 static JSONs + serial/external_schedule → assemble `runtime-validation.json` from committed runtime JSONs + static sha256s.
- [ ] Tickoff via `complete_cycle_statement(discover_statement_factor_cycle(root), progress.json, "alter_function", package_path=<repo-rel>, sql_file_count, validation_evidence=<abs>)` — re-validates all static gates before mutating `progress.json`.
- [ ] Stage ONLY alter_function files (src + tests + ~5k SQL + evidence) via precise `git add` / `git add -f`; do NOT touch the branch's other-task dirty files; count staged files before commit.
- [ ] Commit — `test: publish alter function fuller factor regress`.
- [ ] Mark `progress.json` `alter_function = completed` (fuller); `next_pending_statement` unchanged (alter_index) unless re-stepped.

## Completion gate (all must hold)

ledger frozen (123 baseline unchanged) → extension count frozen → program/derivation conservation (missing/duplicate/unknown=0, every extension `is_extension`+derivation) → byte determinism (re-render==on-disk) → coverage gaps=0 (required factor values witnessed across `baseline ∪ extension`) → style PASS → PG18.4 two-run `passed=True`, all mismatch/failure==0 → runtime evidence bound to current package SHA → registration 2-plan + tickoff → progress/commit on disk.
