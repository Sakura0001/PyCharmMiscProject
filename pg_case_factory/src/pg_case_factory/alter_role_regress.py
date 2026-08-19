"""Frozen PostgreSQL 18.4 ALTER ROLE grammar catalog.

This module freezes the six official synopsis branches of ``ALTER ROLE``
plus the optional-keyword / alternative / list-boundary grammar axes that
are NOT already canonical ``SFV`` rows in ``alter_role.yaml``.  It is the
GRM input to the factor-value-loop compiler in
:mod:`pg_case_factory.alter_role_factor_loop`.

It deliberately does NOT enumerate the six branches or the 18 attribute
options as GRM obligations: ``statement_branch`` (6 values) and
``attribute_option`` (18 values) are already canonical ``SFV`` rows, so
re-emitting them here would duplicate the marginal ledger (the
``alter_index`` anti-pattern that breaks conservation).  Only the pure
grammar modifiers -- the optional ``WITH`` keyword, the optional
``ENCRYPTED`` keyword, the one-vs-many action-list cardinality, and the
``TO`` vs ``=`` assignment spelling -- are frozen here as GRM axes.
``alter_role.yaml`` marks ``column_type_coverage``, ``table_coverage``
and ``target_relation_coverage`` all ``not_applicable``, so there is no
``INV`` block.
"""

from __future__ import annotations

from dataclasses import dataclass


class AlterRoleRegressError(ValueError):
    """Raised when a frozen ALTER ROLE grammar input drifts."""


@dataclass(frozen=True)
class AlterRoleGrammarAxis:
    """An optional / alternative / list-boundary modifier of the synopsis.

    Each ``(axis, value)`` pair is one GRM obligation in the factor-loop
    ledger.  ``values`` is the finite alternative set for that modifier.
    """

    grammar_branch_id: str
    action_id: str
    axis_id: str
    values: tuple[str, ...]
    source_locator: str


# Official synopsis branches (PostgreSQL 18 sql-alterrole.html).  These are
# branch constants used as the consumer-action namespace; they are NOT
# compiled into GRM obligations (statement_branch is an SFV row).
_BRANCH_WITH_OPTION = "branch_1_with_option"
_BRANCH_RENAME = "branch_2_rename"
_BRANCH_SET_VALUE = "branch_3_set_value"
_BRANCH_SET_FROM_CURRENT = "branch_4_set_from_current"
_BRANCH_RESET_PARAMETER = "branch_5_reset_parameter"
_BRANCH_RESET_ALL = "branch_6_reset_all"

# Target-action identifiers used as consumer ids across the factor loop.
# statement_branch canonical values map 1:1 to these actions.
ACTION_WITH_OPTION = "with_option"
ACTION_RENAME = "rename"
ACTION_SET_VALUE = "set_value"
ACTION_SET_FROM_CURRENT = "set_from_current"
ACTION_RESET_PARAMETER = "reset_parameter"
ACTION_RESET_ALL = "reset_all"

# (statement_branch canonical value, target action) pairs.
STATEMENT_BRANCH_ACTIONS = (
    ("branch_1_with_option", ACTION_WITH_OPTION),
    ("branch_2_rename", ACTION_RENAME),
    ("branch_3_set_value", ACTION_SET_VALUE),
    ("branch_4_set_from_current", ACTION_SET_FROM_CURRENT),
    ("branch_5_reset_parameter", ACTION_RESET_PARAMETER),
    ("branch_6_reset_all", ACTION_RESET_ALL),
)

_DOC_SOURCE = "postgresql-18.4-doc:sql-alterrole"


def load_alter_role_grammar_axes() -> tuple[AlterRoleGrammarAxis, ...]:
    """Freeze every optional / alternative / list-boundary modifier.

    The four axes are pure grammar modifiers absent from the SFV matrix:

    * ``with_keyword``      -- ``[ WITH ]`` before the option list (branch_1).
    * ``encrypted_keyword`` -- ``[ ENCRYPTED ]`` before ``PASSWORD`` (branch_1).
    * ``action_list_cardinality`` -- one vs many options in branch_1.
    * ``set_assignment_form`` -- ``{ TO | = }`` spelling in branch_3 SET.
    """

    rows: list[AlterRoleGrammarAxis] = []

    def add(
        branch: str,
        action: str,
        axis: str,
        values: tuple[str, ...],
        locator: str,
    ) -> None:
        rows.append(
            AlterRoleGrammarAxis(
                grammar_branch_id=branch,
                action_id=action,
                axis_id=axis,
                values=values,
                source_locator=f"{_DOC_SOURCE}:{locator}",
            )
        )

    # branch_1 outer modifiers: WITH is optional; the option list may carry
    # one or many sub-clauses.
    add(
        _BRANCH_WITH_OPTION,
        "__outer_action__",
        "with_keyword",
        ("absent", "present"),
        "synopsis-with-keyword",
    )
    add(
        _BRANCH_WITH_OPTION,
        "__outer_action__",
        "action_list_cardinality",
        ("one_action", "multiple_actions"),
        "synopsis-action-list-cardinality",
    )
    # [ ENCRYPTED ] PASSWORD 'password': the ENCRYPTED keyword is optional.
    add(
        _BRANCH_WITH_OPTION,
        "__outer_action__",
        "encrypted_keyword",
        ("omitted", "present"),
        "synopsis-encrypted-keyword",
    )
    # branch_3 SET configuration_parameter has two assignment spellings.
    add(
        _BRANCH_SET_VALUE,
        "__outer_action__",
        "set_assignment_form",
        ("to_value", "equals_value"),
        "synopsis-set-assignment-form",
    )

    if len(rows) != 4 or sum(len(row.values) for row in rows) != 8:
        raise AlterRoleRegressError("alter role axis ledger is incomplete")
    return tuple(rows)


__all__ = [
    "AlterRoleRegressError",
    "AlterRoleGrammarAxis",
    "ACTION_WITH_OPTION",
    "ACTION_RENAME",
    "ACTION_SET_VALUE",
    "ACTION_SET_FROM_CURRENT",
    "ACTION_RESET_PARAMETER",
    "ACTION_RESET_ALL",
    "STATEMENT_BRANCH_ACTIONS",
    "load_alter_role_grammar_axes",
]
