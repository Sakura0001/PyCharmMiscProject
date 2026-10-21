# Virtual/function type-upgrade batch

This batch verifies that base-column type expansion does not corrupt data or
change algorithm behavior when the base column is referenced by a virtual
generated column, a stored generated column, or a functional index.

- **BATCH_ID:** `2026-10-20-virtual-function-type-upgrade-v1`
- **BATCH_KIND:** `virtual_function_type_upgrade`
- **CASE_PREFIX:** `TUCVF`
- **Database:** `qa_virtual_function_type_upgrade`
- **Cases:** 5136
- **Transitions:** 107
- **Dependency modes:** 4
- **Profiles:** copy, inplace, instant
- **Smoke cases:** 84

## Execution

Run one profile:

```bash
PYTHONPATH=src python3 tools/run_virtual_function_type_upgrade.py   --profile copy   --all   --results generated/virtual_function_type_upgrade_v1/copy_results.jsonl   --summary generated/virtual_function_type_upgrade_v1/copy_summary.json   --external   --host <authorized-host>   --port 3306   --user <authorized-user>   --password-env VIRTUAL_FUNCTION_MYSQL_PASSWORD
```

Repeat with `--profile inplace` and `--profile instant`.

Run the 84-case smoke matrix:

```bash
PYTHONPATH=src python3 tools/run_virtual_function_type_upgrade.py   --profile copy   --smoke   --results generated/virtual_function_type_upgrade_v1/smoke_results.jsonl   --summary generated/virtual_function_type_upgrade_v1/smoke_summary.json   --external   --host <authorized-host>   --port 3306   --user <authorized-user>   --password-env VIRTUAL_FUNCTION_MYSQL_PASSWORD
```

Repeat the smoke matrix with `--profile inplace` and `--profile instant`.
