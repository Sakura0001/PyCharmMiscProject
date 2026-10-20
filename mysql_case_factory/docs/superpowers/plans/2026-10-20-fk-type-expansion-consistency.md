# FK type-expansion consistency Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a 568-case internal FK type-expansion regression batch that proves parent/child consistency after `INPLACE` and `INSTANT` child-column expansion.

**Architecture:** A deterministic Python generator creates one SQL scenario per transition/algorithm/FK-action combination. Each SQL file creates a parent and child table, seeds 10 boundary rows, applies one DDL, performs full-table INSERT/UPDATE/DELETE, and prints deterministic PASS/FAIL markers. A separate auditor validates artifact structure and checked-in local evidence.

**Tech Stack:** Python 3.12, pytest, MySQL-compatible SQL, gzip/JSON artifacts.

---

### Task 1: Scenario model and transition catalog

**Files:**
- Create: `src/mysql_case_factory/fk_type_expansion.py`
- Test: `tests/test_fk_type_expansion.py`

- [ ] Define constants:
  - `FK_EXPANSION_BATCH_ID = "2026-10-20-fk-type-expansion-consistency-v1"`
  - `FK_EXPANSION_BATCH_KIND = "fk_type_expansion_consistency"`
  - `FK_EXPANSION_CASE_PREFIX = "TUCFK"`
  - `FK_EXPANSION_DATABASE = "qa_fk_type_expansion"`
  - `FK_EXPANSION_PROFILES = ("inplace", "instant")`
- [ ] Define `FKExpansionScenario` with:
  - `case_no`, `family`, `source_type`, `target_type`, `algorithm`, `fk_action`,
    `expected_ddl_success`, `expected_error_code`, `seed_values`, `update_values`.
- [ ] Implement transition catalogs for integer, character, binary, decimal, and bit.
- [ ] Implement `iter_fk_expansion_scenarios()` yielding exactly 568 scenarios.
- [ ] Implement `smoke_fk_expansion_scenarios()` returning one representative per family.

**Test code:**

```python
def test_scenario_space_is_exact_and_deterministic():
    scenarios = list(iter_fk_expansion_scenarios())
    assert len(scenarios) == 568
    assert scenarios[0].case_id == "TUCFK-000001"
    assert scenarios[-1].case_id == "TUCFK-000568"
    assert [s.case_id for s in iter_fk_expansion_scenarios()] == [s.case_id for s in iter_fk_expansion_scenarios()]

def test_transition_counts_meet_minimum_coverage():
    scenarios = list(iter_fk_expansion_scenarios())
    families = {"integer", "character", "binary", "decimal", "bit"}
    assert {s.family for s in scenarios} == families
    for family in families:
        transitions = {(s.source_type, s.target_type) for s in scenarios if s.family == family}
        assert len(transitions) >= 10, (family, len(transitions))
```

---

### Task 2: SQL rendering and expected output

**Files:**
- Modify: `src/mysql_case_factory/fk_type_expansion.py`
- Test: `tests/test_fk_type_expansion.py`

- [ ] Implement `render_fk_expansion_sql(scenario)` returning a complete SQL script.
- [ ] Each script must:
  - drop old objects;
  - create parent and child tables;
  - seed 10 rows;
  - apply the DDL with the selected algorithm;
  - insert 10 more rows;
  - update all parent FK values and child payloads;
  - exercise the selected FK delete action;
  - delete and reinsert child rows;
  - print deterministic result rows.
- [ ] Implement `expected_fk_expansion_output(scenario)` returning exact TSV rows.

**Test code:**

```python
def test_sql_contains_full_dml_and_fk_oracle():
    scenario = next(iter_fk_expansion_scenarios())
    sql = render_fk_expansion_sql(scenario)
    assert "INSERT INTO" in sql
    assert "UPDATE" in sql
    assert "DELETE FROM" in sql
    assert "LEFT JOIN" in sql
    assert "information_schema.KEY_COLUMN_USAGE" in sql
    assert "DROP TABLE IF EXISTS" in sql

def test_expected_output_is_stable():
    scenario = next(iter_fk_expansion_scenarios())
    output = expected_fk_expansion_output(scenario)
    assert output
    assert all("\t" in line for line in output)
```

---

### Task 3: Artifact writer and generator CLI

**Files:**
- Modify: `src/mysql_case_factory/fk_type_expansion.py`
- Create: `tools/generate_fk_type_expansion.py`
- Test: `tests/test_fk_type_expansion.py`

- [ ] Implement `write_fk_expansion_artifacts(output)`.
- [ ] Write:
  - `manifest.json`
  - `cases.jsonl.gz`
  - `inplace_suite.sql.gz`
  - `instant_suite.sql.gz`
  - `expected_output.tsv`
  - `coverage.tsv`
  - `README.md`
- [ ] Ensure generation is deterministic across repeated runs.
- [ ] Add CLI:

```python
def main() -> None:
    parser = argparse.ArgumentParser(description="Generate the TUCFK FK type-expansion batch")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    manifest = write_fk_expansion_artifacts(args.output)
    print(f"wrote {manifest['case_count']} scenarios to {args.output}")
```

**Test code:**

```python
def test_generator_writes_deterministic_artifacts(tmp_path):
    tool = Path(__file__).parents[1] / "tools" / "generate_fk_type_expansion.py"
    first, second = tmp_path / "first", tmp_path / "second"
    for output in (first, second):
        subprocess.run([sys.executable, str(tool), "--output", str(output)], check=True, cwd=Path(__file__).parents[1])
    for name in ("manifest.json", "cases.jsonl.gz", "inplace_suite.sql.gz", "instant_suite.sql.gz", "expected_output.tsv", "coverage.tsv", "README.md"):
        assert (first / name).read_bytes() == (second / name).read_bytes()
```

---

### Task 4: Auditor

**Files:**
- Create: `src/mysql_case_factory/fk_type_expansion_audit.py`
- Create: `tools/audit_fk_type_expansion.py`
- Test: `tests/test_fk_type_expansion_audit.py`

- [ ] Implement `audit_fk_expansion_artifacts(output, require_local=True)`.
- [ ] Validate:
  - 568 cases;
  - 71 unique transitions;
  - 2 profiles;
  - 4 FK actions;
  - deterministic hashes;
  - expected algorithm matrix;
  - SQL contains full DML and FK oracle;
  - local evidence, if required.

**Test code:**

```python
def test_audit_accepts_structural_artifacts(tmp_path):
    output = tmp_path / "fk"
    subprocess.run([sys.executable, str(Path(__file__).parents[1] / "tools" / "generate_fk_type_expansion.py"), "--output", str(output)], check=True)
    report = audit_fk_expansion_artifacts(output, require_local=False)
    assert report["passed"] is True
    assert report["case_count"] == 568
```

---

### Task 5: Documentation and full-regression integration

**Files:**
- Create: `docs/fk_type_expansion_v1.md`
- Modify: `README.md`
- Modify: `docs/type_upgrade_full_regression.md`
- Modify: `generated/type_upgrade_full_regression/inventory.tsv`
- Modify: `generated/type_upgrade_full_regression/manifest.json`
- Modify: `tests/test_type_upgrade_full_regression.py`

- [ ] Document execution and expected outcomes.
- [ ] Add the batch as the 8th mandatory batch.
- [ ] Update totals to:
  - 8 batches;
  - 24 execution streams;
  - 972,654 cases/scenarios;
  - 2,917,398 case/profile executions.

---

### Task 6: Generate and verify

- [ ] Run:

```bash
PYTHONPATH=src python3 tools/generate_fk_type_expansion.py \
  --output generated/fk_type_expansion_v1
```

- [ ] Run:

```bash
PYTHONPATH=src python3 tools/audit_fk_type_expansion.py \
  --fk generated/fk_type_expansion_v1 --skip-local
```

- [ ] Run full tests:

```bash
uv run --python 3.12 --extra test --extra runner -- pytest -q -p no:cacheprovider
```

- [ ] Commit artifacts, tests, docs, and generator.
