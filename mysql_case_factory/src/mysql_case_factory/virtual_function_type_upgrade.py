from __future__ import annotations

import gzip
import hashlib
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Iterator

from mysql_case_factory.type_upgrade_primary_key import primary_key_transitions

VIRTUAL_FUNCTION_BATCH_ID = "2026-10-20-virtual-function-type-upgrade-v1"
VIRTUAL_FUNCTION_BATCH_KIND = "virtual_function_type_upgrade"
VIRTUAL_FUNCTION_CASE_PREFIX = "TUCVF"
VIRTUAL_FUNCTION_DATABASE = "qa_virtual_function_type_upgrade"
VIRTUAL_FUNCTION_PROFILES = ("copy", "inplace", "instant")

DEPENDENCY_MODES = (
    "none",
    "virtual_generated",
    "stored_generated",
    "functional_index",
)
DATA_STATES = ("normal", "boundary")
NULLABILITY_STATES = ("nullable", "not_null")
SCENARIO_COUNT = (
    len(primary_key_transitions())
    * len(DEPENDENCY_MODES)
    * len(VIRTUAL_FUNCTION_PROFILES)
    * len(DATA_STATES)
    * len(NULLABILITY_STATES)
)


@dataclass(frozen=True)
class VirtualFunctionScenario:
    case_no: int
    family: str
    source_type: str
    target_type: str
    transition_key: str
    dependency_mode: str
    algorithm: str
    data_state: str
    nullability: str
    generated_type: str
    expression: str
    smoke: bool = False

    @property
    def case_id(self) -> str:
        prefix = "TUCVFS" if self.smoke else VIRTUAL_FUNCTION_CASE_PREFIX
        return f"{prefix}-{self.case_no:06d}"

    @property
    def control_table(self) -> str:
        return f"tab_tucvf_{self.case_no:06d}_control"

    @property
    def candidate_table(self) -> str:
        return f"tab_tucvf_{self.case_no:06d}_candidate"

    @property
    def reference_table(self) -> str:
        return f"tab_tucvf_{self.case_no:06d}_reference"

    @property
    def index_name(self) -> str:
        return "idx_tucvf_fn"

    @property
    def batch_id(self) -> str:
        return VIRTUAL_FUNCTION_BATCH_ID

    @property
    def batch_kind(self) -> str:
        return VIRTUAL_FUNCTION_BATCH_KIND

    def to_json(self) -> dict[str, Any]:
        payload = asdict(self)
        payload.update(
            {
                "batch_id": self.batch_id,
                "batch_kind": self.batch_kind,
                "case_id": self.case_id,
                "database": VIRTUAL_FUNCTION_DATABASE,
                "control_table": self.control_table,
                "candidate_table": self.candidate_table,
                "reference_table": self.reference_table,
                "index_name": self.index_name,
            }
        )
        return payload


def generated_type_for_transition(transition: Any) -> str:
    if transition.family in {"integer", "bit"}:
        return "DECIMAL(65,0)"
    if transition.family == "decimal":
        scale = int(transition.source_type.split(",")[-1].rstrip(")"))
        return f"DECIMAL(65,{scale})"
    if transition.family in {"character", "binary", "text", "blob"}:
        return "VARCHAR(64)" if transition.family in {"character", "text"} else "VARCHAR(16)"
    raise AssertionError(transition.family)


def expression_for_transition(transition: Any) -> str:
    if transition.family in {"integer", "bit"}:
        return "CAST(base AS DECIMAL(65,0))"
    if transition.family == "decimal":
        scale = int(transition.source_type.split(",")[-1].rstrip(")"))
        return f"CAST(base AS DECIMAL(65,{scale}))"
    if transition.family in {"character", "text"}:
        return "CAST(LEFT(UPPER(base), 64) AS CHAR(64))"
    if transition.family in {"binary", "blob"}:
        return "LEFT(HEX(base), 16)"
    raise AssertionError(transition.family)


def build_create_table_sql(
    scenario: VirtualFunctionScenario,
    table_name: str,
    base_type: str,
) -> str:
    nullability = "NULL" if scenario.nullability == "nullable" else "NOT NULL"
    lines = [
        f"CREATE TABLE `{table_name}` (",
        "  id BIGINT NOT NULL,",
        f"  base {base_type} {nullability},",
    ]
    if scenario.dependency_mode in {"virtual_generated", "stored_generated"}:
        stored = "STORED" if scenario.dependency_mode == "stored_generated" else "VIRTUAL"
        lines.append(
            f"  gen {scenario.generated_type} AS ({scenario.expression}) {stored},"
        )
    if scenario.dependency_mode == "functional_index":
        lines.append(
            f"  KEY `{scenario.index_name}` (({scenario.expression})),"
        )
    lines.append("  PRIMARY KEY (id)")
    lines.append(") ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci")
    return "\n".join(lines) + ";"


def build_ddl_sql(
    scenario: VirtualFunctionScenario,
    table_name: str,
) -> str:
    nullability = "NULL" if scenario.nullability == "nullable" else "NOT NULL"
    return (
        f"ALTER TABLE `{table_name}` "
        f"MODIFY base {scenario.target_type} {nullability}, "
        f"ALGORITHM={scenario.algorithm.upper()}"
    )


def iter_virtual_function_scenarios() -> Iterator[VirtualFunctionScenario]:
    case_no = 0
    for transition in primary_key_transitions():
        generated_type = generated_type_for_transition(transition)
        expression = expression_for_transition(transition)
        for dependency_mode in DEPENDENCY_MODES:
            for algorithm in VIRTUAL_FUNCTION_PROFILES:
                for data_state in DATA_STATES:
                    for nullability in NULLABILITY_STATES:
                        case_no += 1
                        yield VirtualFunctionScenario(
                            case_no=case_no,
                            family=transition.family,
                            source_type=transition.source_type,
                            target_type=transition.target_type,
                            transition_key=transition.transition_key,
                            dependency_mode=dependency_mode,
                            algorithm=algorithm,
                            data_state=data_state,
                            nullability=nullability,
                            generated_type=generated_type,
                            expression=expression,
                        )
    if case_no != SCENARIO_COUNT:
        raise AssertionError(f"unexpected virtual-function scenario count: {case_no}")


def smoke_virtual_function_scenarios() -> list[VirtualFunctionScenario]:
    representatives: dict[str, VirtualFunctionScenario] = {}
    for scenario in iter_virtual_function_scenarios():
        if scenario.family not in representatives:
            representatives[scenario.family] = scenario
    smoke: list[VirtualFunctionScenario] = []
    for family in ("integer", "decimal", "bit", "character", "binary", "text", "blob"):
        representative = representatives[family]
        for dependency_mode in DEPENDENCY_MODES:
            for algorithm in VIRTUAL_FUNCTION_PROFILES:
                smoke.append(
                    VirtualFunctionScenario(
                        case_no=len(smoke) + 1,
                        family=representative.family,
                        source_type=representative.source_type,
                        target_type=representative.target_type,
                        transition_key=representative.transition_key,
                        dependency_mode=dependency_mode,
                        algorithm=algorithm,
                        data_state=representative.data_state,
                        nullability=representative.nullability,
                        generated_type=representative.generated_type,
                        expression=representative.expression,
                        smoke=True,
                    )
                )
    return smoke


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _gzip_bytes(payload: str) -> bytes:
    return gzip.compress(payload.encode("utf-8"), compresslevel=9, mtime=0)


def write_virtual_function_artifacts(output: Path) -> dict[str, Any]:
    output.mkdir(parents=True, exist_ok=True)
    scenarios = list(iter_virtual_function_scenarios())
    smoke = smoke_virtual_function_scenarios()

    cases_payload = "".join(
        json.dumps(scenario.to_json(), ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n"
        for scenario in scenarios
    )
    smoke_payload = "".join(
        json.dumps(scenario.to_json(), ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n"
        for scenario in smoke
    )
    (output / "cases.jsonl.gz").write_bytes(_gzip_bytes(cases_payload))
    (output / "smoke_cases.jsonl.gz").write_bytes(_gzip_bytes(smoke_payload))

    coverage_lines = [
        "family\tsource_type\ttarget_type\tdependency_mode\talgorithm\tdata_state\tnullability\tscenario_count",
        *[
            "\t".join(
                (
                    scenario.family,
                    scenario.source_type,
                    scenario.target_type,
                    scenario.dependency_mode,
                    scenario.algorithm,
                    scenario.data_state,
                    scenario.nullability,
                    "1",
                )
            )
            for scenario in scenarios
        ],
    ]
    (output / "coverage.tsv").write_text("\n".join(coverage_lines) + "\n", encoding="utf-8")

    artifact_hashes = {
        name: _sha256(output / name)
        for name in ("cases.jsonl.gz", "smoke_cases.jsonl.gz", "coverage.tsv")
    }
    manifest = {
        "artifacts_sha256": artifact_hashes,
        "batch_id": VIRTUAL_FUNCTION_BATCH_ID,
        "batch_kind": VIRTUAL_FUNCTION_BATCH_KIND,
        "case_count": len(scenarios),
        "case_id_prefix": VIRTUAL_FUNCTION_CASE_PREFIX,
        "database": VIRTUAL_FUNCTION_DATABASE,
        "dependency_mode_count": len(DEPENDENCY_MODES),
        "materialization": "virtual_runner",
        "profile_counts": {
            profile: sum(1 for scenario in scenarios if scenario.algorithm == profile)
            for profile in VIRTUAL_FUNCTION_PROFILES
        },
        "profiles": list(VIRTUAL_FUNCTION_PROFILES),
        "smoke_case_count": len(smoke),
        "transition_count": len(primary_key_transitions()),
    }
    (output / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    readme = f"""# Virtual/function type-upgrade batch

This batch verifies that base-column type expansion does not corrupt data or
change algorithm behavior when the base column is referenced by a virtual
generated column, a stored generated column, or a functional index.

- **BATCH_ID:** `{VIRTUAL_FUNCTION_BATCH_ID}`
- **BATCH_KIND:** `{VIRTUAL_FUNCTION_BATCH_KIND}`
- **CASE_PREFIX:** `{VIRTUAL_FUNCTION_CASE_PREFIX}`
- **Database:** `{VIRTUAL_FUNCTION_DATABASE}`
- **Cases:** {len(scenarios)}
- **Transitions:** {len(primary_key_transitions())}
- **Dependency modes:** {len(DEPENDENCY_MODES)}
- **Profiles:** {', '.join(VIRTUAL_FUNCTION_PROFILES)}
- **Smoke cases:** {len(smoke)}

## Execution

Run one profile:

```bash
PYTHONPATH=src python3 tools/run_virtual_function_type_upgrade.py \
  --profile copy \
  --all \
  --results generated/virtual_function_type_upgrade_v1/copy_results.jsonl \
  --summary generated/virtual_function_type_upgrade_v1/copy_summary.json \
  --external \
  --host <authorized-host> \
  --port 3306 \
  --user <authorized-user> \
  --password-env VIRTUAL_FUNCTION_MYSQL_PASSWORD
```

Repeat with `--profile inplace` and `--profile instant`.

Run the 84-case smoke matrix:

```bash
PYTHONPATH=src python3 tools/run_virtual_function_type_upgrade.py \
  --profile copy \
  --smoke \
  --results generated/virtual_function_type_upgrade_v1/smoke_results.jsonl \
  --summary generated/virtual_function_type_upgrade_v1/smoke_summary.json \
  --external \
  --host <authorized-host> \
  --port 3306 \
  --user <authorized-user> \
  --password-env VIRTUAL_FUNCTION_MYSQL_PASSWORD
```

Repeat the smoke matrix with `--profile inplace` and `--profile instant`.
"""
    (output / "README.md").write_text(readme, encoding="utf-8")
    return manifest
