# Type-upgrade condensed pipeline batch v1

This batch provides 50 individually executable, deterministic SQL scenarios for
internal pipeline validation of SQL-direct type upgrades. It is a new batch and
is intentionally separated from `TUC`, `TUCX`, and `TUCS`.

## Identity

- **BATCH_ID:** `2026-10-15-type-upgrade-pipeline-v1`
- **BATCH_KIND:** `pipeline_condensed_batch`
- **PARENT_BATCH_ID:** `2026-10-14-type-upgrade-statistics-and-chain-v1`
- **CASE_PREFIX:** `TUCP`
- **CASE_COUNT:** 50
- **Profiles:** `COPY`, `INPLACE`, `INSTANT`
- **SQL files:** 150, or 50 per profile
- **Fixed QA database:** `qa_type_upgrade_pipeline`

## Design goal

The batch condenses the most important correctness interactions into pipeline-
friendly files:

- Each file is 413-426 lines and has no session/global variable setup.
- Each file starts with table drops and ends with table drops.
- Every table, view, trigger, function, and procedure name includes the case
  number and is globally unique. Index names follow `idx/uk_tucp_NNN_*`, are
  unique within each table, and their qualified `table.index` identifiers are
  globally unique.
- Each scenario uses a reference table and an algorithm table. Both receive
  identical deterministic seed data, the algorithm table is upgraded, and both
  receive identical post-upgrade data.
- Assertions compare schema metadata, row data, index metadata, dependency
  results, and statistics existence without printing unstable estimates.
- Expected output is exactly the same for all three algorithms.
- There are no planned negative SQL errors in this condensed positive batch.

The output contract is intentionally strict: the internal pipeline must run with
`--batch --raw --skip-column-names --binary-mode --force`, compare output to
`expected_output.tsv`, require empty stderr, and treat any nonzero status,
missing row, `|FAIL` row, signal, assertion, timeout, or MySQL 2013/2006 as a
failure.

## Factor coverage

| Factor family | Count / values |
| --- | --- |
| Integer | 8 scenarios: signed and unsigned upgrades across `TINYINT`, `SMALLINT`, `MEDIUMINT`, `INT`, `BIGINT` |
| Decimal | 6 precision extensions with unchanged scale |
| Character | 8 scenarios across `CHAR`, `VARCHAR`, length boundaries, `TINYTEXT -> TEXT` |
| Binary | 6 scenarios across `BINARY`, `VARBINARY`, length boundaries, `TINYBLOB -> BLOB` |
| BIT | 11 scenarios: 1, 4, 8, 11, 16, 24, 32, 40, 48, 56, 63, 64 |
| Index forms | secondary, unique, composite, prefix, descending, functional, primary + `AUTO_INCREMENT` |
| Foreign keys | delete cascade, update cascade, delete set null, no action |
| Dependencies | view, trigger, stored function, stored procedure, combined scenario |
| Statistics | persistent table/index statistics and partition statistics |
| Special forms | chained `SMALLINT -> INT -> BIGINT`, multi-column ALTER, range partition, `MyISAM`, `MEMORY`, InnoDB row formats |

Foreign-key scenarios deliberately place the FK on a stable `fk_col` carrier.
This keeps the target-column upgrade a positive SQL case while still validating
constraint metadata and cascade/set-null behavior around the DDL.

Excluded factors remain out of scope: floating point, temporal types,
`ENUM`/`SET`, JSON, spatial, vector, FULLTEXT, SPATIAL, backup/recovery, crash
injection, and concurrency. This batch is a condensed core matrix, not a
replacement for the full 22,038-case `TUC`/`TUCX`/`TUCS` matrices.

## Artifacts

All artifacts are under `generated/type_upgrade_pipeline_v1`:

- `manifest.json`
- `cases.jsonl.gz`
- `coverage.tsv`
- `expected_output.tsv`
- `expected/TUCP-000001.tsv` through `expected/TUCP-000050.tsv`
- `copy/TUCP-000001.sql` through `copy/TUCP-000050.sql`
- `inplace/TUCP-000001.sql` through `inplace/TUCP-000050.sql`
- `instant/TUCP-000001.sql` through `instant/TUCP-000050.sql`
- `local_results.jsonl`
- `local_summary.json`
- `local_summary.md`
- `audit_report.json`
- `audit_summary.md`

The manifest records SHA-256 hashes for the generated cases, coverage, expected
output, and every SQL file. The generator is deterministic: rerunning it must
produce byte-identical compressed and SQL artifacts.

## Local verification

The local runner starts an isolated MySQL 8.0.45 server, creates
`qa_type_upgrade_pipeline`, executes each COPY SQL file through the MySQL
client, compares exact stdout with the per-case expected file, requires empty
stderr, then executes all 50 files as one concatenated SQL stream and compares
that output with `expected_output.tsv`. Finally, it checks that no `tab_tucp_*`
tables or routines remain.

Current evidence:

```text
Selected: 50
Executed: 50
PASS:     52 (50 scenarios + COMBINED_OUTPUT + FINAL_CLEANUP)
FAIL:     0
MySQL:    8.0.45
```

The independent audit also passes:

```text
Profile counts: copy=50, inplace=50, instant=50
Parent overlap: 0
Unique tables: 110
Unique index names: 54
SQL line range: 413-426
Semantic checks: 17/17
Local COPY: all PASS
```

## Internal execution

See
[generated/type_upgrade_pipeline_v1/README.md](../generated/type_upgrade_pipeline_v1/README.md)
for the exact pipeline commands. In summary:

1. Create or recreate `qa_type_upgrade_pipeline`.
2. Run `copy/*.sql`, `inplace/*.sql`, and `instant/*.sql` separately.
3. Save stdout and stderr for each profile.
4. Compare each stdout with `expected_output.tsv`.
5. Do not rewrite expected outcomes after execution.
6. Report batch ID, profile, nearest `-- CASE_ID`, SQL, stderr, terminal state,
   and output diff for every failure.
