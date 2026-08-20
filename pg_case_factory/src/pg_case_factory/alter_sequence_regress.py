"""Frozen PostgreSQL 18.4 ALTER SEQUENCE grammar catalog.

This module freezes the optional-keyword grammar axes of the
``ALTER SEQUENCE`` parameter-modification synopsis that are NOT already
canonical ``SFV`` rows in ``alter_sequence.yaml``.  It is the GRM input to
the factor-value-loop compiler in
:mod:`pg_case_factory.alter_sequence_factor_loop`.

It deliberately does NOT enumerate the five official synopsis branches or
the nine ``alter_parameter_type`` sub-actions as GRM obligations:
``statement_branch`` (5 values) and ``alter_parameter_type`` (9 values) are
already canonical SFV rows, so re-emitting them here would duplicate the
marginal ledger (the ``alter_index`` anti-pattern that breaks conservation).
Only the pure grammar modifiers -- the optional ``BY`` keyword after
``INCREMENT``, the optional ``WITH`` keyword after ``START`` / ``RESTART``,
and the optional ``NO`` keyword before ``CYCLE`` -- are frozen here as GRM
axes.  ``alter_sequence.yaml`` marks ``column_type_coverage``
``not_applicable``, so there is no ``INV`` block.
"""

from __future__ import annotations

from dataclasses import dataclass


class AlterSequenceRegressError(ValueError):
    """Raised when a frozen ALTER SEQUENCE grammar input drifts."""


@dataclass(frozen=True)
class AlterSequenceGrammarAxis:
    """An optional / alternative / list-boundary modifier of the synopsis.

    Each ``(axis, value)`` pair is one GRM obligation in the factor-loop
    ledger.  ``values`` is the finite alternative set for that modifier.
    """

    grammar_branch_id: str
    action_id: str
    axis_id: str
    values: tuple[str, ...]
    source_locator: str


# Official synopsis branches (PostgreSQL 18 sql-altersequence.html).  These are
# branch constants used as the consumer-action namespace; they are NOT
# compiled into GRM obligations (statement_branch is an SFV row).
_BRANCH_ALTER_PARAMETERS = "branch_alter_parameters"
_BRANCH_SET_LOGGED_UNLOGGED = "branch_set_logged_unlogged"
_BRANCH_OWNER = "branch_owner"
_BRANCH_RENAME = "branch_rename"
_BRANCH_SET_SCHEMA = "branch_set_schema"

# Target-action identifiers used as consumer ids across the factor loop.
ACTION_ALTER_PARAMETERS = "alter_parameters"
ACTION_SET_LOGGED_UNLOGGED = "set_logged_unlogged"
ACTION_OWNER = "owner"
ACTION_RENAME = "rename"
ACTION_SET_SCHEMA = "set_schema"

# (statement_branch canonical value, target action) pairs.
STATEMENT_BRANCH_ACTIONS = (
    (_BRANCH_ALTER_PARAMETERS, ACTION_ALTER_PARAMETERS),
    (_BRANCH_SET_LOGGED_UNLOGGED, ACTION_SET_LOGGED_UNLOGGED),
    (_BRANCH_OWNER, ACTION_OWNER),
    (_BRANCH_RENAME, ACTION_RENAME),
    (_BRANCH_SET_SCHEMA, ACTION_SET_SCHEMA),
)

_DOC_SOURCE = "postgresql-18.4-doc:sql-altersequence"


def load_alter_sequence_grammar_axes() -> (
    tuple[AlterSequenceGrammarAxis, ...]
):
    """Freeze every optional / alternative / list-boundary modifier.

    The four axes are pure grammar modifiers absent from the SFV matrix:

    * ``increment_by_keyword``  -- ``[ INCREMENT [ BY ] increment ]`` (branch_alter_parameters, change_increment).
    * ``start_with_keyword``    -- ``[ START [ WITH ] start ]`` (branch_alter_parameters, change_start).
    * ``restart_with_keyword``  -- ``[ RESTART [ [ WITH ] restart ] ]`` (branch_alter_parameters, restart_with).
    * ``cycle_no_keyword``      -- ``[ [ NO ] CYCLE ]`` (branch_alter_parameters, change_cycle).
    """

    rows: list[AlterSequenceGrammarAxis] = []

    def add(
        branch: str,
        action: str,
        axis: str,
        values: tuple[str, ...],
        locator: str,
    ) -> None:
        rows.append(
            AlterSequenceGrammarAxis(
                grammar_branch_id=branch,
                action_id=action,
                axis_id=axis,
                values=values,
                source_locator=f"{_DOC_SOURCE}:{locator}",
            )
        )

    # [ INCREMENT [ BY ] increment ]: the BY keyword is optional.
    add(
        _BRANCH_ALTER_PARAMETERS,
        "change_increment",
        "increment_by_keyword",
        ("absent", "present"),
        "synopsis-increment-by-keyword",
    )
    # [ START [ WITH ] start ]: the WITH keyword is optional.
    add(
        _BRANCH_ALTER_PARAMETERS,
        "change_start",
        "start_with_keyword",
        ("absent", "present"),
        "synopsis-start-with-keyword",
    )
    # [ RESTART [ [ WITH ] restart ] ]: the WITH keyword is optional.
    add(
        _BRANCH_ALTER_PARAMETERS,
        "restart_with",
        "restart_with_keyword",
        ("absent", "present"),
        "synopsis-restart-with-keyword",
    )
    # [ [ NO ] CYCLE ]: the NO keyword is optional.
    add(
        _BRANCH_ALTER_PARAMETERS,
        "change_cycle",
        "cycle_no_keyword",
        ("absent", "present"),
        "synopsis-cycle-no-keyword",
    )

    if len(rows) != 4 or sum(len(row.values) for row in rows) != 8:
        raise AlterSequenceRegressError(
            "alter sequence axis ledger is incomplete"
        )
    return tuple(rows)


__all__ = [
    "AlterSequenceRegressError",
    "AlterSequenceGrammarAxis",
    "ACTION_ALTER_PARAMETERS",
    "ACTION_SET_LOGGED_UNLOGGED",
    "ACTION_OWNER",
    "ACTION_RENAME",
    "ACTION_SET_SCHEMA",
    "STATEMENT_BRANCH_ACTIONS",
    "load_alter_sequence_grammar_axes",
]
