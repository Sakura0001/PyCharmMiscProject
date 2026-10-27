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
all 12 batches
x all profiles defined by each batch
= 29 execution streams
= 2,933,121 case/profile executions
```

Selective regression is not accepted. If any batch, profile, or SQL artifact is
skipped, the regression is incomplete and must be reported as not run.

## Totals

| Metric | Value |
| --- | ---: |
| Batches | 12 |
| Unique cases/scenarios | 978,109 |
| Profiles | 3 |
| Case/profile executions | 2,933,121 |
| Execution streams | 29 |
| SQL artifacts | 2,531 |

## Required batch order

Run batches in this order:

1. `TUC`
2. `TUCX`
3. `TUCS`
4. `TUCP`
5. `TUCZ`
6. `TUCPK`
7. `TUCUI`
8. `TUCFK`
9. `TUCUD`
10. `TUCVF`
11. `TUCPF`
12. `TUCR`

Within every batch, run profiles in this order:

1. `COPY`
2. `INPLACE`
3. `INSTANT`

This produces the 29 required execution units below.

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
| 16 | `2026-10-19-type-upgrade-primary-key-concurrency-v1` | `TUCPK` | 946,944 | `COPY` | `tools/run_type_upgrade_primary_key_concurrency.py --profile copy --all` | `qa_type_upgrade_primary_key` |
| 17 | `2026-10-19-type-upgrade-primary-key-concurrency-v1` | `TUCPK` | 946,944 | `INPLACE` | `tools/run_type_upgrade_primary_key_concurrency.py --profile inplace --all` | `qa_type_upgrade_primary_key` |
| 18 | `2026-10-19-type-upgrade-primary-key-concurrency-v1` | `TUCPK` | 946,944 | `INSTANT` | `tools/run_type_upgrade_primary_key_concurrency.py --profile instant --all` | `qa_type_upgrade_primary_key` |
| 19 | `2026-10-20-inplace-ddl-unique-conflict-v1` | `TUCUI` | 2,304 | `COPY` | `tools/run_inplace_unique_conflict.py --profile copy --all` | `qa_inplace_unique_conflict` |
| 20 | `2026-10-20-inplace-ddl-unique-conflict-v1` | `TUCUI` | 2,304 | `INPLACE` | `tools/run_inplace_unique_conflict.py --profile inplace --all` | `qa_inplace_unique_conflict` |
| 21 | `2026-10-20-inplace-ddl-unique-conflict-v1` | `TUCUI` | 2,304 | `INSTANT` | `tools/run_inplace_unique_conflict.py --profile instant --all` | `qa_inplace_unique_conflict` |
| 22 | `2026-10-20-fk-type-expansion-consistency-v1` | `TUCFK` | 568 | `INPLACE` | `generated/fk_type_expansion_v1/inplace_suite.sql.gz` | `qa_fk_type_expansion` |
| 23 | `2026-10-20-fk-type-expansion-consistency-v1` | `TUCFK` | 568 | `INSTANT` | `generated/fk_type_expansion_v1/instant_suite.sql.gz` | `qa_fk_type_expansion` |
| 24 | `2026-10-20-unique-ddl-expected-error-v1` | `TUCUD` | 192 | `INPLACE` | `tools/run_unique_ddl_expected_error.py --all` | `qa_unique_ddl_expected_error` |
| 25 | `2026-10-20-virtual-function-type-upgrade-v1` | `TUCVF` | 5,136 | `COPY` | `tools/run_virtual_function_type_upgrade.py --profile copy --all` | `qa_virtual_function_type_upgrade` |
| 26 | `2026-10-20-virtual-function-type-upgrade-v1` | `TUCVF` | 5,136 | `INPLACE` | `tools/run_virtual_function_type_upgrade.py --profile inplace --all` | `qa_virtual_function_type_upgrade` |
| 27 | `2026-10-20-virtual-function-type-upgrade-v1` | `TUCVF` | 5,136 | `INSTANT` | `tools/run_virtual_function_type_upgrade.py --profile instant --all` | `qa_virtual_function_type_upgrade` |
| 28 | `2026-10-21-type-upgrade-performance-v1` | `TUCPF` | 7 | `PERFORMANCE` | `tools/run_type_upgrade_performance.py --all` | `qa_type_upgrade_performance` |
| 29 | `2026-10-27-type-upgrade-condensed-120-v1` | `TUCR` | 120 | `COMBINED` | `generated/type_upgrade_condensed_120_v1/sql/*.sql` | `qa_type_upgrade_condensed_120` |

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

## `TUCPK` virtual runner batch

`TUCPK` is not a single SQL stream. It uses a concurrent Python runner because
it must start multiple worker connections around the DDL and record overlap
evidence.

Command pattern:

```bash
export TUCPK_MYSQL_PASSWORD='...'

PYTHONPATH=src .venv312/bin/python tools/run_type_upgrade_primary_key_concurrency.py \
  --cases generated/type_upgrade_primary_key_concurrency_v1 \
  --results regression_results/TUCPK/<profile>.jsonl \
  --summary regression_results/TUCPK/<profile>.json \
  --profile <profile> \
  --all \
  --filler-rows 1024 \
  --external \
  --host <internal-host> \
  --port 3306 \
  --user <internal-user> \
  --password-env TUCPK_MYSQL_PASSWORD
```

Required result:

```text
summary.all_pass = true
summary.all_pass = true
counts.PASS + counts.EXPECTED_REJECT = 946944
NO_OVERLAP = 0
```

Preserve both the JSONL worker evidence and the JSON summary.

## `TUCUI` virtual runner batch

`TUCUI` is also a concurrent runner batch. It is not a plain SQL stream because
it must keep multiple duplicate-DML workers active around the DDL and prove
real overlap. Detailed design and evidence are in
[docs/inplace_unique_conflict_v1.md](inplace_unique_conflict_v1.md).

Command pattern:

```bash
export TUCUI_MYSQL_PASSWORD='...'

PYTHONPATH=src python3 tools/run_inplace_unique_conflict.py \
  --profile <profile> \
  --all \
  --results regression_results/TUCUI/<profile>.jsonl \
  --summary regression_results/TUCUI/<profile>.json \
  --external \
  --host <authorized-host> \
  --port 3306 \
  --user <authorized-user> \
  --password-env TUCUI_MYSQL_PASSWORD
```

Required result:

```text
summary.all_pass = true
counts.PASS + counts.EXPECTED_REJECT = 2304
NO_OVERLAP = 0
```

Preserve both the JSONL worker evidence and the JSON summary.

## `TUCFK` compressed SQL batch

`TUCFK` verifies FK type-expansion consistency with exact expected output. It
contains planned negative DDL errors, so execute it with `--force`.

```bash
gunzip -c generated/fk_type_expansion_v1/inplace_suite.sql.gz |
  mysql --login-path=internal_qa \
    --batch --raw --skip-column-names --binary-mode --force \
    qa_fk_type_expansion \
    > regression_results/TUCFK/inplace.tsv \
    2> regression_results/TUCFK/inplace.stderr.log

diff -u \
  generated/fk_type_expansion_v1/expected_output_inplace.tsv \
  regression_results/TUCFK/inplace.tsv
```

Repeat with `instant_suite.sql.gz` and `expected_output_instant.tsv`.

Required result:

```text
stdout matches expected TSV exactly
no row ends with FAIL
orphan_count = 0 in every row
fk_exists = 1 in every row
```

## `TUCUD` virtual runner batch

`TUCUD` verifies that unique secondary-index DDL fails when concurrent DML
introduces a duplicate after the DDL starts.

```bash
export UNIQUE_DDL_MYSQL_PASSWORD='...'

PYTHONPATH=src python3 tools/run_unique_ddl_expected_error.py \
  --all \
  --results regression_results/TUCUD/inplace.jsonl \
  --summary regression_results/TUCUD/inplace.json \
  --external \
  --host <authorized-host> \
  --port 3306 \
  --user <authorized-user> \
  --password-env UNIQUE_DDL_MYSQL_PASSWORD
```

Required result:

```text
summary.all_pass = true
counts.PASS = 192
NO_OVERLAP = 0
FAIL_DDL_SUCCESS = 0
```

## `TUCVF` virtual runner batch

`TUCVF` verifies that virtual generated columns, stored generated columns, and
functional indexes do not change algorithm behavior or corrupt data during
base-column type expansion.

```bash
export VIRTUAL_FUNCTION_MYSQL_PASSWORD='...'

PYTHONPATH=src python3 tools/run_virtual_function_type_upgrade.py \
  --profile <profile> \
  --all \
  --results regression_results/TUCVF/<profile>.jsonl \
  --summary regression_results/TUCVF/<profile>.json \
  --external \
  --host <authorized-host> \
  --port 3306 \
  --user <authorized-user> \
  --password-env VIRTUAL_FUNCTION_MYSQL_PASSWORD
```

Required result:

```text
summary.all_pass = true
counts.PASS = 1712
FAIL_ALGORITHM = 0
FAIL_DATA = 0
FAIL_UNCHANGED = 0
```

## `TUCPF` virtual performance runner batch

`TUCPF` measures large-table type-upgrade performance and post-upgrade query and
DML performance.

```bash
export TYPE_PERFORMANCE_MYSQL_PASSWORD='...'

PYTHONPATH=src python3 tools/run_type_upgrade_performance.py \
  --all \
  --rows 0 \
  --calibration-rows 100000 \
  --target-scan-seconds 300 \
  --max-rows 20000000 \
  --results regression_results/TUCPF/performance.jsonl \
  --summary regression_results/TUCPF/performance.json \
  --external \
  --host <authorized-host> \
  --port 3306 \
  --user <authorized-user> \
  --password-env TYPE_PERFORMANCE_MYSQL_PASSWORD
```

Required result:

```text
summary.all_pass = true
counts.PASS = 7
```

## `TUCR` combined SQL batch

`TUCR` contains exactly 120 SQL files. Each file executes both `INPLACE` and
`INSTANT`, performs deterministic partial-row DML, and compares each candidate
with a direct target-type reference table.

```bash
for file in generated/type_upgrade_condensed_120_v1/sql/*.sql; do
  mysql --login-path=internal_qa \
    --batch --raw --skip-column-names --binary-mode --force \
    qa_type_upgrade_condensed_120 \
    < "$file"
done > regression_results/TUCR/combined.tsv
```

Compare:

```bash
diff -u generated/type_upgrade_condensed_120_v1/expected_output.tsv \
  regression_results/TUCR/combined.tsv
```

Required result:

```text
240 result rows
all rows end with PASS
stderr is empty
```

## Required evidence

For every one of the 29 execution units, preserve:

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
generated/type_upgrade_primary_key_concurrency_v1/manifest.json
generated/inplace_unique_conflict_v1/manifest.json
generated/fk_type_expansion_v1/manifest.json
generated/unique_ddl_expected_error_v1/manifest.json
generated/virtual_function_type_upgrade_v1/manifest.json
generated/type_upgrade_performance_v1/manifest.json
generated/type_upgrade_condensed_120_v1/manifest.json
generated/type_upgrade_full_regression/manifest.json
```

The full-regression manifest must continue to list every generated type-upgrade
batch. Adding a new batch without adding it to this inventory is a regression
process defect.

## Non-negotiable completion rule

A regression report may say `PASS` only when all 29 execution units are present
and every batch-specific oracle passes. If any item is missing, the only valid
status is:

```text
INCOMPLETE
```

If any oracle fails, the only valid status is:

```text
FAIL
```
