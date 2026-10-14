# Type-upgrade statistics and chain design

## Goal

Add an independent `TUCS` batch that verifies optimizer statistics after type
upgrades and covers consecutive type upgrades in one test case. The existing
verified `TUC` and `TUCX` batches remain immutable.

## Batch identity

```text
BATCH_ID:        2026-10-14-type-upgrade-statistics-and-chain-v1
BATCH_KIND:      statistics_and_chain_extension
PARENT_BATCH_ID: 2026-10-13-type-upgrade-consistency-extension-v1
CASE_PREFIX:     TUCS
```

## Statistics scope

The batch reads and validates, but never directly updates, these interfaces:

- `mysql.innodb_table_stats`
- `mysql.innodb_index_stats`
- `information_schema.STATISTICS`
- `information_schema.TABLES`
- `information_schema.PARTITIONS`
- `EXPLAIN FORMAT=JSON`

`ANALYZE TABLE` is used to force statistics recalculation. The suite does not
write to MySQL system statistics tables.

## Statistics oracle rules

Statistics are estimates, so raw cardinality, row-count, and cost values are
not compared exactly across algorithms. The suite instead checks:

1. Persistent table statistics exist.
2. Persistent index statistics exist for every expected index.
3. `stat_name`, index names, and key-part descriptions are structurally valid.
4. Values are non-negative and non-null where required.
5. Non-empty tables have positive `n_rows` and indexed columns have cardinality.
6. Tables with secondary indexes have positive `sum_of_other_index_sizes`.
7. `ANALYZE TABLE` succeeds and persistent statistics remain present and valid.
8. `EXPLAIN FORMAT=JSON` uses the expected index and reports positive row
   estimates.
9. Partitioned tables have statistics coverage for the table and its partitions.

## Statistics phases

Each representative case checks:

1. Post-DDL state before explicit analysis.
2. `ANALYZE TABLE` result.
3. Post-analysis persistent and information-schema statistics.
4. Post-DDL new-range data followed by another analysis where applicable.

## Consecutive upgrade scope

MySQL rejects multiple `MODIFY` clauses for the same column in one `ALTER`
statement. Therefore the suite covers two distinct cases:

1. **Chained success case:** one test case executes two consecutive ALTER
   statements, for example `SMALLINT -> INT` and then `INT -> BIGINT`. Both
   statements must succeed, and the final schema, data, indexes, statistics,
   and query plan must match the direct `SMALLINT -> BIGINT` reference.
2. **Duplicate-column negative case:** one ALTER statement contains two
   `MODIFY target_col ...` clauses. It must reject atomically and leave the
   original schema and data unchanged.

## Acceptance criteria

1. Every generated case uses the `TUCS-` prefix and the new batch identity.
2. `TUC` and `TUCX` artifacts remain unchanged.
3. Statistics coverage includes persistent table/index stats, information
   schema, EXPLAIN, and partition stats.
4. Consecutive `SMALLINT -> INT -> BIGINT` is covered as one case.
5. Duplicate `MODIFY` in one ALTER is covered as a negative case.
6. Local MySQL 8.0.45 `COPY` runs every generated case and all pass.
7. `COPY`, `INPLACE`, and `INSTANT` suites have identical case sequences.
8. Project tests pass.
9. Documentation and internal-AI instructions distinguish `TUC`, `TUCX`, and
   `TUCS`.
