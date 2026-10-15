# MySQL type-upgrade boundary extension

This is an independent `TUCZ` boundary batch. It complements, and does not replace, `TUC`, `TUCX`, `TUCS`, and `TUCP`.

- **BATCH_ID:** `2026-10-15-type-upgrade-boundary-v1`
- **BATCH_KIND:** `boundary_extension`
- **PARENT_BATCH_ID:** `2026-10-15-type-upgrade-pipeline-v1`
- **CASE_PREFIX:** `TUCZ`
- **CASE_COUNT:** 750
- **Profiles:** `copy`, `inplace`, `instant`
- **SQL files:** 2,250 (750 per profile)
- **Expected output lines:** 2,458
- **Fixed QA database:** `qa_type_upgrade_boundary`
- **Local MySQL 8.0.45 COPY:** 750/750 scenarios PASS; combined-stream output and final cleanup PASS

## Two-stage data-integrity oracle

Every case performs two explicit upgrades:

1. Seed 24 rows in the source type.
2. Upgrade source type to intermediate type.
3. Insert 24 intermediate target-boundary rows.
4. Upgrade intermediate type to final target type.
5. Insert 24 final target-boundary rows.
6. Compare every row and column with a reference table created directly in the final shape.

This intentionally checks both:

- data that existed before the first upgrade;
- data written after an upgrade and then subjected to another upgrade.

The comparison includes schema metadata, all row data, indexes, selected foreign keys, and selected persistent statistics.

## Category counts

| Category | Cases |
| --- | ---: |
| alias_normalization | 32 |
| decimal_max | 64 |
| variable_max | 20 |
| variable_overflow | 10 |
| zero_core | 512 |
| zero_cross | 112 |

## Boundary coverage

| Factor | Coverage |
| --- | --- |
| Zero-length types | `CHAR(0)`, `VARCHAR(0)`, `BINARY(0)`, `VARBINARY(0)` |
| Zero transitions | fixed/variable length 1 and 2, cross character/binary, `TEXT`, `BLOB` |
| Decimal maximum | `DECIMAL/NUMERIC(63,30) -> (64,30) -> (65,30)`, including cross type names |
| Variable row-size maximum | utf8mb4, utf8mb3, latin1, ascii `VARCHAR`, and `VARBINARY` |
| Overflow to LOB | maximum-adjacent `VARCHAR -> TEXT` and `VARBINARY -> BLOB` |
| Aliases | `BOOL`, `BOOLEAN`, `TINYINT(1)`, `INT(0)`, `ZEROFILL`, `DEC`, `FIXED`, bare types, `NCHAR`, `NVARCHAR`, `CHARACTER`, `CHARACTER VARYING` |
| Attributes | `NOT NULL DEFAULT -> NULL`, preserve default, `NOT NULL` without default, nullable |
| Column positions | no position clause, no-op `AFTER id`, actual `AFTER c`, `FIRST` |
| Row formats | `DYNAMIC`, `COMPACT`, `COMPRESSED`, `REDUNDANT` |
| Index interactions | no index and index added with the first upgrade |
| Other interactions | foreign-key carrier subset and persistent statistics subset |

Zero-length source columns cannot be indexed directly. Selected cases therefore add the target index in the same first ALTER after the column has become non-zero length.

Maximum variable lengths are fixture-specific constants for the exact table shape used here and MySQL 8.0.45 row-size behavior. They are not universal server constants.

## Internal pipeline execution

Create the fixed database first:

```bash
mysql --login-path=internal_qa \
  -e "DROP DATABASE IF EXISTS qa_type_upgrade_boundary; CREATE DATABASE qa_type_upgrade_boundary CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci"
```

Run one profile as one SQL stream:

```bash
cat copy/*.sql | mysql --login-path=internal_qa \
  --batch --raw --skip-column-names --binary-mode --force \
  qa_type_upgrade_boundary > copy.actual.tsv 2> copy.errors.log

diff -u expected_output.tsv copy.actual.tsv
test ! -s copy.errors.log
```

Repeat separately for `inplace/*.sql` and `instant/*.sql`. The expected output is identical for all profiles. Do not mix profiles or batches.

A run passes only when:

1. stdout matches `expected_output.tsv` exactly;
2. stderr is empty;
3. no row is missing;
4. no row contains `|FAIL`;
5. there is no signal, assertion, timeout, MySQL 2013/2006, or lost connection.

This batch has no planned negative SQL errors. `ANALYZE TABLE` output is expected only in statistics cases.

## Regenerate, verify, and audit

```bash
PYTHONPATH=src .venv312/bin/python tools/generate_type_upgrade_boundary.py \
  --output generated/type_upgrade_boundary_v1

PYTHONPATH=src .venv312/bin/python tools/run_type_upgrade_boundary.py \
  --cases generated/type_upgrade_boundary_v1 \
  --results generated/type_upgrade_boundary_v1/local_results.jsonl \
  --summary generated/type_upgrade_boundary_v1/local_summary.json \
  --profile copy

PYTHONPATH=src .venv312/bin/python tools/audit_type_upgrade_boundary.py \
  --boundary generated/type_upgrade_boundary_v1 \
  --parent generated/type_upgrade_consistency/cases.jsonl.gz \
  --parent generated/type_upgrade_consistency_extension_v1/cases.jsonl.gz \
  --parent generated/type_upgrade_statistics_v1/cases.jsonl.gz \
  --parent generated/type_upgrade_pipeline_v1/cases.jsonl.gz
```
