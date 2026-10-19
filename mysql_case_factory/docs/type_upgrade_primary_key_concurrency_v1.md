# Primary-key type-upgrade concurrency batch v1

This batch covers primary-key type upgrades, `AUTO_INCREMENT`, extreme values,
concurrent DML, and all-column correctness.

## Identity

- **BATCH_ID:** `2026-10-19-type-upgrade-primary-key-concurrency-v1`
- **BATCH_KIND:** `primary_key_concurrency_extension`
- **PARENT_BATCH_ID:** `2026-10-15-type-upgrade-boundary-v1`
- **CASE_PREFIX:** `TUCPK`
- **Transition count:** 107
- **Full scenario count:** 946,944
- **Profiles:** `COPY`, `INPLACE`, `INSTANT`
- **Profile execution count:** 2,840,832
- **Smoke cases:** 107, one per transition
- **Fixed database:** `qa_type_upgrade_primary_key`

The full scenario space is virtual and generated lazily by the runner. It is not
materialized as individual SQL files because concurrent DML requires multiple
connections, timing evidence, and worker-level result records.

## Primary-key type coverage

| Family | Transitions | Notes |
| --- | ---: | --- |
| Integer | 45 | Includes `AUTO_INCREMENT` and the known bug path |
| DECIMAL / NUMERIC | 14 | Precision expansion with unchanged scale |
| BIT | 10 | Width boundaries through `BIT(64)` |
| CHAR / VARCHAR | 12 | 256 boundary and `CHAR <-> VARCHAR` conversion |
| BINARY / VARBINARY | 14 | Fixed/variable and 256/512/1024/2048 boundaries |
| TEXT | 6 | All tiers from `TINYTEXT` to `LONGTEXT` |
| BLOB | 6 | All tiers from `TINYBLOB` to `LONGBLOB` |
| **Total** | **107** |  |

TEXT and BLOB primary keys use:

```sql
PRIMARY KEY(pk(32))
```

The suite verifies that the prefix length remains 32 after the upgrade.

## Algorithm expectations

| Family | INPLACE | INSTANT |
| --- | --- | --- |
| Integer | success | success |
| DECIMAL / NUMERIC | success | success |
| BIT | success | success |
| BINARY / VARBINARY | success | success |
| TEXT | success | success |
| BLOB | success | success |
| CHAR / VARCHAR before 256 | success | expected reject |
| CHAR / VARCHAR crossing 256 | success | success |
| CHAR / VARCHAR after 256 | success | expected reject |

Expected `INSTANT` rejection is a negative-pass oracle: the DDL must fail
atomically and leave schema, data, and indexes unchanged.

## Known AUTO_INCREMENT bug path

Every integer scenario performs an insert whose explicit column list omits the
auto-increment primary key:

```sql
INSERT INTO t (
  row_no,
  tenant_id,
  worker_id,
  seq_no,
  phase,
  c_tinyint,
  c_smallint,
  c_mediumint,
  c_int,
  c_bigint,
  c_utinyint,
  c_usmallint,
  c_umediumint,
  c_uint,
  c_ubigint,
  c_char,
  c_varchar,
  c_binary,
  c_varbinary,
  c_decimal,
  c_bit,
  c_text,
  c_blob
) VALUES (...);
```

The runner verifies:

- `pk` is generated;
- `pk` is non-NULL;
- `pk` is unique;
- the auto-increment counter does not regress;
- all other columns remain correct.

The final verification query explicitly lists every column. It does not use
`SELECT *`.

## Scenario factors

| Factor | Values |
| --- | --- |
| Integer initial states | 10 |
| Non-integer initial states | 6 |
| DDL/DML phases | 4 |
| Insert styles | 4 |
| DML modes | 3 |
| Worker counts | 4, 16 |
| Row formats | DYNAMIC, COMPACT, COMPRESSED, REDUNDANT |
| Primary-key shapes | single, PK first composite, PK second composite |

The full count is:

```text
45 integer transitions
× 10 integer states
× 4 phases
× 4 insert styles
× 3 DML modes
× 2 worker counts
× 4 row formats
× 3 key shapes
= 518,400 integer scenarios

62 non-integer transitions
× 6 states
× 4 phases
× 4 insert styles
× 3 DML modes
× 2 worker counts
× 4 row formats
× 3 key shapes
= 428,544 non-integer scenarios

518,400 + 428,544 = 946,944 scenarios
```

## Extreme integer states

```text
empty_counter_1
empty_counter_max_minus_16
empty_counter_max_minus_1
empty_counter_max
one_row_max_minus_1
one_row_max
tail_16_to_max_minus_1
tail_16_to_max
all_deleted_high_counter
mixed_explicit_generated_max
```

After upgrade, integer cases insert:

```text
source_max + 1
target_max - 1
target_max
```

If a concurrent insert starts before the DDL and exceeds the source type range,
the runner records the source-range failure and retries it after the DDL. A
retry must succeed and the final data must be complete and unique.

## Concurrency phases

```text
during_ddl
post_ddl
pre_during_post
across_ddl
```

The runner records DDL and DML monotonic intervals and reports `NO_OVERLAP`
when a `during_ddl`, `pre_during_post`, or `across_ddl` case did not truly
overlap. Increase `--filler-rows` and retry in that case.

## Generate artifacts

```bash
cd mysql_case_factory
PYTHONPATH=src .venv312/bin/python tools/generate_type_upgrade_primary_key.py \
  --output generated/type_upgrade_primary_key_concurrency_v1
```

## Local smoke execution

The local runner starts an isolated MySQL 8.0.45 server:

```bash
cd mysql_case_factory
PYTHONPATH=src .venv312/bin/python tools/run_type_upgrade_primary_key_concurrency.py \
  --cases generated/type_upgrade_primary_key_concurrency_v1 \
  --results generated/type_upgrade_primary_key_concurrency_v1/local_results.jsonl \
  --summary generated/type_upgrade_primary_key_concurrency_v1/local_summary.json \
  --profile copy \
  --smoke \
  --phase post_ddl \
  --filler-rows 16
```

Current local evidence:

```text
107 / 107 smoke scenarios PASS
MySQL 8.0.45
```

Additional local concurrency evidence:

```text
during_ddl:       10 / 10 PASS, 10 true overlaps
across_ddl:        3 / 3 PASS
pre_during_post:   3 / 3 PASS
```

## Internal execution

Run against an existing internal MySQL server:

```bash
cd mysql_case_factory

# Do not put the password on the command line.
export TUCPK_MYSQL_PASSWORD='...'

PYTHONPATH=src .venv312/bin/python tools/run_type_upgrade_primary_key_concurrency.py \
  --cases generated/type_upgrade_primary_key_concurrency_v1 \
  --results generated/type_upgrade_primary_key_concurrency_v1/inplace_results.jsonl \
  --summary generated/type_upgrade_primary_key_concurrency_v1/inplace_summary.json \
  --profile inplace \
  --smoke \
  --phase during_ddl \
  --filler-rows 256 \
  --external \
  --host <internal-host> \
  --port 3306 \
  --user <internal-user> \
  --password-env TUCPK_MYSQL_PASSWORD
```

Repeat with `--profile instant`.

For the full 946,944-scenario matrix, replace `--smoke` with `--all`:

```bash
PYTHONPATH=src .venv312/bin/python tools/run_type_upgrade_primary_key_concurrency.py \
  --cases generated/type_upgrade_primary_key_concurrency_v1 \
  --results generated/type_upgrade_primary_key_concurrency_v1/inplace_full_results.jsonl \
  --summary generated/type_upgrade_primary_key_concurrency_v1/inplace_full_summary.json \
  --profile inplace \
  --all \
  --filler-rows 1024 \
  --external \
  --host <internal-host> \
  --port 3306 \
  --user <internal-user> \
  --password-env TUCPK_MYSQL_PASSWORD
```

Repeat for `instant`.

### Single-case debugging

```bash
PYTHONPATH=src .venv312/bin/python tools/run_type_upgrade_primary_key_concurrency.py \
  --cases generated/type_upgrade_primary_key_concurrency_v1 \
  --results /tmp/tucpk-case.jsonl \
  --summary /tmp/tucpk-case.json \
  --profile inplace \
  --case-id TUCPK-003457 \
  --phase during_ddl \
  --filler-rows 1024 \
  --external \
  --host <internal-host> \
  --port 3306 \
  --user <internal-user> \
  --password-env TUCPK_MYSQL_PASSWORD
```

## Source-range retry verification

The checked-in local evidence uses `TUCPK-003457`, an integer scenario whose
source auto-increment counter is already at the source maximum. It runs with
`--workers-first`, so workers attempt inserts before the DDL converts the PK to
the wider type:

```bash
PYTHONPATH=src .venv312/bin/python tools/run_type_upgrade_primary_key_concurrency.py \
  --cases generated/type_upgrade_primary_key_concurrency_v1 \
  --results generated/type_upgrade_primary_key_concurrency_v1/retry_results.jsonl \
  --summary generated/type_upgrade_primary_key_concurrency_v1/retry_summary.json \
  --profile copy \
  --case-id TUCPK-003457 \
  --phase during_ddl \
  --workers-first \
  --filler-rows 0
```

Current evidence:

```text
PASS
overlap = true
source_range_retries >= 1
```

This verifies that source-range failures do not create partial rows and that all
four inserts succeed after the DDL.

## Multi-row and strict post-DDL evidence

Checked-in local evidence also includes:

```text
TUCPK-000217: integer multi-row INSERT omitting the AUTO_INCREMENT PK
TUCPK-518617: non-integer multi-row INSERT with explicit PK

strict post-DDL: 3 scenarios
overlap = false for all strict post-DDL scenarios
```

These files are:

```text
multi_row_results.jsonl
strict_post_results.jsonl
```

## Expected INSTANT reject evidence

The checked-in evidence uses smoke case `TUCPKS-000070`, a pre-256 `CHAR(16) -> CHAR(32)`
upgrade:

```bash
PYTHONPATH=src .venv312/bin/python tools/run_type_upgrade_primary_key_concurrency.py \
  --cases generated/type_upgrade_primary_key_concurrency_v1 \
  --results generated/type_upgrade_primary_key_concurrency_v1/expected_reject_results.jsonl \
  --summary generated/type_upgrade_primary_key_concurrency_v1/expected_reject_summary.json \
  --profile instant \
  --smoke \
  --case-id TUCPKS-000070 \
  --phase during_ddl \
  --filler-rows 0
```

Current evidence:

```text
EXPECTED_REJECT
overlap = true
summary.all_pass = true
```

The runner verifies that the source schema remains unchanged and no partial DDL
state is visible.

## Result judgment

A scenario is `PASS` only when:

1. DDL has the expected outcome.
2. All committed worker rows exist.
3. All rolled-back worker rows are absent.
4. Primary keys are unique.
5. `AUTO_INCREMENT` values are non-NULL and do not regress.
6. Every canary column matches its expected value.
7. Schema and primary-key metadata match the target.
8. TEXT/BLOB prefix length remains 32.
9. Expected source-range failures retry successfully after DDL.
10. No worker has an unexpected error.
11. DDL/DML overlap is true for concurrency phases.

Any of the following is a failure:

```text
FAIL_DDL
FAIL_VALIDATION
FAIL_CRASH
FAIL_TIMEOUT
NO_OVERLAP
unexpected duplicate
lost row
column mismatch
schema mismatch
index metadata mismatch
```

## Audit

```bash
cd mysql_case_factory
PYTHONPATH=src .venv312/bin/python tools/audit_type_upgrade_primary_key.py \
  --primary-key generated/type_upgrade_primary_key_concurrency_v1
```

The audit checks:

- 107 transitions;
- 946,944 virtual scenarios;
- all three profile counts;
- 107 unique smoke cases;
- CHAR/VARCHAR `INSTANT` expectations;
- TEXT/BLOB prefix primary keys;
- artifact hashes;
- local smoke evidence;
- during/across/pre-during-post concurrency evidence;
- README usage instructions.
