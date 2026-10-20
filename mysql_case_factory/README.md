# mysql_case_factory

MySQL Community Server 8.0.22 and 8.0.41 SQL case planning, generation,
coverage auditing, and differential verification. The control-plane workflow
is aligned with `pg_case_factory`; SQL knowledge and execution semantics are
MySQL-specific and frozen independently for each exact patch release.

## Edition layout

| Edition | Skill | Statements | Factor pairs | Factor values |
| --- | --- | ---: | ---: | ---: |
| MySQL 8.0.22 | `editions/mysql_8_0_22/skills/mysql-8-0-22-sql-generation` | 112 | 505 | 1365 |
| MySQL 8.0.41 | `editions/mysql_8_0_41/skills/mysql-8-0-41-sql-generation` | 112 | 512 | 1389 |

Each edition contains its own skill entry point, statement references, factor
catalog, type catalog, one auditable combination matrix per statement,
coverage inventory, generated contract templates, and immutable inventory
digests. The 8.0.41 edition also contains
`version_delta_from_8_0_22.tsv`, which classifies every factor-value row as
added, changed, removed, or unchanged.

## Install and commands

```bash
python3 -m venv .venv
.venv/bin/pip install -e '.[test]'

mysql-case --edition 8.0.22 doctor --root .
mysql-case --edition 8.0.41 doctor --root .

# Edition-pinned entry points reject cross-edition inputs.
mysql-case-8022 doctor --root .
mysql-case-8041 doctor --root .
```

`mysql-case --help` exposes the same contract, inventory, coverage,
applicability, job, formal-run, differential, and skill-package command groups
used by the PostgreSQL project. `--edition` is required on the generic entry
point. The pinned entry points supply it automatically.

Database endpoints are configured through MySQL login paths, so passwords do
not appear in manifests or command lines. A formal execution profile binds an
exact server version number (`80022` or `80041`) and the runner records the
server UUID, host, port, character set, collation, and SQL mode before
comparison. Reference and candidate endpoints must be distinct instances.

## Rebuild and audit frozen knowledge

The checked-in outputs are deterministic. Run these commands after editing a
statement reference:

```bash
python3 tools/generate_matrices.py
python3 tools/build_edition_catalog.py
python3 tools/build_version_delta.py
python3 tools/build_edition_templates.py
python3 tools/audit_editions.py
python3 tools/package_skills.py --output artifacts/packages
```

The audit fails closed on missing statements, uncovered factors or values,
manifest digest drift, incomplete review status, and unreviewed version
deltas.

## Type-upgrade consistency suite

The SQL-direct type-upgrade consistency suite is a new-merge batch identified
by `2026-10-13-type-upgrade-consistency`; its 8,270 cases use the `TUC` prefix
and are separate from previous DDL verification cases. It covers integer,
DECIMAL, character, binary, and BIT upgrades with indexes, foreign keys,
generated columns, views, triggers, functions, procedures, prepared statements,
table forms, and relevant SQL modes. Local verification uses an isolated MySQL 8.0.45
`COPY` run; the same deterministic case IDs are rendered for internal
`INPLACE` and `INSTANT` validation. Internal AI executors must follow the batch
instructions in
[generated/type_upgrade_consistency/README.md](generated/type_upgrade_consistency/README.md):
execute only `TUC-*` cases carrying this batch ID, verify the manifest first,
run `INPLACE` and `INSTANT` separately with `mysql --force`, and never mix this
batch with previous DDL verification cases.

An independent child extension batch is available as
`2026-10-13-type-upgrade-consistency-extension-v1`. It contains 13,721 `TUCX-*`
cases covering P0 data behavior, target-column primary keys, multi-column ALTER,
foreign-key actions, and query oracles. Internal AI executors must keep `TUC`
and `TUCX` results separate. See
[docs/type_upgrade_consistency_extension_v1.md](docs/type_upgrade_consistency_extension_v1.md)
and
[generated/type_upgrade_consistency_extension_v1/README.md](generated/type_upgrade_consistency_extension_v1/README.md).

A third independent batch,
`2026-10-14-type-upgrade-statistics-and-chain-v1`, contains 47 `TUCS-*` cases
covering InnoDB table/index statistics, information-schema metadata,
partition statistics, EXPLAIN plans, chained `SMALLINT -> INT -> BIGINT`
upgrades, and duplicate-MODIFY rejection. See
[docs/type_upgrade_statistics_and_chain_v1.md](docs/type_upgrade_statistics_and_chain_v1.md)
and
[generated/type_upgrade_statistics_v1/README.md](generated/type_upgrade_statistics_v1/README.md).

A fourth independent condensed batch,
`2026-10-15-type-upgrade-pipeline-v1`, contains 50 `TUCP-*` pipeline scenarios.
It renders 150 individual SQL files: 50 each for `COPY`, `INPLACE`, and
`INSTANT`. Every scenario has deterministic output, globally unique table
names, table-scoped unique index names with globally unique qualified
`table.index` identifiers, no session-variable setup, and exact expected-output
files. See
[docs/type_upgrade_pipeline_v1.md](docs/type_upgrade_pipeline_v1.md) and
[generated/type_upgrade_pipeline_v1/README.md](generated/type_upgrade_pipeline_v1/README.md).

A fifth independent boundary batch,
`2026-10-15-type-upgrade-boundary-v1`, contains 750 `TUCZ-*` scenarios and
2,250 profile-specific SQL files. Every scenario performs two upgrades, inserts
new data between them, and compares pre-upgrade rows, post-upgrade rows,
schema, indexes, selected foreign keys, and selected statistics against a
direct final-shape reference table. It covers zero-length character/binary
types, maximum DECIMAL precision/scale, variable row-size limits, LOB overflow,
aliases, `AFTER` positions, nullability/default transitions, row formats, and
index addition after a zero-length source becomes indexable. See
[docs/type_upgrade_boundary_v1.md](docs/type_upgrade_boundary_v1.md) and
[generated/type_upgrade_boundary_v1/README.md](generated/type_upgrade_boundary_v1/README.md).

A sixth independent concurrency batch,
`2026-10-19-type-upgrade-primary-key-concurrency-v1`, contains 107 `TUCPK-*`
type transitions and a virtual matrix of 946,944 scenarios. It covers integer,
DECIMAL, BIT, character, binary, TEXT, and BLOB primary keys; `AUTO_INCREMENT`
inserts that omit the PK column; extreme counters; DDL-time and post-DDL
concurrent inserts; and explicit all-column verification. `CHAR`/`VARCHAR`
cases enforce the product contract that only 256-crossing upgrades support
`INSTANT`, while pre-256 and post-256 upgrades use `INPLACE` and expect
`INSTANT` rejection. See
[docs/type_upgrade_primary_key_concurrency_v1.md](docs/type_upgrade_primary_key_concurrency_v1.md)
and
[generated/type_upgrade_primary_key_concurrency_v1/README.md](generated/type_upgrade_primary_key_concurrency_v1/README.md).

A seventh independent DDL-concurrency batch,
`2026-10-20-inplace-ddl-unique-conflict-v1`, contains 2,304 virtual `TUCUI-*`
scenarios. It covers twelve non-`MODIFY`/non-`CHANGE` operations that support
`INPLACE, LOCK=NONE`, four unique-key conflict surfaces, four duplicate
patterns, three DDL/DML phases, four and sixteen workers, and normal and
boundary data. The runner proves real time overlap, verifies duplicate inserts
fail without interrupting DDL, and checks all stable columns, row count,
AUTO_INCREMENT, and the final schema. See
[docs/inplace_unique_conflict_v1.md](docs/inplace_unique_conflict_v1.md) and
[generated/inplace_unique_conflict_v1/README.md](generated/inplace_unique_conflict_v1/README.md).

An eighth independent FK-consistency batch,
`2026-10-20-fk-type-expansion-consistency-v1`, contains 568 `TUCFK-*`
scenarios. It covers 71 type transitions across integer, character, binary,
DECIMAL, and BIT columns, both `INPLACE` and `INSTANT`, and all four foreign
key actions. Every scenario performs full-table INSERT, UPDATE, and DELETE and
checks parent/child counts, orphan rows, FK existence, and the final column
type. See [docs/fk_type_expansion_v1.md](docs/fk_type_expansion_v1.md) and
[generated/fk_type_expansion_v1/README.md](generated/fk_type_expansion_v1/README.md).

### Mandatory full type-upgrade regression

Every type-upgrade regression must run all eight current batches and every
profile defined by each batch. Selective regression is not accepted.

```text
8 batches
23 execution streams
972,654 cases/scenarios
2,917,394 case/profile executions
2,411 SQL artifacts
```

The required order and complete SQL inventory are in
[docs/type_upgrade_full_regression.md](docs/type_upgrade_full_regression.md).
The machine-readable checklist is
[generated/type_upgrade_full_regression/inventory.tsv](generated/type_upgrade_full_regression/inventory.tsv),
and the release-gate manifest is
[generated/type_upgrade_full_regression/manifest.json](generated/type_upgrade_full_regression/manifest.json).
A regression is `PASS` only when all 23 execution units are present and every
batch-specific oracle passes; otherwise it is `INCOMPLETE` or `FAIL`.

## Test and smoke environments

```bash
pytest -q
docker compose -f docker-compose.smoke.yml up -d --wait
python3 tools/smoke_mysql_editions.py
docker compose -f docker-compose.smoke.yml down -v
```

The compose file starts two physically distinct MySQL instances for each exact
patch: one reference and one candidate. The smoke tool verifies all four
reported version numbers and server UUIDs before any differential run.

Generated runtime output belongs under `artifacts/`, which is ignored by the
repository root `.gitignore`.

## Version evidence

The original 8.0.22 review sources are recorded in
`docs/migration/mysql80_22_official_sources.md`. The 8.0.41 delta is grounded
in official MySQL 8.0 release notes, with version-sensitive additions kept out
of the 8.0.22 edition.
