# Feature Association Multi-Agent Implementation Plan

> **For Codex:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development to implement this plan task-by-task.

**Goal:** Build a fail-closed, multi-agent feature-association planner that turns a short feature document into independently proved MySQL 8.0.22 and 8.0.41 plans, stops at an external execution-decision gate, and uses `ALTER TABLE ADD COLUMN` as the first complete InnoDB `V × 33` golden feature.

**Architecture:** Preserve every existing v1 contract and obligation ID, then layer typed planning contracts, closed agent envelopes, an immutable planning ledger/bundle, rule-first association knowledge, deterministic set proofs, semantic dry-rendering, blind audit, and external execution authorization on top. Planning and execution remain separate capability domains. Edition assets are independent and digest-pinned; deterministic compilers, rather than model confidence, prove completeness.

**Tech Stack:** Python 3.10+, frozen dataclasses, PyYAML, pytest, existing `contracts`/`coverage`/`artifact_store`/`formal_run`/`jobs`/`differential` foundations, JSON/YAML/TSV edition assets, SHA-256 canonical documents, file locks and atomic `os.replace` publication.

**Working directories:** Run Python/test commands from the project root `<repo>/mysql_case_factory`. Run every `git add`/`git commit`/`git push` command from the monorepo root `<repo>`. Stage and commit only `mysql_case_factory/**`. Run every test with `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3 -m pytest -q -p no:cacheprovider`. Push every successful implementation commit before starting the next milestone.

---

## Task 1: Planning contracts and v1 compatibility

**Files:**

- Create: `src/mysql_case_factory/planning_contracts.py`
- Modify: `src/mysql_case_factory/contracts.py`
- Modify: `src/mysql_case_factory/__init__.py`
- Create: `tests/test_planning_contracts.py`
- Create: `tests/fixtures/coverage/legacy_plan_v1.yaml`
- Create: `tests/fixtures/coverage/legacy_obligations.json`

**Step 1: Write failing contract and compatibility tests**

Cover strict closed schemas for `ArtifactBinding`, `FeatureSpec`, impact nodes/edges, `FactorDecision`, `PlanCaseBlueprint`, `DryRenderArtifact`, `AuditAttestation`, `ExecutionBrief`, `PlanningBundleManifest`, `ExecutionDecision`, and `ExecutionHandoff`. `ExecutionBrief` must carry exact counts by edition/suite, full and partial cost estimates, endpoint/topology/privilege/disk/time/concurrency/harness requirements, safety blockers, known risks, and the explicit confidence lost by every partial proposal. Add `CoverageExpectedCounts` and optional `CoverageContract` to `TestPoint`. Assert that a legacy plan without `coverage_contract` serializes byte-for-byte as its fixture and produces exactly the frozen obligation IDs.

**Step 2: Run RED**

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3 -m pytest -q -p no:cacheprovider tests/test_planning_contracts.py tests/test_feature_contracts.py
```

Expected: import/constructor failures because the new contracts do not exist.

**Step 3: Implement the minimal strict contracts**

Use frozen dataclasses, duplicate-key-safe loaders, portable relative paths, enumerated statuses/policies, canonical JSON SHA-256, and `to_dict()` methods that omit absent optional v2 fields. Reject unknown keys, weak digests, duplicate IDs, missing reasons/sources for new non-success outcomes, self-referential bundle entries, decision paths inside a bundle, and unresolved questions marked complete.

**Step 4: Run GREEN and regression tests**

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3 -m pytest -q -p no:cacheprovider tests/test_planning_contracts.py tests/test_feature_contracts.py tests/test_coverage.py
```

**Step 5: Commit and push**

```bash
git add mysql_case_factory/src/mysql_case_factory/planning_contracts.py mysql_case_factory/src/mysql_case_factory/contracts.py mysql_case_factory/src/mysql_case_factory/__init__.py mysql_case_factory/tests/test_planning_contracts.py mysql_case_factory/tests/fixtures/coverage
git commit -m "feat(mysql-case-factory): add planning contracts"
git push -u origin codex/feature-association-agents
```

## Task 2: Exact coverage-contract proofs

**Files:**

- Modify: `src/mysql_case_factory/coverage.py`
- Modify: `src/mysql_case_factory/feature_plan.py`
- Modify: `tests/test_coverage.py`

**Step 1: Write failing mutation tests**

Add tests for a 2×3 `full_cross` in which one assignment is removed and another duplicated, an axis value is replaced without changing count, axes are split across test points, policy is downgraded to pairwise, expected counts are forged, a conditional tuple loses one member, and a factor has two owning suites.

**Step 2: Run RED**

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3 -m pytest -q -p no:cacheprovider tests/test_coverage.py
```

Expected: new proof APIs are absent and mutations are not rejected.

**Step 3: Implement set proof APIs**

Add `CoverageContractProof`, `CoverageCompilation`, `assignment_set_sha256()`, `prove_coverage_contract()`, and `compile_coverage_plan()`. Build the theoretical set directly from frozen inventories and the actual set independently from obligations. Require exact set equality, unique assignments, inventory/count/digest agreement, per-condition proofs, exact outcome accounting, and unique `owning_suite_id`. Keep `expand_coverage_plan()` and all v1 behavior stable.

**Step 4: Run GREEN**

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3 -m pytest -q -p no:cacheprovider tests/test_coverage.py tests/test_feature_contracts.py
```

**Step 5: Commit and push** using only the three listed files.

## Task 3: Closed agent protocol and capability isolation

**Files:**

- Create: `src/mysql_case_factory/agent_protocol.py`
- Create: `src/mysql_case_factory/planning_capabilities.py`
- Create: `tests/test_agent_protocol.py`
- Create: `tests/test_planning_execution_isolation.py`

**Step 1: Write failing tests**

Test exact input-digest echo, output-path equality, expiry, missing/extra files, symlink/path escape, stale inputs, atomic all-or-nothing publication, and blind-draft envelopes that reject candidate-plan inputs. Use spies that fail if a planning adapter exposes MySQL, Docker, formal-run, materialization, scheduler, differential, subprocess, socket, or direct-execute capabilities.

**Step 2: Run RED**, then implement `AgentTaskEnvelope`, `AgentTaskResult`, validation, staging publication, role/action enums, and a whitelist-only planning capability adapter. `allowed_actions` is audit metadata; object capability injection is the enforcement layer.

**Step 3: Run GREEN**

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3 -m pytest -q -p no:cacheprovider tests/test_agent_protocol.py tests/test_planning_execution_isolation.py
```

**Step 4: Commit and push** the four listed files.

## Task 4: Durable planning ledger and immutable bundle

**Files:**

- Create: `src/mysql_case_factory/planning_ledger.py`
- Create: `src/mysql_case_factory/planning_bundle.py`
- Create: `tests/test_planning_ledger.py`
- Create: `tests/test_planning_bundle.py`

**Step 1: Write failing state/concurrency tests**

Exercise every approved state transition, typed blocked/resume states, rework to owning stage, open finding rejection, source-revision immutability, two-writer races, crash-safe JSON, bundle-entry containment/digests, and the rule that changing a pending decision never changes the bundle digest.

**Step 2: Run RED**, then implement a file-locked `PlanningRunLedger` with temp-file + `os.replace`, monotonic revision, immutable event records, envelope/result binding, and separate bundle/decision digests. Implement manifest construction/validation that excludes itself, `decision/`, and `planning_run.json`.

**Step 3: Run GREEN**

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3 -m pytest -q -p no:cacheprovider tests/test_planning_ledger.py tests/test_planning_bundle.py
```

**Step 4: Commit and push** the four listed files.

## Task 5: General rule-first factor association

**Files:**

- Create: `src/mysql_case_factory/feature_association.py`
- Create: `tests/test_feature_association.py`
- Create in each edition: `references/common/mandatory_factor_domain_policy.yaml`
- Create in each edition: `references/common/feature_association_knowledge.yaml`
- Modify: both `edition.yaml`

**Step 1: Write failing semantic and metamorphic tests**

The short input “`ALTER TABLE ADD COLUMN` is enhanced” must infer `innodb_table_recipe` and `added_column_type` without words such as “all tables/types”. Synonyms must produce the same normalized factor set and digest. A non-table fixture must not receive table/type axes. All 14 mandatory domains must end as `covered` or evidenced `justified_na`; `unknown` blocks. Every factor needs one owner and a requirement-reachable trigger path.

**Step 2: Run RED**, then port the proven PG hybrid rule-first pattern into typed MySQL rules. Normalize operation/object/phase/risk/dependency/observable tags; traverse forward implications and reverse mandatory-domain checks. Never special-case raw feature prose in the compiler. Mark model suggestions as derived extensions that cannot satisfy baseline obligations.

**Step 3: Bind independent edition assets** with kind/count/full-file digest entries in each edition manifest.

**Step 4: Run GREEN**

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3 -m pytest -q -p no:cacheprovider tests/test_feature_association.py tests/test_editions.py tests/test_edition_knowledge.py
```

**Step 5: Commit and push** only association code/tests and the two edition asset sets.

## Task 6: Canonical InnoDB shape universe and recipe closure

**Files:**

- Modify: `src/mysql_case_factory/inventory.py`
- Create: `tests/test_innodb_recipe_inventory.py`
- Modify: `tests/test_inventory.py`
- Create in each edition: `references/common/innodb_table_shape_golden_policy.yaml`
- Create in each edition: `references/common/innodb_table_shape_universe.yaml`
- Create in each edition: `references/common/innodb_table_shape_applicability.yaml`
- Create in each edition: `references/common/innodb_table_recipe_inventory.yaml`
- Create: `tools/build_innodb_recipe_inventory.py`
- Modify: both `edition.yaml`

**Step 1: Write failing inventory and mutation tests**

Require deterministic candidate IDs from complete ordered assignments, full candidate reconciliation, unique recipe IDs, explicit `ENGINE=InnoDB`, no MyISAM/MEMORY, evidence-bound exclusions, constructibility fields, unique semantic setup signatures, and category closure for permanent/temporary, all listed partition modes and valid subpartition shapes, four row formats, three tablespace forms, PK forms, index forms, FK/check/generated forms. Delete, replace, duplicate, reorder, path-escape, and golden-digest mutations must fail.

**Step 2: Run RED**, then add structured inventory loaders alongside the existing scalar APIs: `load_shape_universe()`, `generate_shape_candidates()`, `load_recipe_inventory()`, `reconcile_recipe_inventory()`, `resolve_inventory_records()`, and `inventory_records_sha256()`.

**Step 3: Author a genuinely factorized canonical universe** with frozen ordered axes for persistence, partition/subpartition shape, row format, tablespace shape, primary-key shape, secondary-index shape, and related-object shape. Generate the complete Cartesian candidate set before applying any rule. `tools/build_innodb_recipe_inventory.py` must deterministically materialize every candidate into the recipe inventory as either `included` with a concrete recipe or `structurally_excluded`; the separately manifest-bound applicability inventory carries every exclusion rule, official evidence, and review state. The generator must be streaming/deterministic so scale cannot justify sampling. Keep LOCK, privilege, concurrency, and other feature conditions outside the shape universe. Every category in the approved spec must be represented, and no valid cross-dimension shape may be excluded merely to reduce `V`.

**Step 4: Run GREEN**

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3 -m pytest -q -p no:cacheprovider tests/test_inventory.py tests/test_innodb_recipe_inventory.py tests/test_editions.py
```

**Step 5: Commit and push** the loader/tests and both independent edition inventories.

## Task 7: Structured 33-type inventories

**Files:**

- Create: `tests/test_added_column_type_inventory.py`
- Modify: `src/mysql_case_factory/inventory.py`
- Create in each edition: `references/common/added_column_type_inventory.yaml`
- Modify: both `edition.yaml`

**Step 1: Write failing tests** for the exact stable 33 IDs (9 numeric, 10 string, 5 temporal, 1 JSON, 4 spatial, 4 blob), ordered full-record digest, canonical DDL, semantic type, legal seed, boundaries, metadata oracle, data oracle, evidence and review state. Same-count replacement, duplicate, missing field, ID-only digest, and cross-edition path reuse must fail.

**Step 2: Run RED**, implement `load_added_column_type_inventory()`, author the two independent records, and bind their counts/digests in edition manifests.

**Step 3: Run GREEN**

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3 -m pytest -q -p no:cacheprovider tests/test_added_column_type_inventory.py tests/test_inventory.py tests/test_editions.py
```

**Step 4: Commit and push** the exact files.

## Task 8: ADD COLUMN golden compiler and conditional suites

**Files:**

- Modify: `src/mysql_case_factory/matrix_generation.py`
- Modify: `tools/build_edition_templates.py`
- Create: `tests/test_add_column_golden_plan.py`
- Modify: `tests/test_matrix_generation.py`
- Modify: `tests/test_edition_templates.py`
- Create in each edition: `references/common/add_column_conditional_suite_inventory.yaml`
- Create in each edition: `assets/templates/golden_add_column_feature_manifest_template.yaml`
- Create in each edition: `assets/templates/golden_add_column_coverage_plan_template.yaml`
- Modify: both `edition.yaml`

**Step 1: Write failing golden/mutation tests**

Each edition must compile one primary test point with exactly `[innodb_table_recipe, added_column_type]`, `full_cross`, no conditions, and set equality `V_edition × 33`. Assert recipe/type counts and digests, theoretical/actual assignment digests, exact outcome counts, recipe-major/type-minor order, baseline ADD context, and one factor owner. Reject split points, addition instead of multiplication, post-filtering, pairwise/sample/rotation, same-count substitution, and deletion from every conditional suite.

**Step 2: Run RED**, then add `load_feature_association_knowledge()`, `associate_feature_factors()`, and `compile_associated_feature_matrix()`. Keep `generate_matrix_for_reference()` v1 behavior unchanged. Compile each required conditional bullet from its frozen inventory with its own selector, policy, expected set/digest/count, owner, and mutation witness; do not multiply it into `V`.

**Step 3: Run GREEN**

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3 -m pytest -q -p no:cacheprovider tests/test_add_column_golden_plan.py tests/test_matrix_generation.py tests/test_edition_templates.py
```

**Step 4: Commit and push** compiler, templates, tests, and edition suite inventories.

## Task 9: Exact edition evidence and positional INSTANT witness

**Files:**

- Create: `src/mysql_case_factory/version_claims.py`
- Create: `tests/test_add_column_version_witness.py`
- Create: `tests/test_capture_mysql_8022_witness.py`
- Create: `tools/capture_mysql_8022_witness.py`
- Create in each edition: `references/common/add_column_version_claims.yaml`
- Create in 8.0.22 edition: `references/common/evidence/alter_add_column_instant_first_transcript.yaml`
- Modify: `src/mysql_case_factory/version_delta.py`
- Modify: `tests/test_version_delta.py`
- Modify: both `edition.yaml`

**Step 1: Freeze evidence** from the official 8.0.29 release note, InnoDB online-DDL manual, and server error reference, including retrieval locator and content digest. Add a developer-only capture tool that refuses any server other than exact `8.0.22`, runs only the frozen witness in an isolated scratch schema, normalizes the single terminal error without credentials, and writes a digest-bound transcript for review. It is never imported by the planner and is not a planning capability.

Acquire the prerequisite with an external login path and import the reviewed result:

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3 tools/capture_mysql_8022_witness.py --mysql-bin mysql --login-path mysql8022 --output /tmp/mysql-8.0.22-add-column-witness.yaml
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3 tools/capture_mysql_8022_witness.py --verify-import /tmp/mysql-8.0.22-add-column-witness.yaml --output editions/mysql_8_0_22/skills/mysql-8-0-22-sql-generation/references/common/evidence/alter_add_column_instant_first_transcript.yaml
```

If exact 8.0.22 access is unavailable or the transcript cannot be reviewed, the claim and planning run must remain `planning_blocked_evidence_conflict`; this milestone and the overall golden acceptance may not be reported complete. Never guess the errno/message from a generic manual.

**Step 2: Write failing tests** proving the delta is predicate-level (`operation + FIRST + INSTANT`), not a false statement-wide or single-value change. 8.0.22 requires exactly one terminal diagnostic with frozen errno, `0A000`, and message contract; 8.0.41 requires success and ordinal position 1. Missing transcript/retrieval digest or copied cross-edition conclusions must block review-complete.

**Step 3: Run RED**, implement strict claim loaders and a closed added/changed/removed/unchanged interaction delta without changing correct existing single-factor `unchanged` entries.

**Step 4: Run GREEN**

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3 -m pytest -q -p no:cacheprovider tests/test_capture_mysql_8022_witness.py tests/test_add_column_version_witness.py tests/test_version_delta.py tests/test_editions.py
```

**Step 5: Commit and push** exact evidence/claim files and code/tests.

## Task 10: Lifecycle blueprints and semantic dry-render

**Files:**

- Create: `src/mysql_case_factory/blueprints.py`
- Modify: `src/mysql_case_factory/renderer.py`
- Create: `tests/test_blueprints.py`
- Create: `tests/test_dry_render.py`

**Step 1: Write failing reconciliation/mutation tests** requiring one blueprint per executable obligation, none for `justified_na`, and setup/target/verify/cleanup for every blueprint. Dry-render every primary recipe/type combination and the version witness. Reject assignment-only changes, universal-INT collapse, recipe setup collapse, wrong table/column/type, missing cleanup, mismatched oracle, credentials/endpoints/routes, or runnable formal-case metadata.

**Step 2: Run RED**, then implement typed blueprint compilation, a narrow canonical MySQL planning AST, symbolic identifiers, `dry_render_blueprint()`, and an independent `verify_dry_render_artifact()`. Parse back the emitted preview into the narrow AST and compare semantic signatures/digests; do not trust copied assignment metadata.

**Step 3: Run GREEN**

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3 -m pytest -q -p no:cacheprovider tests/test_blueprints.py tests/test_dry_render.py
```

**Step 4: Commit and push** the four listed files.

## Task 11: Blind audit, orchestration, and plan-first CLI

**Files:**

- Create: `src/mysql_case_factory/planning_audit.py`
- Create: `src/mysql_case_factory/planning_orchestrator.py`
- Modify: `src/mysql_case_factory/cli.py`
- Create: `tests/test_planning_audit.py`
- Create: `tests/test_planning_orchestrator.py`
- Modify: `tests/test_mysql_cli.py`

**Step 1: Write failing workflow tests**

Prove that a resolvable document reaches an immutable bundle and `execution_decision_pending`, unresolved scope/evidence reaches a typed block, repeat input produces identical normalized plan digests, and no execution-capable spy is touched. Freeze blind draft before candidate-plan access, then require set diff, lifecycle audit, finding closure, exact bundle manifest, per-edition/suite execution brief, and a pending decision. Any missing/excess factor or blueprint phase returns to the owning stage.

**Step 2: Run RED**, then implement logical requirement, evidence, association, compiler, lifecycle, coverage-auditor, lifecycle-auditor, and gatekeeper roles through closed envelopes. The orchestrator is the sole ledger writer and atomically publishes only validated role results.

**Step 3: Add CLI commands** `planning start`, `planning status`, `planning audit`, and `planning decide`. Make edition mandatory only for existing single-edition commands; planning analyzes both editions. `planning decide` writes an external envelope/handoff and never starts execution.

**Step 4: Run GREEN**

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3 -m pytest -q -p no:cacheprovider tests/test_planning_audit.py tests/test_planning_orchestrator.py tests/test_mysql_cli.py tests/test_planning_execution_isolation.py
```

**Step 5: Commit and push** the six listed files.

## Task 12: Central execution authorization and formal-run binding

**Files:**

- Create: `src/mysql_case_factory/execution_gate.py`
- Modify: `src/mysql_case_factory/formal_run.py`
- Modify: `src/mysql_case_factory/artifact_store.py`
- Create: `tests/test_execution_gate.py`
- Create: `tests/test_formal_run_authorization.py`
- Modify: `tests/test_artifact_runs.py`

**Step 1: Write failing fail-before-side-effect tests**

For every action enum—materialize, formal init, scheduler, job execute, differential, external handoff, direct execute—reject missing, pending, declined, deferred, expired/not-yet-valid, integrity-invalid, bundle-digest, edition, full/partial scope, obligation-subset, and resource-limit mismatches before creating a directory or calling subprocess. Changing any source/knowledge/inventory/recipe/type/renderer/plan byte invalidates approval.

**Step 2: Run RED**, then implement `DecisionIntegrityVerifier`, `ExecutionRequest`, immutable `ExecutionGrant`, `authorize_execution()`, and `authorize_run_action()`. A host adapter must attest integrity; a boolean `signed` field is never sufficient.

**Step 3: Bind formal runs** to bundle, decision, handoff, approved scope, mode, edition, and validity window. Validate at initialization before filesystem writes and again on resume/action. Keep read-only status available after expiry.

**Step 4: Run GREEN**

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3 -m pytest -q -p no:cacheprovider tests/test_execution_gate.py tests/test_formal_run_authorization.py tests/test_artifact_runs.py
```

**Step 5: Commit and push** the six listed files.

## Task 13: Approved deterministic case materialization

**Files:**

- Create: `src/mysql_case_factory/materialization.py`
- Create: `tests/test_approved_materialization.py`
- Modify: `src/mysql_case_factory/renderer.py`
- Modify: `src/mysql_case_factory/artifact_store.py`
- Modify: `src/mysql_case_factory/cli.py`

**Step 1: Write failing gate and semantic tests**

Reject materialization without a current grant before creating directories. With approval, require exactly one selected executable obligation and blueprint per output case, deterministic run-scoped identifiers, SQL bytes, `CaseManifest`, edition, plan/bundle/decision/renderer/profile digests, expected outcome, and harness. Normalize only run identifiers/routing from the formal SQL AST and require it to reproduce the approved `DryRenderArtifact` canonical AST digest. Reject assignment/recipe/type/oracle drift, extra/missing cases, path escape, partial publication, and any attempt to materialize `justified_na` or an unapproved partial obligation.

**Step 2: Run RED**, then implement `materialize_approved_cases()` as an atomic staging-to-publish operation. It accepts only an `ExecutionGrant` plus validated bundle artifacts; it never executes SQL. Add `run materialize --run-root ...` as a grant-bound command.

**Step 3: Run GREEN**

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3 -m pytest -q -p no:cacheprovider tests/test_approved_materialization.py tests/test_execution_gate.py tests/test_dry_render.py tests/test_mysql_cli.py
```

**Step 4: Commit and push** the exact five files.

## Task 14: Obligation execution ledger, sharding, recovery, and all entry gates

**Files:**

- Create: `src/mysql_case_factory/obligation_ledger.py`
- Modify: `src/mysql_case_factory/jobs.py`
- Modify: `src/mysql_case_factory/differential.py`
- Modify: `src/mysql_case_factory/cli.py`
- Modify: `src/mysql_case_factory/__init__.py`
- Create: `tests/test_obligation_ledger.py`
- Modify: `tests/test_jobs.py`
- Modify: `tests/test_mysql_differential.py`
- Modify: `tests/test_mysql_cli.py`
- Modify: `tests/test_mysql_sql_safety.py`

**Step 1: Write failing ledger tests**

Initialize every obligation; keep unapproved partial items in state `pending` with separate `selected: false` metadata; make `justified_na` an explicit terminal state. Prove stable `sha256(obligation_id) % shard_count` partition union/disjointness, atomic claims under two workers, leases/renewal/expiry recovery, idempotent completion, conflicting completion rejection, terminal no-rerun, interruption before/after artifact marker, and exact accounting.

**Step 2: Run RED**, then implement `ObligationExecutionLedger` with `pending`, `claimed`, `running`, `passed`, `expected_failure_observed`, `justified_na`, `product_failure`, and `infrastructure_failure`; selection is an orthogonal boolean/scope binding, not a state. Add attempt tokens, evidence digests, cleanup status, and failure classes. Reports count every unselected obligation as `pending` and therefore can never call a partial run complete. Preserve the old `JobStore` only for v1 test-point generation/audit state.

**Step 3: Gate execution paths**

Require run-bound grant/attempt/obligation at case materialization, scheduler claim, transition to execution, `execute_differential`, external handoff, and direct runner calls. Remove unauthenticated public exports and legacy overwrite/rerun behavior. Validate frozen reference oracle before DUT classification; unexpected success/wrong errno/SQLSTATE/extra terminal error is product failure, invalid oracle or environment/artifact/cleanup failure is infrastructure failure, and cleanup failure overrides pass.

**Step 4: Update CLI** so `run init` requires handoff, `run claim` is atomic/sharded, differential runs only a claimed obligation, and direct execution cannot accept arbitrary unaffiliated SQL. Keep SQL-safety rejection before subprocess even with valid authorization.

**Step 5: Run GREEN**

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3 -m pytest -q -p no:cacheprovider tests/test_obligation_ledger.py tests/test_jobs.py tests/test_mysql_differential.py tests/test_mysql_cli.py tests/test_mysql_sql_safety.py tests/test_planning_execution_isolation.py
```

**Step 6: Commit and push** only the listed implementation/tests.

## Task 15: Knowledge audit, packaging, documentation, and final verification

**Files:**

- Modify: `src/mysql_case_factory/knowledge_audit.py`
- Modify: `tests/test_edition_knowledge.py`
- Modify: `tests/test_edition_packaging.py`
- Modify: `tests/test_skill_packaging.py`
- Modify: `tests/test_smoke_assets.py`
- Modify: `README.md`
- Modify: both edition `SKILL.md`

**Step 1: Write failing audit/package tests** for association rule/domain counts, shape candidates, included/excluded closure, 33 type records, primary obligation count, dry-render verification count, conditional-suite closure, approved golden digests, and archive inclusion. The auditor must compare to pre-approved digests, not recalculate and bless changes.

**Step 2: Run RED**, extend `EditionKnowledgeReport` and the edition/package audits, document plan-first commands, blocked states, approval semantics, partial-run limits, exact MySQL login-path secret handling, and the InnoDB-only golden scope.

**Step 3: Run focused GREEN**

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3 -m pytest -q -p no:cacheprovider tests/test_edition_knowledge.py tests/test_edition_packaging.py tests/test_skill_packaging.py tests/test_smoke_assets.py
```

**Step 4: Run full deterministic verification twice**

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3 -m pytest -q -p no:cacheprovider
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3 -m pytest -q -p no:cacheprovider
git diff --check
git status --short
```

Regenerate each edition's golden plan twice into separate temporary directories and compare every normalized artifact byte and digest. Run an independent final code review and resolve all confirmed findings before committing.

**Step 5: Commit and push**

```bash
git add mysql_case_factory/src/mysql_case_factory/knowledge_audit.py mysql_case_factory/tests/test_edition_knowledge.py mysql_case_factory/tests/test_edition_packaging.py mysql_case_factory/tests/test_skill_packaging.py mysql_case_factory/tests/test_smoke_assets.py mysql_case_factory/README.md mysql_case_factory/editions/mysql_8_0_22/skills/mysql-8-0-22-sql-generation/SKILL.md mysql_case_factory/editions/mysql_8_0_41/skills/mysql-8-0-41-sql-generation/SKILL.md
git commit -m "docs(mysql-case-factory): complete plan-first feature workflow"
git push origin codex/feature-association-agents
```

## Final acceptance checklist

- Existing v1 plan serialization, digests, obligation IDs, and 187-test baseline behavior remain compatible.
- The short ADD COLUMN feature infers, rather than being told, `innodb_table_recipe × added_column_type`.
- Both editions independently prove exact `V × 33` assignment sets plus all conditional-suite contracts.
- Every required factor domain is covered or evidenced `justified_na`; unknown blocks.
- Every executable obligation has exactly one blueprint and verified dry-render semantics.
- Blind audit is chronologically isolated and all findings are closed.
- Planning cannot reach any execution capability and always stops at pending/blocked.
- Approval is external, integrity-protected, digest/scope/edition/time-bound, and checked at every execution entry.
- Execution is per-obligation, deterministic, resumable, non-duplicating, and truthfully classified.
- Only InnoDB is in the golden success scope; MyISAM/MEMORY are rejected.
- Both exact-patch version plans contain a genuine predicate-level difference.
- Full test suite, deterministic regeneration, diff check, commit, and push all succeed.
