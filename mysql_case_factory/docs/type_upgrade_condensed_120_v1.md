# Type-upgrade condensed 120 SQL batch

## Objective

This batch contains exactly 120 individual SQL regress files. Each file covers
both `INPLACE` and `INSTANT` in the same SQL stream and compares each upgraded
candidate table with a directly created target-type reference table.

The core invariant is:

```text
For every case:
  INPLACE candidate data == direct target reference data
  INSTANT candidate data == direct target reference data
  candidate schema == reference schema
  row count == reference row count
  no large business-row output
  repeated execution output is stable
```

## Batch identity

- **BATCH_ID:** `2026-10-27-type-upgrade-condensed-120-v1`
- **BATCH_KIND:** `type_upgrade_condensed_sql`
- **CASE_PREFIX:** `TUCR`
- **Database:** `qa_type_upgrade_condensed_120`
- **SQL files:** 120
- **Expected output lines:** 240
- **Algorithms per file:** `INPLACE`, `INSTANT`
- **Materialization:** SQL directory

## Per-file structure

Every `TUCR-000NNN.sql` file contains:

1. pre-cleanup;
2. source-type `INPLACE` candidate;
3. source-type `INSTANT` candidate;
4. direct target-type reference table;
5. deterministic seed rows;
6. one reference DML sequence;
7. `INPLACE` DDL;
8. identical candidate DML;
9. `INPLACE` result row;
10. `INSTANT` DDL;
11. identical candidate DML;
12. `INSTANT` result row;
13. final cleanup.

Foreign-key cases also create parent candidates and parent references and
upgrade both parent and child columns with the same algorithm.

## Deterministic DML

The batch does not perform full-table UPDATE or DELETE. It uses fixed
representative IDs:

```text
UPDATE id IN (1, 3, 5)
DELETE id IN (2, 4)
fixed reinsert id = 8
```

The three tables execute the same deterministic DML. Candidate and reference
are then compared with NULL-safe, bidirectional all-column checks.

## Stable output

Each file outputs exactly two rows:

```text
TUCR-000001  INPLACE  0  0  0  0  PASS
TUCR-000001  INSTANT  0  0  0  0  PASS
```

Fields:

```text
case_id
algorithm
schema_diff_count
row_count_diff
mismatch_count
reference_extra_count
result
```

No business rows, cardinalities, costs, execution times, or unstable statistics
are printed.

## Coverage

| Category | Cases |
| --- | ---: |
| Integer | 16 |
| DECIMAL | 10 |
| BIT | 10 |
| Character | 12 |
| Binary | 12 |
| TEXT/BLOB | 8 |
| Zero-length and cross-family | 10 |
| AUTO_INCREMENT primary key | 6 |
| Foreign key | 8 |
| Dependencies and generated/function objects | 8 |
| Table form / row format / partition / engine | 10 |
| Chain, multi-column, statistics metadata | 10 |
| **Total** | **120** |

Special boundaries include:

- `CHAR(0)`
- `VARCHAR(0)`
- `BINARY(0)`
- `VARBINARY(0)`
- `CHAR(255) -> VARCHAR(256)`
- `BINARY(255) -> VARBINARY(256)`
- `DECIMAL(65,30)`
- `BIT(63) -> BIT(64)`
- `VARCHAR(16307) -> TEXT`
- `VARBINARY(65231) -> BLOB`

## Local evidence

Native MySQL 8.0.45 COPY was used to validate the 112 non-FK SQL files:

```text
224 / 224 result rows PASS
stderr = 0 lines
```

The eight FK cases are reserved for the internal run because native MySQL COPY
cannot alter columns used by foreign keys. They remain valid internal
`INPLACE` / `INSTANT` cases.

Evidence:

```text
generated/type_upgrade_condensed_120_v1/local_copy_results.tsv
generated/type_upgrade_condensed_120_v1/local_copy_summary.json
generated/type_upgrade_condensed_120_v1/local_copy_summary.md
```

## Execution

Create the database:

```bash
mysql --login-path=internal_qa \
  -e "DROP DATABASE IF EXISTS qa_type_upgrade_condensed_120; CREATE DATABASE qa_type_upgrade_condensed_120 CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci"
```

Run one file:

```bash
mysql --login-path=internal_qa \
  --batch --raw --skip-column-names --binary-mode --force \
  qa_type_upgrade_condensed_120 \
  < generated/type_upgrade_condensed_120_v1/sql/TUCR-000001.sql
```

Run all files:

```bash
for file in generated/type_upgrade_condensed_120_v1/sql/*.sql; do
  mysql --login-path=internal_qa \
    --batch --raw --skip-column-names --binary-mode --force \
    qa_type_upgrade_condensed_120 \
    < "$file"
done > generated/type_upgrade_condensed_120_v1/actual_output.tsv
```

Compare:

```bash
diff -u generated/type_upgrade_condensed_120_v1/expected_output.tsv \
  generated/type_upgrade_condensed_120_v1/actual_output.tsv
```

Use `--force` so the second algorithm and data comparison still execute if the
first algorithm rejects.

## Audit

```bash
PYTHONPATH=src python3 tools/audit_type_upgrade_condensed_120.py \
  --condensed generated/type_upgrade_condensed_120_v1
```
