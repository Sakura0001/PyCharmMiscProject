"""Render complete PostgreSQL 18.4 ALTER GROUP factor regress programs.

Every planned case -- whether a frozen baseline obligation
(:class:`AlterGroupFactorCase`) or a bounded post-coverage extension
(:class:`AlterGroupFactorExtensionCase`) -- becomes one self-contained,
deterministic SQL file assembled from a single :func:`_resolve_case` plan.
The byte-level witness validator (which re-renders and compares) can never
diverge from the bytes actually written.

The 5-phase byte contract mirrors :mod:`alter_function_factor_render`
exactly: (1) idempotent pre-clean superset; ``\\set ON_ERROR_STOP on``;
(2) role fixture setup; [``\\set ON_ERROR_STOP off`` when expected_failure];
(3) the single credited ``ALTER GROUP`` wrapped in
``-- primary-target-begin`` / ``-- primary-target-end``;
``\\set target_sqlstate :SQLSTATE`` / ``\\echo PGCF_TARGET_SQLSTATE=...``;
[``\\set ON_ERROR_STOP on``]; (4) oracle/assert; (5) unconditional cleanup.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re

from .alter_group_factor_extension import AlterGroupFactorExtensionCase
from .alter_group_factor_loop import AlterGroupFactorCase


_PRIMARY_BEGIN = "-- primary-target-begin"
_PRIMARY_END = "-- primary-target-end"

_DOC_SOURCE = (
    "skills/pg-sql-generation/references/statements/ddl/group/"
    "alter_group.md"
)
_FACTOR_SOURCE = (
    "skills/pg-sql-generation/references/combinations/ddl/group/"
    "alter_group.yaml"
)
_AUTHOR = "codex"
_CREATE_AT = "2026-08-19"
_VERSION = "1.0"
_FE = "PG18-STATEMENT-FACTOR-LOOP"


class AlterGroupFactorRenderError(ValueError):
    """Raised when an ALTER GROUP case cannot be rendered."""


@dataclass(frozen=True)
class AlterGroupFactorWitness:
    primary_obligation_id: str
    target_sql_fragment: str
    outcome: str
    expected_sqlstate: str
    setup_sql: tuple[str, ...]
    oracle_sql: tuple[str, ...]
    cleanup_sql: tuple[str, ...]
    semantic_locus: str


@dataclass(frozen=True)
class AlterGroupRenderCase:
    """Adapter normalising baseline + extension cases for the renderer."""

    case_id: str
    sql_filename: str
    object_prefix: str
    primary_identifier: str
    description: str
    consumer_action_id: str
    outcome: str
    expected_sqlstate: str
    expected_failure_reason: str | None
    assignment: tuple[tuple[str, str], ...]
    is_extension: bool

    @classmethod
    def from_case(cls, case: object) -> "AlterGroupRenderCase":
        if isinstance(case, AlterGroupFactorCase):
            assignment = case.baseline_assignments
            primary = case.primary_obligation_id
            desc = f"{case.factor_key}={case.factor_value}"
            is_ext = False
        elif isinstance(case, AlterGroupFactorExtensionCase):
            assignment = case.factor_assignment
            primary = case.derivation_id
            desc = case.derivation_reason
            is_ext = True
        else:  # pragma: no cover - defensive
            raise AlterGroupFactorRenderError(
                f"unknown case type: {type(case).__name__}"
            )
        return cls(
            case_id=case.case_id,
            sql_filename=case.sql_filename,
            object_prefix=case.object_prefix,
            primary_identifier=primary,
            description=desc,
            consumer_action_id=case.consumer_action_id,
            outcome=case.outcome,
            expected_sqlstate=case.expected_sqlstate,
            expected_failure_reason=case.expected_failure_reason,
            assignment=assignment,
            is_extension=is_ext,
        )


@dataclass(frozen=True)
class _CasePlan:
    target_fragment: str
    setup_lines: tuple[str, ...]
    assert_lines: tuple[str, ...]
    pre_cleanup_lines: tuple[str, ...]
    cleanup_lines: tuple[str, ...]
    on_error_off: bool
    semantic_locus: str


def _a(rc: AlterGroupRenderCase) -> dict[str, str]:
    return dict(rc.assignment)


def _group_role_name(p: str, shape: str) -> str:
    """The group role literal; quoted_id uses a quoted mixed-case form."""

    if shape == "quoted_id":
        return f'"{p}Grp"'
    if shape == "nonexistent_name":
        return f"{p}missing_grp"
    return f"{p}grp"


def _user_role_name(p: str, shape: str, idx: int = 1) -> str:
    """The user role literal for ADD/DROP USER."""

    suffix = "usr" if idx == 1 else f"usr{idx}"
    if shape == "quoted_id":
        return f'"{p}{suffix.capitalize()}"'
    if shape == "nonexistent_user":
        return f"{p}missing_{suffix}"
    return f"{p}{suffix}"


def _new_name_literal(p: str, shape: str) -> str:
    """The RENAME TO target literal."""

    if shape == "quoted_id":
        return f'"{p}Renamed"'
    return f"{p}renamed"


def _group_exists(a: dict[str, str]) -> bool:
    return (
        a["object_state"] == "exists"
        and a["group_name_shape"] != "nonexistent_name"
        and a["nonexistent_group"] != "group_missing"
    )


def _user_exists(a: dict[str, str]) -> bool:
    return (
        a["user_existence"] == "user_exists"
        and a["user_name_shape"] != "nonexistent_user"
        and a["nonexistent_user"] != "user_missing"
    )


def _effective_role(a: dict[str, str], p: str) -> str:
    """The session role under which the target ALTER GROUP runs."""

    level = a["privilege_level"]
    if level == "non_admin":
        return f"{p}actor"
    if level == "group_role_admin":
        return f"{p}admin"
    return ""  # superuser: run as pgcf_superuser


def _role_set(rc: AlterGroupRenderCase, a: dict[str, str], p: str) -> tuple[str, ...]:
    """Every role literal this case may touch, for idempotent DROP ROLE."""

    roles: list[str] = []
    action = rc.consumer_action_id
    if action in ("add_user", "drop_user"):
        roles.append(_group_role_name(p, a["group_name_shape"]))
        shape = a["user_name_shape"]
        if a["multi_user"] == "multiple_users":
            roles.append(_user_role_name(p, shape, 1))
            roles.append(_user_role_name(p, shape, 2))
        else:
            roles.append(_user_role_name(p, shape, 1))
    else:  # rename
        roles.append(_group_role_name(p, a["group_name_shape"]))
        if a["new_name_shape"] == "duplicate_name":
            roles.append(f"{p}dup_grp")
        if a["rename_to_existing_name"] == "same_name_conflict":
            roles.append(f"{p}conflict_grp")
        roles.append(_new_name_literal(p, a["new_name_shape"]))
    eff = _effective_role(a, p)
    if eff:
        roles.append(eff)
    # de-duplicate preserving order
    seen: set[str] = set()
    unique: list[str] = []
    for role in roles:
        if role not in seen:
            seen.add(role)
            unique.append(role)
    return tuple(unique)


def _setup_fixture(
    rc: AlterGroupRenderCase,
    a: dict[str, str],
    p: str,
) -> tuple[tuple[str, ...], str]:
    """Build the role fixture; return (setup_lines, semantic_locus)."""

    lines: list[str] = []
    action = rc.consumer_action_id
    locus = "target.group_membership"
    grp_shape = a["group_name_shape"]
    grp = _group_role_name(p, grp_shape)
    grp_present = _group_exists(a)
    eff = _effective_role(a, p)
    # group role
    if grp_present:
        lines.append(f"CREATE ROLE {grp};")
    # user roles (add/drop)
    created_users: list[str] = []
    if action in ("add_user", "drop_user"):
        shape = a["user_name_shape"]
        if a["multi_user"] == "multiple_users":
            for idx in (1, 2):
                uname = _user_role_name(p, shape, idx)
                created_users.append(uname)
        else:
            created_users.append(_user_role_name(p, shape, 1))
        if _user_exists(a):
            for uname in created_users:
                lines.append(f"CREATE ROLE {uname};")
    # rename duplicate/conflict target role (pre-create to surface 42710)
    if action == "rename":
        if a["new_name_shape"] == "duplicate_name":
            lines.append(f"CREATE ROLE {p}dup_grp;")
        if a["rename_to_existing_name"] == "same_name_conflict":
            lines.append(f"CREATE ROLE {p}conflict_grp;")
    # pre-grant add_user existing_member as superuser (before any SET ROLE).
    # The idempotent ADD USER of an already-member is grantor-agnostic, so a
    # superuser grant is correct for every effective role.
    if grp_present and action == "add_user" and a["duplicate_add_user"] == "existing_member":
        for uname in created_users:
            if _user_exists(a):
                lines.append(f"GRANT {grp} TO {uname};")
    # drop_user existing_member pre-grant; deferred until the privilege fixture
    # establishes the grantor context (see the admin/actor branches below).
    drop_pre_grant: list[str] = []
    if grp_present and action == "drop_user" and a["drop_non_member_user"] == "existing_member":
        for uname in created_users:
            if _user_exists(a):
                drop_pre_grant.append(f"GRANT {grp} TO {uname};")
    # For non-admin effective roles the superuser-granted membership is correct:
    # the actor (no ADMIN OPTION) target is denied 42501 and the membership
    # survives regardless of grantor; the superuser primary can revoke anything.
    # Emit those grants now, before any SET ROLE.
    if eff != f"{p}admin":
        lines.extend(drop_pre_grant)
    # privilege fixture
    if eff == f"{p}admin":
        lines.append(f"CREATE ROLE {p}admin LOGIN;")
        if grp_present:
            lines.append(f"GRANT {grp} TO {p}admin WITH ADMIN OPTION;")
        if action == "rename":
            # ALTER GROUP ... RENAME ~= ALTER ROLE ... RENAME, which needs
            # CREATEROLE; group-admin option alone yields 42501.  Grant it
            # so the rename reaches its true outcome (00000 or 42710 when
            # the target name already exists, which fires first).
            lines.append(f"ALTER ROLE {p}admin CREATEROLE;")
        lines.append(f"SET ROLE {p}admin;")
        locus = "fixture.privilege_state"
        # The admin holds ADMIN OPTION; grant the membership AFTER SET ROLE so
        # the admin is the grantor and can later revoke (drop) its own grant.
        # A superuser-granted membership cannot be revoked by a non-superuser
        # admin (PG emits a no-op WARNING 01000 and the membership survives).
        lines.extend(drop_pre_grant)
    elif eff == f"{p}actor":
        lines.append(f"CREATE ROLE {p}actor LOGIN;")
        lines.append(f"SET ROLE {p}actor;")
        locus = "fixture.privilege_state"
    return tuple(lines), locus


def _user_list(a: dict[str, str], p: str) -> str:
    shape = a["user_name_shape"]
    if a["multi_user"] == "multiple_users":
        return (
            f"{_user_role_name(p, shape, 1)}, {_user_role_name(p, shape, 2)}"
        )
    return _user_role_name(p, shape, 1)


def _rename_target(a: dict[str, str], p: str) -> str:
    if a["new_name_shape"] == "duplicate_name":
        return f"{p}dup_grp"
    if a["rename_to_existing_name"] == "same_name_conflict":
        return f"{p}conflict_grp"
    return _new_name_literal(p, a["new_name_shape"])


def _target_fragment(
    rc: AlterGroupRenderCase,
    a: dict[str, str],
    p: str,
) -> str:
    grp = _group_role_name(p, a["group_name_shape"])
    action = rc.consumer_action_id
    if action == "add_user":
        return f"ALTER GROUP {grp} ADD USER {_user_list(a, p)};"
    if action == "drop_user":
        return f"ALTER GROUP {grp} DROP USER {_user_list(a, p)};"
    return f"ALTER GROUP {grp} RENAME TO {_rename_target(a, p)};"


def _verification_target_name(
    rc: AlterGroupRenderCase,
    a: dict[str, str],
    p: str,
) -> str:
    """The role name the oracle probes (stripped of quotes for catalog match)."""

    if rc.consumer_action_id == "rename" and rc.outcome == "success":
        return _rename_target(a, p).strip('"')
    return _group_role_name(p, a["group_name_shape"]).strip('"')


def _oracle(
    rc: AlterGroupRenderCase,
    a: dict[str, str],
    p: str,
) -> tuple[str, ...]:
    lines: list[str] = [
        f"SELECT :'target_sqlstate' = '{rc.expected_sqlstate}' "
        "AS target_sqlstate_matches_expected;"
    ]
    mode = a["verification_mode"]
    action = rc.consumer_action_id
    if action == "rename":
        new_target = _rename_target(a, p).strip('"')
        if mode == "pg_authid_catalog":
            lines.append(
                "SELECT rolname FROM pg_catalog.pg_authid "
                f"WHERE rolname = '{new_target}' ORDER BY oid;"
            )
        elif mode == "error_assertion":
            lines.append("SELECT :'target_sqlstate' AS asserted_sqlstate;")
        else:
            original = _group_role_name(p, a["group_name_shape"]).strip('"')
            if rc.outcome == "success":
                lines.append(
                    "SELECT EXISTS(SELECT 1 FROM pg_catalog.pg_roles "
                    f"WHERE rolname = '{new_target}') AS rename_target_exists;"
                )
            elif _group_exists(a):
                lines.append(
                    "SELECT EXISTS(SELECT 1 FROM pg_catalog.pg_roles "
                    f"WHERE rolname = '{original}') AS rename_source_exists;"
                )
            else:
                lines.append(
                    "SELECT NOT EXISTS(SELECT 1 FROM pg_catalog.pg_roles "
                    f"WHERE rolname = '{original}') AS rename_source_absent;"
                )
        return tuple(lines)
    grp = _group_role_name(p, a["group_name_shape"]).strip('"')
    usr = _user_role_name(p, a["user_name_shape"], 1).strip('"')
    if mode == "pg_authid_catalog":
        lines.append(
            "SELECT rolname FROM pg_catalog.pg_authid "
            f"WHERE rolname = '{grp}' ORDER BY oid;"
        )
    elif mode == "error_assertion":
        lines.append("SELECT :'target_sqlstate' AS asserted_sqlstate;")
    else:
        # Assert the expected post-target membership state.  The membership is
        # structurally absent unless both the group and the user exist.  On
        # success: add_user -> present, drop_user -> absent.  On failure the
        # target is a no-op, so the pre-target membership state survives:
        # existing_member (pre-granted) -> present, else -> absent.
        if not (_group_exists(a) and _user_exists(a)):
            expect_member = False
        elif rc.outcome == "success":
            expect_member = action == "add_user"
        elif action == "add_user":
            expect_member = a["duplicate_add_user"] == "existing_member"
        else:  # drop_user expected_failure
            expect_member = a["drop_non_member_user"] == "existing_member"
        membership = (
            "SELECT 1 FROM pg_catalog.pg_auth_members m "
            "JOIN pg_catalog.pg_roles g ON g.oid = m.roleid "
            "JOIN pg_catalog.pg_roles u ON u.oid = m.member "
            f"WHERE g.rolname = '{grp}' AND u.rolname = '{usr}'"
        )
        if expect_member:
            lines.append("SELECT EXISTS(" + membership + ") AS membership_present;")
        else:
            lines.append(
                "SELECT NOT EXISTS(" + membership + ") AS membership_absent;"
            )
    return tuple(lines)


def _labeled_cleanup(
    rc: AlterGroupRenderCase,
    a: dict[str, str],
    p: str,
) -> tuple[str, ...]:
    """The cleanup_mode-driven teardown step, only when provably safe."""

    mode = a["cleanup_mode"]
    action = rc.consumer_action_id
    if action == "rename":
        if mode == "revert_rename" and rc.outcome == "success":
            grp = _group_role_name(p, a["group_name_shape"])
            new = _rename_target(a, p)
            return (f"ALTER GROUP {new} RENAME TO {grp};",)
        return ()
    # add/drop: the labeled step is safe only when both grp and usr exist
    if not (_group_exists(a) and _user_exists(a)):
        return ()
    grp = _group_role_name(p, a["group_name_shape"])
    usr = _user_role_name(p, a["user_name_shape"], 1)
    if mode == "revoke_membership":
        return (f"ALTER GROUP {grp} DROP USER {usr};",)
    if mode == "grant_membership":
        return (f"ALTER GROUP {grp} ADD USER {usr};",)
    return ()


def _resolve_case(rc: AlterGroupRenderCase) -> _CasePlan:
    a = _a(rc)
    p = rc.object_prefix
    setup, locus = _setup_fixture(rc, a, p)
    target = _target_fragment(rc, a, p)
    eff = _effective_role(a, p)
    assert_lines = _oracle(rc, a, p)
    # The oracle verifies catalog state from a privileged vantage: the
    # executor's privilege was already exercised by the target.  RESET ROLE
    # before the oracle so pg_authid (not publicly readable by a non-superuser)
    # and every catalog probe succeed as superuser.
    if eff:
        assert_lines = ("RESET ROLE;",) + assert_lines
    roles = _role_set(rc, a, p)
    pre_clean = tuple(
        f"DROP ROLE IF EXISTS {role};" for role in roles
    ) or ("SELECT 1 AS residual_check_no_objects;",)
    cleanup: list[str] = []
    if eff:
        cleanup.append("RESET ROLE;")
    cleanup.extend(_labeled_cleanup(rc, a, p))
    cleanup.extend(f"DROP ROLE IF EXISTS {role};" for role in roles)
    on_error_off = rc.outcome == "expected_failure"
    return _CasePlan(
        target_fragment=target,
        setup_lines=setup,
        assert_lines=assert_lines,
        pre_cleanup_lines=pre_clean,
        cleanup_lines=tuple(cleanup) or ("SELECT 1 AS residual_check_no_objects;",),
        on_error_off=on_error_off,
        semantic_locus=locus,
    )


def _to_render_case(case: object) -> AlterGroupRenderCase:
    return AlterGroupRenderCase.from_case(case)


def resolve_alter_group_factor_witness(
    case: object,
    repository_root: Path,
) -> AlterGroupFactorWitness:
    """Return the byte-level witness fragments for one case."""

    rc = _to_render_case(case)
    plan = _resolve_case(rc)
    return AlterGroupFactorWitness(
        primary_obligation_id=rc.primary_identifier,
        target_sql_fragment=plan.target_fragment,
        outcome=rc.outcome,
        expected_sqlstate=rc.expected_sqlstate,
        setup_sql=plan.setup_lines,
        oracle_sql=plan.assert_lines,
        cleanup_sql=plan.cleanup_lines,
        semantic_locus=plan.semantic_locus,
    )


def count_primary_alter_group(sql: str) -> int:
    """Count the single credited ALTER GROUP inside the primary fence."""

    if sql.count(_PRIMARY_BEGIN) != 1 or sql.count(_PRIMARY_END) != 1:
        return 0
    before_end, _ = sql.split(_PRIMARY_END, 1)
    if _PRIMARY_BEGIN not in before_end:
        return 0
    region = before_end.split(_PRIMARY_BEGIN, 1)[1]
    return len(re.findall(r"(?im)^\s*ALTER\s+GROUP\b", region))


def _header(rc: AlterGroupRenderCase) -> list[str]:
    return [
        "-- --------------------------------------------------------",
        "-- 版权所有(C)  2021-2030 华为技术有限公司",
        "--",
        "-- --",
        f"-- author       : {_AUTHOR}",
        f"-- create at    : {_CREATE_AT}",
        f"-- version      : {_VERSION}",
        f"-- description  : ALTER GROUP {rc.description}",
        f"-- FE           : {_FE}",
        "-- ++",
        "-- --------------------------------------------------------",
        f"-- case_id: {rc.case_id}",
        f"-- source_md: {_DOC_SOURCE}",
        f"-- factor_md: {_FACTOR_SOURCE}",
        f"-- primary_obligation_id: {rc.primary_identifier}",
        f"-- expected_outcome: {rc.outcome}",
        f"-- expected_sqlstate: {rc.expected_sqlstate}",
    ]


def render_alter_group_factor_case(case: object, repository_root: Path) -> str:
    """Render one complete, deterministic ALTER GROUP regress program."""

    rc = _to_render_case(case)
    resolved = _resolve_case(rc)
    lines: list[str] = list(_header(rc))
    lines.append("-- 1. 清理本编号对象，保证脚本可重复执行。")
    lines.extend(resolved.pre_cleanup_lines)
    lines.append("\\set ON_ERROR_STOP on")
    lines.append("-- 2. 创建完整本地角色和因子专用夹具。")
    lines.extend(resolved.setup_lines)
    if resolved.on_error_off:
        lines.append("\\set ON_ERROR_STOP off")
    lines.append("-- 3. 执行唯一获得覆盖信用的 ALTER GROUP。")
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


def generate_alter_group_factor_programs(
    baseline_plan: object,
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


def _write_program(case: object, out: Path) -> None:
    rc = _to_render_case(case)
    text = render_alter_group_factor_case(case, Path("."))
    (out / rc.sql_filename).write_text(text, encoding="utf-8")


__all__ = [
    "AlterGroupFactorRenderError",
    "AlterGroupFactorWitness",
    "AlterGroupRenderCase",
    "count_primary_alter_group",
    "generate_alter_group_factor_programs",
    "render_alter_group_factor_case",
    "resolve_alter_group_factor_witness",
]
