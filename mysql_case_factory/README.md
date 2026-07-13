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
