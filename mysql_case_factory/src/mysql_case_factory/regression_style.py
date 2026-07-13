"""Stable regression-script naming and deterministic-output audits.

This module is intentionally independent from plan expansion and database
execution.  It turns an already ordered set of executable obligation IDs into
an immutable, append-only filename mapping and provides conservative checks
for the SQL text and for two captured process runs.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from datetime import date
from typing import Any, Mapping, Optional, Sequence


REGRESSION_MAPPING_SCHEMA_VERSION = 1
_BATCH_PREFIX_PATTERN = re.compile(r"^[A-Za-z][A-Za-z0-9]*$")
_OBLIGATION_ID_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")
_OBJECT_PREFIX_PATTERN = re.compile(r"^[a-z][a-z0-9]*_[0-9]{3,}_$")
_SHA256_PATTERN = re.compile(r"^[0-9a-f]{64}$")
_HEADER_SEPARATOR = "-- --------------------------------------------------------"
_HEADER_COPYRIGHT = (
    "-- \u7248\u6743\u6240\u6709(C)  2021-2030 "
    "\u534e\u4e3a\u6280\u672f\u6709\u9650\u516c\u53f8"
)
_HEADER_FIELD_PATTERNS = (
    ("author", re.compile(r"^-- author       : (.*)$")),
    ("create_at", re.compile(r"^-- create at    : (.*)$")),
    ("version", re.compile(r"^-- version      : (.*)$")),
    ("description", re.compile(r"^-- description  : (.*)$")),
    ("fe", re.compile(r"^-- FE           : (.*)$")),
)
_CATALOG_RELATION_PATTERN = re.compile(
    r"\b(?:from|join)\s+"
    r"(?P<relation>(?:(?:information_schema|performance_schema|mysql|sys)\s*\.\s*)"
    r"(?:[A-Za-z_][A-Za-z0-9_$]*|`(?:[^`]|``)+`))",
    re.IGNORECASE,
)
_UNQUALIFIED_CATALOG_PATTERN = re.compile(
    r"\b(?:from|join)\s+(?P<relation>"
    r"tables|columns|statistics|routines|triggers|events|user|db|global_variables"
    r")\b(?!\s*\.)",
    re.IGNORECASE,
)
_VOLATILE_OUTPUT_PATTERN = re.compile(
    r"\b(?:now|sysdate|current_timestamp|rand|uuid|uuid_short|connection_id)\s*\(",
    re.IGNORECASE,
)
_CREATE_TABLE_PATTERN = re.compile(
    r"^\s*CREATE\s+(?:(?:GLOBAL|LOCAL)\s+)?"
    r"(?:(?:TEMP|TEMPORARY|UNLOGGED)\s+)?TABLE\s+"
    r"(?:IF\s+NOT\s+EXISTS\s+)?(?P<name>[^\s(]+)",
    re.IGNORECASE | re.DOTALL,
)
_DROP_TABLE_PATTERN = re.compile(
    r"^\s*DROP\s+TABLE\s+IF\s+EXISTS\s+(?P<names>.+?)"
    r"(?:\s+(?:CASCADE|RESTRICT))?\s*$",
    re.IGNORECASE | re.DOTALL,
)


class RegressionStyleError(ValueError):
    """Raised when a regression style contract is invalid."""


def _require_exact_keys(
    raw: Mapping[str, Any], required: set[str], location: str
) -> dict[str, Any]:
    if not isinstance(raw, Mapping):
        raise RegressionStyleError(f"{location} must be a mapping")
    if any(not isinstance(key, str) for key in raw):
        raise RegressionStyleError(f"{location} mapping keys must be strings")
    document = dict(raw)
    missing = sorted(required - set(document))
    unexpected = sorted(set(document) - required)
    if missing or unexpected:
        details: list[str] = []
        if missing:
            details.append("missing " + ", ".join(missing))
        if unexpected:
            details.append("unexpected " + ", ".join(unexpected))
        raise RegressionStyleError(f"{location} has invalid fields: " + "; ".join(details))
    return document


def _require_plain_string(value: Any, location: str, *, allow_empty: bool = False) -> str:
    if not isinstance(value, str):
        raise RegressionStyleError(f"{location} must be a string")
    if "\n" in value or "\r" in value or "\x00" in value:
        raise RegressionStyleError(f"{location} must be a single line without NUL")
    if value != value.strip():
        raise RegressionStyleError(f"{location} must not have surrounding whitespace")
    if not allow_empty and not value:
        raise RegressionStyleError(f"{location} must be non-empty")
    return value


def _validate_batch_prefix(value: Any) -> str:
    prefix = _require_plain_string(value, "batch_prefix")
    if _BATCH_PREFIX_PATTERN.fullmatch(prefix) is None:
        raise RegressionStyleError(
            "batch_prefix must start with an ASCII letter and contain only ASCII letters or digits"
        )
    return prefix


def _validate_obligation_id(value: Any, location: str) -> str:
    obligation_id = _require_plain_string(value, location)
    if _OBLIGATION_ID_PATTERN.fullmatch(obligation_id) is None:
        raise RegressionStyleError(
            f"{location} must match [A-Za-z0-9][A-Za-z0-9._-]*"
        )
    return obligation_id


@dataclass(frozen=True)
class RegressionCaseStyle:
    """One stable obligation-to-script assignment."""

    obligation_id: str
    case_ordinal: int
    sql_filename: str
    object_prefix: str

    def __post_init__(self) -> None:
        _validate_obligation_id(self.obligation_id, "regression_case.obligation_id")
        if type(self.case_ordinal) is not int or self.case_ordinal < 1:
            raise RegressionStyleError("regression_case.case_ordinal must be a positive integer")
        _require_plain_string(self.sql_filename, "regression_case.sql_filename")
        object_prefix = _require_plain_string(
            self.object_prefix, "regression_case.object_prefix"
        )
        if object_prefix != object_prefix.lower() or _OBJECT_PREFIX_PATTERN.fullmatch(
            object_prefix
        ) is None:
            raise RegressionStyleError(
                "regression_case.object_prefix must be a lowercase numbered SQL identifier prefix"
            )

    @classmethod
    def from_dict(
        cls, raw: Mapping[str, Any], location: str = "regression_case"
    ) -> "RegressionCaseStyle":
        document = _require_exact_keys(
            raw,
            {"obligation_id", "case_ordinal", "sql_filename", "object_prefix"},
            location,
        )
        return cls(
            obligation_id=document["obligation_id"],
            case_ordinal=document["case_ordinal"],
            sql_filename=document["sql_filename"],
            object_prefix=document["object_prefix"],
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "obligation_id": self.obligation_id,
            "case_ordinal": self.case_ordinal,
            "sql_filename": self.sql_filename,
            "object_prefix": self.object_prefix,
        }


@dataclass(frozen=True)
class RegressionBatchMapping:
    """Versioned, contiguous and append-only regression filename mapping."""

    schema_version: int
    batch_prefix: str
    number_width: int
    cases: tuple[RegressionCaseStyle, ...]

    def __post_init__(self) -> None:
        if type(self.schema_version) is not int or (
            self.schema_version != REGRESSION_MAPPING_SCHEMA_VERSION
        ):
            raise RegressionStyleError(
                f"schema_version must be {REGRESSION_MAPPING_SCHEMA_VERSION}"
            )
        prefix = _validate_batch_prefix(self.batch_prefix)
        if type(self.number_width) is not int or self.number_width < 3:
            raise RegressionStyleError("number_width must be an integer of at least 3")
        if type(self.cases) is not tuple or not self.cases:
            raise RegressionStyleError("cases must be a non-empty tuple")

        obligation_ids: set[str] = set()
        filenames: set[str] = set()
        object_prefixes: set[str] = set()
        for expected_ordinal, case in enumerate(self.cases, start=1):
            if not isinstance(case, RegressionCaseStyle):
                raise RegressionStyleError("cases must contain only RegressionCaseStyle values")
            if case.case_ordinal != expected_ordinal:
                raise RegressionStyleError("case ordinals must be contiguous and start at 1")
            number = f"{expected_ordinal:0{self.number_width}d}"
            if len(number) != self.number_width:
                raise RegressionStyleError(
                    "number_width is too small for the largest case ordinal"
                )
            expected_filename = f"{prefix}{number}.sql"
            expected_object_prefix = f"{prefix.lower()}_{number}_"
            if len(expected_object_prefix) > 64:
                raise RegressionStyleError(
                    "numbered object prefix exceeds MySQL's 64-character identifier limit"
                )
            if case.sql_filename != expected_filename:
                raise RegressionStyleError(
                    f"case {expected_ordinal} sql_filename must be {expected_filename}"
                )
            if case.object_prefix != expected_object_prefix:
                raise RegressionStyleError(
                    f"case {expected_ordinal} object_prefix must be {expected_object_prefix}"
                )
            if case.obligation_id in obligation_ids:
                raise RegressionStyleError(
                    f"duplicate obligation_id {case.obligation_id} in regression mapping"
                )
            if case.sql_filename in filenames or case.object_prefix in object_prefixes:
                raise RegressionStyleError("regression mapping contains a naming collision")
            obligation_ids.add(case.obligation_id)
            filenames.add(case.sql_filename)
            object_prefixes.add(case.object_prefix)

    @classmethod
    def from_dict(cls, raw: Mapping[str, Any]) -> "RegressionBatchMapping":
        document = _require_exact_keys(
            raw,
            {"schema_version", "batch_prefix", "number_width", "cases"},
            "regression_mapping",
        )
        raw_cases = document["cases"]
        if isinstance(raw_cases, (str, bytes)) or not isinstance(raw_cases, Sequence):
            raise RegressionStyleError("regression_mapping.cases must be a sequence")
        cases = tuple(
            RegressionCaseStyle.from_dict(item, f"regression_mapping.cases[{index}]")
            for index, item in enumerate(raw_cases)
        )
        return cls(
            schema_version=document["schema_version"],
            batch_prefix=document["batch_prefix"],
            number_width=document["number_width"],
            cases=cases,
        )

    @property
    def sha256(self) -> str:
        payload = json.dumps(
            self.to_dict(), ensure_ascii=False, sort_keys=True, separators=(",", ":")
        ).encode("utf-8")
        return hashlib.sha256(payload).hexdigest()

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "batch_prefix": self.batch_prefix,
            "number_width": self.number_width,
            "cases": [case.to_dict() for case in self.cases],
        }


def build_regression_batch_mapping(
    batch_prefix: str,
    executable_obligation_ids: Sequence[str],
    *,
    prior_mapping: Optional[RegressionBatchMapping] = None,
    minimum_width: int = 3,
) -> RegressionBatchMapping:
    """Map plan-order obligations to stable filenames, appending when requested.

    A prior mapping must be an exact prefix of ``executable_obligation_ids``.
    Existing assignments are copied byte-for-byte.  If an append would require
    widening the prior numbering, the operation is refused because widening
    would rename existing scripts; callers can reserve a larger width when the
    batch is first created.
    """

    prefix = _validate_batch_prefix(batch_prefix)
    if isinstance(executable_obligation_ids, (str, bytes)) or not isinstance(
        executable_obligation_ids, Sequence
    ):
        raise RegressionStyleError("executable_obligation_ids must be an ordered sequence")
    if type(minimum_width) is not int or minimum_width < 3:
        raise RegressionStyleError("minimum_width must be an integer of at least 3")
    obligation_ids = tuple(
        _validate_obligation_id(value, f"executable_obligation_ids[{index}]")
        for index, value in enumerate(executable_obligation_ids)
    )
    if not obligation_ids:
        raise RegressionStyleError("executable_obligation_ids must not be empty")
    if len(obligation_ids) != len(set(obligation_ids)):
        raise RegressionStyleError("executable_obligation_ids must not contain duplicates")

    automatic_width = max(3, minimum_width, len(str(len(obligation_ids))))
    retained: tuple[RegressionCaseStyle, ...] = ()
    if prior_mapping is not None:
        if not isinstance(prior_mapping, RegressionBatchMapping):
            raise RegressionStyleError("prior_mapping must be a RegressionBatchMapping")
        if prior_mapping.batch_prefix != prefix:
            raise RegressionStyleError("prior_mapping batch_prefix conflicts with batch_prefix")
        prior_ids = tuple(case.obligation_id for case in prior_mapping.cases)
        if len(obligation_ids) < len(prior_ids):
            raise RegressionStyleError("append-only mapping cannot remove prior obligations")
        if obligation_ids[: len(prior_ids)] != prior_ids:
            raise RegressionStyleError(
                "prior obligations must remain an exact ordered prefix; "
                "reordering or replacement is forbidden"
            )
        if minimum_width > prior_mapping.number_width:
            raise RegressionStyleError(
                "minimum_width cannot widen an existing mapping without renaming prior scripts"
            )
        if len(str(len(obligation_ids))) > prior_mapping.number_width:
            raise RegressionStyleError(
                "append exceeds prior number_width; reserve a larger width when creating the batch"
            )
        width = prior_mapping.number_width
        retained = prior_mapping.cases
    else:
        width = automatic_width

    cases = list(retained)
    for ordinal, obligation_id in enumerate(
        obligation_ids[len(retained) :], start=len(retained) + 1
    ):
        number = f"{ordinal:0{width}d}"
        cases.append(
            RegressionCaseStyle(
                obligation_id=obligation_id,
                case_ordinal=ordinal,
                sql_filename=f"{prefix}{number}.sql",
                object_prefix=f"{prefix.lower()}_{number}_",
            )
        )
    return RegressionBatchMapping(
        schema_version=REGRESSION_MAPPING_SCHEMA_VERSION,
        batch_prefix=prefix,
        number_width=width,
        cases=tuple(cases),
    )


@dataclass(frozen=True)
class HuaweiSqlHeader:
    """Explicit values for the stable Huawei SQL header."""

    author: str
    create_at: str
    version: str
    description: str
    fe: str

    def __post_init__(self) -> None:
        _require_plain_string(self.author, "header.author")
        create_at = _require_plain_string(self.create_at, "header.create_at")
        try:
            parsed_date = date.fromisoformat(create_at)
        except ValueError as exc:
            raise RegressionStyleError("header.create_at must be a real YYYY-MM-DD date") from exc
        if parsed_date.isoformat() != create_at:
            raise RegressionStyleError("header.create_at must use exact YYYY-MM-DD form")
        _require_plain_string(self.version, "header.version")
        _require_plain_string(self.description, "header.description")
        _require_plain_string(self.fe, "header.fe", allow_empty=True)

    @classmethod
    def from_dict(cls, raw: Mapping[str, Any]) -> "HuaweiSqlHeader":
        document = _require_exact_keys(
            raw, {"author", "create_at", "version", "description", "fe"}, "header"
        )
        return cls(
            author=document["author"],
            create_at=document["create_at"],
            version=document["version"],
            description=document["description"],
            fe=document["fe"],
        )

    def to_dict(self) -> dict[str, str]:
        return {
            "author": self.author,
            "create_at": self.create_at,
            "version": self.version,
            "description": self.description,
            "fe": self.fe,
        }


def render_huawei_sql_header(header: HuaweiSqlHeader) -> str:
    """Render the canonical header with LF endings and one final newline."""

    if not isinstance(header, HuaweiSqlHeader):
        raise RegressionStyleError("header must be a HuaweiSqlHeader")
    lines = (
        _HEADER_SEPARATOR,
        _HEADER_COPYRIGHT,
        "--",
        "-- --",
        f"-- author       : {header.author}",
        f"-- create at    : {header.create_at}",
        f"-- version      : {header.version}",
        f"-- description  : {header.description}",
        f"-- FE           : {header.fe}",
        "-- ++",
        _HEADER_SEPARATOR,
    )
    return "\n".join(lines) + "\n"


def validate_huawei_sql_header(
    sql_text: str, *, expected: Optional[HuaweiSqlHeader] = None
) -> HuaweiSqlHeader:
    """Validate the header at byte zero and the canonical SQL EOF shape."""

    if not isinstance(sql_text, str) or not sql_text:
        raise RegressionStyleError("sql_text must be a non-empty string")
    if "\r" in sql_text:
        raise RegressionStyleError("sql_text must use LF line endings")
    if not sql_text.endswith("\n"):
        raise RegressionStyleError("SQL must end with exactly one newline")
    if sql_text.endswith("\n\n"):
        raise RegressionStyleError("SQL must not have a trailing blank line")
    final_line = sql_text[:-1].rsplit("\n", 1)[-1]
    if not final_line.strip():
        raise RegressionStyleError("SQL final line must be non-empty")

    lines = sql_text.splitlines()
    if len(lines) < 11:
        raise RegressionStyleError("SQL does not contain the complete Huawei header")
    fixed_expectations = {
        0: _HEADER_SEPARATOR,
        1: _HEADER_COPYRIGHT,
        2: "--",
        3: "-- --",
        9: "-- ++",
        10: _HEADER_SEPARATOR,
    }
    for index, required_line in fixed_expectations.items():
        if lines[index] != required_line:
            raise RegressionStyleError(f"header line {index + 1} is not canonical")

    values: dict[str, str] = {}
    for offset, (field_name, pattern) in enumerate(_HEADER_FIELD_PATTERNS, start=4):
        match = pattern.fullmatch(lines[offset])
        if match is None:
            raise RegressionStyleError(f"header field {field_name} is missing or malformed")
        values[field_name] = match.group(1)
    parsed = HuaweiSqlHeader(**values)
    if expected is not None:
        if not isinstance(expected, HuaweiSqlHeader):
            raise RegressionStyleError("expected must be a HuaweiSqlHeader")
        if parsed != expected:
            raise RegressionStyleError("rendered header does not match the expected values")
    return parsed


@dataclass(frozen=True)
class CatalogQueryAudit:
    statement_ordinal: int
    relations: tuple[str, ...]
    projection: str
    order_by: str
    issues: tuple[str, ...]

    @property
    def passed(self) -> bool:
        return not self.issues

    def to_dict(self) -> dict[str, Any]:
        return {
            "statement_ordinal": self.statement_ordinal,
            "relations": list(self.relations),
            "projection": self.projection,
            "order_by": self.order_by,
            "issues": list(self.issues),
            "passed": self.passed,
        }


@dataclass(frozen=True)
class CatalogObservabilityReport:
    queries: tuple[CatalogQueryAudit, ...]
    parser_issues: tuple[str, ...] = ()

    @property
    def passed(self) -> bool:
        return not self.parser_issues and all(query.passed for query in self.queries)

    def to_dict(self) -> dict[str, Any]:
        return {
            "catalog_query_count": len(self.queries),
            "queries": [query.to_dict() for query in self.queries],
            "parser_issues": list(self.parser_issues),
            "passed": self.passed,
            "policy": (
                "Catalog observation is allowed when relations are schema-qualified, "
                "the output projection has no top-level wildcard or known volatile "
                "function, and a top-level explicit ORDER BY is present. Semantic "
                "stability and a unique ordering key still require review."
            ),
        }


def _mask_non_code(sql: str) -> tuple[str, tuple[str, ...]]:
    """Replace comments and literal bodies while preserving code positions."""

    output = list(sql)
    issues: list[str] = []
    index = 0
    length = len(sql)
    while index < length:
        if sql.startswith("--", index):
            end = sql.find("\n", index + 2)
            if end < 0:
                end = length
            for position in range(index, end):
                output[position] = " "
            index = end
            continue
        if sql.startswith("/*", index):
            start = index
            depth = 1
            index += 2
            while index < length and depth:
                if sql.startswith("/*", index):
                    depth += 1
                    index += 2
                elif sql.startswith("*/", index):
                    depth -= 1
                    index += 2
                else:
                    index += 1
            if depth:
                issues.append("unterminated block comment")
                index = length
            for position in range(start, index):
                if output[position] != "\n":
                    output[position] = " "
            continue
        if sql[index] == "'":
            start = index
            index += 1
            closed = False
            while index < length:
                if sql[index] == "'":
                    if index + 1 < length and sql[index + 1] == "'":
                        index += 2
                    else:
                        index += 1
                        closed = True
                        break
                elif sql[index] == "\\" and index + 1 < length:
                    # MySQL strings normally interpret backslash escapes.
                    index += 2
                else:
                    index += 1
            if not closed:
                issues.append("unterminated single-quoted literal")
            for position in range(start, index):
                if output[position] != "\n":
                    output[position] = " "
            continue
        if sql[index] in {'"', "`"}:
            delimiter = sql[index]
            index += 1
            closed = False
            while index < length:
                if sql[index] == delimiter:
                    if index + 1 < length and sql[index + 1] == delimiter:
                        index += 2
                    else:
                        index += 1
                        closed = True
                        break
                else:
                    if sql[index] == ";":
                        output[index] = " "
                    index += 1
            if not closed:
                issues.append("unterminated quoted identifier")
            continue
        index += 1
    return "".join(output), tuple(issues)


def _split_sql_statements(sql_text: str) -> tuple[tuple[str, ...], tuple[str, ...]]:
    masked, issues = _mask_non_code(sql_text)
    statements: list[str] = []
    start = 0
    for index, character in enumerate(masked):
        if character == ";":
            original = sql_text[start:index].strip()
            visible = masked[start:index].strip()
            if visible:
                statements.append(original)
            start = index + 1
    remainder = sql_text[start:].strip()
    visible_remainder = masked[start:].strip()
    parser_issues = list(issues)
    if visible_remainder:
        statements.append(remainder)
        parser_issues.append("final executable statement is not semicolon-terminated")
    return tuple(statements), tuple(dict.fromkeys(parser_issues))


def _top_level_tokens(masked_statement: str) -> tuple[tuple[str, int, int], ...]:
    tokens: list[tuple[str, int, int]] = []
    depth = 0
    index = 0
    while index < len(masked_statement):
        character = masked_statement[index]
        if character == '"':
            index += 1
            while index < len(masked_statement):
                if masked_statement[index] == '"':
                    if index + 1 < len(masked_statement) and masked_statement[index + 1] == '"':
                        index += 2
                    else:
                        index += 1
                        break
                else:
                    index += 1
            continue
        if character == "(":
            depth += 1
            index += 1
            continue
        if character == ")":
            depth = max(0, depth - 1)
            index += 1
            continue
        if depth == 0 and (character.isalpha() or character == "_"):
            start = index
            index += 1
            while index < len(masked_statement) and (
                masked_statement[index].isalnum() or masked_statement[index] in "_$"
            ):
                index += 1
            tokens.append((masked_statement[start:index].upper(), start, index))
            continue
        index += 1
    return tuple(tokens)


def _catalog_query_parts(masked: str) -> tuple[str, str, tuple[str, ...]]:
    tokens = _top_level_tokens(masked)
    select_token = next((token for token in tokens if token[0] == "SELECT"), None)
    if select_token is None:
        return "", "", ("catalog observation must be a statically visible SELECT",)
    from_token = next(
        (token for token in tokens if token[0] == "FROM" and token[1] > select_token[2]),
        None,
    )
    if from_token is None:
        return "", "", ("catalog SELECT must contain a top-level FROM",)
    projection = masked[select_token[2] : from_token[1]].strip()
    order_index: Optional[int] = None
    for first, second in zip(tokens, tokens[1:]):
        if first[0] == "ORDER" and second[0] == "BY" and first[1] > from_token[2]:
            order_index = second[2]
            break
    order_by = masked[order_index:].strip() if order_index is not None else ""
    issues: list[str] = []
    if not projection:
        issues.append("catalog SELECT projection must be explicit")
    else:
        depth = 0
        index = 0
        while index < len(projection):
            character = projection[index]
            if character == '"':
                index += 1
                while index < len(projection):
                    if projection[index] == '"':
                        if index + 1 < len(projection) and projection[index + 1] == '"':
                            index += 2
                        else:
                            index += 1
                            break
                    else:
                        index += 1
                continue
            if character == "(":
                depth += 1
            elif character == ")":
                depth = max(0, depth - 1)
            elif character == "*" and depth == 0:
                issues.append("catalog SELECT projection must not use a top-level wildcard")
                break
            index += 1
        if _VOLATILE_OUTPUT_PATTERN.search(projection):
            issues.append("catalog SELECT projection uses a known volatile function")
    if order_index is None:
        issues.append("catalog SELECT must have a top-level ORDER BY")
    else:
        if not order_by:
            issues.append("catalog SELECT ORDER BY must be explicit")
        elif re.fullmatch(r"\s*\d+(?:\s*,\s*\d+)*\s*", order_by):
            issues.append("catalog SELECT ORDER BY must name expressions, not ordinals")
        if _VOLATILE_OUTPUT_PATTERN.search(order_by):
            issues.append("catalog SELECT ORDER BY uses a known volatile function")
    return projection, order_by, tuple(issues)


def audit_catalog_observability(sql_text: str) -> CatalogObservabilityReport:
    """Audit catalog queries without banning stable catalog observability."""

    if not isinstance(sql_text, str):
        raise RegressionStyleError("sql_text must be a string")
    statements, split_issues = _split_sql_statements(sql_text)
    queries: list[CatalogQueryAudit] = []
    parser_issues = list(split_issues)
    for ordinal, statement in enumerate(statements, start=1):
        masked, mask_issues = _mask_non_code(statement)
        parser_issues.extend(f"statement {ordinal}: {issue}" for issue in mask_issues)
        qualified = tuple(
            re.sub(r"\s+", "", match.group("relation"))
            for match in _CATALOG_RELATION_PATTERN.finditer(masked)
        )
        unqualified = tuple(
            match.group("relation") for match in _UNQUALIFIED_CATALOG_PATTERN.finditer(masked)
        )
        if not qualified and not unqualified:
            continue
        projection, order_by, query_issues = _catalog_query_parts(masked)
        issues = list(query_issues)
        if unqualified:
            issues.append(
                "catalog relations must be explicitly schema-qualified: "
                + ", ".join(unqualified)
            )
        if re.search(r"\b(?:WITH|UNION|INTERSECT|EXCEPT)\b", masked, re.IGNORECASE):
            issues.append("compound catalog query requires explicit manual stability review")
        queries.append(
            CatalogQueryAudit(
                statement_ordinal=ordinal,
                relations=qualified + unqualified,
                projection=projection,
                order_by=order_by,
                issues=tuple(dict.fromkeys(issues)),
            )
        )
    return CatalogObservabilityReport(
        queries=tuple(queries), parser_issues=tuple(dict.fromkeys(parser_issues))
    )


@dataclass(frozen=True)
class ExecutionTranscript:
    """Raw process result; stdout and stderr deliberately remain bytes."""

    returncode: int
    stdout: bytes
    stderr: bytes

    def __post_init__(self) -> None:
        if type(self.returncode) is not int:
            raise RegressionStyleError("transcript.returncode must be an integer")
        if not isinstance(self.stdout, bytes):
            raise RegressionStyleError("transcript.stdout must be bytes")
        if not isinstance(self.stderr, bytes):
            raise RegressionStyleError("transcript.stderr must be bytes")


@dataclass(frozen=True)
class TranscriptDeterminismReport:
    deterministic: bool
    differences: tuple[str, ...]
    first_returncode: int
    second_returncode: int
    first_stdout_sha256: str
    second_stdout_sha256: str
    first_stderr_sha256: str
    second_stderr_sha256: str

    @property
    def both_failed(self) -> bool:
        return self.first_returncode != 0 and self.second_returncode != 0

    def __post_init__(self) -> None:
        for field_name in (
            "first_stdout_sha256",
            "second_stdout_sha256",
            "first_stderr_sha256",
            "second_stderr_sha256",
        ):
            if _SHA256_PATTERN.fullmatch(getattr(self, field_name)) is None:
                raise RegressionStyleError(f"{field_name} must be a lowercase SHA-256 digest")

    def to_dict(self) -> dict[str, Any]:
        return {
            "deterministic": self.deterministic,
            "differences": list(self.differences),
            "first_returncode": self.first_returncode,
            "second_returncode": self.second_returncode,
            "both_failed": self.both_failed,
            "first_stdout_sha256": self.first_stdout_sha256,
            "second_stdout_sha256": self.second_stdout_sha256,
            "first_stderr_sha256": self.first_stderr_sha256,
            "second_stderr_sha256": self.second_stderr_sha256,
        }


def compare_two_run_transcripts(
    first: ExecutionTranscript, second: ExecutionTranscript
) -> TranscriptDeterminismReport:
    """Compare status, stdout and stderr exactly, including failed runs."""

    if not isinstance(first, ExecutionTranscript) or not isinstance(
        second, ExecutionTranscript
    ):
        raise RegressionStyleError("both runs must be ExecutionTranscript values")
    differences: list[str] = []
    if first.returncode != second.returncode:
        differences.append("returncode")
    if first.stdout != second.stdout:
        differences.append("stdout")
    if first.stderr != second.stderr:
        differences.append("stderr")
    return TranscriptDeterminismReport(
        deterministic=not differences,
        differences=tuple(differences),
        first_returncode=first.returncode,
        second_returncode=second.returncode,
        first_stdout_sha256=hashlib.sha256(first.stdout).hexdigest(),
        second_stdout_sha256=hashlib.sha256(second.stdout).hexdigest(),
        first_stderr_sha256=hashlib.sha256(first.stderr).hexdigest(),
        second_stderr_sha256=hashlib.sha256(second.stderr).hexdigest(),
    )


def validate_two_run_determinism(
    first: ExecutionTranscript,
    second: ExecutionTranscript,
    *,
    expected_failure: Optional[bool] = None,
) -> TranscriptDeterminismReport:
    """Require byte determinism and optionally require success/failure outcome."""

    if expected_failure is not None and type(expected_failure) is not bool:
        raise RegressionStyleError("expected_failure must be a boolean when present")
    report = compare_two_run_transcripts(first, second)
    if not report.deterministic:
        raise RegressionStyleError(
            "two-run transcript is nondeterministic: " + ", ".join(report.differences)
        )
    if expected_failure is True and first.returncode == 0:
        raise RegressionStyleError("expected-failure run unexpectedly succeeded")
    if expected_failure is False and first.returncode != 0:
        raise RegressionStyleError("success run unexpectedly failed")
    return report


@dataclass(frozen=True)
class TableScriptAuditReport:
    created_tables: tuple[str, ...]
    pre_cleanup_tables: tuple[str, ...]
    final_cleanup_tables: tuple[str, ...]
    issues: tuple[str, ...]
    warnings: tuple[str, ...]
    manual_review_reasons: tuple[str, ...]

    @property
    def passed(self) -> bool:
        return not self.issues and not self.manual_review_reasons

    def to_dict(self) -> dict[str, Any]:
        return {
            "created_tables": list(self.created_tables),
            "pre_cleanup_tables": list(self.pre_cleanup_tables),
            "final_cleanup_tables": list(self.final_cleanup_tables),
            "issues": list(self.issues),
            "warnings": list(self.warnings),
            "manual_review_reasons": list(self.manual_review_reasons),
            "passed": self.passed,
        }


def _normalize_identifier(value: str) -> Optional[str]:
    parts = value.split(".")
    normalized: list[str] = []
    for part in parts:
        part = part.strip()
        if re.fullmatch(r"[A-Za-z_][A-Za-z0-9_$]*", part):
            normalized.append(part.lower())
        else:
            return None
    return ".".join(normalized)


def _split_identifier_list(value: str) -> Optional[tuple[str, ...]]:
    if "(" in value or ")" in value or '"' in value or "'" in value:
        return None
    names: list[str] = []
    for item in value.split(","):
        normalized = _normalize_identifier(item.strip())
        if normalized is None:
            return None
        names.append(normalized)
    return tuple(names) if names else None


def _drop_table_names(statement: str) -> Optional[tuple[str, ...]]:
    masked, _ = _mask_non_code(statement)
    match = _DROP_TABLE_PATTERN.fullmatch(masked.strip())
    if match is None:
        return None
    return _split_identifier_list(match.group("names"))


def audit_complete_table_script(
    sql_text: str, *, expected_object_prefix: Optional[str] = None
) -> TableScriptAuditReport:
    """Conservatively inspect a table-based script without rewriting SQL."""

    if not isinstance(sql_text, str) or not sql_text:
        raise RegressionStyleError("sql_text must be a non-empty string")
    if expected_object_prefix is not None:
        expected_object_prefix = _require_plain_string(
            expected_object_prefix, "expected_object_prefix"
        )
        if expected_object_prefix != expected_object_prefix.lower() or (
            _OBJECT_PREFIX_PATTERN.fullmatch(expected_object_prefix) is None
        ):
            raise RegressionStyleError(
                "expected_object_prefix must be a lowercase numbered SQL identifier prefix"
            )

    statements, parser_issues = _split_sql_statements(sql_text)
    issues: list[str] = []
    warnings: list[str] = []
    manual = list(parser_issues)
    created_tables: list[str] = []
    for ordinal, statement in enumerate(statements, start=1):
        masked, mask_issues = _mask_non_code(statement)
        manual.extend(f"statement {ordinal}: {issue}" for issue in mask_issues)
        if re.search(r"\b(?:CREATE|ALTER|DROP)\s+DATABASE\b", masked, re.IGNORECASE) or (
            re.search(r"(?m)^\s*\\(?:c|connect)\b", masked, re.IGNORECASE)
        ):
            issues.append("database-level create/drop/switch statements are forbidden")
        create_match = _CREATE_TABLE_PATTERN.match(masked)
        if create_match is not None:
            normalized = _normalize_identifier(create_match.group("name"))
            if normalized is None:
                manual.append(
                    f"statement {ordinal}: quoted or complex table identifier requires review"
                )
            else:
                created_tables.append(normalized)
                table_basename = normalized.rsplit(".", 1)[-1]
                if (
                    expected_object_prefix is not None
                    and not table_basename.startswith(expected_object_prefix)
                ):
                    issues.append(
                        f"created table {normalized} does not use {expected_object_prefix}"
                    )
        if re.search(
            r"^\s*(?:DO\b|CREATE\s+(?:OR\s+REPLACE\s+)?(?:FUNCTION|PROCEDURE)\b)",
            masked,
            re.IGNORECASE,
        ) or re.search(r"\bEXECUTE\b|\bFORMAT\s*\(", masked, re.IGNORECASE):
            manual.append(f"statement {ordinal}: dynamic SQL requires manual structure review")

    if not statements:
        issues.append("script contains no executable SQL statements")
        pre_cleanup: tuple[str, ...] = ()
        final_cleanup: tuple[str, ...] = ()
    else:
        pre_cleanup = _drop_table_names(statements[0]) or ()
        final_cleanup = _drop_table_names(statements[-1]) or ()
        if not pre_cleanup:
            issues.append("first executable statement must be DROP TABLE IF EXISTS")
        if not final_cleanup:
            issues.append("final executable statement must be DROP TABLE IF EXISTS")

    if not created_tables:
        issues.append("table-based script must create at least one table")
    else:
        created_set = set(created_tables)
        missing_pre = [name for name in created_tables if name not in set(pre_cleanup)]
        missing_final = [name for name in created_tables if name not in set(final_cleanup)]
        if missing_pre:
            issues.append("pre-cleanup misses created tables: " + ", ".join(missing_pre))
        if missing_final:
            issues.append("final cleanup misses created tables: " + ", ".join(missing_final))
        unexpected_pre = sorted(set(pre_cleanup) - created_set)
        unexpected_final = sorted(set(final_cleanup) - created_set)
        if unexpected_pre or unexpected_final:
            warnings.append(
                "cleanup mentions tables not statically created in this script: "
                + ", ".join(sorted(set(unexpected_pre + unexpected_final)))
            )
        reverse_created = tuple(reversed(created_tables))
        cleanup_created_order = tuple(
            name for name in final_cleanup if name in created_set
        )
        if final_cleanup and cleanup_created_order != reverse_created:
            warnings.append("final cleanup is not in reverse table-creation order")

    warnings.append(
        "static structure audit cannot prove target-statement or verification semantics"
    )
    return TableScriptAuditReport(
        created_tables=tuple(created_tables),
        pre_cleanup_tables=pre_cleanup,
        final_cleanup_tables=final_cleanup,
        issues=tuple(dict.fromkeys(issues)),
        warnings=tuple(dict.fromkeys(warnings)),
        manual_review_reasons=tuple(dict.fromkeys(manual)),
    )


__all__ = [
    "CatalogObservabilityReport",
    "CatalogQueryAudit",
    "ExecutionTranscript",
    "HuaweiSqlHeader",
    "REGRESSION_MAPPING_SCHEMA_VERSION",
    "RegressionBatchMapping",
    "RegressionCaseStyle",
    "RegressionStyleError",
    "TableScriptAuditReport",
    "TranscriptDeterminismReport",
    "audit_catalog_observability",
    "audit_complete_table_script",
    "build_regression_batch_mapping",
    "compare_two_run_transcripts",
    "render_huawei_sql_header",
    "validate_huawei_sql_header",
    "validate_two_run_determinism",
]
