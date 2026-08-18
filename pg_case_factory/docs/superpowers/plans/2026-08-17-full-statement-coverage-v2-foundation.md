# Full Statement Coverage V2 Canonical Artifact Core Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use
> `superpowers:using-git-worktrees`, then `superpowers:subagent-driven-development`
> (recommended) or `superpowers:executing-plans`. Execute one checkbox at a time and
> stop at the final handoff gate.

**Goal:** Implement only the first independently testable V2 core: pure RFC 8785
canonical bytes, all 17 domain-separated logical ID kinds, canonical artifact envelopes,
current-byte-backed declared predecessor graph verification, and the one frozen manifest
digest domain.

**Architecture:** Add an isolated `pg_case_factory.coverage_v2` package. Generic artifact
canonicalization performs pure JCS and never normalizes Unicode. Logical ID components alone
receive NFC normalization. Artifact graph validation always rereads the supplied repository
files, detects cycles before trusting hashes, and then recomputes byte SHA, semantic SHA, and
declared predecessor SHA links. This increment intentionally does not implement kind-specific
component arity/statement-key contracts, schemas, or exact predecessor policies; those belong to
typed ledger/compiler schemas. Therefore this increment cannot claim readiness, advance a V2
state, publish artifacts, expose a CLI, or generate SQL.

**Tech Stack:** Python 3.10+, `unittest`, `rfc8785`, stdlib `hashlib`, `json`, `pathlib`,
`types.MappingProxyType`, and `unicodedata`.

---

## Scope and file map

Create:

```text
src/pg_case_factory/coverage_v2/
├── __init__.py
├── errors.py
├── canonical.py
├── ids.py
└── artifacts.py
tests/
├── test_coverage_v2_canonical.py
└── test_coverage_v2_artifacts.py
```

Modify only:

```text
pyproject.toml
uv.lock
```

Do not modify V1 modules, the CLI, formal evidence, regress SQL, or `artifacts/`.
Run the plan in a dedicated worktree because the shared tree already contains unrelated
changes to `pyproject.toml` and `uv.lock`.

### Task 1: Pure RFC 8785 canonical bytes

**Files:**
- Modify: `pyproject.toml`
- Modify: `uv.lock`
- Create: `src/pg_case_factory/coverage_v2/__init__.py`
- Create: `src/pg_case_factory/coverage_v2/errors.py`
- Create: `src/pg_case_factory/coverage_v2/canonical.py`
- Create: `tests/test_coverage_v2_canonical.py`

- [ ] **Step 1: Record the no-output baseline**

Run:

```bash
(
  find \
    artifacts/intermediates/full-statement-coverage-v2 \
    artifacts/regress \
    -type f -exec shasum -a 256 {} + 2>/dev/null || true
) | LC_ALL=C sort > "$(git rev-parse --git-path fscr-v2-core-before.sha256)"
```

Expected: the command exits 0. The baseline lives under `.git/`, not in the worktree.

- [ ] **Step 2: Add the failing canonicalization tests**

Create `tests/test_coverage_v2_canonical.py`:

```python
from __future__ import annotations

import unittest

from pg_case_factory.coverage_v2.canonical import canonical_json_bytes
from pg_case_factory.coverage_v2.errors import CoverageV2ContractError


class CanonicalJsonTest(unittest.TestCase):
    def test_mapping_order_is_canonical_and_utf8_is_preserved(self) -> None:
        left = {"b": 2, "a": "caf\N{LATIN SMALL LETTER E WITH ACUTE}"}
        right = {"a": "caf\N{LATIN SMALL LETTER E WITH ACUTE}", "b": 2}
        expected = b'{"a":"caf\xc3\xa9","b":2}'
        self.assertEqual(expected, canonical_json_bytes(left))
        self.assertEqual(canonical_json_bytes(left), canonical_json_bytes(right))

    def test_generic_jcs_does_not_apply_unicode_normalization(self) -> None:
        composed = {"value": "caf\N{LATIN SMALL LETTER E WITH ACUTE}"}
        decomposed = {"value": "cafe\N{COMBINING ACUTE ACCENT}"}
        self.assertNotEqual(
            canonical_json_bytes(composed),
            canonical_json_bytes(decomposed),
        )

    def test_float_non_string_key_and_non_json_value_are_rejected(self) -> None:
        invalid = (
            {"value": 1.5},
            {1: "not-a-string-key"},
            {"value": (1, 2)},
            {"value": b"bytes"},
        )
        for value in invalid:
            with self.subTest(value=value):
                with self.assertRaises(CoverageV2ContractError):
                    canonical_json_bytes(value)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 3: Run the test and confirm the package is absent**

Run:

```bash
uv run python -m unittest tests.test_coverage_v2_canonical.CanonicalJsonTest -v
```

Expected: FAIL with `ModuleNotFoundError: No module named 'pg_case_factory.coverage_v2'`.

- [ ] **Step 4: Add the runtime dependency without overwriting project metadata**

In the dedicated worktree, change only the dependency array in `pyproject.toml` to include:

```toml
dependencies = [
  "PyYAML>=6.0.2",
  "rfc8785>=0.1.4,<1",
]
```

Run:

```bash
uv lock
git diff -- pyproject.toml uv.lock
```

Expected: the diff adds `rfc8785` and its lock entry. It must not change the project version,
description, entry points, or unrelated dependencies.

- [ ] **Step 5: Add the exception module**

Create `src/pg_case_factory/coverage_v2/errors.py`:

```python
class CoverageV2Error(ValueError):
    """Base class for fail-closed coverage V2 errors."""


class CoverageV2ContractError(CoverageV2Error):
    """Raised when canonical or contract-shaped data is invalid."""


class CoverageV2ArtifactError(CoverageV2Error):
    """Raised when an artifact or declared predecessor graph is invalid."""
```

- [ ] **Step 6: Implement pure JCS with the V2 no-float contract**

Create `src/pg_case_factory/coverage_v2/canonical.py`:

```python
from __future__ import annotations

import hashlib
from typing import Any

import rfc8785

from .errors import CoverageV2ContractError


CANONICAL_JSON_VERSION = "rfc8785-no-float-v1"


def _validate_json_value(value: Any, location: str) -> None:
    if value is None or type(value) in (bool, int, str):
        return
    if isinstance(value, float):
        raise CoverageV2ContractError(f"{location} must not contain float values")
    if isinstance(value, list):
        for index, item in enumerate(value):
            _validate_json_value(item, f"{location}[{index}]")
        return
    if isinstance(value, dict):
        for key, item in value.items():
            if not isinstance(key, str):
                raise CoverageV2ContractError(f"{location} keys must be strings")
            _validate_json_value(item, f"{location}.{key}")
        return
    raise CoverageV2ContractError(
        f"{location} contains unsupported {type(value).__name__}"
    )


def canonical_json_bytes(value: Any) -> bytes:
    _validate_json_value(value, "value")
    try:
        return rfc8785.dumps(value)
    except (TypeError, ValueError) as exc:
        raise CoverageV2ContractError(f"cannot canonicalize value: {exc}") from exc


def sha256_hex(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()
```

- [ ] **Step 7: Add the package marker**

Create `src/pg_case_factory/coverage_v2/__init__.py`:

```python
"""Fail-closed full statement coverage V2 primitives."""

SCHEMA_VERSION = 2

__all__ = ["SCHEMA_VERSION"]
```

- [ ] **Step 8: Run the canonical tests**

Run:

```bash
uv run python -m unittest tests.test_coverage_v2_canonical.CanonicalJsonTest -v
```

Expected: 3 tests PASS.

- [ ] **Step 9: Commit only Task 1 files**

Run:

```bash
git add pyproject.toml uv.lock \
  src/pg_case_factory/coverage_v2/__init__.py \
  src/pg_case_factory/coverage_v2/errors.py \
  src/pg_case_factory/coverage_v2/canonical.py \
  tests/test_coverage_v2_canonical.py
git diff --cached --name-only
```

Expected: exactly the six paths above. Then run:

```bash
git commit -m "feat: add coverage v2 canonical bytes"
```

### Task 2: All 17 domain-separated logical ID kinds

**Files:**
- Create: `src/pg_case_factory/coverage_v2/ids.py`
- Modify: `src/pg_case_factory/coverage_v2/__init__.py`
- Modify: `tests/test_coverage_v2_canonical.py`

- [ ] **Step 1: Add failing ID tests**

Append to `tests/test_coverage_v2_canonical.py` before the final `if __name__` block:

```python
from pg_case_factory.coverage_v2.ids import (
    ALLOWED_ID_KINDS,
    LogicalIdRegistry,
    logical_id,
)


class LogicalIdTest(unittest.TestCase):
    def test_kind_set_matches_the_frozen_spec(self) -> None:
        self.assertEqual(
            {
                "GRM", "FOB", "INV", "RISK", "NA", "INT", "AXI", "ITUP",
                "PROD", "PTUP", "STUP", "ATOM", "SUB", "PROGRAM",
                "BUNDLE", "SHARD", "WIT",
            },
            ALLOWED_ID_KINDS,
        )

    def test_fixed_vector_kind_separation_and_id_only_nfc(self) -> None:
        components = ["insert", "branch", "intent", "sfv-1", "ctx", "role"]
        factor = logical_id("FOB", components)
        grammar = logical_id("GRM", components)
        self.assertEqual(
            "FOB-17f39272f8c543a6fad7053797ece535da1051eec798bf0f98c1e52e07b060e0",
            factor,
        )
        self.assertNotEqual(factor.split("-", 1)[1], grammar.split("-", 1)[1])
        composed = ["insert", "caf\N{LATIN SMALL LETTER E WITH ACUTE}"]
        decomposed = ["insert", "cafe\N{COMBINING ACUTE ACCENT}"]
        self.assertEqual(logical_id("INV", composed), logical_id("INV", decomposed))

    def test_unknown_kind_empty_component_and_false_declaration_fail(self) -> None:
        registry = LogicalIdRegistry()
        components = ["insert", "branch", "intent", "sfv-1", "ctx", "role"]
        invalid_calls = (
            lambda: logical_id("fob", components),
            lambda: logical_id("UNKNOWN", components),
            lambda: logical_id("FOB", ["insert", ""]),
            lambda: registry.register_declared("GRM-" + "0" * 64, "FOB", components),
            lambda: registry.register_declared("FOB-" + "0" * 64, "FOB", components),
        )
        for call in invalid_calls:
            with self.subTest(call=call):
                with self.assertRaises(CoverageV2ContractError):
                    call()
```

Move the existing final `if __name__ == "__main__":` block below these imports and tests.

- [ ] **Step 2: Run the ID tests and confirm failure**

Run:

```bash
uv run python -m unittest tests.test_coverage_v2_canonical.LogicalIdTest -v
```

Expected: FAIL because `ids.py` is absent.

- [ ] **Step 3: Implement the exact ID codec and collision registry**

Create `src/pg_case_factory/coverage_v2/ids.py`:

```python
from __future__ import annotations

import re
import unicodedata
from collections.abc import Sequence
from dataclasses import dataclass, field

from .canonical import canonical_json_bytes, sha256_hex
from .errors import CoverageV2ContractError


ID_DOMAIN = b"FSCR_ID_V2\0"
ALLOWED_ID_KINDS = frozenset(
    {
        "GRM", "FOB", "INV", "RISK", "NA", "INT", "AXI", "ITUP",
        "PROD", "PTUP", "STUP", "ATOM", "SUB", "PROGRAM",
        "BUNDLE", "SHARD", "WIT",
    }
)
DECLARED_ID = re.compile(r"^([A-Z]+)-([0-9a-f]{64})$")


def _normalized_components(components: Sequence[str]) -> tuple[str, ...]:
    if isinstance(components, (str, bytes, bytearray)):
        raise CoverageV2ContractError("logical ID components must be a sequence")
    result: list[str] = []
    for index, component in enumerate(components):
        if not isinstance(component, str) or not component:
            raise CoverageV2ContractError(
                f"logical ID component {index} must be a non-empty string"
            )
        result.append(unicodedata.normalize("NFC", component))
    return tuple(result)


def logical_id(kind: str, components: Sequence[str]) -> str:
    if kind not in ALLOWED_ID_KINDS:
        raise CoverageV2ContractError(f"unsupported logical ID kind {kind!r}")
    normalized = _normalized_components(components)
    digest = sha256_hex(ID_DOMAIN + canonical_json_bytes([kind, *normalized]))
    return f"{kind}-{digest}"


@dataclass
class LogicalIdRegistry:
    by_id: dict[str, tuple[str, tuple[str, ...]]] = field(default_factory=dict)
    by_components: dict[tuple[str, tuple[str, ...]], str] = field(default_factory=dict)

    def register(self, kind: str, components: Sequence[str]) -> str:
        declared = logical_id(kind, components)
        return self.register_declared(declared, kind, components)

    def register_declared(
        self,
        declared_id: str,
        kind: str,
        components: Sequence[str],
    ) -> str:
        match = DECLARED_ID.fullmatch(declared_id)
        if match is None or match.group(1) != kind:
            raise CoverageV2ContractError("declared logical ID has invalid syntax or kind")
        normalized = _normalized_components(components)
        expected = logical_id(kind, normalized)
        if declared_id != expected:
            raise CoverageV2ContractError("declared logical ID differs from recomputed ID")
        identity = (kind, normalized)
        existing_identity = self.by_id.get(declared_id)
        if existing_identity is not None and existing_identity != identity:
            raise CoverageV2ContractError("one logical ID maps to different components")
        existing_id = self.by_components.get(identity)
        if existing_id is not None and existing_id != declared_id:
            raise CoverageV2ContractError("one component tuple maps to different logical IDs")
        self.by_id[declared_id] = identity
        self.by_components[identity] = declared_id
        return declared_id
```

- [ ] **Step 4: Export the ID API**

Replace `src/pg_case_factory/coverage_v2/__init__.py` with:

```python
"""Fail-closed full statement coverage V2 primitives."""

from .ids import ALLOWED_ID_KINDS, LogicalIdRegistry, logical_id

SCHEMA_VERSION = 2

__all__ = [
    "ALLOWED_ID_KINDS",
    "LogicalIdRegistry",
    "SCHEMA_VERSION",
    "logical_id",
]
```

- [ ] **Step 5: Run all canonical and ID tests**

Run:

```bash
uv run python -m unittest tests.test_coverage_v2_canonical -v
```

Expected: 6 tests PASS.

- [ ] **Step 6: Commit only Task 2 files**

Run:

```bash
git add src/pg_case_factory/coverage_v2/ids.py \
  src/pg_case_factory/coverage_v2/__init__.py \
  tests/test_coverage_v2_canonical.py
git diff --cached --name-only
```

Expected: exactly the three paths above. Then run:

```bash
git commit -m "feat: add full coverage v2 logical ids"
```

### Task 3: Canonical envelopes and current-byte-backed declared DAG verification

**Files:**
- Create: `src/pg_case_factory/coverage_v2/artifacts.py`
- Create: `tests/test_coverage_v2_artifacts.py`

- [ ] **Step 1: Add failing envelope and manifest tests**

Create `tests/test_coverage_v2_artifacts.py`:

```python
from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from pg_case_factory.coverage_v2.artifacts import (
    ArtifactBinding,
    ManifestDomain,
    artifact_bytes,
    artifact_semantic_sha256,
    build_artifact,
    manifest_digest,
    verify_declared_artifact_graph,
)
from pg_case_factory.coverage_v2.errors import CoverageV2ArtifactError


class ArtifactEnvelopeTest(unittest.TestCase):
    def test_fixed_semantic_hash_excludes_operational_metadata(self) -> None:
        document = build_artifact(
            artifact_id="ART-1",
            kind="input-lock",
            semantic_payload={"inputs": []},
            predecessors=(),
            operational_metadata={"attempt": 9},
        )
        self.assertEqual(
            "70a44df23b65bc837e757a637e7047b74541dbe30ea9616a77caa4714be34cb5",
            document["semantic_sha256"],
        )
        changed = dict(document)
        changed["operational_metadata"] = {"attempt": 10}
        self.assertEqual(
            document["semantic_sha256"],
            artifact_semantic_sha256(changed),
        )
        self.assertNotEqual(artifact_bytes(document), artifact_bytes(changed))

    def test_manifest_digest_has_a_fixed_domain_and_rejects_duplicates(self) -> None:
        bindings = (
            ArtifactBinding("B", "b.json", "b" * 64, "2" * 64, "kind-b", 2),
            ArtifactBinding("A", "a.json", "a" * 64, "1" * 64, "kind-a", 2),
        )
        self.assertEqual(
            "93a2d62a66b4d9cc7ccbe214c0a9e69794dd584593b86ceb73deb44e78bada0f",
            manifest_digest(ManifestDomain.VALIDATED_PLAN, bindings),
        )
        with self.assertRaises(CoverageV2ArtifactError):
            manifest_digest(ManifestDomain.VALIDATED_PLAN, (bindings[0], bindings[0]))
        with self.assertRaises(CoverageV2ArtifactError):
            manifest_digest("CALLER_CHOSEN", bindings)  # type: ignore[arg-type]
        malformed = (
            ArtifactBinding("", "bad-id.json", "c" * 64, "3" * 64, "bad", 2),
            ArtifactBinding("C", "bad-sha.json", "c" * 64, "not-a-sha", "bad", 2),
        )
        for binding in malformed:
            with self.subTest(binding=binding):
                with self.assertRaises(CoverageV2ArtifactError):
                    manifest_digest(ManifestDomain.VALIDATED_PLAN, (binding,))


class DeclaredArtifactGraphTest(unittest.TestCase):
    def _write(self, root: Path, name: str, document: dict[str, object]) -> None:
        root.joinpath(name).write_bytes(artifact_bytes(document))

    def test_current_files_pass_and_stale_predecessor_fails(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            parent = build_artifact(
                artifact_id="A",
                kind="input-lock",
                semantic_payload={"version": 1},
                predecessors=(),
            )
            parent_binding = ArtifactBinding(
                "A", "a.json", "0" * 64,
                str(parent["semantic_sha256"]), "input-lock", 2,
            )
            child = build_artifact(
                artifact_id="B",
                kind="plan-validation",
                semantic_payload={"passed": True},
                predecessors=(parent_binding,),
            )
            self._write(root, "a.json", parent)
            self._write(root, "b.json", child)
            graph = verify_declared_artifact_graph(root, ("b.json", "a.json"))
            self.assertEqual({"A", "B"}, set(graph.bindings))

            replacement = build_artifact(
                artifact_id="A",
                kind="input-lock",
                semantic_payload={"version": 2},
                predecessors=(),
            )
            self._write(root, "a.json", replacement)
            with self.assertRaisesRegex(CoverageV2ArtifactError, "predecessor"):
                verify_declared_artifact_graph(root, ("a.json", "b.json"))

    def test_cycle_is_reported_before_stale_semantic_hash(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            a = build_artifact(
                artifact_id="A",
                kind="kind-a",
                semantic_payload={},
                predecessors=(),
            )
            b = build_artifact(
                artifact_id="B",
                kind="kind-b",
                semantic_payload={},
                predecessors=(),
            )
            a["predecessors"] = {"B": str(b["semantic_sha256"])}
            b["predecessors"] = {"A": str(a["semantic_sha256"])}
            self._write(root, "a.json", a)
            self._write(root, "b.json", b)
            with self.assertRaisesRegex(CoverageV2ArtifactError, "cycle"):
                verify_declared_artifact_graph(root, ("a.json", "b.json"))

    def test_duplicate_json_key_missing_file_and_symlink_fail(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            root.joinpath("duplicate.json").write_text(
                '{"schema_version":2,"schema_version":2}',
                encoding="utf-8",
            )
            with self.assertRaises(CoverageV2ArtifactError):
                verify_declared_artifact_graph(root, ("duplicate.json",))
            root.joinpath("nan.json").write_text('{"value":NaN}', encoding="utf-8")
            with self.assertRaisesRegex(CoverageV2ArtifactError, "invalid JSON constant"):
                verify_declared_artifact_graph(root, ("nan.json",))
            canonical = build_artifact(
                artifact_id="FLOAT",
                kind="input-lock",
                semantic_payload={},
                predecessors=(),
            )
            canonical["operational_metadata"] = {"finite_float": 1.5}
            root.joinpath("float.json").write_text(json.dumps(canonical), encoding="utf-8")
            with self.assertRaises(CoverageV2ArtifactError):
                verify_declared_artifact_graph(root, ("float.json",))
            pretty = build_artifact(
                artifact_id="PRETTY",
                kind="input-lock",
                semantic_payload={},
                predecessors=(),
            )
            root.joinpath("pretty.json").write_text(
                json.dumps(pretty, indent=2) + "\n",
                encoding="utf-8",
            )
            with self.assertRaisesRegex(CoverageV2ArtifactError, "not canonical"):
                verify_declared_artifact_graph(root, ("pretty.json",))
            with self.assertRaises(CoverageV2ArtifactError):
                verify_declared_artifact_graph(root, ("missing.json",))

            target = root.joinpath("target.json")
            target.write_text(json.dumps({}), encoding="utf-8")
            root.joinpath("link.json").symlink_to(target)
            with self.assertRaises(CoverageV2ArtifactError):
                verify_declared_artifact_graph(root, ("link.json",))


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run the tests and confirm failure**

Run:

```bash
uv run python -m unittest tests.test_coverage_v2_artifacts -v
```

Expected: FAIL because `artifacts.py` is absent.

- [ ] **Step 3: Implement exact envelopes, byte loading, DAG verification, and digest**

Create `src/pg_case_factory/coverage_v2/artifacts.py`:

```python
from __future__ import annotations

import json
import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from enum import Enum
from pathlib import Path, PurePosixPath
from types import MappingProxyType
from typing import Any

from .canonical import canonical_json_bytes, sha256_hex
from .errors import CoverageV2ArtifactError, CoverageV2ContractError


ARTIFACT_DOMAIN = b"FSCR_ARTIFACT_V2\0"
SHA256_HEX = re.compile(r"^[0-9a-f]{64}$")
ENVELOPE_KEYS = frozenset(
    {
        "schema_version",
        "kind",
        "artifact_id",
        "predecessors",
        "semantic_payload",
        "semantic_sha256",
        "operational_metadata",
    }
)


class ManifestDomain(str, Enum):
    VALIDATED_PLAN = "FSCR_VALIDATED_PLAN_V2"


@dataclass(frozen=True)
class ArtifactBinding:
    artifact_id: str
    relative_path: str
    byte_sha256: str
    semantic_sha256: str
    kind: str
    schema_version: int


@dataclass(frozen=True)
class VerifiedArtifactGraph:
    bindings: Mapping[str, ArtifactBinding]


@dataclass(frozen=True)
class _ArtifactCandidate:
    relative_path: str
    raw_bytes: bytes
    document: Mapping[str, Any]


def _semantic_projection(document: Mapping[str, Any]) -> dict[str, Any]:
    required = (
        "schema_version",
        "kind",
        "artifact_id",
        "predecessors",
        "semantic_payload",
    )
    missing = [key for key in required if key not in document]
    if missing:
        raise CoverageV2ArtifactError(f"artifact semantic projection missing {missing}")
    return {key: document[key] for key in required}


def artifact_semantic_sha256(document: Mapping[str, Any]) -> str:
    try:
        payload = canonical_json_bytes(_semantic_projection(document))
    except CoverageV2ContractError as exc:
        raise CoverageV2ArtifactError(str(exc)) from exc
    return sha256_hex(ARTIFACT_DOMAIN + payload)


def _validate_envelope_shape(document: Mapping[str, Any]) -> None:
    if frozenset(document) != ENVELOPE_KEYS:
        raise CoverageV2ArtifactError("artifact envelope key set differs")
    if document["schema_version"] != 2:
        raise CoverageV2ArtifactError("artifact schema_version must equal 2")
    for key in ("kind", "artifact_id"):
        if not isinstance(document[key], str) or not document[key]:
            raise CoverageV2ArtifactError(f"artifact {key} must be a non-empty string")
    if not isinstance(document["semantic_payload"], dict):
        raise CoverageV2ArtifactError("artifact semantic_payload must be an object")
    if document["operational_metadata"] is not None and not isinstance(
        document["operational_metadata"], dict
    ):
        raise CoverageV2ArtifactError("artifact operational_metadata must be null or object")
    predecessors = document["predecessors"]
    if not isinstance(predecessors, dict):
        raise CoverageV2ArtifactError("artifact predecessors must be an object")
    for predecessor_id, semantic_sha in predecessors.items():
        if not isinstance(predecessor_id, str) or not predecessor_id:
            raise CoverageV2ArtifactError("predecessor ID must be a non-empty string")
        if not isinstance(semantic_sha, str) or SHA256_HEX.fullmatch(semantic_sha) is None:
            raise CoverageV2ArtifactError("predecessor semantic SHA must be lowercase SHA-256")
    semantic_sha = document["semantic_sha256"]
    if not isinstance(semantic_sha, str) or SHA256_HEX.fullmatch(semantic_sha) is None:
        raise CoverageV2ArtifactError("artifact semantic SHA must be lowercase SHA-256")


def build_artifact(
    *,
    artifact_id: str,
    kind: str,
    semantic_payload: Mapping[str, Any],
    predecessors: Sequence[ArtifactBinding],
    operational_metadata: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    predecessor_map: dict[str, str] = {}
    for binding in sorted(predecessors, key=lambda item: item.artifact_id.encode("utf-8")):
        if binding.artifact_id in predecessor_map:
            raise CoverageV2ArtifactError("artifact has duplicate predecessor ID")
        predecessor_map[binding.artifact_id] = binding.semantic_sha256
    document: dict[str, Any] = {
        "schema_version": 2,
        "kind": kind,
        "artifact_id": artifact_id,
        "predecessors": predecessor_map,
        "semantic_payload": dict(semantic_payload),
        "semantic_sha256": "0" * 64,
        "operational_metadata": (
            None if operational_metadata is None else dict(operational_metadata)
        ),
    }
    document["semantic_sha256"] = artifact_semantic_sha256(document)
    _validate_envelope_shape(document)
    artifact_bytes(document)
    return document


def artifact_bytes(document: Mapping[str, Any]) -> bytes:
    _validate_envelope_shape(document)
    try:
        return canonical_json_bytes(dict(document)) + b"\n"
    except CoverageV2ContractError as exc:
        raise CoverageV2ArtifactError(str(exc)) from exc


def _reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise CoverageV2ArtifactError(f"duplicate JSON key {key!r}")
        result[key] = value
    return result


def _safe_candidate_path(repository_root: Path, relative_path: str) -> Path:
    pure = PurePosixPath(relative_path)
    if pure.is_absolute() or not pure.parts or any(part in ("", ".", "..") for part in pure.parts):
        raise CoverageV2ArtifactError("artifact path must be a safe repository-relative path")
    root = repository_root.resolve(strict=True)
    candidate = root
    for part in pure.parts:
        candidate = candidate.joinpath(part)
        if candidate.is_symlink():
            raise CoverageV2ArtifactError("artifact path must not contain symlinks")
    try:
        resolved = candidate.resolve(strict=True)
        resolved.relative_to(root)
    except (FileNotFoundError, ValueError) as exc:
        raise CoverageV2ArtifactError("artifact path is missing or outside the root") from exc
    if not resolved.is_file():
        raise CoverageV2ArtifactError("artifact path must name a regular file")
    return resolved


def _read_candidate(repository_root: Path, relative_path: str) -> _ArtifactCandidate:
    path = _safe_candidate_path(repository_root, relative_path)
    raw_bytes = path.read_bytes()
    try:
        text = raw_bytes.decode("utf-8")
        document = json.loads(
            text,
            object_pairs_hook=_reject_duplicate_keys,
            parse_constant=lambda token: (_ for _ in ()).throw(
                CoverageV2ArtifactError(f"invalid JSON constant {token}")
            ),
        )
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise CoverageV2ArtifactError("artifact is not valid UTF-8 JSON") from exc
    if not isinstance(document, dict):
        raise CoverageV2ArtifactError("artifact root must be an object")
    _validate_envelope_shape(document)
    expected_bytes = artifact_bytes(document)
    if raw_bytes != expected_bytes:
        raise CoverageV2ArtifactError("artifact bytes are not canonical")
    return _ArtifactCandidate(relative_path, raw_bytes, document)


def _detect_cycle(documents: Mapping[str, Mapping[str, Any]]) -> None:
    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(artifact_id: str) -> None:
        if artifact_id in visiting:
            raise CoverageV2ArtifactError("artifact predecessor graph contains a cycle")
        if artifact_id in visited:
            return
        visiting.add(artifact_id)
        predecessors = documents[artifact_id]["predecessors"]
        assert isinstance(predecessors, dict)
        for predecessor_id in predecessors:
            if predecessor_id not in documents:
                raise CoverageV2ArtifactError(
                    f"artifact predecessor {predecessor_id} is absent from current files"
                )
            visit(predecessor_id)
        visiting.remove(artifact_id)
        visited.add(artifact_id)

    for artifact_id in sorted(documents, key=lambda value: value.encode("utf-8")):
        visit(artifact_id)


def verify_declared_artifact_graph(
    repository_root: Path,
    relative_paths: Sequence[str],
) -> VerifiedArtifactGraph:
    candidates: dict[str, _ArtifactCandidate] = {}
    documents: dict[str, Mapping[str, Any]] = {}
    for relative_path in relative_paths:
        candidate = _read_candidate(repository_root, relative_path)
        artifact_id = candidate.document["artifact_id"]
        assert isinstance(artifact_id, str)
        if artifact_id in candidates:
            raise CoverageV2ArtifactError("duplicate artifact ID in current files")
        candidates[artifact_id] = candidate
        documents[artifact_id] = candidate.document

    _detect_cycle(documents)

    bindings: dict[str, ArtifactBinding] = {}
    for artifact_id, candidate in candidates.items():
        expected = artifact_semantic_sha256(candidate.document)
        if candidate.document["semantic_sha256"] != expected:
            raise CoverageV2ArtifactError("artifact semantic SHA differs from current content")
        bindings[artifact_id] = ArtifactBinding(
            artifact_id=artifact_id,
            relative_path=candidate.relative_path,
            byte_sha256=sha256_hex(candidate.raw_bytes),
            semantic_sha256=expected,
            kind=str(candidate.document["kind"]),
            schema_version=2,
        )

    for artifact_id, document in documents.items():
        predecessors = document["predecessors"]
        assert isinstance(predecessors, dict)
        for predecessor_id, expected_sha in predecessors.items():
            actual_sha = bindings[predecessor_id].semantic_sha256
            if actual_sha != expected_sha:
                raise CoverageV2ArtifactError(
                    f"artifact predecessor {predecessor_id} differs from current semantic SHA"
                )

    return VerifiedArtifactGraph(MappingProxyType(dict(bindings)))


def manifest_digest(
    domain: ManifestDomain,
    artifacts: Sequence[ArtifactBinding],
) -> str:
    if not isinstance(domain, ManifestDomain):
        raise CoverageV2ArtifactError("manifest digest domain is not frozen")
    seen: set[str] = set()
    records: list[dict[str, str]] = []
    for binding in artifacts:
        if not isinstance(binding.artifact_id, str) or not binding.artifact_id:
            raise CoverageV2ArtifactError("manifest artifact ID must be non-empty")
        if (
            not isinstance(binding.semantic_sha256, str)
            or SHA256_HEX.fullmatch(binding.semantic_sha256) is None
        ):
            raise CoverageV2ArtifactError(
                "manifest artifact semantic SHA must be lowercase SHA-256"
            )
        if binding.artifact_id in seen:
            raise CoverageV2ArtifactError("manifest has duplicate artifact ID")
        seen.add(binding.artifact_id)
        records.append(
            {
                "artifact_id": binding.artifact_id,
                "semantic_sha256": binding.semantic_sha256,
            }
        )
    records.sort(key=lambda item: item["artifact_id"].encode("utf-8"))
    return sha256_hex(
        domain.value.encode("ascii") + b"\0" + canonical_json_bytes(records)
    )
```

- [ ] **Step 4: Run all artifact tests**

Run:

```bash
uv run python -m unittest tests.test_coverage_v2_artifacts -v
```

Expected: 5 tests PASS.

- [ ] **Step 5: Commit only Task 3 files**

Run:

```bash
git add src/pg_case_factory/coverage_v2/artifacts.py \
  tests/test_coverage_v2_artifacts.py
git diff --cached --name-only
```

Expected: exactly the two paths above. Then run:

```bash
git commit -m "feat: add coverage v2 artifact primitives"
```

### Task 4: Verify the isolated increment and stop

**Files:**
- No source changes unless a targeted test exposes a defect

- [ ] **Step 1: Run the complete new test set**

Run:

```bash
uv run python -m unittest \
  tests.test_coverage_v2_canonical \
  tests.test_coverage_v2_artifacts -v
```

Expected: 11 tests PASS.

- [ ] **Step 2: Run compile and existing package boundaries**

Run:

```bash
uv run python -m compileall -q src/pg_case_factory/coverage_v2 tests/test_coverage_v2_canonical.py tests/test_coverage_v2_artifacts.py
uv run python -m unittest tests.test_feature_contracts tests.test_coverage tests.test_cli -v
```

Expected: compilation succeeds and all selected V1 tests PASS.

- [ ] **Step 3: Prove that this increment emitted no repository artifacts or SQL**

Run:

```bash
(
  find \
    artifacts/intermediates/full-statement-coverage-v2 \
    artifacts/regress \
    -type f -exec shasum -a 256 {} + 2>/dev/null || true
) | LC_ALL=C sort > "$(git rev-parse --git-path fscr-v2-core-after.sha256)"
cmp \
  "$(git rev-parse --git-path fscr-v2-core-before.sha256)" \
  "$(git rev-parse --git-path fscr-v2-core-after.sha256)"
git diff HEAD~3..HEAD --check
```

Expected: `cmp` and the three-commit `git diff --check` both exit 0 with no output.

- [ ] **Step 4: Verify final scope and hand off**

Run:

```bash
git log -3 --oneline
git status --short
```

Expected: exactly three task commits belong to this increment. No V2 CLI, schema registry,
input lock, revision store, state machine, readiness claim, formal evidence, or SQL exists.

Stop here. The next plans, each independently reviewed before execution, are:

1. strict schema registry and exact direct-predecessor policies;
2. immutable input locks and collision-safe run IDs;
3. revision allocation, atomic publication, and verified current pointers;
4. evidence-backed planning/runtime state machines.
