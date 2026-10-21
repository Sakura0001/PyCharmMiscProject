# Type-upgrade performance batch

## Objective

Measure large-table type-upgrade performance and post-upgrade query/DML
performance across every SQL-direct upgradeable type family.

The batch compares:

1. source-table baseline performance;
2. direct target-type reference-table performance;
3. `COPY` upgrade performance;
4. `INPLACE` upgrade performance;
5. `INSTANT` upgrade performance;
6. mixed `INPLACE` / `INSTANT` upgrade performance.

## Batch identity

- **BATCH_ID:** `2026-10-21-type-upgrade-performance-v1`
- **BATCH_KIND:** `type_upgrade_performance`
- **CASE_PREFIX:** `TUCPF`
- **Database:** `qa_type_upgrade_performance`
- **Scenarios:** 7
- **Upgrade columns:** 31
- **Noise columns:** 4
- **Profile:** `performance`

## Scenarios

1. `source_baseline`
2. `all_copy`
3. `all_inplace`
4. `all_instant`
5. `mixed_inplace_first`
6. `mixed_instant_first`
7. `reference`

`all_copy` is retained as a local-oracle and performance baseline. The internal
build is expected to support the `INPLACE`, `INSTANT`, and mixed scenarios.

## Type coverage

| Family | Coverage |
| --- | --- |
| Integer | All signed and unsigned integer families, including `BIGINT` controls |
| DECIMAL | Scales 2, 6, and 18 with precision expansion |
| BIT | `BIT(8)`, `BIT(32)` |
| Character | `CHAR`/`VARCHAR`, including 255-to-256 crossings |
| Binary | `BINARY`/`VARBINARY`, including 255-to-256 crossings |
| TEXT | `TINYTEXT`, `TEXT`, `MEDIUMTEXT` |
| BLOB | `TINYBLOB`, `BLOB`, `MEDIUMBLOB` |

Noise columns:

- `FLOAT`
- `DOUBLE`
- `DATE`
- `JSON`

## Data volume

The runner supports two modes.

### Fixed rows

```bash
--rows 12000000
```

### Adaptive calibration

```bash
--rows 0
--calibration-rows 100000
--target-scan-seconds 300
--max-rows 20000000
```

Adaptive mode:

1. creates a 100,000-row calibration table;
2. executes the full-scan aggregate query;
3. estimates the row count needed to reach 300 seconds;
4. caps the estimate at `--max-rows`;
5. recreates the source and reference tables at the estimated row count.

## Timing standard

Every full-scan measurement records:

1. client wall time using a high-resolution timer;
2. `EXPLAIN ANALYZE` output;
3. aggregate values used for candidate/reference comparison.

DDL timing records:

- total DDL duration;
- per-scenario statement count;
- DDL success;
- DDL error.

DML timing records:

- insert duration;
- update duration;
- delete duration;
- reinsert duration.

## Local evidence

Local MySQL 8.0.45 smoke evidence uses:

```text
source_baseline
all_copy
reference
```

Result:

```text
3 / 3 PASS
```

The local Oracle does not support the internal `INPLACE` / `INSTANT`
type-upgrade optimizations, so those scenarios are reserved for the internal
performance run.

## Execution

Run all seven scenarios:

```bash
export TYPE_PERFORMANCE_MYSQL_PASSWORD='...'

PYTHONPATH=src python3 tools/run_type_upgrade_performance.py \
  --all \
  --results generated/type_upgrade_performance_v1/performance_results.jsonl \
  --summary generated/type_upgrade_performance_v1/performance_summary.json \
  --external \
  --host <authorized-host> \
  --port 3306 \
  --user <authorized-user> \
  --password-env TYPE_PERFORMANCE_MYSQL_PASSWORD
```

Use adaptive row-count calibration:

```bash
PYTHONPATH=src python3 tools/run_type_upgrade_performance.py \
  --all \
  --rows 0 \
  --calibration-rows 100000 \
  --target-scan-seconds 300 \
  --max-rows 20000000 \
  --results generated/type_upgrade_performance_v1/performance_results.jsonl \
  --summary generated/type_upgrade_performance_v1/performance_summary.json \
  --external \
  --host <authorized-host> \
  --port 3306 \
  --user <authorized-user> \
  --password-env TYPE_PERFORMANCE_MYSQL_PASSWORD
```

Run selected scenarios:

```bash
PYTHONPATH=src python3 tools/run_type_upgrade_performance.py \
  --scenario all_inplace \
  --scenario all_instant \
  --scenario mixed_inplace_first \
  --scenario mixed_instant_first \
  --results generated/type_upgrade_performance_v1/internal_results.jsonl \
  --summary generated/type_upgrade_performance_v1/internal_summary.json \
  --external \
  --host <authorized-host> \
  --port 3306 \
  --user <authorized-user> \
  --password-env TYPE_PERFORMANCE_MYSQL_PASSWORD
```

## Audit

```bash
PYTHONPATH=src python3 tools/audit_type_upgrade_performance.py \
  --performance generated/type_upgrade_performance_v1
```

The local audit validates the complete seven-scenario structure and the
three-scenario local smoke evidence.
