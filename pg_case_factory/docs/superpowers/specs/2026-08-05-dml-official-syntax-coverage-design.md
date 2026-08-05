# PostgreSQL 18.4 DML Official-Syntax Coverage Design

## 1. Goal

Extend the existing DML statement-factor regress generator so that every syntax alternative declared directly by the PostgreSQL 18.4 command synopses for `CALL`, `DELETE`, `INSERT`, `MERGE`, `SELECT`, `UPDATE`, and `VALUES` has an auditable disposition and, when executable, exactly one attributable generated SQL subcase.

This design first closes the known `INSERT ... ON CONFLICT DO NOTHING` / `DO UPDATE` gap, then applies the same syntax-by-syntax audit and remediation to all seven DML commands before publishing a new immutable regress package.

## 2. Problem statement

The existing batch proves complete coverage of its current 105 statement-factor pairs and 344 factor-value rows, but that universe is not equivalent to the complete official command grammar. Statement-specific grammar alternatives can be collapsed into a broad generic value. For example, the current INSERT model credits `condition_shape=cursor_or_conflict_target`, while the official syntax contains two distinct conflict actions and several distinct conflict-target forms.

The INSERT matrix also declares `index_presence`, `conflict_target_shape`, and `conflict_action` as required dynamic fields, but the current expander treats the dynamic interaction as a Boolean requirement and does not expand or validate those fields. This permits a structural coverage audit to pass even when a required syntax alternative has no atom or SQL.

The replacement model must fail closed whenever a command-specific syntax value is declared but lacks a disposition, renderer, verification, or mapping.

## 3. Authoritative scope

The dialect target is exactly PostgreSQL 18.4. The primary sources are the official PostgreSQL 18 command pages:

- `https://www.postgresql.org/docs/18/sql-call.html`
- `https://www.postgresql.org/docs/18/sql-delete.html`
- `https://www.postgresql.org/docs/18/sql-insert.html`
- `https://www.postgresql.org/docs/18/sql-merge.html`
- `https://www.postgresql.org/docs/18/sql-select.html`
- `https://www.postgresql.org/docs/18/sql-update.html`
- `https://www.postgresql.org/docs/18/sql-values.html`

The checked-in statement references remain the immutable local source snapshots used during generation. Each syntax obligation binds both an official URL/source locator and the SHA-256 of the local reference that was audited against it.

Coverage includes:

1. every optional clause in the command's own synopsis in both absent and present forms;
2. every alternative separated by `|` in the command synopsis and its command-specific subproductions;
3. command-specific modifiers such as `ONLY`, `*`, `OVERRIDING`, `ON CONFLICT`, MERGE match categories/actions, row-lock modes, and RETURNING aliases;
4. single-item and multi-item representatives for repeated command-level lists;
5. minimal valid dependent combinations and official command-specific invalid combinations whose failure can be attributed to one cause.

Coverage does not recursively enumerate the complete grammar of generic SQL expressions, identifiers, data types, `from_item`, or nested query expressions referenced from another chapter. Those inputs continue to use the existing expression, name, type, relation, data-shape, and failure factors. A command-specific syntax factor may combine with one representative generic input without creating an unbounded Cartesian product.

## 4. Chosen architecture

### 4.1 Dedicated DML syntax-factor catalog

Add:

`skills/pg-sql-generation/references/common/postgresql_18_4_dml_syntax_catalog.yaml`

The catalog is separate from the existing generic factor audit. This preserves the meaning and historical counts of the 105/344 generic factor universe while adding an explicit statement-specific syntax universe.

The catalog has this shape:

```yaml
schema_version: 1
kind: postgresql_18_4_dml_syntax_catalog
target_version: "18.4"
statements:
  insert:
    official_source: https://www.postgresql.org/docs/18/sql-insert.html
    local_reference: references/statements/dml/table/insert.md
    syntax_factors:
      conflict_action:
        source_locator: synopsis.conflict_action
        coverage_rule: all_values
        values:
          - key: absent
            renderer: insert_without_conflict
            verification: inserted_row_visible
          - key: do_nothing
            renderer: insert_conflict_do_nothing
            verification: conflicting_row_unchanged
          - key: do_update
            renderer: insert_conflict_do_update
            verification: conflicting_row_updated
```

Every value record has a stable key, source locator, expected disposition, renderer key, verification key, fixture requirements, and optional dependency constraints. A syntax value cannot rely on prose-only implication.

### 4.2 Catalog loading and isolation

Add `src/pg_case_factory/dml_syntax.py` with focused immutable contracts:

- `DmlSyntaxValue`
- `DmlSyntaxFactor`
- `DmlStatementSyntaxContract`
- `DmlSyntaxCatalog`
- `load_dml_syntax_catalog(repository_root)`
- `validate_dml_syntax_catalog(catalog, statement_snapshot)`

The module validates schema, statement order, source bindings, unique IDs, non-empty value domains, dependency references, renderer/verification registry keys, and the required absent/present or all-alternative coverage rule. It does not render SQL and does not depend on bundling.

`src/pg_case_factory/dml_regress.py` consumes the validated catalog and converts every syntax value into a `DmlCoverageAtom` with `coverage_kind=syntax_value`. This keeps the existing packer, mapping, shard, publication, and tamper-detection machinery.

## 5. Syntax coverage semantics

### 5.1 Coverage unit

The minimum unit is:

```text
statement × syntax_factor × syntax_value
```

Each unit has exactly one of:

- `success`: generates SQL with a branch-specific observable verification;
- `expected_failure`: generates a single-cause negative SQL and, where stable, an exact SQLSTATE assertion;
- `justified_na`: remains in the syntax ledger with a concrete PostgreSQL 18.4 reason and generates no SQL.

No syntax value may be credited by a neighboring value or by keyword occurrence elsewhere in the file.

### 5.2 Dependent syntax

Dependencies are explicit. For INSERT:

- `DO NOTHING` is covered both with an omitted conflict target and with an explicit arbiter representative;
- `DO UPDATE` always carries a valid conflict target;
- conflict-target alternatives cover column inference, expression inference, collation/opclass modifiers, partial-index predicate, and `ON CONSTRAINT`;
- `DO UPDATE SET` covers scalar assignment, `DEFAULT`, row assignment, sub-SELECT assignment, multiple assignments, and optional action `WHERE`;
- invalid inference and unsupported arbiter cases are expected failures with one attributed cause.

The catalog may define a `syntax_case` when one official production requires a combination of two or more syntax values. A syntax case receives its own stable ID and atom; it cannot silently serve as the only credit for every constituent value.

### 5.3 Repetition and combinations

For `[, ...]` and equivalent repetitions, the catalog records `single_item` and `multiple_items` representatives. It does not enumerate arbitrary list lengths.

Independent optional clauses are not fully cross-multiplied. Each branch is rendered in a minimal valid statement, while combinations are added only when PostgreSQL defines a dependency, incompatibility, visibility difference, privilege difference, or result difference.

## 6. INSERT conflict-action correction

The first TDD slice adds distinct syntax atoms and SQL for:

1. no `ON CONFLICT` clause;
2. `ON CONFLICT DO NOTHING` without a target;
3. `ON CONFLICT (unique_key) DO NOTHING`;
4. `ON CONFLICT (unique_key) DO UPDATE SET payload = EXCLUDED.payload`;
5. `DO UPDATE ... WHERE` true and false paths.

Verification must distinguish the branches:

- no-conflict insert: the new row exists;
- `DO NOTHING`: row count is unchanged, the existing row retains its original payload, and the proposed primary key is absent;
- `DO UPDATE`: row count is unchanged, the existing row contains the proposed payload, and the proposed primary key is absent;
- `DO UPDATE ... WHERE FALSE`: the existing row remains unchanged and the conflicting row is not returned.

A row-count-only query is not a valid verification for either conflict action.

## 7. Seven-statement audit workflow

For each statement in inventory order (`call`, `delete`, `insert`, `merge`, `select`, `update`, `values`):

1. compare the checked-in synopsis to the official PostgreSQL 18 command page;
2. enumerate command-level optional clauses, alternatives, modifiers, lists, and direct subproductions;
3. compare them with existing generic factor atoms, PG18 parity atoms, interaction atoms, and rendered SQL;
4. record every missing or weakly verified branch in the syntax catalog;
5. add a failing catalog/renderer/verification test;
6. implement the minimal renderer and branch-specific verification;
7. require the statement syntax ledger to report zero missing values and zero unresolved registry keys before advancing.

The audit produces a machine-readable statement report and a human-readable summary. A statement cannot be marked complete merely because its SQL contains the command keyword.

## 8. Rendering and verification registry

The syntax catalog refers to stable registry keys rather than embedding arbitrary SQL templates. `dml_regress.py` supplies registries for:

- fixture resolver;
- target-statement renderer;
- observable verification renderer;
- expected-failure assertion;
- cleanup/post-state handler.

Discovery rejects unknown keys. Rendering rejects unused syntax assignments. Validation compares the atom's syntax assignment, the bundle metadata, the subcase marker, and the recorded renderer/verification keys.

Branch-specific verification favors ordered result rows and explicit values. Catalog queries are used only for catalog state; row count alone is accepted only when it uniquely distinguishes the branch.

## 9. Fail-closed validation

The final package is blocked if any of these conditions holds:

- a DML statement is missing from the syntax catalog;
- an official syntax factor has an empty value domain;
- an optional factor lacks its `absent` or `present` disposition;
- an alternative factor has a declared value without an atom;
- a dynamic `required_fields` entry from a DML matrix has no catalog factor or explicit resolver binding;
- a syntax renderer or verification key is unknown;
- an executable syntax atom has zero or multiple mapping entries;
- rendered SQL does not carry the matching syntax atom/subcase metadata;
- verification is empty or is not approved for that syntax value;
- the aggregate or per-statement syntax report contains missing, duplicate, unresolved, or weak-verification entries.

The existing generic factor, scope, risk, packing-conservation, style, hash, atomic-publication, and no-overwrite gates remain mandatory.

## 10. Reports and package layout

The new package adds:

```text
syntax/
  call.json
  delete.json
  insert.json
  merge.json
  select.json
  update.json
  values.json
reports/syntax/
  aggregate.json
  call.json
  delete.json
  insert.json
  merge.json
  select.json
  update.json
  values.json
```

`batch.json` and `package.json` record syntax-factor, syntax-value, executable-syntax-atom, expected-failure, and justified-N/A counts plus the syntax catalog SHA-256.

The human report records, for every statement, official synopsis elements, catalog values, generated atom IDs, SQL/subcase IDs, dispositions, verification strategy, and remaining gaps. Final publication requires remaining gaps to be zero.

## 11. Publication and immutability

The existing `dml-statement-factor-loop-v1` package remains immutable historical evidence. The corrected package is published atomically as:

`artifacts/regress/dml-statement-factor-loop-v2`

Generation never overwrites either package. A second independent v2 generation under `/tmp` must be byte-identical. Schedules are regenerated from the new bundle set; external-harness atoms remain excluded from ordinary pg_regress schedules.

## 12. Testing strategy

Tests are written before production changes and must demonstrate the expected red failure.

Required test groups:

1. catalog schema, source binding, unique IDs, dependencies, and registry validation;
2. a negative test proving an unbound `dynamic_inputs.required_fields` value blocks discovery;
3. distinct INSERT `DO NOTHING` and `DO UPDATE` atoms and SQL;
4. semantic verification assertions that distinguish unchanged and updated rows;
5. one exhaustive renderer-mapping test over every executable syntax value;
6. one official-synopsis snapshot test per DML statement;
7. tamper tests for syntax ledger, mapping, SQL metadata, verification key, reports, and package counts;
8. deterministic v2 regeneration;
9. all existing DML/style tests and the complete repository suite.

Static SQL review remains mandatory for PostgreSQL semantics that cannot be executed in this task.

## 13. Runtime and safety boundary

This task generates and statically audits SQL only. It does not connect to PostgreSQL, create expected transcripts, run pg_regress, or claim PostgreSQL 18.4 runtime verification. Multi-session, restart/recovery, foreign-table, or privilege-sensitive branches retain explicit authorized harness routes and prerequisites.

## 14. Acceptance criteria

The work is complete only when:

1. INSERT conflict actions and target forms have distinct syntax atoms and distinguishing verification;
2. all seven official command synopses have reviewed syntax catalogs;
3. every syntax value is success, expected failure, or justified N/A with a source locator;
4. every executable syntax atom maps exactly once to a generated subcase;
5. per-statement and aggregate syntax audits report zero gaps;
6. all generic factor and packing-conservation gates still pass;
7. all SQL style checks and repository tests pass;
8. v2 deterministic regeneration has no byte differences;
9. the final report states that database execution and expected-output generation were not performed.
