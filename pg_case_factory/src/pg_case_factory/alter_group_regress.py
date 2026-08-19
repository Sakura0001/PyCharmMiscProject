"""Frozen grammar constants for PostgreSQL 18.4 ALTER GROUP.

``ALTER GROUP`` is a deprecated role-membership / role-rename command.
Unlike ``ALTER FUNCTION`` it has **no grammar axis beyond the canonical
factors**: every syntactic alternative (``statement_branch`` ADD/DROP/
RENAME, ``role_specification`` role_name/CURRENT_ROLE/CURRENT_USER/
SESSION_USER, ``multi_user`` single/multiple, ``*_shape`` identifiers)
is already a canonical ``SFV`` row in ``alter_group.yaml``.  The
marginal ledger therefore compiles to ``57 SFV + 2 RISK`` with
``GRM == 0``; that compilation lives in :mod:`alter_group_factor_loop`.

This module holds only the branch/action constants and the shared error
type so the publication control plane and the renderer can reference a
stable per-statement grammar surface.
"""

from __future__ import annotations


class AlterGroupRegressError(ValueError):
    """Raised when a frozen ALTER GROUP grammar input drifts."""


# Target-action identifiers used as consumer ids across the factor loop.
# statement_branch values map 1:1 to these actions (branch_add_user ->
# add_user, branch_drop_user -> drop_user, branch_rename -> rename).
ACTION_ADD_USER = "add_user"
ACTION_DROP_USER = "drop_user"
ACTION_RENAME = "rename"

# (statement_branch canonical value, target action) pairs.
STATEMENT_BRANCH_ACTIONS = (
    ("branch_add_user", ACTION_ADD_USER),
    ("branch_drop_user", ACTION_DROP_USER),
    ("branch_rename", ACTION_RENAME),
)

ALTER_ACTION_VALUES = (ACTION_ADD_USER, ACTION_DROP_USER, ACTION_RENAME)


__all__ = [
    "AlterGroupRegressError",
    "ACTION_ADD_USER",
    "ACTION_DROP_USER",
    "ACTION_RENAME",
    "STATEMENT_BRANCH_ACTIONS",
    "ALTER_ACTION_VALUES",
]
