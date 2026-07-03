from __future__ import annotations

from itertools import product
from pathlib import Path


DEFAULT_HEADER_TEMPLATE = """-- --------------------------------------------------------
-- description : {description}
-- statement : {statement_key}
-- sequence : {sequence}
-- --------------------------------------------------------"""


def _stable_token(case_token: str) -> str:
    return case_token.lower().replace(" ", "_").replace("-", "_")


def _build_object_name(prefix: str, case_token: str, sequence: int, max_length: int = 64) -> str:
    suffix = f"_{sequence:04d}"
    body_limit = max_length - len(suffix)
    stable_body = f"{prefix}{_stable_token(case_token)}"[:body_limit].rstrip("_")
    return f"{stable_body}{suffix}"


def build_name_context(case_token: str, sequence: int, max_identifier_length: int = 64) -> dict[str, str]:
    return {
        "table_name": _build_object_name("tab_", case_token, sequence, max_identifier_length),
        "index_name": _build_object_name("idx_", case_token, sequence, max_identifier_length),
        "view_name": _build_object_name("vw_", case_token, sequence, max_identifier_length),
        "database_name": _build_object_name("db_", case_token, sequence, max_identifier_length),
        "enum_name": _build_object_name("typ_", case_token, sequence, max_identifier_length),
        "prepared_name": _build_object_name("stmt_", case_token, sequence, max_identifier_length),
        "procedure_name": _build_object_name("proc_", case_token, sequence, max_identifier_length),
        "function_name": _build_object_name("fn_", case_token, sequence, max_identifier_length),
        "trigger_name": _build_object_name("trg_", case_token, sequence, max_identifier_length),
        "event_name": _build_object_name("ev_", case_token, sequence, max_identifier_length),
        "server_name": _build_object_name("srv_", case_token, sequence, max_identifier_length),
        "tablespace_name": _build_object_name("ts_", case_token, sequence, max_identifier_length),
        "logfile_group_name": _build_object_name("lfg_", case_token, sequence, max_identifier_length),
        "resource_group_name": _build_object_name("rg_", case_token, sequence, max_identifier_length),
        "spatial_ref_name": _build_object_name("srs_", case_token, sequence, max_identifier_length),
        "component_urn": f"file://component_{_stable_token(case_token)}_{sequence:04d}",
        "plugin_name": _build_object_name("plugin_", case_token, sequence, max_identifier_length),
        "srs_id": str(500000 + sequence),
        "cursor_name": _build_object_name("cur_", case_token, sequence, max_identifier_length),
        "xa_xid": _build_object_name("xid_", case_token, sequence, max_identifier_length),
    }


def build_bindings(skill: dict) -> list[dict[str, str]]:
    important_factors = tuple(skill["important_factors"])
    non_important_factors = tuple(skill["non_important_factors"])
    factor_values = dict(skill["factor_values"])
    defaults = dict(skill["defaults"])

    important_values = [factor_values[name] for name in important_factors]
    main_combinations = [dict(zip(important_factors, combo)) for combo in product(*important_values)] if important_values else [dict()]
    combos = [{**defaults, **main_binding} for main_binding in main_combinations]
    main_count = len(main_combinations)

    extra_assignments: list[tuple[str, str]] = []
    for factor in non_important_factors:
        for value in factor_values[factor][1:]:
            extra_assignments.append((factor, value))

    safe_main_count = max(1, main_count)
    for index, (factor, value) in enumerate(extra_assignments):
        skeleton_index = index % safe_main_count
        clone_round = index // safe_main_count
        if clone_round == 0 and combos:
            target = combos[skeleton_index]
        else:
            base = main_combinations[skeleton_index] if main_combinations else {}
            target = {**defaults, **base}
            combos.append(target)
        target[factor] = value
    return combos


def render_object_template(object_path: str | Path, context: dict[str, str]) -> str:
    template = Path(object_path).read_text(encoding="utf-8")
    return template.format(**context).strip()


def render_statement(skill: dict, binding: dict[str, str], context: dict[str, str]) -> dict[str, str]:
    rendering = dict(skill["rendering"])
    resolved = dict(context)
    for placeholder, spec in dict(rendering["factor_value_bindings"]).items():
        factor = str(dict(spec)["factor"])
        values = dict(dict(spec).get("values") or {})
        raw_value = str(values[binding[factor]])
        resolved[placeholder] = raw_value.format(**resolved)

    statement_sql = str(rendering.get("statement_template") or "").format(**resolved).strip()
    verification_template = str(rendering.get("verification_query_template") or "").strip()
    verification_sql = verification_template.format(**resolved).strip() if verification_template else ""
    return {
        "statement_sql": statement_sql,
        "verification_sql": verification_sql,
        "resolved_context": resolved,
    }


def compose_sql_script(
    statement_key: str,
    sequence: int,
    blocks: list[tuple[str, str]],
    description: str,
) -> str:
    header = DEFAULT_HEADER_TEMPLATE.format(
        description=description,
        statement_key=statement_key,
        sequence=f"{sequence:04d}",
    ).strip()
    sections = [header]
    for label, sql in blocks:
        if not sql or not sql.strip():
            continue
        sections.append(f"-- {label}\n{sql.strip()}" if label else sql.strip())
    return "\n\n".join(sections) + "\n"
