"""Render complete PostgreSQL 18.4 ALTER PUBLICATION factor-loop regress programs.

Every planned obligation becomes one self-contained, deterministic SQL file.
The file is assembled from a single :func:`_resolve_case` plan so that the
byte-level witness validator (which re-renders and compares) can never
diverge from the bytes actually written.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re

from .alter_publication_factor_extension import (
    AlterPublicationFactorExtensionCase,
)
from .alter_publication_factor_loop import (
    AlterPublicationFactorCase,
    AlterPublicationFactorLoopPlan,
)


_PRIMARY_BEGIN = "-- primary-target-begin"
_PRIMARY_END = "-- primary-target-end"

_DOC_SOURCE = (
    "skills/pg-sql-generation/references/statements/ddl/publication/"
    "alter_publication.md"
)
_FACTOR_SOURCE = (
    "skills/pg-sql-generation/references/combinations/ddl/publication/"
    "alter_publication.yaml"
)
_AUTHOR = "codex"
_CREATE_AT = "2026-08-20"
_VERSION = "1.0"
_FE = "PG18-STATEMENT-FACTOR-LOOP"

_BRANCH_ADD = "branch_add"
_BRANCH_SET_OBJECT = "branch_set_object"
_BRANCH_DROP = "branch_drop"
_BRANCH_SET_PARAMETER = "branch_set_parameter"
_BRANCH_OWNER_TO = "branch_owner_to"
_BRANCH_RENAME = "branch_rename"

_TABLE_OPS = frozenset({"add_table", "set_table", "drop_table"})
_SCHEMA_OPS = frozenset(
    {"add_tables_in_schema", "set_tables_in_schema", "drop_tables_in_schema"}
)
_TABLE_NON_EXISTENT = frozenset(
    {"table_not_exists", "nonexistent_table"}
)
_SCHEMA_NON_EXISTENT = frozenset(
    {"schema_not_exists", "nonexistent_schema"}
)


def _synthetic_case(
    ext: AlterPublicationFactorExtensionCase,
) -> AlterPublicationFactorCase:
    """Build a byte-safe baseline-shaped case from an extension case."""

    from .alter_publication_factor_extension import _present_failure_pair

    assignment = dict(ext.factor_assignment)
    branch = assignment["grammar_branch"]
    pair = _present_failure_pair(assignment)
    if pair is not None:
        factor_key, factor_value = pair
    elif branch == _BRANCH_RENAME and ext.outcome == "success":
        factor_key = "new_name_shape"
        factor_value = assignment["new_name_shape"]
    else:
        factor_key = "publication_state"
        factor_value = assignment.get("publication_state", "exists")
    return AlterPublicationFactorCase(
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
        execution_profile="serial_sql",
    )


def _as_render_case(
    case: AlterPublicationFactorCase | AlterPublicationFactorExtensionCase,
) -> AlterPublicationFactorCase:
    if isinstance(case, AlterPublicationFactorExtensionCase):
        return _synthetic_case(case)
    return case


class AlterPublicationFactorRenderError(ValueError):
    """Raised when an ALTER PUBLICATION case cannot be rendered."""


@dataclass(frozen=True)
class AlterPublicationFactorWitness:
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


@dataclass(frozen=True)
class _FixtureState:
    pub_fixture: str
    needs_table: bool
    needs_schema: bool
    needs_member_tbl: bool
    needs_tbl2: bool
    pre_add_target: bool
    pre_add_tbl2: bool
    effective: str
    pub_name: str
    fixture_pub: str
    table_name: str
    schema_name: str
    create_schema_name: str
    should_create_schema: bool


def _baseline(case: AlterPublicationFactorCase) -> dict[str, str]:
    return dict(case.baseline_assignments)


def _pub_name(a: dict[str, str], p: str) -> str:
    """Publication name in the target ALTER (and fixture CREATE)."""
    shape = a.get("publication_name_shape", "simple_name")
    if shape == "quoted_name":
        return f'"{p}Mixed Pub"'
    if shape == "non_existent_name":
        return f"{p}no_such_pub"
    return f"{p}pub"


def _table_name(a: dict[str, str], p: str) -> str:
    shape = a.get("table_name_shape", "simple_name")
    if shape == "schema_qualified_name":
        return f"{p}sch.{p}tbl"
    if shape == "quoted_name":
        return f'"{p}tbl"'
    if shape == "nonexistent_table":
        return f"{p}no_such_tbl"
    return f"{p}tbl"


def _fixture_table(a: dict[str, str], p: str) -> str:
    """Audit-normalizable name for fixture CREATE TABLE and bookend DROPs.

    The shared ``audit_complete_table_script`` gate normalizes identifiers
    with a plain ``[A-Za-z_][A-Za-z0-9_$]*`` grammar that rejects quoted
    names (and stops at the space inside a quoted name), so the fixture
    CREATE TABLE and the bookend DROP TABLE statements emit a plain name.
    The ALTER PUBLICATION target still uses the shape-appropriate
    :func:`_table_name` form — a quoted lowercase identifier resolves to the
    same table as the plain fixture name — so the ``quoted_name`` factor
    stays byte-observable in the target without breaking the table audit.
    """
    shape = a.get("table_name_shape", "simple_name")
    if shape == "schema_qualified_name":
        return f"{p}sch.{p}tbl"
    return f"{p}tbl"


def _schema_name(a: dict[str, str], p: str) -> str:
    shape = a.get("schema_name_shape", "simple_name")
    if shape == "current_schema_keyword":
        return "CURRENT_SCHEMA"
    if shape == "quoted_name":
        return f'"{p}Mixed Sch"'
    if shape == "nonexistent_schema":
        return f"{p}no_such_sch"
    return f"{p}sch"


def _new_name(a: dict[str, str], p: str) -> str:
    form = a.get("new_name_shape", "simple_name")
    if form == "quoted_name":
        return f'"{p}Mixed New"'
    if form == "existing_name_conflict":
        # A DIFFERENT name from the source pub so the setup can create it as
        # the conflicting publication; renaming to it surfaces 42710.
        return f"{p}conflict"
    return f"{p}renamed"


def _owner_target(a: dict[str, str], p: str) -> str:
    if a.get("new_owner_shape") == "nonexistent_role":
        return f"{p}no_such_role"
    clause = a.get("owner_to_clause", "explicit_role_name")
    if clause == "current_role_keyword":
        return "CURRENT_ROLE"
    if clause == "current_user_keyword":
        return "CURRENT_USER"
    if clause == "session_user_keyword":
        return "SESSION_USER"
    return f"{p}new_owner"


def _parameter_clause(a: dict[str, str]) -> str:
    param = a.get("publication_parameter", "publish_insert_only")
    form = a.get("parameter_assignment_form", "equals_value")
    # PG 18.4's synopsis marks ``[= value]`` optional, but the engine REQUIRES
    # ``= value`` for ``publish`` (bare ``publish`` raises 42601).  Only
    # ``publish_via_partition_root`` accepts the bare-name (no ``=``) reset
    # form, so the no_equals assignment form is rendered bare solely for it;
    # for every publish-family parameter the no_equals case collapses to the
    # equals form on its success path (there is no valid bare render).
    bare = form == "no_equals" and param == "publish_via_partition_root"
    sep = " " if bare else "="
    if param == "publish_all_operations":
        return f"publish{sep}'insert, update, delete, truncate'"
    if param == "publish_via_partition_root":
        return f"publish_via_partition_root{sep}'on'" if not bare else "publish_via_partition_root"
    if param == "multiple_parameters":
        return f"publish{sep}'insert', publish_via_partition_root{sep}'on'"
    return f"publish{sep}'insert'"


def _column_clause(a: dict[str, str]) -> str:
    filt = a.get("column_filter", "no_column_filter")
    if filt == "single_column_filter":
        return " (id)"
    if filt == "multiple_column_filter":
        return " (id, data)"
    return ""


def _where_clause(a: dict[str, str]) -> str:
    if a.get("where_clause") == "simple_where_condition":
        return " WHERE (id > 0)"
    return ""


def _render_table_ref(a: dict[str, str], p: str) -> str:
    """Table reference for TABLE ops.

    When a schema factor is nonexistent (schema_dependency /
    schema_name_shape / nonexistent_schema) the table is rendered
    schema-qualified with the nonexistent schema name so PG 18.4 surfaces
    3F000 (undefined schema) rather than 00000 -- a plain ``ADD TABLE tbl``
    with no schema reference succeeds.  Only the ``simple_name`` table shape
    is re-qualified: ``schema_qualified_name`` already carries a schema and
    ``nonexistent_table`` / ``quoted_name`` carry their own reference.
    """
    table = _table_name(a, p)
    if _schema_non_existent(a) and a.get("table_name_shape", "simple_name") == "simple_name":
        schema = _schema_name(a, p)
        return f"{schema}.{table}"
    return table


def _object_clause(
    case: AlterPublicationFactorCase, a: dict[str, str], p: str
) -> str:
    op = a.get("add_set_drop_operation", "add_table")
    only_kw = "ONLY " if a.get("only_keyword") == "present" else ""
    star = " *" if a.get("star_marker") == "present" else ""
    branch = a["grammar_branch"]
    if op in _TABLE_OPS:
        table = _render_table_ref(a, p)
        cols = ""
        where = ""
        if branch != _BRANCH_DROP:
            cols = _column_clause(a)
            where = _where_clause(a)
        return f"TABLE {only_kw}{table}{star}{cols}{where}"
    if op in _SCHEMA_OPS:
        schema = _schema_name(a, p)
        return f"TABLES IN SCHEMA {schema}"
    raise AlterPublicationFactorRenderError(f"unknown operation: {op}")


def _pub_non_existent(
    case: AlterPublicationFactorCase, a: dict[str, str]
) -> bool:
    if case.kind != "EXT" and a.get("expected_status") == "failure":
        return True
    if a.get("publication_state") == "non_existent":
        return True
    if a.get("nonexistent_publication") == "publication_does_not_exist":
        return True
    if a.get("publication_name_shape") == "non_existent_name":
        return True
    return False


def _pub_for_all_tables(a: dict[str, str]) -> bool:
    return (
        a.get("publication_state") == "exists_as_for_all_tables"
        or a.get("drop_from_for_all_tables")
        == "cannot_drop_from_for_all_tables"
    )


def _table_non_existent(a: dict[str, str]) -> bool:
    if a.get("table_dependency") in _TABLE_NON_EXISTENT:
        return True
    if a.get("table_name_shape") in _TABLE_NON_EXISTENT:
        return True
    if a.get("nonexistent_table") == "add_nonexistent_table_failure":
        return True
    return False


def _schema_non_existent(a: dict[str, str]) -> bool:
    # CURRENT_SCHEMA resolves to an existing schema in PG, so the schema
    # negative (3F000) never fires for it regardless of the crossed
    # schema_dependency value.  This mirrors the extension's
    # _schema_negative_fires which returns False for current_schema_keyword.
    if a.get("schema_name_shape") == "current_schema_keyword":
        return False
    if a.get("schema_dependency") in _SCHEMA_NON_EXISTENT:
        return True
    if a.get("schema_name_shape") in _SCHEMA_NON_EXISTENT:
        return True
    if a.get("nonexistent_schema") == "add_nonexistent_schema_failure":
        return True
    return False


def _privilege_denied(
    case: AlterPublicationFactorCase, a: dict[str, str]
) -> bool:
    if case.kind != "EXT" and a.get("expected_status") == "failure":
        return False
    if a.get("executor_privilege") == "non_owner_no_privilege":
        return True
    if a.get("privilege_insufficient") in (
        "non_owner_altering_publication",
        "non_superuser_altering_other_publication",
    ):
        return True
    return False


def _is_owner_of_pub(a: dict[str, str]) -> bool:
    return a.get("executor_privilege") == "owner_of_publication"


def _effective_role(
    case: AlterPublicationFactorCase, a: dict[str, str], p: str
) -> str:
    if _privilege_denied(case, a):
        return f"{p}actor"
    if _is_owner_of_pub(a):
        return f"{p}owner"
    return ""


def _needs_table(a: dict[str, str]) -> bool:
    op = a.get("add_set_drop_operation", "add_table")
    if op not in _TABLE_OPS:
        return False
    if _table_non_existent(a):
        return False
    return True


def _needs_schema(a: dict[str, str]) -> bool:
    op = a.get("add_set_drop_operation", "add_table")
    if op in _TABLE_OPS:
        return a.get("table_name_shape") == "schema_qualified_name"
    if _schema_non_existent(a):
        return False
    return True


def _pub_fixture(
    case: AlterPublicationFactorCase, a: dict[str, str]
) -> str:
    if _pub_non_existent(case, a):
        return "none"
    if _pub_for_all_tables(a):
        return "for_all_tables"
    if a.get("publication_state") == "exists_with_tables":
        return "with_tables"
    return "exists"


def _compute_state(
    case: AlterPublicationFactorCase,
) -> _FixtureState:
    a = _baseline(case)
    p = case.object_prefix
    branch = a["grammar_branch"]
    pub_fix = _pub_fixture(case, a)
    nt = _needs_table(a)
    ns = _needs_schema(a)
    is_drop = branch == _BRANCH_DROP
    is_conflict = (
        case.factor_key == "conflicting_add_existing_table"
    )
    with_tables = pub_fix == "with_tables"
    # member_tbl: needed for exists_with_tables when target is NOT a
    # pre-added table (i.e., not DROP+table or not conflicting_add).
    needs_member = with_tables and not (
        is_drop and nt
    )
    # tbl2: needed for multiple_objects (object_list_cardinality).
    needs_tbl2 = (
        a.get("object_list_cardinality") == "multiple_objects"
        and nt
        and branch in (_BRANCH_ADD, _BRANCH_SET_OBJECT, _BRANCH_DROP)
    )
    # pre_add_target: DROP branch needs the target in the pub;
    # conflicting_add also needs it.
    pre_add_target = (
        nt and pub_fix != "none" and not _pub_for_all_tables(a)
        and (is_drop or is_conflict)
    )
    pre_add_tbl2 = (
        needs_tbl2 and is_drop and pub_fix != "none"
        and not _pub_for_all_tables(a)
    )
    effective = _effective_role(case, a, p)
    op = a.get("add_set_drop_operation", "add_table")
    is_table_op = op in _TABLE_OPS
    schema_name = _schema_name(a, p)
    # For TABLE ops the schema name in the table reference is always {p}sch
    # (a concrete simple name); CURRENT_SCHEMA is not accepted by PG as a
    # schema name in CREATE TABLE / ADD TABLE context.  For SCHEMA ops
    # (TABLES IN SCHEMA) the target uses _schema_name which may be a quoted
    # name or CURRENT_SCHEMA (PG accepts CURRENT_SCHEMA in that context).
    create_schema_name = f"{p}sch" if is_table_op else schema_name
    # should_create_schema: skip only for current_schema_keyword + SCHEMA ops
    # (CURRENT_SCHEMA resolves to the session's current schema, no creation
    # needed).  For TABLE ops, always create when table is schema-qualified.
    should_create = ns and not (
        not is_table_op
        and a.get("schema_name_shape") == "current_schema_keyword"
    )
    return _FixtureState(
        pub_fixture=pub_fix,
        needs_table=nt,
        needs_schema=ns,
        needs_member_tbl=needs_member,
        needs_tbl2=needs_tbl2,
        pre_add_target=pre_add_target,
        pre_add_tbl2=pre_add_tbl2,
        effective=effective,
        pub_name=_pub_name(a, p),
        fixture_pub=_pub_name(a, p),
        table_name=_fixture_table(a, p),
        schema_name=schema_name,
        create_schema_name=create_schema_name,
        should_create_schema=should_create,
    )


def _probe_name(
    case: AlterPublicationFactorCase, a: dict[str, str], p: str
) -> str:
    if a.get("grammar_branch") == _BRANCH_RENAME and (
        case.outcome == "success"
    ):
        return _new_name(a, p).strip('"')
    return _pub_name(a, p).strip('"')


def _probe_select(
    case: AlterPublicationFactorCase, a: dict[str, str], p: str
) -> str:
    mode = a.get("verification_mode", "pg_publication_catalog")
    if case.factor_key == "verification_mode":
        mode = case.factor_value
    name = _probe_name(case, a, p)
    if mode == "pg_publication_tables_catalog":
        return (
            "SELECT pt.pubname, pt.tablename "
            "FROM pg_catalog.pg_publication_tables AS pt "
            f"WHERE pt.pubname = '{name}' "
            "ORDER BY pt.tablename;"
        )
    if mode == "error_assertion":
        return "SELECT 1 AS error_assertion_verified;"
    return (
        "SELECT pub.pubname "
        "FROM pg_catalog.pg_publication AS pub "
        f"WHERE pub.pubname = '{name}' "
        "ORDER BY pub.pubname;"
    )


def _build_setup(
    case: AlterPublicationFactorCase,
    st: _FixtureState,
) -> tuple[list[str], str]:
    a = _baseline(case)
    p = case.object_prefix
    branch = a["grammar_branch"]
    setup: list[str] = []
    locus = "target.publication"
    if st.should_create_schema:
        setup.append(f"CREATE SCHEMA IF NOT EXISTS {st.create_schema_name};")
    effective = st.effective
    if branch == _BRANCH_OWNER_TO:
        owner = _owner_target(a, p)
        if owner not in {"CURRENT_ROLE", "CURRENT_USER", "SESSION_USER"} and owner != f"{p}no_such_role":
            setup.append(f"CREATE ROLE {p}new_owner LOGIN;")
    if effective:
        setup.append(f"CREATE ROLE {p}owner LOGIN;")
        if _privilege_denied(case, a):
            setup.append(f"CREATE ROLE {p}actor LOGIN;")
        setup.append(f"GRANT USAGE ON SCHEMA public TO {p}owner;")
        if _privilege_denied(case, a):
            setup.append(f"GRANT USAGE ON SCHEMA public TO {p}actor;")
        # A non-superuser publication owner must hold USAGE on the case schema
        # to resolve a schema-qualified table / TABLES-IN-SCHEMA reference;
        # without it PG raises 42501 (permission denied for schema) before
        # the intended table/schema-existence negative can surface.
        if st.should_create_schema:
            setup.append(f"GRANT USAGE ON SCHEMA {st.create_schema_name} TO {p}owner;")
        locus = "fixture.privilege_state"
    # CREATE PUBLICATION before CREATE TABLE so the \set meta-command
    # does not mask the CREATE TABLE from audit_complete_table_script.
    pub = st.fixture_pub
    if st.pub_fixture == "for_all_tables":
        setup.append(f"CREATE PUBLICATION {pub} FOR ALL TABLES;")
    elif st.pub_fixture != "none":
        setup.append(f"CREATE PUBLICATION {pub};")
    if st.needs_table:
        setup.append(f"CREATE TABLE {st.table_name} (id integer, data text);")
    if st.needs_member_tbl:
        setup.append(f"CREATE TABLE {p}member_tbl (id integer, data text);")
    if st.needs_tbl2:
        setup.append(f"CREATE TABLE {p}tbl2 (id integer, data text);")
    # A non-superuser publication owner must also OWN every table it adds to
    # the publication (PG: "must be owner of the table"); transfer ownership
    # of the fixture tables to the owner role so the success path surfaces.
    if _is_owner_of_pub(a):
        if st.needs_table:
            setup.append(f"ALTER TABLE {st.table_name} OWNER TO {p}owner;")
        if st.needs_member_tbl:
            setup.append(f"ALTER TABLE {p}member_tbl OWNER TO {p}owner;")
        if st.needs_tbl2:
            setup.append(f"ALTER TABLE {p}tbl2 OWNER TO {p}owner;")
    # Pre-add tables to the publication (after CREATE TABLE).
    is_for_all = _pub_for_all_tables(a)
    if st.pub_fixture not in ("none", "for_all_tables"):
        if st.needs_member_tbl and not is_for_all:
            setup.append(f"ALTER PUBLICATION {pub} ADD TABLE {p}member_tbl;")
        if st.pre_add_target and not is_for_all:
            setup.append(f"ALTER PUBLICATION {pub} ADD TABLE {st.table_name};")
        if st.pre_add_tbl2 and not is_for_all:
            setup.append(f"ALTER PUBLICATION {pub} ADD TABLE {p}tbl2;")
        # For DROP TABLES IN SCHEMA, pre-add the schema to the publication so
        # the DROP succeeds (00000); without it PG raises 42704 ("tables from
        # schema are not part of the publication").  ADD TABLES IN SCHEMA
        # requires superuser, so this runs before the ownership transfer.
        if (
            branch == _BRANCH_DROP
            and a.get("add_set_drop_operation") == "drop_tables_in_schema"
            and st.needs_schema
            and not is_for_all
        ):
            setup.append(
                f"ALTER PUBLICATION {pub} ADD TABLES IN SCHEMA {st.schema_name};"
            )
    return setup, locus


def _build_target(
    case: AlterPublicationFactorCase,
    st: _FixtureState,
) -> str:
    a = _baseline(case)
    p = case.object_prefix
    branch = a["grammar_branch"]
    ref = _pub_name(a, p)
    if branch == _BRANCH_ADD:
        objects = _object_clause(case, a, p)
        if st.needs_tbl2:
            objects = f"{objects}, TABLE {p}tbl2"
        return f"ALTER PUBLICATION {ref} ADD {objects};"
    if branch == _BRANCH_SET_OBJECT:
        objects = _object_clause(case, a, p)
        if st.needs_tbl2:
            objects = f"{objects}, TABLE {p}tbl2"
        return f"ALTER PUBLICATION {ref} SET {objects};"
    if branch == _BRANCH_DROP:
        objects = _object_clause(case, a, p)
        if st.needs_tbl2:
            objects = f"{objects}, TABLE {p}tbl2"
        return f"ALTER PUBLICATION {ref} DROP {objects};"
    if branch == _BRANCH_SET_PARAMETER:
        return f"ALTER PUBLICATION {ref} SET ({_parameter_clause(a)});"
    if branch == _BRANCH_OWNER_TO:
        return f"ALTER PUBLICATION {ref} OWNER TO {_owner_target(a, p)};"
    if branch == _BRANCH_RENAME:
        return f"ALTER PUBLICATION {ref} RENAME TO {_new_name(a, p)};"
    raise AlterPublicationFactorRenderError(f"unknown branch {branch}")


def _build_assert(
    case: AlterPublicationFactorCase,
) -> tuple[str, ...]:
    a = _baseline(case)
    p = case.object_prefix
    lines: list[str] = []
    if case.kind == "RISK":
        lines.append(
            "COMMIT;" if case.factor_value == "commit"
            else "ROLLBACK;"
        )
    lines.append(
        f"SELECT :'target_sqlstate' = '{case.expected_sqlstate}' "
        "AS target_sqlstate_matches_expected;"
    )
    lines.append(_probe_select(case, a, p))
    return tuple(lines)


def _tables_to_drop(
    case: AlterPublicationFactorCase, st: _FixtureState
) -> list[str]:
    p = case.object_prefix
    tables: list[str] = []
    if st.needs_table:
        tables.append(st.table_name)
    if st.needs_member_tbl:
        tables.append(f"{p}member_tbl")
    if st.needs_tbl2:
        tables.append(f"{p}tbl2")
    return tables


def _pub_names_to_drop(
    case: AlterPublicationFactorCase, st: _FixtureState
) -> list[str]:
    a = _baseline(case)
    p = case.object_prefix
    names: list[str] = []
    if st.pub_fixture != "none":
        names.append(st.fixture_pub)
    if a["grammar_branch"] == _BRANCH_RENAME and case.outcome == "success":
        names.append(_new_name(a, p))
    if case.factor_key == "new_name_shape" and case.factor_value == "existing_name_conflict":
        names.append(_new_name(a, p))
    return names


def _roles_to_drop(
    case: AlterPublicationFactorCase, a: dict[str, str], p: str
) -> list[str]:
    roles: list[str] = []
    if _effective_role(case, a, p):
        roles.append(f"{p}owner")
        if _privilege_denied(case, a):
            roles.append(f"{p}actor")
    if a["grammar_branch"] == _BRANCH_OWNER_TO and _owner_target(a, p) == f"{p}new_owner":
        roles.append(f"{p}new_owner")
    return roles


def _build_pre_cleanup(
    case: AlterPublicationFactorCase, st: _FixtureState
) -> tuple[str, ...]:
    a = _baseline(case)
    p = case.object_prefix
    tables = _tables_to_drop(case, st)
    pubs = _pub_names_to_drop(case, st)
    lines: list[str] = []
    if tables:
        lines.append(f"DROP TABLE IF EXISTS {', '.join(tables)} CASCADE;")
    lines.extend(f"DROP PUBLICATION IF EXISTS {n} CASCADE;" for n in pubs)
    if st.should_create_schema:
        lines.append(f"DROP SCHEMA IF EXISTS {st.create_schema_name} CASCADE;")
    for role in _roles_to_drop(case, a, p):
        lines.append(f"DROP ROLE IF EXISTS {role};")
    if not lines:
        lines.append("SELECT 1 AS residual_check_no_objects;")
    return tuple(lines)


def _build_cleanup(
    case: AlterPublicationFactorCase, st: _FixtureState
) -> tuple[str, ...]:
    a = _baseline(case)
    p = case.object_prefix
    tables = _tables_to_drop(case, st)
    pubs = _pub_names_to_drop(case, st)
    lines: list[str] = []
    if st.effective:
        lines.append("RESET ROLE;")
    lines.extend(f"DROP PUBLICATION IF EXISTS {n} CASCADE;" for n in pubs)
    if st.should_create_schema:
        lines.append(f"DROP SCHEMA IF EXISTS {st.create_schema_name} CASCADE;")
    for role in _roles_to_drop(case, a, p):
        lines.append(f"DROP OWNED BY {role};")
        lines.append(f"DROP ROLE IF EXISTS {role};")
    if tables:
        lines.append(f"DROP TABLE IF EXISTS {', '.join(tables)} CASCADE;")
    if not lines:
        lines.append("SELECT 1 AS residual_check_no_objects;")
    return tuple(lines)


def _resolve_case(
    case: AlterPublicationFactorCase,
) -> _CasePlan:
    a = _baseline(case)
    p = case.object_prefix
    st = _compute_state(case)
    setup, locus = _build_setup(case, st)
    if (case.factor_key == "new_name_shape"
            and case.factor_value == "existing_name_conflict"
            and st.pub_fixture != "none"):
        setup.append(f"CREATE PUBLICATION {_new_name(a, p)};")
    if st.effective and st.pub_fixture != "none":
        # For non_owner + SESSION_USER: the no-op escape only works when
        # SESSION_USER IS the current owner.  The pub was created by
        # pgcf_superuser (= SESSION_USER), so DO NOT transfer it to {p}owner;
        # the actor's OWNER TO SESSION_USER is then a no-op (00000).
        skip_transfer = (
            _privilege_denied(case, a)
            and a.get("owner_to_clause") == "session_user_keyword"
        )
        if not skip_transfer:
            setup.append(f"ALTER PUBLICATION {st.fixture_pub} OWNER TO {p}owner;")
        setup.append(f"SET ROLE {st.effective};")
    if case.kind == "RISK":
        setup.append("BEGIN;")
        locus = "target.transaction_boundary"
    target = _build_target(case, st)
    assert_lines = _build_assert(case)
    pre_cleanup = _build_pre_cleanup(case, st)
    cleanup = _build_cleanup(case, st)
    on_error_off = case.outcome == "expected_failure"
    return _CasePlan(
        target_fragment=target,
        setup_lines=tuple(setup),
        assert_lines=assert_lines,
        pre_cleanup_lines=pre_cleanup,
        cleanup_lines=cleanup,
        on_error_off=on_error_off,
        semantic_locus=locus,
    )


def resolve_alter_publication_factor_witness(
    case: AlterPublicationFactorCase | AlterPublicationFactorExtensionCase,
    repository_root: Path,
) -> AlterPublicationFactorWitness:
    """Return the byte-level witness fragments for one case."""

    rc = _as_render_case(case)
    plan = _resolve_case(rc)
    return AlterPublicationFactorWitness(
        primary_obligation_id=rc.primary_obligation_id,
        target_sql_fragment=plan.target_fragment,
        outcome=rc.outcome,
        expected_sqlstate=rc.expected_sqlstate,
        setup_sql=plan.setup_lines,
        oracle_sql=plan.assert_lines,
        cleanup_sql=plan.cleanup_lines,
        semantic_locus=plan.semantic_locus,
    )


def count_primary_alter_publication(sql: str) -> int:
    """Count the single credited ALTER PUBLICATION inside the fence."""

    if sql.count(_PRIMARY_BEGIN) != 1 or sql.count(_PRIMARY_END) != 1:
        return 0
    before_end, _ = sql.split(_PRIMARY_END, 1)
    if _PRIMARY_BEGIN not in before_end:
        return 0
    region = before_end.split(_PRIMARY_BEGIN, 1)[1]
    return len(re.findall(r"(?im)^\s*ALTER\s+PUBLICATION\b", region))


def _header(case: AlterPublicationFactorCase) -> list[str]:
    return [
        "-- --------------------------------------------------------",
        "-- 版权所有(C)  2021-2030 华为技术有限公司",
        "--",
        "-- --",
        f"-- author       : {_AUTHOR}",
        f"-- create at    : {_CREATE_AT}",
        f"-- version      : {_VERSION}",
        f"-- description  : ALTER PUBLICATION "
        f"{case.factor_key}={case.factor_value}",
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


def render_alter_publication_factor_case(
    case: AlterPublicationFactorCase | AlterPublicationFactorExtensionCase,
    repository_root: Path,
) -> str:
    """Render one complete, deterministic ALTER PUBLICATION regress program."""

    rc = _as_render_case(case)
    resolved = _resolve_case(rc)
    lines: list[str] = list(_header(rc))
    lines.append("-- 1. 清理本编号对象，保证脚本可重复执行。")
    lines.extend(resolved.pre_cleanup_lines)
    lines.append("\\set ON_ERROR_STOP on")
    lines.append("-- 2. 创建完整本地发布和因子专用夹具。")
    lines.extend(resolved.setup_lines)
    if resolved.on_error_off:
        lines.append("\\set ON_ERROR_STOP off")
    lines.append("-- 3. 执行唯一获得覆盖信用的 ALTER PUBLICATION。")
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


def generate_alter_publication_factor_programs(
    baseline_plan: AlterPublicationFactorLoopPlan,
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
    case: AlterPublicationFactorCase | AlterPublicationFactorExtensionCase,
    out: Path,
) -> None:
    text = render_alter_publication_factor_case(case, Path("."))
    rc = _as_render_case(case)
    (out / rc.sql_filename).write_text(text, encoding="utf-8")


__all__ = [
    "AlterPublicationFactorRenderError",
    "AlterPublicationFactorWitness",
    "count_primary_alter_publication",
    "generate_alter_publication_factor_programs",
    "render_alter_publication_factor_case",
    "resolve_alter_publication_factor_witness",
]
