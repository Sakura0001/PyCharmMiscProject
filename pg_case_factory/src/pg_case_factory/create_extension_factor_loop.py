"""Factor-value-loop obligation ledger for PostgreSQL 18.4 CREATE EXTENSION.

This module compiles the marginal ``GRM``/``SFV`` obligation ledger for
``CREATE EXTENSION``.  CREATE EXTENSION is a PostgreSQL DDL statement
with a single official synopsis branch:
``CREATE EXTENSION [ IF NOT EXISTS ] extension_name [ WITH ]
[ SCHEMA schema_name ] [ VERSION version ] [ CASCADE ]``.
The statement loads an extension into ``pg_catalog.pg_extension`` (not a
``pg_class`` relation), so column/table/relation coverage is
``not_applicable`` and there is no ``INV`` block.

Each local obligation becomes exactly one regress program.  CREATE
EXTENSION requires superuser privilege for untrusted extensions; trusted
extensions can be installed by users with CREATE privilege.  The inventory
declares 24 factors / 62 factor values; together with the single GRM
synopsis obligation the ledger has 63 local cases.

The grammar ledger is self-contained (there is no separate
``create_extension_regress`` module): the 1 synopsis action is frozen
inline.  The 63 canonical ``SFV`` rows are loaded from the shipped
applicability universe (``postgresql_18_4_factor_audit.tsv``).
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path

from .applicability import load_shipped_applicability_universe


class CreateExtensionFactorLoopError(ValueError):
    """Raised when a frozen CREATE EXTENSION obligation input drifts."""


@dataclass(frozen=True)
class CreateExtensionGrammarAction:
    """One official target action form of the CREATE EXTENSION synopsis."""

    action_id: str
    grammar_branch_id: str
    syntax_template: str
    source_locator: str


@dataclass(frozen=True)
class CreateExtensionFactorObligation:
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
class CreateExtensionFactorCase:
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
class CreateExtensionFactorLoopPlan:
    obligations: tuple[CreateExtensionFactorObligation, ...]
    cases: tuple[CreateExtensionFactorCase, ...]
    delegated: tuple[CreateExtensionFactorObligation, ...]
    obligation_multiset_sha256: str


# Official synopsis branch (PostgreSQL 18 sql-createextension.html).
_BRANCH_1 = "branch_create_extension"

_DOC_SOURCE = "postgresql-18.4-doc:sql-createextension"

# CREATE EXTENSION has a single synopsis action; every factor value is
# observable through it.
_REPRESENTATIVE_ACTION = "create_extension"

# statement_branch canonical value -> target action.
_STATEMENT_BRANCH_CONSUMER = {
    "branch_create_extension": "create_extension",
    "branch_create_extension_if_not_exists": "create_extension",
}

# Canonical factor -> the action where the value is observable.
_SFV_FACTOR_CONSUMER = {
    "statement_branch": _REPRESENTATIVE_ACTION,
    "object_state": _REPRESENTATIVE_ACTION,
    "expected_status": _REPRESENTATIVE_ACTION,
    "if_not_exists_clause": _REPRESENTATIVE_ACTION,
    "schema_clause": _REPRESENTATIVE_ACTION,
    "version_clause": _REPRESENTATIVE_ACTION,
    "cascade_clause": _REPRESENTATIVE_ACTION,
    "extension_trust_level": _REPRESENTATIVE_ACTION,
    "extension_name_shape": _REPRESENTATIVE_ACTION,
    "schema_name_shape": _REPRESENTATIVE_ACTION,
    "version_string_shape": _REPRESENTATIVE_ACTION,
    "privilege_level": _REPRESENTATIVE_ACTION,
    "schema_existence": _REPRESENTATIVE_ACTION,
    "dependency_extension_state": _REPRESENTATIVE_ACTION,
    "control_file_presence": _REPRESENTATIVE_ACTION,
    "duplicate_extension_name": _REPRESENTATIVE_ACTION,
    "nonexistent_extension_script": _REPRESENTATIVE_ACTION,
    "nonexistent_schema": _REPRESENTATIVE_ACTION,
    "control_file_schema_conflict": _REPRESENTATIVE_ACTION,
    "insufficient_privilege": _REPRESENTATIVE_ACTION,
    "invalid_version": _REPRESENTATIVE_ACTION,
    "if_not_exists_no_op": _REPRESENTATIVE_ACTION,
    "verification_mode": _REPRESENTATIVE_ACTION,
    "cleanup_mode": _REPRESENTATIVE_ACTION,
}

# Canonical (factor, value) pairs that reach the PostgreSQL target
# check and are rejected (provisional sqlstates - DB phase verifies
# on PG 18.4).
_SFV_FAILURE_VALUES = frozenset(
    {
        # T1
        ("expected_status", "failure"),
        ("object_state", "already_exists"),
        # T2
        ("schema_clause", "control_file_schema_conflict"),
        ("version_clause", "invalid_version"),
        # T3
        ("extension_name_shape", "nonexistent_extension"),
        ("extension_name_shape", "duplicate_name"),
        ("schema_name_shape", "nonexistent_schema"),
        ("version_string_shape", "invalid_version_string"),
        # T4
        ("privilege_level", "non_superuser_no_create"),
        ("schema_existence", "schema_not_exists"),
        ("dependency_extension_state", "not_installed_no_cascade"),
        ("control_file_presence", "not_installed_on_system"),
        # T5 (overlapping with T1-T4)
        ("duplicate_extension_name", "same_name_conflict"),
        ("nonexistent_extension_script", "script_missing"),
        ("nonexistent_schema", "schema_missing"),
        ("control_file_schema_conflict", "conflict_without_cascade"),
        ("insufficient_privilege", "non_superuser_untrusted_extension"),
        ("insufficient_privilege", "no_create_privilege_trusted"),
        ("invalid_version", "nonexistent_version"),
    }
)

# Provisional PG 18.4 SQLSTATE for each reachable expected-failure value.
_SFV_FAILURE_SQLSTATE: dict[tuple[str, str], tuple[str, str]] = {
    ("expected_status", "failure"): (
        "42710",
        "duplicate_object_provisional",
    ),
    ("object_state", "already_exists"): (
        "42710",
        "duplicate_object_provisional",
    ),
    ("schema_clause", "control_file_schema_conflict"): (
        "42P17",
        "invalid_schema_definition_provisional",
    ),
    ("version_clause", "invalid_version"): (
        "22023",
        "invalid_parameter_value_provisional",
    ),
    ("extension_name_shape", "nonexistent_extension"): (
        "42704",
        "undefined_object_provisional",
    ),
    ("extension_name_shape", "duplicate_name"): (
        "42710",
        "duplicate_object_provisional",
    ),
    ("schema_name_shape", "nonexistent_schema"): (
        "3F000",
        "invalid_schema_provisional",
    ),
    ("version_string_shape", "invalid_version_string"): (
        "22023",
        "invalid_parameter_value_provisional",
    ),
    ("privilege_level", "non_superuser_no_create"): (
        "42501",
        "insufficient_privilege_provisional",
    ),
    ("schema_existence", "schema_not_exists"): (
        "3F000",
        "invalid_schema_provisional",
    ),
    ("dependency_extension_state", "not_installed_no_cascade"): (
        "2BP01",
        "extension_violation_provisional",
    ),
    ("control_file_presence", "not_installed_on_system"): (
        "58P01",
        "undefined_file_provisional",
    ),
    ("duplicate_extension_name", "same_name_conflict"): (
        "42710",
        "duplicate_object_provisional",
    ),
    ("nonexistent_extension_script", "script_missing"): (
        "58P01",
        "undefined_file_provisional",
    ),
    ("nonexistent_schema", "schema_missing"): (
        "3F000",
        "invalid_schema_provisional",
    ),
    ("control_file_schema_conflict", "conflict_without_cascade"): (
        "42P17",
        "invalid_schema_definition_provisional",
    ),
    ("insufficient_privilege", "non_superuser_untrusted_extension"): (
        "42501",
        "insufficient_privilege_provisional",
    ),
    ("insufficient_privilege", "no_create_privilege_trusted"): (
        "42501",
        "insufficient_privilege_provisional",
    ),
    ("invalid_version", "nonexistent_version"): (
        "22023",
        "invalid_parameter_value_provisional",
    ),
}


def _load_grammar_actions() -> (
    tuple[CreateExtensionGrammarAction, ...]
):
    """Freeze every CREATE EXTENSION synopsis target action."""

    rows: tuple[tuple[str, str, str, str], ...] = (
        (
            "create_extension",
            _BRANCH_1,
            (
                "CREATE EXTENSION [ IF NOT EXISTS ] extension_name "
                "[ WITH ] [ SCHEMA schema_name ] "
                "[ VERSION version ] [ CASCADE ]"
            ),
            "synopsis-branch-1",
        ),
    )
    actions = [
        CreateExtensionGrammarAction(
            action_id=action_id,
            grammar_branch_id=branch,
            syntax_template=syntax,
            source_locator=f"{_DOC_SOURCE}:{locator}",
        )
        for action_id, branch, syntax, locator in rows
    ]
    if len(actions) != 1:
        raise CreateExtensionFactorLoopError(
            "create extension action count drift"
        )
    return tuple(actions)


def _canonical_consumer(row) -> str:
    if row.factor == "statement_branch":
        try:
            return _STATEMENT_BRANCH_CONSUMER[row.value]
        except KeyError as exc:
            raise CreateExtensionFactorLoopError(
                f"unknown statement branch value: {row.value}"
            ) from exc
    try:
        return _SFV_FACTOR_CONSUMER[row.factor]
    except KeyError as exc:
        raise CreateExtensionFactorLoopError(
            f"canonical factor has no consumer action: {row.factor}"
        ) from exc


def _compile_grammar_obligations() -> (
    list[CreateExtensionFactorObligation]
):
    rows: list[CreateExtensionFactorObligation] = []
    for action in _load_grammar_actions():
        rows.append(
            CreateExtensionFactorObligation(
                ordinal=0,
                obligation_id=(
                    f"CE-GRM|{action.grammar_branch_id}|"
                    f"{action.action_id}|target_action|"
                    f"{action.action_id}"
                ),
                kind="GRM",
                factor_key="target_action",
                value=action.action_id,
                consumer_action_id=action.action_id,
                disposition="covered",
                source_locator=action.source_locator,
            )
        )
    if len(rows) != 1:
        raise CreateExtensionFactorLoopError(
            "grammar obligation count drift"
        )
    return rows


def _compile_canonical_obligations(
    repository_root: Path,
) -> list[CreateExtensionFactorObligation]:
    catalog_rows = load_shipped_applicability_universe(
        repository_root
    ).rows_for_statement("create_extension")
    if len(catalog_rows) != 62:
        raise CreateExtensionFactorLoopError(
            "canonical obligation count drift"
        )
    rows: list[CreateExtensionFactorObligation] = []
    for row in catalog_rows:
        consumer = _canonical_consumer(row)
        is_failure = (row.factor, row.value) in _SFV_FAILURE_VALUES
        rows.append(
            CreateExtensionFactorObligation(
                ordinal=0,
                obligation_id=f"CE-SFV|{row.row_id}|{consumer}",
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
    rows: tuple[CreateExtensionFactorObligation, ...],
) -> str:
    digest = hashlib.sha256(
        b"create-extension-factor-obligations-v1\n"
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
    "create_extension": _BRANCH_1,
}

# Dense baseline defaults (all positive T1-T4 + T6 factor values).  The
# T5 single-value factors (duplicate_extension_name,
# nonexistent_extension_script, nonexistent_schema,
# control_file_schema_conflict, insufficient_privilege, invalid_version,
# if_not_exists_no_op) are NOT baselined here: every declared value is
# either a failure mode or derived from T1-T4, so they are set only when
# they are the primary (or derived in the extension).
_BASELINE_DEFAULTS: dict[str, str] = {
    "statement_branch": _BRANCH_1,
    "grammar_branch": _BRANCH_1,
    "target_action": "create_extension",
    "object_state": "not_exists",
    "expected_status": "success",
    "if_not_exists_clause": "omitted",
    "schema_clause": "omitted",
    "version_clause": "omitted",
    "cascade_clause": "omitted",
    "extension_trust_level": "trusted",
    "extension_name_shape": "simple_id",
    "schema_name_shape": "simple_id",
    "version_string_shape": "identifier_form",
    "privilege_level": "superuser",
    "schema_existence": "schema_exists",
    "dependency_extension_state": "already_installed",
    "control_file_presence": "installed_on_system",
    "verification_mode": "pg_extension_catalog_query",
    "cleanup_mode": "drop_extension",
}


def _derive_overlapping_factors(a: dict[str, str]) -> None:
    """Derive T5 boundary factors and expected_status from T1-T4 values.

    The T5 single-value factors describe the same scenario as their
    T1-T4 counterparts.  When the primary factor is a T1-T4 value, the
    corresponding T5 value is derived; when the primary is a T5 value,
    the T1-T4 counterpart is derived.  This keeps the baseline
    assignment self-consistent so the render produces SQL that reaches
    the intended boundary.
    """

    os_ = a.get("object_state", "not_exists")
    ens = a.get("extension_name_shape", "simple_id")
    dan = a.get("duplicate_extension_name", "")
    cfp = a.get("control_file_presence", "installed_on_system")
    nes = a.get("nonexistent_extension_script", "")
    se = a.get("schema_existence", "schema_exists")
    sns = a.get("schema_name_shape", "simple_id")
    ns = a.get("nonexistent_schema", "")
    sc = a.get("schema_clause", "omitted")
    cfsc = a.get("control_file_schema_conflict", "")
    cas = a.get("cascade_clause", "omitted")
    pl = a.get("privilege_level", "superuser")
    etl = a.get("extension_trust_level", "trusted")
    ip = a.get("insufficient_privilege", "")
    vc = a.get("version_clause", "omitted")
    vss = a.get("version_string_shape", "identifier_form")
    iv = a.get("invalid_version", "")
    ine = a.get("if_not_exists_clause", "omitted")
    ino = a.get("if_not_exists_no_op", "")

    # 1. object_state / duplicate_extension_name /
    #    extension_name_shape=duplicate_name cluster
    if (
        os_ == "already_exists"
        or dan == "same_name_conflict"
        or ens == "duplicate_name"
    ):
        a["object_state"] = "already_exists"
        a["duplicate_extension_name"] = "same_name_conflict"
        if ens != "duplicate_name":
            a["extension_name_shape"] = "duplicate_name"
    else:
        a["object_state"] = "not_exists"
        a["duplicate_extension_name"] = "no_conflict"

    # 2. control_file_presence / nonexistent_extension_script /
    #    extension_name_shape=nonexistent_extension cluster
    if (
        cfp == "not_installed_on_system"
        or nes == "script_missing"
        or ens == "nonexistent_extension"
    ):
        a["control_file_presence"] = "not_installed_on_system"
        a["nonexistent_extension_script"] = "script_missing"
        if ens != "nonexistent_extension":
            a["extension_name_shape"] = "nonexistent_extension"
    else:
        if cfp != "installed_in_extension_control_path":
            a["control_file_presence"] = "installed_on_system"
        a["nonexistent_extension_script"] = "script_exists"

    # 3. schema_existence / nonexistent_schema /
    #    schema_name_shape=nonexistent_schema cluster
    if (
        se == "schema_not_exists"
        or ns == "schema_missing"
        or sns == "nonexistent_schema"
    ):
        a["schema_existence"] = "schema_not_exists"
        a["nonexistent_schema"] = "schema_missing"
        if sns != "nonexistent_schema":
            a["schema_name_shape"] = "nonexistent_schema"
    else:
        a["schema_existence"] = "schema_exists"
        a["nonexistent_schema"] = "schema_exists"

    # 4. schema_clause / control_file_schema_conflict cluster
    #    (depends on cascade_clause)
    if (
        sc == "control_file_schema_conflict"
        or cfsc in (
            "conflict_without_cascade",
            "conflict_with_cascade_ignored",
        )
    ):
        a["schema_clause"] = "control_file_schema_conflict"
        if cas == "specified" or cfsc == "conflict_with_cascade_ignored":
            a["control_file_schema_conflict"] = (
                "conflict_with_cascade_ignored"
            )
            a["cascade_clause"] = "specified"
        else:
            a["control_file_schema_conflict"] = (
                "conflict_without_cascade"
            )
            a["cascade_clause"] = "omitted"
    else:
        a["control_file_schema_conflict"] = "no_conflict"

    # 5. privilege_level / insufficient_privilege /
    #    extension_trust_level cluster
    if pl == "non_superuser_no_create" or ip in (
        "non_superuser_untrusted_extension",
        "no_create_privilege_trusted",
    ):
        a["privilege_level"] = "non_superuser_no_create"
        if etl == "untrusted" or ip == "non_superuser_untrusted_extension":
            a["extension_trust_level"] = "untrusted"
            a["insufficient_privilege"] = (
                "non_superuser_untrusted_extension"
            )
        else:
            a["insufficient_privilege"] = "no_create_privilege_trusted"
    else:
        a["privilege_level"] = "superuser"
        a["insufficient_privilege"] = "sufficient_privilege"

    # 6. version_clause / invalid_version /
    #    version_string_shape=invalid_version_string cluster
    if (
        vc == "invalid_version"
        or iv == "nonexistent_version"
        or vss == "invalid_version_string"
    ):
        a["version_clause"] = "invalid_version"
        a["invalid_version"] = "nonexistent_version"
        a["version_string_shape"] = "invalid_version_string"
    else:
        a["invalid_version"] = "valid_version"

    # 7. if_not_exists_clause / object_state /
    #    if_not_exists_no_op cluster
    if (
        ine == "specified"
        and a.get("object_state") == "already_exists"
    ) or ino == "no_op_notice":
        a["if_not_exists_no_op"] = "no_op_notice"
        a["if_not_exists_clause"] = "specified"
        a["object_state"] = "already_exists"
        a["duplicate_extension_name"] = "same_name_conflict"
    else:
        a["if_not_exists_no_op"] = "new_install"

    # 8. expected_status: needs a real failure trigger.
    if a.get("expected_status") == "failure":
        if a.get("object_state") != "already_exists":
            a["object_state"] = "already_exists"
            a["duplicate_extension_name"] = "same_name_conflict"
            if a.get("extension_name_shape") not in (
                "duplicate_name",
                "nonexistent_extension",
            ):
                a["extension_name_shape"] = "duplicate_name"
        _derive_overlapping_factors_inner(a)
    else:
        _derive_overlapping_factors_inner(a)


def _derive_overlapping_factors_inner(a: dict[str, str]) -> None:
    """Set expected_status from the failure count."""

    failures = _count_baseline_failures(a)
    a["expected_status"] = "failure" if failures > 0 else "success"


def _count_baseline_failures(a: dict[str, str]) -> int:
    return sum(
        1
        for pair in _SFV_FAILURE_VALUES
        if a.get(pair[0]) == pair[1]
    )


def _baseline_assignments(
    obligation: CreateExtensionFactorObligation,
) -> tuple[tuple[str, str], ...]:
    """One legal baseline value per factor key; primary overrides."""

    assignments: dict[str, str] = dict(_BASELINE_DEFAULTS)
    assignments["grammar_branch"] = _ACTION_BRANCH[
        obligation.consumer_action_id
    ]
    assignments["target_action"] = obligation.consumer_action_id
    assignments["statement_branch"] = _ACTION_BRANCH[
        obligation.consumer_action_id
    ]
    assignments[obligation.factor_key] = obligation.value
    _derive_overlapping_factors(assignments)
    if len(assignments) != len(set(assignments)):
        raise CreateExtensionFactorLoopError(
            "duplicate baseline factor key"
        )
    return tuple(sorted(assignments.items()))


def _expected_failure_details(
    obligation: CreateExtensionFactorObligation,
) -> tuple[str, str]:
    try:
        return _SFV_FAILURE_SQLSTATE[
            (obligation.factor_key, obligation.value)
        ]
    except KeyError as exc:
        raise CreateExtensionFactorLoopError(
            "missing expected-failure SQLSTATE for "
            f"{obligation.factor_key}={obligation.value}"
        ) from exc


def build_create_extension_factor_loop_plan(
    repository_root: Path,
) -> CreateExtensionFactorLoopPlan:
    """Assign one stable local SQL program to every obligation."""

    root = Path(repository_root).resolve(strict=True)
    obligations = compile_create_extension_factor_loop_obligations(
        root
    )
    cases: list[CreateExtensionFactorCase] = []
    delegated: list[CreateExtensionFactorObligation] = []
    for obligation in obligations:
        if obligation.disposition == "delegated":
            delegated.append(obligation)
            continue
        ordinal = len(cases) + 1
        if obligation.disposition == "expected_failure":
            sqlstate, failure_reason = _expected_failure_details(
                obligation
            )
            outcome = "expected_failure"
        else:
            outcome = "success"
            sqlstate = "00000"
            failure_reason = None
        cases.append(
            CreateExtensionFactorCase(
                ordinal=ordinal,
                case_id=f"CREATEEXTENSION{ordinal:05d}",
                sql_filename=(
                    f"CREATEEXTENSION{ordinal:05d}.sql"
                ),
                object_prefix=(
                    f"createextension_{ordinal:05d}_"
                ),
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
    plan = CreateExtensionFactorLoopPlan(
        obligations=obligations,
        cases=tuple(cases),
        delegated=tuple(delegated),
        obligation_multiset_sha256=_obligation_multiset_sha256(
            obligations
        ),
    )
    if len(plan.cases) != 63 or len(plan.delegated) != 0:
        raise CreateExtensionFactorLoopError(
            "factor loop plan count drift"
        )
    if len({row.primary_obligation_id for row in plan.cases}) != 63:
        raise CreateExtensionFactorLoopError(
            "local obligation mapping drift"
        )
    if len({row.sql_filename for row in plan.cases}) != 63:
        raise CreateExtensionFactorLoopError("duplicate SQL filename")
    return plan


def compile_create_extension_factor_loop_obligations(
    repository_root: Path,
) -> tuple[CreateExtensionFactorObligation, ...]:
    """Compile the exact marginal obligation ledger in frozen source order."""

    root = Path(repository_root).resolve(strict=True)
    unordered_rows = (
        _compile_grammar_obligations()
        + _compile_canonical_obligations(root)
    )
    rows = tuple(
        CreateExtensionFactorObligation(
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
    if len(rows) != 63:
        raise CreateExtensionFactorLoopError(
            "obligation count drift"
        )
    if len({row.obligation_id for row in rows}) != len(rows):
        raise CreateExtensionFactorLoopError("duplicate obligation id")
    expected_kind_counts = {"GRM": 1, "SFV": 62}
    if Counter(row.kind for row in rows) != expected_kind_counts:
        raise CreateExtensionFactorLoopError(
            "obligation kind count drift"
        )
    if sum(row.disposition == "delegated" for row in rows) != 0:
        raise CreateExtensionFactorLoopError(
            "delegated obligation count drift"
        )
    if sum(
        row.disposition in {"covered", "expected_failure"}
        for row in rows
    ) != 63:
        raise CreateExtensionFactorLoopError(
            "local obligation count drift"
        )
    allowed_dispositions = {"covered", "expected_failure", "delegated"}
    if any(
        row.disposition not in allowed_dispositions for row in rows
    ):
        raise CreateExtensionFactorLoopError(
            "unknown obligation disposition"
        )
    return rows


__all__ = [
    "CreateExtensionFactorLoopError",
    "CreateExtensionGrammarAction",
    "CreateExtensionFactorObligation",
    "CreateExtensionFactorCase",
    "CreateExtensionFactorLoopPlan",
    "_SFV_FAILURE_SQLSTATE",
    "_SFV_FAILURE_VALUES",
    "compile_create_extension_factor_loop_obligations",
    "build_create_extension_factor_loop_plan",
    "_obligation_multiset_sha256",
]
