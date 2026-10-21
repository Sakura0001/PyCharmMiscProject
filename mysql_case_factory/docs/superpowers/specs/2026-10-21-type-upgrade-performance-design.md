# Type-upgrade performance design

## Goal

Measure large-table type-upgrade performance and post-upgrade query/DML
performance for all supported SQL-direct upgradeable type families.

## Scope

- One wide source table containing all upgradeable source types and four noise
  types.
- One reference table created directly in all target types.
- One candidate table reused across DDL scenarios.
- Scenarios:
  1. `source_baseline`
  2. `all_inplace`
  3. `all_instant`
  4. `mixed_inplace_first`
  5. `mixed_instant_first`
  6. `reference`
- Adaptive row-count calibration targeting a full-scan time of 300 seconds.
- Extreme and boundary data for every upgradeable type.
- Standardized timing using client wall time and `EXPLAIN ANALYZE`.
- DML benchmark after each successful DDL scenario.

## Data volume

- Default calibration row count: 100,000.
- Default target full-scan time: 300 seconds.
- Default maximum rows: 20,000,000.
- The runner estimates the final row count from the calibration scan and caps
  it at the configured maximum.

## Deliverables

- `src/mysql_case_factory/type_upgrade_performance.py`
- `src/mysql_case_factory/type_upgrade_performance_runner.py`
- `src/mysql_case_factory/type_upgrade_performance_audit.py`
- `tools/generate_type_upgrade_performance.py`
- `tools/run_type_upgrade_performance.py`
- `tools/audit_type_upgrade_performance.py`
- `tests/test_type_upgrade_performance.py`
- `tests/test_type_upgrade_performance_runner.py`
- `tests/test_type_upgrade_performance_audit.py`
- `generated/type_upgrade_performance_v1/`
- `docs/type_upgrade_performance_v1.md`
