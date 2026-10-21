# Virtual/function type-upgrade batch

## Objective

This batch verifies that base-column type expansion does not corrupt data or
change algorithm behavior when the base column is referenced by:

1. a `VIRTUAL` generated column;
2. a `STORED` generated column;
3. a functional index.

The core invariant is:

```text
A dependency on the base column must not change the DDL outcome.
If the DDL succeeds, candidate data must match a direct target-type reference.
If the DDL fails, candidate data must remain unchanged.
No crash, assertion, MySQL 2013/2006, or lost connection is allowed.
```

## Batch identity

- **BATCH_ID:** `2026-10-20-virtual-function-type-upgrade-v1`
- **BATCH_KIND:** `virtual_function_type_upgrade`
- **CASE_PREFIX:** `TUCVF`
- **Database:** `qa_virtual_function_type_upgrade`
- **Cases:** 5,136
- **Transitions:** 107
- **Dependency modes:** 4
- **Profiles:** `copy`, `inplace`, `instant`
- **Smoke cases:** 84

## Scenario matrix

```text
107 type transitions
× 4 dependency modes
× 3 profiles
× 2 data states
× 2 nullability states
= 5,136 scenarios
```

### Dependency modes

1. `none`
2. `virtual_generated`
3. `stored_generated`
4. `functional_index`

### Data states

- `normal`
- `boundary`

### Nullability states

- `nullable`
- `not_null`

## Type coverage

The batch reuses the existing 107 type transitions:

- Integer
- DECIMAL
- BIT
- CHAR / VARCHAR
- BINARY / VARBINARY
- TEXT
- BLOB

Temporal, JSON, spatial, vector, ENUM/SET, and floating-point types remain
excluded.

## Oracle design

Each scenario creates three tables:

1. **control:** source type, no dependency
2. **candidate:** source type, selected dependency
3. **reference:** direct target type, selected dependency

The control table determines the expected DDL result for the selected
algorithm. The candidate must match that result.

If the candidate DDL succeeds:

1. insert additional target-boundary rows;
2. update rows;
3. delete rows;
4. reinsert rows;
5. compare candidate and reference rows;
6. compare generated-column or functional-expression values.

If the candidate DDL fails:

1. compare candidate rows before and after DDL;
2. compare the base-column type before and after DDL.

## Local evidence

Local MySQL 8.0.45 evidence:

```text
COPY:    1,712 / 1,712 PASS
INPLACE: 1,712 / 1,712 PASS
INSTANT: 1,712 / 1,712 PASS
```

Evidence files:

```text
generated/virtual_function_type_upgrade_v1/copy_results.jsonl
generated/virtual_function_type_upgrade_v1/copy_summary.json
generated/virtual_function_type_upgrade_v1/inplace_results.jsonl
generated/virtual_function_type_upgrade_v1/inplace_summary.json
generated/virtual_function_type_upgrade_v1/instant_results.jsonl
generated/virtual_function_type_upgrade_v1/instant_summary.json
```

## Execution

Run one profile:

```bash
export VIRTUAL_FUNCTION_MYSQL_PASSWORD='...'

PYTHONPATH=src python3 tools/run_virtual_function_type_upgrade.py \
  --profile copy \
  --all \
  --results generated/virtual_function_type_upgrade_v1/copy_results.jsonl \
  --summary generated/virtual_function_type_upgrade_v1/copy_summary.json \
  --external \
  --host <authorized-host> \
  --port 3306 \
  --user <authorized-user> \
  --password-env VIRTUAL_FUNCTION_MYSQL_PASSWORD
```

Repeat with `--profile inplace` and `--profile instant`.

Run the 84-case smoke matrix:

```bash
PYTHONPATH=src python3 tools/run_virtual_function_type_upgrade.py \
  --profile copy \
  --smoke \
  --results generated/virtual_function_type_upgrade_v1/smoke_results.jsonl \
  --summary generated/virtual_function_type_upgrade_v1/smoke_summary.json \
  --external \
  --host <authorized-host> \
  --port 3306 \
  --user <authorized-user> \
  --password-env VIRTUAL_FUNCTION_MYSQL_PASSWORD
```

Repeat the smoke matrix with `--profile inplace` and `--profile instant`.

## Audit

```bash
PYTHONPATH=src python3 tools/audit_virtual_function_type_upgrade.py \
  --virtual-function generated/virtual_function_type_upgrade_v1
```

The audit validates:

- 5,136 cases;
- 107 transitions;
- 4 dependency modes;
- 3 profiles;
- deterministic artifact hashes;
- complete local evidence for all three profiles.
