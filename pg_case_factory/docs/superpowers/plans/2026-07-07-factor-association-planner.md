# Factor Association Planner Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a reusable hybrid Factor Association Planner that reads the existing pg_case_factory factor assets and produces expert-level derived scenario-family plans for any statement, without hardcoding CREATE INDEX only.

**Architecture:** Keep the current Python engine minimal and add a focused association-planning module that consumes already structured statement references, combination matrices, type catalog metadata, and shared coverage inventory. The planner emits structured scenario families, coverage obligations, lifecycle outlines, oracle bindings, and cleanup expectations; SQL rendering remains a downstream concern.

**Tech Stack:** Python 3.9+, PyYAML, unittest/pytest-compatible tests, existing `pg_case_factory.skill_loader` conventions.

---

## File Structure

- Create `src/pg_case_factory/association_planner.py`
  - Owns semantic tagging, association rule application, scenario-family construction, and YAML-safe serialization.
- Modify `src/pg_case_factory/__init__.py`
  - Exports the public planner entry points.
- Modify `src/pg_case_factory/engine.py`
  - Re-exports planner entry points for generated programs and tools.
- Create `tools/plan_factor_associations.py`
  - CLI for generating association plans from a statement key or matrix path.
- Create `tests/test_association_planner.py`
  - Unit tests for semantic tagging, scenario families, and generic behavior.
- Create `tests/test_plan_factor_associations_cli.py`
  - CLI tests against a temporary mini repository fixture.
- Create `skills/pg-sql-generation/references/common/association_policy.md`
  - Documents the hybrid policy: facts from catalogs, deterministic rules first, LLM-derived ideas only as marked extensions.
- Create `docs/factor_association_planner_map.md`
  - Final project-facing版图: inputs, planner stages, outputs, quality gates, and extension path.

## API Contract

`association_planner.py` must expose these functions:

```python
def load_markdown_yaml(path: Path) -> dict:
    """Load the first fenced yaml block from a markdown reference."""

def load_yaml_file(path: Path) -> dict:
    """Load a yaml file as a mapping."""

def infer_semantic_tags(factor_name: str, factor_doc: dict) -> tuple[str, ...]:
    """Infer stable semantic tags from factor metadata."""

def build_factor_profiles(statement_config: dict) -> dict[str, dict]:
    """Return factor profiles keyed by local factor name."""

def plan_associations(
    *,
    statement_config: dict,
    matrix_config: dict | None = None,
    type_catalog_config: dict | None = None,
    coverage_inventory: dict | None = None,
) -> dict:
    """Return an association plan with scenario_families and coverage_obligations."""
```

The returned plan must contain:

```yaml
kind: factor_association_plan
target_statement:
  key: create_index
  name: CREATE INDEX
association_model:
  mode: hybrid_rule_first
factor_profiles: {}
scenario_families: []
coverage_obligations: []
quality_gates: []
```

## Task 1: Core Association Planner

**Files:**
- Create: `src/pg_case_factory/association_planner.py`
- Modify: `src/pg_case_factory/__init__.py`
- Modify: `src/pg_case_factory/engine.py`
- Test: `tests/test_association_planner.py`

- [ ] **Step 1: Write failing semantic tagging tests**

Add tests that assert:

```python
from pg_case_factory.association_planner import infer_semantic_tags

def test_infer_semantic_tags_for_column_type_factor():
    tags = infer_semantic_tags("data_type", {"label": "列数据类型", "values": ["integer", "jsonb"]})
    assert "column_type" in tags
    assert "method_compatibility_sensitive" in tags

def test_infer_semantic_tags_for_transaction_factor():
    tags = infer_semantic_tags("concurrently", {"label": "CONCURRENTLY", "values": ["false", "true"]})
    assert "transaction_sensitive" in tags
    assert "locking_sensitive" in tags
```

Run:

```bash
env PYTHONDONTWRITEBYTECODE=1 python3 -m pytest tests/test_association_planner.py -q -p no:cacheprovider
```

Expected: FAIL because `pg_case_factory.association_planner` does not exist.

- [ ] **Step 2: Implement semantic tagging**

Implement deterministic name/label/value heuristics for:

- `column_type`
- `relation_kind`
- `data_profile`
- `schema_mutation`
- `dependency_state`
- `privilege_environment`
- `transaction_sensitive`
- `locking_sensitive`
- `optimizer_sensitive`
- `negative_control`
- `oracle`

- [ ] **Step 3: Write failing scenario-family tests**

Add tests that construct a minimal `create_index`-like statement config plus matrix config and assert scenario families include:

- `relation_kind_matrix`
- `column_type_matrix`
- `data_profile_matrix`
- `schema_mutation_lifecycle`
- `transaction_concurrency_matrix`
- `optimizer_statistics_matrix`
- `negative_control_matrix`

- [ ] **Step 4: Implement `plan_associations`**

Generate scenario families from facts:

- Matrix `coverage_scope.target_relation_coverage` creates relation-kind scenario families.
- Matrix `coverage_scope.column_type_coverage` and type catalog create column-type scenario families.
- Factor profiles tagged `transaction_sensitive` create transaction/concurrency families.
- Factor profiles tagged `optimizer_sensitive` create optimizer/statistics families.
- Factor profiles tagged `dependency_state` or `schema_mutation` create lifecycle mutation families.
- Any `expected_status=failure` factor or negative inventory creates negative-control families.

- [ ] **Step 5: Export public APIs**

Update `src/pg_case_factory/__init__.py` and `src/pg_case_factory/engine.py` so tools can import:

```python
from pg_case_factory import plan_associations, build_factor_profiles, infer_semantic_tags
```

- [ ] **Step 6: Verify Task 1**

Run:

```bash
env PYTHONDONTWRITEBYTECODE=1 python3 -m pytest tests/test_association_planner.py -q -p no:cacheprovider
```

Expected: PASS.

## Task 2: CLI and YAML Report Generation

**Files:**
- Create: `tools/plan_factor_associations.py`
- Test: `tests/test_plan_factor_associations_cli.py`

- [ ] **Step 1: Write failing CLI tests**

Create a temporary mini repository with:

- `skills/pg-sql-generation/references/statements/ddl/example/example_statement.md`
- `skills/pg-sql-generation/references/combinations/ddl/example/example_statement.yaml`
- `skills/pg-sql-generation/references/common/pg16_type_catalog.md`
- `skills/pg-sql-generation/references/combinations/_shared/coverage_inventory.yaml`

Assert the CLI writes:

```text
artifacts/intermediates/example_statement_association_plan.yaml
```

and that the YAML has `kind: factor_association_plan` and at least one `scenario_families` entry.

- [ ] **Step 2: Implement CLI**

CLI options:

```bash
python3 tools/plan_factor_associations.py --root . --statement create_index
python3 tools/plan_factor_associations.py --root . --matrix skills/pg-sql-generation/references/combinations/ddl/index/create_index.yaml
python3 tools/plan_factor_associations.py --root . --statement create_index --output artifacts/intermediates/create_index_association_plan.yaml
```

Behavior:

- Resolve statement by key from statement references.
- Resolve matching matrix by statement key when available.
- Load type catalog and coverage inventory if present.
- Write YAML to `artifacts/intermediates/<statement_key>_association_plan.yaml`.
- Print `PASS factor association plan: statement=<key> families=<n> obligations=<n>`.

- [ ] **Step 3: Verify Task 2**

Run:

```bash
env PYTHONDONTWRITEBYTECODE=1 python3 -m pytest tests/test_plan_factor_associations_cli.py -q -p no:cacheprovider
```

Expected: PASS.

## Task 3: Policy Reference and Complete Map

**Files:**
- Create: `skills/pg-sql-generation/references/common/association_policy.md`
- Create: `docs/factor_association_planner_map.md`

- [ ] **Step 1: Add association policy reference**

Document:

- Planner reads existing facts first.
- Deterministic rules create stable scenario families.
- LLM-suggested ideas are allowed only as marked derived extensions.
- Every scenario family must have trigger facts, generated lifecycle, oracle, cleanup, and coverage tags.
- Derived extensions do not count toward required baseline matrix coverage unless manually promoted.

- [ ] **Step 2: Add project版图**

Include:

- Inputs map.
- Pipeline stages.
- Association operators.
- Scenario-family output schema.
- Quality gates.
- How this fits current statement references and combination matrices.
- CREATE INDEX as one example, but not as the implementation boundary.

- [ ] **Step 3: Verify docs are referenced by README**

Add a short README pointer to `docs/factor_association_planner_map.md` and `association_policy.md`.

## Integration Task

**Files:**
- All files above.

- [ ] **Step 1: Run focused tests**

```bash
env PYTHONDONTWRITEBYTECODE=1 python3 -m pytest tests/test_association_planner.py tests/test_plan_factor_associations_cli.py -q -p no:cacheprovider
```

- [ ] **Step 2: Run existing audits**

```bash
env PYTHONDONTWRITEBYTECODE=1 python3 tools/audit_combination_matrix.py --root .
env PYTHONDONTWRITEBYTECODE=1 python3 tools/audit_factor_catalog_mapping.py --root .
```

- [ ] **Step 3: Run full tests**

```bash
env PYTHONDONTWRITEBYTECODE=1 python3 -m pytest -q -p no:cacheprovider
```

- [ ] **Step 4: Generate a real CREATE INDEX association plan**

```bash
env PYTHONDONTWRITEBYTECODE=1 python3 tools/plan_factor_associations.py --root . --statement create_index
```

Expected: PASS with nonzero families and obligations.

- [ ] **Step 5: Review generated YAML**

Confirm it includes generic families beyond CREATE INDEX hardcoding, including relation, column type, data profile, lifecycle mutation, transaction/concurrency, optimizer/statistics, and negative control families when the source facts support them.
