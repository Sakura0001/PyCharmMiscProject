"""Render complete PostgreSQL 18.4 DROP POLICY factor-loop regress programs.

Every planned obligation becomes one self-contained, deterministic SQL file.  The
file is assembled from a single :func:`_resolve_case` plan so that the byte-level
witness validator (which re-renders and compares) can never diverge from the
bytes actually written.

The oracle queries are catalog-audit-compliant: a top-level
``SELECT count(*) <op> AS alias FROM pg_catalog.pg_policy ... ORDER BY count(*)``
never nests a ``FROM`` inside an ``EXISTS`` subquery, so
``audit_catalog_observability`` accepts it.

DROP POLICY operates on a row-level-security policy attached to a host table,
so the success fixture creates the host table (and one or two policies on it).
When a table is created the bookend gate requires the FIRST and LAST
``;``-statement to each be ``DROP TABLE IF EXISTS``; the pre-cleanup therefore
leads with the table drop and the final cleanup ends with it.  Table-less
cases (the host table is intentionally absent) create no table and are exempt
from the bookend.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re

from .cleanup_bookend import (
    OnDropSpec,
    build_cleanup,
    build_pre_cleanup,
)
from .drop_policy_factor_extension import (
    DropPolicyFactorExtensionCase,
)
from .drop_policy_factor_loop import (
    DropPolicyFactorCase,
    DropPolicyFactorLoopPlan,
)

_PRIMARY_BEGIN = "-- primary-target-begin"
_PRIMARY_END = "-- primary-target-end"

_DOC_SOURCE = (
    "skills/pg-sql-generation/references/statements/ddl/policy/"
    "drop_policy.md"
)
_FACTOR_SOURCE = (
    "skills/pg-sql-generation/references/combinations/ddl/policy/"
    "drop_policy.yaml"
)
_AUTHOR = "codex"
_CREATE_AT = "2026-08-20"
_VERSION = "1.0"
_FE = "PG18-STATEMENT-FACTOR-LOOP"

_BRANCH_1 = "branch_1"

# Baseline primaries where the target policy is intentionally absent, so the
# drop surfaces a not-found error (or a notice under IF EXISTS) and the oracle
# asserts absence.  These withhold the policy fixture.
_ABSENT_POLICY_PRIMARIES = frozenset(
    {
        ("expected_status", "failure"),
        ("object_state", "absent"),
        ("nonexistent_policy", "policy_missing_without_if_exists"),
        ("policy_name_shape", "nonexistent_name"),
    }
)

# Baseline primaries where the host table is intentionally absent, so the drop
# surfaces an undefined-table error and the oracle asserts absence.  These
# withhold the table fixture (and therefore the policy fixture too).
_ABSENT_TABLE_PRIMARIES = frozenset(
    {
        ("table_existence", "table_not_exists"),
        ("nonexistent_table", "table_missing"),
        ("table_name_shape", "nonexistent_table"),
    }
)

# For an extension SUCCESS case (no present failure pair) the synthetic
# primary must be a neutral success primary whose helpers fall through to the
# assignment; the policy always exists in extensions (object_state held at
# exists).
_BRANCH_NEUTRAL_SUCCESS = ("object_state", "exists")


def _synthetic_case(
    ext: DropPolicyFactorExtensionCase,
) -> DropPolicyFactorCase:
    """Build a byte-safe baseline-shaped case from an extension case."""

    from .drop_policy_factor_extension import _present_failure_pair

    assignment = dict(ext.factor_assignment)
    pair = _present_failure_pair(assignment)
    if pair is not None:
        factor_key, factor_value = pair
    else:
        factor_key, factor_value = _BRANCH_NEUTRAL_SUCCESS
    return DropPolicyFactorCase(
        ordinal=ext.ordinal,
        case_id=ext.case_id,
        sql_filename=ext.sql_filename,
        object_prefix=ext.object_prefix,
        primary_obligation_id=ext.derivation_id,
        kind="EXT",
        factor_key=factor_key,
        factor_value=factor_value,
        consumer_action_id=ext.consumer_action_id,
        outcome=ext.outcome,
        expected_sqlstate=ext.expected_sqlstate,
        expected_failure_reason=ext.expected_failure_reason,
        baseline_assignments=ext.factor_assignment,
        execution_profile="default",
    )


def _as_render_case(
    case: DropPolicyFactorCase | DropPolicyFactorExtensionCase,
) -> DropPolicyFactorCase:
    if isinstance(case, DropPolicyFactorExtensionCase):
        return _synthetic_case(case)
    return case


class DropPolicyFactorRenderError(ValueError):
    """Raised when a DROP POLICY case cannot be rendered."""


@dataclass(frozen=True)
class DropPolicyFactorWitness:
    primary_obligation_id: str
    target_sql_fragment: str
    outcome: str
    expected_sqlstate: str
    setup_sql: tuple[str, ...]
    oracle_sql: tuple[str, ...]
    cleanup_sql: tuple[str, ...]
    semantic_locus: str


@dataclass(frozen=True)
class _CasePlan:
    target_fragment: str
    setup_lines: tuple[str, ...]
    assert_lines: tuple[str, ...]
    pre_cleanup_lines: tuple[str, ...]
    cleanup_lines: tuple[str, ...]
    on_error_off: bool
    semantic_locus: str


def _baseline(case: DropPolicyFactorCase) -> dict[str, str]:
    return dict(case.baseline_assignments)


def _policy_name(case: DropPolicyFactorCase, a: dict[str, str], p: str) -> str:
    """The policy name as referenced inside DROP POLICY / CREATE POLICY."""

    shape = a.get("policy_name_shape", "simple_id")
    if shape == "quoted_id":
        return f'"{p}QuotedPol"'
    if shape == "nonexistent_name":
        return f"{p}nonexistent_pol"
    # simple_id and existing_name both use a plain prefixed id.
    return f"{p}pol"


def _policy_probe_name(case: DropPolicyFactorCase, a: dict[str, str], p: str) -> str:
    """The bare policy name (no quotes) for the catalog probe."""

    shape = a.get("policy_name_shape", "simple_id")
    if shape == "quoted_id":
        return f"{p}QuotedPol"
    if shape == "nonexistent_name":
        return f"{p}nonexistent_pol"
    return f"{p}pol"


def _secondary_policy_name(p: str) -> str:
    return f"{p}pol2"


def _table_ref(case: DropPolicyFactorCase, a: dict[str, str], p: str) -> str:
    """The table reference as used in the ON clause (may be quoted/qualified)."""

    shape = a.get("table_name_shape", "simple_id")
    if shape == "quoted_id":
        return f'"{p}t"'
    if shape == "schema_qualified":
        return f"public.{p}t"
    if shape == "nonexistent_table":
        return f"{p}nonexistent_tbl"
    return f"{p}t"


def _table_fixture_name(a: dict[str, str], p: str) -> str:
    """The plain unqualified table name used in CREATE/DROP TABLE fixtures.

    The shared style gate's identifier normalizer strips schema qualifiers and
    quotes, so the fixture is always a plain prefixed id; the quoted/schema
    form is kept byte-observable only in the DROP POLICY target.
    """

    return f"{p}t"


def _table_fixture_created(
    case: DropPolicyFactorCase, a: dict[str, str]
) -> bool:
    """Whether a host table fixture must be created."""

    if case.kind == "RISK":
        return True
    if (case.factor_key, case.factor_value) in _ABSENT_TABLE_PRIMARIES:
        return False
    if case.kind == "EXT":
        if a.get("table_existence") == "table_not_exists":
            return False
        if a.get("table_name_shape") == "nonexistent_table":
            return False
        return True
    return True


def _policy_fixture_created(
    case: DropPolicyFactorCase, a: dict[str, str]
) -> bool:
    """Whether a policy fixture must be created."""

    if not _table_fixture_created(case, a):
        return False
    if case.kind == "RISK":
        return True
    if (case.factor_key, case.factor_value) in _ABSENT_POLICY_PRIMARIES:
        return False
    if case.kind == "EXT":
        if a.get("object_state") == "absent":
            return False
        if a.get("policy_name_shape") == "nonexistent_name":
            return False
        return True
    return True


def _if_exists_present(
    case: DropPolicyFactorCase, a: dict[str, str]
) -> bool:
    return a.get("if_exists_clause") == "present"


def _cascade_clause(a: dict[str, str]) -> str:
    cascade = a.get("cascade_restrict", "omitted")
    if cascade == "cascade":
        return "CASCADE"
    if cascade == "restrict":
        return "RESTRICT"
    return ""  # omitted: RESTRICT is the default but the clause is absent


def _effective_role(
    case: DropPolicyFactorCase, a: dict[str, str], p: str
) -> str:
    """The session role under which the target DROP POLICY runs."""

    if case.kind == "EXT":
        level = a.get("privilege_level", "superuser")
        if level == "table_owner":
            return f"{p}owner"
        if level == "non_owner":
            return f"{p}actor"
        return ""
    if case.factor_key == "privilege_level":
        if case.factor_value == "table_owner":
            return f"{p}owner"
        if case.factor_value == "non_owner":
            return f"{p}actor"
        return ""
    return ""


def _policy_count(a: dict[str, str]) -> int:
    eff = a.get("last_policy_effect", "not_last_policy")
    if eff == "last_policy_remaining":
        return 1
    return 2  # not_last_policy and table_has_multiple_policies


def _rls_enabled(a: dict[str, str]) -> bool:
    return a.get("rls_state", "rls_enabled") == "rls_enabled"


def _policy_absent_after(
    case: DropPolicyFactorCase, a: dict[str, str]
) -> bool:
    """Whether the target policy is absent AFTER the target statement."""

    if case.kind == "RISK":
        return case.factor_value == "commit"
    if not _table_fixture_created(case, a):
        return True
    if not _policy_fixture_created(case, a):
        return True
    if case.outcome == "success":
        return True
    # expected_failure: drop did not succeed
    if a.get("privilege_level") == "non_owner":
        return False  # policy still present (drop denied)
    return True  # table/policy lookup failure -> policy absent


def _probe_select(
    case: DropPolicyFactorCase, a: dict[str, str], p: str
) -> str:
    pol = _policy_probe_name(case, a, p)
    table = _table_fixture_name(a, p)
    absent = _policy_absent_after(case, a)
    comparator = "= 0" if absent else "> 0"
    alias = "policy_absent" if absent else "policy_present"
    return (
        f"SELECT count(*) {comparator} AS {alias} "
        "FROM pg_catalog.pg_policy "
        f"WHERE polname = '{pol}' "
        f"AND polrelid = (SELECT oid FROM pg_catalog.pg_class "
        f"WHERE relname = '{table}') ORDER BY count(*) LIMIT 1;"
    )


def _role_names(
    case: DropPolicyFactorCase, p: str, effective: str
) -> tuple[str, ...]:
    roles: list[str] = []
    if effective == f"{p}owner":
        roles.append(f"{p}owner")
    elif effective == f"{p}actor":
        roles.append(f"{p}actor")
    return tuple(roles)


def _resolve_case(case: DropPolicyFactorCase) -> _CasePlan:
    a = _baseline(case)
    p = case.object_prefix
    table_created = _table_fixture_created(case, a)
    policy_created = _policy_fixture_created(case, a)
    pol_ref = _policy_name(case, a, p)
    table_ref = _table_ref(case, a, p)
    table_fix = _table_fixture_name(a, p)
    effective = _effective_role(case, a, p)
    pol_count = _policy_count(a)

    setup: list[str] = []
    locus = "target.policy"

    # A `;`-terminated boundary statement absorbs the preceding ``\set
    # ON_ERROR_STOP on`` meta-command so it does not merge with (and mask) the
    # fixture ``CREATE TABLE`` from ``audit_complete_table_script`` /
    # ``contains_create_table_statement``.  Emitted only when a host table is
    # created; table-less cases have no CREATE TABLE to mask.
    if table_created:
        setup.append("SELECT 1 AS setup_boundary;")

    # --- role fixtures (CREATE only; SET ROLE deferred to after the policy
    # fixture so they run as the superuser) ---
    if effective == f"{p}owner":
        setup.append(f"CREATE ROLE {p}owner LOGIN NOSUPERUSER;")
        locus = "fixture.privilege_state"
    elif effective == f"{p}actor":
        setup.append(f"CREATE ROLE {p}actor LOGIN NOSUPERUSER;")
        locus = "fixture.privilege_state"

    # --- the host table fixture (as superuser, before SET ROLE) -----------
    if table_created:
        setup.append(f"CREATE TABLE {table_fix} (c integer);")
        locus = "fixture.table_state"
        if _rls_enabled(a):
            setup.append(
                f"ALTER TABLE {table_fix} ENABLE ROW LEVEL SECURITY;"
            )
        else:
            setup.append(
                f"ALTER TABLE {table_fix} DISABLE ROW LEVEL SECURITY;"
            )
        # --- policy fixture(s) -------------------------------------------
        if policy_created:
            setup.append(
                f"CREATE POLICY {pol_ref} ON {table_fix} "
                "FOR SELECT USING (true);"
            )
            if pol_count > 1:
                setup.append(
                    f"CREATE POLICY {_secondary_policy_name(p)} ON {table_fix} "
                    "FOR SELECT USING (true);"
                )
            locus = "fixture.policy_state"
        else:
            setup.append(
                "SELECT 1 AS target_policy_intentionally_absent;"
            )
            locus = "fixture.object_state"
        # --- transfer ownership for the table_owner boundary --------------
        if effective == f"{p}owner":
            setup.append(f"ALTER TABLE {table_fix} OWNER TO {p}owner;")
    else:
        setup.append(
            "SELECT 1 AS target_host_table_intentionally_absent;"
        )
        locus = "fixture.table_state"

    # --- arm the non-superuser role (AFTER fixture creation) -------------
    if effective:
        setup.append(f"SET ROLE {effective};")
    if_exists = "IF EXISTS " if _if_exists_present(case, a) else ""
    cascade = _cascade_clause(a)
    target = f"DROP POLICY {if_exists}{pol_ref} ON {table_ref}"
    if cascade:
        target += f" {cascade}"
    target += ";"

    # RISK transaction wrapper around the target.
    if case.kind == "RISK":
        setup.append("BEGIN;")
        locus = "target.transaction_boundary"

    # --- oracle / SQLSTATE assertion ------------------------------------
    assert_lines: list[str] = []
    if effective:
        assert_lines.append("RESET ROLE;")
    if case.kind == "RISK":
        assert_lines.append(
            "COMMIT;" if case.factor_value == "commit" else "ROLLBACK;"
        )
    assert_lines.append(
        f"SELECT :'target_sqlstate' = '{case.expected_sqlstate}' "
        "AS target_sqlstate_matches_expected;"
    )
    assert_lines.append(_probe_select(case, a, p))

    # --- cleanup construction (idempotent bookends via cleanup_bookend) ---
    # The POLICY drops are shape A (ON <table>) and go through complex_specs.
    # They are routed to build_cleanup only: in pre_cleanup the table is
    # dropped first (CASCADE removes the policies), so a later DROP POLICY ON
    # <table> would error on the missing relation.  IF EXISTS on the policy
    # does not suppress a missing-table error, so policies stay out of
    # pre_cleanup.  The table_created gate is the structural-absence
    # exception (Q3): when the container table is never created, DROP POLICY
    # ON <missing-relation> errors regardless of IF EXISTS.
    complex_specs: tuple[OnDropSpec, ...] = ()
    if table_created:
        complex_specs = (
            OnDropSpec("POLICY", pol_ref, table_fix),
            OnDropSpec("POLICY", _secondary_policy_name(p), table_fix),
        )
    roles = _role_names(case, p, effective)
    tables = (table_fix,) if table_created else ()

    pre_cleanup_bk = build_pre_cleanup(
        tables=tables,
        roles=tuple(roles),
    )
    cleanup_bk = build_cleanup(
        tables=tables,
        complex_specs=complex_specs,
        roles=tuple(roles),
        drop_owned=bool(roles),
        reset_role=effective,
    )
    pre_cleanup = list(pre_cleanup_bk.statements)
    cleanup = list(cleanup_bk.statements)

    on_error_off = case.outcome == "expected_failure"
    return _CasePlan(
        target_fragment=target,
        setup_lines=tuple(setup),
        assert_lines=tuple(assert_lines),
        pre_cleanup_lines=tuple(pre_cleanup),
        cleanup_lines=tuple(cleanup),
        on_error_off=on_error_off,
        semantic_locus=locus,
    )


def resolve_drop_policy_factor_witness(
    case: DropPolicyFactorCase | DropPolicyFactorExtensionCase,
    repository_root: Path,
) -> DropPolicyFactorWitness:
    """Return the byte-level witness fragments for one case."""

    rc = _as_render_case(case)
    plan = _resolve_case(rc)
    return DropPolicyFactorWitness(
        primary_obligation_id=rc.primary_obligation_id,
        target_sql_fragment=plan.target_fragment,
        outcome=rc.outcome,
        expected_sqlstate=rc.expected_sqlstate,
        setup_sql=plan.setup_lines,
        oracle_sql=plan.assert_lines,
        cleanup_sql=plan.cleanup_lines,
        semantic_locus=plan.semantic_locus,
    )


def count_primary_drop_policy(sql: str) -> int:
    """Count the single credited DROP POLICY inside the primary fence."""

    if sql.count(_PRIMARY_BEGIN) != 1 or sql.count(_PRIMARY_END) != 1:
        return 0
    before_end, _ = sql.split(_PRIMARY_END, 1)
    if _PRIMARY_BEGIN not in before_end:
        return 0
    region = before_end.split(_PRIMARY_BEGIN, 1)[1]
    return len(
        re.findall(r"(?im)^\s*DROP\s+POLICY\b", region)
    )


def _header(case: DropPolicyFactorCase) -> list[str]:
    return [
        "-- --------------------------------------------------------",
        "-- 版权所有(C)  2021-2030 华为技术有限公司",
        "--",
        "-- --",
        f"-- author       : {_AUTHOR}",
        f"-- create at    : {_CREATE_AT}",
        f"-- version      : {_VERSION}",
        f"-- description  : DROP POLICY {case.factor_key}={case.factor_value}",
        f"-- FE           : {_FE}",
        "-- ++",
        "-- --------------------------------------------------------",
        f"-- case_id: {case.case_id}",
        f"-- source_md: {_DOC_SOURCE}",
        f"-- factor_md: {_FACTOR_SOURCE}",
        f"-- primary_obligation_id: {case.primary_obligation_id}",
        f"-- expected_outcome: {case.outcome}",
        f"-- expected_sqlstate: {case.expected_sqlstate}",
    ]


def render_drop_policy_factor_case(
    case: DropPolicyFactorCase | DropPolicyFactorExtensionCase,
    repository_root: Path,
) -> str:
    """Render one complete, deterministic DROP POLICY regress program."""

    rc = _as_render_case(case)
    resolved = _resolve_case(rc)
    lines: list[str] = list(_header(rc))
    lines.append("-- 1. 清理本编号对象，保证脚本可重复执行。")
    lines.extend(resolved.pre_cleanup_lines)
    lines.append("\\set ON_ERROR_STOP on")
    lines.append("-- 2. 创建完整本地行级安全策略和因子专用夹具。")
    lines.extend(resolved.setup_lines)
    if resolved.on_error_off:
        lines.append("\\set ON_ERROR_STOP off")
    lines.append("-- 3. 执行唯一获得覆盖信用的 DROP POLICY。")
    lines.append(_PRIMARY_BEGIN)
    lines.append(resolved.target_fragment)
    lines.append(_PRIMARY_END)
    lines.append("\\set target_sqlstate :SQLSTATE")
    lines.append("\\echo PGCF_TARGET_SQLSTATE=:target_sqlstate")
    if resolved.on_error_off:
        lines.append("\\set ON_ERROR_STOP on")
    lines.append("-- 4. 验证 SQLSTATE、目录状态和数据行为。")
    lines.extend(resolved.assert_lines)
    lines.append("-- 5. 清理全部本编号对象。")
    lines.extend(resolved.cleanup_lines)
    text = "\n".join(lines)
    if not text.endswith(";"):
        text += ";"
    return text + "\n"


def generate_drop_policy_factor_programs(
    baseline_plan: DropPolicyFactorLoopPlan,
    extension_plan: object,
    out_dir: Path,
) -> int:
    """Write every baseline + extension program; return the file count."""

    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    count = 0
    for case in baseline_plan.cases:
        _write_program(case, out)
        count += 1
    for case in extension_plan.cases:
        _write_program(case, out)
        count += 1
    return count


def _write_program(
    case: DropPolicyFactorCase | DropPolicyFactorExtensionCase,
    out: Path,
) -> None:
    text = render_drop_policy_factor_case(case, Path("."))
    rc = _as_render_case(case)
    (out / rc.sql_filename).write_text(text, encoding="utf-8")


__all__ = [
    "DropPolicyFactorRenderError",
    "DropPolicyFactorWitness",
    "count_primary_drop_policy",
    "generate_drop_policy_factor_programs",
    "render_drop_policy_factor_case",
    "resolve_drop_policy_factor_witness",
]
