"""Frozen PostgreSQL 18.4 ALTER RULE grammar catalog.

This module freezes the single official synopsis branch of ``ALTER RULE``.
ALTER RULE supports only ``RENAME``; ``ENABLE``/``DISABLE``/``REPLICA``/
``ALWAYS RULE`` are ``ALTER TABLE`` subcommands and are out of scope for
this statement.  There are no optional keywords or alternative modifiers,
so the grammar ledger comprises exactly one GRM action with zero axes.
"""

from __future__ import annotations

from dataclasses import dataclass


class AlterRuleRegressError(ValueError):
    """Raised when a frozen ALTER RULE grammar input drifts."""


@dataclass(frozen=True)
class AlterRuleGrammarAction:
    """One official target action form of the ALTER RULE synopsis."""

    action_id: str
    grammar_branch_id: str
    syntax_template: str
    source_locator: str


@dataclass(frozen=True)
class AlterRuleGrammarAxis:
    """An optional / alternative / list-boundary modifier of the synopsis."""

    grammar_branch_id: str
    action_id: str
    axis_id: str
    values: tuple[str, ...]
    source_locator: str


# Official synopsis branch (PostgreSQL 18 sql-alterrule.html).
_BRANCH_RENAME = "branch_rename"

_DOC_SOURCE = "postgresql-18.4-doc:sql-alterrule"


def load_alter_rule_grammar_actions() -> (
    tuple[AlterRuleGrammarAction, ...]
):
    """Freeze every ALTER RULE synopsis target action."""

    rows: list[AlterRuleGrammarAction] = [
        AlterRuleGrammarAction(
            action_id="rename",
            grammar_branch_id=_BRANCH_RENAME,
            syntax_template=(
                "ALTER RULE name ON table_name RENAME TO new_name"
            ),
            source_locator=f"{_DOC_SOURCE}:synopsis-rename",
        ),
    ]
    if len(rows) != 1:
        raise AlterRuleRegressError("alter rule action count drift")
    return tuple(rows)


def load_alter_rule_grammar_axes() -> tuple[AlterRuleGrammarAxis, ...]:
    """Freeze every optional / alternative / list-boundary modifier.

    ALTER RULE has a single fixed form with no optional keywords,
    alternatives, or list-boundary modifiers, so the axis ledger is empty.
    """

    return ()


__all__ = [
    "AlterRuleRegressError",
    "AlterRuleGrammarAction",
    "AlterRuleGrammarAxis",
    "load_alter_rule_grammar_actions",
    "load_alter_rule_grammar_axes",
]
