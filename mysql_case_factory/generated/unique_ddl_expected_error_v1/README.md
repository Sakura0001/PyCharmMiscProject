# Unique-DDL expected-error batch

This batch verifies that online unique secondary-index DDL fails with MySQL
1062 when concurrent DML introduces a duplicate after the DDL has started.

- **BATCH_ID:** `2026-10-20-unique-ddl-expected-error-v1`
- **BATCH_KIND:** `unique_ddl_expected_error`
- **CASE_PREFIX:** `TUCUD`
- **Database:** `qa_unique_ddl_expected_error`
- **Cases:** 192
- **DDL forms:** 4
- **Index shapes:** 6
- **DML types:** 8
- **Rows per shape:** 200000
- **Smoke cases:** 6

## Execution

```bash
PYTHONPATH=src python3 tools/run_unique_ddl_expected_error.py \
  --all \
  --results generated/unique_ddl_expected_error_v1/inplace_results.jsonl \
  --summary generated/unique_ddl_expected_error_v1/inplace_summary.json \
  --external \
  --host <authorized-host> \
  --port 3306 \
  --user <authorized-user> \
  --password-env UNIQUE_DDL_MYSQL_PASSWORD
```

Use `--smoke` for the six shape representatives. Increase `--rows` if any case
reports `NO_OVERLAP`.
