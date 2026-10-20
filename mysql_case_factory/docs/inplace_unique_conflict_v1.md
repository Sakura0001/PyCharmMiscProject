# INPLACE DDL unique-conflict batch

## Objective

This batch verifies that MySQL DDL operations which support
`ALGORITHM=INPLACE, LOCK=NONE` are not interrupted or corrupted by concurrent
DML that continuously hits a unique-key conflict.

The invariant under test is:

```text
A concurrent duplicate INSERT may fail with error 1062.
The DDL must still succeed.
No committed row may be lost, duplicated, or changed.
No uncommitted or failed row may remain.
AUTO_INCREMENT must not regress.
The final schema must match the operation.
```

This batch deliberately excludes `MODIFY` and `CHANGE` because the internal
build explicitly does not support the unique-key conflict optimization for
those forms.

## Scope

The batch contains 12 non-`MODIFY` operations that were verified to support
`ALGORITHM=INPLACE, LOCK=NONE` on MySQL 8.0.45:

1. `ADD INDEX`
2. `DROP INDEX`
3. `ADD UNIQUE`
4. `DROP UNIQUE`
5. `RENAME INDEX`
6. `ADD COLUMN`
7. `DROP COLUMN`
8. `RENAME COLUMN`
9. `ADD FOREIGN KEY`
10. `DROP FOREIGN KEY`
11. `DROP CHECK`
12. `DROP GENERATED COLUMN`

The complete virtual matrix is:

```text
12 operations
x 4 conflict surfaces
x 4 conflict patterns
x 3 phases
x 2 worker counts
x 2 data states
= 2,304 scenarios
```

## Factors

### Conflict surfaces

- `existing_unique`
- `new_unique`
- `composite_unique`
- `nullable_unique`

The DDL target is independent from the conflict surface. This prevents an
`ADD UNIQUE` or `DROP UNIQUE` operation from being logically impossible merely
because the concurrent DML is hitting that same key.

### Conflict patterns

- `seed_duplicate`
- `concurrent_duplicate`
- `semantic_collision`
- `boundary_duplicate`

`semantic_collision` uses case-insensitive string values under
`utf8mb4_0900_ai_ci`, such as `Tucui-Semantic-Value` versus
`TUCUI-SEMANTIC-VALUE`. `boundary_duplicate` uses the zero-length string as the
string boundary.

### Concurrency phases

- `during_ddl`
- `before_and_during_ddl`
- `across_ddl_transaction`

### Worker counts

- 4 workers
- 16 workers

### Data states

- `normal`
- `boundary`

## Runner design

Each scenario:

1. Creates a unique run database, parent table, and target table.
2. Seeds deterministic normal or boundary rows.
3. Inserts one committed base row.
4. Starts the configured number of worker connections.
5. Each worker repeatedly attempts to insert a duplicate of the base row in a
   short transaction.
6. The DDL connection starts only after every worker has completed at least one
   duplicate attempt and has an open transaction.
7. The DDL runs with the selected profile:
   - `COPY`: `ALGORITHM=COPY, LOCK=SHARED`
   - `INPLACE`: `ALGORITHM=INPLACE, LOCK=NONE`
   - `INSTANT`: `ALGORITHM=INSTANT`
8. The runner records real DDL/DML time overlap.
9. A post-DDL row is inserted.
10. The runner validates row count, all stable columns, duplicate conflict
    count, AUTO_INCREMENT, and the operation-specific final schema.
11. The run database is removed.

The result classifier is:

- `PASS`
- `EXPECTED_REJECT`
- `FAIL_DDL`
- `FAIL_VALIDATION`
- `FAIL_CRASH`
- `NO_OVERLAP`

For `INSTANT`, only these operations are expected to succeed:

- `add_column`
- `drop_column`
- `rename_column`
- `drop_check`
- `drop_generated`

The remaining seven operations are expected rejects under `INSTANT`.

## Local evidence

The checked-in local evidence uses the conservative `COPY` profile on MySQL
8.0.45:

```text
12 / 12 smoke scenarios PASS
12 / 12 true DDL/DML overlaps
12 / 12 duplicate-conflict observations
```

The artifacts are:

```text
generated/inplace_unique_conflict_v1/local_results.jsonl
generated/inplace_unique_conflict_v1/local_summary.json
generated/inplace_unique_conflict_v1/local_summary.md
```

The same MySQL 8.0.45 `INSTANT` smoke run produced:

```text
5 PASS
7 EXPECTED_REJECT
```

Native MySQL 8.0.45 also exposed three `INPLACE` smoke failures when duplicate
DML remained active:

- `add_column`
- `drop_column`
- `drop_generated`

All three failed with error 1062 while replaying concurrent DML, for example:

```text
Duplicate entry 'TUCUI-SEED-000129' for key '<table>.uk_tucui_existing_unique'
```

This is exactly the class of interruption this batch is designed to detect. It
is recorded as product behavior, not hidden as a runner failure.

## Execution

Use an authorized MySQL server and do not place the password on the command
line:

```bash
export TUCUI_MYSQL_PASSWORD='...'

PYTHONPATH=src python3 tools/run_inplace_unique_conflict.py \
  --profile copy \
  --smoke \
  --results regression_results/TUCUI/copy.jsonl \
  --summary regression_results/TUCUI/copy.json \
  --external \
  --host <authorized-host> \
  --port 3306 \
  --user <authorized-user> \
  --password-env TUCUI_MYSQL_PASSWORD
```

Repeat with `--profile inplace` and `--profile instant`.

For the complete virtual matrix:

```bash
PYTHONPATH=src python3 tools/run_inplace_unique_conflict.py \
  --profile inplace \
  --all \
  --results regression_results/TUCUI/inplace.jsonl \
  --summary regression_results/TUCUI/inplace.json \
  --external \
  --host <authorized-host> \
  --port 3306 \
  --user <authorized-user> \
  --password-env TUCUI_MYSQL_PASSWORD
```

Single-case debugging:

```bash
PYTHONPATH=src python3 tools/run_inplace_unique_conflict.py \
  --profile inplace \
  --case-id TUCUI-000961 \
  --results regression_results/TUCUI/TUCUI-000961.jsonl \
  --summary regression_results/TUCUI/TUCUI-000961.json \
  --external \
  --host <authorized-host> \
  --port 3306 \
  --user <authorized-user> \
  --password-env TUCUI_MYSQL_PASSWORD
```

The runner creates and removes a unique database for each case.

Optional tuning:

- `--filler-rows` controls the seeded row count; the default is 128.
- `--hold-seconds` controls how long each worker transaction stays open; the
  default is 1 second.
- `--max-attempts` bounds duplicate attempts per worker; the default is 10000.

## Audit

```bash
PYTHONPATH=src python3 tools/audit_inplace_unique_conflict.py \
  --inplace-unique generated/inplace_unique_conflict_v1
```

Use `--skip-local` for a structural-only audit.
