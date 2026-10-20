# INPLACE DDL unique-conflict batch

This independent `TUCUI` batch covers unique-index conflicts around twelve
MySQL DDL operations. The complete matrix is virtual and lazily generated; no
credentials, endpoints, or connection settings are embedded in the artifacts.

- **BATCH_ID:** `2026-10-20-inplace-ddl-unique-conflict-v1`
- **BATCH_KIND:** `inplace_unique_conflict_extension`
- **CASE_PREFIX:** `TUCUI`
- **Database:** `qa_inplace_unique_conflict`
- **Operations:** 12
- **Full scenario space:** 2,304
- **Profiles:** `copy`, `inplace`, `instant`
- **Profile executions:** 6,912
- **Smoke cases:** 12, one per operation
- **Materialization:** `virtual_lazy_runner`

Every canonical operation DDL requests `ALGORITHM=INPLACE` and `LOCK=NONE`.
The legacy `MODIFY` and `CHANGE` forms are absent.

## Factor matrix

The scenario space is the exact Cartesian product of:

- 12 operations
- 4 conflict surfaces: `existing_unique`, `new_unique`, `composite_unique`, `nullable_unique`
- 4 conflict patterns: `seed_duplicate`, `concurrent_duplicate`, `semantic_collision`, `boundary_duplicate`
- 3 phases: `during_ddl`, `before_and_during_ddl`, `across_ddl_transaction`
- 2 worker counts: 4 and 16
- 2 data states: `normal` and `boundary`

The first case is `TUCUI-000001`; the last case is `TUCUI-002304`.

## Operation coverage

| Operation | Scenarios | Smoke case |
| --- | ---: | --- |
| `add_index` | 192 | `TUCUI-000001` |
| `drop_index` | 192 | `TUCUI-000193` |
| `add_unique` | 192 | `TUCUI-000385` |
| `drop_unique` | 192 | `TUCUI-000577` |
| `rename_index` | 192 | `TUCUI-000769` |
| `add_column` | 192 | `TUCUI-000961` |
| `drop_column` | 192 | `TUCUI-001153` |
| `rename_column` | 192 | `TUCUI-001345` |
| `add_foreign_key` | 192 | `TUCUI-001537` |
| `drop_foreign_key` | 192 | `TUCUI-001729` |
| `drop_check` | 192 | `TUCUI-001921` |
| `drop_generated` | 192 | `TUCUI-002113` |

The smoke selector uses `existing_unique`, `seed_duplicate`, `during_ddl`,
4 workers, and the `normal` data state.

## Generation

```bash
cd mysql_case_factory
python3 tools/generate_inplace_unique_conflict.py \
  --output generated/inplace_unique_conflict_v1
```

Generation is deterministic. `manifest.json`, `smoke_cases.jsonl.gz`,
`coverage.tsv`, and `README.md` have stable bytes for the same source version.

## Execution

The runner uses multiple concurrent MySQL connections, so it is not a plain SQL
suite. Run it against an authorized MySQL server and keep the password in an
environment variable.

```bash
export TUCUI_MYSQL_PASSWORD='...'

PYTHONPATH=src python3 tools/run_inplace_unique_conflict.py \
  --profile copy \
  --smoke \
  --results generated/inplace_unique_conflict_v1/local_results.jsonl \
  --summary generated/inplace_unique_conflict_v1/local_summary.json \
  --external \
  --host <authorized-host> \
  --port 3306 \
  --user <authorized-user> \
  --password-env TUCUI_MYSQL_PASSWORD
```

Repeat with `--profile inplace` and `--profile instant`. For the complete
virtual matrix, replace `--smoke` with `--all`:

```bash
PYTHONPATH=src python3 tools/run_inplace_unique_conflict.py \
  --profile inplace \
  --all \
  --results generated/inplace_unique_conflict_v1/inplace_results.jsonl \
  --summary generated/inplace_unique_conflict_v1/inplace_summary.json \
  --external \
  --host <authorized-host> \
  --port 3306 \
  --user <authorized-user> \
  --password-env TUCUI_MYSQL_PASSWORD
```

Single-case debugging uses `--case-id`, for example `--case-id TUCUI-000961`.
The runner creates and removes a unique run database for every case.

Optional tuning:

- `--filler-rows` controls the seeded row count; the default is 128.
- `--hold-seconds` controls how long each worker transaction stays open; the
  default is 1 second.
- `--max-attempts` bounds duplicate attempts per worker; the default is 10000.

## Local evidence

- **MySQL:** 8.0.45
- **COPY smoke:** 12/12 `PASS`, 12 true overlaps, 12 duplicate conflicts
- **INSTANT smoke:** 5 `PASS`, 7 `EXPECTED_REJECT`
- **INPLACE smoke:** 9 `PASS`, 3 `FAIL_DDL`
  (`add_column`, `drop_column`, `drop_generated`)
