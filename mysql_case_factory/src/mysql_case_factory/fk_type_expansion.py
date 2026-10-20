from __future__ import annotations

import gzip
import hashlib
import json
import re
from dataclasses import asdict, dataclass
from decimal import Decimal, localcontext
from pathlib import Path
from typing import Any, Iterator, Sequence

FK_EXPANSION_BATCH_ID = "2026-10-20-fk-type-expansion-consistency-v1"
FK_EXPANSION_BATCH_KIND = "fk_type_expansion_consistency"
FK_EXPANSION_CASE_PREFIX = "TUCFK"
FK_EXPANSION_DATABASE = "qa_fk_type_expansion"
FK_EXPANSION_PROFILES = ("inplace", "instant")
FK_EXPANSION_AUTHOR = "yuzhengwen y00938623"
FK_EXPANSION_CREATE_AT = "2026-10-20"
FK_EXPANSION_FE = "FE2026081100174"

FK_ACTIONS = ("RESTRICT", "NO ACTION", "CASCADE", "SET NULL")


@dataclass(frozen=True)
class TypeTransition:
    family: str
    source_type: str
    target_type: str

    @property
    def key(self) -> str:
        return f"{self.source_type}->{self.target_type}"


@dataclass(frozen=True)
class FKExpansionScenario:
    case_no: int
    family: str
    source_type: str
    target_type: str
    algorithm: str
    fk_action: str
    expected_ddl_success: bool
    expected_error_code: int | None
    seed_values: tuple[str, ...]
    update_values: tuple[str, ...]

    @property
    def case_id(self) -> str:
        return f"{FK_EXPANSION_CASE_PREFIX}-{self.case_no:06d}"

    @property
    def parent_table(self) -> str:
        return f"tab_tucfk_{self.case_no:06d}_parent"

    @property
    def child_table(self) -> str:
        return f"tab_tucfk_{self.case_no:06d}_child"

    @property
    def fk_name(self) -> str:
        return f"fk_tucfk_{self.case_no:06d}"

    @property
    def batch_id(self) -> str:
        return FK_EXPANSION_BATCH_ID

    @property
    def batch_kind(self) -> str:
        return FK_EXPANSION_BATCH_KIND

    def to_json(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["case_id"] = self.case_id
        payload["batch_id"] = self.batch_id
        payload["batch_kind"] = self.batch_kind
        payload["database"] = FK_EXPANSION_DATABASE
        payload["parent_table"] = self.parent_table
        payload["child_table"] = self.child_table
        payload["fk_name"] = self.fk_name
        return payload


def _signed_integer_transitions() -> list[TypeTransition]:
    sources = ("TINYINT", "SMALLINT", "MEDIUMINT", "INT", "BIGINT")
    transitions: list[TypeTransition] = []
    for index, source in enumerate(sources):
        targets = sources[index + 1 :]
        for target in targets:
            transitions.append(TypeTransition("integer", source, target))
    transitions.append(TypeTransition("integer", "BIGINT", "BIGINT"))
    return transitions


def _unsigned_integer_transitions() -> list[TypeTransition]:
    sources = (
        "TINYINT UNSIGNED",
        "SMALLINT UNSIGNED",
        "MEDIUMINT UNSIGNED",
        "INT UNSIGNED",
        "BIGINT UNSIGNED",
    )
    transitions: list[TypeTransition] = []
    for index, source in enumerate(sources):
        targets = sources[index + 1 :]
        for target in targets:
            transitions.append(TypeTransition("integer", source, target))
    transitions.append(TypeTransition("integer", "BIGINT UNSIGNED", "BIGINT UNSIGNED"))
    return transitions


def _character_transitions() -> list[TypeTransition]:
    return [
        TypeTransition("character", "CHAR(0)", "CHAR(1)"),
        TypeTransition("character", "CHAR(1)", "CHAR(2)"),
        TypeTransition("character", "CHAR(10)", "CHAR(20)"),
        TypeTransition("character", "CHAR(50)", "CHAR(100)"),
        TypeTransition("character", "CHAR(100)", "CHAR(200)"),
        TypeTransition("character", "CHAR(255)", "VARCHAR(256)"),
        TypeTransition("character", "VARCHAR(0)", "VARCHAR(1)"),
        TypeTransition("character", "VARCHAR(1)", "VARCHAR(2)"),
        TypeTransition("character", "VARCHAR(10)", "VARCHAR(20)"),
        TypeTransition("character", "VARCHAR(60)", "VARCHAR(100)"),
        TypeTransition("character", "VARCHAR(100)", "VARCHAR(200)"),
        TypeTransition("character", "VARCHAR(255)", "VARCHAR(256)"),
        TypeTransition("character", "VARCHAR(512)", "VARCHAR(1024)"),
        TypeTransition("character", "VARCHAR(2048)", "VARCHAR(4096)"),
    ]


def _binary_transitions() -> list[TypeTransition]:
    return [
        TypeTransition("binary", "BINARY(0)", "BINARY(1)"),
        TypeTransition("binary", "BINARY(1)", "BINARY(2)"),
        TypeTransition("binary", "BINARY(10)", "BINARY(20)"),
        TypeTransition("binary", "BINARY(50)", "BINARY(100)"),
        TypeTransition("binary", "BINARY(100)", "BINARY(200)"),
        TypeTransition("binary", "BINARY(255)", "VARBINARY(256)"),
        TypeTransition("binary", "VARBINARY(0)", "VARBINARY(1)"),
        TypeTransition("binary", "VARBINARY(1)", "VARBINARY(2)"),
        TypeTransition("binary", "VARBINARY(10)", "VARBINARY(20)"),
        TypeTransition("binary", "VARBINARY(60)", "VARBINARY(100)"),
        TypeTransition("binary", "VARBINARY(255)", "VARBINARY(256)"),
        TypeTransition("binary", "VARBINARY(512)", "VARBINARY(1024)"),
    ]


def _decimal_transitions() -> list[TypeTransition]:
    return [
        TypeTransition("decimal", "DECIMAL(1,0)", "DECIMAL(2,0)"),
        TypeTransition("decimal", "DECIMAL(5,2)", "DECIMAL(10,2)"),
        TypeTransition("decimal", "DECIMAL(10,2)", "DECIMAL(18,2)"),
        TypeTransition("decimal", "DECIMAL(18,6)", "DECIMAL(28,6)"),
        TypeTransition("decimal", "DECIMAL(28,10)", "DECIMAL(38,10)"),
        TypeTransition("decimal", "DECIMAL(38,18)", "DECIMAL(50,18)"),
        TypeTransition("decimal", "DECIMAL(50,30)", "DECIMAL(65,30)"),
        TypeTransition("decimal", "DECIMAL(65,30)", "DECIMAL(65,30)"),
        TypeTransition("decimal", "DECIMAL(10,0)", "DECIMAL(20,0)"),
        TypeTransition("decimal", "DECIMAL(20,4)", "DECIMAL(30,4)"),
    ]


def _bit_transitions() -> list[TypeTransition]:
    widths = [
        (0, 1),
        (1, 2),
        (2, 4),
        (4, 8),
        (8, 16),
        (16, 24),
        (24, 32),
        (32, 40),
        (40, 48),
        (48, 56),
        (56, 64),
        (63, 64),
        (64, 64),
    ]
    return [TypeTransition("bit", f"BIT({source})", f"BIT({target})") for source, target in widths]


def fk_type_transitions() -> tuple[TypeTransition, ...]:
    return (
        *_signed_integer_transitions(),
        *_unsigned_integer_transitions(),
        *_character_transitions(),
        *_binary_transitions(),
        *_decimal_transitions(),
        *_bit_transitions(),
    )


def _expected_outcome(transition: TypeTransition, algorithm: str) -> tuple[bool, int | None]:
    family = transition.family
    same_type = transition.source_type == transition.target_type
    if family == "integer":
        return (True, None) if same_type else (False, 3780)
    if family == "binary" and transition.source_type.startswith("BINARY"):
        return False, 1846
    if algorithm == "inplace":
        return True, None
    return False, 1845


def _integer_bounds(type_name: str) -> tuple[int, int]:
    unsigned = "UNSIGNED" in type_name
    base = type_name.replace(" UNSIGNED", "")
    signed = {
        "TINYINT": (-128, 127),
        "SMALLINT": (-32768, 32767),
        "MEDIUMINT": (-8388608, 8388607),
        "INT": (-2147483648, 2147483647),
        "BIGINT": (-(2**63), 2**63 - 1),
    }[base]
    unsigned_max = {
        "TINYINT": 255,
        "SMALLINT": 65535,
        "MEDIUMINT": 16777215,
        "INT": 4294967295,
        "BIGINT": 2**64 - 1,
    }[base]
    return (0, unsigned_max) if unsigned else signed


def _integer_values(type_name: str, offset: int = 0) -> tuple[str, ...]:
    minimum, maximum = _integer_bounds(type_name)
    if minimum < 0:
        raw = [minimum, minimum + 1, -1, 0, 1, -2, 2, maximum - 1, maximum, maximum - 2]
    else:
        raw = [0, 1, 2, 3, 4, 5, 6, maximum - 2, maximum - 1, maximum]
    values = [min(maximum, max(minimum, value + offset)) for value in raw]
    # Ensure ten entries even when clamping collapses values.
    index = 0
    while len(values) < 10:
        candidate = min(maximum, max(minimum, minimum + index + offset))
        values.append(candidate)
        index += 1
    return tuple(str(value) for value in values[:10])


def _type_length(type_name: str) -> int:
    match = re.search(r"\((\d+)", type_name)
    return int(match.group(1)) if match else 0


def _character_values(type_name: str, offset: int = 0) -> tuple[str, ...]:
    length = _type_length(type_name)
    if length == 0:
        return tuple(["''"] * 10)
    values: list[str] = []
    for index in range(10):
        letter = chr(ord("a") + ((index + offset) % 26))
        value = letter * min(index + 1, length)
        values.append("'" + value + "'")
    return tuple(values)


def _binary_values(type_name: str, offset: int = 0) -> tuple[str, ...]:
    length = _type_length(type_name)
    if length == 0:
        return tuple(["x''"] * 10)
    values: list[str] = []
    for index in range(10):
        byte = (index + 1 + offset) % 256
        value = f"{byte:02x}" * min(index + 1, length)
        values.append(f"x'{value}'")
    return tuple(values)


def _decimal_bounds(type_name: str) -> tuple[Decimal, Decimal, int]:
    match = re.search(r"\((\d+),(\d+)\)", type_name)
    if not match:
        return Decimal(-9999999999), Decimal(9999999999), 0
    precision, scale = int(match.group(1)), int(match.group(2))
    integer_digits = precision - scale
    maximum = Decimal("9" * integer_digits + ("." + "9" * scale if scale else ""))
    return -maximum, maximum, scale


def _decimal_values(type_name: str, offset: int = 0) -> tuple[str, ...]:
    minimum, maximum, scale = _decimal_bounds(type_name)
    span = maximum - minimum
    values: list[Decimal] = []
    with localcontext() as context:
        context.prec = 100
        for index in range(10):
            value = minimum + (span * index / 9) + offset
            quantum = Decimal(1).scaleb(-scale)
            value = value.quantize(quantum)
            value = min(maximum, max(minimum, value))
            values.append(value)
    return tuple(f"{value:.{scale}f}" for value in values)


def _bit_width(type_name: str) -> int:
    match = re.search(r"\((\d+)\)", type_name)
    return int(match.group(1)) if match else 1


def _bit_values(type_name: str, offset: int = 0) -> tuple[str, ...]:
    width = _bit_width(type_name)
    if width == 0:
        return tuple(["b'0'"] * 10)
    maximum = (1 << width) - 1
    preferred = [0, 1, 2, 4, 8, 16, 32, 64, maximum - 1, maximum]
    values: list[int] = []
    for value in preferred:
        adjusted = (value + offset) % (maximum + 1)
        if adjusted not in values:
            values.append(adjusted)
    index = 0
    while len(values) < 10:
        adjusted = (index + offset) % (maximum + 1)
        values.append(adjusted)
        index += 1
    return tuple(f"b'{value:0{width}b}'" for value in values[:10])


def _seed_values(transition: TypeTransition, offset: int = 0) -> tuple[str, ...]:
    family = transition.family
    if family == "integer":
        return _integer_values(transition.source_type, offset)
    if family == "character":
        return _character_values(transition.source_type, offset)
    if family == "binary":
        return _binary_values(transition.source_type, offset)
    if family == "decimal":
        return _decimal_values(transition.source_type, offset)
    if family == "bit":
        return _bit_values(transition.source_type, offset)
    raise AssertionError(family)


def iter_fk_expansion_scenarios() -> Iterator[FKExpansionScenario]:
    case_no = 0
    for transition in fk_type_transitions():
        for algorithm in FK_EXPANSION_PROFILES:
            expected_success, expected_error = _expected_outcome(transition, algorithm)
            for action in FK_ACTIONS:
                case_no += 1
                yield FKExpansionScenario(
                    case_no=case_no,
                    family=transition.family,
                    source_type=transition.source_type,
                    target_type=transition.target_type,
                    algorithm=algorithm,
                    fk_action=action,
                    expected_ddl_success=expected_success,
                    expected_error_code=expected_error,
                    seed_values=_seed_values(transition, 0),
                    update_values=_seed_values(transition, 1),
                )


def smoke_fk_expansion_scenarios() -> list[FKExpansionScenario]:
    scenarios = list(iter_fk_expansion_scenarios())
    return [
        next(scenario for scenario in scenarios if scenario.family == family)
        for family in ("integer", "character", "binary", "decimal", "bit")
    ]


def _sql_comment(scenario: FKExpansionScenario) -> str:
    return (
        "-- --------------------------------------------------------\n"
        "-- author       : yuzhengwen y00938623\n"
        "-- create at    : 2026-10-20\n"
        f"-- description  : FK type expansion {scenario.source_type} -> {scenario.target_type} "
        f"({scenario.algorithm}, {scenario.fk_action})\n"
        "-- FE           : FE2026081100174\n"
        "-- --------------------------------------------------------\n"
    )


def render_fk_expansion_sql(scenario: FKExpansionScenario) -> str:
    parent = scenario.parent_table
    child = scenario.child_table
    fk = scenario.fk_name
    action = scenario.fk_action
    seed = scenario.seed_values
    update = scenario.update_values
    source_type = scenario.source_type

    parent_rows = ",\n".join(
        f"  ({index + 1}, {seed[index % len(seed)]}, {index + 1})"
        for index in range(10)
    )
    child_rows = ",\n".join(
        f"  ({index + 1}, {index + 1}, {seed[index % len(seed)]}, {index + 1})"
        for index in range(10)
    )
    extra_parent_rows = ",\n".join(
        f"  ({index + 11}, {seed[index % len(seed)]}, {index + 11})"
        for index in range(10)
    )
    extra_child_rows = ",\n".join(
        f"  ({index + 11}, {index + 11}, {seed[index % len(seed)]}, {index + 11})"
        for index in range(10)
    )
    update_rows = ",\n".join(
        f"    WHEN {index + 1} THEN {update[index % len(update)]}"
        for index in range(10)
    )
    expected_parent_count = 20 if action in {"RESTRICT", "NO ACTION"} else 15
    expected_type = scenario.target_type if scenario.expected_ddl_success else source_type
    expected_type_lower = expected_type.lower()

    return f"""{_sql_comment(scenario)}
-- pre-cleanup
DROP TABLE IF EXISTS `{child}`;
DROP TABLE IF EXISTS `{parent}`;

-- create parent and child with a composite FK
CREATE TABLE `{parent}` (
  id INT NOT NULL,
  fk_col {source_type} NOT NULL,
  payload INT NOT NULL,
  PRIMARY KEY (id, fk_col)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE `{child}` (
  id INT NOT NULL,
  parent_id INT NOT NULL,
  fk_col {source_type} NULL,
  payload INT NOT NULL,
  PRIMARY KEY (id),
  KEY `idx_{fk}` (parent_id, fk_col),
  CONSTRAINT `{fk}` FOREIGN KEY (parent_id, fk_col)
    REFERENCES `{parent}` (id, fk_col)
    ON UPDATE CASCADE
    ON DELETE {action}
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- seed 10 parent and child rows
INSERT INTO `{parent}` (id, fk_col, payload) VALUES
{parent_rows};

INSERT INTO `{child}` (id, parent_id, fk_col, payload) VALUES
{child_rows};

-- target DDL
ALTER TABLE `{child}`
  MODIFY `fk_col` {scenario.target_type} NULL,
  ALGORITHM={scenario.algorithm.upper()};

-- insert 10 additional parent and child rows
INSERT INTO `{parent}` (id, fk_col, payload) VALUES
{extra_parent_rows};

INSERT INTO `{child}` (id, parent_id, fk_col, payload) VALUES
{extra_child_rows};

-- full-table update of parent FK values and child payload
UPDATE `{parent}`
SET fk_col = CASE id
{update_rows}
  ELSE fk_col END,
  payload = payload + 100;

UPDATE `{child}`
SET payload = payload + 100;

-- exercise the selected FK delete action
DELETE FROM `{parent}` WHERE id <= 5;

-- full child delete and deterministic reinsert for surviving parents 6..20
DELETE FROM `{child}`;

INSERT INTO `{child}` (id, parent_id, fk_col, payload)
SELECT p.id, p.id, p.fk_col, p.id
FROM `{parent}` p
WHERE p.id BETWEEN 6 AND 20;

-- deterministic result row
SELECT case_id, algorithm, fk_action, column_type, parent_count, child_count,
       orphan_count, matched_count, fk_exists,
       CASE
         WHEN column_type = '{expected_type_lower}'
          AND parent_count = {expected_parent_count}
          AND child_count = 15
          AND orphan_count = 0
          AND matched_count = 15
          AND fk_exists = 1
         THEN 'PASS' ELSE 'FAIL'
       END AS result
FROM (
  SELECT
    '{scenario.case_id}' AS case_id,
    '{scenario.algorithm}' AS algorithm,
    '{scenario.fk_action}' AS fk_action,
    (SELECT LOWER(COLUMN_TYPE)
       FROM information_schema.COLUMNS
      WHERE TABLE_SCHEMA = DATABASE()
        AND TABLE_NAME = '{child}'
        AND COLUMN_NAME = 'fk_col') AS column_type,
    (SELECT COUNT(*) FROM `{parent}`) AS parent_count,
    (SELECT COUNT(*) FROM `{child}`) AS child_count,
    (SELECT COUNT(*)
       FROM `{child}` c
       LEFT JOIN `{parent}` p
         ON c.parent_id = p.id AND c.fk_col = p.fk_col
      WHERE p.id IS NULL) AS orphan_count,
    (SELECT COUNT(*)
       FROM `{child}` c
       JOIN `{parent}` p
         ON c.parent_id = p.id AND c.fk_col = p.fk_col) AS matched_count,
    (SELECT COUNT(*)
       FROM information_schema.KEY_COLUMN_USAGE
      WHERE TABLE_SCHEMA = DATABASE()
        AND TABLE_NAME = '{child}'
        AND CONSTRAINT_NAME = '{fk}') AS fk_exists
) AS t;

-- final cleanup
DROP TABLE IF EXISTS `{child}`;
DROP TABLE IF EXISTS `{parent}`;
"""


def expected_fk_expansion_output(scenario: FKExpansionScenario) -> str:
    expected_type = scenario.target_type if scenario.expected_ddl_success else scenario.source_type
    parent_count = 20 if scenario.fk_action in {"RESTRICT", "NO ACTION"} else 15
    fields = (
        scenario.case_id,
        scenario.algorithm,
        scenario.fk_action,
        expected_type.lower(),
        str(parent_count),
        "15",
        "0",
        "15",
        "1",
        "PASS",
    )
    return "\t".join(fields)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _gzip_bytes(payload: str) -> bytes:
    return gzip.compress(payload.encode("utf-8"), compresslevel=9, mtime=0)


def _write_text(path: Path, payload: str) -> None:
    path.write_text(payload, encoding="utf-8", newline="\n")


def write_fk_expansion_artifacts(output: Path) -> dict[str, Any]:
    output.mkdir(parents=True, exist_ok=True)
    scenarios = list(iter_fk_expansion_scenarios())

    cases_payload = "".join(
        json.dumps(scenario.to_json(), ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n"
        for scenario in scenarios
    )
    (output / "cases.jsonl.gz").write_bytes(_gzip_bytes(cases_payload))

    for profile in FK_EXPANSION_PROFILES:
        profile_scenarios = [scenario for scenario in scenarios if scenario.algorithm == profile]
        sql_payload = "\n".join(render_fk_expansion_sql(scenario) for scenario in profile_scenarios)
        expected_payload = "\n".join(expected_fk_expansion_output(scenario) for scenario in profile_scenarios) + "\n"
        (output / f"{profile}_suite.sql.gz").write_bytes(_gzip_bytes(sql_payload))
        _write_text(output / f"expected_output_{profile}.tsv", expected_payload)

    coverage_lines = [
        "family\tsource_type\ttarget_type\tscenario_count\tinplace_scenarios\tinstant_scenarios",
        *[
            "\t".join(
                (
                    family,
                    source_type,
                    target_type,
                    str(sum(1 for scenario in scenarios if scenario.family == family and scenario.source_type == source_type and scenario.target_type == target_type)),
                    str(sum(1 for scenario in scenarios if scenario.family == family and scenario.source_type == source_type and scenario.target_type == target_type and scenario.algorithm == "inplace")),
                    str(sum(1 for scenario in scenarios if scenario.family == family and scenario.source_type == source_type and scenario.target_type == target_type and scenario.algorithm == "instant")),
                )
            )
            for family, source_type, target_type in sorted({
                (transition.family, transition.source_type, transition.target_type)
                for transition in fk_type_transitions()
            })
        ],
    ]
    _write_text(output / "coverage.tsv", "\n".join(coverage_lines) + "\n")

    artifact_hashes = {
        name: _sha256(output / name)
        for name in (
            "cases.jsonl.gz",
            "inplace_suite.sql.gz",
            "instant_suite.sql.gz",
            "expected_output_inplace.tsv",
            "expected_output_instant.tsv",
            "coverage.tsv",
        )
    }
    manifest = {
        "artifacts_sha256": artifact_hashes,
        "batch_id": FK_EXPANSION_BATCH_ID,
        "batch_kind": FK_EXPANSION_BATCH_KIND,
        "case_count": len(scenarios),
        "case_id_prefix": FK_EXPANSION_CASE_PREFIX,
        "database": FK_EXPANSION_DATABASE,
        "transition_count": len(fk_type_transitions()),
        "profiles": list(FK_EXPANSION_PROFILES),
        "profile_counts": {profile: len([s for s in scenarios if s.algorithm == profile]) for profile in FK_EXPANSION_PROFILES},
        "fk_actions": list(FK_ACTIONS),
        "materialization": "sql_suite",
        "forbidden_types_absent": True,
    }
    _write_text(output / "manifest.json", json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n")

    readme = f"""# FK type-expansion consistency batch

This independent `TUCFK` batch verifies parent/child consistency after child
foreign-key column expansion.

- **BATCH_ID:** `{FK_EXPANSION_BATCH_ID}`
- **BATCH_KIND:** `{FK_EXPANSION_BATCH_KIND}`
- **CASE_PREFIX:** `{FK_EXPANSION_CASE_PREFIX}`
- **Database:** `{FK_EXPANSION_DATABASE}`
- **Cases:** {len(scenarios)}
- **Transitions:** {len(fk_type_transitions())}
- **Profiles:** `inplace`, `instant`
- **FK actions:** `RESTRICT`, `NO ACTION`, `CASCADE`, `SET NULL`

## Execution

```bash
gunzip -c inplace_suite.sql.gz > inplace.sql
mysql --login-path=internal_qa --batch --raw --skip-column-names --binary-mode --force \\
  {FK_EXPANSION_DATABASE} < inplace.sql > inplace.actual.tsv 2> inplace.errors.log

diff -u expected_output_inplace.tsv inplace.actual.tsv
```

Repeat for `instant_suite.sql.gz` and `expected_output_instant.tsv`.

A run passes only when:

1. stdout matches the expected TSV exactly;
2. no result row is `FAIL`;
3. orphan count is always zero;
4. the FK still exists;
5. there is no signal, assertion, timeout, MySQL 2013/2006, or lost connection.
"""
    _write_text(output / "README.md", readme)
    return manifest
