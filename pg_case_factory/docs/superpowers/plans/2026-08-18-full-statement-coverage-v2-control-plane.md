# Full Statement Coverage V2 Control Plane Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use
> `superpowers:test-driven-development` and `superpowers:executing-plans`. Execute every
> checkbox in order. The user explicitly selected the current `codex/` branch, so preserve all
> unrelated dirty-worktree files and stage only the files named by each task.

**Goal:** Implement the second V2 stage: strict kind-specific schema validation, immutable input
locks, collision-safe run/revision allocation, verified atomic current pointers, and evidence-backed
planning/runtime state transitions.

**Architecture:** Extend only `pg_case_factory.coverage_v2`. JSON Schema files are package data and
are themselves hashable inputs. Input locks bind repository-relative current bytes through frozen
semantic decoders. Revision publication is same-filesystem and atomic. State transitions consume
verified `ArtifactBinding` objects rather than caller-supplied evidence-kind strings.

**Tech Stack:** Python 3.10+, `unittest`, `jsonschema`, `PyYAML`, RFC 8785/JCS primitives from the
first V2 increment, stdlib `fcntl`, `pathlib`, `tempfile`, `os`, and `hashlib`.

---

## Scope and invariants

Create:

```text
src/pg_case_factory/coverage_v2/
├── schema_registry.py
├── input_lock.py
├── revisions.py
├── state.py
└── schemas/
    ├── registry.json
    ├── artifact-envelope.schema.json
    ├── input-lock.schema.json
    ├── current-pointer.schema.json
    └── readiness.schema.json
tests/
├── test_coverage_v2_schema_registry.py
├── test_coverage_v2_input_lock.py
├── test_coverage_v2_revisions.py
└── test_coverage_v2_state.py
```

Modify only:

```text
pyproject.toml
uv.lock
src/pg_case_factory/coverage_v2/__init__.py
src/pg_case_factory/coverage_v2/artifacts.py
```

The stage must not create `artifacts/intermediates/full-statement-coverage-v2`, regress SQL,
`.spec`, session files, approvals, generation contracts, or a V2 CLI command. The immediately
following inventory-freeze increment additionally registers the strict `statement-order` kind and
adds `inventory.py` plus its test; it is recorded separately from the three control-plane schema
kinds below.

### Task 1: Strict package-backed schema registry

**Files:** schema JSON files, `schema_registry.py`, `test_coverage_v2_schema_registry.py`,
`pyproject.toml`, `uv.lock`.

- [x] **Step 1: Add failing tests for exact kinds and strict payloads**

Tests must construct artifacts with `build_artifact` and prove:

```python
registry = ArtifactSchemaRegistry.load_packaged()
self.assertEqual(
    {"input-lock", "current-pointer", "readiness", "statement-order"},
    registry.implemented_kinds,
)
registry.validate(valid_input_lock)
with self.assertRaises(CoverageV2SchemaError):
    registry.validate({**valid_input_lock, "unexpected": True})
with self.assertRaises(CoverageV2SchemaError):
    registry.validate(build_artifact(
        artifact_id="X", kind="unknown-v2-kind", semantic_payload={}, predecessors=(),
    ))
with self.assertRaises(CoverageV2SchemaError):
    registry.validate(build_artifact(
        artifact_id="L", kind="input-lock", semantic_payload={"scope": "global"}, predecessors=(),
    ))
```

Also test that absolute schema filenames and `..` escapes in `registry.json` fail, every schema has
Draft 2020-12 identity, envelope `additionalProperties=false`, semantic payload
`additionalProperties=false`, and packaged resources remain readable through `importlib.resources`.

- [x] **Step 2: Run RED**

```bash
uv run python -m unittest tests.test_coverage_v2_schema_registry -v
```

Expected: import failure for `pg_case_factory.coverage_v2.schema_registry`.

- [x] **Step 3: Add `jsonschema` and implement the registry**

The public API is fixed as:

```python
@dataclass(frozen=True)
class SchemaBinding:
    kind: str
    resource_name: str
    schema_version: int
    byte_sha256: str
    semantic_sha256: str

class ArtifactSchemaRegistry:
    @classmethod
    def load_packaged(cls) -> "ArtifactSchemaRegistry": ...
    @property
    def implemented_kinds(self) -> frozenset[str]: ...
    @property
    def bindings(self) -> Mapping[str, SchemaBinding]: ...
    def validate(self, document: Mapping[str, Any]) -> None: ...
```

`registry.json` contains exactly one row per implemented kind. Each kind has a separate strict
schema. The common envelope is repeated via local `$defs`; no remote `$ref` or network resolution is
allowed. `validate()` first calls the existing canonical envelope validator and then the exact kind
validator. Unknown kind/version/field and missing field fail closed.

- [x] **Step 4: Run GREEN and commit the task files**

```bash
uv lock
uv sync
uv run python -m unittest tests.test_coverage_v2_schema_registry -v
```

Expected: all schema-registry tests PASS.

### Task 2: Immutable input lock and collision-safe run ID

**Files:** `input_lock.py`, `test_coverage_v2_input_lock.py`, `__init__.py`.

- [x] **Step 1: Add failing input-lock tests**

Use real temporary files. Tests must prove exact input ordering, raw byte SHA, semantic SHA,
decoder identity, version binding, symlink/path escape rejection, YAML duplicate-key rejection,
input drift detection, and the absence of a self-referential `input_root_sha256` payload field.

The desired API is:

```python
specs = (
    InputSpec("a.yaml", "pg18-catalog-v1", "yaml-v1"),
    InputSpec("b.json", "schema-v2", "json-v1"),
)
document = freeze_input_lock(root, scope="global", input_specs=specs)
self.assertEqual(document["semantic_sha256"], global_input_root(document))
self.assertEqual(
    f"fscr-pg18_4-{document['semantic_sha256'][:16]}",
    run_id_for_global_input_lock(document),
)
verify_input_lock(root, document)
```

Collision test: an existing run directory with the same 16-hex prefix but a different complete
global root must fail rather than reuse the path.

- [x] **Step 2: Run RED**

```bash
uv run python -m unittest tests.test_coverage_v2_input_lock -v
```

Expected: import failure for `pg_case_factory.coverage_v2.input_lock`.

- [x] **Step 3: Implement frozen decoders and lock verification**

The public records and functions are:

```python
@dataclass(frozen=True)
class InputSpec:
    relative_path: str
    version: str
    semantic_decoder_id: Literal["raw-v1", "utf8-text-v1", "json-v1", "yaml-v1"]

def freeze_input_lock(repository_root: Path, *, scope: str,
                      input_specs: Sequence[InputSpec]) -> dict[str, Any]: ...
def verify_input_lock(repository_root: Path,
                      document: Mapping[str, Any]) -> tuple[InputBinding, ...]: ...
def global_input_root(document: Mapping[str, Any]) -> str: ...
def run_id_for_global_input_lock(document: Mapping[str, Any]) -> str: ...
def assert_run_id_available(runs_root: Path, run_id: str, full_root_sha256: str) -> None: ...
```

YAML uses a `SafeLoader` subclass that rejects duplicate mapping keys. JSON rejects duplicate keys,
NaN/Infinity, and non-canonical ambiguity. Semantic hashes use domain-separated JCS of decoded
values; raw mode hashes bytes under its own frozen domain. Input rows sort by UTF-8 relative path.

- [x] **Step 4: Run GREEN**

```bash
uv run python -m unittest tests.test_coverage_v2_input_lock -v
```

Expected: all input-lock tests PASS.

### Task 3: Revision allocation, publication, and current pointer

**Files:** `revisions.py`, `test_coverage_v2_revisions.py`, `__init__.py`.

- [x] **Step 1: Add failing filesystem tests**

Tests use a temporary intermediate root and prove:

```python
store = RevisionStore(root, run_id="fscr-pg18_4-0123456789abcdef", statement="abort")
first = store.allocate_revision_id()
second = store.allocate_revision_id()
self.assertEqual(("r0001", "r0002"), (first, second))
staging = store.create_staging(first)
staging.joinpath("plan-validation.json").write_bytes(b"validated\n")
published = store.publish_revision(first)
self.assertTrue(published.is_dir())
with self.assertRaises(CoverageV2RevisionError):
    store.publish_revision(first)
```

Also prove concurrent allocation is unique, a final directory is never overwritten, staging and
final parents are on the same filesystem, pointer writes are atomic, pointer targets must exist,
pointer artifact/schema/SHA are revalidated on read, and a 16-prefix collision cannot share a run.

- [x] **Step 2: Run RED**

```bash
uv run python -m unittest tests.test_coverage_v2_revisions -v
```

Expected: import failure for `pg_case_factory.coverage_v2.revisions`.

- [x] **Step 3: Implement the revision store**

The API is:

```python
class RevisionStore:
    def allocate_revision_id(self) -> str: ...
    def create_staging(self, revision_id: str) -> Path: ...
    def publish_revision(self, revision_id: str) -> Path: ...
    def write_current(self, pointer_document: Mapping[str, Any]) -> None: ...
    def read_current(self, registry: ArtifactSchemaRegistry) -> Mapping[str, Any]: ...
```

Allocation holds `fcntl.flock(LOCK_EX)` on a statement-local lock, scans both `.planning/rNNNN`
and `plan-revisions/rNNNN`, and reserves the next ID before releasing the lock. Publication fsyncs
files and staging directory, then uses one `os.rename` to a nonexistent final directory and fsyncs
the parent. Current pointer uses a sibling temporary file, fsync, `os.replace`, and parent fsync.

- [x] **Step 4: Run GREEN**

```bash
uv run python -m unittest tests.test_coverage_v2_revisions -v
```

Expected: all revision-store tests PASS.

### Task 4: Evidence-backed state machine and readiness

**Files:** `state.py`, `test_coverage_v2_state.py`, `__init__.py`, `artifacts.py`.

- [x] **Step 1: Add failing transition tests**

Tests cover every legal planning/runtime edge, every skipped edge, failure/retry precedence,
package drift reset, and the generation guard. Evidence is passed as verified `ArtifactBinding`
records:

```python
state = CoverageState.discovered(origin=Origin.NATIVE_V2)
with self.assertRaises(CoverageV2StateError):
    advance_planning_state(state, PlanningState.INPUTS_LOCKED, evidence=())
locked = advance_planning_state(
    state,
    PlanningState.INPUTS_LOCKED,
    evidence=(global_input_lock_binding, local_input_lock_binding),
)
with self.assertRaises(CoverageV2StateError):
    GenerationGuard(locked).assert_can_write("case.sql")
```

Readiness tests prove the stage reports `passed=false` while any required V2 schema/catalog/
validator/runner is missing, and never turns a partial schema registry into full V2 readiness.

- [x] **Step 2: Run RED**

```bash
uv run python -m unittest tests.test_coverage_v2_state -v
```

Expected: import failure for `pg_case_factory.coverage_v2.state`.

- [x] **Step 3: Implement states and exact evidence policies**

Use frozen enums for all planning and runtime states from specification section 5. A transition
policy maps each target state to an exact set of required artifact kinds. `advance_planning_state`
rejects missing, duplicate, stale-schema, and extra evidence; it never accepts plain strings.
`record_failure` preserves the last proven planning state. `retry_failure` requires
`retryable=true` plus fresh verified predecessor evidence. `GenerationGuard` permits SQL, `.spec`,
and session-file paths only at or after `generation_allowed`.

`build_foundation_readiness()` emits a strict `readiness` artifact whose payload contains every
required infrastructure component and an explicit missing list. During this second stage the
overall full-V2 readiness is intentionally false until later compiler/extractor/runner schemas
exist; tests lock this fail-closed behavior.

- [x] **Step 4: Run GREEN and the merged regression suite**

```bash
uv run python -m unittest \
  tests.test_coverage_v2_canonical \
  tests.test_coverage_v2_artifacts \
  tests.test_coverage_v2_schema_registry \
  tests.test_coverage_v2_input_lock \
  tests.test_coverage_v2_revisions \
  tests.test_coverage_v2_state -v
uv run python -m unittest tests.test_feature_contracts tests.test_coverage tests.test_cli -v
uv run python -m compileall -q src/pg_case_factory/coverage_v2 tests/test_coverage_v2_*.py
git diff --check
```

Expected: every command exits 0. No regress SQL or formal V2 artifact was created.

### Task 5: Second-stage completion audit

- [x] Re-read specification sections 4.2–4.6, 5, 6, and 13.1 and map every second-stage
      requirement to a test.
- [x] Confirm the second-stage core kinds `input-lock`, `current-pointer`, and `readiness`, plus
      the immediately following strict `statement-order` inventory kind, are the only implemented
      kinds; all later kinds remain fail-closed rather than using a permissive schema.
- [x] Compare pre/post SHA maps for `artifacts/regress` and
      `artifacts/intermediates/full-statement-coverage-v2`.
- [x] Record the canonical first-ten statement inventory in the next planning increment:
      `abort`, `alter_aggregate`, `alter_collation`, `alter_conversion`, `alter_database`,
      `alter_default_privileges`, `alter_domain`, `alter_event_trigger`, `alter_extension`,
      `alter_foreign_data_wrapper` (237 factors, 670 values).

## Completion evidence (2026-08-18)

- V2 foundation/control-plane/inventory: 31 tests passed; every planning/runtime edge and every
  unlisted transition are table-tested.
- Existing project flow compatibility: 64 tests passed.
- First-ten statement generators: 67 tests passed, including deterministic double generation.
- Published first-ten packages independently revalidated: 10 statements, 237 factors, 670 factor
  values, 8,563 SQL files; every coverage ledger has zero missing/duplicate row IDs.
- Phase-two no-write audit: the 40,712 existing files under `artifacts/regress` had identical
  pre/post SHA maps; `artifacts/intermediates/full-statement-coverage-v2` remained absent/empty.
- The next canonical statement is `alter_foreign_table`.

Stop only after fresh verification. The following increment must implement the frozen catalogs,
ledgers, interaction/atom compiler, semantic extractor, renderer routes, global approval, and
generation contracts before any formal SQL is emitted.
