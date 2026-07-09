---
name: pg-sql-generation
description: Use when generating PostgreSQL 16.4 SQL test cases, designing lifecycle plans, auditing statement coverage references, or using bundled base-object templates.
---

# PG SQL Generation

Use this skill when converting a natural-language PostgreSQL SQL test request into lifecycle plans, statement coverage references, generation programs, audits, or complete SQL test cases.

## Workflow Navigation

- For end-to-end SQL generation from a request, read `references/mainflow/generate_sql_from_request.md`.
- For feature-level repeated execution, diagnosis, and feedback promotion, read `references/mainflow/run_feature_test_loop.md`.
- For lifecycle plan review, read `references/mainflow/audit_lifecycle_plan.md`.
- For generating batch SQL programs from a plan, read `references/mainflow/write_sql_program.md`.
- For creating or completing statement references, read `references/mainflow/create_statement_reference.md`.
- For feature test intake, use `references/templates/feature_test_intake_template.md`.
- For shared output, factor, lifecycle, validation, and naming rules, read only the needed files under `references/common/`.
- For 查询语句 or any feature that uses query verification, read
  `references/common/query_context_policy.md` before planning fixtures, data distribution, indexes,
  hints, optimizer settings, statistics, parameterization, MVCC, parallelism, rewrite behavior, or query oracles.
- For query result, row order, `EXPLAIN`, hint/no-hint, and `plan_observation` oracle design, also read
  `references/common/query_oracle_policy.md`.
- For loop execution contracts and artifacts, read `references/common/execution_loop_policy.md`.
- For failure clustering rules, read `references/common/failure_diagnosis_policy.md`.
- For converting loop feedback into reviewed derived extensions, read `references/common/feedback_promotion_policy.md`.
- For statement-specific syntax, factors, coverage policy, and constraints, read only the needed file under `references/statements/<category>/<domain>/<statement>.md`.
- For statement factor combination matrices, read `references/combinations/README.md`
  and then the matching `references/combinations/<category>/<domain>/<statement_key>.yaml`.

## Directory Roles

- `references/mainflow/` contains agent workflows.
- `references/common/` contains shared SQL generation rules.
- `references/statements/` contains PostgreSQL statement references grouped first by SQL category, then by domain.
- `references/combinations/` contains audited baseline statement combination matrices.
- `references/templates/` contains reference authoring templates.
- `assets/templates/` contains output templates that may be copied or consumed.
- `assets/objects/` contains bundled base-object SQL templates used by generation workflows.

## Important Constraints

- Statement references are not independent Codex skills; they are reference files for this skill.
- Treat paths inside this skill as relative to the skill root unless explicitly described as generated output paths.
- Keep statement-specific behavior in statement references; any helper code or runner should stay generic.
- Generated `artifacts/` paths are relative to the current execution workspace, not to this skill directory.
- Loop-discovered cases are derived extensions until reviewed; they cannot replace required baseline combination coverage.
