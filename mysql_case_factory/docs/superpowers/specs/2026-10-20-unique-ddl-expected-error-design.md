# Unique-DDL expected-error design

## Goal

Cover online unique-secondary-index DDL statements that must fail when concurrent DML introduces a duplicate key after the DDL has started on a table that initially has no duplicates.

## Scope

- Algorithm: `INPLACE`.
- DDL forms:
  1. `CREATE UNIQUE INDEX`
  2. `ALTER TABLE ADD UNIQUE INDEX`
  3. `ALTER TABLE ADD UNIQUE KEY`
  4. `ALTER TABLE ADD CONSTRAINT ... UNIQUE`
- Index shapes:
  1. single integer
  2. exact string
  3. string prefix
  4. case-insensitive string
  5. generated normalization column
  6. composite key
- Duplicate-producing DML:
  1. `INSERT`
  2. `INSERT IGNORE`
  3. `INSERT ... ON DUPLICATE KEY UPDATE`
  4. `INSERT ... SELECT`
  5. multi-row `INSERT`
  6. `UPDATE`
  7. `UPDATE ... JOIN`
  8. `DELETE` + `INSERT`
- Matrix size: `4 × 6 × 8 = 192` scenarios.
- Expected result: DDL fails with MySQL 1062 while the DML statement succeeds.
- `REPLACE` is intentionally excluded because it replaces an existing row and does not create a duplicate.
- `ADD PRIMARY KEY` is excluded because the requirement is specifically secondary-index DDL.

## Oracle

Each scenario records:

- DDL start/end time
- DML start/end time
- true overlap
- DDL error code
- DML result
- final classification

Classifications:

- `PASS`: overlap exists, DDL fails with 1062, DML succeeds
- `NO_OVERLAP`: DML starts after DDL ends
- `FAIL_DDL_SUCCESS`: DDL unexpectedly succeeds
- `FAIL_DDL_ERROR`: DDL fails with a non-1062 error
- `FAIL_DML`: DML fails while overlap exists
- `FAIL_CRASH`: connection loss or server crash

## Runner

The runner:

1. Creates one large base table per index shape.
2. Seeds deterministic unique values.
3. For each scenario:
   - resets the shape table;
   - starts the DDL on a separate connection;
   - waits a short configurable delay;
   - executes the duplicate-producing DML;
   - waits for DDL completion;
   - validates overlap and outcomes;
   - drops an unexpectedly created unique index;
   - restores the table to its unique baseline.
4. Writes JSONL results and a JSON/Markdown summary.

## Deliverables

- `src/mysql_case_factory/unique_ddl_expected_error.py`
- `src/mysql_case_factory/unique_ddl_expected_error_runner.py`
- `tools/generate_unique_ddl_expected_error.py`
- `tools/run_unique_ddl_expected_error.py`
- `tools/audit_unique_ddl_expected_error.py`
- `tests/test_unique_ddl_expected_error.py`
- `tests/test_unique_ddl_expected_error_runner.py`
- `tests/test_unique_ddl_expected_error_audit.py`
- `generated/unique_ddl_expected_error_v1/`
- `docs/unique_ddl_expected_error_v1.md`
