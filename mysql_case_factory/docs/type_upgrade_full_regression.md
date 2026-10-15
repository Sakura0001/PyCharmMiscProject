# Mandatory full type-upgrade regression

This document is the release gate for the SQL-direct type-upgrade feature. It
integrates every current type-upgrade SQL artifact into one mandatory
regression inventory.

The machine-readable inventory is:

```text
generated/type_upgrade_full_regression/inventory.tsv
```

The machine-readable regression manifest is:

```text
generated/type_upgrade_full_regression/manifest.json
```

## Policy

Every regression must run:

```text
all 5 batches
x all 3 profiles
= 15 execution streams
= 68,514 case/profile executions
```

Selective regression is not accepted. If any batch, profile, or SQL artifact is
skipped, the regression is incomplete and must be reported as not run.

## Totals

| Metric | Value |
| --- | ---: |
| Batches | 5 |
| Unique cases/scenarios | 22,838 |
| Profiles | 3 |
| Case/profile executions | 68,514 |
| Execution streams | 15 |
| SQL artifacts | 2,409 |

## Required batch order

Run batches in this order:

1. `TUC`
2. `TUCX`
3. `TUCS`
4. `TUCP`
5. `TUCZ`

Within every batch, run profiles in this order:

1. `COPY`
2. `INPLACE`
3. `INSTANT`

This produces the 15 required execution units below.

## Full execution inventory

| Order | Batch ID | Prefix | Cases | Profile | SQL artifact | Database |
| ---: | --- | --- | ---: | --- | --- | --- |
| 1 | `2026-10-13-type-upgrade-consistency` | `TUC` | 8,270 | `COPY` | `generated/type_upgrade_consistency/copy_suite.sql.gz` | `qa_type_upgrade` |
| 2 | `2026-10-13-type-upgrade-consistency` | `TUC` | 8,270 | `INPLACE` | `generated/type_upgrade_consistency/inplace_suite.sql.gz` | `qa_type_upgrade` |
| 3 | `2026-10-13-type-upgrade-consistency` | `TUC` | 8,270 | `INSTANT` | `generated/type_upgrade_consistency/instant_suite.sql.gz` | `qa_type_upgrade` |
| 4 | `2026-10-13-type-upgrade-consistency-extension-v1` | `TUCX` | 13,721 | `COPY` | `generated/type_upgrade_consistency_extension_v1/copy_suite.sql.gz` | `qa_type_upgrade_extension` |
| 5 | `2026-10-13-type-upgrade-consistency-extension-v1` | `TUCX` | 13,721 | `INPLACE` | `generated/type_upgrade_consistency_extension_v1/inplace_suite.sql.gz` | `qa_type_upgrade_extension` |
| 6 | `2026-10-13-type-upgrade-consistency-extension-v1` | `TUCX` | 13,721 | `INSTANT` | `generated/type_upgrade_consistency_extension_v1/instant_suite.sql.gz` | `qa_type_upgrade_extension` |
| 7 | `2026-10-14-type-upgrade-statistics-and-chain-v1` | `TUCS` | 47 | `COPY` | `generated/type_upgrade_statistics_v1/copy_suite.sql.gz` | `qa_type_upgrade_statistics` |
| 8 | `2026-10-14-type-upgrade-statistics-and-chain-v1` | `TUCS` | 47 | `INPLACE` | `generated/type_upgrade_statistics_v1/inplace_suite.sql.gz` | `qa_type_upgrade_statistics` |
| 9 | `2026-10-14-type-upgrade-statistics-and-chain-v1` | `TUCS` | 47 | `INSTANT` | `generated/type_upgrade_statistics_v1/instant_suite.sql.gz` | `qa_type_upgrade_statistics` |
| 10 | `2026-10-15-type-upgrade-pipeline-v1` | `TUCP` | 50 | `COPY` | `generated/type_upgrade_pipeline_v1/copy/*.sql` | `qa_type_upgrade_pipeline` |
| 11 | `2026-10-15-type-upgrade-pipeline-v1` | `TUCP` | 50 | `INPLACE` | `generated/type_upgrade_pipeline_v1/inplace/*.sql` | `qa_type_upgrade_pipeline` |
| 12 | `2026-10-15-type-upgrade-pipeline-v1` | `TUCP` | 50 | `INSTANT` | `generated/type_upgrade_pipeline_v1/instant/*.sql` | `qa_type_upgrade_pipeline` |
| 13 | `2026-10-15-type-upgrade-boundary-v1` | `TUCZ` | 750 | `COPY` | `generated/type_upgrade_boundary_v1/copy/*.sql` | `qa_type_upgrade_boundary` |
| 14 | `2026-10-15-type-upgrade-boundary-v1` | `TUCZ` | 750 | `INPLACE` | `generated/type_upgrade_boundary_v1/inplace/*.sql` | `qa_type_upgrade_boundary` |
| 15 | `2026-10-15-type-upgrade-boundary-v1` | `TUCZ` | 750 | `INSTANT` | `generated/type_upgrade_boundary_v1/instant/*.sql` | `qa_type_upgrade_boundary` |

## Output and failure policy

### `TUC`, `TUCX`, and `TUCS`

These batches contain planned negative cases. Use `mysql --force`.

Required checks:

1. Execute the complete compressed suite.
2. Preserve stdout and stderr.
3. Result output must not contain `FAIL`.
4. Planned negative SQL errors may appear in stderr.
5. Every expected-success case must satisfy its schema, data, index,
   dependency, statistics, and query oracles.
6. Every expected-reject case must reject atomically.
7. Crash, assertion, signal, timeout, MySQL 2013/2006, and lost connection are
   failures.

Command pattern:

```bash
gunzip -c generated/type_upgrade_consistency/copy_suite.sql.gz |
  mysql --login-path="$MYSQL_LOGIN_PATH" \
    --batch --raw --skip-column-names --force \
    qa_type_upgrade \
    > regression_results/TUC/copy.tsv \
    2> regression_results/TUC/copy.stderr.log

grep -n $'\tFAIL\t\|^FAIL\b' regression_results/TUC/copy.tsv || true
```

The final `grep` must return no matches.

### `TUCP` and `TUCZ`

These batches have exact expected output and no planned negative SQL errors.

Required checks:

1. Execute the complete profile directory as one SQL stream.
2. Stdout must equal the batch's `expected_output.tsv`.
3. Stderr must be empty.
4. No row may be missing.
5. No row may contain `|FAIL`.
6. Crash, assertion, signal, timeout, MySQL 2013/2006, and lost connection are
   failures.

Command pattern:

```bash
cat generated/type_upgrade_pipeline_v1/copy/*.sql |
  mysql --login-path="$MYSQL_LOGIN_PATH" \
    --batch --raw --skip-column-names --binary-mode --force \
    qa_type_upgrade_pipeline \
    > regression_results/TUCP/copy.tsv \
    2> regression_results/TUCP/copy.stderr.log

diff -u \
  generated/type_upgrade_pipeline_v1/expected_output.tsv \
  regression_results/TUCP/copy.tsv

test ! -s regression_results/TUCP/copy.stderr.log
```

Repeat the same pattern for all six `TUCP` and `TUCZ` profile directories.

## Required evidence

For every one of the 15 execution units, preserve:

```text
batch ID
batch kind
case prefix
profile
SQL artifact or artifact glob
database
stdout
stderr
mysql exit status
start time
end time
server version
nearest CASE_ID for any failure
terminal state
```

For exact-output batches also preserve the `diff` result.

Do not rewrite expected outputs after execution.

## Artifact integrity

Before execution, verify:

```text
generated/type_upgrade_consistency/manifest.json
generated/type_upgrade_consistency_extension_v1/manifest.json
generated/type_upgrade_statistics_v1/manifest.json
generated/type_upgrade_pipeline_v1/manifest.json
generated/type_upgrade_boundary_v1/manifest.json
generated/type_upgrade_full_regression/manifest.json
```

The full-regression manifest must continue to list every generated type-upgrade
batch. Adding a new batch without adding it to this inventory is a regression
process defect.

## Non-negotiable completion rule

A regression report may say `PASS` only when all 15 execution units are present
and every batch-specific oracle passes. If any item is missing, the only valid
status is:

```text
INCOMPLETE
```

If any oracle fails, the only valid status is:

```text
FAIL
```
