# Type-upgrade statistics and chain batch

BATCH_ID: 2026-10-14-type-upgrade-statistics-and-chain-v1
BATCH_KIND: STATISTICS_AND_CHAIN_EXTENSION
PARENT_BATCH_ID: 2026-10-13-type-upgrade-consistency-extension-v1
CASE_COUNT: 47
CASE_PREFIX: TUCS

This batch is independent from `TUC` and `TUCX`. It verifies optimizer statistics and chained type upgrades.

## Internal AI execution instructions

1. Verify `manifest.json` first.
2. Execute only `TUCS-` cases carrying this batch ID.
3. Do not mix results with `TUC-` or `TUCX-` cases.
4. Run `INPLACE` and `INSTANT` separately in an isolated QA schema.
5. `COPY` is only the local MySQL 8.0.45 oracle and is not internal PASS evidence.
6. Use `mysql --force`; negative duplicate-MODIFY cases intentionally return SQL errors.
7. A crash, assertion, signal, or MySQL 2013 is `FAIL_CRASH`, never an expected negative result.
8. On failure, report batch ID, profile, case ID, gap ID, SQL, error, and terminal state.
