"""Frozen PostgreSQL 18.4 ALTER FUNCTION grammar catalog.

This module freezes the five official synopsis branches, the 19 attribute
sub-clauses, and the optional-keyword / alternative / list-boundary axes of
``ALTER FUNCTION``.  It is the GRM input to the factor-value-loop compiler in
:mod:`pg_case_factory.alter_function_factor_loop`.

It deliberately does NOT enumerate a signature/type cross product: argument
and return types identify the target routine and are consumed via the
``argtype_specification`` canonical factor plus the dynamic
``routine_signature_resolution_manifest``, never as a free type catalog
(``alter_function.yaml`` marks ``column_type_coverage``, ``table_coverage``
and ``target_relation_coverage`` all ``not_applicable``).
"""

from __future__ import annotations

from dataclasses import dataclass


class AlterFunctionRegressError(ValueError):
    """Raised when a frozen ALTER FUNCTION grammar input drifts."""


@dataclass(frozen=True)
class AlterFunctionGrammarAction:
    """One official target action form of the ALTER FUNCTION synopsis."""

    action_id: str
    grammar_branch_id: str
    syntax_template: str
    source_locator: str


@dataclass(frozen=True)
class AlterFunctionGrammarAxis:
    """An optional / alternative / list-boundary modifier of the synopsis.

    Each ``(axis, value)`` pair is one GRM obligation in the factor-loop
    ledger.  ``values`` is the finite alternative set for that modifier.
    """

    grammar_branch_id: str
    action_id: str
    axis_id: str
    values: tuple[str, ...]
    source_locator: str


# Official synopsis branches (PostgreSQL 18 sql-alterfunction.html).
_BRANCH_ACTION_FORM = "branch_action_form"
_BRANCH_RENAME = "branch_rename"
_BRANCH_OWNER = "branch_owner"
_BRANCH_SET_SCHEMA = "branch_set_schema"
_BRANCH_DEPENDS_EXTENSION = "branch_depends_extension"

_DOC_SOURCE = "postgresql-18.4-doc:sql-alterfunction"


def load_alter_function_grammar_actions() -> (
    tuple[AlterFunctionGrammarAction, ...]
):
    """Freeze every ALTER FUNCTION synopsis target action."""

    # branch_1: attribute sub-clauses (19), one action each.
    branch_one: tuple[tuple[str, str, str], ...] = (
        (
            "called_on_null_input",
            "CALLED ON NULL INPUT",
            "synopsis-action-called-on-null-input",
        ),
        (
            "returns_null_on_null_input",
            "RETURNS NULL ON NULL INPUT",
            "synopsis-action-returns-null-on-null-input",
        ),
        ("strict", "STRICT", "synopsis-action-strict"),
        ("immutable", "IMMUTABLE", "synopsis-action-immutable"),
        ("stable", "STABLE", "synopsis-action-stable"),
        ("volatile", "VOLATILE", "synopsis-action-volatile"),
        ("leakproof", "LEAKPROOF", "synopsis-action-leakproof"),
        ("not_leakproof", "NOT LEAKPROOF", "synopsis-action-not-leakproof"),
        ("security_invoker", "SECURITY INVOKER", "synopsis-action-security-invoker"),
        ("security_definer", "SECURITY DEFINER", "synopsis-action-security-definer"),
        ("parallel_unsafe", "PARALLEL UNSAFE", "synopsis-action-parallel-unsafe"),
        (
            "parallel_restricted",
            "PARALLEL RESTRICTED",
            "synopsis-action-parallel-restricted",
        ),
        ("parallel_safe", "PARALLEL SAFE", "synopsis-action-parallel-safe"),
        ("cost", "COST execution_cost", "synopsis-action-cost"),
        ("rows", "ROWS result_rows", "synopsis-action-rows"),
        ("support", "SUPPORT support_function", "synopsis-action-support"),
        (
            "set_parameter",
            "SET configuration_parameter { TO | = } { value | DEFAULT }",
            "synopsis-action-set-parameter",
        ),
        (
            "reset_parameter",
            "RESET configuration_parameter",
            "synopsis-action-reset-parameter",
        ),
        ("reset_all", "RESET ALL", "synopsis-action-reset-all"),
    )
    outer_branches: tuple[tuple[str, str, str, str], ...] = (
        (
            "rename",
            _BRANCH_RENAME,
            "RENAME TO new_name",
            "synopsis-rename",
        ),
        (
            "owner",
            _BRANCH_OWNER,
            "OWNER TO { new_owner | CURRENT_ROLE | CURRENT_USER | SESSION_USER }",
            "synopsis-owner",
        ),
        (
            "set_schema",
            _BRANCH_SET_SCHEMA,
            "SET SCHEMA new_schema",
            "synopsis-set-schema",
        ),
        (
            "depends_on_extension",
            _BRANCH_DEPENDS_EXTENSION,
            "[ NO ] DEPENDS ON EXTENSION extension_name",
            "synopsis-depends-on-extension",
        ),
    )
    rows: list[AlterFunctionGrammarAction] = [
        AlterFunctionGrammarAction(
            action_id=action_id,
            grammar_branch_id=_BRANCH_ACTION_FORM,
            syntax_template=syntax,
            source_locator=f"{_DOC_SOURCE}:{locator}",
        )
        for action_id, syntax, locator in branch_one
    ]
    for action_id, branch, syntax, locator in outer_branches:
        rows.append(
            AlterFunctionGrammarAction(
                action_id=action_id,
                grammar_branch_id=branch,
                syntax_template=syntax,
                source_locator=f"{_DOC_SOURCE}:{locator}",
            )
        )
    if len(rows) != 23:
        raise AlterFunctionRegressError("alter function action count drift")
    return tuple(rows)


def load_alter_function_grammar_axes() -> tuple[AlterFunctionGrammarAxis, ...]:
    """Freeze every optional / alternative / list-boundary modifier."""

    rows: list[AlterFunctionGrammarAxis] = []

    def add(
        branch: str,
        action: str,
        axis: str,
        values: tuple[str, ...],
        locator: str,
    ) -> None:
        rows.append(
            AlterFunctionGrammarAxis(
                grammar_branch_id=branch,
                action_id=action,
                axis_id=axis,
                values=values,
                source_locator=f"{_DOC_SOURCE}:{locator}",
            )
        )

    # branch_1 outer modifiers: RESTRICT is accepted (no-op default) and the
    # action list may carry one or many sub-clauses.
    add(
        _BRANCH_ACTION_FORM,
        "__outer_action__",
        "restrict_clause",
        ("absent", "present"),
        "synopsis-action-restrict",
    )
    add(
        _BRANCH_ACTION_FORM,
        "__outer_action__",
        "action_list_cardinality",
        ("one_action", "multiple_actions"),
        "synopsis-action-list-cardinality",
    )
    # SET configuration_parameter has three assignment spellings.
    add(
        _BRANCH_ACTION_FORM,
        "set_parameter",
        "set_assignment_form",
        ("to_value", "equals_value", "to_default"),
        "synopsis-action-set-assignment-form",
    )
    # [ EXTERNAL ] SECURITY INVOKER / DEFINER: EXTERNAL is optional on each.
    add(
        _BRANCH_ACTION_FORM,
        "security_invoker",
        "external_keyword",
        ("omitted", "present"),
        "synopsis-action-external-invoker",
    )
    add(
        _BRANCH_ACTION_FORM,
        "security_definer",
        "external_keyword",
        ("omitted", "present"),
        "synopsis-action-external-definer",
    )
    # [ NO ] DEPENDS ON EXTENSION: the NO keyword is the polarity modifier.
    add(
        _BRANCH_DEPENDS_EXTENSION,
        "depends_on_extension",
        "depends_polarity",
        ("depends", "no_depends"),
        "synopsis-depends-polarity",
    )

    if len(rows) != 6 or sum(len(row.values) for row in rows) != 13:
        raise AlterFunctionRegressError("alter function axis ledger is incomplete")
    return tuple(rows)


__all__ = [
    "AlterFunctionRegressError",
    "AlterFunctionGrammarAction",
    "AlterFunctionGrammarAxis",
    "load_alter_function_grammar_actions",
    "load_alter_function_grammar_axes",
]
