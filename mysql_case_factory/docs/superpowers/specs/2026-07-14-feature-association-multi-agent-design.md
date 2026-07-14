# Feature Association Multi-Agent Planning Design

**Status:** Approved design, 2026-07-14

## Goal

Extend `mysql_case_factory` with a general, evidence-backed feature-association
system. Whenever a feature requirement document is received, the system must
first produce a complete, version-specific test plan, prove the plan's declared
coverage, publish an independent omission audit, and stop at an explicit
execution-decision gate.

The system must not depend on the requester already knowing which factors to
name. A short feature statement such as "`ALTER TABLE ADD COLUMN` is enhanced"
must cause the planning system to discover the affected object shapes, column
types, syntax branches, algorithms, data states, dependencies, boundaries,
concurrency paths, observables, recovery concerns, and version differences.

Complete planning means:

```text
source frozen
  + requirements resolved
  + mandatory factor domains decided
  + version evidence bound
  + coverage obligations reconciled
  + lifecycle/oracle blueprints complete
  + independent blind audit passed
  = ready for an execution decision
```

This design supplements the 2026-07-13 dual-version parity design. For feature
planning, execution authorization, and obligation-level scheduling, this design
takes precedence where the two documents differ.

## Non-goals

- Planning does not connect to MySQL, start a test environment, initialize a
  formal execution run, or execute SQL.
- Model output alone never proves complete coverage. Completeness is established
  by deterministic inventory, set, count, digest, and reconciliation checks.
- The system does not multiply every auxiliary factor into one unbounded global
  Cartesian product. Core axes are exhaustive; conditional factors use explicit
  conditional, boundary, negative, representative, or pairwise policies.
- The first golden feature covers InnoDB only. MyISAM, MEMORY, NDB, and
  Enterprise-only objects are not included in the `ADD COLUMN` success scope.
- An execution blocked by environment, topology, privilege, or harness readiness
  does not reduce the completeness requirement for the preceding plan.
- The system does not store credentials or model chain-of-thought in planning or
  execution artifacts.

## Selected Architecture

The selected design is hybrid:

1. agents perform semantic extraction, evidence retrieval, risk propagation,
   and adversarial re-analysis;
2. a structured, edition-bound knowledge base supplies canonical objects,
   values, relationships, constraints, renderers, and oracles;
3. deterministic compilers and auditors expand and prove coverage sets;
4. execution is a separate workflow that can consume only an approved, frozen
   planning bundle.

Pure prompt/RAG planning was rejected because it cannot prove that a plausible
list has no omissions. A rules-only system was rejected because it cannot adapt
well to unfamiliar feature wording or discover new propagation paths. The
hybrid architecture uses agents for discovery and deterministic contracts for
proof.

## Plan-First Invariants

The following rules are fail-closed:

1. Every input document creates a new immutable request revision and source
   digest.
2. Both MySQL 8.0.22 and 8.0.41 are analyzed from isolated edition evidence.
3. Every mandatory factor domain is either covered or assigned an evidenced
   `justified_na`; unknown applicability remains unresolved and blocks the plan.
4. Executable negative behavior is `expected_failure`, not `justified_na`.
5. Core inventory values cannot be sampled, silently filtered, or replaced by
   same-count duplicates.
6. A large plan may influence the later execution recommendation, but never the
   generated obligation set.
7. A planning workflow with resolved scope and evidence terminates at
   `execution_decision_pending`; an unresolved workflow terminates at a typed
   `planning_blocked` state.
8. An approval binds the exact planning-bundle digest, editions, scope, mode,
   and validity window. Any upstream change invalidates it.
9. Partial execution is permitted only after approval and cannot be reported as
   complete feature validation.

## Planning Artifact Model

A planning run has a stable request ID and monotonically increasing revision.
Its logical artifact layout is:

```text
planning_runs/<request-id>/<revision>/
  inputs/
    feature.md
    source_manifest.yaml
  analysis/
    feature_spec.yaml
    requirements.yaml
    unresolved_questions.yaml
    mysql_8_0_22/feature_manifest.yaml
    mysql_8_0_41/feature_manifest.yaml
  evidence/
    mysql_8_0_22.yaml
    mysql_8_0_41.yaml
    version_delta.yaml
  association/
    impact_graph.yaml
    factor_decisions.yaml
    mandatory_domain_review.yaml
  applicability/
    mysql_8_0_22/feature_applicability_index.yaml
    mysql_8_0_22/review_bundle.yaml
    mysql_8_0_22/reconciliation_report.json
    mysql_8_0_41/feature_applicability_index.yaml
    mysql_8_0_41/review_bundle.yaml
    mysql_8_0_41/reconciliation_report.json
  plans/
    mysql_8_0_22/coverage_plan.yaml
    mysql_8_0_22/coverage_obligations.json
    mysql_8_0_41/coverage_plan.yaml
    mysql_8_0_41/coverage_obligations.json
  dry_render/
    mysql_8_0_22.json
    mysql_8_0_41.json
  blueprints/
    mysql_8_0_22.json
    mysql_8_0_41.json
  audits/
    blind_draft.yaml
    plan_diff.yaml
    coverage_attestation.json
    lifecycle_attestation.json
  execution_brief.json
  decision/
    execution_decision.yaml
  planning_bundle_manifest.json
  planning_run.json
```

The paths describe artifact-store structure, not files that must be committed to
Git. Every artifact records its schema version, producer role, input digests,
output digest, policy digest, and creation time.

`planning_bundle_manifest.json` is immutable and binds every immutable planning
artifact, including `execution_brief.json`, except itself, `decision/`, and the
mutable planning ledger. These exclusions avoid a self-referential approval
digest. `execution_decision.yaml` is an external authorization envelope that
references the immutable planning-bundle digest.
`planning_run.json` records the current state plus those two independent
digests; changing a pending decision to an approval never changes the object
being approved.

### Core contracts

`FeatureSpec` contains the operation, target objects, stated behavior change,
affected execution phases, target editions, explicit constraints, atomic
requirements, source locators, and unresolved questions.

`FeatureImpactGraph` contains typed nodes for requirements, objects, operations,
factor domains, inventory selectors, constraints, risks, observables, and
version claims. Edges record a stable rule ID and evidence showing why one node
implies another. Every planned factor must be reachable from a requirement.

`FactorDecision` records a factor ID, domain, trigger path, inventory source and
digest, edition applicability, combination strategy, dependencies, exclusions,
and review state.

`PlanCaseBlueprint` binds one executable obligation to a setup recipe, target
statement shape, verification oracle, cleanup procedure, expected outcome,
diagnostic contract, and basic or external harness. Error code, SQLSTATE, and
terminal-diagnostic constraints are required for `expected_failure` and omitted
only when they do not apply to a success obligation. It is a plan-level recipe;
formal SQL materialization occurs only after execution approval.

`DryRenderArtifact` is an immutable planning artifact containing a canonical SQL
AST, normalized symbolic identifiers, and non-runnable preview text for each
blueprint. It has no credentials, endpoint, scheduler route, executable case
manifest, or formal-run location. It is included in the planning bundle so that
assignment-to-SQL semantics can be audited before an execution decision.

`AuditAttestation` records the auditor's permitted inputs, reconstructed factor
set, missing and excess sets, findings, closed-finding evidence, and final
digest-bound decision.

`ExecutionDecision` defaults to `pending` and records `approved`, `declined`, or
`deferred` only through an explicit user decision. It is not part of the
planning bundle. Approval includes the immutable planning-bundle digest,
editions, selected execution scope, full or partial mode, resource limits,
expiry, and approver identity supplied by the host workflow.

## Multi-Agent Topology

Agents are logical roles with separate task envelopes and output directories.
They may run in waves when concurrency is limited, but one role cannot silently
substitute for another.

### Planning Orchestrator

The orchestrator is the only planning-state writer. It freezes inputs, dispatches
roles, verifies envelopes and digests, merges structured findings, invokes
deterministic compilers, and stops at the execution-decision gate. It cannot
approve execution.

Planning roles run with capability-level isolation: their tool set has no MySQL
connection, Docker lifecycle, formal-run initialization, case materialization,
scheduler, differential execution, or direct execute capability. The
`allowed_actions` and `forbidden_actions` fields are audited descriptions of an
enforced sandbox, not the enforcement mechanism itself.

### Requirement Analyst

The requirement analyst converts the source into atomic requirements and a
`FeatureSpec`. It preserves source locations and reports questions whose answers
would change coverage. Such questions block downstream completion.

### Version Evidence Agents

Two independent evidence roles analyze MySQL 8.0.22 and 8.0.41. Each can read
only its edition snapshot plus approved official MySQL evidence. They report
syntax, semantics, restrictions, boundaries, and version-specific claims. The
orchestrator derives a closed added/changed/removed/unchanged delta; one edition's
conclusion is never copied to the other without an explicit unchanged proof.

### Factor Association Agent

The association agent traverses object, operation, phase, risk, dependency, and
observable relationships to produce the impact graph and factor decisions. It
must perform both forward association from the requirement and reverse checks
from every mandatory domain.

### Deterministic Coverage Compiler

The compiler is treated as an isolated role even though its core is ordinary
Python rather than generative reasoning. It validates inventories, produces
edition-specific applicability and coverage plans, expands obligations, checks
exact sets and counts, and builds the dependency DAG.

### Lifecycle and Oracle Agent

This role produces one blueprint for every executable obligation. It plans
setup, target, verify, and cleanup phases and selects the required harness. It
does not render or execute the formal case.

### Independent Audit Agents

At least two audit roles are required:

- the coverage auditor reconstructs a `blind_draft` from only the original
  source, edition knowledge, official evidence, and mandatory-domain policy;
- the lifecycle auditor checks setup, target, verify, cleanup, observability,
  expected errors, and harness routing.

The coverage auditor receives the candidate plan only after its blind draft is
frozen. It then performs a set diff. Auditors never receive another agent's
private reasoning. Unexplained missing or excess factors, missing evidence, or
open findings return the run to rework.

### Execution Decision Gatekeeper

The gatekeeper produces a decision brief with exact per-edition and per-suite
counts, expected duration, resource and topology needs, external-harness needs,
known risks, and the consequences of full, partial, deferred, or declined
execution. Its output is always `pending`; only the user can approve.

## Agent Task Envelope

Every role accepts a closed `AgentTaskEnvelope` similar to:

```yaml
task_id: stable-id
request_id: stable-id
request_revision: 1
role: factor_association
input_artifacts:
  - path: inputs/feature.md
    sha256: "..."
allowed_actions:
  - read_knowledge
  - read_approved_official_sources
  - write_plan_artifacts
forbidden_actions:
  - database_connect
  - test_execute
  - formal_run_init
expected_outputs:
  - association/impact_graph.yaml
  - association/factor_decisions.yaml
policy_sha256: "..."
```

The result contract contains `complete`, `blocked`, or `failed`; all input and
output digests; structured findings; unresolved questions; and metrics. Missing
outputs, stale inputs, undeclared writes, symlinks, path escapes, and partial
publication are rejected. Each role writes only to its staging directory, and
the orchestrator atomically publishes accepted artifacts.

## Planning State Machine

```text
received
  -> source_frozen
  -> requirements_ready
       -> planning_blocked_needs_input -> resume at requirements_ready
  -> version_evidence_ready
       -> planning_blocked_evidence_conflict -> resume at version_evidence_ready
  -> factors_associated
  -> applicability_complete
  -> plan_compiled
  -> obligations_reconciled
  -> blueprints_complete
  -> audit_in_progress
       -> rework_required -> return to the owning stage
       -> audit_passed
  -> execution_decision_pending
       -> execution_deferred
       -> execution_declined
       -> approved_for_separate_execution_handoff
```

Agent crashes are idempotently retried with the same task and input digests.
Conflicting conclusions are not resolved by voting or last-write-wins; findings
are unioned and must be explicitly closed. A revised source creates a new
revision and invalidates every downstream artifact and decision.

Both named blocked states publish an immutable diagnostic bundle but are not
complete plans and cannot reach an execution decision. Other pre-audit stages
may enter a typed `planning_blocked` state with an owning stage and resume
target. Only a document whose scope-changing questions and evidence conflicts
are resolved can reach `execution_decision_pending`.

This state machine is separate from the existing execution-oriented `JobStore`.
A new `PlanningRunLedger` owns planning progress. Formal run initialization can
consume only a valid execution handoff whose plan digest matches exactly.

## Mandatory Factor Ontology

Every feature must make an explicit, evidenced decision for each domain:

1. target object and related-object shapes;
2. data and type domain;
3. object lifecycle and data state;
4. syntax branches, options, and defaults;
5. execution algorithm and storage path;
6. indexes, constraints, dependencies, and generated objects;
7. positive, negative, boundary, and limit behavior;
8. transactions, locks, isolation, and concurrency;
9. privileges, security, and SQL mode;
10. metadata, diagnostics, and observability;
11. atomicity, durability, restart, backup, and recovery;
12. binlog, replication, and topology effects;
13. version compatibility, upgrade, downgrade, and rollback;
14. performance, capacity, and resource effects.

Features can add domains but cannot silently remove these. A domain irrelevant
to a feature still requires a source-bound `justified_na` decision. Knowledge
nodes and association rules are edition-versioned, reviewable data rather than
hard-coded prompt prose.

## Coverage Compilation Semantics

Coverage combination policies are explicit:

- `full_cross` for primary axes whose complete interaction is required;
- `conditional_cross` for a complete cross within each applicable condition;
- `boundary` for minima, maxima, just-inside, and just-outside values;
- `negative` for invalid inputs and forbidden states;
- `representative` for a documented equivalence class;
- `pairwise` only for auxiliary interactions that have an evidenced low-risk
  policy and are not part of a primary completeness claim.

Each new feature-level test point carries a coverage contract:

```yaml
coverage_contract:
  combination_policy: full_cross
  primary_axes:
    - innodb_table_recipe
    - added_column_type
  condition_axes: []
  expected_counts:
    total: 0      # compiled and frozen from inventories
    success: 0
    expected_failure: 0
    justified_na: 0
```

The zeroes above are schema examples, not accepted final counts. The compiler
calculates and freezes the exact edition-specific values. Existing v1 plans that
lack `coverage_contract` retain byte-for-byte serialization and obligation IDs;
they do not gain a new completeness claim.

For every condition tuple, the actual primary assignment set must equal the
mathematical Cartesian set, not merely have the same count. Duplicate values,
same-count substitution, split test points that turn multiplication into
addition, and post-coverage filtering all fail.

The accounting invariant remains:

```text
required = success + expected_failure + justified_na
missing = 0
```

`expected_failure` and `justified_na` require a non-empty reason and source.
Structurally absent capabilities may be `justified_na`; executable unsupported
combinations remain executable expected-failure obligations.

Every conditional suite is subject to the same proof discipline as a primary
test point. It owns a versioned source inventory, explicit primary and condition
axes, an allowed combination policy, a theoretical assignment set and digest,
exact outcome counts, and deletion/substitution mutation tests. A topic heading
or one representative example cannot satisfy a conditional-domain decision.

Every factor ID has exactly one `owning_suite_id`. Other suites may reference an
owned factor only through an explicit interaction edge and selector; that reuse
does not earn a second coverage credit or close the owner's inventory. The
coverage ledger reconciles unique factor ownership separately from obligation
execution, so intentional cross-suite overlap cannot hide a missing factor or
inflate completeness.

## Canonical Universe and Render Integrity

"All InnoDB table types" is a closed, edition-bound contract rather than an
agent-generated count. Each edition contains three independently reviewed and
digest-pinned inputs:

1. `innodb_table_shape_universe` defines the candidate shape axes, canonical
   values, structural validity rules, and deterministic candidate IDs;
2. `innodb_table_recipe_inventory` maps every candidate to an executable recipe
   or an evidenced structural exclusion;
3. `added_column_type_inventory` defines the 33 canonical column types.

The shape universe is bound by the edition manifest and by a separately reviewed
golden-policy digest. A plan can neither edit the universe nor bless a newly
calculated digest. Updating the universe is an explicit knowledge revision that
requires review, mutation tests, edition-template regeneration, and a deliberate
golden digest change.

Candidate generation is fixed and deterministic:

```text
theoretical_candidates
  = Cartesian product of every canonical shape-axis inventory
    in the frozen axis and value order
```

The generator version, axis order, value order, theoretical count, canonical
assignment set, and assignment-set digest are frozen before any structural rule
is applied. Every theoretical candidate then receives a structural-validity
decision. Rules classify candidates but cannot prevent their generation. The
shape universe contains table-shape axes only; feature conditions such as LOCK,
privilege, concurrency, and failure injection remain separate conditional
suites.

Universe reconciliation requires every deterministic candidate ID exactly once
in the recipe inventory as `included` or `structurally_excluded`. Included rows
bind a unique recipe ID. Exclusions bind an official or approved knowledge
source, the violated structural rule, and a review state. Removing recipes and
recalculating `V` therefore creates unresolved universe candidates rather than a
smaller passing universe.

Each type entry binds a canonical DDL declaration, normalized semantic type,
legal seed values, boundary values, and metadata/data oracles. Each recipe binds
its table-shape signature, setup template, prerequisites, static assertions,
runtime metadata oracle, and cleanup template.

Before approval, a static semantic verifier parses every bundled
`DryRenderArtifact` and proves that:

- the target table reference resolves to the assigned recipe;
- the setup semantics match the assigned shape signature;
- the added column declaration matches the assigned canonical type;
- the verify oracle checks the same table, column, type, and feature condition.

After approval, formal materialization substitutes only run-scoped identifiers
and routing data. Normalizing those substitutions must reproduce the bundled
canonical AST digest. Exact-version reference execution then additionally proves
the created table's observed metadata and the added column's observed type.
Changing only an assignment while leaving `INT` SQL, or rendering distinct
recipes to the same table shape, fails reconciliation.

## `ALTER TABLE ADD COLUMN` Golden Feature

The first golden input deliberately states only that `ALTER TABLE ADD COLUMN`
has been enhanced. It does not tell the agents to cover all table shapes or data
types. Passing requires the system to infer those axes from the knowledge graph.

### Primary matrix

Each edition has one feature-level primary test point:

```text
all canonical executable InnoDB table recipes for the edition
  x all 33 canonical added-column types for the edition
```

If an edition has `V` canonical recipes, the primary obligation set is exactly
`V x 33`. The compiler freezes the recipe count and digest, type count and
digest, theoretical assignment digest, actual assignment digest, and outcome
counts. The two editions are proved independently.

An InnoDB table recipe is concrete, directly constructible, and owns setup and
cleanup logic plus prerequisite declarations. The canonical inventory must
close at least these table-shape categories:

- permanent and temporary tables;
- nonpartitioned, RANGE, RANGE COLUMNS, LIST, LIST COLUMNS, HASH, LINEAR HASH,
  KEY, LINEAR KEY, and valid subpartitioned shapes;
- DYNAMIC, COMPACT, REDUNDANT, and COMPRESSED row formats where constructible;
- file-per-table, system, and general tablespace shapes where constructible;
- no primary key, single-column primary key, and composite primary key;
- ordinary, unique, prefix, FULLTEXT, SPATIAL, functional, and multi-valued
  index-bearing shapes where supported;
- foreign-key parent and child, CHECK-constrained, virtual-generated-column,
  and stored-generated-column shapes.

Every executable recipe explicitly declares `ENGINE=InnoDB`. Unsupported
cross-dimension shapes are kept in a separate applicability inventory with an
officially evidenced decision; they are not silently omitted from category
closure.

The primary matrix owns only `innodb_table_recipe` and
`added_column_type`. Its ADD statement uses one frozen baseline context: last
position, nullable, no explicit default, default ALGORITHM/LOCK, and a canonical
small seed where the recipe permits data. Data volume, DDL history, row-version
state, target-column dependency, and algorithm choices belong to conditional
suites and do not change `V`.

Planning-stage `constructible` means schema-valid, statically renderable, free
of unresolved prerequisites, and consistent with the edition's structural
rules. It never means runtime-tested. Runtime constructibility is a separate
status earned only by an approved, exact-patch reference execution; reports
must keep these two statuses distinct.

### Required cross-version witness

The golden fixture pins a real `ADD COLUMN` delta introduced in MySQL 8.0.29:

```sql
ALTER TABLE t
  ADD COLUMN added_col INT FIRST,
  ALGORITHM=INSTANT;
```

For MySQL 8.0.22 the plan expects the unsupported-INSTANT error class
`SQLSTATE 0A000`; for MySQL 8.0.41 it expects success and verifies that the
column is first. The fixture freezes the exact patch-reference diagnostic before
it can be used as an execution oracle.

The evidence bundle pins the official
[MySQL 8.0.29 release-note locator](https://dev.mysql.com/doc/relnotes/mysql/8.0/en/news-8-0-29.html)
and
[InnoDB online DDL operations](https://dev.mysql.com/doc/refman/8.0/en/innodb-online-ddl-operations.html),
plus the official
[MySQL 8.0 server error reference](https://dev.mysql.com/doc/mysql-errors/8.0/en/server-error-reference.html#error_er_alter_operation_not_supported),
including retrieved-content digests. The release note states that pre-8.0.29
instant addition was limited to the last position and 8.0.29 allows any
position. The error reference binds `ER_ALTER_OPERATION_NOT_SUPPORTED` and its
reason-bearing variant to `SQLSTATE 0A000`. A reviewed 8.0.22 exact-patch oracle
transcript freezes which numeric error and terminal message this statement
produces; the fixture cannot reach review-complete without that transcript and
digest. This fixed witness prevents two generic, identical edition plans from
passing the golden version-association test.

### Conditional suites

The following suites have their own policies and counts instead of multiplying
blindly into the primary matrix:

- NULL, NOT NULL, DEFAULT, generated, AUTO_INCREMENT, and visibility forms;
- default position, FIRST, and AFTER;
- ALGORITHM and LOCK combinations;
- empty, populated, wide-row, large-value, and mixed old/new row states;
- prior DDL history and INSTANT row-version lifecycle states;
- the added column participating in indexes, constraints, dependencies,
  triggers, or generated expressions;
- duplicate names, illegal names, missing/wrong objects, illegal definitions,
  insufficient privileges, and expected SQLSTATEs;
- maximum columns, maximum row size, key limits, and INSTANT row-version
  boundaries;
- concurrent SELECT, DML, and DDL; lock wait, timeout, cancellation, commit, and
  rollback behavior;
- failed-DDL atomicity, restart, and crash-recovery behavior;
- `SHOW CREATE TABLE`, `INFORMATION_SCHEMA`, warnings, diagnostics, and data
  read/write oracles;
- binlog/replication, upgrade compatibility, backup/recovery, and performance or
  an evidenced external-harness/`justified_na` decision.

For each bullet, the golden feature supplies a suite-specific
`coverage_contract`, canonical input selector, exact expected assignment set and
digest, outcome accounting, and at least one deletion mutation. Equivalence
classes name all members and the evidence for treating them as equivalent;
representative coverage never means an unreviewed single example.

## Blueprint and Execution Separation

Planning produces exactly one blueprint for each executable obligation and no
blueprint for `justified_na`. Reconciliation rejects missing, duplicate, or
mismatched bindings. Every blueprint has setup, target, verify, and cleanup; a
missing phase fails lifecycle audit.

After explicit approval, a separate materialization workflow renders each
blueprint to a deterministic case and SQL program. Every case binds the plan,
obligation, assignments, edition, renderer, SQL bytes, expected result,
execution profile, and harness digests.

Materialization performs the same assignment-to-SQL semantic reconciliation as
the planning verifier. It cannot trust metadata copied from the obligation.

Execution scheduling is per obligation, not per test point. The execution ledger
supports deterministic sharding using the obligation ID, idempotent retries,
crash recovery, and resumption without rerunning completed cases. The default
database concurrency is conservative and profile-controlled.

Execution reporting separates coverage completion from product correctness:

```text
planned
  = passed
  + expected_failure_observed
  + justified_na
  + product_failure
  + infrastructure_failure
  + pending
```

A complete run has `pending = 0`. A passing run also has zero product and
infrastructure failures. A partial run names its unexecuted obligation set and
never claims full validation.

An expected-failure obligation counts as `expected_failure_observed` only when
the reference oracle is valid and the observed terminal error count, error code,
SQLSTATE, and diagnostic contract match exactly. Unexpected success, wrong
SQLSTATE/code, or additional terminal errors are product failures when the
reference oracle remains valid; an invalid reference oracle is an oracle or
infrastructure failure. Cleanup failure is always an infrastructure failure and
the case cannot be counted as passed or expected-failure-observed.

## Execution Decision Gate

The planning result always includes an execution brief and a decision with
status `pending`. The brief reports:

- exact case counts by edition and suite;
- full and optional partial execution cost estimates;
- required MySQL endpoints, privileges, disk, time, concurrency, replication,
  restart, and fault-injection harnesses;
- safety or environment blockers;
- what confidence is lost under each partial-execution proposal.

Approval is a separate user action. The same planning task does not begin SQL
execution after producing the plan. Formal run initialization rejects a missing,
expired, declined, deferred, partial-scope-mismatched, or digest-mismatched
decision.

The authorization check is centralized and mandatory at every execution-capable
entry point: case materialization, formal run initialization, scheduler start,
job execution, differential execution, external-harness handoff, and direct
execute APIs. CLI aliases and library calls cannot bypass it. The host, not a
planning agent, creates the signed or otherwise integrity-protected authorization
envelope.

## Failure and Conflict Handling

- An agent failure retains diagnostics and retries without advancing state.
- Unknown applicability remains pending and blocks audit; it is never converted
  automatically to N/A.
- Official patch-specific evidence outranks a generic manual statement for that
  patch. Unresolved evidence conflicts become blocking artifacts.
- Auditor and generator disagreements use the union of findings. Every finding
  needs an explicit disposition and evidence.
- Missing external harnesses can leave execution readiness blocked while the
  logical plan remains complete.
- Plan size never authorizes automatic sampling or omission.
- Secrets remain in existing external login-path mechanisms and never enter a
  task envelope, prompt, plan, decision, or run artifact.

## Testing and Acceptance

The implementation is test-driven and must reuse the existing contract,
inventory, coverage, applicability, formal-run, job, differential, and version
delta foundations.

P0 acceptance for documents with resolved scope-changing questions and evidence
includes:

1. A resolvable feature document ends in a frozen planning bundle and
   `execution_decision_pending` before any executable action; an unresolved
   document ends in a frozen typed diagnostic bundle and `planning_blocked`.
2. Planning tests prove that database connections, Docker startup, formal run
   initialization, and execution calls are unreachable before approval.
3. The `ADD COLUMN` golden plan independently equals `V_edition x 33` for both
   editions by set equality and digest, not only by count.
4. Every canonical InnoDB recipe is constructible and category closure is
   audited against the independent shape universe; MyISAM and MEMORY recipes
   fail this golden scope.
5. Every executable obligation has exactly one lifecycle blueprint.
6. Blind audit input manifests prove that the candidate plan was unavailable
   until the blind draft was frozen.
7. Version evidence and plans cannot be copied across editions without a closed
   unchanged decision.
8. Old plans without the new coverage contract keep their serialization,
   digests, and obligation IDs.
9. An approved plan can be deterministically materialized, sharded, interrupted,
   resumed, and reconciled per obligation.
10. Type and recipe assignments are statically reconciled to rendered SQL and,
    after approval, to observed exact-version metadata.
11. Every conditional suite proves its own inventory, expected assignment set,
    digest, counts, and mutation closure.
12. The fixed `INSTANT` positional witness fails with the frozen `0A000` oracle
    on 8.0.22 and succeeds with positional metadata verification on 8.0.41.

Mutation tests must fail when any of these changes is introduced:

- remove or replace a column type or InnoDB recipe;
- split table and type axes into separate test points;
- downgrade `full_cross` to sampling, pairwise, or rotation;
- disguise an executable combination as `justified_na`;
- remove a mandatory domain, reason, source, blueprint phase, case, or version
  decision;
- duplicate an obligation binding or change rendered SQL after approval;
- change an assignment without changing SQL, or collapse distinct recipes to
  the same setup shape;
- let the blind auditor read the candidate plan before freezing its draft;
- initialize or execute a run before approval;
- change source, knowledge, inventory, recipe, type, renderer, or plan bytes
  after approval.

The golden suite also includes a non-table feature to prove that table/type
matrices are inferred by relevance rather than hard-coded for every input.

Metamorphic planning tests require synonymous feature wording to produce the
same normalized factor set, removal of explicit "all tables/all types" hints to
preserve the inferred primary axes, and repeated runs over identical source,
knowledge, policy, and edition digests to produce identical normalized plans and
digests.

When the user approves `full` execution, integration acceptance requires an
independent reference/DUT endpoint pair for each of 8.0.22 and 8.0.41. Each pair
must have distinct stable server UUIDs and both endpoints must match the exact
patch. Every primary obligation and every approved conditional obligation is
executed on its pair and receives a differential comparison. The run must finish
with `pending = 0` and satisfy both the coverage and execution accounting
equations. A partial approval exercises only its bound subset and cannot satisfy
this full-integration gate.

## Delivery Boundaries

The implementation will reuse `FeatureManifest`, `FeatureApplicability`,
`CoveragePlan`, coverage expansion and reconciliation, edition snapshots,
differential execution, and artifact integrity checks.

It will add planning contracts, a `PlanningRunLedger`, agent envelopes and
results, the impact graph and factor decisions, blueprint and audit contracts,
the execution-decision contract, orchestration/status/audit/decision CLI
commands, canonical InnoDB recipe inventories, unified added-column type axes,
feature-level cross-coverage validation, and obligation-level execution state.

Only `mysql_case_factory` files are staged. Design, implementation plan, and
implementation commits are pushed after successful verification. Credentials
and generated run artifacts never enter Git history.
