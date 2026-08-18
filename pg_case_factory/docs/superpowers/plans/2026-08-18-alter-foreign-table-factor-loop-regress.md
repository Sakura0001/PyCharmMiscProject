# ALTER FOREIGN TABLE Factor-Value Loop Regress Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Generate and locally verify one complete PostgreSQL 18.4 `ALTER FOREIGN TABLE` regress program for every applicable factor-value obligation, without expanding the global Cartesian product.

**Architecture:** Keep the existing official grammar, type inventory, and column applicability compiler as immutable inputs. Add a factor-loop planner that emits one case per local obligation, action-specific witness renderers, a byte-level/static coverage validator, deterministic publication, and a local two-run PostgreSQL 18.4 runner. The 12 `index_role` obligations remain selector-qualified delegated records and do not create false `ALTER FOREIGN TABLE` targets.

**Tech Stack:** Python 3.11+, dataclasses, PyYAML, `unittest`, PostgreSQL 18.4 `psql`, existing `remaining_statement_regress` publication utilities, and `regress-output-script-style` validation.

---

## File map

| Path | Responsibility |
|---|---|
| `src/pg_case_factory/alter_foreign_table_regress.py` | Frozen grammar/type/column catalogs and PG18.4 outcome helpers; no longer a formal Cartesian generator |
| `src/pg_case_factory/alter_foreign_table_factor_loop.py` | Compile 1,817 decisions, split 1,805 programs from 12 delegated records, assign IDs and baselines |
| `src/pg_case_factory/alter_foreign_table_factor_render.py` | Render a complete SQL program for each planned obligation |
| `src/pg_case_factory/alter_foreign_table_factor_validate.py` | Extract primary witnesses from final bytes and prove conservation |
| `src/pg_case_factory/alter_foreign_table_factor_runtime.py` | Run every SQL twice on isolated PG18.4 and write runtime evidence |
| `src/pg_case_factory/remaining_statement_regress.py` | Register plan, renderer, target pattern, package evidence, and output path |
| `tests/test_alter_foreign_table_factor_loop.py` | Ledger, IDs, dispositions, baseline, and conservation tests |
| `tests/test_alter_foreign_table_factor_render.py` | Dimension/action renderer and complete-program tests |
| `tests/test_alter_foreign_table_factor_validate.py` | Mutation and publication validation tests |
| `tests/test_alter_foreign_table_factor_runtime.py` | Two-run, SQLSTATE, cleanup, and evidence tests |
| `artifacts/regress/by-factor/ddl/foreign_table/alter_foreign_table/` | 1,805 numbered SQL files and schedules |
| `artifacts/intermediates/remaining-statement-factor-cycle/alter_foreign_table/` | Plan, coverage, handoff, package, validation, and runtime evidence |

## Frozen arithmetic

```text
GRM official obligations                    136
SFV canonical obligations                   103
INV local column member/action obligations 1557
INV foreign-table topology obligations        7
RISK transaction obligations                  2
------------------------------------------------
local SQL programs                          1805

INV delegated index-role obligations          12
------------------------------------------------
all decisions                               1817
```

The compiler must derive these counts from repository inputs and fail closed on drift. The constants are assertions, not replacement inputs.

### Task 1: Compile the factor-loop obligation ledger

**Files:**
- Create: `src/pg_case_factory/alter_foreign_table_factor_loop.py`
- Create: `tests/test_alter_foreign_table_factor_loop.py`
- Modify: `src/pg_case_factory/alter_foreign_table_regress.py`

- [x] **Step 1: Write the failing ledger-count and identity test**

```python
from collections import Counter
from pathlib import Path
import unittest

from pg_case_factory.alter_foreign_table_factor_loop import (
    compile_alter_foreign_table_factor_loop_obligations,
)

ROOT = Path(__file__).resolve().parents[1]


class AlterForeignTableFactorLoopLedgerTest(unittest.TestCase):
    def test_compiles_exact_required_obligation_bag(self) -> None:
        rows = compile_alter_foreign_table_factor_loop_obligations(ROOT)
        self.assertEqual(1_817, len(rows))
        self.assertEqual(
            {"GRM": 136, "SFV": 103, "INV": 1_576, "RISK": 2},
            Counter(row.kind for row in rows),
        )
        self.assertEqual(1_817, len({row.obligation_id for row in rows}))
        self.assertEqual(12, sum(row.disposition == "delegated" for row in rows))
        self.assertEqual(
            1_805,
            sum(row.disposition in {"covered", "expected_failure"} for row in rows),
        )
```

- [x] **Step 2: Run the test and verify RED**

```bash
uv run python -m unittest -v \
  tests.test_alter_foreign_table_factor_loop.AlterForeignTableFactorLoopLedgerTest.test_compiles_exact_required_obligation_bag
```

Expected: `ModuleNotFoundError: pg_case_factory.alter_foreign_table_factor_loop`.

- [x] **Step 3: Implement the immutable obligation record and compiler**

```python
@dataclass(frozen=True)
class AlterForeignTableFactorObligation:
    ordinal: int
    obligation_id: str
    kind: str
    factor_key: str
    value: str
    consumer_action_id: str
    disposition: str
    source_locator: str
    delegated_statement_key: str | None = None


def compile_alter_foreign_table_factor_loop_obligations(
    repository_root: Path,
) -> tuple[AlterForeignTableFactorObligation, ...]:
    rows = (
        _compile_grammar_obligations()
        + _compile_canonical_obligations(repository_root)
        + _compile_column_obligations(repository_root)
        + _compile_topology_obligations()
        + _compile_transaction_obligations()
    )
    if len(rows) != 1_817:
        raise AlterForeignTableFactorLoopError("obligation count drift")
    if len({row.obligation_id for row in rows}) != len(rows):
        raise AlterForeignTableFactorLoopError("duplicate obligation id")
    return rows
```

Use stable identities:

```text
AFT-GRM|branch|action|factor|value
AFT-SFV|canonical-row-id|branch-context
AFT-INV|consumer-action|dimension-or-selector|member
AFT-RISK|transaction|commit-or-rollback
```

`_compile_column_obligations()` consumes `compile_alter_foreign_table_column_obligations()` and preserves all 1,569 rows. Convert its 12 `handoff:create_index` rows to `disposition="delegated"`; preserve the other 1,557 rows as `covered` or `expected_failure`. Add seven `INV` topology rows. Never call `iter_alter_foreign_table_single_action_inventory_interactions()`.

- [x] **Step 4: Add public exports and run GREEN**

```bash
uv run python -m unittest -v tests.test_alter_foreign_table_factor_loop
```

Expected: all Task 1 tests pass in under five seconds.

- [x] **Step 5: Commit Task 1**

```bash
git add src/pg_case_factory/alter_foreign_table_factor_loop.py \
        src/pg_case_factory/alter_foreign_table_regress.py \
        tests/test_alter_foreign_table_factor_loop.py
git commit -m "feat: compile alter foreign table factor loop"
```

### Task 2: Plan one local case per local obligation

**Files:**
- Modify: `src/pg_case_factory/alter_foreign_table_factor_loop.py`
- Modify: `tests/test_alter_foreign_table_factor_loop.py`

- [x] **Step 1: Write the failing one-to-one plan test**

```python
def test_builds_one_stable_program_per_local_obligation(self) -> None:
    plan = build_alter_foreign_table_factor_loop_plan(ROOT)
    self.assertEqual(1_805, len(plan.cases))
    self.assertEqual(12, len(plan.delegated))
    self.assertEqual(tuple(range(1, 1_806)), tuple(row.ordinal for row in plan.cases))
    self.assertEqual(1_805, len({row.primary_obligation_id for row in plan.cases}))
    self.assertEqual(1_805, len({row.sql_filename for row in plan.cases}))
    self.assertEqual("ALTERFOREIGNTABLE0001.sql", plan.cases[0].sql_filename)
    self.assertEqual("alterforeigntable_0001_", plan.cases[0].object_prefix)
    self.assertEqual("ALTERFOREIGNTABLE1805.sql", plan.cases[-1].sql_filename)
    expected = {
        row.obligation_id
        for row in plan.obligations
        if row.disposition in {"covered", "expected_failure"}
    }
    self.assertEqual(expected, {row.primary_obligation_id for row in plan.cases})
```

- [x] **Step 2: Run the test and verify RED**

Expected: import error for `build_alter_foreign_table_factor_loop_plan`.

- [x] **Step 3: Implement plan records and deterministic numbering**

```python
@dataclass(frozen=True)
class AlterForeignTableFactorCase:
    ordinal: int
    case_id: str
    sql_filename: str
    object_prefix: str
    primary_obligation_id: str
    kind: str
    factor_key: str
    factor_value: str
    consumer_action_id: str
    outcome: str
    expected_sqlstate: str
    expected_failure_reason: str | None
    baseline_assignments: tuple[tuple[str, str], ...]
    execution_profile: str


@dataclass(frozen=True)
class AlterForeignTableFactorLoopPlan:
    obligations: tuple[AlterForeignTableFactorObligation, ...]
    cases: tuple[AlterForeignTableFactorCase, ...]
    delegated: tuple[AlterForeignTableFactorObligation, ...]
    obligation_multiset_sha256: str
```

Use ledger order and four-digit filenames. `baseline_assignments` contains exactly one value for each action-applicable key and never contains a second value for `case.factor_key`.

- [x] **Step 4: Add assignment-driven failure tests**

```python
def test_failure_disposition_drives_case_outcome(self) -> None:
    plan = build_alter_foreign_table_factor_loop_plan(ROOT)
    cases = {row.primary_obligation_id: row for row in plan.cases}
    for obligation in plan.obligations:
        if obligation.disposition == "delegated":
            self.assertNotIn(obligation.obligation_id, cases)
            continue
        case = cases[obligation.obligation_id]
        if obligation.disposition == "expected_failure":
            self.assertEqual("expected_failure", case.outcome)
            self.assertRegex(case.expected_sqlstate, r"^[0-9A-Z]{5}$")
            self.assertNotEqual("00000", case.expected_sqlstate)
            self.assertTrue(case.expected_failure_reason)
        else:
            self.assertEqual(
                ("success", "00000", None),
                (case.outcome, case.expected_sqlstate, case.expected_failure_reason),
            )
```

- [x] **Step 5: Run tests and commit**

```bash
uv run python -m unittest -v tests.test_alter_foreign_table_factor_loop
git add src/pg_case_factory/alter_foreign_table_factor_loop.py \
        tests/test_alter_foreign_table_factor_loop.py
git commit -m "feat: plan one alter foreign table case per factor"
```

### Task 3: Render column-definition and type obligations

**Files:**
- Create: `src/pg_case_factory/alter_foreign_table_factor_render.py`
- Create: `tests/test_alter_foreign_table_factor_render.py`

This task covers `data_type_and_typmod`, `collation`, `nullability`, `default_state`, `generation_mode`, `identity_mode`, and `storage_and_compression` for their real consumer actions.

- [x] **Step 1: Write failing tests for all column-definition members**

```python
def test_every_column_definition_obligation_has_a_real_target_fragment(self) -> None:
    plan = build_alter_foreign_table_factor_loop_plan(ROOT)
    dimensions = {
        "data_type_and_typmod", "collation", "nullability", "default_state",
        "generation_mode", "identity_mode", "storage_and_compression",
    }
    cases = [row for row in plan.cases if row.factor_key in dimensions]
    self.assertEqual(853, len(cases))
    for case in cases:
        witness = resolve_alter_foreign_table_factor_witness(case, ROOT)
        self.assertEqual(case.primary_obligation_id, witness.primary_obligation_id)
        self.assertTrue(witness.target_sql_fragment.strip())
        self.assertNotRegex(witness.target_sql_fragment, r"\{[A-Za-z_]\w*\}")
        self.assertIn(
            witness.semantic_locus,
            {"target.column_definition", "target.type_name", "fixture.column_state"},
        )
```

The asserted 853 rows are derived as follows:

```text
data_type_and_typmod 359 × 2 = 718
collation              10 × 2 =  20
nullability             9 × 4 =  36
default_state           13 × 3 =  39
generation_mode         12 × 1 =  12
identity_mode            6 × 1 =   6
storage/compression     11 × 2 =  22
total                              853
```

- [x] **Step 2: Run the test and verify RED**

Expected: import failure for `resolve_alter_foreign_table_factor_witness`.

- [x] **Step 3: Implement the witness record and type-member resolver**

```python
@dataclass(frozen=True)
class AlterForeignTableFactorWitness:
    primary_obligation_id: str
    setup_sql: tuple[str, ...]
    target_sql_fragment: str
    oracle_sql: tuple[str, ...]
    cleanup_sql: tuple[str, ...]
    semantic_locus: str
    outcome: str
    expected_sqlstate: str
```

For `data_type_and_typmod`, look up the selector-qualified `AlterForeignTableTypeWitness` and use its frozen `declaration_sql`. Preserve selector identity even when two declarations resolve to the same `pg_type`. ADD uses `ADD COLUMN <name> <declaration>`; TYPE uses `ALTER COLUMN <name> TYPE <declaration>`.

- [x] **Step 4: Implement total direct-member fragment maps**

Define dictionaries whose key sets are asserted against the catalog. Required entries include:

```python
NULLABILITY_SQL = {
    "implicit_nullable": "",
    "explicit_null": "NULL",
    "unnamed_not_null": "NOT NULL",
    "named_not_null": 'CONSTRAINT "nn factor" NOT NULL',
    "not_null_no_inherit": "NOT NULL NO INHERIT",
    "not_null_enforced": "NOT NULL ENFORCED",
    "not_null_not_enforced": "NOT NULL NOT ENFORCED",
    "duplicate_not_null_declarations": "NOT NULL NOT NULL",
    "explicit_null_with_not_null": "NULL NOT NULL",
}

IDENTITY_SQL = {
    "no_identity": "",
    "generated_always_identity": "GENERATED ALWAYS AS IDENTITY",
    "generated_by_default_identity": "GENERATED BY DEFAULT AS IDENTITY",
    "generated_always_identity_with_sequence_options": (
        "GENERATED ALWAYS AS IDENTITY (START WITH 11 INCREMENT BY 3)"
    ),
    "generated_by_default_identity_with_sequence_options": (
        "GENERATED BY DEFAULT AS IDENTITY (START WITH 13 INCREMENT BY 5)"
    ),
    "identity_on_non_integer_type": "GENERATED ALWAYS AS IDENTITY",
}
```

Use calibrated maps in `alter_foreign_table_regress.py` for default, generated, storage, compression, and collation outcomes. LZ4 retains a build-capability prerequisite and the current local `0A000`; it must not be labeled as a PostgreSQL-wide semantic rejection.

- [x] **Step 5: Add totality and mutation tests**

For each direct dimension, delete one mapping in a copied registry and assert `AlterForeignTableFactorRenderError("missing member renderer")`. Mutate one type declaration to an empty string and assert rendering fails.

- [x] **Step 6: Run tests and commit**

```bash
uv run python -m unittest -v \
  tests.test_alter_foreign_table_factor_loop \
  tests.test_alter_foreign_table_factor_render
git add src/pg_case_factory/alter_foreign_table_factor_render.py \
        tests/test_alter_foreign_table_factor_render.py
git commit -m "feat: render alter foreign table column factors"
```

### Task 4: Render constraint and dependency obligations

**Files:**
- Modify: `src/pg_case_factory/alter_foreign_table_factor_render.py`
- Modify: `tests/test_alter_foreign_table_factor_render.py`

- [x] **Step 1: Write a failing test for all constraint-member/action rows**

```python
def test_constraint_members_have_isolated_action_witnesses(self) -> None:
    plan = build_alter_foreign_table_factor_loop_plan(ROOT)
    dimensions = {
        "primary_key_participation", "unique_constraint",
        "check_constraint", "foreign_key_role",
    }
    rows = [row for row in plan.cases if row.factor_key in dimensions]
    self.assertEqual(128, len(rows))
    for case in rows:
        witness = resolve_alter_foreign_table_factor_witness(case, ROOT)
        self.assertTrue(witness.target_sql_fragment)
        if case.factor_key in {
            "primary_key_participation", "unique_constraint", "foreign_key_role"
        } and case.factor_value not in {
            "not_primary_key_member", "no_unique_constraint", "no_foreign_key_role"
        }:
            self.assertEqual(
                ("expected_failure", "0A000"),
                (witness.outcome, witness.expected_sqlstate),
            )
```

Arithmetic:

```text
primary key  7 × 2 actions = 14
unique       9 × 2 actions = 18
check       15 × 4 actions = 60
foreign key 18 × 2 actions = 36
total                              128
```

- [x] **Step 2: Run the test and verify RED**

Expected: the first constraint member lacking a renderer is reported.

- [x] **Step 3: Implement total constraint maps**

Render baseline members with a legal CHECK/NOT NULL baseline. Render PK, UNIQUE, and FK forms so PostgreSQL reaches the foreign-table restriction and returns `0A000`; do not substitute parser-invalid text. Render `subquery_check_expression` as the isolated `0A000` check-expression failure. Create referenced local tables for FK members and clean them in reverse dependency order.

- [x] **Step 4: Implement all 60 dependency-state/action witnesses**

Create the declared dependent view, materialized view, sequence, function, type, collation, constraint, trigger, inheritance, partition, or composite row-type fixture. RESTRICT preserves the dependency after failure; CASCADE proves removal. Oracle output is normalized boolean/text and never a raw OID.

- [x] **Step 5: Run tests and commit**

```bash
uv run python -m unittest -v tests.test_alter_foreign_table_factor_render
git add src/pg_case_factory/alter_foreign_table_factor_render.py \
        tests/test_alter_foreign_table_factor_render.py
git commit -m "feat: render alter foreign table constraints"
```

### Task 5: Render structural, name, statistics, and data-profile obligations

**Files:**
- Modify: `src/pg_case_factory/alter_foreign_table_factor_render.py`
- Modify: `tests/test_alter_foreign_table_factor_render.py`

- [x] **Step 1: Write the failing remaining-INV totality test**

```python
def test_every_local_inventory_obligation_has_one_renderer(self) -> None:
    plan = build_alter_foreign_table_factor_loop_plan(ROOT)
    inv_cases = [row for row in plan.cases if row.kind == "INV"]
    self.assertEqual(1_564, len(inv_cases))
    rendered = [resolve_alter_foreign_table_factor_witness(row, ROOT) for row in inv_cases]
    self.assertEqual(1_564, len(rendered))
    self.assertTrue(all(row.primary_obligation_id for row in rendered))
```

- [x] **Step 2: Run the test and verify RED on the first missing dimension**

Expected: `AlterForeignTableFactorRenderError` names the unimplemented dimension/member/action.

- [x] **Step 3: Implement the remaining structural dimensions in catalog order**

```text
column_count_and_position
column_name_shape
partition_key_role
inheritance_role
statistics_target
dropped_or_existing_column_state
data_profile
```

Each renderer receives one primary member and a compatible complete baseline table. Identifier tests use PostgreSQL's 63-byte limit after UTF-8 byte counting and folding. `zero_length_quoted_identifier` is a parser-reachable failure; the overlength collision fixture creates the colliding identifier first.

- [x] **Step 4: Implement exactly seven topology witnesses**

```python
TOPOLOGY_IDS = (
    "standalone", "inheritance_parent", "inheritance_child",
    "inheritance_parent_and_child", "partition_leaf_range",
    "partition_leaf_list", "partition_leaf_hash",
)
```

The primary target uses a legal baseline action. Partition leaf cases validate `42809` or `42P16` only when that guard is primary.

- [x] **Step 5: Implement statistics and attribute-option oracles**

Cover `-1`, `0`, `1`, the configured default, `10000`, above-maximum clamping, below-`-1` failure, attribute-number form, positive/negative `n_distinct`, inherited values, reset, and unknown option. Normalize every oracle.

- [x] **Step 6: Run tests and commit**

```bash
uv run python -m unittest -v tests.test_alter_foreign_table_factor_render
git add src/pg_case_factory/alter_foreign_table_factor_render.py \
        tests/test_alter_foreign_table_factor_render.py
git commit -m "feat: render alter foreign table structural factors"
```

### Task 6: Render all GRM, SFV, and transaction obligations

**Files:**
- Modify: `src/pg_case_factory/alter_foreign_table_factor_loop.py`
- Modify: `src/pg_case_factory/alter_foreign_table_factor_render.py`
- Modify: `tests/test_alter_foreign_table_factor_loop.py`
- Modify: `tests/test_alter_foreign_table_factor_render.py`

- [x] **Step 1: Write failing branch/action coverage tests**

```python
def test_all_27_official_actions_render_once_as_primary(self) -> None:
    plan = build_alter_foreign_table_factor_loop_plan(ROOT)
    action_cases = [
        row for row in plan.cases
        if row.kind == "GRM" and row.factor_key == "target_action"
    ]
    self.assertEqual(27, len(action_cases))
    self.assertEqual(
        {row.action_id for row in load_alter_foreign_table_grammar_actions()},
        {row.factor_value for row in action_cases},
    )
```

- [x] **Step 2: Run the test and verify RED**

Expected: missing routing or rendering for at least one of the six PG18 actions absent from the old canonical action list.

- [x] **Step 3: Implement the 46-axis/109-value grammar router**

For every grammar obligation, select its declared branch/action and render the exact syntax value. `multiple_actions` receives one dedicated command containing two compatible action fragments; it never expands ordered pairs. `one` and `many` list values use frozen lengths one and two. Omitted/present noise keywords must be visible in target bytes.

- [x] **Step 4: Implement the 32-factor/103-value SFV router**

Load factor values from the matrix contract. Define a total `CANONICAL_FACTOR_ROUTE` keyed by factor name and assert its key set equals the matrix factor key set. Negative aliases use isolated fixtures; `verification_mode` values are primary in the oracle locus and `cleanup_mode` values are primary in the cleanup locus.

- [x] **Step 5: Implement commit and rollback transaction witnesses**

The commit case performs a legal metadata change and proves persistence. The rollback case captures original state, runs one target inside `BEGIN`, rolls back, and proves name/column/owner/schema state is unchanged. Both files contain exactly one target statement.

- [x] **Step 6: Run complete witness totality and commit**

```bash
uv run python -m unittest -v \
  tests.test_alter_foreign_table_factor_loop \
  tests.test_alter_foreign_table_factor_render
git add src/pg_case_factory/alter_foreign_table_factor_loop.py \
        src/pg_case_factory/alter_foreign_table_factor_render.py \
        tests/test_alter_foreign_table_factor_loop.py \
        tests/test_alter_foreign_table_factor_render.py
git commit -m "feat: render all alter foreign table factor values"
```

### Task 7: Assemble complete numbered SQL programs

**Files:**
- Modify: `src/pg_case_factory/alter_foreign_table_factor_render.py`
- Modify: `tests/test_alter_foreign_table_factor_render.py`

- [x] **Step 1: Write the failing full-program contract test**

```python
def test_all_programs_are_complete_and_have_one_target(self) -> None:
    plan = build_alter_foreign_table_factor_loop_plan(ROOT)
    for case in plan.cases:
        sql = render_alter_foreign_table_factor_case(plan, case, ROOT)
        self.assertTrue(sql.startswith("-- --------------------------------------------------------\n"))
        self.assertEqual(1, count_primary_alter_foreign_table(sql))
        self.assertIn(f"-- primary_obligation_id: {case.primary_obligation_id}", sql)
        self.assertNotRegex(sql, r"\{[A-Za-z_]\w*\}")
        self.assertTrue(sql.endswith(";\n"))
        self.assertFalse(sql.endswith("\n\n"))
```

- [x] **Step 2: Run the test and verify RED**

Expected: missing `render_alter_foreign_table_factor_case`.

- [x] **Step 3: Implement the complete common fixture**

Every program creates unique no-handler FDW/server objects and a complete structure using the case prefix. For `ALTERFOREIGNTABLE0001.sql`, the first executable statement after the header is `DROP TABLE IF EXISTS alterforeigntable_0001_base CASCADE;`; later files substitute only their frozen numbered prefix. The target foreign table includes an identifier column, primary test column, auxiliary text column, status/check column, and deterministic data when the action permits it.

Use this exact stage order:

```text
header
pre-cleanup
FDW/server setup
complete local/foreign table setup
role/schema/dependency setup
deterministic data setup
exactly one primary ALTER FOREIGN TABLE
SQLSTATE/effect oracle
reverse dependency cleanup
final DROP TABLE IF EXISTS
```

- [x] **Step 4: Implement expected-failure continuation**

Expected-failure files set `\set ON_ERROR_STOP off` immediately before target, print `target_sqlstate :SQLSTATE`, assert equality with `case.expected_sqlstate`, then restore `\set ON_ERROR_STOP on` before cleanup. Success files keep `ON_ERROR_STOP on` and assert `:SQLSTATE = '00000'` after target.

- [x] **Step 5: Render all 1,805 programs twice in memory**

```python
first = [render_alter_foreign_table_factor_case(plan, row, ROOT) for row in plan.cases]
second = [render_alter_foreign_table_factor_case(plan, row, ROOT) for row in plan.cases]
self.assertEqual(first, second)
self.assertEqual(1_805, len(first))
```

- [x] **Step 6: Run tests and commit**

```bash
uv run python -m unittest -v tests.test_alter_foreign_table_factor_render
git add src/pg_case_factory/alter_foreign_table_factor_render.py \
        tests/test_alter_foreign_table_factor_render.py
git commit -m "feat: assemble alter foreign table regress programs"
```

### Task 8: Validate actual witnesses and publish the static package

**Files:**
- Create: `src/pg_case_factory/alter_foreign_table_factor_validate.py`
- Create: `tests/test_alter_foreign_table_factor_validate.py`
- Modify: `src/pg_case_factory/remaining_statement_regress.py`
- Modify: `tests/test_remaining_statement_regress.py`

- [ ] **Step 1: Write failing conservation and mutation tests**

```python
def test_actual_programs_conserve_primary_obligation_bag(self) -> None:
    plan = build_alter_foreign_table_factor_loop_plan(ROOT)
    programs = {
        row.sql_filename: render_alter_foreign_table_factor_case(plan, row, ROOT)
        for row in plan.cases
    }
    report = validate_alter_foreign_table_factor_programs(plan, programs, ROOT)
    self.assertTrue(report.passed)
    self.assertEqual(
        (0, 0, 0),
        (report.missing_count, report.duplicate_count, report.unknown_count),
    )

def test_comment_only_primary_value_cannot_pass(self) -> None:
    plan = build_alter_foreign_table_factor_loop_plan(ROOT)
    case = plan.cases[0]
    sql = render_alter_foreign_table_factor_case(plan, case, ROOT)
    mutated = remove_primary_semantic_locus_but_keep_comments(sql, case)
    report = validate_alter_foreign_table_factor_programs(
        plan,
        {case.sql_filename: mutated},
        ROOT,
        selected_case_ids={case.case_id},
    )
    self.assertFalse(report.passed)
    self.assertEqual(1, report.semantic_witness_mismatch_count)
```

- [ ] **Step 2: Run tests and verify RED**

Expected: missing validator module.

- [ ] **Step 3: Implement strict validation reports**

Store exact expected/actual primary-obligation multisets, SQL SHA map, semantic locus, expected outcome/SQLSTATE, delegated multiset, and missing/duplicate/unknown/mismatch counters. Validate final bytes, not planner metadata. Factor decoders read the declared target, fixture, oracle, or cleanup locus.

- [ ] **Step 4: Register the statement in the main publication path**

Add lazy plan and renderer branches for `alter_foreign_table` and this exact target regex:

```python
r"(?m)^ALTER\s+FOREIGN\s+TABLE(?:\s|;|$)"
```

Package evidence must include:

```json
{
  "generation_mode": "factor_value_independent_loop_v1",
  "decision_count": 1817,
  "sql_file_count": 1805,
  "delegated_count": 12,
  "missing_count": 0,
  "duplicate_count": 0,
  "unknown_count": 0
}
```

- [ ] **Step 5: Publish twice to empty temporary directories and compare bytes**

Use `publish_statement_regress()` twice. Compare complete relative-path-to-SHA maps for SQL, schedules, plan, coverage, handoff, package, and validation. Missing, extra, or different paths fail.

- [ ] **Step 6: Run static tests and commit**

```bash
uv run python -m unittest -v \
  tests.test_alter_foreign_table_factor_loop \
  tests.test_alter_foreign_table_factor_render \
  tests.test_alter_foreign_table_factor_validate \
  tests.test_remaining_statement_regress
git add src/pg_case_factory/alter_foreign_table_factor_validate.py \
        src/pg_case_factory/remaining_statement_regress.py \
        tests/test_alter_foreign_table_factor_validate.py \
        tests/test_remaining_statement_regress.py
git commit -m "feat: publish alter foreign table factor regress"
```

### Task 9: Add the isolated PostgreSQL 18.4 two-run runner

**Files:**
- Create: `src/pg_case_factory/alter_foreign_table_factor_runtime.py`
- Create: `tests/test_alter_foreign_table_factor_runtime.py`

- [ ] **Step 1: Write the failing transcript-comparison test**

```python
def test_two_run_result_requires_identical_normalized_transcripts(self) -> None:
    result = compare_alter_foreign_table_runs(
        run_01=sample_run(stdout="ok\n", stderr="", exit_code=0),
        run_02=sample_run(stdout="ok\n", stderr="", exit_code=0),
    )
    self.assertTrue(result.passed)
    changed = compare_alter_foreign_table_runs(
        run_01=sample_run(stdout="ok\n", stderr="", exit_code=0),
        run_02=sample_run(stdout="different\n", stderr="", exit_code=0),
    )
    self.assertFalse(changed.passed)
```

- [ ] **Step 2: Run the test and verify RED**

Expected: missing runtime module.

- [ ] **Step 3: Implement bounded psql execution**

Use this frozen profile:

```python
PG18_BIN = Path("/tmp/pgcf-postgresql-18.4-install/bin")
PG18_SOCKET = Path("/tmp/pgcf-pg18-aft-sock-20260818")
PG18_PORT = 55484
PG18_DATABASE = "pgcf_aft"
PER_FILE_TIMEOUT_SECONDS = 30
MAX_PARALLELISM = 1
```

Reject a server whose `server_version_num` is outside `[180400, 180500)`. Execute `psql -X -v VERBOSITY=sqlstate -f <file>`. Capture stdout, stderr, exit code, timeout, extracted `target_sqlstate`, boolean oracle failures, and cleanup result.

- [ ] **Step 4: Implement clean-state and two-run evidence**

Before each run, execute an allowlisted probe proving no object with the case prefix remains. Verify the same condition afterward. Run every file twice, normalize only psql banners and absolute temporary paths, then require byte-identical normalized transcripts and identical structured results.

- [ ] **Step 5: Add a six-case PG18.4 integration test**

Select one success, expected failure, quoted identifier, type member, partition guard, and transaction rollback. Execute all six twice and assert 12 executions, zero mismatches, zero cleanup failures, and exact SQLSTATEs.

- [ ] **Step 6: Run tests and commit**

```bash
uv run python -m unittest -v tests.test_alter_foreign_table_factor_runtime
git add src/pg_case_factory/alter_foreign_table_factor_runtime.py \
        tests/test_alter_foreign_table_factor_runtime.py
git commit -m "test: add alter foreign table pg18 runtime"
```

### Task 10: Generate, validate, run, and mark the statement complete

**Files:**
- Modify: `docs/superpowers/plans/2026-08-18-alter-foreign-table-full-regress-coverage-plan.md`
- Modify: `artifacts/intermediates/remaining-statement-factor-cycle/progress.json`
- Create/replace: `artifacts/regress/by-factor/ddl/foreign_table/alter_foreign_table/`
- Create/replace: `artifacts/intermediates/remaining-statement-factor-cycle/alter_foreign_table/`

- [ ] **Step 1: Generate into a temporary sibling directory**

Run the statement publication command with the frozen cycle snapshot. Require exactly 1,805 `.sql` files, two schedules, plan/coverage/handoff/package/validation JSON, and no unexpected files.

- [ ] **Step 2: Run mechanical style validation**

```bash
uv run python skills/regress-output-script-style/scripts/validate_regress_sql_style.py \
  artifacts/regress/by-factor/ddl/foreign_table/alter_foreign_table \
  --prefix ALTERFOREIGNTABLE
```

Expected: `PASS`. `MANUAL_CONFIRMATION_REQUIRED` is not accepted as completion.

- [ ] **Step 3: Run the complete local suite twice**

Call `run_alter_foreign_table_factor_suite()` with serial execution and 30-second per-file timeout. Require:

```text
planned programs         1805
run-01 executions        1805
run-02 executions        1805
missing executions          0
unexpected executions       0
SQLSTATE mismatches          0
oracle failures              0
cleanup failures             0
two-run mismatches           0
```

- [ ] **Step 4: Re-run static validation from published bytes**

Recompute every SQL SHA, the primary-obligation bag, 12 delegated records, schedules, package SHA, and runtime predecessor SHA. Do not trust pre-publication in-memory objects.

- [ ] **Step 5: Update the readable plan and progress atomically**

Set AFT status to `complete`, record exact 1,817/1,805/12 counts, package SHA, runtime evidence SHA, PG18.4 identity, and two-run totals. Mark only `alter_foreign_table` complete and set the next pointer to `alter_function`.

- [ ] **Step 6: Run the final verification set**

```bash
uv run python -m unittest -v \
  tests.test_pg18_column_structure_catalog \
  tests.test_pg18_type_catalog \
  tests.test_alter_foreign_table_regress \
  tests.test_alter_foreign_table_factor_loop \
  tests.test_alter_foreign_table_factor_render \
  tests.test_alter_foreign_table_factor_validate \
  tests.test_alter_foreign_table_factor_runtime \
  tests.test_remaining_statement_regress \
  tests.test_statement_factor_cycle
python -m py_compile \
  src/pg_case_factory/alter_foreign_table_regress.py \
  src/pg_case_factory/alter_foreign_table_factor_loop.py \
  src/pg_case_factory/alter_foreign_table_factor_render.py \
  src/pg_case_factory/alter_foreign_table_factor_validate.py \
  src/pg_case_factory/alter_foreign_table_factor_runtime.py
git diff --check
```

Expected: all tests pass, compilation succeeds, and `git diff --check` prints nothing.

- [ ] **Step 7: Commit package and completion evidence**

```bash
git add docs/superpowers/plans/2026-08-18-alter-foreign-table-full-regress-coverage-plan.md \
        artifacts/regress/by-factor/ddl/foreign_table/alter_foreign_table \
        artifacts/intermediates/remaining-statement-factor-cycle/alter_foreign_table \
        artifacts/intermediates/remaining-statement-factor-cycle/progress.json
git commit -m "test: publish alter foreign table factor regress"
```

Do not begin `ALTER FUNCTION` until Task 10 evidence has been re-read from disk and all mismatch/failure totals remain zero.
