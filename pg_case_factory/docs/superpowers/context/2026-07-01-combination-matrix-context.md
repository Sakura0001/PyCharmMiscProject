# Combination Matrix Migration Context

## Current Rules

- Statement reference defines factors.
- Combination matrix defines baseline SQL combinations.
- Baseline audit must pass before extension inference.
- Extensions are allowed after baseline audit and must be marked.
- Extensions never count as required coverage.

## Required Files For Subagents

- This context file.
- The implementation plan:
  `docs/superpowers/plans/2026-07-01-full-factor-combination-matrix.md`.
- The target statement reference file.
- The shared matrix schema:
  `skills/pg-sql-generation/references/combinations/_shared/statement_combination_matrix_schema.yaml`.
- The shared coverage inventory:
  `skills/pg-sql-generation/references/combinations/_shared/coverage_inventory.yaml`.
- The PG16 type catalog:
  `skills/pg-sql-generation/references/common/pg16_type_catalog.md`.
- The audit tool:
  `tools/audit_combination_matrix.py`.
- The migration status file:
  `docs/pg16_combination_matrix_migration_status.md`.

## Known Local State

`1.txt` may be modified by the user. Do not stage, commit, or rewrite it
unless explicitly requested.

## Current Completed Baseline

- Shared combination matrix schema and coverage inventory are available.
- PG16 type catalog is available.
- Combination matrix audit tool is available.
- `CREATE INDEX` has a formal matrix at
  `skills/pg-sql-generation/references/combinations/ddl/index/create_index.yaml`.
- The current root audit command is:
  `python3 tools/audit_combination_matrix.py --root .`.

## Worker Contract

- Work only on `main`.
- Run `git status --short --branch` before editing.
- Do not stage unrelated files.
- Run the matrix audit for every matrix touched.
- Commit and push each completed batch.
