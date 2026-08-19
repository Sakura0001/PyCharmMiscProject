# ALTER INDEX Factor-Value Loop Regress Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Generate and locally verify one complete PostgreSQL 18.4 `ALTER INDEX` regress program for every applicable factor-value obligation, then bounded post-coverage extensions toward thousands — without expanding the global Cartesian product.

**Architecture:** A YAML-driven grammar catalog (loaded from `alter_index.yaml`) exposes the nine `ALTER INDEX` branches as grammar actions and the nineteen canonical factors as grammar axes, with declared `compatibility` rules binding factor values to expected sqlstates. The marginal factor-value ledger (one stable local SQL program per non-delegated obligation value) is the required-coverage baseline; the bounded post-coverage extension phase (cross positive T1–T4 axes × T6, at-most-one T5 negative per case) multiplies it toward thousands. `ALTER INDEX` declares `column_type_coverage` `conditional` with `branch_scoped_representative_types`, so there is **no exhaustive column `INV` sweep** — representative types (integer/text/jsonb/tsvector/int4range/point) are branch-scoped, and exhaustive type compatibility remains owned by `CREATE INDEX`. The renderer emits complete schema/table/index fixture, one target statement, a success or expected-failure oracle, idempotent cleanup, and a residual check.

**Tech Stack:** Python 3.11+, dataclasses (frozen), PyYAML, `unittest`, PostgreSQL 18.4 `psql`, existing `remaining_statement_regress` publication utilities, and `regress-output-script-style` validation.

---

## Scope discipline (why this statement's marginal ledger is 772, not ~1,576)

`skills/pg-sql-generation/references/combinations/ddl/index/alter_index.yaml` `coverage_scope`:

| scope | required | mode | reason |
|---|---|---|---|
| target_object_coverage | true | explicit | index lifecycle/storage/statistics/partition/dependency |
| target_relation_coverage | true | explicit | the index's owning table |
| table_coverage | true | representative | partitioned + regular table fixture variants |
| column_type_coverage | true | conditional | branch_scoped_representative_types — no exhaustive INV |

Therefore the formal ledger has **no 1,576-row column `INV` block** (unlike `ALTER FOREIGN TABLE`). Quantity is driven by `GRM` (21 action skeletons across 10 combination groups × 9 branches) + `SFV` (751 single factor values). There is no separate `RISK` section — T5 negative controls (`invalid_combination`, `syntax_error`, `permission_boundary`) are realized as expected-failure `SFV` values. The exact marginal total is **compiled, not pre-assumed**; this plan never targets a number first.

---

## File map

| Path | Responsibility | Status |
|---|---|---|
| `src/pg_case_factory/alter_index_regress.py` | YAML-driven grammar catalog, grammar actions/axes/type-witnesses, `EXPECTED_SQLSTATE_BY_REASON`, `evaluate_condition`, `_METHOD_PARAMETER_VALID` | ✅ DONE (committed 51696367) |
| `src/pg_case_factory/alter_index_factor_loop.py` | Compile marginal obligations, assign IDs/baselines, fail-fast drift guards, disposition→outcome attribution | ✅ DONE (committed 51696367) |
| `src/pg_case_factory/alter_index_factor_extension.py` | Bounded post-coverage extension expander (772 → thousands) | ⬜ follow-on |
| `src/pg_case_factory/alter_index_factor_render.py` | Unified 2-arg renderer (baseline + extension), byte contract | ⬜ follow-on |
| `src/pg_case_factory/alter_index_factor_validate.py` | 2-plan byte witness + conservation (marginal + extensions = total) | ⬜ follow-on |
| `src/pg_case_factory/alter_index_factor_runtime.py` | Run every SQL twice on isolated PG18.4, write runtime evidence | ⬜ follow-on |
| `src/pg_case_factory/remaining_statement_regress.py` | Register `_build_alter_index_plan_lazily` + `target_patterns` entry, package evidence, output path | ⬜ follow-on |
| `tests/test_alter_index_factor_loop.py` | ledger, IDs, dispositions, baseline, factor-coverage, determinism | ✅ DONE (11 tests GREEN) |
| `tests/test_alter_index_factor_extension.py` | extension count freeze, conservation, byte-stability | ⬜ follow-on |
| `tests/test_alter_index_factor_render.py` | branch renderer + complete-program byte contract | ⬜ follow-on |
| `tests/test_alter_index_factor_validate.py` | actual witness + conservation mutation gate | ⬜ follow-on |
| `tests/test_alter_index_factor_runtime.py` | two-run, SQLSTATE, cleanup, determinism | ⬜ follow-on |
| `artifacts/regress/by-factor/ddl/index/alter_index/` | numbered SQL files (`ALTERINDEX*.sql`) + schedules | ⬜ follow-on |
| `artifacts/intermediates/remaining-statement-factor-cycle/alter_index/` | plan, coverage, handoff, package, validation, runtime evidence | ⬜ follow-on |

---

## Frozen arithmetic (marginal ledger DONE; extension count compiled in Task E1)

```text
GRM action-skeleton obligations              21   (10 combination groups × 9 branches; one per (group,branch) action)
SFV single factor-value obligations          751  (one per (action, axis, value) from each group's expansion)
INV column/table/relation obligations         0   (column_type_coverage=conditional, not exhaustive)
RISK transaction obligations                  0   (T5 negatives realized as expected-failure SFV values)
delegated handoffs                            0   (T5 boundaries are real ALTER INDEX errors → expected_failure)
------------------------------------------------
marginal local SQL programs                 772   ✅ FROZEN (committed 51696367)
extension local SQL programs            compiled   (bounded cross, Task E1; cap ~50k table + drop-logging)
```

**Marginal ledger frozen values (commit 51696367):**
- `obligation_multiset_sha256 = adf8e0b9a5d1310b93a7764989c95bd55086d89f863da4f3c9275d824b63f7b6`
- kind split: `GRM=21`, `SFV=751`
- outcome split: `success=485`, `expected_failure=287`
- all 19 canonical factor values fully witnessed (0 missing); no synthetic factors leak outside `factor_contract`
- `case_id` range `ALTERINDEX00001`..`ALTERINDEX00772`; ordinals contiguous 1..772; baselines sorted + unique-key; `statement_branch` bound in every case's baseline.

The compiler must derive these counts from repository inputs and fail closed on drift (`_assert_frozen_ledger`). Constants are assertions, not replacement inputs.

---

## Grammar model (faithful to PG18 `sql-alterindex.html`)

Official synopsis (9 branches):

```sql
ALTER INDEX [ IF EXISTS ] name RENAME TO new_name                         -- rename
ALTER INDEX [ IF EXISTS ] name SET TABLESPACE tablespace_name            -- set_tablespace
ALTER INDEX name ATTACH PARTITION index_name                             -- attach_partition
ALTER INDEX [ IF EXISTS ] name DEPENDS ON EXTENSION extension_name       -- depends_on_extension
ALTER INDEX [ IF EXISTS ] name NO DEPENDS ON EXTENSION extension_name    -- no_depends_on_extension
ALTER INDEX [ IF EXISTS ] name SET ( storage_parameter = value [, ...] ) -- set_storage
ALTER INDEX [ IF EXISTS ] name RESET ( storage_parameter [, ...] )        -- reset_storage
ALTER INDEX [ IF EXISTS ] name ALTER COLUMN column SET STATISTICS integer -- set_statistics
ALTER INDEX [ IF EXISTS ] name ALL IN TABLESPACE name [OWNED BY ...] SET TABLESPACE ...  -- all_in_tablespace
```

The 10 combination groups (`combination_groups` in the YAML) exercise these branches across success, missing-index (with/without `IF EXISTS`), storage-parameter/method validity, statistics/column boundary, extension-dependency, attach-partition mismatch, system-catalog, and PG18 revalidate contexts.

`EXPECTED_SQLSTATE_BY_REASON` (15 reasons → PG18.4 sqlstate) backs the disposition attribution; the downstream PG18.4 serial two-run calibration verifies and refines these against the live catalog.

---

## Extension design blueprint (the non-obvious insight — read before Task E1)

**Key insight:** the extension expander REUSES the marginal ledger's compatibility logic — it does NOT redesign bespoke validity/attribution rules. The grammar's `failure_when` conditions and `EXPECTED_SQLSTATE_BY_REASON` already encode the compatibility contract; the extension just crosses more axes and re-evaluates the same predicates.

### Positive axes (crossed, T1–T4)
Per action, from the group's `expansion` block: `object_state`, `if_exists`, `name_shape`, `index_method`, `storage_parameter_set`, `storage_parameter_reset`, `statistics_value`, `column_number_value`, `owned_by`, `nowait`, `no_keyword`, `column_keyword`.

### Excluded from the cross
- `expected_status` — **derived** (the outcome), not an independent input. Crossing it is nonsensical; it is set by `_resolve_disposition`.
- `statement_branch` — the branch selector; fixed per action (one action = one branch).
- `target_action` — not a contract factor (synthetic; not used in this ledger).

### T6 (crossed as verification/cleanup context)
`verification_mode`, `cleanup_mode` — crossed per Option A ("cross positive T1–T4 axes × T6 cross"). They affect the program's verification/cleanup shape, not the SQL sqlstate, so the same factor assignment multiplies across verification contexts (legitimate bounded extension).

### T5 negatives (at-most-one)
`invalid_combination` (6 values), `syntax_error` (2 values), `permission_boundary` (3 values) — each contributes either its `none` value (no negative) OR exactly one real negative value, and **at most one real negative across all three T5 factors** per extension case (the attribution rule: a case carries a single attributable failure unit).

### Validity + attribution (REUSE the ledger)
For each crossed combination:
1. Build `bindings` = group baseline + `statement_branch` + crossed positive-axis values + at-most-one T5 negative + T6 values.
2. Call `_resolve_disposition(action, bindings)` — evaluates the group's `failure_when` conditions via `evaluate_condition` (first match → `expected_failure` with reason→sqlstate; else `default_expected_status`).
3. Valid case ⇔ `failure_unit_count(bindings) <= 1` (count `failure_when` conditions evaluating `True`; the at-most-one-T5 rule guarantees this for T5; positive-axis failures like `storage_parameter not valid for index_method` count as the single unit).
4. Outcome = `expected_failure` (1 unit) or `success` (0 units); sqlstate via `EXPECTED_SQLSTATE_BY_REASON` or `00000`.

### Bounding (forbidden cartesian → bounded)
The full positive-axes cartesian per action is 140k–840k (e.g. rename: 2×2×6×6×T6 9×T5 ~10 ≈ 13k before cap) — **never emit the full cartesian**. Bound via:
- positive-axes-only cross (exclude `expected_status`, `statement_branch`);
- at-most-one T5 (not the T5 cartesian);
- per-statement cap ~50k (table statement) + **log dropped** combinations if capped (no silent truncation).

### Conservation
- Marginal cases (one axis varied, rest baseline) are EXCLUDED from extensions (they're already in the 772 ledger).
- Extension cases = combinations where ≥2 positive axes differ from the group baseline.
- `extension_multiset_sha256` frozen; total = marginal + extensions (no overlap, no gap).

---

## Marginal ledger tasks (DONE — committed 51696367)

- [x] **Task L1** Compile the marginal obligation ledger (`compile_alter_index_factor_loop_obligations`): GRM(21) + SFV(751) = 772, fail-fast drift guards.
- [x] **Task L2** One case per obligation + stable `ALTERINDEX00001..00772` numbering + sorted baselines + `statement_branch` binding.
- [x] **Task L3** Disposition→outcome attribution (`_resolve_disposition`: `failure_when` first-match → `expected_failure`+sqlstate; else `default_expected_status`).
- [x] **Task L4** `tests/test_alter_index_factor_loop.py` — 11 tests GREEN (determinism, frozen counts, 19-factor coverage 0-missing, outcome attribution, sqlstate mapping, baseline invariants, 9-branch coverage, obligation uniqueness).
- [x] **Task L5** Static gates: `py_compile` OK; sibling imports OK; surgical commit (3 files, 938 insertions, no other-task files, no attribution).

---

## Extension + render + runtime + publish tasks (follow-on — fresh-context fork)

### Phase 1 — no DB (can parallelize across statements, but alter_index is one statement)
- [ ] **Task E1** `alter_index_factor_extension.py` expander + `tests/test_alter_index_factor_extension.py` (freeze count, conservation vs marginal 772, byte-stability, at-most-one-T5, no expected_status cross).
- [ ] **Task E2** `alter_index_factor_render.py` unified 2-arg renderer (baseline + extension), byte contract: 5-phase `-- primary-target-begin/end` + `PGCF_TARGET_SQLSTATE=` (mirror `alter_function_factor_render.py`).
- [ ] **Task E3** `alter_index_factor_validate.py` 2-plan byte witness + conservation validator (marginal 772 + extensions = total).
- [ ] **Task E4** `alter_index_factor_runtime.py` runtime case-set combiner + skip-gated test (module code only; mirror `alter_function_factor_runtime.py`).
- [ ] **Task E5** Register `_build_alter_index_plan_lazily` + `target_patterns` entry in `remaining_statement_regress.py`; `@lru_cache(maxsize=4)` on BOTH plan wrappers (gotcha #2 — else ~2.2h render for thousands).
- [ ] **Task E6** Static gates: `py_compile` + style (`validate_regress_sql_style.py` for SQL) + all 5 alter_index test modules GREEN + 80%+ coverage.

### Phase 2 — serial DB-bound (one cluster, MAX_PARALLELISM=1)
- [ ] **Task D1** Stand up alter_index's OWN PG18.4 cluster: port ~55487, db `pgcf_ai`, socket `/tmp/pgcf-pg18-ai-sock-20260819`, `PG18_BIN=/tmp/pgcf-postgresql-18.4-install/bin`, superuser `pgcf_superuser`. Do NOT reuse user's 5432 PG16, af cluster 55485, or ag cluster 55486.
- [ ] **Task D2** Serial doublerun #1 (run-01 + run-02 + two-run-comparison).
- [ ] **Task D3** Calibration: Track A attribution scoping (don't let a branch's privilege negative leak into other branches) + Track B render fixes (mirror alter_function calibration gotchas). Iterate until `passed=True`, 0 mismatches across sqlstate/execution/oracle/cleanup/transcript/structured.
- [ ] **Task D4** Publish via `/tmp/ai_publish.py` mirroring `/tmp/af_publish.py`: generate into tmpdirs → byte-verify committed leaf == validated leaf → copy 7 static JSONs (plan/coverage/package/validation/factor-loop-plan/handoff/actual-factor-witness-report) + serial/external_schedule → assemble `runtime-validation.json` from committed run-01/02/comparison + static sha256s → verify 11 artefacts.
- [ ] **Task D5** `progress.json` tickoff: `complete_cycle_statement(discover_statement_factor_cycle(root), progress.json, "alter_index", package_path=<repo-rel>, sql_file_count=<N>, validation_evidence=<abs>)` — re-validates all static gates before mutating.
- [ ] **Task D6** Surgical commit (only alter_index files; `artifacts/` paths need `git add -f`; count staged first; no attribution). Other-task dirty files on this branch must remain untouched.

---

## Reusable gotchas (from the proven alter_function/alter_group/alter_foreign_table templates)

1. **catalog-audit-compliant oracle** — existence/membership probes must be `SELECT count(*) > 0/=0 AS alias FROM pg_catalog... WHERE... ORDER BY count(*)` (top-level FROM + ORDER BY count(*)); NOT `SELECT EXISTS(SELECT 1 FROM...)`. Output-preserving (t/f under same alias).
2. **Master-flow registration** needs `@lru_cache(maxsize=4)` on BOTH plan wrappers + a `target_patterns` entry (else the static "real statement" gate uses the `r"(?!)"` fallback and never matches; else per-case render rebuilds plans → ~2.2h).
3. **publish byte contract** — generate into tmpdir → byte-verify committed leaf == validated leaf → copy 7 static JSONs + schedules → assemble runtime-validation.json from committed runtime + static sha256s; the tickoff `complete_cycle_statement` re-validates all static gates before mutating `progress.json`.
4. **artifacts gitignored** — `.gitignore:66 artifacts/` → `git add` refuses even tracked files under gitignored paths in this git version; use `git add -f` for all `artifacts/` paths (harmless for tracked, required for new 5-digit SQL).
5. **surgical commits** — branch `codex/mysql-8022-8041-parity` carries many user/other-task dirty files; stage ONLY the current statement's files via precise `git add`; count staged before commit; no `git reset --hard`; no attribution (globally disabled).
6. **DB-bound doublerun is serial** — single isolated cluster per statement, MAX_PARALLELISM=1; parallel doubleruns collide on the shared DB.
