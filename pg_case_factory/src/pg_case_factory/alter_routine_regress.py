"""Frozen PostgreSQL 18.4 ALTER ROUTINE grammar catalog.

This module freezes the five official synopsis branches, the 20 attribute
sub-clauses (16 ``branch_action`` actions + 4 outer-branch operations), and the
optional-keyword / alternative / list-boundary axes of ``ALTER ROUTINE``.  It
is the GRM input to the factor-value-loop compiler in
:mod:`pg_case_factory.alter_routine_factor_loop`.

``ALTER ROUTINE`` is the generic routine wrapper: it resolves to
``ALTER FUNCTION`` / ``ALTER PROCEDURE`` / ``ALTER AGGREGATE`` depending on the
target object kind.  Its synopsis action set is the union of the routine-kind
actions (volatility, leakproof, security, parallel, cost, rows, SET/RESET),
modelled here as 16 ``branch_action`` grammar actions.

It deliberately does NOT enumerate a signature/type cross product: argument
and return types identify the target routine and are consumed via the
``arg_signature`` canonical factor plus the dynamic
``routine_resolution_manifest``, never as a free type catalog
(``alter_routine.yaml`` marks ``column_type_coverage``, ``table_coverage``
and ``target_relation_coverage`` all ``not_applicable``).
"""

from __future__ import annotations

from dataclasses import dataclass


class AlterRoutineRegressError(ValueError):
    """Raised when a frozen ALTER ROUTINE grammar input drifts."""


@dataclass(frozen=True)
class AlterRoutineGrammarAction:
    """One official target action form of the ALTER ROUTINE synopsis."""

    action_id: str
    grammar_branch_id: str
    syntax_template: str
    source_locator: str


@dataclass(frozen=True)
class AlterRoutineGrammarAxis:
    """An optional / alternative / list-boundary modifier of the synopsis.

    Each ``(axis, value)`` pair is one GRM obligation in the factor-loop
    ledger.  ``values`` is the finite alternative set for that modifier.
    """

    grammar_branch_id: str
    action_id: str
    axis_id: str
    values: tuple[str, ...]
    source_locator: str


# Official synopsis branches (PostgreSQL 18 sql-alterroutine.html).
_BRANCH_ACTION_FORM = "branch_action_form"
_BRANCH_RENAME = "branch_rename"
_BRANCH_OWNER = "branch_owner"
_BRANCH_SET_SCHEMA = "branch_set_schema"
_BRANCH_DEPENDS_EXTENSION = "branch_depends_extension"

_DOC_SOURCE = "postgresql-18.4-doc:sql-alterroutine"


def load_alter_routine_grammar_actions() -> (
    tuple[AlterRoutineGrammarAction, ...]
):
    """Freeze every ALTER ROUTINE synopsis target action."""

    # branch_action: attribute sub-clauses (16), one action each.  The action
    # set is the union of routine-kind actions: volatility, leakproof,
    # security, parallel, cost, rows, and the SET/RESET configuration family.
    # SET ... FROM CURRENT is modelled as its own action (set_config_from_current)
    # rather than as an axis variant of set_config_parameter.
    branch_one: tuple[tuple[str, str, str], ...] = (
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
        (
            "set_config_parameter",
            "SET configuration_parameter { TO | = } { value | DEFAULT }",
            "synopsis-action-set-config-parameter",
        ),
        (
            "set_config_from_current",
            "SET configuration_parameter FROM CURRENT",
            "synopsis-action-set-config-from-current",
        ),
        (
            "reset_config_parameter",
            "RESET configuration_parameter",
            "synopsis-action-reset-config-parameter",
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
    rows: list[AlterRoutineGrammarAction] = [
        AlterRoutineGrammarAction(
            action_id=action_id,
            grammar_branch_id=_BRANCH_ACTION_FORM,
            syntax_template=syntax,
            source_locator=f"{_DOC_SOURCE}:{locator}",
        )
        for action_id, syntax, locator in branch_one
    ]
    for action_id, branch, syntax, locator in outer_branches:
        rows.append(
            AlterRoutineGrammarAction(
                action_id=action_id,
                grammar_branch_id=branch,
                syntax_template=syntax,
                source_locator=f"{_DOC_SOURCE}:{locator}",
            )
        )
    if len(rows) != 20:
        raise AlterRoutineRegressError("alter routine action count drift")
    return tuple(rows)


def load_alter_routine_grammar_axes() -> tuple[AlterRoutineGrammarAxis, ...]:
    """Freeze every optional / alternative / list-boundary modifier."""

    rows: list[AlterRoutineGrammarAxis] = []

    def add(
        branch: str,
        action: str,
        axis: str,
        values: tuple[str, ...],
        locator: str,
    ) -> None:
        rows.append(
            AlterRoutineGrammarAxis(
                grammar_branch_id=branch,
                action_id=action,
                axis_id=axis,
                values=values,
                source_locator=f"{_DOC_SOURCE}:{locator}",
            )
        )

    # branch_action outer modifiers: RESTRICT is accepted (no-op default for
    # RENAME/SET SCHEMA/DEPENDS ON EXTENSION; for the action form it is also a
    # no-op marker) and the action list may carry one or many sub-clauses.
    # restrict_clause values mirror the SFV factor audit TSV ("omitted"/
    # "restrict") so the GRM axis and the canonical factor share one namespace.
    add(
        _BRANCH_ACTION_FORM,
        "__outer_action__",
        "restrict_clause",
        ("omitted", "restrict"),
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
        "set_config_parameter",
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
        raise AlterRoutineRegressError(
            "alter routine axis ledger is incomplete"
        )
    return tuple(rows)


__all__ = [
    "AlterRoutineRegressError",
    "AlterRoutineGrammarAction",
    "AlterRoutineGrammarAxis",
    "load_alter_routine_grammar_actions",
    "load_alter_routine_grammar_axes",
]
