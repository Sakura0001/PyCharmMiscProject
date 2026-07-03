# mysql_case_factory

MySQL 8.0.22 SQL factor library and SQL-first case generation scaffold.

This project mirrors the `pg_case_factory` architecture but keeps MySQL-specific
knowledge in a dedicated Codex skill:

- `skills/mysql-sql-generation/SKILL.md`
  Skill entry point and navigation.
- `skills/mysql-sql-generation/references/mainflow/`
  Request-to-plan, plan audit, and SQL program generation workflow references.
- `skills/mysql-sql-generation/references/common/`
  MySQL 8.0.22 factor policy, naming, lifecycle, validation, type, and global
  factor catalogs.
- `skills/mysql-sql-generation/references/statements/`
  Statement references grouped by SQL category and domain.
- `skills/mysql-sql-generation/references/combinations/`
  Auditable baseline combination matrices.
- `skills/mysql-sql-generation/assets/objects/`
  Bundled MySQL object templates.
- `src/mysql_case_factory/`
  Minimal generic engine for discovery, loading, factor expansion, rendering,
  and artifact management.

The migration from PostgreSQL is intentionally evidence-driven. PostgreSQL
statement references are not copied wholesale into the MySQL library. Each
statement and factor must be reviewed against MySQL Community Server 8.0.22
official documentation before it is retained, rewritten, or dropped.

## MySQL 8.0.22 Documentation Boundary

Primary official sources are listed in
`docs/migration/mysql80_22_official_sources.md`. Current MySQL 8.0 online
manual pages can include features added after 8.0.22, so version-sensitive
syntax must be checked against MySQL 8.0 release notes before being accepted.

## Artifacts

Generated runtime output belongs under `artifacts/`, which is ignored by the
repository root `.gitignore`.
