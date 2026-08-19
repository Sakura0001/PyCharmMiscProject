"""Frozen PostgreSQL 18.4 ALTER PUBLICATION grammar catalog.

This module freezes the six official synopsis branches of
``ALTER PUBLICATION`` plus the optional-keyword / alternative /
list-boundary axes of the publication-object and parameter grammar.  It is
the GRM input to the factor-value-loop compiler in
:mod:`pg_case_factory.alter_publication_factor_loop`.

It deliberately does NOT enumerate a table/column cross product: member
tables and columns are consumed via the ``add_set_drop_operation``,
``column_filter`` and ``where_clause`` canonical factors (T2), never as a
free type catalog (``alter_publication.yaml`` marks
``column_type_coverage`` ``conditional`` on the ADD/SET branches).
"""

from __future__ import annotations

from dataclasses import dataclass


class AlterPublicationRegressError(ValueError):
    """Raised when a frozen ALTER PUBLICATION grammar input drifts."""


@dataclass(frozen=True)
class AlterPublicationGrammarAction:
    """One official target action form of the ALTER PUBLICATION synopsis."""

    action_id: str
    grammar_branch_id: str
    syntax_template: str
    source_locator: str


@dataclass(frozen=True)
class AlterPublicationGrammarAxis:
    """An optional / alternative / list-boundary modifier of the synopsis.

    Each ``(axis, value)`` pair is one GRM obligation in the factor-loop
    ledger.  ``values`` is the finite alternative set for that modifier.
    """

    grammar_branch_id: str
    action_id: str
    axis_id: str
    values: tuple[str, ...]
    source_locator: str


# Official synopsis branches (PostgreSQL 18 sql-alterpublication.html).
_BRANCH_ADD = "branch_add"
_BRANCH_SET_OBJECT = "branch_set_object"
_BRANCH_DROP = "branch_drop"
_BRANCH_SET_PARAMETER = "branch_set_parameter"
_BRANCH_OWNER_TO = "branch_owner_to"
_BRANCH_RENAME = "branch_rename"

_DOC_SOURCE = "postgresql-18.4-doc:sql-alterpublication"


def load_alter_publication_grammar_actions() -> (
    tuple[AlterPublicationGrammarAction, ...]
):
    """Freeze every ALTER PUBLICATION synopsis target action."""

    actions: tuple[tuple[str, str, str, str], ...] = (
        (
            "add_object",
            _BRANCH_ADD,
            "ALTER PUBLICATION name ADD publication_object [, ...]",
            "synopsis-add",
        ),
        (
            "set_object",
            _BRANCH_SET_OBJECT,
            "ALTER PUBLICATION name SET publication_object [, ...]",
            "synopsis-set-object",
        ),
        (
            "drop_object",
            _BRANCH_DROP,
            "ALTER PUBLICATION name DROP publication_drop_object [, ...]",
            "synopsis-drop",
        ),
        (
            "set_parameter",
            _BRANCH_SET_PARAMETER,
            "ALTER PUBLICATION name SET ( publication_parameter [= value] [, ...] )",
            "synopsis-set-parameter",
        ),
        (
            "owner",
            _BRANCH_OWNER_TO,
            "ALTER PUBLICATION name OWNER TO { new_owner | CURRENT_ROLE | CURRENT_USER | SESSION_USER }",
            "synopsis-owner-to",
        ),
        (
            "rename",
            _BRANCH_RENAME,
            "ALTER PUBLICATION name RENAME TO new_name",
            "synopsis-rename",
        ),
    )
    rows = [
        AlterPublicationGrammarAction(
            action_id=action_id,
            grammar_branch_id=branch,
            syntax_template=syntax,
            source_locator=f"{_DOC_SOURCE}:{locator}",
        )
        for action_id, branch, syntax, locator in actions
    ]
    if len(rows) != 6:
        raise AlterPublicationRegressError("alter publication action count drift")
    return tuple(rows)


def load_alter_publication_grammar_axes() -> (
    tuple[AlterPublicationGrammarAxis, ...]
):
    """Freeze every optional / alternative / list-boundary modifier."""

    rows: list[AlterPublicationGrammarAxis] = []

    def add(
        branch: str,
        action: str,
        axis: str,
        values: tuple[str, ...],
        locator: str,
    ) -> None:
        rows.append(
            AlterPublicationGrammarAxis(
                grammar_branch_id=branch,
                action_id=action,
                axis_id=axis,
                values=values,
                source_locator=f"{_DOC_SOURCE}:{locator}",
            )
        )

    # [ ONLY ] table_name [ * ]: the ONLY keyword and the * marker are
    # optional on each TABLE publication object in the ADD / SET / DROP
    # branches.
    for branch in (_BRANCH_ADD, _BRANCH_SET_OBJECT, _BRANCH_DROP):
        add(
            branch,
            "__outer_action__",
            "only_keyword",
            ("absent", "present"),
            "synopsis-only-keyword",
        )
        add(
            branch,
            "__outer_action__",
            "star_marker",
            ("absent", "present"),
            "synopsis-star-marker",
        )
        add(
            branch,
            "__outer_action__",
            "object_list_cardinality",
            ("one_object", "multiple_objects"),
            "synopsis-object-list-cardinality",
        )
    # SET ( publication_parameter [= value] ): the ``=`` is optional on each
    # parameter assignment in the SET-parameter branch.
    add(
        _BRANCH_SET_PARAMETER,
        "set_parameter",
        "parameter_assignment_form",
        ("equals_value", "no_equals"),
        "synopsis-parameter-assignment-form",
    )

    if len(rows) != 10 or sum(len(row.values) for row in rows) != 20:
        raise AlterPublicationRegressError(
            "alter publication axis ledger is incomplete"
        )
    return tuple(rows)


__all__ = [
    "AlterPublicationRegressError",
    "AlterPublicationGrammarAction",
    "AlterPublicationGrammarAxis",
    "load_alter_publication_grammar_actions",
    "load_alter_publication_grammar_axes",
]
