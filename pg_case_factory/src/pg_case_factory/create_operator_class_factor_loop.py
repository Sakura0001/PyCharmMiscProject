"""Factor-value-loop obligation ledger for PostgreSQL 18.4 CREATE OPERATOR CLASS.

This module compiles the marginal ``GRM``/``SFV`` obligation ledger for
``CREATE OPERATOR CLASS``.  CREATE OPERATOR CLASS is a PostgreSQL
schema-level DDL statement with a single official synopsis branch.  The
statement defines a new operator class for a specific index method and
data type, with optional DEFAULT, FAMILY, OPERATOR, FUNCTION, and
STORAGE entries.

The statement touches the ``pg_catalog.pg_opclass`` catalog row (not a
``pg_class`` relation), so column/table/relation coverage is
``not_applicable`` and there is no ``INV`` block.  CREATE OPERATOR CLASS
does not create tables, so the bookend (DROP TABLE IF EXISTS) is never
emitted.

Each local obligation becomes exactly one regress program.  The 53
canonical ``SFV`` rows are loaded from the shipped applicability universe
(``postgresql_18_4_factor_audit.tsv``).
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path

from .applicability import load_shipped_applicability_universe


class CreateOperatorClassFactorLoopError(ValueError):
    """Raised when a frozen CREATE OPERATOR CLASS obligation input drifts."""


@dataclass(frozen=True)
class CreateOperatorClassGrammarAction:
    """One official target action form of the CREATE OPERATOR CLASS synopsis."""

    action_id: str
    grammar_branch_id: str
    syntax_template: str
    source_locator: str


@dataclass(frozen=True)
class CreateOperatorClassFactorObligation:
    ordinal: int
    obligation_id: str
    kind: str
    factor_key: str
    value: str
    consumer_action_id: str
    disposition: str
    source_locator: str
    delegated_statement_key: str | None = None


@dataclass(frozen=True)
class CreateOperatorClassFactorCase:
    ordinal: int
    case_id: str
    sql_filename: str
    object_prefix: str
    primary_obligation_id: str
    kind: str
    factor_key: str
    factor_value: str
    consumer_action_id: str
    outcome: str
    expected_sqlstate: str
    expected_failure_reason: str | None
    baseline_assignments: tuple[tuple[str, str], ...]
    execution_profile: str


@dataclass(frozen=True)
class CreateOperatorClassFactorLoopPlan:
    obligations: tuple[CreateOperatorClassFactorObligation, ...]
    cases: tuple[CreateOperatorClassFactorCase, ...]
    delegated: tuple[CreateOperatorClassFactorObligation, ...]
    obligation_multiset_sha256: str


# Official synopsis branch (PostgreSQL 18 sql-createopclass.html).
_BRANCH_CREATE = "branch_1"

_DOC_SOURCE = "postgresql-18.4-doc:sql-createopclass"

# A representative create_with_entries action used as the baseline consumer
# for canonical factors that are not bound to a specific branch variant.
_REPRESENTATIVE_ACTION = "create_with_entries"

# statement_branch canonical value -> target action.
_STATEMENT_BRANCH_CONSUMER = {
    _BRANCH_CREATE: "create_with_entries",
}


def _canonical_consumer(row) -> str:
    if row.factor == "statement_branch":
        try:
            return _STATEMENT_BRANCH_CONSUMER[row.value]
        except KeyError as exc:
            raise CreateOperatorClassFactorLoopError(
                f"unknown statement branch value: {row.value}"
            ) from exc
    return _REPRESENTATIVE_ACTION


# Canonical (factor, value) pairs that reach the PostgreSQL target check
# and are rejected (provisional sqlstates — DB phase verifies on PG 18.4).
_SFV_FAILURE_VALUES = frozenset(
    {
        ("expected_status", "failure"),
        ("target_object_state", "exists"),
        ("target_object_state", "exists_conflict"),
        ("family_clause", "present_missing"),
        ("dependency_state", "missing_operator"),
        ("dependency_state", "missing_function"),
        ("dependency_state", "missing_family"),
        ("index_method_compatibility", "incompatible"),
        ("index_method_compatibility", "storage_not_allowed_btree_hash"),
        ("invalid_combination", "syntax_valid_semantic_error"),
        ("invalid_combination", "object_type_mismatch"),
        ("privilege_context", "insufficient_privilege"),
        ("ownership_boundary", "non_privileged"),
    }
)

# Provisional PG 18.4 SQLSTATE for each reachable expected-failure value.
_SFV_FAILURE_SQLSTATE: dict[tuple[str, str], tuple[str, str]] = {
    ("expected_status", "failure"): (
        "42710",
        "duplicate_operator_class_provisional",
    ),
    ("target_object_state", "exists"): (
        "42710",
        "duplicate_operator_class_provisional",
    ),
    ("target_object_state", "exists_conflict"): (
        "42710",
        "duplicate_operator_class_provisional",
    ),
    ("family_clause", "present_missing"): (
        "42704",
        "missing_family_provisional",
    ),
    ("dependency_state", "missing_operator"): (
        "42704",
        "missing_operator_provisional",
    ),
    ("dependency_state", "missing_function"): (
        "42883",
        "missing_function_provisional",
    ),
    ("dependency_state", "missing_family"): (
        "42704",
        "missing_family_provisional",
    ),
    ("index_method_compatibility", "incompatible"): (
        "42804",
        "incompatible_type_method_provisional",
    ),
    ("index_method_compatibility", "storage_not_allowed_btree_hash"): (
        "42601",
        "storage_not_allowed_provisional",
    ),
    ("invalid_combination", "syntax_valid_semantic_error"): (
        "42P17",
        "invalid_object_definition_provisional",
    ),
    ("invalid_combination", "object_type_mismatch"): (
        "42804",
        "datatype_mismatch_provisional",
    ),
    ("privilege_context", "insufficient_privilege"): (
        "42501",
        "insufficient_privilege_provisional",
    ),
    ("ownership_boundary", "non_privileged"): (
        "42501",
        "insufficient_privilege_provisional",
    ),
}


def _load_grammar_actions() -> (
    tuple[CreateOperatorClassGrammarAction, ...]
):
    """Freeze every CREATE OPERATOR CLASS synopsis target action."""

    rows: tuple[tuple[str, str, str, str], ...] = (
        (
            "create_with_entries",
            _BRANCH_CREATE,
            (
                "CREATE OPERATOR CLASS name [DEFAULT] FOR TYPE data_type "
                "USING index_method [FAMILY family_name] AS "
                "{OPERATOR|FUNCTION|STORAGE} [, ...]"
            ),
            "synopsis-create-with-entries",
        ),
    )
    actions = [
        CreateOperatorClassGrammarAction(
            action_id=action_id,
            grammar_branch_id=branch,
            syntax_template=syntax,
            source_locator=f"{_DOC_SOURCE}:{locator}",
        )
        for action_id, branch, syntax, locator in rows
    ]
    if len(actions) != 1:
        raise CreateOperatorClassFactorLoopError(
            "create operator class action count drift"
        )
    return tuple(actions)


def _compile_grammar_obligations() -> (
    list[CreateOperatorClassFactorObligation]
):
    rows: list[CreateOperatorClassFactorObligation] = []
    for action in _load_grammar_actions():
        rows.append(
            CreateOperatorClassFactorObligation(
                ordinal=0,
                obligation_id=(
                    f"COPC-GRM|{action.grammar_branch_id}|"
                    f"{action.action_id}|target_form|"
                    f"{action.action_id}"
                ),
                kind="GRM",
                factor_key="target_form",
                value=action.action_id,
                consumer_action_id=action.action_id,
                disposition="covered",
                source_locator=action.source_locator,
            )
        )
    if len(rows) != 1:
        raise CreateOperatorClassFactorLoopError(
            "grammar obligation count drift"
        )
    return rows


def _compile_canonical_obligations(
    repository_root: Path,
) -> list[CreateOperatorClassFactorObligation]:
    catalog_rows = load_shipped_applicability_universe(
        repository_root
    ).rows_for_statement("create_operator_class")
    if len(catalog_rows) != 53:
        raise CreateOperatorClassFactorLoopError(
            "canonical obligation count drift"
        )
    rows: list[CreateOperatorClassFactorObligation] = []
    for row in catalog_rows:
        consumer = _canonical_consumer(row)
        is_failure = (row.factor, row.value) in _SFV_FAILURE_VALUES
        rows.append(
            CreateOperatorClassFactorObligation(
                ordinal=0,
                obligation_id=f"COPC-SFV|{row.row_id}|{consumer}",
                kind="SFV",
                factor_key=row.factor,
                value=row.value,
                consumer_action_id=consumer,
                disposition=(
                    "expected_failure" if is_failure else "covered"
                ),
                source_locator=f"{row.source_reference}#{row.row_id}",
            )
        )
    return rows


def _obligation_multiset_sha256(
    rows: tuple[CreateOperatorClassFactorObligation, ...],
) -> str:
    digest = hashlib.sha256(
        b"create-operator-class-factor-obligations-v1\n"
    )
    for row in rows:
        digest.update(
            json.dumps(
                {
                    "obligation_id": row.obligation_id,
                    "kind": row.kind,
                    "factor_key": row.factor_key,
                    "value": row.value,
                    "consumer_action_id": row.consumer_action_id,
                    "disposition": row.disposition,
                    "delegated_statement_key": (
                        row.delegated_statement_key
                    ),
                },
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
            ).encode("utf-8")
        )
        digest.update(b"\n")
    return digest.hexdigest()


# Branch action -> grammar branch id used by the renderer.
_ACTION_BRANCH = {
    "create_with_entries": _BRANCH_CREATE,
}

# data_type_index_method -> (data_type, index_method).
_DATA_TYPE_METHOD: dict[str, tuple[str, str]] = {
    "btree_integer": ("integer", "btree"),
    "hash_text": ("text", "hash"),
    "gist_geometry": ("custom", "gist"),
}

# data_type_index_method -> data_type_shape.
_DTIM_TO_DTS: dict[str, str] = {
    "btree_integer": "integer",
    "hash_text": "text",
    "gist_geometry": "custom_type",
}

# data_type_shape -> data_type_index_method.
_DTS_TO_DTIM: dict[str, str] = {
    "integer": "btree_integer",
    "text": "hash_text",
    "anyarray": "gist_geometry",
    "custom_type": "gist_geometry",
}

# ownership_boundary <-> privilege_context mapping.
_OB_TO_PC: dict[str, str] = {
    "superuser": "superuser",
    "schema_owner": "schema_create_privilege",
    "non_privileged": "insufficient_privilege",
}
_PC_TO_OB: dict[str, str] = {
    v: k for k, v in _OB_TO_PC.items()
}

# invalid_combination <-> index_method_compatibility mapping.
_IC_TO_IMC: dict[str, str] = {
    "none": "compatible",
    "syntax_valid_semantic_error": "storage_not_allowed_btree_hash",
    "object_type_mismatch": "incompatible",
}
_IMC_TO_IC: dict[str, str] = {
    v: k for k, v in _IC_TO_IMC.items()
}

# Dense baseline defaults (all positive T1-T6 factor values).
_BASELINE_DEFAULTS: dict[str, str] = {
    "statement_branch": _BRANCH_CREATE,
    "target_object_state": "absent",
    "data_type_index_method": "btree_integer",
    "expected_status": "success",
    "default_clause": "absent",
    "family_clause": "absent_auto_created",
    "operator_entry": "for_search",
    "function_entry": "with_op_type",
    "storage_entry": "absent",
    "privilege_context": "superuser",
    "name_shape": "plain_identifier",
    "data_type_shape": "integer",
    "dependency_state": "ready",
    "index_method_compatibility": "compatible",
    "invalid_combination": "none",
    "ownership_boundary": "superuser",
    "verification_mode": "catalog_query",
    "cleanup_mode": "drop_objects",
}


def _count_baseline_failures(a: dict[str, str]) -> int:
    return sum(
        1
        for pair in _SFV_FAILURE_VALUES
        if a.get(pair[0]) == pair[1]
    )


def _derive_overlapping_factors(a: dict[str, str]) -> None:
    """Derive boundary factors and expected_status from primary values.

    The T5 single-value factors describe the same scenario as their T1-T4
    counterparts.  When the primary factor is a T1-T4 value, the
    corresponding T5 value is derived; when the primary is a T5 value, the
    T1-T4 counterpart is derived.  This keeps the baseline assignment
    self-consistent so the render produces SQL that reaches the intended
    boundary.
    """

    # --- ownership_boundary <-> privilege_context ---
    ob = a.get("ownership_boundary", "superuser")
    if ob in _OB_TO_PC:
        a["privilege_context"] = _OB_TO_PC[ob]
    pc = a.get("privilege_context", "superuser")
    if pc in _PC_TO_OB:
        a["ownership_boundary"] = _PC_TO_OB[pc]

    # --- data_type_index_method <-> data_type_shape ---
    dtim = a.get("data_type_index_method", "btree_integer")
    if dtim in _DTIM_TO_DTS:
        a["data_type_shape"] = _DTIM_TO_DTS[dtim]
    dts = a.get("data_type_shape", "integer")
    if dts in _DTS_TO_DTIM:
        a["data_type_index_method"] = _DTS_TO_DTIM[dts]

    # --- invalid_combination <-> index_method_compatibility ---
    ic = a.get("invalid_combination", "none")
    if ic in _IC_TO_IMC:
        a["index_method_compatibility"] = _IC_TO_IMC[ic]
    imc = a.get("index_method_compatibility", "compatible")
    if imc in _IMC_TO_IC:
        a["invalid_combination"] = _IMC_TO_IC[imc]

    # --- storage_entry + data_type_index_method -> compatibility ---
    se = a.get("storage_entry", "absent")
    dtim = a.get("data_type_index_method", "btree_integer")
    if se != "absent" and dtim in ("btree_integer", "hash_text"):
        a["index_method_compatibility"] = (
            "storage_not_allowed_btree_hash"
        )
        a["invalid_combination"] = "syntax_valid_semantic_error"
    elif se != "absent" and dtim == "gist_geometry":
        if a.get("index_method_compatibility", "") not in (
            "incompatible",
        ):
            a["index_method_compatibility"] = "compatible"
            a["invalid_combination"] = "none"

    # --- dependency_state <-> family_clause ---
    ds = a.get("dependency_state", "ready")
    if ds == "missing_family":
        a["family_clause"] = "present_missing"
    fc = a.get("family_clause", "absent_auto_created")
    if fc == "present_missing":
        a["dependency_state"] = "missing_family"

    # --- target_object_state -> expected failure ---
    tos = a.get("target_object_state", "absent")
    if tos in ("exists", "exists_conflict"):
        a["expected_status"] = "failure"

    # --- family_clause=present_missing -> failure ---
    if a.get("family_clause", "") == "present_missing":
        a["expected_status"] = "failure"

    # --- dependency_state=missing_* -> failure ---
    ds = a.get("dependency_state", "ready")
    if ds in ("missing_operator", "missing_function", "missing_family"):
        a["expected_status"] = "failure"

    # --- privilege_context=insufficient_privilege -> failure ---
    if a.get("privilege_context", "") == "insufficient_privilege":
        a["expected_status"] = "failure"

    # --- index_method_compatibility failure -> expected_status ---
    imc = a.get("index_method_compatibility", "compatible")
    if imc in ("incompatible", "storage_not_allowed_btree_hash"):
        a["expected_status"] = "failure"

    # --- expected_status=failure -> representative failure ---
    es = a.get("expected_status", "success")
    if es == "failure":
        failures = _count_baseline_failures(a)
        if failures == 0:
            a["target_object_state"] = "exists"

    # --- Derive expected_status from failure count ---
    failures = _count_baseline_failures(a)
    a["expected_status"] = "failure" if failures > 0 else "success"


def _baseline_assignments(
    obligation: CreateOperatorClassFactorObligation,
) -> tuple[tuple[str, str], ...]:
    """One legal baseline value per factor key; primary overrides."""

    assignments: dict[str, str] = dict(_BASELINE_DEFAULTS)
    assignments["statement_branch"] = _ACTION_BRANCH[
        obligation.consumer_action_id
    ]
    assignments[obligation.factor_key] = obligation.value
    _derive_overlapping_factors(assignments)
    failures = _count_baseline_failures(assignments)
    assignments["expected_status"] = (
        "failure" if failures > 0 else "success"
    )
    if len(assignments) != len(set(assignments)):
        raise CreateOperatorClassFactorLoopError(
            "duplicate baseline factor key"
        )
    return tuple(sorted(assignments.items()))


def _expected_failure_details(
    obligation: CreateOperatorClassFactorObligation,
) -> tuple[str, str]:
    try:
        return _SFV_FAILURE_SQLSTATE[
            (obligation.factor_key, obligation.value)
        ]
    except KeyError as exc:
        raise CreateOperatorClassFactorLoopError(
            "missing expected-failure SQLSTATE for "
            f"{obligation.factor_key}={obligation.value}"
        ) from exc


def build_create_operator_class_factor_loop_plan(
    repository_root: Path,
) -> CreateOperatorClassFactorLoopPlan:
    """Assign one stable local SQL program to every obligation."""

    root = Path(repository_root).resolve(strict=True)
    obligations = compile_create_operator_class_factor_loop_obligations(
        root
    )
    cases: list[CreateOperatorClassFactorCase] = []
    delegated: list[CreateOperatorClassFactorObligation] = []
    for obligation in obligations:
        if obligation.disposition == "delegated":
            delegated.append(obligation)
            continue
        ordinal = len(cases) + 1
        if obligation.disposition == "expected_failure":
            sqlstate, failure_reason = _expected_failure_details(obligation)
            outcome = "expected_failure"
        else:
            outcome = "success"
            sqlstate = "00000"
            failure_reason = None
        cases.append(
            CreateOperatorClassFactorCase(
                ordinal=ordinal,
                case_id=f"CREATEOPERATORCLASS{ordinal:05d}",
                sql_filename=f"CREATEOPERATORCLASS{ordinal:05d}.sql",
                object_prefix=f"createoperatorclass_{ordinal:05d}_",
                primary_obligation_id=obligation.obligation_id,
                kind=obligation.kind,
                factor_key=obligation.factor_key,
                factor_value=obligation.value,
                consumer_action_id=obligation.consumer_action_id,
                outcome=outcome,
                expected_sqlstate=sqlstate,
                expected_failure_reason=failure_reason,
                baseline_assignments=_baseline_assignments(obligation),
                execution_profile="serial_sql",
            )
        )
    plan = CreateOperatorClassFactorLoopPlan(
        obligations=obligations,
        cases=tuple(cases),
        delegated=tuple(delegated),
        obligation_multiset_sha256=_obligation_multiset_sha256(
            obligations
        ),
    )
    if len(plan.cases) != 54 or len(plan.delegated) != 0:
        raise CreateOperatorClassFactorLoopError(
            "factor loop plan count drift"
        )
    if len({row.primary_obligation_id for row in plan.cases}) != 54:
        raise CreateOperatorClassFactorLoopError(
            "local obligation mapping drift"
        )
    if len({row.sql_filename for row in plan.cases}) != 54:
        raise CreateOperatorClassFactorLoopError(
            "duplicate SQL filename"
        )
    return plan


def compile_create_operator_class_factor_loop_obligations(
    repository_root: Path,
) -> tuple[CreateOperatorClassFactorObligation, ...]:
    """Compile the exact marginal obligation ledger in frozen source order."""

    root = Path(repository_root).resolve(strict=True)
    unordered_rows = (
        _compile_grammar_obligations()
        + _compile_canonical_obligations(root)
    )
    rows = tuple(
        CreateOperatorClassFactorObligation(
            ordinal=ordinal,
            obligation_id=row.obligation_id,
            kind=row.kind,
            factor_key=row.factor_key,
            value=row.value,
            consumer_action_id=row.consumer_action_id,
            disposition=row.disposition,
            source_locator=row.source_locator,
            delegated_statement_key=row.delegated_statement_key,
        )
        for ordinal, row in enumerate(unordered_rows, start=1)
    )
    if len(rows) != 54:
        raise CreateOperatorClassFactorLoopError(
            "obligation count drift"
        )
    if len({row.obligation_id for row in rows}) != len(rows):
        raise CreateOperatorClassFactorLoopError(
            "duplicate obligation id"
        )
    expected_kind_counts = {"GRM": 1, "SFV": 53}
    if Counter(row.kind for row in rows) != expected_kind_counts:
        raise CreateOperatorClassFactorLoopError(
            "obligation kind count drift"
        )
    if sum(row.disposition == "delegated" for row in rows) != 0:
        raise CreateOperatorClassFactorLoopError(
            "delegated obligation count drift"
        )
    if sum(
        row.disposition in {"covered", "expected_failure"}
        for row in rows
    ) != 54:
        raise CreateOperatorClassFactorLoopError(
            "local obligation count drift"
        )
    allowed_dispositions = {"covered", "expected_failure", "delegated"}
    if any(
        row.disposition not in allowed_dispositions for row in rows
    ):
        raise CreateOperatorClassFactorLoopError(
            "unknown obligation disposition"
        )
    return rows


__all__ = [
    "CreateOperatorClassFactorLoopError",
    "CreateOperatorClassGrammarAction",
    "CreateOperatorClassFactorObligation",
    "CreateOperatorClassFactorCase",
    "CreateOperatorClassFactorLoopPlan",
    "_SFV_FAILURE_SQLSTATE",
    "_SFV_FAILURE_VALUES",
    "_BASELINE_DEFAULTS",
    "_DATA_TYPE_METHOD",
    "compile_create_operator_class_factor_loop_obligations",
    "build_create_operator_class_factor_loop_plan",
    "_obligation_multiset_sha256",
]
