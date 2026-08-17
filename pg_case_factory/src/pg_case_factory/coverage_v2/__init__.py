"""Fail-closed full statement coverage V2 primitives."""

from .ids import ALLOWED_ID_KINDS, LogicalIdRegistry, logical_id

SCHEMA_VERSION = 2

__all__ = [
    "ALLOWED_ID_KINDS",
    "LogicalIdRegistry",
    "SCHEMA_VERSION",
    "logical_id",
]
