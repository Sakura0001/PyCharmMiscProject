# Type-upgrade statistics and chain v1

This is the third independent batch. It extends the verified `TUCX` batch with
optimizer-statistics coverage and consecutive type upgrades.

## Batch identity

```text
BATCH_ID:        2026-10-14-type-upgrade-statistics-and-chain-v1
BATCH_KIND:      statistics_and_chain_extension
PARENT_BATCH_ID: 2026-10-13-type-upgrade-consistency-extension-v1
CASE_PREFIX:     TUCS
CASE_COUNT:      47
```

Batch separation:

```text
TUC  = 8,270-case new-merge baseline
TUCX = 13,721-case interaction extension
TUCS = 47-case statistics and chained-upgrade extension
```

## Statistics coverage

The batch reads, but never directly updates:

- `mysql.innodb_table_stats`
- `mysql.innodb_index_stats`
- `information_schema.STATISTICS`
- `information_schema.TABLES`
- `information_schema.PARTITIONS`
- `EXPLAIN FORMAT=JSON`

It explicitly runs:

```sql
ANALYZE TABLE table_name;
```

Statistics are estimates. The suite does not compare raw cardinality, row
counts, or costs exactly across algorithms. It checks:

- Persistent table statistics exist.
- Persistent index statistics exist.
- Values are non-negative.
- Non-empty indexed columns have cardinality.
- Information-schema metadata is valid.
- Partition statistics cover every partition.
- `EXPLAIN` uses the expected index.
- `ANALYZE TABLE` succeeds.
- Statistics remain valid after analysis.

## Consecutive upgrade coverage

A single test case executes two consecutive ALTER statements:

```sql
ALTER TABLE t
  MODIFY target_col INT,
  ALGORITHM=<profile>;

ALTER TABLE t
  MODIFY target_col BIGINT,
  ALGORITHM=<profile>;
```

The final state is compared with a direct `SMALLINT -> BIGINT` reference table.
Statistics and query plans are checked after the full chain.

MySQL does not allow two `MODIFY` clauses for the same column in one ALTER
statement. A separate negative case verifies that this form rejects atomically:

```sql
ALTER TABLE t
  MODIFY target_col INT,
  MODIFY target_col BIGINT,
  ALGORITHM=<profile>;
```

## Local verification

```text
Selected: 47
Executed: 47
PASS:     47
FAIL:     0
Stopped early: false
MySQL version: 8.0.45
```

## Audit

```bash
python3 tools/audit_type_upgrade_statistics.py \
  --parent generated/type_upgrade_consistency_extension_v1 \
  --statistics generated/type_upgrade_statistics_v1 \
  --report-dir generated/type_upgrade_statistics_v1
```

The audit checks all manifest artifacts, all three profile counts, parent
linkage, case-ID uniqueness, local results, and semantic coverage.

## Internal AI execution rules

1. Verify `manifest.json` first.
2. Execute only `TUCS-` cases carrying this batch ID.
3. Do not mix results with `TUC-` or `TUCX-`.
4. Run `INPLACE` and `INSTANT` separately in an isolated QA schema.
5. Local `COPY` is only the MySQL 8.0.45 oracle; it is not internal PASS.
6. Use `mysql --force` because the duplicate-MODIFY case intentionally fails.
7. A crash, assertion, signal, or MySQL 2013 is `FAIL_CRASH`.
8. On failure, report batch ID, profile, case ID, gap ID, SQL, error, and
   terminal state.
