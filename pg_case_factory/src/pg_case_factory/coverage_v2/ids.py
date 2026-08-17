from __future__ import annotations

import re
import unicodedata
from collections.abc import Sequence
from dataclasses import dataclass, field

from .canonical import canonical_json_bytes, sha256_hex
from .errors import CoverageV2ContractError


ID_DOMAIN = b"FSCR_ID_V2\0"
ALLOWED_ID_KINDS = frozenset(
    {
        "GRM", "FOB", "INV", "RISK", "NA", "INT", "AXI", "ITUP",
        "PROD", "PTUP", "STUP", "ATOM", "SUB", "PROGRAM",
        "BUNDLE", "SHARD", "WIT",
    }
)
DECLARED_ID = re.compile(r"^([A-Z]+)-([0-9a-f]{64})$")


def _normalized_components(components: Sequence[str]) -> tuple[str, ...]:
    if isinstance(components, (str, bytes, bytearray)):
        raise CoverageV2ContractError("logical ID components must be a sequence")
    result: list[str] = []
    for index, component in enumerate(components):
        if not isinstance(component, str) or not component:
            raise CoverageV2ContractError(
                f"logical ID component {index} must be a non-empty string"
            )
        result.append(unicodedata.normalize("NFC", component))
    return tuple(result)


def logical_id(kind: str, components: Sequence[str]) -> str:
    if kind not in ALLOWED_ID_KINDS:
        raise CoverageV2ContractError(f"unsupported logical ID kind {kind!r}")
    normalized = _normalized_components(components)
    digest = sha256_hex(ID_DOMAIN + canonical_json_bytes([kind, *normalized]))
    return f"{kind}-{digest}"


@dataclass
class LogicalIdRegistry:
    by_id: dict[str, tuple[str, tuple[str, ...]]] = field(default_factory=dict)
    by_components: dict[tuple[str, tuple[str, ...]], str] = field(default_factory=dict)

    def register(self, kind: str, components: Sequence[str]) -> str:
        declared = logical_id(kind, components)
        return self.register_declared(declared, kind, components)

    def register_declared(
        self,
        declared_id: str,
        kind: str,
        components: Sequence[str],
    ) -> str:
        match = DECLARED_ID.fullmatch(declared_id)
        if match is None or match.group(1) != kind:
            raise CoverageV2ContractError("declared logical ID has invalid syntax or kind")
        normalized = _normalized_components(components)
        expected = logical_id(kind, normalized)
        if declared_id != expected:
            raise CoverageV2ContractError("declared logical ID differs from recomputed ID")
        identity = (kind, normalized)
        existing_identity = self.by_id.get(declared_id)
        if existing_identity is not None and existing_identity != identity:
            raise CoverageV2ContractError("one logical ID maps to different components")
        existing_id = self.by_components.get(identity)
        if existing_id is not None and existing_id != declared_id:
            raise CoverageV2ContractError("one component tuple maps to different logical IDs")
        self.by_id[declared_id] = identity
        self.by_components[identity] = declared_id
        return declared_id
