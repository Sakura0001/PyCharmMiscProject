# Project Structure

`mysql_case_factory` is a sibling project to `pg_case_factory` in the shared
monorepo. It contains a MySQL-specific Codex skill plus a small reusable Python
engine.

```text
mysql_case_factory/
├─ README.md
├─ PROJECT_STRUCTURE.md
├─ pyproject.toml
├─ docs/
│  └─ migration/
├─ skills/
│  └─ mysql-sql-generation/
├─ src/
│  └─ mysql_case_factory/
├─ tests/
└─ tools/
```

## Skill Layout

```text
skills/mysql-sql-generation/
├─ SKILL.md
├─ agents/
├─ assets/
│  ├─ objects/
│  └─ templates/
└─ references/
   ├─ common/
   ├─ combinations/
   ├─ mainflow/
   ├─ statements/
   └─ templates/
```

The skill references are the source of truth for SQL semantics. Python code is
kept generic and must not hard-code a MySQL statement-specific lifecycle or
factor list.

## Migration Review Files

- `docs/migration/factor_review_manifest.tsv` tracks PostgreSQL reference files
  and their MySQL 8.0.22 migration status.
- `docs/migration/subagent_review_template.md` defines the required sub-agent
  review format.
- `docs/migration/mysql80_22_official_sources.md` records official source URLs
  and the version-boundary rule.
