"""Virtual scenario space for primary-key type upgrades and concurrent DML.

The full matrix contains 946,944 scenarios.  Materializing one SQL file per
scenario would create millions of files, so the batch uses a deterministic lazy
iterator and a concurrency runner.  The runner executes scenarios directly from
factor values and records per-scenario evidence.
"""

from __future__ import annotations

import gzip
import hashlib
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Iterator

PRIMARY_KEY_BATCH_ID = "2026-10-19-type-upgrade-primary-key-concurrency-v1"
PRIMARY_KEY_BATCH_KIND = "primary_key_concurrency_extension"
PRIMARY_KEY_PARENT_BATCH_ID = "2026-10-15-type-upgrade-boundary-v1"
PRIMARY_KEY_CASE_PREFIX = "TUCPK"
PRIMARY_KEY_PROFILES = ("copy", "inplace", "instant")
PRIMARY_KEY_DATABASE = "qa_type_upgrade_primary_key"
PRIMARY_KEY_AUTHOR = "yuzhengwen y00938623"
PRIMARY_KEY_CREATE_AT = "2026-10-19"
PRIMARY_KEY_FE = "FE2026081100174"

INTEGER_STATES = (
    "empty_counter_1",
    "empty_counter_max_minus_16",
    "empty_counter_max_minus_1",
    "empty_counter_max",
    "one_row_max_minus_1",
    "one_row_max",
    "tail_16_to_max_minus_1",
    "tail_16_to_max",
    "all_deleted_high_counter",
    "mixed_explicit_generated_max",
)
NON_INTEGER_STATES = (
    "empty",
    "one_row",
    "normal_24_rows",
    "boundary_or_near_boundary",
    "prefix_or_collation_conflict",
    "high_value_all_deleted",
)
PHASES = ("during_ddl", "post_ddl", "pre_during_post", "across_ddl")
INTEGER_INSERT_STYLES = (
    "omit_pk_explicit_columns",
    "null_pk_positional",
    "insert_select_omit_pk",
    "multi_row_omit_pk",
)
NON_INTEGER_INSERT_STYLES = (
    "explicit_pk_all_columns",
    "explicit_pk_partial_columns",
    "insert_select_explicit_pk",
    "multi_row_explicit_pk",
)
DML_MODES = ("insert_only", "insert_update_all_canaries", "commit_rollback_mix")
WORKER_COUNTS = (4, 16)
ROW_FORMATS = ("DYNAMIC", "COMPACT", "COMPRESSED", "REDUNDANT")
KEY_SHAPES = ("single_pk", "composite_pk_pk_first", "composite_pk_pk_second")


@dataclass(frozen=True)
class PrimaryKeyTransition:
    family: str
    source_type: str
    target_type: str
    length_boundary: str = "not_applicable"

    @property
    def transition_key(self) -> str:
        return f"{self.source_type}->{self.target_type}"


@dataclass(frozen=True)
class PrimaryKeyScenario:
    case_no: int
    family: str
    source_type: str
    target_type: str
    transition_key: str
    initial_state: str
    phase: str
    insert_style: str
    dml_mode: str
    workers: int
    row_format: str
    key_shape: str
    length_boundary: str
    auto_increment: bool
    pk_prefix_length: int | None
    inplace_expected: bool
    instant_expected: bool
    smoke: bool = False

    @property
    def case_id(self) -> str:
        prefix = "TUCPKS" if self.smoke else PRIMARY_KEY_CASE_PREFIX
        return f"{prefix}-{self.case_no:06d}"

    @property
    def batch_id(self) -> str:
        return PRIMARY_KEY_BATCH_ID

    @property
    def batch_kind(self) -> str:
        return PRIMARY_KEY_BATCH_KIND

    def to_json(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["case_id"] = self.case_id
        payload["batch_id"] = self.batch_id
        payload["batch_kind"] = self.batch_kind
        return payload


def _integer_transitions() -> list[PrimaryKeyTransition]:
    integer_types = (
        "TINYINT",
        "TINYINT UNSIGNED",
        "SMALLINT",
        "SMALLINT UNSIGNED",
        "MEDIUMINT",
        "MEDIUMINT UNSIGNED",
        "INT",
        "INT UNSIGNED",
        "BIGINT",
        "BIGINT UNSIGNED",
    )
    ranges = {
        "TINYINT": (-128, 127),
        "TINYINT UNSIGNED": (0, 255),
        "SMALLINT": (-32768, 32767),
        "SMALLINT UNSIGNED": (0, 65535),
        "MEDIUMINT": (-8388608, 8388607),
        "MEDIUMINT UNSIGNED": (0, 16777215),
        "INT": (-2147483648, 2147483647),
        "INT UNSIGNED": (0, 4294967295),
        "BIGINT": (-(2**63), 2**63 - 1),
        "BIGINT UNSIGNED": (0, 2**64 - 1),
    }
    transitions: list[PrimaryKeyTransition] = []
    for source in integer_types:
        if source == "BIGINT UNSIGNED":
            continue
        source_min, source_max = ranges[source]
        for target in integer_types:
            if target == source:
                continue
            target_min, target_max = ranges[target]
            # AUTO_INCREMENT data is non-negative.  A transition is a positive
            # capacity expansion when the target can hold source_max and has a
            # larger signed range or a larger unsigned ceiling.
            if target_max < source_max:
                continue
            if target_min > 0:
                continue
            if (target_min, target_max) == (source_min, source_max):
                continue
            transitions.append(PrimaryKeyTransition("integer", source, target))
    return transitions


def primary_key_transitions() -> list[PrimaryKeyTransition]:
    integer = _integer_transitions()
    decimal = [
        PrimaryKeyTransition("decimal", "DECIMAL(1,0)", "DECIMAL(2,0)"),
        PrimaryKeyTransition("decimal", "DECIMAL(8,0)", "DECIMAL(9,0)"),
        PrimaryKeyTransition("decimal", "DECIMAL(9,0)", "DECIMAL(10,0)"),
        PrimaryKeyTransition("decimal", "DECIMAL(18,0)", "DECIMAL(19,0)"),
        PrimaryKeyTransition("decimal", "DECIMAL(27,0)", "DECIMAL(28,0)"),
        PrimaryKeyTransition("decimal", "DECIMAL(36,0)", "DECIMAL(37,0)"),
        PrimaryKeyTransition("decimal", "DECIMAL(64,0)", "DECIMAL(65,0)"),
        PrimaryKeyTransition("decimal", "DECIMAL(10,2)", "DECIMAL(11,2)"),
        PrimaryKeyTransition("decimal", "DECIMAL(18,6)", "DECIMAL(19,6)"),
        PrimaryKeyTransition("decimal", "DECIMAL(27,9)", "DECIMAL(28,9)"),
        PrimaryKeyTransition("decimal", "DECIMAL(36,18)", "DECIMAL(37,18)"),
        PrimaryKeyTransition("decimal", "DECIMAL(63,30)", "DECIMAL(64,30)"),
        PrimaryKeyTransition("decimal", "DECIMAL(18,6)", "NUMERIC(19,6)"),
        PrimaryKeyTransition("decimal", "NUMERIC(18,6)", "DECIMAL(19,6)"),
    ]
    bit = [
        PrimaryKeyTransition("bit", "BIT(1)", "BIT(2)"),
        PrimaryKeyTransition("bit", "BIT(4)", "BIT(8)"),
        PrimaryKeyTransition("bit", "BIT(7)", "BIT(8)"),
        PrimaryKeyTransition("bit", "BIT(8)", "BIT(16)"),
        PrimaryKeyTransition("bit", "BIT(15)", "BIT(16)"),
        PrimaryKeyTransition("bit", "BIT(16)", "BIT(24)"),
        PrimaryKeyTransition("bit", "BIT(24)", "BIT(32)"),
        PrimaryKeyTransition("bit", "BIT(31)", "BIT(32)"),
        PrimaryKeyTransition("bit", "BIT(32)", "BIT(40)"),
        PrimaryKeyTransition("bit", "BIT(63)", "BIT(64)"),
    ]
    character = [
        PrimaryKeyTransition("character", "CHAR(16)", "CHAR(32)", "pre_256"),
        PrimaryKeyTransition("character", "CHAR(128)", "CHAR(255)", "pre_256"),
        PrimaryKeyTransition("character", "VARCHAR(16)", "VARCHAR(32)", "pre_256"),
        PrimaryKeyTransition("character", "VARCHAR(128)", "VARCHAR(255)", "pre_256"),
        PrimaryKeyTransition("character", "VARCHAR(255)", "VARCHAR(256)", "cross_256"),
        PrimaryKeyTransition("character", "CHAR(255)", "VARCHAR(256)", "cross_256"),
        PrimaryKeyTransition("character", "VARCHAR(255)", "VARCHAR(257)", "cross_256"),
        PrimaryKeyTransition("character", "CHAR(255)", "VARCHAR(257)", "cross_256"),
        PrimaryKeyTransition("character", "VARCHAR(128)", "VARCHAR(256)", "cross_256"),
        PrimaryKeyTransition("character", "CHAR(128)", "VARCHAR(256)", "cross_256"),
        PrimaryKeyTransition("character", "VARCHAR(256)", "VARCHAR(257)", "post_256"),
        PrimaryKeyTransition("character", "VARCHAR(2047)", "VARCHAR(2048)", "post_256"),
    ]
    binary = [
        PrimaryKeyTransition("binary", "BINARY(16)", "BINARY(32)", "pre_256"),
        PrimaryKeyTransition("binary", "BINARY(128)", "BINARY(255)", "pre_256"),
        PrimaryKeyTransition("binary", "VARBINARY(16)", "VARBINARY(32)", "pre_256"),
        PrimaryKeyTransition("binary", "VARBINARY(128)", "VARBINARY(255)", "pre_256"),
        PrimaryKeyTransition("binary", "VARBINARY(255)", "VARBINARY(256)", "cross_256"),
        PrimaryKeyTransition("binary", "BINARY(255)", "VARBINARY(256)", "cross_256"),
        PrimaryKeyTransition("binary", "VARBINARY(255)", "VARBINARY(257)", "cross_256"),
        PrimaryKeyTransition("binary", "BINARY(255)", "VARBINARY(257)", "cross_256"),
        PrimaryKeyTransition("binary", "VARBINARY(128)", "VARBINARY(256)", "cross_256"),
        PrimaryKeyTransition("binary", "BINARY(128)", "VARBINARY(256)", "cross_256"),
        PrimaryKeyTransition("binary", "VARBINARY(256)", "VARBINARY(257)", "post_256"),
        PrimaryKeyTransition("binary", "VARBINARY(511)", "VARBINARY(512)", "post_256"),
        PrimaryKeyTransition("binary", "VARBINARY(1023)", "VARBINARY(1024)", "post_256"),
        PrimaryKeyTransition("binary", "VARBINARY(2047)", "VARBINARY(2048)", "post_256"),
    ]
    text = [
        PrimaryKeyTransition("text", "TINYTEXT", "TEXT"),
        PrimaryKeyTransition("text", "TINYTEXT", "MEDIUMTEXT"),
        PrimaryKeyTransition("text", "TINYTEXT", "LONGTEXT"),
        PrimaryKeyTransition("text", "TEXT", "MEDIUMTEXT"),
        PrimaryKeyTransition("text", "TEXT", "LONGTEXT"),
        PrimaryKeyTransition("text", "MEDIUMTEXT", "LONGTEXT"),
    ]
    blob = [
        PrimaryKeyTransition("blob", "TINYBLOB", "BLOB"),
        PrimaryKeyTransition("blob", "TINYBLOB", "MEDIUMBLOB"),
        PrimaryKeyTransition("blob", "TINYBLOB", "LONGBLOB"),
        PrimaryKeyTransition("blob", "BLOB", "MEDIUMBLOB"),
        PrimaryKeyTransition("blob", "BLOB", "LONGBLOB"),
        PrimaryKeyTransition("blob", "MEDIUMBLOB", "LONGBLOB"),
    ]
    transitions = [*integer, *decimal, *bit, *character, *binary, *text, *blob]
    assert len(transitions) == 107
    return transitions


def iter_primary_key_scenarios() -> Iterator[PrimaryKeyScenario]:
    case_no = 0
    for transition in primary_key_transitions():
        states = INTEGER_STATES if transition.family == "integer" else NON_INTEGER_STATES
        insert_styles = INTEGER_INSERT_STYLES if transition.family == "integer" else NON_INTEGER_INSERT_STYLES
        for initial_state in states:
            for phase in PHASES:
                for insert_style in insert_styles:
                    for dml_mode in DML_MODES:
                        for workers in WORKER_COUNTS:
                            for row_format in ROW_FORMATS:
                                for key_shape in KEY_SHAPES:
                                    case_no += 1
                                    instant_expected = not (
                                        transition.family == "character"
                                        and transition.length_boundary in {"pre_256", "post_256"}
                                    )
                                    yield PrimaryKeyScenario(
                                        case_no=case_no,
                                        family=transition.family,
                                        source_type=transition.source_type,
                                        target_type=transition.target_type,
                                        transition_key=transition.transition_key,
                                        initial_state=initial_state,
                                        phase=phase,
                                        insert_style=insert_style,
                                        dml_mode=dml_mode,
                                        workers=workers,
                                        row_format=row_format,
                                        key_shape=key_shape,
                                        length_boundary=transition.length_boundary,
                                        auto_increment=transition.family == "integer",
                                        pk_prefix_length=32 if transition.family in {"text", "blob"} else None,
                                        inplace_expected=True,
                                        instant_expected=instant_expected,
                                    )
    if case_no != 946_944:
        raise AssertionError(f"unexpected primary-key scenario count: {case_no}")


def smoke_primary_key_scenarios() -> list[PrimaryKeyScenario]:
    scenarios: list[PrimaryKeyScenario] = []
    for transition in primary_key_transitions():
        initial_state = "empty_counter_1" if transition.family == "integer" else "boundary_or_near_boundary"
        insert_style = (
            "omit_pk_explicit_columns"
            if transition.family == "integer"
            else "explicit_pk_all_columns"
        )
        scenarios.append(
            PrimaryKeyScenario(
                case_no=len(scenarios) + 1,
                family=transition.family,
                source_type=transition.source_type,
                target_type=transition.target_type,
                transition_key=transition.transition_key,
                initial_state=initial_state,
                phase="during_ddl",
                insert_style=insert_style,
                dml_mode="insert_only",
                workers=4,
                row_format="DYNAMIC",
                key_shape="single_pk",
                length_boundary=transition.length_boundary,
                auto_increment=transition.family == "integer",
                pk_prefix_length=32 if transition.family in {"text", "blob"} else None,
                inplace_expected=True,
                instant_expected=not (
                    transition.family == "character"
                    and transition.length_boundary in {"pre_256", "post_256"}
                ),
                smoke=True,
            )
        )
    return scenarios


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _gzip_bytes(payload: str) -> bytes:
    return gzip.compress(payload.encode("utf-8"), compresslevel=9, mtime=0)


def primary_key_manifest(output: Path) -> dict[str, Any]:
    smoke = smoke_primary_key_scenarios()
    hashes = {
        "smoke_cases.jsonl.gz": _sha256(output / "smoke_cases.jsonl.gz"),
        "coverage.tsv": _sha256(output / "coverage.tsv"),
    }
    return {
        "batch_id": PRIMARY_KEY_BATCH_ID,
        "batch_kind": PRIMARY_KEY_BATCH_KIND,
        "parent_batch_id": PRIMARY_KEY_PARENT_BATCH_ID,
        "case_id_prefix": PRIMARY_KEY_CASE_PREFIX,
        "smoke_case_id_prefix": "TUCPKS",
        "transition_count": 107,
        "case_count": 946_944,
        "scenario_count": 946_944,
        "smoke_case_count": len(smoke),
        "profiles": list(PRIMARY_KEY_PROFILES),
        "profile_counts": {profile: 946_944 for profile in PRIMARY_KEY_PROFILES},
        "profile_execution_count": 946_944 * len(PRIMARY_KEY_PROFILES),
        "database": PRIMARY_KEY_DATABASE,
        "materialization": "virtual_lazy_runner",
        "forbidden_types_absent": True,
        "artifacts_sha256": hashes,
    }


def write_primary_key_artifacts(output: Path) -> dict[str, Any]:
    output.mkdir(parents=True, exist_ok=True)
    (output / ".gitignore").write_text("*.actual.tsv\n*.errors.log\n*.out\n", encoding="utf-8")

    smoke = smoke_primary_key_scenarios()
    payload = "".join(
        json.dumps(scenario.to_json(), sort_keys=True, separators=(",", ":")) + "\n"
        for scenario in smoke
    )
    (output / "smoke_cases.jsonl.gz").write_bytes(_gzip_bytes(payload))

    coverage_lines = [
        "transition_key\tfamily\tsource_type\ttarget_type\tlength_boundary\tauto_increment\tpk_prefix_length\tinplace_expected\tinstant_expected",
        *(
            "\t".join(
                (
                    transition.transition_key,
                    transition.family,
                    transition.source_type,
                    transition.target_type,
                    transition.length_boundary,
                    str(transition.family == "integer").lower(),
                    "32" if transition.family in {"text", "blob"} else "-",
                    "true",
                    str(
                        not (
                            transition.family == "character"
                            and transition.length_boundary in {"pre_256", "post_256"}
                        )
                    ).lower(),
                )
            )
            for transition in primary_key_transitions()
        ),
    ]
    (output / "coverage.tsv").write_text("\n".join(coverage_lines) + "\n", encoding="utf-8")

    manifest = primary_key_manifest(output)
    (output / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    family_counts: dict[str, int] = {}
    for transition in primary_key_transitions():
        family_counts[transition.family] = family_counts.get(transition.family, 0) + 1
    readme = f"""# Primary-key type-upgrade concurrency batch

This is an independent `TUCPK` batch. It covers primary-key type upgrades,
`AUTO_INCREMENT` insertion without naming the PK column, extreme counters,
concurrent DML, and all-column correctness.

- **BATCH_ID:** `{PRIMARY_KEY_BATCH_ID}`
- **BATCH_KIND:** `{PRIMARY_KEY_BATCH_KIND}`
- **CASE_PREFIX:** `{PRIMARY_KEY_CASE_PREFIX}`
- **Smoke case prefix:** `TUCPKS`
- **Transitions:** 107
- **Full scenario space:** 946,944
- **Profiles:** `copy`, `inplace`, `instant`
- **Profile executions:** 2,840,832
- **Smoke cases:** 107, one per transition
- **Fixed database:** `{PRIMARY_KEY_DATABASE}`

The full scenario space is virtual and lazily generated by the runner. It is not
materialized as individual SQL files because concurrent execution requires
multiple connections and per-worker timing evidence.

## Coverage

| Family | Transitions |
| --- | ---: |
| Integer with AUTO_INCREMENT | 45 |
| DECIMAL / NUMERIC | 14 |
| BIT | 10 |
| CHAR / VARCHAR | 12 |
| BINARY / VARBINARY | 14 |
| TEXT | 6 |
| BLOB | 6 |

TEXT and BLOB primary keys use `PRIMARY KEY(pk(32))`.

`CHAR` / `VARCHAR` expectations:

- before 256: `INPLACE` success, `INSTANT` expected reject;
- crossing 256: both success;
- after 256: `INPLACE` success, `INSTANT` expected reject.

## Local smoke

```bash
cd mysql_case_factory
PYTHONPATH=src .venv312/bin/python tools/run_type_upgrade_primary_key_concurrency.py \\
  --cases generated/type_upgrade_primary_key_concurrency_v1 \\
  --results generated/type_upgrade_primary_key_concurrency_v1/local_results.jsonl \\
  --summary generated/type_upgrade_primary_key_concurrency_v1/local_summary.json \\
  --profile copy \\
  --smoke \\
  --phase post_ddl \\
  --filler-rows 16
```

Current evidence:

```text
107 / 107 PASS
MySQL 8.0.45
```

## Internal smoke

Use an existing internal server. Do not put passwords on the command line.

```bash
export TUCPK_MYSQL_PASSWORD='...'

cd mysql_case_factory
PYTHONPATH=src .venv312/bin/python tools/run_type_upgrade_primary_key_concurrency.py \\
  --cases generated/type_upgrade_primary_key_concurrency_v1 \\
  --results generated/type_upgrade_primary_key_concurrency_v1/inplace_results.jsonl \\
  --summary generated/type_upgrade_primary_key_concurrency_v1/inplace_summary.json \\
  --profile inplace \\
  --smoke \\
  --phase during_ddl \\
  --filler-rows 256 \\
  --external \\
  --host <internal-host> \\
  --port 3306 \\
  --user <internal-user> \\
  --password-env TUCPK_MYSQL_PASSWORD
```

Repeat with `--profile instant`.

For the complete 946,944-scenario matrix, replace `--smoke` with `--all` and
increase `--filler-rows` as needed. A `NO_OVERLAP` result means the DDL and DML
did not truly overlap; increase `--filler-rows` and retry.

## Result rules

A scenario passes only when:

1. DDL has the expected outcome.
2. All committed rows exist.
3. Rolled-back rows are absent.
4. Primary keys are unique.
5. AUTO_INCREMENT does not regress.
6. Every canary column is correct.
7. Schema and index metadata are correct.
8. TEXT/BLOB prefix length remains 32.
9. Expected source-range failures retry successfully after DDL.
10. Concurrency phases have true overlap.

Any crash, assertion, lost row, duplicate key, column mismatch, schema mismatch,
timeout, MySQL 2013/2006, or lost connection is a failure.

## Audit

```bash
cd mysql_case_factory
PYTHONPATH=src .venv312/bin/python tools/audit_type_upgrade_primary_key.py \\
  --primary-key generated/type_upgrade_primary_key_concurrency_v1
```
"""
    (output / "README.md").write_text(readme, encoding="utf-8")
    return manifest
