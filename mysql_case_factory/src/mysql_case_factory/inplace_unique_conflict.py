"""Deterministic virtual scenarios for INPLACE DDL unique conflicts.

The batch is deliberately virtual: the 2,304 scenarios are generated lazily by
factor combination instead of being written as individual SQL files.  Each
operation exposes one canonical DDL statement that always requests
``ALGORITHM=INPLACE`` and ``LOCK=NONE``; the legacy ``MODIFY`` and ``CHANGE``
column forms are intentionally absent.
"""

from __future__ import annotations

import gzip
import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterator

INPLACE_UNIQUE_BATCH_ID = "2026-10-20-inplace-ddl-unique-conflict-v1"
INPLACE_UNIQUE_BATCH_KIND = "inplace_unique_conflict_extension"
INPLACE_UNIQUE_CASE_PREFIX = "TUCUI"
INPLACE_UNIQUE_DATABASE = "qa_inplace_unique_conflict"
INPLACE_UNIQUE_PROFILES = ("copy", "inplace", "instant")

CONFLICT_SURFACES = (
    "existing_unique",
    "new_unique",
    "composite_unique",
    "nullable_unique",
)
CONFLICT_PATTERNS = (
    "seed_duplicate",
    "concurrent_duplicate",
    "semantic_collision",
    "boundary_duplicate",
)
PHASES = ("during_ddl", "before_and_during_ddl", "across_ddl_transaction")
WORKER_COUNTS = (4, 16)
DATA_STATES = ("normal", "boundary")
FORBIDDEN_DDL_TYPES = ("MODIFY", "CHANGE")

SCENARIO_COUNT = (
    12
    * len(CONFLICT_SURFACES)
    * len(CONFLICT_PATTERNS)
    * len(PHASES)
    * len(WORKER_COUNTS)
    * len(DATA_STATES)
)
SCENARIOS_PER_OPERATION = SCENARIO_COUNT // 12


@dataclass(frozen=True)
class InplaceUniqueOperation:
    """A canonical DDL operation used by the virtual runner."""

    operation_id: str
    description: str
    ddl_sql: str

    def to_json(self) -> dict[str, Any]:
        return {
            "operation_id": self.operation_id,
            "description": self.description,
            "ddl_sql": self.ddl_sql,
        }


@dataclass(frozen=True)
class InplaceUniqueScenario:
    """One lazily generated factor combination."""

    case_no: int
    operation_id: str
    conflict_surface: str
    conflict_pattern: str
    phase: str
    workers: int
    data_state: str
    ddl_sql: str
    smoke: bool = False

    @property
    def case_id(self) -> str:
        return f"{INPLACE_UNIQUE_CASE_PREFIX}-{self.case_no:06d}"

    @property
    def batch_id(self) -> str:
        return INPLACE_UNIQUE_BATCH_ID

    @property
    def batch_kind(self) -> str:
        return INPLACE_UNIQUE_BATCH_KIND

    @property
    def database(self) -> str:
        return INPLACE_UNIQUE_DATABASE

    def to_json(self) -> dict[str, Any]:
        return {
            "batch_id": self.batch_id,
            "batch_kind": self.batch_kind,
            "case_id": self.case_id,
            "case_no": self.case_no,
            "conflict_pattern": self.conflict_pattern,
            "conflict_surface": self.conflict_surface,
            "data_state": self.data_state,
            "database": self.database,
            "ddl_sql": self.ddl_sql,
            "operation_id": self.operation_id,
            "phase": self.phase,
            "profiles": list(INPLACE_UNIQUE_PROFILES),
            "smoke": self.smoke,
            "workers": self.workers,
        }


def inplace_unique_operations() -> tuple[InplaceUniqueOperation, ...]:
    """Return the 12 canonical operations in deterministic batch order."""

    operations = (
        InplaceUniqueOperation(
            "add_index",
            "Add a non-unique secondary index during concurrent writes.",
            "ALTER TABLE `tucui_unique_target`\n"
            "  ADD INDEX `idx_tucui_value` (`value`),\n"
            "  ALGORITHM=INPLACE,\n"
            "  LOCK=NONE;\n",
        ),
        InplaceUniqueOperation(
            "drop_index",
            "Drop a non-unique secondary index during concurrent writes.",
            "ALTER TABLE `tucui_unique_target`\n"
            "  DROP INDEX `idx_tucui_value`,\n"
            "  ALGORITHM=INPLACE,\n"
            "  LOCK=NONE;\n",
        ),
        InplaceUniqueOperation(
            "add_unique",
            "Add a unique index while duplicate rows are possible.",
            "ALTER TABLE `tucui_unique_target`\n"
            "  ADD UNIQUE INDEX `uk_tucui_value` (`value`),\n"
            "  ALGORITHM=INPLACE,\n"
            "  LOCK=NONE;\n",
        ),
        InplaceUniqueOperation(
            "drop_unique",
            "Drop a unique index during concurrent writes.",
            "ALTER TABLE `tucui_unique_target`\n"
            "  DROP INDEX `uk_tucui_value`,\n"
            "  ALGORITHM=INPLACE,\n"
            "  LOCK=NONE;\n",
        ),
        InplaceUniqueOperation(
            "rename_index",
            "Rename a secondary index during concurrent writes.",
            "ALTER TABLE `tucui_unique_target`\n"
            "  RENAME INDEX `idx_tucui_value` TO `idx_tucui_value_renamed`,\n"
            "  ALGORITHM=INPLACE,\n"
            "  LOCK=NONE;\n",
        ),
        InplaceUniqueOperation(
            "add_column",
            "Add a column without using the legacy column-replacement forms.",
            "ALTER TABLE `tucui_unique_target`\n"
            "  ADD COLUMN `extra_value` VARCHAR(64) NOT NULL DEFAULT '',\n"
            "  ALGORITHM=INPLACE,\n"
            "  LOCK=NONE;\n",
        ),
        InplaceUniqueOperation(
            "drop_column",
            "Drop a non-key column during concurrent writes.",
            "ALTER TABLE `tucui_unique_target`\n"
            "  DROP COLUMN `extra_value`,\n"
            "  ALGORITHM=INPLACE,\n"
            "  LOCK=NONE;\n",
        ),
        InplaceUniqueOperation(
            "rename_column",
            "Rename a column with the explicit RENAME COLUMN syntax.",
            "ALTER TABLE `tucui_unique_target`\n"
            "  RENAME COLUMN `extra_value` TO `extra_value_renamed`,\n"
            "  ALGORITHM=INPLACE,\n"
            "  LOCK=NONE;\n",
        ),
        InplaceUniqueOperation(
            "add_foreign_key",
            "Add a foreign key while concurrent writes are active.",
            "ALTER TABLE `tucui_unique_target`\n"
            "  ADD CONSTRAINT `fk_tucui_parent`\n"
            "    FOREIGN KEY (`parent_id`) REFERENCES `tucui_unique_parent` (`id`),\n"
            "  ALGORITHM=INPLACE,\n"
            "  LOCK=NONE;\n",
        ),
        InplaceUniqueOperation(
            "drop_foreign_key",
            "Drop a foreign key during concurrent writes.",
            "ALTER TABLE `tucui_unique_target`\n"
            "  DROP FOREIGN KEY `fk_tucui_parent`,\n"
            "  ALGORITHM=INPLACE,\n"
            "  LOCK=NONE;\n",
        ),
        InplaceUniqueOperation(
            "drop_check",
            "Drop a CHECK constraint during concurrent writes.",
            "ALTER TABLE `tucui_unique_target`\n"
            "  DROP CHECK `chk_tucui_value`,\n"
            "  ALGORITHM=INPLACE,\n"
            "  LOCK=NONE;\n",
        ),
        InplaceUniqueOperation(
            "drop_generated",
            "Drop a generated column during concurrent writes.",
            "ALTER TABLE `tucui_unique_target`\n"
            "  DROP COLUMN `generated_value`,\n"
            "  ALGORITHM=INPLACE,\n"
            "  LOCK=NONE;\n",
        ),
    )
    _validate_operations(operations)
    return operations


def _validate_operations(
    operations: tuple[InplaceUniqueOperation, ...],
) -> None:
    expected_ids = (
        "add_index",
        "drop_index",
        "add_unique",
        "drop_unique",
        "rename_index",
        "add_column",
        "drop_column",
        "rename_column",
        "add_foreign_key",
        "drop_foreign_key",
        "drop_check",
        "drop_generated",
    )
    operation_ids = tuple(operation.operation_id for operation in operations)
    if operation_ids != expected_ids or len(set(operation_ids)) != 12:
        raise AssertionError(f"unexpected INPLACE unique operation set: {operation_ids}")
    for operation in operations:
        ddl = operation.ddl_sql
        if "ALGORITHM=INPLACE" not in ddl or "LOCK=NONE" not in ddl:
            raise AssertionError(f"canonical DDL is not INPLACE/LOCK=NONE: {operation.operation_id}")
        if any(forbidden in ddl.upper() for forbidden in FORBIDDEN_DDL_TYPES):
            raise AssertionError(f"forbidden DDL type in {operation.operation_id}")


def _is_smoke_combination(
    conflict_surface: str,
    conflict_pattern: str,
    phase: str,
    workers: int,
    data_state: str,
) -> bool:
    return (
        conflict_surface == CONFLICT_SURFACES[0]
        and conflict_pattern == CONFLICT_PATTERNS[0]
        and phase == PHASES[0]
        and workers == WORKER_COUNTS[0]
        and data_state == DATA_STATES[0]
    )


def iter_inplace_unique_scenarios() -> Iterator[InplaceUniqueScenario]:
    """Lazily yield the complete 2,304-scenario factor matrix."""

    case_no = 0
    for operation in inplace_unique_operations():
        for conflict_surface in CONFLICT_SURFACES:
            for conflict_pattern in CONFLICT_PATTERNS:
                for phase in PHASES:
                    for workers in WORKER_COUNTS:
                        for data_state in DATA_STATES:
                            case_no += 1
                            yield InplaceUniqueScenario(
                                case_no=case_no,
                                operation_id=operation.operation_id,
                                conflict_surface=conflict_surface,
                                conflict_pattern=conflict_pattern,
                                phase=phase,
                                workers=workers,
                                data_state=data_state,
                                ddl_sql=operation.ddl_sql,
                                smoke=_is_smoke_combination(
                                    conflict_surface,
                                    conflict_pattern,
                                    phase,
                                    workers,
                                    data_state,
                                ),
                            )
    if case_no != SCENARIO_COUNT:
        raise AssertionError(f"unexpected INPLACE unique scenario count: {case_no}")


def smoke_inplace_unique_scenarios() -> list[InplaceUniqueScenario]:
    """Return one representative full-matrix scenario for each operation."""

    scenarios: list[InplaceUniqueScenario] = []
    for operation_index, operation in enumerate(inplace_unique_operations(), start=1):
        case_no = (operation_index - 1) * SCENARIOS_PER_OPERATION + 1
        scenarios.append(
            InplaceUniqueScenario(
                case_no=case_no,
                operation_id=operation.operation_id,
                conflict_surface=CONFLICT_SURFACES[0],
                conflict_pattern=CONFLICT_PATTERNS[0],
                phase=PHASES[0],
                workers=WORKER_COUNTS[0],
                data_state=DATA_STATES[0],
                ddl_sql=operation.ddl_sql,
                smoke=True,
            )
        )
    return scenarios


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _gzip_bytes(payload: str) -> bytes:
    return gzip.compress(payload.encode("utf-8"), compresslevel=9, mtime=0)


def _write_bytes(path: Path, payload: bytes) -> None:
    path.write_bytes(payload)


def _coverage_lines(operations: tuple[InplaceUniqueOperation, ...]) -> list[str]:
    header = (
        "operation_id\tscenario_count\tconflict_surface_count\t"
        "conflict_pattern_count\tphase_count\tworker_count_count\t"
        "data_state_count\tsmoke_case_count\tddl_sha256"
    )
    rows = [
        "\t".join(
            (
                operation.operation_id,
                str(SCENARIOS_PER_OPERATION),
                str(len(CONFLICT_SURFACES)),
                str(len(CONFLICT_PATTERNS)),
                str(len(PHASES)),
                str(len(WORKER_COUNTS)),
                str(len(DATA_STATES)),
                "1",
                hashlib.sha256(operation.ddl_sql.encode("utf-8")).hexdigest(),
            )
        )
        for operation in operations
    ]
    return [header, *rows]


def _readme(
    operations: tuple[InplaceUniqueOperation, ...],
    smoke: list[InplaceUniqueScenario],
) -> str:
    operation_rows = "\n".join(
        f"| `{operation.operation_id}` | {SCENARIOS_PER_OPERATION} | `{scenario.case_id}` |"
        for operation, scenario in zip(operations, smoke)
    )
    return rf"""# INPLACE DDL unique-conflict batch

This independent `TUCUI` batch covers unique-index conflicts around twelve
MySQL DDL operations. The complete matrix is virtual and lazily generated; no
credentials, endpoints, or connection settings are embedded in the artifacts.

- **BATCH_ID:** `{INPLACE_UNIQUE_BATCH_ID}`
- **BATCH_KIND:** `{INPLACE_UNIQUE_BATCH_KIND}`
- **CASE_PREFIX:** `{INPLACE_UNIQUE_CASE_PREFIX}`
- **Database:** `{INPLACE_UNIQUE_DATABASE}`
- **Operations:** 12
- **Full scenario space:** {SCENARIO_COUNT:,}
- **Profiles:** `copy`, `inplace`, `instant`
- **Profile executions:** {SCENARIO_COUNT * len(INPLACE_UNIQUE_PROFILES):,}
- **Smoke cases:** 12, one per operation
- **Materialization:** `virtual_lazy_runner`

Every canonical operation DDL requests `ALGORITHM=INPLACE` and `LOCK=NONE`.
The legacy `MODIFY` and `CHANGE` forms are absent.

## Factor matrix

The scenario space is the exact Cartesian product of:

- 12 operations
- 4 conflict surfaces: `existing_unique`, `new_unique`, `composite_unique`, `nullable_unique`
- 4 conflict patterns: `seed_duplicate`, `concurrent_duplicate`, `semantic_collision`, `boundary_duplicate`
- 3 phases: `during_ddl`, `before_and_during_ddl`, `across_ddl_transaction`
- 2 worker counts: 4 and 16
- 2 data states: `normal` and `boundary`

The first case is `TUCUI-000001`; the last case is `TUCUI-002304`.

## Operation coverage

| Operation | Scenarios | Smoke case |
| --- | ---: | --- |
{operation_rows}

The smoke selector uses `existing_unique`, `seed_duplicate`, `during_ddl`,
4 workers, and the `normal` data state.

## Generation

```bash
cd mysql_case_factory
python3 tools/generate_inplace_unique_conflict.py \
  --output generated/inplace_unique_conflict_v1
```

Generation is deterministic. `manifest.json`, `smoke_cases.jsonl.gz`,
`coverage.tsv`, and `README.md` have stable bytes for the same source version.

## Execution

The runner uses multiple concurrent MySQL connections, so it is not a plain SQL
suite. Run it against an authorized MySQL server and keep the password in an
environment variable.

```bash
export TUCUI_MYSQL_PASSWORD='...'

PYTHONPATH=src python3 tools/run_inplace_unique_conflict.py \
  --profile copy \
  --smoke \
  --results generated/inplace_unique_conflict_v1/local_results.jsonl \
  --summary generated/inplace_unique_conflict_v1/local_summary.json \
  --external \
  --host <authorized-host> \
  --port 3306 \
  --user <authorized-user> \
  --password-env TUCUI_MYSQL_PASSWORD
```

Repeat with `--profile inplace` and `--profile instant`. For the complete
virtual matrix, replace `--smoke` with `--all`:

```bash
PYTHONPATH=src python3 tools/run_inplace_unique_conflict.py \
  --profile inplace \
  --all \
  --results generated/inplace_unique_conflict_v1/inplace_results.jsonl \
  --summary generated/inplace_unique_conflict_v1/inplace_summary.json \
  --external \
  --host <authorized-host> \
  --port 3306 \
  --user <authorized-user> \
  --password-env TUCUI_MYSQL_PASSWORD
```

Single-case debugging uses `--case-id`, for example `--case-id TUCUI-000961`.
The runner creates and removes a unique run database for every case.

Optional tuning:

- `--filler-rows` controls the seeded row count; the default is 128.
- `--hold-seconds` controls how long each worker transaction stays open; the
  default is 1 second.
- `--max-attempts` bounds duplicate attempts per worker; the default is 10000.

## Local evidence

- **MySQL:** 8.0.45
- **COPY smoke:** 12/12 `PASS`, 12 true overlaps, 12 duplicate conflicts
- **INSTANT smoke:** 5 `PASS`, 7 `EXPECTED_REJECT`
- **INPLACE smoke:** 9 `PASS`, 3 `FAIL_DDL`
  (`add_column`, `drop_column`, `drop_generated`)
"""


def inplace_unique_manifest(output: Path) -> dict[str, Any]:
    """Build the manifest after the other deterministic artifacts exist."""

    operations = inplace_unique_operations()
    smoke = smoke_inplace_unique_scenarios()
    hashes = {
        "coverage.tsv": _sha256(output / "coverage.tsv"),
        "README.md": _sha256(output / "README.md"),
        "smoke_cases.jsonl.gz": _sha256(output / "smoke_cases.jsonl.gz"),
    }
    return {
        "artifacts_sha256": hashes,
        "batch_id": INPLACE_UNIQUE_BATCH_ID,
        "batch_kind": INPLACE_UNIQUE_BATCH_KIND,
        "case_count": SCENARIO_COUNT,
        "case_id_prefix": INPLACE_UNIQUE_CASE_PREFIX,
        "database": INPLACE_UNIQUE_DATABASE,
        "factor_counts": {
            "conflict_patterns": {
                pattern: SCENARIO_COUNT // len(CONFLICT_PATTERNS)
                for pattern in CONFLICT_PATTERNS
            },
            "conflict_surfaces": {
                surface: SCENARIO_COUNT // len(CONFLICT_SURFACES)
                for surface in CONFLICT_SURFACES
            },
            "data_states": {
                state: SCENARIO_COUNT // len(DATA_STATES) for state in DATA_STATES
            },
            "operations": {operation.operation_id: SCENARIOS_PER_OPERATION for operation in operations},
            "phases": {phase: SCENARIO_COUNT // len(PHASES) for phase in PHASES},
            "worker_counts": {
                str(workers): SCENARIO_COUNT // len(WORKER_COUNTS)
                for workers in WORKER_COUNTS
            },
        },
        "forbidden_ddl_types": list(FORBIDDEN_DDL_TYPES),
        "forbidden_types_absent": True,
        "materialization": "virtual_lazy_runner",
        "operation_count": len(operations),
        "operation_ids": [operation.operation_id for operation in operations],
        "profile_counts": {
            profile: SCENARIO_COUNT for profile in INPLACE_UNIQUE_PROFILES
        },
        "profile_execution_count": SCENARIO_COUNT * len(INPLACE_UNIQUE_PROFILES),
        "profiles": list(INPLACE_UNIQUE_PROFILES),
        "scenario_count": SCENARIO_COUNT,
        "smoke_case_count": len(smoke),
        "smoke_case_ids": [scenario.case_id for scenario in smoke],
    }


def write_inplace_unique_artifacts(output: Path) -> dict[str, Any]:
    """Write the four deterministic virtual-batch artifacts."""

    operations = inplace_unique_operations()
    output.mkdir(parents=True, exist_ok=True)

    smoke = smoke_inplace_unique_scenarios()
    smoke_payload = "".join(
        json.dumps(scenario.to_json(), ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        + "\n"
        for scenario in smoke
    )
    _write_bytes(output / "smoke_cases.jsonl.gz", _gzip_bytes(smoke_payload))
    _write_bytes(
        output / "coverage.tsv",
        ("\n".join(_coverage_lines(operations)) + "\n").encode("utf-8"),
    )
    _write_bytes(output / "README.md", _readme(operations, smoke).encode("utf-8"))
    manifest = inplace_unique_manifest(output)
    _write_bytes(
        output / "manifest.json",
        (
            json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
        ).encode("utf-8"),
    )
    return manifest
