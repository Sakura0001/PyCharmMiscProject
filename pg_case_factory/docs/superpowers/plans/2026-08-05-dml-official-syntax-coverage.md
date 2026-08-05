# PostgreSQL 18.4 DML Official-Syntax Coverage Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add fail-closed, statement-specific PostgreSQL 18.4 syntax coverage for CALL, DELETE, INSERT, MERGE, SELECT, UPDATE, and VALUES, then publish a corrected immutable v2 DML regress package with zero official-syntax gaps.

**Architecture:** A new `dml_syntax` module validates a checked-in PostgreSQL 18.4 DML syntax-factor catalog independently of SQL rendering. The existing `dml_regress` pipeline converts every catalog value into a `syntax_value` coverage atom, renders it through explicit statement-specific resolver registries, verifies one-to-one atom/subcase conservation, and publishes syntax ledgers/reports alongside the existing generic factor package artifacts.

**Tech Stack:** Python 3.10+, PyYAML, `unittest`, JSON manifests, PostgreSQL 18.4 SQL, existing atomic DML package publisher and regress style validator.

## Global Constraints

- PostgreSQL compatibility target is exactly `18.4`.
- DML statement order is exactly `call`, `delete`, `insert`, `merge`, `select`, `update`, `values`.
- Official command sources are the seven `https://www.postgresql.org/docs/18/sql-*.html` pages recorded in the approved design.
- Every command-level optional clause has absent/present coverage and every direct `|` alternative has an explicit syntax value.
- Repeated command-level lists use single-item and multiple-item representatives, not unbounded list lengths.
- Generic expressions, identifiers, data types, `from_item`, and nested query grammars remain covered by existing generic factors unless the command synopsis defines a statement-specific alternative.
- Every syntax value is `success`, `expected_failure`, or `justified_na` with a source locator and concrete reason when non-success.
- Every executable syntax atom maps to exactly one generated SQL subcase.
- Static generation only: no PostgreSQL connection, expected transcript, pg_regress execution, or runtime-verification claim.
- The v1 package remains immutable; corrected output is `artifacts/regress/dml-statement-factor-loop-v2`.
- Preserve unrelated worktree changes; stage or commit only files named by this plan.

---

### Task 1: Add the DML syntax catalog contract and fail-closed loader

**Files:**
- Create: `src/pg_case_factory/dml_syntax.py`
- Create: `tests/test_dml_syntax.py`
- Create: `skills/pg-sql-generation/references/common/postgresql_18_4_dml_syntax_catalog.yaml`

**Interfaces:**
- Produces `DmlSyntaxValue`, `DmlSyntaxFactor`, `DmlStatementSyntaxContract`, `DmlSyntaxCatalog`.
- Produces `load_dml_syntax_catalog(repository_root: Path) -> DmlSyntaxCatalog`.
- Produces `validate_dml_syntax_catalog(catalog, statement_snapshots, renderer_keys, verification_keys) -> dict[str, object]`.
- Later tasks consume stable `syntax_id`, `statement_key`, `factor_key`, `value_key`, source locator, disposition, renderer, verification, dependencies, fixture requirements, and route.

- [ ] **Step 1: Write catalog RED tests**

Add tests that require all seven statements in exact order, reject duplicate syntax IDs, empty value domains, missing `absent` for optional clauses, unknown dependency values, unknown renderer/verification keys, and any matrix `dynamic_inputs.required_fields` entry without a syntax factor or explicit binding.

```python
def test_insert_dynamic_fields_are_bound_to_syntax_factors(self):
    catalog = load_dml_syntax_catalog(REPOSITORY_ROOT)
    insert = catalog.by_statement["insert"]
    self.assertEqual(
        set(insert.dynamic_field_bindings),
        {"index_presence", "conflict_target_shape", "conflict_action"},
    )
```

- [ ] **Step 2: Run catalog tests and verify RED**

Run:

```bash
PYTHONPATH=src .venv/bin/python -m unittest tests.test_dml_syntax.DmlSyntaxCatalogTest -v
```

Expected: import failure for `pg_case_factory.dml_syntax`.

- [ ] **Step 3: Implement immutable catalog parsing and validation**

Use frozen dataclasses and tuples. Reject symlinks, non-mappings, non-string stable keys, missing source locators, non-18.4 targets, unknown dispositions, empty reasons for non-success values, and missing dynamic-field bindings. Keep SQL rendering out of this module.

- [ ] **Step 4: Populate the initial seven-statement catalog skeleton**

Define every command-level syntax factor and value extracted from each official synopsis. Include explicit `coverage_rule`, `optional`, `source_locator`, `renderer`, `verification`, dependencies, disposition, fixture, and route for every value. Do not use generic catch-all values such as `other` or `representative`.

- [ ] **Step 5: Run catalog tests and verify GREEN**

Run the Task 1 command and require all catalog schema and dynamic binding tests to pass.

### Task 2: Close INSERT conflict actions and targets with semantic verification

**Files:**
- Modify: `skills/pg-sql-generation/references/common/postgresql_18_4_dml_syntax_catalog.yaml`
- Modify: `src/pg_case_factory/dml_regress.py`
- Modify: `tests/test_dml_regress.py`
- Modify: `tests/test_dml_syntax.py`

**Interfaces:**
- Adds syntax renderers `insert_without_conflict`, `insert_conflict_do_nothing`, `insert_conflict_do_update`, `insert_conflict_do_update_where`.
- Adds verification renderers `inserted_row_visible`, `conflicting_row_unchanged`, `conflicting_row_updated`, `conflicting_row_locked_not_updated`.

- [ ] **Step 1: Write distinct conflict-action RED tests**

Require separate atoms for `absent`, `do_nothing`, and `do_update`; require target forms `omitted`, `column_list`, `index_expression`, `collation_opclass`, `index_predicate`, and `on_constraint`; require scalar, default, row, sub-select, multi-assignment, and WHERE forms for `DO UPDATE SET`.

```python
self.assertIn("ON CONFLICT DO NOTHING", do_nothing_sql)
self.assertIn("payload = 'alpha'", do_nothing_verification)
self.assertIn("id = 10", do_nothing_verification)
self.assertIn("DO UPDATE SET payload = EXCLUDED.payload", do_update_sql)
self.assertIn("payload = 'conflict-update'", do_update_verification)
self.assertNotEqual(do_nothing_verification, do_update_verification)
```

- [ ] **Step 2: Run INSERT syntax tests and verify RED**

Run:

```bash
PYTHONPATH=src .venv/bin/python -m unittest \
  tests.test_dml_syntax.DmlInsertSyntaxTest \
  tests.test_dml_regress.DmlRendererTest.test_condition_branches_are_reachable_and_attributable -v
```

Expected: missing syntax expansion APIs or zero `DO NOTHING` atoms.

- [ ] **Step 3: Implement INSERT conflict renderers and distinguishing verification**

Use seeded `unique_key=101`. `DO NOTHING` must prove the original payload is unchanged and proposed id is absent. `DO UPDATE` must prove the original row payload changed and proposed id is absent. The false action-WHERE path must prove the original payload remains and no row is returned. Do not use row count as the sole oracle.

- [ ] **Step 4: Verify INSERT GREEN and absence of aggregate-only credit**

Require the targeted tests to pass and require the old `cursor_or_conflict_target` atom not to be the sole syntax credit for any conflict action.

### Task 3: Expand syntax atoms and add syntax conservation audits

**Files:**
- Modify: `src/pg_case_factory/dml_regress.py`
- Modify: `tests/test_dml_regress.py`
- Modify: `tests/test_dml_syntax.py`

**Interfaces:**
- Adds `coverage_kind="syntax_value"` atoms with `syntax_id` metadata.
- Adds per-ledger `expected_syntax_values`, `missing_syntax_values`, and `duplicate_syntax_values`.
- Extends `audit_dml_atom_coverage` and packing conservation with syntax counts.

- [ ] **Step 1: Write syntax atom/conservation RED tests**

Assert every catalog value has exactly one disposition atom, every executable syntax atom has exactly one mapping entry, N/A syntax atoms have no SQL, and tampering one syntax ID produces a validation issue.

- [ ] **Step 2: Run syntax atom tests and verify RED**

Run:

```bash
PYTHONPATH=src .venv/bin/python -m unittest tests.test_dml_syntax.DmlSyntaxAtomTest -v
```

- [ ] **Step 3: Implement syntax atom expansion and audit integration**

Load the catalog during DML discovery, bind its digest, expand values in statement/catalog order, include renderer and verification keys in fixture signatures and bundle JSON, and report missing/duplicate/unresolved syntax values separately from generic factor values.

- [ ] **Step 4: Run syntax atom tests and existing atom/packing tests**

Run:

```bash
PYTHONPATH=src .venv/bin/python -m unittest \
  tests.test_dml_syntax.DmlSyntaxAtomTest \
  tests.test_dml_regress.DmlAtomExpansionTest \
  tests.test_dml_regress.DmlPackingTest -v
```

### Task 4: Audit and render CALL, VALUES, DELETE, and UPDATE syntax

**Files:**
- Modify: `skills/pg-sql-generation/references/common/postgresql_18_4_dml_syntax_catalog.yaml`
- Modify: `src/pg_case_factory/dml_regress.py`
- Modify: `tests/test_dml_syntax.py`

**Interfaces:**
- Adds statement-specific syntax renderer/verification registry entries for CALL, VALUES, DELETE, and UPDATE.

- [ ] **Step 1: Write official-synopsis snapshot RED tests**

Require CALL positional/named/default/output-parameter forms; VALUES single/multiple rows, expression/default/order/limit/offset/fetch forms; DELETE WITH/RECURSIVE, ONLY/descendants, alias, USING list, condition/absent/CURRENT OF, and RETURNING forms; UPDATE WITH/RECURSIVE, ONLY/descendants, alias, scalar/default/row/sub-select SET, multiple assignments, FROM list, condition/absent/CURRENT OF, and RETURNING forms.

- [ ] **Step 2: Verify RED for missing values/renderers**

Run:

```bash
PYTHONPATH=src .venv/bin/python -m unittest \
  tests.test_dml_syntax.DmlCallSyntaxTest \
  tests.test_dml_syntax.DmlValuesSyntaxTest \
  tests.test_dml_syntax.DmlDeleteSyntaxTest \
  tests.test_dml_syntax.DmlUpdateSyntaxTest -v
```

- [ ] **Step 3: Implement minimal valid renderers and branch-specific verification**

Use cursor setup/cleanup only for CURRENT OF values, inherited fixtures for ONLY/descendant values, ordered outputs for VALUES and RETURNING lists, and explicit pre/post-state queries for whole-table versus filtered modification.

- [ ] **Step 4: Verify GREEN for the four statements**

Run the Task 4 test command and the full `DmlRendererTest` class.

### Task 5: Audit and render MERGE syntax

**Files:**
- Modify: `skills/pg-sql-generation/references/common/postgresql_18_4_dml_syntax_catalog.yaml`
- Modify: `src/pg_case_factory/dml_regress.py`
- Modify: `tests/test_dml_syntax.py`

**Interfaces:**
- Adds MERGE source/target modifiers, match-category, action, condition, assignment, overriding, and RETURNING syntax registries.

- [ ] **Step 1: Write MERGE synopsis RED tests**

Require WITH, ONLY/descendants, alias, source table/query, join condition, `WHEN MATCHED`, `WHEN NOT MATCHED BY SOURCE`, `WHEN NOT MATCHED BY TARGET`, optional conditions, UPDATE/DELETE/INSERT/DO NOTHING actions, INSERT column list/VALUES/OVERRIDING forms, multiple WHEN clauses, and RETURNING star/expression/OLD-NEW aliases.

- [ ] **Step 2: Run MERGE tests and verify RED**

Run:

```bash
PYTHONPATH=src .venv/bin/python -m unittest tests.test_dml_syntax.DmlMergeSyntaxTest -v
```

- [ ] **Step 3: Implement MERGE renderers with acted-row verification**

Seed matched, source-only, and target-only rows so each selected WHEN clause acts on a row. Verification must identify inserted, updated, deleted, and unchanged rows rather than merely parsing the statement.

- [ ] **Step 4: Verify MERGE GREEN**

Run the Task 5 command and existing PostgreSQL 18 MERGE parity tests.

### Task 6: Audit and render SELECT syntax

**Files:**
- Modify: `skills/pg-sql-generation/references/common/postgresql_18_4_dml_syntax_catalog.yaml`
- Modify: `src/pg_case_factory/dml_regress.py`
- Modify: `tests/test_dml_syntax.py`

**Interfaces:**
- Adds SELECT command-level syntax renderers for its direct synopsis and direct subproductions without recursively expanding generic expression grammar.

- [ ] **Step 1: Write SELECT synopsis RED tests**

Require WITH/RECURSIVE and materialization modifiers; ALL/DISTINCT/DISTINCT ON; select-list single/multiple; INTO placement; FROM absent/single/multiple and direct join variants; WHERE; GROUP BY ALL/DISTINCT, grouping sets, ROLLUP, CUBE, empty grouping set; HAVING; WINDOW; set operations UNION/INTERSECT/EXCEPT with ALL/DISTINCT; ORDER BY direction/null ordering/operator; LIMIT/OFFSET/FETCH alternatives; and row-lock strengths, OF list, NOWAIT/SKIP LOCKED.

- [ ] **Step 2: Run SELECT tests and verify RED**

Run:

```bash
PYTHONPATH=src .venv/bin/python -m unittest tests.test_dml_syntax.DmlSelectSyntaxTest -v
```

- [ ] **Step 3: Implement SELECT renderers and deterministic ordered verification**

Use small seeded relations and explicit ORDER BY where output order matters. Transaction-only locking cases must declare their envelope, and incompatible syntax combinations must be separate expected failures rather than masquerading as success.

- [ ] **Step 4: Verify SELECT GREEN**

Run the Task 6 command and existing SELECT renderer/parity tests.

### Task 7: Extend package validation, reports, and tamper detection

**Files:**
- Modify: `src/pg_case_factory/dml_regress.py`
- Modify: `tests/test_dml_regress.py`
- Modify: `tests/test_dml_syntax.py`

**Interfaces:**
- Publishes `syntax/*.json` and `reports/syntax/*.json`.
- Adds syntax counts and catalog SHA to `batch.json` and `package.json`.
- Public validation rejects missing/tampered syntax files, counts, mappings, renderer keys, verification keys, and weak-verification flags.

- [ ] **Step 1: Write publication/tamper RED tests**

Generate a temporary batch and mutate one syntax ledger ID, one syntax count, one mapping entry, one verification key, and one report status. Require each mutation to fail public validation.

- [ ] **Step 2: Run publication tests and verify RED**

Run:

```bash
PYTHONPATH=src .venv/bin/python -m unittest \
  tests.test_dml_syntax.DmlSyntaxPublicationTest \
  tests.test_dml_regress.DmlBatchPublicationTest -v
```

- [ ] **Step 3: Implement syntax artifacts and fail-closed package validation**

Hash every syntax artifact, compare report content with fresh validation, and include syntax conservation in the package status. Do not add external fixtures to pg_regress schedules.

- [ ] **Step 4: Verify publication GREEN**

Run the Task 7 command and the regress style-validator tests.

### Task 8: Record root cause and prevention rules in the original design

**Files:**
- Modify: `docs/superpowers/specs/2026-08-05-statement-factor-loop-regress-bundling-design.md`
- Create: `artifacts/evaluations/dml-official-syntax-coverage-report.md`

**Interfaces:**
- Documents the INSERT coverage false positive, its modeling/expansion/validation/test causes, and mandatory prevention gates for all future statement loops.

- [ ] **Step 1: Add a design regression checklist**

Document that factor-ledger completeness does not imply grammar completeness; dynamic required fields must have value domains and resolvers; representative values cannot credit sibling grammar alternatives; branch verification must distinguish neighboring actions; and syntax audits must block packaging.

- [ ] **Step 2: Write the seven-statement syntax coverage report**

For each official command synopsis, record every catalog factor/value, disposition, atom, SQL/subcase, verification strategy, and zero-gap result. Record all changes from v1 and retain the static-only runtime boundary.

- [ ] **Step 3: Self-review both documents**

Reject placeholders, ambiguous scope, stale v1 counts presented as v2, and any claim of database execution.

### Task 9: Generate and independently verify the immutable v2 package

**Files:**
- Create: `artifacts/regress/dml-statement-factor-loop-v2/**`
- Create: `/tmp/dml-statement-factor-loop-v2-repeat/**` (temporary verification only)

**Interfaces:**
- Produces the final corrected SQL-only package and deterministic comparison evidence.

- [ ] **Step 1: Run all unit and static checks**

Run:

```bash
PYTHONPATH=src .venv/bin/python -m unittest \
  tests.test_dml_syntax \
  tests.test_dml_regress \
  skills.regress-output-script-style.tests.test_validate_regress_sql_style -v

PYTHONPATH=src .venv/bin/python -m unittest discover -s tests -q
```

- [ ] **Step 2: Generate v2 once**

Run:

```bash
PYTHONPATH=src .venv/bin/python artifacts/generated_programs/dml-statement-factor-loop.py \
  --repository-root . \
  --output artifacts/regress/dml-statement-factor-loop-v2 \
  --prefix PCF
```

- [ ] **Step 3: Validate package and SQL style**

Run:

```bash
PYTHONPATH=src .venv/bin/python -m pg_case_factory.dml_regress validate \
  artifacts/regress/dml-statement-factor-loop-v2

.venv/bin/python skills/regress-output-script-style/scripts/validate_regress_sql_style.py \
  artifacts/regress/dml-statement-factor-loop-v2/sql --prefix PCF
```

Require zero generic-factor, syntax-factor, scope, parity, risk, conservation, mapping, hash, and style issues.

- [ ] **Step 4: Verify deterministic regeneration**

Generate `/tmp/dml-statement-factor-loop-v2-repeat` with the same options and require:

```bash
diff -qr \
  artifacts/regress/dml-statement-factor-loop-v2 \
  /tmp/dml-statement-factor-loop-v2-repeat
```

to return no differences.

- [ ] **Step 5: Final evidence review**

Confirm v1 remains unchanged, v2 package metadata says `not_run_static_sql_only`, all seven syntax reports have zero gaps, and the human report contains exact final counts and external-harness prerequisites.
