class CoverageV2Error(ValueError):
    """Base class for fail-closed coverage V2 errors."""


class CoverageV2ContractError(CoverageV2Error):
    """Raised when canonical or contract-shaped data is invalid."""


class CoverageV2ArtifactError(CoverageV2Error):
    """Raised when an artifact or declared predecessor graph is invalid."""


class CoverageV2SchemaError(CoverageV2ArtifactError):
    """Raised when an artifact or schema violates its strict kind contract."""


class CoverageV2InputLockError(CoverageV2ArtifactError):
    """Raised when an input lock cannot be frozen or verified from current bytes."""


class CoverageV2RevisionError(CoverageV2ArtifactError):
    """Raised when a V2 revision or current pointer violates immutability."""


class CoverageV2StateError(CoverageV2ArtifactError):
    """Raised when a V2 planning or runtime state transition is not proven."""


class CoverageV2InventoryError(CoverageV2ArtifactError):
    """Raised when the canonical statement inventory cannot be reproduced."""
