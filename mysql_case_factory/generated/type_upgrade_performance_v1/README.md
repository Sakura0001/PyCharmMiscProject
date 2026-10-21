# Type-upgrade performance batch

This batch measures large-table type-upgrade performance and post-upgrade
query/DML performance.

- **BATCH_ID:** `2026-10-21-type-upgrade-performance-v1`
- **CASE_PREFIX:** `TUCPF`
- **Database:** `qa_type_upgrade_performance`
- **Scenarios:** 7
- **Upgrade columns:** 31
- **Noise columns:** 4

## Execution

```bash
PYTHONPATH=src python3 tools/run_type_upgrade_performance.py \
  --all \
  --results generated/type_upgrade_performance_v1/performance_results.jsonl \
  --summary generated/type_upgrade_performance_v1/performance_summary.json \
  --external \
  --host <authorized-host> \
  --port 3306 \
  --user <authorized-user> \
  --password-env TYPE_PERFORMANCE_MYSQL_PASSWORD
```
