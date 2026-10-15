# MySQL type-upgrade condensed pipeline batch

This is a **new, independent condensed batch** for internal pipeline use. It is separate from the earlier `TUC`, `TUCX`, and `TUCS` batches.

- **BATCH_ID:** `2026-10-15-type-upgrade-pipeline-v1`
- **BATCH_KIND:** `pipeline_condensed_batch`
- **PARENT_BATCH_ID:** `2026-10-14-type-upgrade-statistics-and-chain-v1`
- **CASE_PREFIX:** `TUCP`
- **CASE_COUNT:** 50
- **Profiles:** `copy`, `inplace`, `instant`
- **SQL files:** 150 (50 per profile)
- **Rows per scenario:** 96 reference rows + 96 algorithm rows = 192
- **SQL line range per file:** 413-426
- **Fixed QA database:** `qa_type_upgrade_pipeline`
- **Local MySQL 8.0.45 COPY:** 50/50 scenarios PASS; combined-stream output and final object cleanup PASS

## Output contract

The SQL sets no session or global variables. Each scenario:

1. Starts with `DROP TABLE IF EXISTS`.
2. Creates globally unique `tab_tucp_NNN_*` tables; `idx/uk_tucp_NNN_*` indexes are unique within each table and have globally unique qualified `table.index` identifiers.
3. Seeds deterministic boundary/pattern data.
4. Executes the target upgrade with one explicit `ALGORITHM=<profile>` statement (two statements for the chained case).
5. Inserts post-upgrade target-boundary data.
6. Emits only stable assertion labels such as `TUCP-000001|DATA|OK`.
7. Drops all tables last.

The expected output is identical for `COPY`, `INPLACE`, and `INSTANT`. `ANALYZE TABLE` result rows are included only in the two statistics scenarios; therefore the pipeline must use the fixed database name `qa_type_upgrade_pipeline`. Run the client with `--batch --raw --skip-column-names` so output can be compared byte-for-byte with `expected_output.tsv`.

## Internal pipeline execution

Run each profile separately and do not mix result files:

```bash
# Prepare the fixed schema before running SQL.
mysql --login-path=internal_qa \
  -e "DROP DATABASE IF EXISTS qa_type_upgrade_pipeline; CREATE DATABASE qa_type_upgrade_pipeline CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci"

cat copy/*.sql | mysql --login-path=internal_qa \
  --batch --raw --skip-column-names --binary-mode --force \
  qa_type_upgrade_pipeline > copy.actual.tsv 2> copy.errors.log

diff -u expected_output.tsv copy.actual.tsv
test ! -s copy.errors.log
```

Repeat the same three commands with `inplace/*.sql` and `instant/*.sql`, writing `inplace.actual.tsv` / `instant.actual.tsv`. A run passes only when all three conditions hold:

1. `mysql` has no error output and does not report a nonzero execution status.
2. `diff` is empty.
3. No expected output row is missing and no actual row contains `|FAIL`.

A signal, assertion, MySQL 2013/2006, lost connection, timeout, or missing output is `FAIL_CRASH` or `FAIL_TIMEOUT`, never an expected negative result. This condensed batch intentionally contains no planned negative SQL errors.

For single-scene debugging, use `expected/TUCP-NNNNNN.tsv` as that scene's expected output.

## Core coverage

| Factor | Coverage |
| --- | --- |
| Type families | Integer 8, DECIMAL 6, character 8, binary 6, BIT 11 |
| Index forms | secondary, unique, composite, prefix, descending, functional, primary/AUTO_INCREMENT |
| Foreign keys | `ON DELETE CASCADE`, `ON UPDATE CASCADE`, `ON DELETE SET NULL`, `NO ACTION` |
| Dependencies | view, trigger, stored function, stored procedure, combined dependency scenario |
| Statistics | persistent table/index statistics and partition statistics |
| Special forms | chained `SMALLINT -> INT -> BIGINT`, multi-column upgrade, range partition, `MyISAM`, `MEMORY`, InnoDB row formats |
| BIT widths | 1, 4, 8, 11, 16, 24, 32, 40, 48, 56, 63, 64 (11 upgrade pairs) |

Excluded factors remain excluded: floating point, temporal types, `ENUM`/`SET`, JSON, spatial, vector, FULLTEXT, SPATIAL, backup/recovery, crash injection, and concurrency. This batch is a condensed core matrix, not a replacement for the full `TUC`/`TUCX`/`TUCS` matrices.

## Regenerate, verify, and audit

```bash
PYTHONPATH=src .venv312/bin/python tools/generate_type_upgrade_pipeline.py \
  --output generated/type_upgrade_pipeline_v1

PYTHONPATH=src .venv312/bin/python tools/run_type_upgrade_pipeline.py \
  --cases generated/type_upgrade_pipeline_v1 \
  --results generated/type_upgrade_pipeline_v1/local_results.jsonl \
  --summary generated/type_upgrade_pipeline_v1/local_summary.json \
  --profile copy

PYTHONPATH=src .venv312/bin/python tools/audit_type_upgrade_pipeline.py \
  --pipeline generated/type_upgrade_pipeline_v1 \
  --parent generated/type_upgrade_consistency/cases.jsonl.gz \
  --parent generated/type_upgrade_consistency_extension_v1/cases.jsonl.gz \
  --parent generated/type_upgrade_statistics_v1/cases.jsonl.gz
```

The audit checks 50 case IDs, all 150 SQL files, exact expected output, artifact hashes, unique table names, index-name format and per-table uniqueness, no forbidden types, no session statements, parent-batch isolation, local COPY evidence, and 17 required semantic coverage checks.
