---
name: mysql-sql-generation
description: Use when generating MySQL 8.0.22 SQL test cases, designing lifecycle plans, auditing statement coverage references, or using bundled MySQL base-object templates.
---

# MySQL SQL Generation

Use this skill when converting a natural-language MySQL SQL test request into
lifecycle plans, statement coverage references, generation programs, audits, or
complete SQL test cases.

## Workflow Navigation

- For end-to-end SQL generation from a request, read
  `references/mainflow/generate_sql_from_request.md`.
- For lifecycle plan review, read
  `references/mainflow/audit_lifecycle_plan.md`.
- For generating batch SQL programs from a plan, read
  `references/mainflow/write_sql_program.md`.
- For creating or completing statement references, read
  `references/mainflow/create_statement_reference.md`.
- For shared output, factor, lifecycle, validation, and naming rules, read only
  the needed files under `references/common/`.
- For statement-specific syntax, factors, coverage policy, and constraints,
  read only the needed file under
  `references/statements/<category>/<domain>/<statement>.md`.
- For statement factor combination matrices, read
  `references/combinations/README.md` and then the matching
  `references/combinations/<category>/<domain>/<statement_key>.yaml`.

## Version Boundary

This skill targets MySQL Community Server 8.0.22. Current MySQL 8.0 online
manual pages may include features introduced after 8.0.22. Before adding a
version-sensitive factor, check the MySQL 8.0 release notes and record the
official source URL in the statement reference.

## Directory Roles

- `references/mainflow/` contains agent workflows.
- `references/common/` contains shared SQL generation rules.
- `references/statements/` contains MySQL statement references grouped first by
  SQL category, then by domain.
- `references/combinations/` contains audited baseline statement combination
  matrices.
- `references/templates/` contains reference authoring templates.
- `assets/templates/` contains output templates that may be copied or consumed.
- `assets/objects/` contains bundled base-object SQL templates used by
  generation workflows.

## Important Constraints

- Statement references are not independent Codex skills; they are reference
  files for this skill.
- Treat paths inside this skill as relative to the skill root unless explicitly
  described as generated output paths.
- Keep statement-specific behavior in statement references; helper code and
  runners must stay generic.
- Generated `artifacts/` paths are relative to the current execution workspace,
  not to this skill directory.
