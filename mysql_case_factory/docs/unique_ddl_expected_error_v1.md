# Unique-DDL expected-error batch

## Objective

This batch verifies that online unique secondary-index DDL fails when concurrent DML introduces a duplicate after the DDL has started on a table that initially has no duplicates.

The core invariant is:

```text
The base table has no duplicates under the new unique-index semantics.
Duplicate-producing DML overlaps and completes before the DDL completes.
The DML succeeds.
The DDL fails with MySQL 1062 or 1859.
No crash, assertion, MySQL 2013/2006, or lost connection occurs.
```

## Batch identity

- **BATCH_ID:** `2026-10-20-unique-ddl-expected-error-v1`
- **BATCH_KIND:** `unique_ddl_expected_error`
- **CASE_PREFIX:** `TUCUD`
- **Database:** `qa_unique_ddl_expected_error`
- **Profile:** `inplace`
- **Cases:** 192
- **DDL forms:** 4
- **Index shapes:** 6
- **DML types:** 8
- **Rows per shape:** 200,000
- **Materialization:** virtual runner

## Scenario matrix

```text
4 DDL forms
× 6 index shapes
× 8 duplicate-producing DML types
= 192 scenarios
```

### DDL forms

1. `CREATE UNIQUE INDEX`
2. `ALTER TABLE ADD UNIQUE INDEX`
3. `ALTER TABLE ADD UNIQUE KEY`
4. `ALTER TABLE ADD CONSTRAINT ... UNIQUE`

`CREATE UNIQUE INDEX` uses `ALGORITHM=INPLACE` but does not accept a `LOCK` clause.
The three `ALTER TABLE` forms use `ALGORITHM=INPLACE, LOCK=NONE`.

### Index shapes

| Shape | Conflict semantics |
| --- | --- |
| `integer` | Exact duplicate integer |
| `string` | Exact duplicate binary string |
| `prefix` | Different full strings share the indexed prefix |
| `case_insensitive` | Different case maps to the same collation key |
| `generated` | Different source strings map to the same `LOWER(v)` value |
| `composite` | Duplicate `(a,b)` tuple |

### Duplicate-producing DML

1. `INSERT`
2. `INSERT IGNORE`
3. `INSERT ... ON DUPLICATE KEY UPDATE`
4. `INSERT ... SELECT`
5. Multi-row `INSERT`
6. `UPDATE`
7. `UPDATE ... JOIN`
8. `DELETE` + `INSERT`

`REPLACE` is intentionally excluded because it replaces an existing row and does not create a duplicate.

## Expected result

The DDL must fail with one of:

- MySQL `1062`: `Duplicate entry`
- MySQL `1859`: `Duplicate entry for key` during online DDL replay

Both codes are accepted because MySQL may report either code depending on whether the duplicate is detected with a concrete key value or during online-DDL index replay.

If the DDL succeeds, the case is `FAIL_DDL_SUCCESS`.

If the DML completes only after the DDL has already completed, the case is `NO_OVERLAP` and must be rerun with more rows or a smaller `--dml-delay`.

## Local evidence

Local MySQL 8.0.45 evidence:

```text
192 / 192 scenarios PASS
192 / 192 true overlaps
192 / 192 duplicate DDL errors
Rows per shape: 200,000
```

Evidence files:

```text
generated/unique_ddl_expected_error_v1/local_results.jsonl
generated/unique_ddl_expected_error_v1/local_summary.json
generated/unique_ddl_expected_error_v1/local_summary.md
```

## Execution

Run the complete matrix:

```bash
export UNIQUE_DDL_MYSQL_PASSWORD='...'

PYTHONPATH=src python3 tools/run_unique_ddl_expected_error.py \
  --all \
  --results generated/unique_ddl_expected_error_v1/inplace_results.jsonl \
  --summary generated/unique_ddl_expected_error_v1/inplace_summary.json \
  --external \
  --host <authorized-host> \
  --port 3306 \
  --user <authorized-user> \
  --password-env UNIQUE_DDL_MYSQL_PASSWORD
```

Run the six shape representatives:

```bash
PYTHONPATH=src python3 tools/run_unique_ddl_expected_error.py \
  --smoke \
  --results generated/unique_ddl_expected_error_v1/smoke_results.jsonl \
  --summary generated/unique_ddl_expected_error_v1/smoke_summary.json \
  --external \
  --host <authorized-host> \
  --port 3306 \
  --user <authorized-user> \
  --password-env UNIQUE_DDL_MYSQL_PASSWORD
```

Single-case debugging:

```bash
PYTHONPATH=src python3 tools/run_unique_ddl_expected_error.py \
  --case-id TUCUD-000001 \
  --results /tmp/tucud-case.jsonl \
  --summary /tmp/tucud-case.json \
  --external \
  --host <authorized-host> \
  --port 3306 \
  --user <authorized-user> \
  --password-env UNIQUE_DDL_MYSQL_PASSWORD
```

If any result is `NO_OVERLAP`, increase `--rows` or decrease `--dml-delay`.

## Audit

```bash
PYTHONPATH=src python3 tools/audit_unique_ddl_expected_error.py \
  --unique-ddl generated/unique_ddl_expected_error_v1
```

Use `--skip-local` for structural validation only.
