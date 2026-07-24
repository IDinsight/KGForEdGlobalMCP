"""This module contains typed domain exceptions for stable public error translation."""

# Standard Library
from collections.abc import Mapping
from types import MappingProxyType
from typing import ClassVar


class KGFEGMCPError(Exception):
    """Base exception for expected backend domain failures."""

    error_code: ClassVar[str] = "kgfegmcp_error"

    def __init__(
        self, message: str, *, details: Mapping[str, object] | None = None
    ) -> None:
        """Initialize a stable domain error.

        Parameters
        ----------
        message
            Actionable public message suitable for later MCP error translation.
        details
            Optional internal structured details that must not be exposed blindly.

        Raises
        ------
        ValueError
            If ``message`` is empty.
        """

        normalized_message = message.strip()

        if not normalized_message:
            raise ValueError("Domain error messages must be non-empty.")

        super().__init__(normalized_message)
        self.details = MappingProxyType(dict(details or {}))
        self.message = normalized_message

    def public_payload(self) -> dict[str, str]:
        """Return the stable public error representation.

        Returns
        -------
        dict[str, str]
            Error code and actionable public message.
        """

        return {"code": self.error_code, "message": self.message}


class AlignmentNotFoundError(KGFEGMCPError):
    """Raised when a requested derived alignment cannot be found."""

    error_code = "alignment_not_found"


class AmbiguousFrameworkError(KGFEGMCPError):
    """Raised when a framework request resolves to multiple snapshots."""

    error_code = "ambiguous_framework"


class AmbiguousGraphNodeError(KGFEGMCPError):
    """Raised when an exact identifier resolves to several graph nodes."""

    error_code = "ambiguous_graph_node"


class CapabilityUnavailableError(KGFEGMCPError):
    """Raised when a selected package does not provide a requested capability."""

    error_code = "capability_unavailable"


class CatalogError(KGFEGMCPError):
    """Raised for catalog loading, validation, or lookup failures."""

    error_code = "catalog_error"


class ConfigurationError(KGFEGMCPError):
    """Raised when application settings cannot be resolved safely."""

    error_code = "configuration_error"


class DeliveryPropertyDecodingError(KGFEGMCPError):
    """Raised when a string-encoded delivery property cannot be decoded."""

    error_code = "delivery_property_decoding_error"


class FrameworkNotFoundError(KGFEGMCPError):
    """Raised when a requested framework or snapshot is unavailable."""

    error_code = "framework_not_found"


class GraphNodeNotFoundError(KGFEGMCPError):
    """Raised when a requested graph node identifier cannot be resolved."""

    error_code = "graph_node_not_found"


class InvalidComparisonSelectionError(KGFEGMCPError):
    """Raised when cross-framework selectors do not form a valid exact selection."""

    error_code = "invalid_comparison_selection"


class InvalidCursorError(KGFEGMCPError):
    """Raised when a pagination cursor is malformed or no longer valid."""

    error_code = "invalid_cursor"


class JSONLParsingError(KGFEGMCPError):
    """Raised when a JSONL record cannot be read or validated as a wire envelope."""

    error_code = "jsonl_parsing_error"


class ManifestBuildError(KGFEGMCPError):
    """Raised when a pending graph-package manifest cannot be built safely."""

    error_code = "manifest_build_error"


class PackageValidationError(KGFEGMCPError):
    """Raised when a graph package fails deterministic validation."""

    error_code = "package_validation_error"


class ProfileValidationError(KGFEGMCPError):
    """Raised when a curriculum interpretation profile is invalid."""

    error_code = "profile_validation_error"


class PromptAccessDeniedError(KGFEGMCPError):
    """Raised when rights policy blocks a generated-derivative prompt."""

    error_code = "prompt_access_denied"


class PromptConfigurationError(KGFEGMCPError):
    """Raised when optional framework prompt configuration is invalid."""

    error_code = "prompt_configuration_error"


class PromptRenderingError(KGFEGMCPError):
    """Raised when a deterministic prompt cannot be rendered safely."""

    error_code = "prompt_rendering_error"


class ResourceAccessDeniedError(KGFEGMCPError):
    """Raised when rights or exposure policy blocks a resource read."""

    error_code = "resource_access_denied"


class ResourceNotFoundError(KGFEGMCPError):
    """Raised when a declared resource cannot be resolved."""

    error_code = "resource_not_found"


class StandardNotFoundError(KGFEGMCPError):
    """Raised when a requested standard identifier cannot be resolved."""

    error_code = "standard_not_found"


class UnsupportedSearchModeError(KGFEGMCPError):
    """Raised when a requested deterministic search mode is unsupported."""

    error_code = "unsupported_search_mode"
