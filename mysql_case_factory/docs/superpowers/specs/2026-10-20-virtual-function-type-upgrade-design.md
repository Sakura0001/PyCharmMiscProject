# Virtual/function type-upgrade design

## Goal

Verify that base-column type expansion does not corrupt data or change algorithm
behavior when the base column is referenced by a virtual generated column, a
stored generated column, or a functional index.

## Scope

- Reuse the 107 existing type transitions.
- Dependency modes:
  - `none`
  - `virtual_generated`
  - `stored_generated`
  - `functional_index`
- Algorithms:
  - `COPY`
  - `INPLACE`
  - `INSTANT`
- Data states:
  - `normal`
  - `boundary`
- Nullability:
  - `nullable`
  - `not_null`
- Scenario count: `107 × 4 × 3 × 2 × 2 = 5,136`.
- Sequential DML only; concurrency is out of scope for this batch.

## Oracle

Each scenario creates:

1. a control table without dependencies;
2. a candidate table with the selected dependency;
3. a reference table created directly in the target type.

The control table determines the expected DDL outcome for the selected
algorithm. The candidate must match that outcome. If the candidate DDL succeeds,
candidate data, generated-column values, and functional-index query results must
match the reference table. If the candidate DDL fails, the candidate must remain
unchanged.

## Deliverables

- `src/mysql_case_factory/virtual_function_type_upgrade.py`
- `src/mysql_case_factory/virtual_function_type_upgrade_runner.py`
- `src/mysql_case_factory/virtual_function_type_upgrade_audit.py`
- `tools/generate_virtual_function_type_upgrade.py`
- `tools/run_virtual_function_type_upgrade.py`
- `tools/audit_virtual_function_type_upgrade.py`
- `tests/test_virtual_function_type_upgrade.py`
- `tests/test_virtual_function_type_upgrade_runner.py`
- `tests/test_virtual_function_type_upgrade_audit.py`
- `generated/virtual_function_type_upgrade_v1/`
- `docs/virtual_function_type_upgrade_v1.md`
