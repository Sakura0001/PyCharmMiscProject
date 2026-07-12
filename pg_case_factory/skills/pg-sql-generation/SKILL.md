---
name: pg-sql-generation
description: Generate and audit exhaustive PostgreSQL 18.4 SQL compatibility tests from feature documents or SQL test requests. Use when Codex must preserve requirement traceability, enumerate every relevant object/type/statement factor without sampling, reconcile coverage, dispatch durable test-point jobs, generate regression SQL, or compare upstream PostgreSQL 18.4 output with a compatible DUT.
---

# PG SQL Generation

Treat upstream PostgreSQL 18.4 as the SQL and user-visible behavior oracle. Treat every unexplained observable difference from the DUT as a finding candidate.

## Execute the feature workflow

1. Preserve the source document and extract a traceable feature manifest. Read [analyze_feature_document.md](references/mainflow/analyze_feature_document.md).
2. Enumerate complete applicable inventories and reconcile every required obligation. Review the pinned PostgreSQL 18.4 applicability universe (183 statements, 3,357 statement-factor pairs, and 9,978 factor-value rows), resolve every row, and compile those decisions into the formal plan before run initialization. Read [design_feature_coverage_plan.md](references/mainflow/design_feature_coverage_plan.md).
3. Create one durable, resumable job per test point. The main Codex agent must use the deterministic `pg-case run next --jobs ... --limit 1` loop, assign at most one child agent to that point, wait for its artifacts to pass the state/evidence gates, and only then select another point. Read [orchestrate_test_points.md](references/mainflow/orchestrate_test_points.md).
4. Execute identical SQL on upstream PostgreSQL 18.4 and the DUT, compare the complete output exactly by default, and package findings/regression artifacts. Read [execute_differential_regression.md](references/mainflow/execute_differential_regression.md).

Do not start SQL generation while coverage reconciliation reports `missing > 0`. Prove:

```text
required = success + expected_failure + justified_na
missing = 0
```

Do not initialize a formal run from the base plan or from a pending applicability scaffold. First classify all 9,978 rows as covered or concretely justified exclusions, validate with `--require-complete`, compile a separate plan, and initialize the run with that compiled plan plus the matching applicability index. The main agent owns the immutable plan, applicability bundle, run metadata, and job transitions; a child agent may write only its assigned point artifacts and must never rewrite shared planning inputs.

Keep excluded inventory values in their axes and classify them as `justified_na` with a concrete reason. Never replace a complete relation, table, column-type, syntax, or other applicable inventory with samples or representative values.

For every plan, explicitly decide exactly four scopes: `object`, `relation`, `table`, and `column_type`. A scope is either backed by its canonical inventory group with matching count/hash, or is `not_applicable` with a concrete reason. The `table` scope is five orthogonal axes. A complete `column_type` scope requires all seven catalog dimensions: executable profiles, exact non-pseudo built-ins, automatic arrays, pseudo-type negatives, declaration aliases, typmod boundaries, and user-defined archetypes. Resolve repository inventories with `--inventory-root`; a declared subset cannot pass as complete.

Record at least these 12 mandatory risk decisions for every plan: `syntax`, `operation`, `lifecycle`, `data_profile`, `large_value_toast`, `transaction`, `partitioning`, `index_constraint_trigger`, `privilege`, `maintenance`, `concurrency`, and `restart_recovery`. Each is either `covered` with axes/test points or `not_applicable` with a concrete reason. Add feature-specific risks whenever the document exposes a separate observable boundary; do not discard WAL, MVCC, read-path, TOAST-physical, or provisioning semantics just because they are not one of the mandatory names.

The bundled storage cross-product template currently expands deterministically to 3,175 obligations (2,787 success, 153 expected failure, 235 justified N/A, 0 missing) across 37 axes and 25 test points. This proves only the classification closure of those declared axes; it is neither a universal target count nor proof that all 9,978 statement-factor-values were reviewed for the feature. Feature-local inline axes must record derivation, feature and PG18 source locators, an exclusion policy, and source/semantic review status. COPY protocol ingestion, privileged object administration, extension files, logical replication, extension table AMs, trusted base types, postgres_fdw, LZ4, multisession schedules, and fault injection remain executable obligations: a missing named harness blocks execution and is never justified N/A. Internal ObjectType/relkind members are tested through their owning SQL DDL plus catalog observability, never invented standalone syntax. Each obligation carries an execution route: `basic_psql`, or `external_isolated` plus a risk-declared harness ID; the basic differential command must refuse external cases. Create exactly one durable job per test point. Every normal `run transition` requires run-root-relative `--evidence`. Job-store schema v3 records every evidence file's SHA-256 and revalidates it on later transitions and status. `generated` evidence must contain the exact case-manifest and SQL set for every executable obligation in that point; one sample case cannot advance a multi-obligation job. Run case reconciliation with both `--cases` and `--artifact-root` so referenced SQL files are proven to exist inside the run.

Each executable obligation has exactly one case manifest and exactly one deterministic SQL program. Bind the exact SQL bytes with top-level `sql_sha256`; do not reuse a SQL path or identical SQL content for different obligations. Formal cases use `comparison.mode: exact_text`, `oracle: upstream-postgresql-18.4`, and `require_identical: true`. An `expected_failure` case also declares the five-character upstream SQLSTATE.

For `execution_harness: external-copy-ingest`, make that one manifest-bound SQL file a complete psql COPY program: every direct COPY must be `COPY ... FROM STDIN;`, followed on the next line by at least one inline payload line and a standalone `\.` terminator. Do not use `\copy`, an external payload path, `PROGRAM`, `COPY TO`, a second payload artifact, a pipe, or out-of-band stdin. The isolated harness must execute the exact declared SQL file on each endpoint; its `sql_sha256` therefore binds the COPY command, payload, terminator, setup, verification, and cleanup bytes together.

Use formal execution only with all three bindings: `pg-case run differential <run-sql> --run-root <run> --case-id <id> --case-manifest <run-manifest> ...`. The manifest must be under the current run and must identify that single SQL and SHA. Formal execution is exact-only and always stops on the first error. A `success` case requires upstream return code zero; an `expected_failure` case requires a nonzero upstream result with exactly one verbose terminal `ERROR`/`FATAL`/`PANIC` diagnostic whose SQLSTATE is the declared value. NOTICE/WARNING text and ambiguous multiple terminal diagnostics never satisfy the oracle. Identical reference/DUT failures do not rescue an invalid upstream outcome oracle.

Before either database receives SQL, the runner locks and reserves the case artifact set, re-loads the immutable run execution profile and case manifest, requires their digest/settings/case/SQL path+SHA bindings to remain unchanged, reads one immutable SQL snapshot, and rechecks its manifest SHA. It writes through staging and publishes `comparisons/<case-id>.json` last as the completion marker. Every execution and comparison JSON binds `execution_profile_sha256` (the run digest, or explicit `null` for a legacy unprofiled run), and job/status validation recomputes the digest plus each side's profile service/database/expected-system-identifier/expected-current-user binding. Endpoint identity is checked before execution, inside the same psql session as the SQL, and after execution; pre/session/post must agree, both systems must be PostgreSQL 18.4 targets, reference/DUT system identifiers must differ and exactly match their immutable profile anchors, and database/current_user must match (including the expected profile user). The basic runner fixes client encoding to UTF8.

Every point uses `jobs/audits/<point>.json`, `jobs/readiness/<point>.json`, and `jobs/lint/<point>.json` fixed-schema evidence. These records bind the plan, feature, point and exact obligation list; audit/readiness require zero unresolved items/blockers, while lint re-reads every manifest and SQL, recomputes SHA-256, validates the Huawei header, catalog-output stability, and route-specific SQL safety. An arbitrary `{safe: true}` self-report cannot advance a job.

If a covered risk names `execution_harness`, `ready` evidence also contains `jobs/harnesses/<harness-id>.json` plus its bound implementation file under `jobs/harnesses/implementations/`. The record binds the run execution-profile SHA, implementation path/SHA, non-empty event model and probe; its fingerprint covers all four values. The gate validates structure, plan/profile/implementation binding, self-consistency and later immutability. It does not independently attest that the probe ran, so the external harness/operator still owns probe truth and runtime verification.

Every non-passing comparison must have one `differential_finding` that binds its SQL, reference execution, DUT execution, and comparison by run-relative path plus SHA-256. `packaged` requires one `regression_package` JSON that lists every case in the point and binds each regression SQL and upstream exact expected transcript by SHA-256. Status and packaging revalidate the complete chain.

## Handle other requests

- Route a natural-language SQL request through [generate_sql_from_request.md](references/mainflow/generate_sql_from_request.md).
- Audit a lifecycle plan with [audit_lifecycle_plan.md](references/mainflow/audit_lifecycle_plan.md).
- Generate SQL for an audited point with [write_sql_program.md](references/mainflow/write_sql_program.md).
- Create or update a PostgreSQL 18.4 statement reference with [create_statement_reference.md](references/mainflow/create_statement_reference.md).

## Load only relevant knowledge

- Read [compatibility_profile.yaml](references/common/compatibility_profile.yaml), [statement_support_inventory.yaml](references/common/statement_support_inventory.yaml), [pg18_factor_catalog.md](references/common/pg18_factor_catalog.md), and [pg18_type_catalog.md](references/common/pg18_type_catalog.md) when planning PostgreSQL 18.4 coverage. The bundled factor-value ledger has 9,978 rows; query only the needed statement with `rg -n '^<statement-key>\t' references/common/postgresql_18_4_factor_audit.tsv` instead of loading the whole file.
- Read [combinations/README.md](references/combinations/README.md) and only the matching statement matrices for required baseline combinations.
- Read only the matching `references/statements/<category>/<domain>/<statement>.md` files.
- Read the needed output, validation, lifecycle, factor, and naming policies under `references/common/`.
- Copy and complete the YAML templates under `assets/templates/`; do not edit the templates in place.
- Use matching base-object templates under `assets/objects/` when they are valid for the planned axis assignment.

## Enforce boundaries

- Test strict SQL/user-visible PostgreSQL 18.4 compatibility only.
- Treat the type catalog's 85 canonical entries as finite executable core profiles, not every `pg_type` row; add source-derived concrete/automatic-array axes when the feature is sensitive to them.
- Before differential execution, require preflight, same-psql-session, and postflight identities to agree; require both endpoints to report `server_version_num=180004`, require non-empty and different `system_identifier` values, require matching database/current_user, fix basic client encoding to UTF8, and compare the complete return-code/stdout/stderr transcript with formal exact-only semantics. Execute the entire SQL twice per endpoint and require byte-identical `(returncode, stdout, stderr)` before accepting the cross-endpoint result.
- Leave storage-layer log inspection and root-cause analysis to the user; record enough SQL and output evidence for that work.
- Store each run under `artifacts/runs/<run-id>/`; never clear another run to start or resume work.
- Never write passwords, tokens, connection strings containing secrets, or real credentials into manifests, SQL, logs, findings, prompts, or archives. Refer to libpq service names or an external secret provider.
- The basic runner is not a server sandbox. Use a dedicated role without superuser, CREATEDB, CREATEROLE, REPLICATION, BYPASSRLS, `pg_read_server_files`, `pg_write_server_files`, `pg_execute_server_program`, or membership in a role carrying those capabilities. Its lexer rejects every user psql meta command, `COPY PROGRAM`, and `COPY FROM STDIN` data mode, but cannot sandbox dynamic SQL, procedural languages, extensions, or server functions. Use a separately isolated, explicitly authorized external harness for privileged cases, COPY STDIN, host programs, multiple sessions, restart, fault injection, or cluster control. The `external-copy-ingest` route is specifically for manifest-bound inline COPY payloads; use a different declared external harness for server files or programs. Privilege rejection applies only to `basic_psql`; an `external_isolated` harness may prove an explicitly required privileged identity, but must still prove the full PostgreSQL 18.4 identity structure, different system identifiers, matching database/current_user, and the same profile-bound artifact schema.
- Do not claim multi-session, restart, fault-injection, or real-database execution occurred unless an appropriate external harness actually performed it.
- Static PG18.4 catalog review covers 183 statements, 3,357 statement-factor pairs, and 9,978 factor-value rows. All 105 required parity points across 53 affected matrices explicitly bind their affected values (132 bindings), but `runtime_verified_statements=0`; never present static readiness as rendered, exhaustive, or runtime verification.
