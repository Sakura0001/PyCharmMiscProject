"""Frozen PostgreSQL 18.4 ALTER SCHEMA grammar catalog.

This module freezes the two official synopsis branches of
``ALTER SCHEMA``: ``RENAME TO`` and ``OWNER TO``.  ALTER SCHEMA is a
PostgreSQL extension outside the SQL standard; it is a pure
namespace-management statement with no attribute/option subcommands and no
optional keywords, alternative modifiers, or list-boundary axes, so the
grammar ledger comprises exactly two GRM actions with zero axes.
"""

from __future__ import annotations

from dataclasses import dataclass


class AlterSchemaRegressError(ValueError):
    """Raised when a frozen ALTER SCHEMA grammar input drifts."""


@dataclass(frozen=True)
class AlterSchemaGrammarAction:
    """One official target action form of the ALTER SCHEMA synopsis."""

    action_id: str
    grammar_branch_id: str
    syntax_template: str
    source_locator: str


@dataclass(frozen=True)
class AlterSchemaGrammarAxis:
    """An optional / alternative / list-boundary modifier of the synopsis."""

    grammar_branch_id: str
    action_id: str
    axis_id: str
    values: tuple[str, ...]
    source_locator: str


# Official synopsis branches (PostgreSQL 18 sql-alterschema.html).
_BRANCH_RENAME = "branch_rename"
_BRANCH_OWNER = "branch_owner"

_DOC_SOURCE = "postgresql-18.4-doc:sql-alterschema"

# Ordered (branch, action) pairs mirroring alter_role's
# STATEMENT_BRANCH_ACTIONS so the factor-loop can resolve a canonical
# statement_branch value to its consumer action id.
STATEMENT_BRANCH_ACTIONS = (
    (_BRANCH_RENAME, "rename"),
    (_BRANCH_OWNER, "owner"),
)


def load_alter_schema_grammar_actions() -> (
    tuple[AlterSchemaGrammarAction, ...]
):
    """Freeze every ALTER SCHEMA synopsis target action."""

    rows: tuple[tuple[str, str, str, str], ...] = (
        (
            "rename",
            _BRANCH_RENAME,
            "ALTER SCHEMA name RENAME TO new_name",
            "synopsis-rename",
        ),
        (
            "owner",
            _BRANCH_OWNER,
            (
                "ALTER SCHEMA name OWNER TO "
                "{ new_owner | CURRENT_ROLE | CURRENT_USER | SESSION_USER }"
            ),
            "synopsis-owner-to",
        ),
    )
    actions = [
        AlterSchemaGrammarAction(
            action_id=action_id,
            grammar_branch_id=branch,
            syntax_template=syntax,
            source_locator=f"{_DOC_SOURCE}:{locator}",
        )
        for action_id, branch, syntax, locator in rows
    ]
    if len(actions) != 2:
        raise AlterSchemaRegressError("alter schema action count drift")
    return tuple(actions)


def load_alter_schema_grammar_axes() -> (
    tuple[AlterSchemaGrammarAxis, ...]
):
    """Freeze every optional / alternative / list-boundary modifier.

    ALTER SCHEMA has two fixed forms with no optional keywords,
    alternatives, or list-boundary modifiers, so the axis ledger is empty.
    """

    return ()


__all__ = [
    "AlterSchemaRegressError",
    "AlterSchemaGrammarAction",
    "AlterSchemaGrammarAxis",
    "STATEMENT_BRANCH_ACTIONS",
    "load_alter_schema_grammar_actions",
    "load_alter_schema_grammar_axes",
]
