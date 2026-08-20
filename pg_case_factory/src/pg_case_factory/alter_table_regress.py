"""Frozen PostgreSQL 18.4 ALTER TABLE grammar catalog.

This module freezes the optional-keyword grammar axes of the
``ALTER TABLE`` synopsis that are NOT already canonical ``SFV`` rows in
``alter_table.yaml``.  It is the GRM input to the factor-value-loop compiler
in :mod:`pg_case_factory.alter_table_factor_loop`.

The four axes are the optional ``COLUMN`` keyword (after ADD / DROP / ALTER)
and the optional ``SET DATA`` keywords (before TYPE).  These are pure grammar
modifiers absent from the SFV matrix, so re-emitting them here does not
duplicate the marginal ledger.
"""

from __future__ import annotations

from dataclasses import dataclass


class AlterTableRegressError(ValueError):
    """Raised when a frozen ALTER TABLE grammar input drifts."""


@dataclass(frozen=True)
class AlterTableGrammarAxis:
    """An optional / alternative / list-boundary modifier of the synopsis.

    Each ``(axis, value)`` pair is one GRM obligation in the factor-loop
    ledger.  ``values`` is the finite alternative set for that modifier.
    """

    grammar_branch_id: str
    action_id: str
    axis_id: str
    values: tuple[str, ...]
    source_locator: str


# Official synopsis branches (PostgreSQL 18 sql-altertable.html).
_BRANCH_1_ACTION = "branch_1_action"
_BRANCH_2_RENAME_COLUMN = "branch_2_rename_column"
_BRANCH_3_RENAME_CONSTRAINT = "branch_3_rename_constraint"
_BRANCH_4_RENAME_TABLE = "branch_4_rename_table"
_BRANCH_5_SET_SCHEMA = "branch_5_set_schema"
_BRANCH_6_SET_TABLESPACE_BATCH = "branch_6_set_tablespace_batch"
_BRANCH_7_ATTACH_PARTITION = "branch_7_attach_partition"
_BRANCH_8_DETACH_PARTITION = "branch_8_detach_partition"

# Target-action identifiers used as consumer ids across the factor loop.
ACTION_ADD_COLUMN = "add_column"
ACTION_DROP_COLUMN = "drop_column"
ACTION_ALTER_COLUMN_TYPE = "alter_column_type"

_DOC_SOURCE = "postgresql-18.4-doc:sql-altertable"


def load_alter_table_grammar_axes() -> (
    tuple[AlterTableGrammarAxis, ...]
):
    """Freeze every optional / alternative / list-boundary modifier.

    The four axes are pure grammar modifiers absent from the SFV matrix:

    * ``add_column_keyword``     -- ``ADD [ COLUMN ]`` (the COLUMN keyword is optional).
    * ``drop_column_keyword``    -- ``DROP [ COLUMN ]`` (the COLUMN keyword is optional).
    * ``alter_column_keyword``   -- ``ALTER [ COLUMN ]`` (the COLUMN keyword is optional).
    * ``set_data_keyword``       -- ``[ SET DATA ] TYPE`` (SET DATA is optional).
    """

    rows: list[AlterTableGrammarAxis] = []

    def add(
        branch: str,
        action: str,
        axis: str,
        values: tuple[str, ...],
        locator: str,
    ) -> None:
        rows.append(
            AlterTableGrammarAxis(
                grammar_branch_id=branch,
                action_id=action,
                axis_id=axis,
                values=values,
                source_locator=f"{_DOC_SOURCE}:{locator}",
            )
        )

    # ADD [ COLUMN ]: the COLUMN keyword is optional.
    add(
        _BRANCH_1_ACTION,
        ACTION_ADD_COLUMN,
        "add_column_keyword",
        ("absent", "present"),
        "synopsis-add-column-keyword",
    )
    # DROP [ COLUMN ]: the COLUMN keyword is optional.
    add(
        _BRANCH_1_ACTION,
        ACTION_DROP_COLUMN,
        "drop_column_keyword",
        ("absent", "present"),
        "synopsis-drop-column-keyword",
    )
    # ALTER [ COLUMN ]: the COLUMN keyword is optional.
    add(
        _BRANCH_1_ACTION,
        ACTION_ALTER_COLUMN_TYPE,
        "alter_column_keyword",
        ("absent", "present"),
        "synopsis-alter-column-keyword",
    )
    # [ SET DATA ] TYPE: the SET DATA keywords are optional.
    add(
        _BRANCH_1_ACTION,
        ACTION_ALTER_COLUMN_TYPE,
        "set_data_keyword",
        ("absent", "present"),
        "synopsis-set-data-keyword",
    )

    if len(rows) != 4 or sum(len(row.values) for row in rows) != 8:
        raise AlterTableRegressError(
            "alter table axis ledger is incomplete"
        )
    return tuple(rows)


__all__ = [
    "AlterTableRegressError",
    "AlterTableGrammarAxis",
    "ACTION_ADD_COLUMN",
    "ACTION_DROP_COLUMN",
    "ACTION_ALTER_COLUMN_TYPE",
    "load_alter_table_grammar_axes",
]
