# Mandatory full type-upgrade regression

This inventory integrates every current type-upgrade SQL batch. It is the
required regression scope. A regression is not complete unless all six batches
and all three profiles are executed.

- **Regression ID:** `2026-10-15-type-upgrade-full-regression-v1`
- **Batches:** 6
- **Cases/scenarios:** 969,782
- **Profile executions:** 2,909,346
- **Execution streams:** 18
- **SQL artifacts:** 2,409
- **Selective regression allowed:** no

There are 18 execution streams in total.

Use `inventory.tsv` as the machine-readable execution checklist. The fixed
order is TUC, TUCX, TUCS, TUCP, TUCZ, TUCPK; within each batch run `COPY`, `INPLACE`,
then `INSTANT`.

## Full inventory

| Order | Batch | Prefix | Cases | COPY SQL | INPLACE SQL | INSTANT SQL | Database |
| ---: | --- | --- | ---: | --- | --- | --- | --- |
| 1 | `2026-10-13-type-upgrade-consistency` | `TUC` | 8,270 | `copy_suite.sql.gz` | `inplace_suite.sql.gz` | `instant_suite.sql.gz` | `qa_type_upgrade` |
| 2 | `2026-10-13-type-upgrade-consistency-extension-v1` | `TUCX` | 13,721 | `copy_suite.sql.gz` | `inplace_suite.sql.gz` | `instant_suite.sql.gz` | `qa_type_upgrade_extension` |
| 3 | `2026-10-14-type-upgrade-statistics-and-chain-v1` | `TUCS` | 47 | `copy_suite.sql.gz` | `inplace_suite.sql.gz` | `instant_suite.sql.gz` | `qa_type_upgrade_statistics` |
| 4 | `2026-10-15-type-upgrade-pipeline-v1` | `TUCP` | 50 | `copy/*.sql` | `inplace/*.sql` | `instant/*.sql` | `qa_type_upgrade_pipeline` |
| 5 | `2026-10-15-type-upgrade-boundary-v1` | `TUCZ` | 750 | `copy/*.sql` | `inplace/*.sql` | `instant/*.sql` | `qa_type_upgrade_boundary` |
| 6 | `2026-10-19-type-upgrade-primary-key-concurrency-v1` | `TUCPK` | 946,944 | virtual runner | virtual runner | virtual runner | `qa_type_upgrade_primary_key` |

## Execution rules

1. Verify each source batch `manifest.json` before execution.
2. Execute all 18 rows in `inventory.tsv`; skipping any row makes the
   regression incomplete.
3. Run profiles separately and never mix output files.
4. Use an isolated internal QA database for each batch.
5. Do not rewrite expected output after execution.
6. A natural crash, assertion, signal, timeout, MySQL 2013/2006, or lost
   connection is a failure, never an expected negative result.

For `TUC`, `TUCX`, and `TUCS`, planned negative SQL errors are allowed in
stderr. Their result output must not contain `FAIL`.

For `TUCP` and `TUCZ`, there are no planned negative SQL errors. Stderr must
be empty, and stdout must match the batch's `expected_output.tsv` exactly.

## Command template

Set the login path once:

```bash
MYSQL_LOGIN_PATH=internal_qa
```

Compressed suite batches:

```bash
gunzip -c generated/type_upgrade_consistency/copy_suite.sql.gz |
  mysql --login-path="$MYSQL_LOGIN_PATH" \
    --batch --raw --skip-column-names --force \
    qa_type_upgrade \
    > regression_results/TUC/copy.tsv \
    2> regression_results/TUC/copy.stderr.log

grep -n $'\tFAIL\t\|^FAIL\b' regression_results/TUC/copy.tsv || true
```

Repeat for every `TUC`, `TUCX`, and `TUCS` profile artifact listed in
`inventory.tsv`.

Exact-output batches:

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

Repeat for every `TUCP` and `TUCZ` profile directory listed in `inventory.tsv`.

`TUCPK` uses the concurrent runner:

```bash
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
