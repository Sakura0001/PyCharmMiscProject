"""Factor-value-loop obligation ledger for PostgreSQL 18.4 CREATE COLLATION.

This module compiles the marginal ``GRM``/``SFV`` obligation ledger for
``CREATE COLLATION``.  CREATE COLLATION is a PostgreSQL schema-level DDL
statement with 2 official synopsis branches: the parameter-definition
form (``CREATE COLLATION name ( ... )``) and the copy-from-existing form
(``CREATE COLLATION name FROM existing_collation``).  PG18 additionally
introduces 3 builtin-provider locale forms (C, C.UTF-8, PG_UNICODE_FAST)
tracked as separate grammar target forms.

The statement touches the ``pg_catalog.pg_collation`` catalog row (not a
``pg_class`` relation), so column/table/relation coverage is
``not_applicable`` and there is no ``INV`` block.  CREATE COLLATION does
not create tables, so the bookend (DROP TABLE IF EXISTS) is never emitted.

Each local obligation becomes exactly one regress program.  The 50
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


class CreateCollationFactorLoopError(ValueError):
    """Raised when a frozen CREATE COLLATION obligation input drifts."""


@dataclass(frozen=True)
class CreateCollationGrammarAction:
    """One official target action form of the CREATE COLLATION synopsis."""

    action_id: str
    grammar_branch_id: str
    syntax_template: str
    source_locator: str


@dataclass(frozen=True)
class CreateCollationFactorObligation:
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
class CreateCollationFactorCase:
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
class CreateCollationFactorLoopPlan:
    obligations: tuple[CreateCollationFactorObligation, ...]
    cases: tuple[CreateCollationFactorCase, ...]
    delegated: tuple[CreateCollationFactorObligation, ...]
    obligation_multiset_sha256: str


# Official synopsis branches (PostgreSQL 18 sql-createcollation.html).
_BRANCH_DEFINE = "branch_define_with_params"
_BRANCH_FROM = "branch_from_existing"
_BRANCH_BUILTIN_C = "branch_pg18_builtin_c"
_BRANCH_BUILTIN_C_UTF8 = "branch_pg18_builtin_c_utf8"
_BRANCH_BUILTIN_PG_UNICODE_FAST = "branch_pg18_builtin_pg_unicode_fast"

_DOC_SOURCE = "postgresql-18.4-doc:sql-createcollation"

# A representative define_with_params action used as the baseline consumer
# for canonical factors that are not bound to one specific branch.
_REPRESENTATIVE_ACTION = "define_with_params"

# statement_branch canonical value -> target action.
_STATEMENT_BRANCH_CONSUMER = {
    _BRANCH_DEFINE: "define_with_params",
    _BRANCH_FROM: "from_existing",
}

# locale_setting canonical value -> target action (pg18 builtin forms).
_LOCALE_SETTING_CONSUMER = {
    "BUILTIN_C": "pg18_builtin_c",
    "BUILTIN_C_UTF8": "pg18_builtin_c_utf8",
    "BUILTIN_PG_UNICODE_FAST": "pg18_builtin_pg_unicode_fast",
    "LOCALE_only": "define_with_params",
    "LC_COLLATE_LC_CTYPE_separate": "define_with_params",
    "LOCALE_with_provider": "define_with_params",
}


def _canonical_consumer(row) -> str:
    if row.factor == "statement_branch":
        try:
            return _STATEMENT_BRANCH_CONSUMER[row.value]
        except KeyError as exc:
            raise CreateCollationFactorLoopError(
                f"unknown statement branch value: {row.value}"
            ) from exc
    if row.factor == "locale_setting":
        try:
            return _LOCALE_SETTING_CONSUMER[row.value]
        except KeyError as exc:
            raise CreateCollationFactorLoopError(
                f"unknown locale_setting value: {row.value}"
            ) from exc
    if row.factor == "provider" and row.value == "builtin":
        return "pg18_builtin_c"
    if row.factor in ("from_collation_shape", "from_collation_dependency"):
        return "from_existing"
    return _REPRESENTATIVE_ACTION


# Canonical (factor, value) pairs that reach the PostgreSQL target check
# and are rejected (provisional sqlstates — DB phase verifies on PG 18.4).
_SFV_FAILURE_VALUES = frozenset(
    {
        ("expected_status", "failure"),
        ("object_state", "already_exists"),
        ("from_collation_shape", "nonexistent_collation"),
        ("from_collation_dependency", "from_not_exists"),
        ("privilege_level", "non_schema_owner"),
        ("locale_validity", "invalid_locale_for_encoding"),
        ("duplicate_collation", "same_schema_same_name_no_ifne"),
        ("invalid_locale_for_encoding", "wrong_encoding_locale"),
        ("icu_not_available", "provider_icu_no_support"),
        ("nondeterministic_non_icu", "deterministic_false_libc"),
        ("rules_non_icu", "rules_with_libc"),
        ("locale_and_lc_conflict", "locale_with_lc_collate"),
        ("locale_and_lc_conflict", "locale_with_lc_ctype"),
        ("insufficient_privilege", "no_create_on_schema"),
        ("icu_availability", "icu_not_available"),
    }
)

# Provisional PG 18.4 SQLSTATE for each reachable expected-failure value.
_SFV_FAILURE_SQLSTATE: dict[tuple[str, str], tuple[str, str]] = {
    ("expected_status", "failure"): (
        "42710",
        "duplicate_collation_provisional",
    ),
    ("object_state", "already_exists"): (
        "42710",
        "duplicate_collation_provisional",
    ),
    ("duplicate_collation", "same_schema_same_name_no_ifne"): (
        "42710",
        "duplicate_collation_provisional",
    ),
    ("from_collation_shape", "nonexistent_collation"): (
        "42704",
        "missing_source_collation_provisional",
    ),
    ("from_collation_dependency", "from_not_exists"): (
        "42704",
        "missing_source_collation_provisional",
    ),
    ("privilege_level", "non_schema_owner"): (
        "42501",
        "insufficient_privilege_provisional",
    ),
    ("insufficient_privilege", "no_create_on_schema"): (
        "42501",
        "insufficient_privilege_provisional",
    ),
    ("locale_validity", "invalid_locale_for_encoding"): (
        "22023",
        "invalid_locale_provisional",
    ),
    ("invalid_locale_for_encoding", "wrong_encoding_locale"): (
        "22023",
        "invalid_locale_provisional",
    ),
    ("icu_not_available", "provider_icu_no_support"): (
        "0A000",
        "icu_not_available_provisional",
    ),
    ("icu_availability", "icu_not_available"): (
        "0A000",
        "icu_not_available_provisional",
    ),
    ("nondeterministic_non_icu", "deterministic_false_libc"): (
        "22023",
        "nondeterministic_non_icu_provisional",
    ),
    ("rules_non_icu", "rules_with_libc"): (
        "22023",
        "rules_non_icu_provisional",
    ),
    ("locale_and_lc_conflict", "locale_with_lc_collate"): (
        "42601",
        "locale_conflict_provisional",
    ),
    ("locale_and_lc_conflict", "locale_with_lc_ctype"): (
        "42601",
        "locale_conflict_provisional",
    ),
}


def _load_grammar_actions() -> (
    tuple[CreateCollationGrammarAction, ...]
):
    """Freeze every CREATE COLLATION synopsis target action."""

    rows: tuple[tuple[str, str, str, str], ...] = (
        (
            "define_with_params",
            _BRANCH_DEFINE,
            "CREATE COLLATION [IF NOT EXISTS] name ( [LOCALE=...] ... )",
            "synopsis-define-with-params",
        ),
        (
            "from_existing",
            _BRANCH_FROM,
            "CREATE COLLATION [IF NOT EXISTS] name FROM existing_collation",
            "synopsis-from-existing",
        ),
        (
            "pg18_builtin_c",
            _BRANCH_BUILTIN_C,
            "CREATE COLLATION name (provider = builtin, locale = 'C')",
            "pg18-builtin-c",
        ),
        (
            "pg18_builtin_c_utf8",
            _BRANCH_BUILTIN_C_UTF8,
            "CREATE COLLATION name (provider = builtin, locale = 'C.UTF-8')",
            "pg18-builtin-c-utf8",
        ),
        (
            "pg18_builtin_pg_unicode_fast",
            _BRANCH_BUILTIN_PG_UNICODE_FAST,
            "CREATE COLLATION name (provider = builtin, locale = 'PG_UNICODE_FAST')",
            "pg18-builtin-pg-unicode-fast",
        ),
    )
    actions = [
        CreateCollationGrammarAction(
            action_id=action_id,
            grammar_branch_id=branch,
            syntax_template=syntax,
            source_locator=f"{_DOC_SOURCE}:{locator}",
        )
        for action_id, branch, syntax, locator in rows
    ]
    if len(actions) != 5:
        raise CreateCollationFactorLoopError(
            "create collation action count drift"
        )
    return tuple(actions)


def _compile_grammar_obligations() -> (
    list[CreateCollationFactorObligation]
):
    rows: list[CreateCollationFactorObligation] = []
    for action in _load_grammar_actions():
        rows.append(
            CreateCollationFactorObligation(
                ordinal=0,
                obligation_id=(
                    f"CCOL-GRM|{action.grammar_branch_id}|"
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
    if len(rows) != 5:
        raise CreateCollationFactorLoopError(
            "grammar obligation count drift"
        )
    return rows


def _compile_canonical_obligations(
    repository_root: Path,
) -> list[CreateCollationFactorObligation]:
    catalog_rows = load_shipped_applicability_universe(
        repository_root
    ).rows_for_statement("create_collation")
    if len(catalog_rows) != 50:
        raise CreateCollationFactorLoopError(
            "canonical obligation count drift"
        )
    rows: list[CreateCollationFactorObligation] = []
    for row in catalog_rows:
        consumer = _canonical_consumer(row)
        is_failure = (row.factor, row.value) in _SFV_FAILURE_VALUES
        rows.append(
            CreateCollationFactorObligation(
                ordinal=0,
                obligation_id=f"CCOL-SFV|{row.row_id}|{consumer}",
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
    rows: tuple[CreateCollationFactorObligation, ...],
) -> str:
    digest = hashlib.sha256(
        b"create-collation-factor-obligations-v1\n"
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
    "define_with_params": _BRANCH_DEFINE,
    "from_existing": _BRANCH_FROM,
    "pg18_builtin_c": _BRANCH_BUILTIN_C,
    "pg18_builtin_c_utf8": _BRANCH_BUILTIN_C_UTF8,
    "pg18_builtin_pg_unicode_fast": _BRANCH_BUILTIN_PG_UNICODE_FAST,
}

# Dense baseline defaults (all positive T1-T4 + T6 factor values).  The T5
# single-value factors are derived in :func:`_derive_overlapping_factors`.
_BASELINE_DEFAULTS: dict[str, str] = {
    "statement_branch": _BRANCH_DEFINE,
    "object_state": "not_exists",
    "expected_status": "success",
    "if_not_exists_clause": "absent",
    "provider": "libc_default",
    "deterministic_option": "true_default",
    "collation_name_shape": "plain_identifier",
    "locale_setting": "LOCALE_only",
    "from_collation_shape": "existing_builtin_collation",
    "rules_setting": "no_rules",
    "privilege_level": "schema_owner_with_create",
    "icu_availability": "icu_available",
    "locale_validity": "valid_locale_for_encoding",
    "from_collation_dependency": "from_exists",
    "verification_mode": "pg_collation_catalog_query",
    "cleanup_mode": "DROP_COLLATION_IF_EXISTS",
}

_BUILTIN_LOCALES = frozenset(
    {"BUILTIN_C", "BUILTIN_C_UTF8", "BUILTIN_PG_UNICODE_FAST"}
)


def _count_baseline_failures(a: dict[str, str]) -> int:
    return sum(
        1
        for pair in _SFV_FAILURE_VALUES
        if a.get(pair[0]) == pair[1]
    )


def _derive_overlapping_factors(a: dict[str, str]) -> None:
    """Derive T5 boundary factors and expected_status from T1-T4 values.

    The T5 single-value factors describe the same scenario as their T1-T4
    counterparts.  When the primary factor is a T1-T4 value, the
    corresponding T5 value is derived; when the primary is a T5 value, the
    T1-T4 counterpart is derived.  This keeps the baseline assignment
    self-consistent so the render produces SQL that reaches the intended
    boundary.
    """

    # --- T5 → T1-T4 derivation (when T5 is the primary, set T1-T4) -----
    dc = a.get("duplicate_collation", "")
    if dc == "same_schema_same_name_no_ifne":
        a["object_state"] = "already_exists"
        a["if_not_exists_clause"] = "absent"
    elif dc == "same_schema_same_name_with_ifne":
        a["object_state"] = "already_exists"
        a["if_not_exists_clause"] = "present_with_conflict"

    ile = a.get("invalid_locale_for_encoding", "")
    if ile == "wrong_encoding_locale":
        a["locale_validity"] = "invalid_locale_for_encoding"

    ina = a.get("icu_not_available", "")
    if ina == "provider_icu_no_support":
        a["provider"] = "icu"
        a["icu_availability"] = "icu_not_available"

    nni = a.get("nondeterministic_non_icu", "")
    if nni == "deterministic_false_libc":
        a["provider"] = "libc_default"
        a["deterministic_option"] = "false_icu_only"

    rni = a.get("rules_non_icu", "")
    if rni == "rules_with_libc":
        a["provider"] = "libc_default"
        a["rules_setting"] = "with_rules"

    ip = a.get("insufficient_privilege", "")
    if ip == "no_create_on_schema":
        a["privilege_level"] = "non_schema_owner"

    # --- ifne ↔ object_state ---
    ifne = a.get("if_not_exists_clause", "absent")
    if ifne == "present_with_conflict":
        a["object_state"] = "already_exists"
    elif ifne == "present_no_conflict":
        a["object_state"] = "not_exists"

    # --- object_state + ifne → duplicate_collation ---
    os = a.get("object_state", "not_exists")
    ifne = a.get("if_not_exists_clause", "absent")
    if os == "already_exists" and ifne == "absent":
        a["duplicate_collation"] = "same_schema_same_name_no_ifne"
    elif os == "already_exists" and ifne == "present_with_conflict":
        a["duplicate_collation"] = "same_schema_same_name_with_ifne"

    # --- from_collation_shape ↔ from_collation_dependency ---
    fcs = a.get("from_collation_shape", "existing_builtin_collation")
    fcd = a.get("from_collation_dependency", "from_exists")
    if fcs == "nonexistent_collation":
        a["from_collation_dependency"] = "from_not_exists"
    elif fcd == "from_not_exists":
        a["from_collation_shape"] = "nonexistent_collation"

    # --- provider ↔ deterministic/rules → T5 ---------------------------
    prov = a.get("provider", "libc_default")
    det = a.get("deterministic_option", "true_default")
    rules = a.get("rules_setting", "no_rules")

    # If det=false with libc (and not explicitly a T5 failure), switch to icu
    if det == "false_icu_only" and prov == "libc_default":
        if a.get("nondeterministic_non_icu", "") != "deterministic_false_libc":
            a["provider"] = "icu"
            prov = "icu"

    # If rules=with_rules with libc (and not explicitly T5), switch to icu
    if rules == "with_rules" and prov == "libc_default":
        if a.get("rules_non_icu", "") != "rules_with_libc":
            a["provider"] = "icu"
            prov = "icu"

    prov = a.get("provider", "libc_default")
    if prov == "libc_default" and det == "false_icu_only":
        a["nondeterministic_non_icu"] = "deterministic_false_libc"
    if prov == "libc_default" and rules == "with_rules":
        a["rules_non_icu"] = "rules_with_libc"
    if prov == "icu":
        if a.get("icu_availability", "") != "icu_not_available":
            a["icu_availability"] = "icu_available"

    # --- icu_availability → provider/icu_not_available ---
    if a.get("icu_availability", "") == "icu_not_available":
        a["provider"] = "icu"
        a["icu_not_available"] = "provider_icu_no_support"

    # --- locale_setting ↔ provider (builtin) ---
    ls = a.get("locale_setting", "LOCALE_only")
    if ls in _BUILTIN_LOCALES:
        a["provider"] = "builtin"
    prov = a.get("provider", "libc_default")
    if prov == "builtin" and ls not in _BUILTIN_LOCALES:
        a["locale_setting"] = "BUILTIN_C"

    # --- privilege_level → insufficient_privilege ---
    priv = a.get("privilege_level", "schema_owner_with_create")
    if priv == "non_schema_owner":
        a["insufficient_privilege"] = "no_create_on_schema"

    # --- locale_validity → invalid_locale_for_encoding ---
    lv = a.get("locale_validity", "valid_locale_for_encoding")
    if lv == "invalid_locale_for_encoding":
        a["invalid_locale_for_encoding"] = "wrong_encoding_locale"

    # --- expected_status=failure → representative failure ---
    es = a.get("expected_status", "success")
    if es == "failure":
        a["object_state"] = "already_exists"
        a["if_not_exists_clause"] = "absent"
        a["duplicate_collation"] = "same_schema_same_name_no_ifne"

    # --- Derive expected_status from failure count ---
    failures = _count_baseline_failures(a)
    a["expected_status"] = "failure" if failures > 0 else "success"


def _baseline_assignments(
    obligation: CreateCollationFactorObligation,
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
        raise CreateCollationFactorLoopError(
            "duplicate baseline factor key"
        )
    return tuple(sorted(assignments.items()))


def _expected_failure_details(
    obligation: CreateCollationFactorObligation,
) -> tuple[str, str]:
    try:
        return _SFV_FAILURE_SQLSTATE[
            (obligation.factor_key, obligation.value)
        ]
    except KeyError as exc:
        raise CreateCollationFactorLoopError(
            "missing expected-failure SQLSTATE for "
            f"{obligation.factor_key}={obligation.value}"
        ) from exc


def build_create_collation_factor_loop_plan(
    repository_root: Path,
) -> CreateCollationFactorLoopPlan:
    """Assign one stable local SQL program to every obligation."""

    root = Path(repository_root).resolve(strict=True)
    obligations = compile_create_collation_factor_loop_obligations(root)
    cases: list[CreateCollationFactorCase] = []
    delegated: list[CreateCollationFactorObligation] = []
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
            CreateCollationFactorCase(
                ordinal=ordinal,
                case_id=f"CREATECOLLATION{ordinal:05d}",
                sql_filename=f"CREATECOLLATION{ordinal:05d}.sql",
                object_prefix=f"createcollation_{ordinal:05d}_",
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
    plan = CreateCollationFactorLoopPlan(
        obligations=obligations,
        cases=tuple(cases),
        delegated=tuple(delegated),
        obligation_multiset_sha256=_obligation_multiset_sha256(
            obligations
        ),
    )
    if len(plan.cases) != 55 or len(plan.delegated) != 0:
        raise CreateCollationFactorLoopError(
            "factor loop plan count drift"
        )
    if len({row.primary_obligation_id for row in plan.cases}) != 55:
        raise CreateCollationFactorLoopError(
            "local obligation mapping drift"
        )
    if len({row.sql_filename for row in plan.cases}) != 55:
        raise CreateCollationFactorLoopError("duplicate SQL filename")
    return plan


def compile_create_collation_factor_loop_obligations(
    repository_root: Path,
) -> tuple[CreateCollationFactorObligation, ...]:
    """Compile the exact marginal obligation ledger in frozen source order."""

    root = Path(repository_root).resolve(strict=True)
    unordered_rows = (
        _compile_grammar_obligations()
        + _compile_canonical_obligations(root)
    )
    rows = tuple(
        CreateCollationFactorObligation(
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
    if len(rows) != 55:
        raise CreateCollationFactorLoopError("obligation count drift")
    if len({row.obligation_id for row in rows}) != len(rows):
        raise CreateCollationFactorLoopError("duplicate obligation id")
    expected_kind_counts = {"GRM": 5, "SFV": 50}
    if Counter(row.kind for row in rows) != expected_kind_counts:
        raise CreateCollationFactorLoopError(
            "obligation kind count drift"
        )
    if sum(row.disposition == "delegated" for row in rows) != 0:
        raise CreateCollationFactorLoopError(
            "delegated obligation count drift"
        )
    if sum(
        row.disposition in {"covered", "expected_failure"}
        for row in rows
    ) != 55:
        raise CreateCollationFactorLoopError(
            "local obligation count drift"
        )
    allowed_dispositions = {"covered", "expected_failure", "delegated"}
    if any(
        row.disposition not in allowed_dispositions for row in rows
    ):
        raise CreateCollationFactorLoopError(
            "unknown obligation disposition"
        )
    return rows


__all__ = [
    "CreateCollationFactorLoopError",
    "CreateCollationGrammarAction",
    "CreateCollationFactorObligation",
    "CreateCollationFactorCase",
    "CreateCollationFactorLoopPlan",
    "_SFV_FAILURE_SQLSTATE",
    "_SFV_FAILURE_VALUES",
    "compile_create_collation_factor_loop_obligations",
    "build_create_collation_factor_loop_plan",
    "_obligation_multiset_sha256",
]
