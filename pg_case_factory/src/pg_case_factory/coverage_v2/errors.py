class CoverageV2Error(ValueError):
    """Base class for fail-closed coverage V2 errors."""


class CoverageV2ContractError(CoverageV2Error):
    """Raised when canonical or contract-shaped data is invalid."""


class CoverageV2ArtifactError(CoverageV2Error):
    """Raised when an artifact or declared predecessor graph is invalid."""
