# MySQL 8.0.22 / 8.0.41 Case Factory Parity Design

## Goal

Upgrade `mysql_case_factory` from an SQL-reference scaffold into the same kind
of traceable, auditable, resumable compatibility-test system as
`pg_case_factory` v0.2, while shipping two isolated MySQL Community Server
editions: 8.0.22 and 8.0.41.

Complete means that both editions can turn a preserved feature document into a
version-bound manifest, compile complete coverage obligations, persist one job
per test point, bind one deterministic SQL program to each executable
obligation, execute matching-version reference and DUT endpoints twice, compare
the exact observable transcripts, and package findings/regression evidence.

## Non-goals

- Do not store passwords, tokens, private keys, host names, or credential-bearing
  URIs in repository files or run artifacts.
- Do not treat MySQL Enterprise or NDB-only capabilities as ordinary Community
  Server success paths. They remain explicit external-harness or justified-N/A
  decisions.
- Do not claim runtime verification for statements that have only passed static
  inventory and matrix audits.
- Do not infer storage-engine root causes from SQL-level differences.
- Do not duplicate the Python control plane per patch release.

## Selected Architecture

The parent `mysql_case_factory` remains one installable Python control plane.
Two edition directories contain independently packageable knowledge snapshots:

```text
mysql_case_factory/
├── src/mysql_case_factory/
├── editions/
│   ├── mysql_8_0_22/
│   │   ├── edition.yaml
│   │   ├── README.md
│   │   └── skills/mysql-8-0-22-sql-generation/
│   └── mysql_8_0_41/
│       ├── edition.yaml
│       ├── README.md
│       └── skills/mysql-8-0-41-sql-generation/
├── tests/
├── tools/
└── docs/
```

The control plane accepts an explicit edition root or the dedicated
`mysql-case-8022` / `mysql-case-8041` entry point. It never selects a version
from SQL text. `run init` snapshots the edition manifest, relevant inventories,
applicability ledger, feature source, coverage plan, and execution profile. All
later job and execution gates recompute those digests.

The alternatives were rejected for specific reasons:

- Two copied Python projects would isolate releases but duplicate thousands of
  lines of security- and evidence-sensitive code.
- One shared knowledge tree with version conditionals would make it easy for a
  post-8.0.22 syntax branch to leak into an 8.0.22 run.

## Edition Contract

Each `edition.yaml` has a closed schema containing:

- edition ID (`mysql-community-8.0.22` or `mysql-community-8.0.41`);
- numeric target version (`80022` or `80041`);
- skill root and entry-point name;
- factor, type, statement-support, compatibility, and delta-ledger paths;
- SHA-256 digests and exact counts for every inventory;
- reference-oracle policy (`mysql-community-server`, exact patch target);
- review state, which must be `complete` before formal `run init`.

The 8.0.41 edition owns a delta ledger against 8.0.22. Every 8.0.22 statement,
factor, and value is classified as `unchanged`, `changed`, or `removed`, and
every 8.0.41-only item is classified as `added`. Changed/added/removed rows bind
official release-note or manual locators. There is no implicit inheritance.

## Knowledge and Coverage Model

The existing 8.0.22 references are migrated with history preserved, then
audited against a MySQL-native statement universe rather than only the old
PostgreSQL migration manifest. Every supported statement must have:

1. a statement reference with version, official source, syntax branches,
   factors, defaults, rendering bindings, risks, and execution profile;
2. mappings to versioned global factor/type inventories;
3. a required combination matrix or an explicit non-renderable/external record;
4. complete statement-factor-value applicability rows;
5. static and runtime review states kept separate.

Coverage plans retain the PG v0.2 reconciliation rule:

```text
required = success + expected_failure + justified_na
missing = 0
```

Mandatory MySQL risk decisions cover syntax, lifecycle, data profile, SQL mode,
character set/collation, transaction/autocommit, storage engine, partitioning,
indexes/constraints/triggers, privilege, maintenance, concurrency,
replication/binlog, and restart/recovery. Feature-specific risks remain extra
decisions rather than being collapsed into those fixed categories.

## Runtime Data Flow

```text
feature document
  -> version-bound feature_manifest.yaml
  -> complete applicability index
  -> compiled coverage_plan.yaml
  -> deterministic coverage obligations
  -> one durable job per test point
  -> one case manifest + one SQL program per executable obligation
  -> reference first run + replay
  -> DUT first run + replay
  -> endpoint-internal determinism checks
  -> formal exact reference-vs-DUT comparison
  -> finding and numbered regression package
```

Newline encoding is normalized to LF; return code, stdout, stderr, whitespace,
and final-newline boundaries otherwise remain exact.

## Execution and Identity

Basic execution uses the `mysql` CLI with batch/raw, no-column-name, UTF-8,
warning, and deterministic locale settings. Credentials live outside the
repository in `mysql_config_editor` login paths. An execution profile stores
only login-path names, the common database, expected server UUIDs, expected
`CURRENT_USER()`, executable, timeout, and the edition ID.

Before, during, and after execution, each endpoint reports:

- the numeric `MAJOR.MINOR.PATCH` prefix parsed from `VERSION()`;
- `@@server_uuid`;
- `DATABASE()`;
- `CURRENT_USER()`;
- `@@version_comment`, recorded as evidence rather than used as a secret.

Both endpoints must match the edition patch, database, and expected current
user. Their server UUIDs must be distinct and stable. Profile values and case
bytes are reloaded under the case lock before the first database call.

An expected-failure case succeeds as an oracle only when the reference exits
nonzero and emits exactly one terminal `ERROR <number> (<five-character
SQLSTATE>)` diagnostic matching its manifest. Same-looking reference and DUT
errors do not rescue an invalid reference oracle.

Basic SQL safety rejects client meta commands, credential directives, `SYSTEM`,
`SOURCE`, dangerous outfile/infile paths, plugin/component loading, shutdown,
restart, server file access, replication/topology control, and multi-session or
fault-injection programs. Such cases use a named external isolated harness whose
implementation and readiness evidence are hash-bound to the run.

## Error Handling and Artifact Integrity

Contracts reject unknown keys, path traversal, symlinks, duplicate IDs,
incorrect digests, incomplete inventories, edition/version mismatch, unresolved
questions, missing evidence, and unsupported state transitions before executing
SQL. Artifact writes use staging plus atomic publication. A comparison JSON is
the completion marker; a pre-existing marker requires explicit overwrite.

Failed jobs retain a reason and can be retried through the state machine. A
finding binds the exact SQL, reference execution, DUT execution, comparison,
edition manifest, and execution-profile digests.

## Testing Strategy

- Port the PG v0.2 contract, coverage, job, artifact, CLI, regression, safety,
  and packaging tests to MySQL first and watch them fail before porting code.
- Add edition-isolation tests that deliberately cross 8.0.22 and 8.0.41 inputs.
- Test MySQL version parsing, UUID/current-user identity, login-path validation,
  SQLSTATE parsing, exact output, collision locks, and external routing.
- Audit every statement reference, factor/value mapping, matrix, delta-ledger
  row, inventory count, and digest for both editions.
- Use fake `mysql` executables for deterministic failure injection.
- Build and verify both deterministic skill archives twice.
- Attempt a four-endpoint Docker smoke test (reference and DUT for each patch).
  If a historical image or host architecture prevents it, record the exact
  blocker and keep runtime verification explicitly false.

## Git and Delivery

Work occurs on `codex/mysql-8022-8041-parity`, based on the completed PG v0.2
branch. Only `mysql_case_factory` files and any required repository-root
`.gitignore` entry are staged. Documentation and implementation commits are
pushed immediately after each successful commit. Local credentials never enter
Git history.
