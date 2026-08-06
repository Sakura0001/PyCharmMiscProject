# Unified Regress By-Factor Layout Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Generate a deterministic `artifacts/regress/by-factor` tree whose 13 SQL leaf directories mirror the DML, Cursor, and DCL combination-matrix paths while preserving one-to-one traceability to the three validated source packages.

**Architecture:** Add one focused Python module that discovers structured source assignments, plans per-statement renumbering, rewrites only file-scoped identities, writes a staged tree, and validates its manifest. Existing DML and regress validators remain the source-of-truth gates; the new module never regenerates factors or mutates source packages.

**Tech Stack:** Python 3.11 standard library, existing `pg_case_factory.dml_regress` and `pg_case_factory.regress_generation` contracts, `unittest`, JSON manifests, SQL style validator.

---

## File structure

- Create `src/pg_case_factory/regress_by_factor.py`: source discovery, classification, identity transformation, manifest generation, validation, atomic publishing, and module CLI.
- Create `tests/test_regress_by_factor.py`: unit and integration tests for all classification, conservation, determinism, and failure-closed rules.
- Create `docs/superpowers/plans/2026-08-06-unified-regress-by-factor-layout.md`: this executable plan.
- Generate `artifacts/regress/by-factor/**`: README, manifest, 13 leaf schedules, and 15,260 derived SQL files.
- Do not modify or remove the three source package directories.

### Task 1: Model the exact factor-path inventory

**Files:**
- Create: `tests/test_regress_by_factor.py`
- Create: `src/pg_case_factory/regress_by_factor.py`

- [ ] **Step 1: Write the failing inventory test**

```python
from pathlib import Path
import unittest

from pg_case_factory.regress_by_factor import FACTOR_PATHS, EXPECTED_SQL_COUNTS


ROOT = Path(__file__).resolve().parents[1]


class FactorPathInventoryTest(unittest.TestCase):
    def test_inventory_matches_all_13_combination_matrix_leaves(self) -> None:
        self.assertEqual(13, len(FACTOR_PATHS))
        self.assertEqual(15260, sum(EXPECTED_SQL_COUNTS.values()))
        for statement, relative in FACTOR_PATHS.items():
            matrix = ROOT / "skills/pg-sql-generation/references/combinations" / relative
            self.assertTrue(matrix.with_suffix(".yaml").is_file(), statement)
```

- [ ] **Step 2: Run the test and verify the import fails**

Run: `.venv/bin/python -m unittest tests.test_regress_by_factor.FactorPathInventoryTest`

Expected: `ModuleNotFoundError: No module named 'pg_case_factory.regress_by_factor'`.

- [ ] **Step 3: Implement the immutable inventory and data models**

```python
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping


FACTOR_PATHS = {
    "select": Path("dml/query/select"),
    "values": Path("dml/query/values"),
    "call": Path("dml/routine/call"),
    "delete": Path("dml/table/delete"),
    "insert": Path("dml/table/insert"),
    "merge": Path("dml/table/merge"),
    "update": Path("dml/table/update"),
    "close": Path("cursor/cursor/close"),
    "declare": Path("cursor/cursor/declare"),
    "fetch": Path("cursor/cursor/fetch"),
    "move": Path("cursor/cursor/move"),
    "grant": Path("dcl/privilege/grant"),
    "revoke": Path("dcl/privilege/revoke"),
}

EXPECTED_SQL_COUNTS = {
    "select": 119, "values": 43, "call": 39,
    "delete": 80, "insert": 88, "merge": 90, "update": 83,
    "close": 213, "declare": 213, "fetch": 213, "move": 213,
    "grant": 6933, "revoke": 6933,
}


@dataclass(frozen=True)
class SourceCase:
    domain: str
    statement: str
    source_package: Path
    sql_filename: str
    object_prefix: str
    identity: Mapping[str, Any]
    subcases: tuple[Mapping[str, Any], ...] = ()


@dataclass(frozen=True)
class DerivedCase:
    source: SourceCase
    target_relative_path: Path
    target_filename: str
    target_object_prefix: str
```

- [ ] **Step 4: Run the inventory test**

Run: `.venv/bin/python -m unittest tests.test_regress_by_factor.FactorPathInventoryTest`

Expected: one test passes.

- [ ] **Step 5: Commit the inventory contract**

```bash
git add src/pg_case_factory/regress_by_factor.py tests/test_regress_by_factor.py
git commit -m "feat: define regress factor layout inventory"
```

### Task 2: Discover and classify all structured source cases

**Files:**
- Modify: `tests/test_regress_by_factor.py`
- Modify: `src/pg_case_factory/regress_by_factor.py`

- [ ] **Step 1: Write failing discovery and conservation tests**

```python
from collections import Counter

from pg_case_factory.regress_by_factor import discover_source_cases


class SourceDiscoveryTest(unittest.TestCase):
    def test_all_source_sql_files_are_classified_once(self) -> None:
        cases = discover_source_cases(ROOT)
        counts = Counter(case.statement for case in cases)
        self.assertEqual(EXPECTED_SQL_COUNTS, dict(counts))
        self.assertEqual(15260, len(cases))
        identities = {(case.domain, case.sql_filename) for case in cases}
        self.assertEqual(len(cases), len(identities))

    def test_every_classification_points_to_its_factor_matrix(self) -> None:
        for case in discover_source_cases(ROOT):
            path = FACTOR_PATHS[case.statement].with_suffix(".yaml")
            self.assertTrue(
                (ROOT / "skills/pg-sql-generation/references/combinations" / path).is_file()
            )
```

- [ ] **Step 2: Run the discovery test and verify the missing function failure**

Run: `.venv/bin/python -m unittest tests.test_regress_by_factor.SourceDiscoveryTest`

Expected: import failure for `discover_source_cases`.

- [ ] **Step 3: Implement DML discovery through validated mapping entries**

Implement `_discover_dml_cases(repository)` so it:

```python
report = validate_dml_regress_batch(source_root)
if not report["passed"]:
    raise RegressByFactorError("DML source package is invalid")
entries = json.loads((source_root / "mapping.json").read_text())["entries"]
by_filename: dict[str, list[dict[str, Any]]] = {}
for entry in entries:
    by_filename.setdefault(entry["sql_filename"], []).append(entry)
for filename, file_entries in sorted(by_filename.items()):
    statements = {entry["statement_key"] for entry in file_entries}
    if len(statements) != 1:
        raise RegressByFactorError(f"{filename} maps to multiple statements")
```

Build one `SourceCase` per source SQL and retain all ordered subcase entries for the manifest and DML marker rewrite.

- [ ] **Step 4: Implement Cursor/DCL discovery through regress generation plans**

Use `load_regress_generation_plan(source_root)` and fresh `validate_regress_generation(source_root)`. Classify Cursor test points by exact `TP-CURSOR-CLOSE-`, `TP-CURSOR-DECLARE-`, `TP-CURSOR-FETCH-`, and `TP-CURSOR-MOVE-` tokens. Classify DCL Cartesian/SFV points by the exact GRANT or REVOKE token; for `TP-DCL-COLUMN-TYPES` and `TP-DCL-PG18-MAINTAIN`, require `assignments["dcl_statement"]`.

Reject an unknown test point instead of parsing SQL text.

- [ ] **Step 5: Run source discovery tests**

Run: `.venv/bin/python -m unittest tests.test_regress_by_factor.SourceDiscoveryTest`

Expected: two tests pass with exact `119/43/39/80/88/90/83/213×4/6933×2` counts.

- [ ] **Step 6: Commit structured discovery**

```bash
git add src/pg_case_factory/regress_by_factor.py tests/test_regress_by_factor.py
git commit -m "feat: classify regress sources by factor path"
```

### Task 3: Plan stable per-leaf identities and rewrite SQL safely

**Files:**
- Modify: `tests/test_regress_by_factor.py`
- Modify: `src/pg_case_factory/regress_by_factor.py`

- [ ] **Step 1: Write failing planning and rewrite tests**

```python
from pg_case_factory.regress_by_factor import build_layout_plan, transform_sql


class IdentityRewriteTest(unittest.TestCase):
    def test_each_leaf_uses_independent_five_digit_numbering(self) -> None:
        plan = build_layout_plan(discover_source_cases(ROOT))
        first_by_statement = {case.source.statement: case for case in plan if case.target_filename.endswith("00001.sql")}
        self.assertEqual(set(FACTOR_PATHS), set(first_by_statement))
        self.assertEqual("grant_00001_", first_by_statement["grant"].target_object_prefix)
        self.assertEqual("FETCH00001.sql", first_by_statement["fetch"].target_filename)

    def test_dml_rewrite_preserves_markers_and_removes_source_prefix(self) -> None:
        source = next(case for case in discover_source_cases(ROOT) if case.statement == "insert")
        target = next(case for case in build_layout_plan((source,), enforce_production_counts=False))
        sql = (source.source_package / "sql" / source.sql_filename).read_text()
        rewritten, subcase_map = transform_sql(sql, target)
        self.assertNotIn(source.object_prefix, rewritten)
        self.assertIn(target.target_object_prefix, rewritten)
        self.assertEqual(len(source.subcases), len(subcase_map))
```

- [ ] **Step 2: Run the rewrite tests and verify they fail**

Run: `.venv/bin/python -m unittest tests.test_regress_by_factor.IdentityRewriteTest`

Expected: missing `build_layout_plan` and `transform_sql`.

- [ ] **Step 3: Implement deterministic layout planning**

Group cases by statement, sort each group by source filename, then assign:

```python
target_filename = f"{statement.upper()}{ordinal:05d}.sql"
target_object_prefix = f"{statement}_{ordinal:05d}_"
target_relative_path = FACTOR_PATHS[statement] / target_filename
```

Reject duplicate source identities, duplicate target paths, unexpected counts, non-contiguous ordinals, and target identifiers longer than 63 UTF-8 bytes.

- [ ] **Step 4: Implement exact identity rewriting**

`transform_sql(sql, derived_case)` must:

```python
rewritten = sql.replace(source.object_prefix, derived_case.target_object_prefix)
if rewritten == sql:
    raise RegressByFactorError("source object prefix was not present")
if source.object_prefix in rewritten:
    raise RegressByFactorError("source object prefix remains after rewrite")
```

For DML, replace every source marker stem such as `PCF00001-SC001` with `INSERT00001-SC001`, preserve marker order, and return the exact source/target subcase map. Require one trailing newline and no extra blank line.

- [ ] **Step 5: Run rewrite tests**

Run: `.venv/bin/python -m unittest tests.test_regress_by_factor.IdentityRewriteTest`

Expected: both tests pass.

- [ ] **Step 6: Commit identity rewriting**

```bash
git add src/pg_case_factory/regress_by_factor.py tests/test_regress_by_factor.py
git commit -m "feat: rewrite derived regress identities"
```

### Task 4: Write and validate the complete derived tree

**Files:**
- Modify: `tests/test_regress_by_factor.py`
- Modify: `src/pg_case_factory/regress_by_factor.py`

- [ ] **Step 1: Write failing staged-tree tests**

```python
import tempfile

from pg_case_factory.regress_by_factor import write_layout_tree, validate_layout_tree


class LayoutTreeTest(unittest.TestCase):
    def test_small_tree_has_manifest_schedule_and_exact_mapping(self) -> None:
        selected = tuple(next(case for case in discover_source_cases(ROOT) if case.statement == key) for key in ("select", "fetch", "grant"))
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "by-factor"
            write_layout_tree(ROOT, selected, output, enforce_production_counts=False)
            report = validate_layout_tree(output, expected_source_count=3)
            self.assertTrue(report["passed"], report["issues"])
            self.assertEqual(3, report["sql_file_count"])
            self.assertTrue((output / "manifest.json").is_file())

    def test_validator_detects_a_changed_sql_file(self) -> None:
        selected = (next(case for case in discover_source_cases(ROOT) if case.statement == "fetch"),)
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "by-factor"
            write_layout_tree(ROOT, selected, output, enforce_production_counts=False)
            sql_path = next(output.rglob("*.sql"))
            sql_path.write_text(sql_path.read_text() + "SELECT 99;\n")
            self.assertFalse(validate_layout_tree(output, expected_source_count=1)["passed"])
```

- [ ] **Step 2: Run staged-tree tests and verify failure**

Run: `.venv/bin/python -m unittest tests.test_regress_by_factor.LayoutTreeTest`

Expected: missing tree writer/validator functions.

- [ ] **Step 3: Implement staged output and deterministic JSON**

Write files in plan order. Each leaf schedule contains exactly one line such as `test: FETCH00001` per SQL stem. Write JSON with `sort_keys=True`, `indent=2`, `ensure_ascii=False`, and one final newline. The manifest records source/target paths, prefixes, hashes, identities, subcase mappings, leaf counts, schedule hashes, and `not_run_static_sql_only`.

Write a README that states the source packages, factor-path rule, total count, schedule usage, and runtime boundary without timestamps or temporary paths.

- [ ] **Step 4: Implement fail-closed manifest validation**

Validate regular files only, allowed paths only, exact source/target bijection, expected leaf counts, contiguous filenames, prefix/hash bindings, exact schedule stems, no symlinks, no unexpected SQL, and manifest total conservation. Return:

```python
{
    "kind": "regress_by_factor_validation",
    "passed": not issues,
    "issue_count": len(issues),
    "issues": issues,
    "sql_file_count": len(actual_sql),
    "leaf_count": len(actual_leaves),
}
```

- [ ] **Step 5: Run staged-tree tests**

Run: `.venv/bin/python -m unittest tests.test_regress_by_factor.LayoutTreeTest`

Expected: two tests pass.

- [ ] **Step 6: Commit tree generation and validation**

```bash
git add src/pg_case_factory/regress_by_factor.py tests/test_regress_by_factor.py
git commit -m "feat: generate validated regress factor tree"
```

### Task 5: Add atomic publishing, determinism checking, and CLI

**Files:**
- Modify: `tests/test_regress_by_factor.py`
- Modify: `src/pg_case_factory/regress_by_factor.py`

- [ ] **Step 1: Write failing publish tests**

```python
from pg_case_factory.regress_by_factor import compare_trees, publish_layout


class PublishTest(unittest.TestCase):
    def test_compare_trees_detects_byte_changes(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            left = Path(temporary) / "left"
            right = Path(temporary) / "right"
            left.mkdir(); right.mkdir()
            (left / "x").write_bytes(b"same")
            (right / "x").write_bytes(b"different")
            self.assertEqual(["content differs: x"], compare_trees(left, right))

    def test_publish_refuses_an_existing_target(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            target = Path(temporary) / "by-factor"
            target.mkdir()
            with self.assertRaises(FileExistsError):
                publish_layout(ROOT, target)
```

- [ ] **Step 2: Run publish tests and verify failure**

Run: `.venv/bin/python -m unittest tests.test_regress_by_factor.PublishTest`

Expected: missing publish functions.

- [ ] **Step 3: Implement recursive byte comparison and atomic publish**

Create two sibling temporary staging directories, call `write_layout_tree` independently for both, validate both, compare relative file sets and bytes, then publish the first with `Path.replace(target)`. Reject an existing target before source discovery and ensure failed runs leave no target directory.

- [ ] **Step 4: Implement module CLI**

Support exact commands:

```text
python -m pg_case_factory.regress_by_factor generate --root . --output artifacts/regress/by-factor
python -m pg_case_factory.regress_by_factor validate --root artifacts/regress/by-factor
```

Both commands emit concise JSON. `generate` returns nonzero on any source, conservation, determinism, or publication failure; `validate` returns nonzero when `passed=false`.

- [ ] **Step 5: Run the complete new test module**

Run: `.venv/bin/python -m unittest tests.test_regress_by_factor`

Expected: all tests pass.

- [ ] **Step 6: Commit publishing and CLI**

```bash
git add src/pg_case_factory/regress_by_factor.py tests/test_regress_by_factor.py
git commit -m "feat: publish deterministic regress factor tree"
```

### Task 6: Generate and verify the production tree

**Files:**
- Create: `artifacts/regress/by-factor/**`
- Modify: `docs/superpowers/specs/2026-08-06-unified-regress-by-factor-layout-design.md` only if implementation evidence requires a factual status update.

- [ ] **Step 1: Run the production generator**

Run:

```bash
.venv/bin/python -m pg_case_factory.regress_by_factor generate \
  --root . \
  --output artifacts/regress/by-factor
```

Expected: JSON reports `sql_file_count=15260`, `leaf_count=13`, `passed=true`, and `runtime_verification_status=not_run_static_sql_only`.

- [ ] **Step 2: Run the manifest validator**

Run: `.venv/bin/python -m pg_case_factory.regress_by_factor validate --root artifacts/regress/by-factor`

Expected: `issue_count=0` and `passed=true`.

- [ ] **Step 3: Run the mandatory SQL style validator for all leaves**

Run the validator once for each leaf using the uppercase statement prefix. All 13 invocations must print `PASS`:

```bash
.venv/bin/python skills/regress-output-script-style/scripts/validate_regress_sql_style.py artifacts/regress/by-factor/dml/query/select --prefix SELECT
.venv/bin/python skills/regress-output-script-style/scripts/validate_regress_sql_style.py artifacts/regress/by-factor/dml/query/values --prefix VALUES
.venv/bin/python skills/regress-output-script-style/scripts/validate_regress_sql_style.py artifacts/regress/by-factor/dml/routine/call --prefix CALL
.venv/bin/python skills/regress-output-script-style/scripts/validate_regress_sql_style.py artifacts/regress/by-factor/dml/table/delete --prefix DELETE
.venv/bin/python skills/regress-output-script-style/scripts/validate_regress_sql_style.py artifacts/regress/by-factor/dml/table/insert --prefix INSERT
.venv/bin/python skills/regress-output-script-style/scripts/validate_regress_sql_style.py artifacts/regress/by-factor/dml/table/merge --prefix MERGE
.venv/bin/python skills/regress-output-script-style/scripts/validate_regress_sql_style.py artifacts/regress/by-factor/dml/table/update --prefix UPDATE
.venv/bin/python skills/regress-output-script-style/scripts/validate_regress_sql_style.py artifacts/regress/by-factor/cursor/cursor/close --prefix CLOSE
.venv/bin/python skills/regress-output-script-style/scripts/validate_regress_sql_style.py artifacts/regress/by-factor/cursor/cursor/declare --prefix DECLARE
.venv/bin/python skills/regress-output-script-style/scripts/validate_regress_sql_style.py artifacts/regress/by-factor/cursor/cursor/fetch --prefix FETCH
.venv/bin/python skills/regress-output-script-style/scripts/validate_regress_sql_style.py artifacts/regress/by-factor/cursor/cursor/move --prefix MOVE
.venv/bin/python skills/regress-output-script-style/scripts/validate_regress_sql_style.py artifacts/regress/by-factor/dcl/privilege/grant --prefix GRANT
.venv/bin/python skills/regress-output-script-style/scripts/validate_regress_sql_style.py artifacts/regress/by-factor/dcl/privilege/revoke --prefix REVOKE
```

- [ ] **Step 4: Run targeted and full tests**

Run:

```bash
.venv/bin/python -m unittest tests.test_regress_by_factor
.venv/bin/python -m unittest discover -s tests
```

Expected: new tests and the complete project suite pass; existing intentional skips remain skips.

- [ ] **Step 5: Verify source packages were not changed**

Run fresh source validators and compare their mapping SHA values with the pre-migration values:

```text
DML source validation: passed=true
Cursor mapping SHA: 636b95b687a9d237604a2bc35e6fb2f7e84e38249d2edc4387c78ee9aa3d823e
DCL mapping SHA: a26c7f137f51465ceacea597262031e2859d1b5e7b2d746f167446d3cf0c20d9
```

- [ ] **Step 6: Commit implementation and generated manifest metadata**

Stage only the implementation, tests, plan, and intended by-factor artifacts; do not stage unrelated dirty-worktree files.

```bash
git add src/pg_case_factory/regress_by_factor.py tests/test_regress_by_factor.py docs/superpowers/plans/2026-08-06-unified-regress-by-factor-layout.md artifacts/regress/by-factor
git commit -m "feat: organize regress cases by factor path"
```
