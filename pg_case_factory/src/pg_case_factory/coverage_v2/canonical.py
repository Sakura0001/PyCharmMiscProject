from __future__ import annotations

import hashlib
from typing import Any

import rfc8785

from .errors import CoverageV2ContractError


CANONICAL_JSON_VERSION = "rfc8785-no-float-v1"


def _validate_json_value(value: Any, location: str) -> None:
    if value is None or type(value) in (bool, int, str):
        return
    if isinstance(value, float):
        raise CoverageV2ContractError(f"{location} must not contain float values")
    if isinstance(value, list):
        for index, item in enumerate(value):
            _validate_json_value(item, f"{location}[{index}]")
        return
    if isinstance(value, dict):
        for key, item in value.items():
            if not isinstance(key, str):
                raise CoverageV2ContractError(f"{location} keys must be strings")
            _validate_json_value(item, f"{location}.{key}")
        return
    raise CoverageV2ContractError(
        f"{location} contains unsupported {type(value).__name__}"
    )


def canonical_json_bytes(value: Any) -> bytes:
    _validate_json_value(value, "value")
    try:
        return rfc8785.dumps(value)
    except (TypeError, ValueError) as exc:
        raise CoverageV2ContractError(f"cannot canonicalize value: {exc}") from exc


def sha256_hex(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()
