"""Frozen PostgreSQL 18.4 ALTER PROCEDURE grammar catalog.

This module freezes the five official synopsis branches, the five attribute
sub-clauses, and the optional-keyword / alternative / list-boundary axes of
``ALTER PROCEDURE``.  It is the GRM input to the factor-value-loop compiler in
:mod:`pg_case_factory.alter_procedure_factor_loop`.

It deliberately does NOT enumerate a signature/type cross product: argument
types identify the target routine and are consumed via the
``argtype_specification`` canonical factor plus the dynamic
``routine_signature_resolution_manifest``, never as a free type catalog
(``alter_procedure.yaml`` marks ``column_type_coverage``, ``table_coverage``
and ``target_relation_coverage`` all ``not_applicable``).
"""

from __future__ import annotations

from dataclasses import dataclass


class AlterProcedureRegressError(ValueError):
    """Raised when a frozen ALTER PROCEDURE grammar input drifts."""


@dataclass(frozen=True)
class AlterProcedureGrammarAction:
    """One official target action form of the ALTER PROCEDURE synopsis."""

    action_id: str
    grammar_branch_id: str
    syntax_template: str
    source_locator: str


@dataclass(frozen=True)
class AlterProcedureGrammarAxis:
    """An optional / alternative / list-boundary modifier of the synopsis.

    Each ``(axis, value)`` pair is one GRM obligation in the factor-loop
    ledger.  ``values`` is the finite alternative set for that modifier.
    """

    grammar_branch_id: str
    action_id: str
    axis_id: str
    values: tuple[str, ...]
    source_locator: str


# Official synopsis branches (PostgreSQL 18 sql-alterprocedure.html).
_BRANCH_ACTION_FORM = "branch_action_form"
_BRANCH_RENAME = "branch_rename"
_BRANCH_OWNER = "branch_owner"
_BRANCH_SET_SCHEMA = "branch_set_schema"
_BRANCH_DEPENDS_EXTENSION = "branch_depends_extension"

_DOC_SOURCE = "postgresql-18.4-doc:sql-alterprocedure"


def load_alter_procedure_grammar_actions() -> (
    tuple[AlterProcedureGrammarAction, ...]
):
    """Freeze every ALTER PROCEDURE synopsis target action."""

    # branch_1: attribute sub-clauses (5), one action each.
    branch_one: tuple[tuple[str, str, str], ...] = (
        (
            "security_invoker",
            "[ EXTERNAL ] SECURITY INVOKER",
            "synopsis-action-security-invoker",
        ),
        (
            "security_definer",
            "[ EXTERNAL ] SECURITY DEFINER",
            "synopsis-action-security-definer",
        ),
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
    rows: list[AlterProcedureGrammarAction] = [
        AlterProcedureGrammarAction(
            action_id=action_id,
            grammar_branch_id=_BRANCH_ACTION_FORM,
            syntax_template=syntax,
            source_locator=f"{_DOC_SOURCE}:{locator}",
        )
        for action_id, syntax, locator in branch_one
    ]
    for action_id, branch, syntax, locator in outer_branches:
        rows.append(
            AlterProcedureGrammarAction(
                action_id=action_id,
                grammar_branch_id=branch,
                syntax_template=syntax,
                source_locator=f"{_DOC_SOURCE}:{locator}",
            )
        )
    if len(rows) != 9:
        raise AlterProcedureRegressError("alter procedure action count drift")
    return tuple(rows)


def load_alter_procedure_grammar_axes() -> (
    tuple[AlterProcedureGrammarAxis, ...]
):
    """Freeze every optional / alternative / list-boundary modifier."""

    rows: list[AlterProcedureGrammarAxis] = []

    def add(
        branch: str,
        action: str,
        axis: str,
        values: tuple[str, ...],
        locator: str,
    ) -> None:
        rows.append(
            AlterProcedureGrammarAxis(
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
        raise AlterProcedureRegressError(
            "alter procedure axis ledger is incomplete"
        )
    return tuple(rows)


__all__ = [
    "AlterProcedureRegressError",
    "AlterProcedureGrammarAction",
    "AlterProcedureGrammarAxis",
    "load_alter_procedure_grammar_actions",
    "load_alter_procedure_grammar_axes",
]
