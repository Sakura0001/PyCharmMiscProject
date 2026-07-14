"""Typed YAML contracts for feature-driven MySQL test generation.

The contracts in this module deliberately model plans, not generated prose.  They
are small enough to be produced by an agent, while retaining the identifiers and
source links needed for deterministic expansion and later execution auditing.
"""

from __future__ import annotations

import hashlib
import json
import math
import re
from dataclasses import dataclass, field
from pathlib import Path, PurePosixPath
from typing import Any, Iterable, Mapping, Optional, Sequence, Union

import yaml


COVERAGE_OUTCOMES = ("success", "expected_failure", "justified_na")
CASE_EXECUTION_PROFILES = ("basic_mysql", "external_isolated")
SUPPORTED_COMPATIBILITY_TARGETS = (
    "mysql-community-8.0.22",
    "mysql-community-8.0.41",
)
REQUIRED_SCOPE_DECISIONS = ("object", "relation", "table", "column_type")
REQUIRED_RISK_DECISIONS = (
    "syntax",
    "operation",
    "lifecycle",
    "data_profile",
    "large_value_lob",
    "transaction",
    "partitioning",
    "index_constraint_trigger",
    "privilege",
    "maintenance",
    "concurrency",
    "restart_recovery",
)
CANONICAL_SCOPE_SELECTORS = {
    "object": "#sql_object_types.all_sql_object_types",
    "relation": "#relation_kinds.all_mysql8022_relkinds",
    "table": "#relation_dimensions.<table-dimension>.values",
    "column_type": "#structured_config.<complete-column-dimension>",
}
_SKILL_INVENTORY = "references/combinations/_shared/coverage_inventory.yaml"
_SKILL_TYPE_CATALOG = "references/common/mysql80_type_catalog.md"
_TABLE_DIMENSION_SELECTORS = (
    "relation_dimensions.relpersistence.values",
    "relation_dimensions.partition_role.values",
    "relation_dimensions.partition_strategy.values",
    "relation_dimensions.inheritance_role.values",
    "relation_dimensions.table_access_method_selection.values",
)
_COLUMN_DIMENSION_SELECTORS = (
    "structured_config.families.numeric.values",
    "structured_config.families.string.values",
    "structured_config.families.temporal.values",
    "structured_config.families.json.values",
    "structured_config.families.spatial.values",
    "structured_config.families.blob.values",
)
CANONICAL_SCOPE_SOURCE_GROUPS = {
    "object": (
        (f"{_SKILL_INVENTORY}#sql_object_types.all_sql_object_types",),
    ),
    "relation": (
        (f"{_SKILL_INVENTORY}#relation_kinds.all_mysql8022_relkinds",),
    ),
    "table": (
        tuple(f"{_SKILL_INVENTORY}#{selector}" for selector in _TABLE_DIMENSION_SELECTORS),
    ),
    "column_type": (
        tuple(f"{_SKILL_TYPE_CATALOG}#{selector}" for selector in _COLUMN_DIMENSION_SELECTORS),
    ),
}
CANONICAL_SCOPE_SNAPSHOTS = {
    "object": ((18, "94e86d2f51f5832154d344b553925d68d909aa8d65b95aac5eea8bd7a8bc39f6"),),
    "relation": ((4, "9cba8f8abeea197c914347b298268047378904b2c39a159d919dbe33751742b2"),),
    "table": (
        (2, "124d32a98830f86eb3293a9ce69291304ffdaa2b7a5a6058957040b789dab304"),
        (3, "e8d2a308ca55827a1da49bd8e67a9e89bea63d3a57c594d099661c537509e199"),
        (5, "74dc0f327b60fa7b34936f18c524497a1ebcbb51dc6e129b9c394dab2378d119"),
        (1, "aeb30d3540aee03dc2cb23a6b339c5a71d89a48891d804226617a4edeae9919e"),
        (3, "acc512898516c00c1343b5e531d9a03dc6384cad370eb3e58be169ec530b674b"),
    ),
    "column_type": (
        (9, "12f76694007f07803d05d90c9c094048a593db890c6dda98fd889b99761fbc83"),
        (10, "4b8d3ce6762fe170951487825eff44aecd085392378b8ff90b008a565e232de6"),
        (5, "77348ee9b812c1a0fad6dd42e826b7330bdc4d9a9e604b9cfa5e0f1a4d49ef55"),
        (1, "8b7e5172c2f7c47256cc46a90cf755d8b0de7f992db99fa6e15b6d58ed8813d5"),
        (4, "fe366ac47affdd89928b95bc1d2b661812b9814caa9095f588122b87c2977d95"),
        (4, "53b93aeddea3bb7c7d3396931fb1802cd412be2f7114be4670c857f8de4ef261"),
    ),
}
_SCALAR_TYPES = (str, int, float, bool, type(None))
_SHA256_PATTERN = re.compile(r"^[0-9a-f]{64}$")
_STABLE_ID_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")
_LIBPQ_SERVICE_PATTERN = re.compile(r"^[A-Za-z0-9_.-]+$")
_REQUIREMENT_LOCATOR_KEYS = {
    "anchor",
    "heading",
    "line",
    "locator",
    "page",
    "paragraph",
    "section",
}
_YAML_SCALAR_TAGS = {
    type(None): "tag:yaml.org,2002:null",
    bool: "tag:yaml.org,2002:bool",
    int: "tag:yaml.org,2002:int",
    float: "tag:yaml.org,2002:float",
    str: "tag:yaml.org,2002:str",
}


class ContractValidationError(ValueError):
    """Raised when a contract is structurally or semantically invalid."""

    def __init__(self, issues: Union[str, Iterable[str]]):
        if isinstance(issues, str):
            normalized = [issues]
        else:
            normalized = [str(issue) for issue in issues if str(issue)]
        self.issues = tuple(normalized)
        super().__init__("; ".join(self.issues))


class _UniqueKeySafeLoader(yaml.SafeLoader):
    """SafeLoader variant that refuses lossy duplicate mapping keys."""

    def construct_mapping(self, node, deep=False):
        seen = set()
        for key_node, _ in node.value:
            key = self.construct_object(key_node, deep=deep)
            if not isinstance(key, str):
                raise ContractValidationError(
                    f"contract mapping keys must be strings, got {type(key).__name__}"
                )
            try:
                duplicate = key in seen
            except TypeError:
                # The regular SafeLoader will report invalid unhashable mapping
                # keys.  Contract keys are strings, so no special case is needed.
                continue
            if duplicate:
                raise ContractValidationError(f"duplicate YAML key {key}")
            seen.add(key)
        return super().construct_mapping(node, deep=deep)


def _mapping(value: Any, location: str) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        raise ContractValidationError(f"{location} must be a mapping")
    for key in value:
        if not isinstance(key, str):
            raise ContractValidationError(
                f"{location} mapping keys must be strings, got {type(key).__name__}"
            )
    return dict(value)


def _validate_json_safe(value: Any, location: str) -> None:
    """Reject YAML-only values that cannot enter the durable JSON ledger.

    YAML implicitly constructs values such as dates, timestamps, sets, and
    binary blobs.  Accepting those values here would make a contract parse
    successfully and then fail later while hashing or persisting a job.  The
    contract boundary therefore accepts only strict JSON-shaped data.
    """

    if value is None or isinstance(value, (str, bool, int)):
        return
    if isinstance(value, float):
        if not math.isfinite(value):
            raise ContractValidationError(f"{location} must not contain NaN or infinity")
        return
    if isinstance(value, Mapping):
        for key, item in value.items():
            if not isinstance(key, str):
                raise ContractValidationError(
                    f"{location} mapping keys must be strings, got {type(key).__name__}"
                )
            _validate_json_safe(item, f"{location}.{key}")
        return
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        for index, item in enumerate(value):
            _validate_json_safe(item, f"{location}[{index}]")
        return
    raise ContractValidationError(
        f"{location} must contain only JSON-compatible values, got {type(value).__name__}"
    )


def _json_mapping(value: Any, location: str) -> dict[str, Any]:
    document = _mapping(value, location)
    _validate_json_safe(document, location)
    return document


def _sequence(value: Any, location: str) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, (str, bytes)) or not isinstance(value, Sequence):
        raise ContractValidationError(f"{location} must be a sequence")
    return list(value)


def _required_string(document: Mapping[str, Any], key: str, location: str) -> str:
    value = document.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ContractValidationError(f"{location}.{key} must be a non-empty string")
    return value.strip()


def _optional_string(document: Mapping[str, Any], key: str, location: str) -> Optional[str]:
    value = document.get(key)
    if value is None:
        return None
    if not isinstance(value, str) or not value.strip():
        raise ContractValidationError(f"{location}.{key} must be a non-empty string when present")
    return value.strip()


def _stable_id(value: Any, location: str) -> str:
    if not isinstance(value, str) or _STABLE_ID_PATTERN.fullmatch(value) is None:
        raise ContractValidationError(
            f"{location} must be a portable stable identifier matching "
            "[A-Za-z0-9][A-Za-z0-9._-]*"
        )
    return value


def _require_allowed_keys(
    document: Mapping[str, Any],
    required: set[str],
    optional: set[str],
    location: str,
) -> None:
    actual = set(document)
    missing = sorted(required - actual)
    unexpected = sorted(actual - required - optional)
    if not missing and not unexpected:
        return
    details: list[str] = []
    if missing:
        details.append(
            "missing " + ", ".join(f"{location}.{key}" for key in missing)
        )
    if unexpected:
        details.append("unexpected " + ", ".join(unexpected))
    raise ContractValidationError(
        f"{location} has invalid fields: " + "; ".join(details)
    )


def _string_tuple(value: Any, location: str) -> tuple[str, ...]:
    values = _sequence(value, location)
    normalized: list[str] = []
    for index, item in enumerate(values):
        if not isinstance(item, str) or not item.strip():
            raise ContractValidationError(f"{location}[{index}] must be a non-empty string")
        normalized.append(item.strip())
    return tuple(normalized)


def _stable_id_tuple(value: Any, location: str) -> tuple[str, ...]:
    values = _string_tuple(value, location)
    for index, item in enumerate(values):
        _stable_id(item, f"{location}[{index}]")
    return values


def _schema_header(document: Mapping[str, Any], expected_kind: str) -> int:
    schema_version = document.get("schema_version")
    if schema_version != 1:
        raise ContractValidationError("schema_version must be 1")
    if document.get("kind") != expected_kind:
        raise ContractValidationError(f"kind must be {expected_kind}")
    return 1


def _require_exact_keys(
    document: Mapping[str, Any],
    expected: set[str],
    location: str,
) -> None:
    """Reject both omitted and silently ignored contract fields."""

    actual = set(document)
    if actual == expected:
        return
    details: list[str] = []
    missing = sorted(expected - actual)
    unexpected = sorted(actual - expected)
    if missing:
        details.append("missing " + ", ".join(missing))
    if unexpected:
        details.append("unexpected " + ", ".join(unexpected))
    raise ContractValidationError(
        f"{location} has invalid fields: " + "; ".join(details)
    )


def _validate_unique(values: Iterable[str], noun: str) -> None:
    seen: set[str] = set()
    for value in values:
        if value in seen:
            raise ContractValidationError(f"duplicate {noun} {value}")
        seen.add(value)


def _inventory_values_payload(values: Iterable[Any]) -> bytes:
    """Return the canonical type-tagged YAML representation of axis values."""

    tagged_values = []
    for index, value in enumerate(values):
        if type(value) not in _SCALAR_TYPES:
            raise ContractValidationError(
                f"inventory values[{index}] must be a YAML scalar"
            )
        tagged_values.append(
            {
                "tag": _YAML_SCALAR_TAGS[type(value)],
                "value": value,
            }
        )
    return yaml.safe_dump(
        tagged_values,
        allow_unicode=True,
        default_flow_style=False,
        explicit_start=True,
        sort_keys=True,
        width=4096,
    ).encode("utf-8")


def inventory_values_sha256(values: Iterable[Any]) -> str:
    """Hash an ordered sequence of type-tagged YAML scalar values.

    Explicit YAML tags make otherwise-equal Python values such as ``true`` and
    ``1`` distinct.  Sequence order is intentionally significant because an
    inventory snapshot is also the deterministic case-expansion order.
    """

    return hashlib.sha256(_inventory_values_payload(values)).hexdigest()


def inventory_value_equal(left: Any, right: Any) -> bool:
    """Compare two inventory scalars using the contract's YAML type semantics."""

    return _inventory_values_payload((left,)) == _inventory_values_payload((right,))


@dataclass(frozen=True)
class FeatureRequirement:
    requirement_id: str
    description: str
    source: Mapping[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, raw: Mapping[str, Any], location: str = "requirement") -> "FeatureRequirement":
        document = _mapping(raw, location)
        _require_exact_keys(document, {"id", "description", "source"}, location)
        source = _json_mapping(document.get("source"), f"{location}.source")
        if not source:
            raise ContractValidationError(
                f"{location}.source must contain a locator into the preserved feature document"
            )
        valid_locators = []
        for key in _REQUIREMENT_LOCATOR_KEYS & set(source):
            value = source[key]
            if isinstance(value, str) and value.strip():
                valid_locators.append(key)
            elif type(value) is int and value > 0:
                valid_locators.append(key)
            else:
                raise ContractValidationError(
                    f"{location}.source.{key} must be a non-empty string or positive integer"
                )
        if not valid_locators:
            raise ContractValidationError(
                f"{location}.source must contain at least one of: "
                + ", ".join(sorted(_REQUIREMENT_LOCATOR_KEYS))
            )
        unexpected_source_keys = sorted(set(source) - _REQUIREMENT_LOCATOR_KEYS)
        if unexpected_source_keys:
            raise ContractValidationError(
                f"{location}.source has invalid fields: unexpected "
                + ", ".join(unexpected_source_keys)
            )
        return cls(
            requirement_id=_stable_id(document.get("id"), f"{location}.id"),
            description=_required_string(document, "description", location),
            source=source,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.requirement_id,
            "description": self.description,
            "source": dict(self.source),
        }


@dataclass(frozen=True)
class FeatureManifest:
    schema_version: int
    feature_id: str
    title: str
    compatibility_target: str
    source: Mapping[str, Any]
    requirements: tuple[FeatureRequirement, ...]
    summary: Optional[str] = None
    metadata: Mapping[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, raw: Mapping[str, Any]) -> "FeatureManifest":
        document = _mapping(raw, "feature_manifest")
        _require_allowed_keys(
            document,
            {
                "schema_version",
                "kind",
                "feature_id",
                "title",
                "compatibility_target",
                "source",
                "requirements",
            },
            {"summary", "metadata"},
            "feature_manifest",
        )
        schema_version = _schema_header(document, "feature_manifest")
        compatibility_target = _required_string(
            document,
            "compatibility_target",
            "feature_manifest",
        )
        if compatibility_target not in SUPPORTED_COMPATIBILITY_TARGETS:
            raise ContractValidationError(
                "feature_manifest.compatibility_target must be mysql-community-8.0.22 "
                "or mysql-community-8.0.41"
            )
        source = _json_mapping(document.get("source"), "feature_manifest.source")
        _require_allowed_keys(
            source,
            {"path", "sha256"},
            {"revision"},
            "feature_manifest.source",
        )
        source_path = _required_string(source, "path", "feature_manifest.source")
        if "\\" in source_path:
            raise ContractValidationError(
                "feature_manifest.source.path must use portable forward slashes"
            )
        portable_source_path = PurePosixPath(source_path)
        if portable_source_path.is_absolute() or ".." in portable_source_path.parts:
            raise ContractValidationError(
                "feature_manifest.source.path must be relative and stay under its source root"
            )
        source_sha256 = source.get("sha256")
        if not isinstance(source_sha256, str) or not _SHA256_PATTERN.fullmatch(
            source_sha256
        ):
            raise ContractValidationError(
                "feature_manifest.source.sha256 must be a 64-character lowercase SHA-256"
            )
        if "revision" in source:
            _required_string(source, "revision", "feature_manifest.source")
        requirement_documents = _sequence(document.get("requirements"), "feature_manifest.requirements")
        if not requirement_documents:
            raise ContractValidationError("feature_manifest.requirements must not be empty")
        requirements = tuple(
            FeatureRequirement.from_dict(item, f"feature_manifest.requirements[{index}]")
            for index, item in enumerate(requirement_documents)
        )
        _validate_unique((item.requirement_id for item in requirements), "requirement id")
        return cls(
            schema_version=schema_version,
            feature_id=_stable_id(document.get("feature_id"), "feature_manifest.feature_id"),
            title=_required_string(document, "title", "feature_manifest"),
            compatibility_target=compatibility_target,
            source=source,
            requirements=requirements,
            summary=_optional_string(document, "summary", "feature_manifest"),
            metadata=_json_mapping(document.get("metadata") or {}, "feature_manifest.metadata"),
        )

    def to_dict(self) -> dict[str, Any]:
        document: dict[str, Any] = {
            "schema_version": self.schema_version,
            "kind": "feature_manifest",
            "feature_id": self.feature_id,
            "title": self.title,
            "compatibility_target": self.compatibility_target,
            "source": dict(self.source),
            "requirements": [item.to_dict() for item in self.requirements],
        }
        if self.summary is not None:
            document["summary"] = self.summary
        if self.metadata:
            document["metadata"] = dict(self.metadata)
        return document


@dataclass(frozen=True)
class ExecutionEndpoint:
    """One formal endpoint addressed through an external mysql login path."""

    login_path: str
    database: str
    expected_server_uuid: str
    expected_current_user: str

    @classmethod
    def from_dict(
        cls,
        raw: Mapping[str, Any],
        location: str,
    ) -> "ExecutionEndpoint":
        document = _mapping(raw, location)
        _require_exact_keys(
            document,
            {
                "login_path",
                "database",
                "expected_server_uuid",
                "expected_current_user",
            },
            location,
        )
        login_path = _required_string(document, "login_path", location)
        if not _LIBPQ_SERVICE_PATTERN.fullmatch(login_path):
            raise ContractValidationError(
                f"{location}.login_path must be a bare mysql_config_editor login path"
            )
        database = _required_string(document, "database", location)
        lowered_database = database.lower()
        if (
            document["database"] != database
            or "=" in database
            or lowered_database.startswith("mysql://")
            or any(ord(character) < 32 or ord(character) == 127 for character in database)
        ):
            raise ContractValidationError(
                f"{location}.database must be a bare database name, not a URI or conninfo"
            )
        expected_server_uuid = document["expected_server_uuid"]
        if not isinstance(expected_server_uuid, str) or re.fullmatch(
            r"[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-"
            r"[0-9a-fA-F]{4}-[0-9a-fA-F]{12}",
            expected_server_uuid,
        ) is None:
            raise ContractValidationError(
                f"{location}.expected_server_uuid must be a canonical UUID"
            )
        expected_current_user = document["expected_current_user"]
        if (
            not isinstance(expected_current_user, str)
            or not expected_current_user
            or any(
                ord(character) < 32 or ord(character) == 127
                for character in expected_current_user
            )
        ):
            raise ContractValidationError(
                f"{location}.expected_current_user must be a non-empty string "
                "without control characters"
            )
        return cls(
            login_path=login_path,
            database=database,
            expected_server_uuid=expected_server_uuid,
            expected_current_user=expected_current_user,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "login_path": self.login_path,
            "database": self.database,
            "expected_server_uuid": self.expected_server_uuid,
            "expected_current_user": self.expected_current_user,
        }


@dataclass(frozen=True)
class ExecutionRunner:
    executable: str
    timeout_seconds: int
    stop_on_error: bool = True

    @classmethod
    def from_dict(cls, raw: Mapping[str, Any]) -> "ExecutionRunner":
        location = "execution_profile.runner"
        document = _mapping(raw, location)
        _require_exact_keys(
            document,
            {"executable", "timeout_seconds", "stop_on_error"},
            location,
        )
        executable = _required_string(document, "executable", location)
        if document["executable"] != executable or any(
            ord(character) < 32 or ord(character) == 127
            for character in executable
        ):
            raise ContractValidationError(
                f"{location}.executable must be a literal executable name or path"
            )
        timeout_seconds = document["timeout_seconds"]
        if type(timeout_seconds) is not int or timeout_seconds <= 0:
            raise ContractValidationError(
                f"{location}.timeout_seconds must be a positive integer"
            )
        if document["stop_on_error"] is not True:
            raise ContractValidationError(
                f"{location}.stop_on_error must be true for formal execution"
            )
        return cls(
            executable=executable,
            timeout_seconds=timeout_seconds,
            stop_on_error=True,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "executable": self.executable,
            "timeout_seconds": self.timeout_seconds,
            "stop_on_error": True,
        }


@dataclass(frozen=True)
class ExecutionComparison:
    """The only formal comparison policy supported by the basic runner."""

    mode: str = "exact_text"

    @classmethod
    def from_dict(cls, raw: Mapping[str, Any]) -> "ExecutionComparison":
        location = "execution_profile.comparison"
        document = _mapping(raw, location)
        _require_exact_keys(document, {"mode", "normalization"}, location)
        if document["mode"] != "exact_text":
            raise ContractValidationError(
                f"{location}.mode must be exact_text"
            )
        normalization_location = f"{location}.normalization"
        normalization = _mapping(document["normalization"], normalization_location)
        _require_exact_keys(
            normalization,
            {
                "drop_line_patterns",
                "replacements",
                "strip_trailing_whitespace",
            },
            normalization_location,
        )
        if normalization["drop_line_patterns"] != []:
            raise ContractValidationError(
                f"{normalization_location}.drop_line_patterns must be empty"
            )
        if normalization["replacements"] != []:
            raise ContractValidationError(
                f"{normalization_location}.replacements must be empty"
            )
        if normalization["strip_trailing_whitespace"] is not False:
            raise ContractValidationError(
                f"{normalization_location}.strip_trailing_whitespace must be false"
            )
        return cls()

    def to_dict(self) -> dict[str, Any]:
        return {
            "mode": "exact_text",
            "normalization": {
                "drop_line_patterns": [],
                "replacements": [],
                "strip_trailing_whitespace": False,
            },
        }


@dataclass(frozen=True)
class ExecutionSecurityPolicy:
    credential_source: str = "external-mysql-login-path"
    persist_credentials: bool = False

    @classmethod
    def from_dict(cls, raw: Mapping[str, Any]) -> "ExecutionSecurityPolicy":
        location = "execution_profile.security"
        document = _mapping(raw, location)
        _require_exact_keys(
            document,
            {"credential_source", "persist_credentials"},
            location,
        )
        if document["credential_source"] != "external-mysql-login-path":
            raise ContractValidationError(
                f"{location}.credential_source must be external-mysql-login-path"
            )
        if document["persist_credentials"] is not False:
            raise ContractValidationError(
                f"{location}.persist_credentials must be false"
            )
        return cls()

    def to_dict(self) -> dict[str, Any]:
        return {
            "credential_source": "external-mysql-login-path",
            "persist_credentials": False,
        }


@dataclass(frozen=True)
class ExecutionProfile:
    """Immutable configuration for a formal MySQL patch differential run."""

    schema_version: int
    compatibility_target: str
    reference: ExecutionEndpoint
    dut: ExecutionEndpoint
    runner: ExecutionRunner
    comparison: ExecutionComparison
    security: ExecutionSecurityPolicy

    @property
    def target_version_num(self) -> int:
        return 80022 if self.compatibility_target.endswith("8.0.22") else 80041

    @classmethod
    def from_dict(cls, raw: Mapping[str, Any]) -> "ExecutionProfile":
        location = "execution_profile"
        document = _mapping(raw, location)
        _require_exact_keys(
            document,
            {
                "schema_version",
                "kind",
                "compatibility_target",
                "reference",
                "dut",
                "runner",
                "comparison",
                "security",
            },
            location,
        )
        schema_version = _schema_header(document, "execution_profile")
        if document["compatibility_target"] not in SUPPORTED_COMPATIBILITY_TARGETS:
            raise ContractValidationError(
                "execution_profile.compatibility_target must be mysql-community-8.0.22 "
                "or mysql-community-8.0.41"
            )
        reference = ExecutionEndpoint.from_dict(
            document["reference"],
            "execution_profile.reference",
        )
        dut = ExecutionEndpoint.from_dict(
            document["dut"],
            "execution_profile.dut",
        )
        if reference.login_path == dut.login_path:
            raise ContractValidationError(
                "execution_profile reference and DUT must use different login paths"
            )
        if reference.database != dut.database:
            raise ContractValidationError(
                "execution_profile reference and DUT database names must be identical"
            )
        if (
            reference.expected_server_uuid
            == dut.expected_server_uuid
        ):
            raise ContractValidationError(
                "execution_profile reference and DUT expected system identifiers "
                "must be different"
            )
        if reference.expected_current_user != dut.expected_current_user:
            raise ContractValidationError(
                "execution_profile reference and DUT expected current_user must be identical"
            )
        return cls(
            schema_version=schema_version,
            compatibility_target=document["compatibility_target"],
            reference=reference,
            dut=dut,
            runner=ExecutionRunner.from_dict(document["runner"]),
            comparison=ExecutionComparison.from_dict(document["comparison"]),
            security=ExecutionSecurityPolicy.from_dict(document["security"]),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "kind": "execution_profile",
            "compatibility_target": self.compatibility_target,
            "reference": self.reference.to_dict(),
            "dut": self.dut.to_dict(),
            "runner": self.runner.to_dict(),
            "comparison": self.comparison.to_dict(),
            "security": self.security.to_dict(),
        }


def execution_profile_sha256(profile: ExecutionProfile) -> str:
    """Hash the normalized semantic profile, independent of source YAML style."""

    encoded = json.dumps(
        profile.to_dict(),
        ensure_ascii=False,
        allow_nan=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def canonical_execution_profile_yaml(profile: ExecutionProfile) -> str:
    """Serialize the single canonical on-disk representation for run inputs."""

    return yaml.safe_dump(
        profile.to_dict(),
        allow_unicode=True,
        sort_keys=False,
    )


@dataclass(frozen=True)
class CoverageAxis:
    axis_id: str
    values: tuple[Any, ...]
    inventory_source: str
    coverage_mode: str
    inventory_count: int
    inventory_sha256: str
    description: Optional[str] = None
    derivation: Optional[str] = None
    source_locators: tuple[str, ...] = ()
    exclusion_policy: Optional[str] = None
    review_status: Optional[str] = None

    @classmethod
    def from_dict(cls, axis_id: str, raw: Mapping[str, Any]) -> "CoverageAxis":
        location = f"coverage_plan.axes.{axis_id}"
        _stable_id(axis_id, f"{location}.id")
        document = _mapping(raw, location)
        _require_allowed_keys(
            document,
            {
                "values",
                "inventory_source",
                "coverage_mode",
                "inventory_count",
                "inventory_sha256",
            },
            {
                "description",
                "derivation",
                "source_locators",
                "exclusion_policy",
                "review_status",
            },
            location,
        )
        values = tuple(_sequence(document.get("values"), f"{location}.values"))
        if not values:
            raise ContractValidationError(f"{location}.values must not be empty")
        for index, value in enumerate(values):
            if type(value) not in _SCALAR_TYPES:
                raise ContractValidationError(f"{location}.values[{index}] must be a YAML scalar")
        canonical_values = [(type(value).__name__, repr(value)) for value in values]
        if len(set(canonical_values)) != len(values):
            raise ContractValidationError(f"{location}.values contains duplicates")
        inventory_source = _required_string(document, "inventory_source", location)
        description = _optional_string(document, "description", location)
        derivation = _optional_string(document, "derivation", location)
        source_locators = _string_tuple(
            document.get("source_locators"),
            f"{location}.source_locators",
        )
        exclusion_policy = _optional_string(document, "exclusion_policy", location)
        review_status = _optional_string(document, "review_status", location)
        if inventory_source.startswith("inline:"):
            if not inventory_source.removeprefix("inline:").strip():
                raise ContractValidationError(
                    f"{location}.inventory_source inline source must have a name"
                )
            if (
                description is None
                or derivation is None
                or not source_locators
                or exclusion_policy is None
                or review_status not in ("source_derived", "semantic_reviewed")
            ):
                raise ContractValidationError(
                    f"{location} inline inventories require description, derivation, "
                    "non-empty source_locators, exclusion_policy, and "
                    "review_status=source_derived|semantic_reviewed"
                )
        else:
            if inventory_source.count("#") != 1:
                raise ContractValidationError(
                    f"{location}.inventory_source must use <path>#<selector>"
                )
            source_path, selector = inventory_source.split("#", 1)
            if not source_path.strip() or not selector.strip():
                raise ContractValidationError(
                    f"{location}.inventory_source must use non-empty <path>#<selector>"
                )
            if "\\" in source_path:
                raise ContractValidationError(
                    f"{location}.inventory_source path must use portable forward slashes"
                )
            portable_source = PurePosixPath(source_path)
            if portable_source.is_absolute() or ".." in portable_source.parts:
                raise ContractValidationError(
                    f"{location}.inventory_source path must be repository-relative; "
                    "paths outside inventory_root are forbidden"
                )
        coverage_mode = _required_string(document, "coverage_mode", location)
        if coverage_mode != "complete":
            raise ContractValidationError(f"{location}.coverage_mode must be complete")
        inventory_count = document.get("inventory_count")
        if type(inventory_count) is not int or inventory_count < 1:
            raise ContractValidationError(
                f"{location}.inventory_count must be a positive integer"
            )
        if inventory_count != len(values):
            raise ContractValidationError(
                f"{location}.inventory_count {inventory_count} does not match "
                f"the {len(values)} declared values"
            )
        inventory_sha256 = document.get("inventory_sha256")
        if not isinstance(inventory_sha256, str) or not _SHA256_PATTERN.fullmatch(
            inventory_sha256
        ):
            raise ContractValidationError(
                f"{location}.inventory_sha256 must be a 64-character lowercase SHA-256"
            )
        expected_sha256 = inventory_values_sha256(values)
        if inventory_sha256 != expected_sha256:
            raise ContractValidationError(
                f"{location}.inventory_sha256 does not match the declared values"
            )
        return cls(
            axis_id=axis_id,
            values=values,
            inventory_source=inventory_source,
            coverage_mode=coverage_mode,
            inventory_count=inventory_count,
            inventory_sha256=inventory_sha256,
            description=description,
            derivation=derivation,
            source_locators=source_locators,
            exclusion_policy=exclusion_policy,
            review_status=review_status,
        )

    def to_dict(self) -> dict[str, Any]:
        document: dict[str, Any] = {
            "values": list(self.values),
            "inventory_source": self.inventory_source,
            "coverage_mode": self.coverage_mode,
            "inventory_count": self.inventory_count,
            "inventory_sha256": self.inventory_sha256,
        }
        if self.description is not None:
            document["description"] = self.description
        if self.derivation is not None:
            document["derivation"] = self.derivation
        if self.source_locators:
            document["source_locators"] = list(self.source_locators)
        if self.exclusion_policy is not None:
            document["exclusion_policy"] = self.exclusion_policy
        if self.review_status is not None:
            document["review_status"] = self.review_status
        return document


@dataclass(frozen=True)
class ScopeDecision:
    scope_id: str
    status: str
    axes: tuple[str, ...] = ()
    reason: Optional[str] = None

    @property
    def axis(self) -> Optional[str]:
        return self.axes[0] if len(self.axes) == 1 else None

    @classmethod
    def from_dict(
        cls,
        scope_id: str,
        raw: Mapping[str, Any],
    ) -> "ScopeDecision":
        location = f"coverage_plan.scope_decisions.{scope_id}"
        document = _mapping(raw, location)
        _require_allowed_keys(document, {"status"}, {"axis", "axes", "reason"}, location)
        status = _required_string(document, "status", location)
        if status not in ("complete", "not_applicable"):
            raise ContractValidationError(
                f"{location}.status must be complete or not_applicable"
            )
        axis = _optional_string(document, "axis", location)
        axes = _stable_id_tuple(document.get("axes"), f"{location}.axes")
        if axis is not None and axes:
            raise ContractValidationError(
                f"{location} cannot declare both axis and axes"
            )
        normalized_axes = (axis,) if axis is not None else axes
        reason = _optional_string(document, "reason", location)
        if status == "complete":
            if not normalized_axes:
                raise ContractValidationError(
                    f"{location}.axis or axes is required when status is complete"
                )
            if reason is not None:
                raise ContractValidationError(
                    f"{location}.reason is not allowed when status is complete"
                )
        else:
            if reason is None:
                raise ContractValidationError(
                    f"{location}.reason is required when status is not_applicable"
                )
            if normalized_axes:
                raise ContractValidationError(
                    f"{location}.axis/axes is not allowed when status is not_applicable"
                )
        _validate_unique(normalized_axes, f"{scope_id} scope axis")
        return cls(
            scope_id=scope_id,
            status=status,
            axes=normalized_axes,
            reason=reason,
        )

    def to_dict(self) -> dict[str, Any]:
        document: dict[str, Any] = {"status": self.status}
        if len(self.axes) == 1:
            document["axis"] = self.axes[0]
        elif self.axes:
            document["axes"] = list(self.axes)
        if self.reason is not None:
            document["reason"] = self.reason
        return document


@dataclass(frozen=True)
class RiskDecision:
    risk_id: str
    status: str
    axes: tuple[str, ...] = ()
    test_points: tuple[str, ...] = ()
    reason: Optional[str] = None
    execution_harness: Optional[str] = None

    @classmethod
    def from_dict(cls, risk_id: str, raw: Mapping[str, Any]) -> "RiskDecision":
        location = f"coverage_plan.risk_decisions.{risk_id}"
        _stable_id(risk_id, f"{location}.id")
        document = _mapping(raw, location)
        _require_allowed_keys(
            document,
            {"status"},
            {"axes", "test_points", "reason", "execution_harness"},
            location,
        )
        status = _required_string(document, "status", location)
        if status not in ("covered", "not_applicable"):
            raise ContractValidationError(
                f"{location}.status must be covered or not_applicable"
            )
        axes = _stable_id_tuple(document.get("axes"), f"{location}.axes")
        test_points = _stable_id_tuple(
            document.get("test_points"),
            f"{location}.test_points",
        )
        reason = _optional_string(document, "reason", location)
        execution_harness = _optional_string(
            document,
            "execution_harness",
            location,
        )
        if execution_harness is not None:
            _stable_id(execution_harness, f"{location}.execution_harness")
        if status == "covered":
            if not axes or not test_points:
                raise ContractValidationError(
                    f"{location} covered risks require non-empty axes and test_points"
                )
        else:
            if reason is None:
                raise ContractValidationError(
                    f"{location}.reason is required when status is not_applicable"
                )
            if axes or test_points or execution_harness is not None:
                raise ContractValidationError(
                    f"{location} not_applicable risks cannot declare axes, test_points, or execution_harness"
                )
        _validate_unique(axes, f"{risk_id} risk axis")
        _validate_unique(test_points, f"{risk_id} risk test point")
        return cls(
            risk_id=risk_id,
            status=status,
            axes=axes,
            test_points=test_points,
            reason=reason,
            execution_harness=execution_harness,
        )

    def to_dict(self) -> dict[str, Any]:
        document: dict[str, Any] = {"status": self.status}
        if self.axes:
            document["axes"] = list(self.axes)
        if self.test_points:
            document["test_points"] = list(self.test_points)
        if self.reason is not None:
            document["reason"] = self.reason
        if self.execution_harness is not None:
            document["execution_harness"] = self.execution_harness
        return document


@dataclass(frozen=True)
class CoverageClassificationRule:
    when: Mapping[str, Any]
    outcome: str
    reason: Optional[str] = None

    @classmethod
    def from_dict(
        cls,
        raw: Mapping[str, Any],
        location: str = "classification_rule",
    ) -> "CoverageClassificationRule":
        document = _mapping(raw, location)
        _require_allowed_keys(document, {"when", "outcome"}, {"reason"}, location)
        outcome = _required_string(document, "outcome", location)
        if outcome not in COVERAGE_OUTCOMES:
            raise ContractValidationError(
                f"{location}.outcome must be one of {', '.join(COVERAGE_OUTCOMES)}"
            )
        when = _mapping(document.get("when") or {}, f"{location}.when")
        if not when:
            raise ContractValidationError(f"{location}.when must not be empty")
        for axis_id, criterion in when.items():
            _stable_id(axis_id, f"{location}.when axis id")
            candidates = criterion if isinstance(criterion, list) else [criterion]
            if not candidates:
                raise ContractValidationError(f"{location}.when.{axis_id} must not be empty")
            if any(type(item) not in _SCALAR_TYPES for item in candidates):
                raise ContractValidationError(f"{location}.when.{axis_id} must contain YAML scalars")
        return cls(
            when=when,
            outcome=outcome,
            reason=_optional_string(document, "reason", location),
        )

    def to_dict(self) -> dict[str, Any]:
        document: dict[str, Any] = {"when": dict(self.when), "outcome": self.outcome}
        if self.reason is not None:
            document["reason"] = self.reason
        return document


def _validate_case_execution_route(
    execution_profile: str,
    execution_harness: Optional[str],
    location: str,
) -> None:
    if execution_profile not in CASE_EXECUTION_PROFILES:
        raise ContractValidationError(
            f"{location}.execution_profile must be basic_mysql or external_isolated"
        )
    if execution_profile == "basic_mysql" and execution_harness is not None:
        raise ContractValidationError(
            f"{location} basic_mysql route must not declare execution_harness"
        )
    if execution_profile == "external_isolated" and (
        execution_harness is None
        or re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]*", execution_harness) is None
    ):
        raise ContractValidationError(
            f"{location} external_isolated route requires a stable execution_harness id"
        )


@dataclass(frozen=True)
class ExecutionRoutingRule:
    when: Mapping[str, Any]
    execution_profile: str
    execution_harness: Optional[str] = None

    @classmethod
    def from_dict(
        cls,
        raw: Mapping[str, Any],
        location: str = "execution_rule",
    ) -> "ExecutionRoutingRule":
        document = _mapping(raw, location)
        _require_allowed_keys(
            document,
            {"when", "execution_profile"},
            {"execution_harness"},
            location,
        )
        when = _mapping(document.get("when") or {}, f"{location}.when")
        if not when:
            raise ContractValidationError(f"{location}.when must not be empty")
        for axis_id, criterion in when.items():
            _stable_id(axis_id, f"{location}.when axis id")
            candidates = criterion if isinstance(criterion, list) else [criterion]
            if not candidates or any(type(item) not in _SCALAR_TYPES for item in candidates):
                raise ContractValidationError(
                    f"{location}.when.{axis_id} must contain YAML scalars"
                )
        execution_profile = _required_string(document, "execution_profile", location)
        execution_harness = _optional_string(document, "execution_harness", location)
        _validate_case_execution_route(
            execution_profile,
            execution_harness,
            location,
        )
        return cls(when, execution_profile, execution_harness)

    def to_dict(self) -> dict[str, Any]:
        document: dict[str, Any] = {
            "when": dict(self.when),
            "execution_profile": self.execution_profile,
        }
        if self.execution_harness is not None:
            document["execution_harness"] = self.execution_harness
        return document


@dataclass(frozen=True)
class CoverageExpectedCounts:
    """Frozen outcome accounting for one feature-level coverage contract."""

    total: int
    success: int
    expected_failure: int
    justified_na: int

    def __post_init__(self) -> None:
        counts = {
            "total": self.total,
            "success": self.success,
            "expected_failure": self.expected_failure,
            "justified_na": self.justified_na,
        }
        for key, value in counts.items():
            if type(value) is not int or value < 0:
                raise ContractValidationError(
                    f"coverage_contract.expected_counts.{key} must be a non-negative integer"
                )
        if self.total < 1:
            raise ContractValidationError(
                "coverage_contract.expected_counts.total must be positive; "
                "zero is not a frozen final count"
            )
        if self.total != self.success + self.expected_failure + self.justified_na:
            raise ContractValidationError(
                "coverage_contract.expected_counts.total must equal success + "
                "expected_failure + justified_na"
            )

    @classmethod
    def from_dict(
        cls,
        raw: Mapping[str, Any],
        location: str = "coverage_contract.expected_counts",
    ) -> "CoverageExpectedCounts":
        document = _mapping(raw, location)
        _require_exact_keys(
            document,
            {"total", "success", "expected_failure", "justified_na"},
            location,
        )
        counts: dict[str, int] = {}
        for key in ("total", "success", "expected_failure", "justified_na"):
            value = document.get(key)
            if type(value) is not int or value < 0:
                raise ContractValidationError(
                    f"{location}.{key} must be a non-negative integer"
                )
            counts[key] = value
        if counts["total"] < 1:
            raise ContractValidationError(
                f"{location}.total must be positive; zero is not a frozen final count"
            )
        classified = (
            counts["success"]
            + counts["expected_failure"]
            + counts["justified_na"]
        )
        if counts["total"] != classified:
            raise ContractValidationError(
                f"{location}.total must equal success + expected_failure + justified_na"
            )
        return cls(**counts)

    def to_dict(self) -> dict[str, int]:
        return {
            "total": self.total,
            "success": self.success,
            "expected_failure": self.expected_failure,
            "justified_na": self.justified_na,
        }


@dataclass(frozen=True)
class CoverageContract:
    """An explicit completeness claim attached to a new feature test point.

    Legacy v1 points omit this object.  Its absence intentionally preserves the
    old expansion semantics and makes no new mathematical coverage claim.
    """

    combination_policy: str
    primary_axes: tuple[str, ...]
    condition_axes: tuple[str, ...]
    expected_counts: CoverageExpectedCounts

    def __post_init__(self) -> None:
        allowed_policies = {
            "full_cross",
            "conditional_cross",
            "boundary",
            "negative",
            "representative",
            "pairwise",
        }
        if (
            not isinstance(self.combination_policy, str)
            or self.combination_policy not in allowed_policies
        ):
            raise ContractValidationError(
                "coverage_contract.combination_policy must be one of "
                + ", ".join(sorted(allowed_policies))
            )
        if type(self.primary_axes) is not tuple or type(self.condition_axes) is not tuple:
            raise ContractValidationError(
                "coverage_contract primary_axes and condition_axes must be immutable tuples"
            )
        if not self.primary_axes:
            raise ContractValidationError(
                "coverage_contract.primary_axes must not be empty"
            )
        for index, axis_id in enumerate(self.primary_axes):
            _stable_id(axis_id, f"coverage_contract.primary_axes[{index}]")
        for index, axis_id in enumerate(self.condition_axes):
            _stable_id(axis_id, f"coverage_contract.condition_axes[{index}]")
        _validate_unique(self.primary_axes, "coverage-contract primary axis")
        _validate_unique(self.condition_axes, "coverage-contract condition axis")
        overlap = sorted(set(self.primary_axes) & set(self.condition_axes))
        if overlap:
            raise ContractValidationError(
                "coverage_contract primary_axes and condition_axes overlap: "
                + ", ".join(overlap)
            )
        if self.combination_policy == "conditional_cross" and not self.condition_axes:
            raise ContractValidationError(
                "coverage_contract.condition_axes must not be empty for conditional_cross"
            )
        if self.combination_policy == "full_cross" and self.condition_axes:
            raise ContractValidationError(
                "coverage_contract.condition_axes must be empty for full_cross"
            )
        if not isinstance(self.expected_counts, CoverageExpectedCounts):
            raise ContractValidationError(
                "coverage_contract.expected_counts must be CoverageExpectedCounts"
            )

    @classmethod
    def from_dict(
        cls,
        raw: Mapping[str, Any],
        location: str = "coverage_contract",
    ) -> "CoverageContract":
        document = _mapping(raw, location)
        _require_exact_keys(
            document,
            {"combination_policy", "primary_axes", "condition_axes", "expected_counts"},
            location,
        )
        combination_policy = _required_string(document, "combination_policy", location)
        allowed_policies = {
            "full_cross",
            "conditional_cross",
            "boundary",
            "negative",
            "representative",
            "pairwise",
        }
        if combination_policy not in allowed_policies:
            raise ContractValidationError(
                f"{location}.combination_policy must be one of "
                + ", ".join(sorted(allowed_policies))
            )
        primary_axes = _stable_id_tuple(
            document.get("primary_axes"), f"{location}.primary_axes"
        )
        condition_axes = _stable_id_tuple(
            document.get("condition_axes"), f"{location}.condition_axes"
        )
        if not primary_axes:
            raise ContractValidationError(f"{location}.primary_axes must not be empty")
        _validate_unique(primary_axes, "coverage-contract primary axis")
        _validate_unique(condition_axes, "coverage-contract condition axis")
        overlap = sorted(set(primary_axes) & set(condition_axes))
        if overlap:
            raise ContractValidationError(
                f"{location} primary_axes and condition_axes overlap: " + ", ".join(overlap)
            )
        if combination_policy == "conditional_cross" and not condition_axes:
            raise ContractValidationError(
                f"{location}.condition_axes must not be empty for conditional_cross"
            )
        if combination_policy == "full_cross" and condition_axes:
            raise ContractValidationError(
                f"{location}.condition_axes must be empty for full_cross"
            )
        return cls(
            combination_policy=combination_policy,
            primary_axes=primary_axes,
            condition_axes=condition_axes,
            expected_counts=CoverageExpectedCounts.from_dict(
                document.get("expected_counts"), f"{location}.expected_counts"
            ),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "combination_policy": self.combination_policy,
            "primary_axes": list(self.primary_axes),
            "condition_axes": list(self.condition_axes),
            "expected_counts": self.expected_counts.to_dict(),
        }


@dataclass(frozen=True)
class TestPoint:
    test_point_id: str
    title: str
    requirement_ids: tuple[str, ...]
    core_axes: tuple[str, ...]
    dependencies: tuple[str, ...]
    classification_rules: tuple[CoverageClassificationRule, ...] = ()
    execution_rules: tuple[ExecutionRoutingRule, ...] = ()
    default_outcome: Optional[str] = None
    default_reason: Optional[str] = None
    description: Optional[str] = None
    default_execution_profile: str = "basic_mysql"
    default_execution_harness: Optional[str] = None
    coverage_contract: Optional[CoverageContract] = None

    @classmethod
    def from_dict(cls, raw: Mapping[str, Any], location: str = "test_point") -> "TestPoint":
        document = _mapping(raw, location)
        _require_allowed_keys(
            document,
            {"id", "title", "requirement_ids", "core_axes", "dependencies"},
            {
                "classification_rules",
                "execution_rules",
                "default_outcome",
                "default_reason",
                "description",
                "default_execution_profile",
                "default_execution_harness",
                "coverage_contract",
            },
            location,
        )
        rules = tuple(
            CoverageClassificationRule.from_dict(item, f"{location}.classification_rules[{index}]")
            for index, item in enumerate(
                _sequence(document.get("classification_rules"), f"{location}.classification_rules")
            )
        )
        default_outcome = _optional_string(document, "default_outcome", location)
        if default_outcome is not None and default_outcome not in COVERAGE_OUTCOMES:
            raise ContractValidationError(
                f"{location}.default_outcome must be one of {', '.join(COVERAGE_OUTCOMES)}"
            )
        execution_rules = tuple(
            ExecutionRoutingRule.from_dict(
                item,
                f"{location}.execution_rules[{index}]",
            )
            for index, item in enumerate(
                _sequence(document.get("execution_rules"), f"{location}.execution_rules")
            )
        )
        default_execution_profile = document.get(
            "default_execution_profile",
            "basic_mysql",
        )
        if not isinstance(default_execution_profile, str):
            raise ContractValidationError(
                f"{location}.default_execution_profile must be a string"
            )
        default_execution_harness = _optional_string(
            document,
            "default_execution_harness",
            location,
        )
        _validate_case_execution_route(
            default_execution_profile,
            default_execution_harness,
            location,
        )
        return cls(
            test_point_id=_stable_id(document.get("id"), f"{location}.id"),
            title=_required_string(document, "title", location),
            requirement_ids=_stable_id_tuple(
                document.get("requirement_ids"), f"{location}.requirement_ids"
            ),
            core_axes=_stable_id_tuple(document.get("core_axes"), f"{location}.core_axes"),
            dependencies=_stable_id_tuple(
                document.get("dependencies"), f"{location}.dependencies"
            ),
            classification_rules=rules,
            execution_rules=execution_rules,
            default_outcome=default_outcome,
            default_reason=_optional_string(document, "default_reason", location),
            description=_optional_string(document, "description", location),
            default_execution_profile=default_execution_profile,
            default_execution_harness=default_execution_harness,
            coverage_contract=(
                CoverageContract.from_dict(
                    document["coverage_contract"],
                    f"{location}.coverage_contract",
                )
                if "coverage_contract" in document
                else None
            ),
        )

    def to_dict(self) -> dict[str, Any]:
        document: dict[str, Any] = {
            "id": self.test_point_id,
            "title": self.title,
            "requirement_ids": list(self.requirement_ids),
            "core_axes": list(self.core_axes),
            "dependencies": list(self.dependencies),
        }
        if self.classification_rules:
            document["classification_rules"] = [rule.to_dict() for rule in self.classification_rules]
        if self.execution_rules:
            document["execution_rules"] = [rule.to_dict() for rule in self.execution_rules]
        if self.default_execution_profile != "basic_mysql":
            document["default_execution_profile"] = self.default_execution_profile
        if self.default_execution_harness is not None:
            document["default_execution_harness"] = self.default_execution_harness
        if self.default_outcome is not None:
            document["default_outcome"] = self.default_outcome
        if self.default_reason is not None:
            document["default_reason"] = self.default_reason
        if self.description is not None:
            document["description"] = self.description
        if self.coverage_contract is not None:
            document["coverage_contract"] = self.coverage_contract.to_dict()
        return document


@dataclass(frozen=True)
class CoveragePlan:
    schema_version: int
    plan_id: str
    feature_id: str
    axes: Mapping[str, CoverageAxis]
    scope_decisions: Mapping[str, ScopeDecision]
    risk_decisions: Mapping[str, RiskDecision]
    test_points: tuple[TestPoint, ...]
    metadata: Mapping[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, raw: Mapping[str, Any]) -> "CoveragePlan":
        document = _mapping(raw, "coverage_plan")
        _require_allowed_keys(
            document,
            {
                "schema_version",
                "kind",
                "plan_id",
                "feature_id",
                "axes",
                "scope_decisions",
                "risk_decisions",
                "test_points",
            },
            {"metadata"},
            "coverage_plan",
        )
        schema_version = _schema_header(document, "coverage_plan")
        axes_document = _mapping(document.get("axes"), "coverage_plan.axes")
        if not axes_document:
            raise ContractValidationError("coverage_plan.axes must not be empty")
        axes = {
            axis_id: CoverageAxis.from_dict(axis_id, axis_document)
            for axis_id, axis_document in axes_document.items()
        }
        point_documents = _sequence(document.get("test_points"), "coverage_plan.test_points")
        if not point_documents:
            raise ContractValidationError("coverage_plan.test_points must not be empty")
        test_points = tuple(
            TestPoint.from_dict(item, f"coverage_plan.test_points[{index}]")
            for index, item in enumerate(point_documents)
        )
        _validate_unique((item.test_point_id for item in test_points), "test point id")
        scope_documents = _mapping(
            document.get("scope_decisions"),
            "coverage_plan.scope_decisions",
        )
        expected_scopes = set(REQUIRED_SCOPE_DECISIONS)
        actual_scopes = set(scope_documents)
        if actual_scopes != expected_scopes:
            details = []
            missing = sorted(expected_scopes - actual_scopes)
            unexpected = sorted(actual_scopes - expected_scopes)
            if missing:
                details.append("missing " + ", ".join(missing))
            if unexpected:
                details.append("unexpected " + ", ".join(unexpected))
            raise ContractValidationError(
                "coverage_plan.scope_decisions must contain exactly object, relation, "
                "table, column_type (" + "; ".join(details) + ")"
            )
        scope_decisions = {
            scope_id: ScopeDecision.from_dict(scope_id, scope_documents[scope_id])
            for scope_id in REQUIRED_SCOPE_DECISIONS
        }
        risk_documents = _mapping(
            document.get("risk_decisions"),
            "coverage_plan.risk_decisions",
        )
        expected_risks = set(REQUIRED_RISK_DECISIONS)
        actual_risks = set(risk_documents)
        missing_risks = sorted(expected_risks - actual_risks)
        if missing_risks:
            raise ContractValidationError(
                "coverage_plan.risk_decisions must contain the complete mandatory "
                "risk review set (missing " + ", ".join(missing_risks) + ")"
            )
        risk_decisions = {
            risk_id: RiskDecision.from_dict(risk_id, risk_documents[risk_id])
            for risk_id in (
                *REQUIRED_RISK_DECISIONS,
                *(key for key in risk_documents if key not in expected_risks),
            )
        }
        return cls(
            schema_version=schema_version,
            plan_id=_stable_id(document.get("plan_id"), "coverage_plan.plan_id"),
            feature_id=_stable_id(document.get("feature_id"), "coverage_plan.feature_id"),
            axes=axes,
            scope_decisions=scope_decisions,
            risk_decisions=risk_decisions,
            test_points=test_points,
            metadata=_json_mapping(document.get("metadata") or {}, "coverage_plan.metadata"),
        )

    def to_dict(self) -> dict[str, Any]:
        document: dict[str, Any] = {
            "schema_version": self.schema_version,
            "kind": "coverage_plan",
            "plan_id": self.plan_id,
            "feature_id": self.feature_id,
            "axes": {axis_id: axis.to_dict() for axis_id, axis in self.axes.items()},
            "scope_decisions": {
                scope_id: self.scope_decisions[scope_id].to_dict()
                for scope_id in REQUIRED_SCOPE_DECISIONS
            },
            "risk_decisions": {
                risk_id: decision.to_dict()
                for risk_id, decision in self.risk_decisions.items()
            },
            "test_points": [point.to_dict() for point in self.test_points],
        }
        if self.metadata:
            document["metadata"] = dict(self.metadata)
        return document


@dataclass(frozen=True)
class CaseManifest:
    schema_version: int
    case_id: str
    test_point_id: str
    obligation_id: str
    outcome: str
    sql_files: tuple[str, ...]
    sql_sha256: str
    execution_profile: str
    execution_harness: Optional[str]
    comparison: Mapping[str, Any]
    cleanup: Mapping[str, Any]
    metadata: Mapping[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, raw: Mapping[str, Any]) -> "CaseManifest":
        document = _mapping(raw, "case_manifest")
        _require_allowed_keys(
            document,
            {
                "schema_version",
                "kind",
                "case_id",
                "test_point_id",
                "obligation_id",
                "outcome",
                "sql_files",
                "sql_sha256",
                "execution_profile",
                "comparison",
                "cleanup",
            },
            {"execution_harness", "metadata"},
            "case_manifest",
        )
        schema_version = _schema_header(document, "case_manifest")
        outcome = _required_string(document, "outcome", "case_manifest")
        if outcome not in ("success", "expected_failure"):
            raise ContractValidationError(
                "case_manifest.outcome must be success or expected_failure; "
                "justified_na obligations do not generate cases"
            )
        sql_files = _string_tuple(document.get("sql_files"), "case_manifest.sql_files")
        if len(sql_files) != 1:
            raise ContractValidationError(
                "case_manifest.sql_files must contain exactly one deterministic SQL program"
            )
        for sql_file in sql_files:
            if "\\" in sql_file:
                raise ContractValidationError(
                    f"case_manifest.sql_files contains a non-portable path: {sql_file}"
                )
            sql_path = PurePosixPath(sql_file)
            if sql_path.is_absolute() or ".." in sql_path.parts:
                raise ContractValidationError(
                    f"case_manifest.sql_files must stay under the run root: {sql_file}"
                )
        sql_sha256 = document.get("sql_sha256")
        if not isinstance(sql_sha256, str) or not _SHA256_PATTERN.fullmatch(sql_sha256):
            raise ContractValidationError(
                "case_manifest.sql_sha256 must be the 64-character lowercase SHA-256 "
                "of its one SQL program"
            )
        execution_profile = _required_string(
            document,
            "execution_profile",
            "case_manifest",
        )
        execution_harness = _optional_string(
            document,
            "execution_harness",
            "case_manifest",
        )
        _validate_case_execution_route(
            execution_profile,
            execution_harness,
            "case_manifest",
        )
        comparison = _json_mapping(document.get("comparison") or {}, "case_manifest.comparison")
        cleanup = _json_mapping(document.get("cleanup") or {}, "case_manifest.cleanup")
        mode = _required_string(comparison, "mode", "case_manifest.comparison")
        if mode != "exact_text":
            raise ContractValidationError(
                "case_manifest.comparison.mode must be exact_text for formal MySQL compatibility cases"
            )
        oracle = _required_string(comparison, "oracle", "case_manifest.comparison")
        if oracle not in {
            "upstream-mysql-community-8.0.22",
            "upstream-mysql-community-8.0.41",
        }:
            raise ContractValidationError(
                "case_manifest.comparison.oracle must name an exact supported upstream MySQL edition"
            )
        if comparison.get("require_identical") is not True:
            raise ContractValidationError(
                "case_manifest.comparison.require_identical must be true"
            )
        if comparison.get("normalization") is not None:
            raise ContractValidationError(
                "exact_text comparison must not declare normalization rules"
            )
        expected_sqlstate = comparison.get("expected_sqlstate")
        if outcome == "expected_failure":
            if (
                not isinstance(expected_sqlstate, str)
                or not re.fullmatch(r"[0-9A-Z]{5}", expected_sqlstate)
            ):
                raise ContractValidationError(
                    "expected_failure case_manifest.comparison.expected_sqlstate "
                    "must be a five-character SQLSTATE"
                )
        elif expected_sqlstate is not None:
            raise ContractValidationError(
                "success case_manifest must not declare expected_sqlstate"
            )
        if cleanup.get("required") is not True:
            raise ContractValidationError("case_manifest.cleanup.required must be true")
        if cleanup.get("idempotent") is not True:
            raise ContractValidationError("case_manifest.cleanup.idempotent must be true")
        comparison_expected = {"mode", "oracle", "require_identical"}
        if outcome == "expected_failure":
            comparison_expected.add("expected_sqlstate")
        _require_exact_keys(comparison, comparison_expected, "case_manifest.comparison")
        _require_exact_keys(cleanup, {"required", "idempotent"}, "case_manifest.cleanup")
        return cls(
            schema_version=schema_version,
            case_id=_stable_id(document.get("case_id"), "case_manifest.case_id"),
            test_point_id=_stable_id(
                document.get("test_point_id"), "case_manifest.test_point_id"
            ),
            obligation_id=_stable_id(
                document.get("obligation_id"), "case_manifest.obligation_id"
            ),
            outcome=outcome,
            sql_files=sql_files,
            sql_sha256=sql_sha256,
            execution_profile=execution_profile,
            execution_harness=execution_harness,
            comparison=comparison,
            cleanup=cleanup,
            metadata=_json_mapping(document.get("metadata") or {}, "case_manifest.metadata"),
        )

    def to_dict(self) -> dict[str, Any]:
        document: dict[str, Any] = {
            "schema_version": self.schema_version,
            "kind": "case_manifest",
            "case_id": self.case_id,
            "test_point_id": self.test_point_id,
            "obligation_id": self.obligation_id,
            "outcome": self.outcome,
            "sql_files": list(self.sql_files),
            "sql_sha256": self.sql_sha256,
            "execution_profile": self.execution_profile,
            "comparison": dict(self.comparison),
            "cleanup": dict(self.cleanup),
        }
        if self.metadata:
            document["metadata"] = dict(self.metadata)
        if self.execution_harness is not None:
            document["execution_harness"] = self.execution_harness
        return document


def _load_yaml_mapping(path: Union[str, Path]) -> dict[str, Any]:
    source = Path(path)
    try:
        loaded = yaml.load(
            source.read_text(encoding="utf-8"),
            Loader=_UniqueKeySafeLoader,
        )
    except OSError as exc:
        raise ContractValidationError(f"cannot read YAML contract {source}: {exc}") from exc
    except yaml.YAMLError as exc:
        raise ContractValidationError(f"invalid YAML contract {source}: {exc}") from exc
    if not isinstance(loaded, Mapping):
        raise ContractValidationError("YAML root must be a mapping")
    return _mapping(loaded, "YAML root")


def verify_feature_source(
    manifest: FeatureManifest,
    manifest_path: Union[str, Path],
    source_root: Optional[Union[str, Path]] = None,
) -> Path:
    """Verify the preserved feature document named by a manifest.

    Source paths are relative to the manifest directory by default.  Callers
    may provide an explicit source root when a run-root-relative layout is
    preferred.  Containment and the declared SHA-256 are both fail-closed.
    """

    manifest_file = Path(manifest_path).expanduser().resolve(strict=True)
    root_candidate = (
        Path(source_root).expanduser()
        if source_root is not None
        else manifest_file.parent
    )
    root = root_candidate.resolve(strict=True)
    if not root.is_dir():
        raise ContractValidationError(f"feature source root is not a directory: {root}")
    candidate = root / Path(*PurePosixPath(str(manifest.source["path"])).parts)
    try:
        resolved = candidate.resolve(strict=True)
        resolved.relative_to(root)
    except FileNotFoundError as exc:
        raise ContractValidationError(
            f"feature source does not exist: {manifest.source['path']}"
        ) from exc
    except (OSError, RuntimeError) as exc:
        raise ContractValidationError(
            f"cannot resolve feature source {manifest.source['path']}: {exc}"
        ) from exc
    except ValueError as exc:
        raise ContractValidationError(
            f"feature source escapes its source root: {manifest.source['path']}"
        ) from exc
    if not resolved.is_file():
        raise ContractValidationError(f"feature source is not a file: {resolved}")
    digest = hashlib.sha256()
    try:
        with resolved.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
    except OSError as exc:
        raise ContractValidationError(f"cannot read feature source {resolved}: {exc}") from exc
    expected = str(manifest.source["sha256"])
    actual = digest.hexdigest()
    if actual != expected:
        raise ContractValidationError(
            f"feature source SHA-256 mismatch: declared {expected}, actual {actual}"
        )
    return resolved


def load_feature_manifest(
    path: Union[str, Path],
    *,
    verify_source: bool = False,
    source_root: Optional[Union[str, Path]] = None,
) -> FeatureManifest:
    manifest = FeatureManifest.from_dict(_load_yaml_mapping(path))
    if verify_source:
        verify_feature_source(manifest, path, source_root=source_root)
    return manifest


def load_execution_profile(path: Union[str, Path]) -> ExecutionProfile:
    return ExecutionProfile.from_dict(_load_yaml_mapping(path))


def load_coverage_plan(
    path: Union[str, Path],
    manifest: Optional[FeatureManifest] = None,
    inventory_root: Optional[Union[str, Path]] = None,
) -> CoveragePlan:
    plan = CoveragePlan.from_dict(_load_yaml_mapping(path))
    # Local import avoids making the data model depend on the graph validator.
    from .feature_plan import validate_coverage_plan

    validate_coverage_plan(plan, manifest=manifest)
    if inventory_root is not None:
        from .inventory import verify_inventory_sources

        verify_inventory_sources(plan, inventory_root)
    return plan


def load_case_manifest(path: Union[str, Path]) -> CaseManifest:
    return CaseManifest.from_dict(_load_yaml_mapping(path))


__all__ = [
    "COVERAGE_OUTCOMES",
    "CASE_EXECUTION_PROFILES",
    "REQUIRED_SCOPE_DECISIONS",
    "REQUIRED_RISK_DECISIONS",
    "CANONICAL_SCOPE_SELECTORS",
    "CANONICAL_SCOPE_SOURCE_GROUPS",
    "CANONICAL_SCOPE_SNAPSHOTS",
    "ContractValidationError",
    "inventory_values_sha256",
    "inventory_value_equal",
    "verify_feature_source",
    "FeatureRequirement",
    "FeatureManifest",
    "ExecutionEndpoint",
    "ExecutionRunner",
    "ExecutionComparison",
    "ExecutionSecurityPolicy",
    "ExecutionProfile",
    "execution_profile_sha256",
    "canonical_execution_profile_yaml",
    "CoverageAxis",
    "ScopeDecision",
    "RiskDecision",
    "CoverageClassificationRule",
    "ExecutionRoutingRule",
    "CoverageExpectedCounts",
    "CoverageContract",
    "TestPoint",
    "CoveragePlan",
    "CaseManifest",
    "load_feature_manifest",
    "load_execution_profile",
    "load_coverage_plan",
    "load_case_manifest",
]
