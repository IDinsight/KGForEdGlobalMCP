"""This module reports capabilities implemented by the accepted application runtime.

This module provides ``CapabilitiesService``, which combines the retained catalog load,
accepted graph-package metadata, and existing search-index metadata into one truthful
description of the server's implemented behavior.

The service reports the canonical tools and prompts, available graph types,
package-specific search modes, traversal support, implemented features, approved
resource URI families, optional framework prompt overlays, and explicitly unavailable
features. It does not inspect the filesystem, dynamically test packages, register MCP
components, or advertise semantic retrieval, comparisons, alignments, persistence, or
future graph domains.
"""

# Future Library
from __future__ import annotations

# Standard Library
from dataclasses import dataclass
from typing import TYPE_CHECKING, Final

# Package Library
from kgfegmcp.catalog.models import CatalogLoadResult
from kgfegmcp.domain.enums import CodeAvailability, GraphType
from kgfegmcp.errors import CatalogError
from kgfegmcp.prompts.models import PROMPT_CONFIG_SCHEMA_VERSION, PROMPT_NAMES
from kgfegmcp.resources.uri import CATALOG_URI, RESOURCE_URI_TEMPLATES
from kgfegmcp.search.models import PackageSearchIndexMetadata, SearchMode
from kgfegmcp.search.service import SearchService
from kgfegmcp.services.models import GetCapabilitiesResult, PackageCapabilityResult

if TYPE_CHECKING:
    # Package Library
    from kgfegmcp.resources.service import ResourceService

_IMPLEMENTED_FEATURES: Final[tuple[str, ...]] = (
    "bounded_ancestor_traversal",
    "bounded_descendant_traversal",
    "catalog_discovery",
    "complete_root_path_enumeration",
    "direct_graph_navigation",
    "exact_framework_lookup",
    "exact_standard_lookup",
    "framework_prompt_overlays",
    "framework_statistics",
    "lexical_standard_search",
    "manifest_declared_artifact_access",
    "profile_governed_exact_code_search",
    "profile_governed_prefix_code_search",
    "read_only_resources",
    "rights_aware_resource_access",
    "role_oriented_prompt_workflows",
    "unique_current_framework_routing",
)
_SERVER_NAME: Final[str] = "Knowledge Graph For Education Global MCP"
_TOOL_NAMES: Final[tuple[str, ...]] = (
    "get_capabilities",
    "get_framework",
    "get_framework_statistics",
    "get_standard",
    "get_standard_context",
    "list_frameworks",
    "search_standards",
)
_UNAVAILABLE_FEATURES: Final[tuple[str, ...]] = (
    "alignments",
    "comparisons",
    "embeddings",
    "learning_components",
    "learning_progressions",
    "mutations",
    "persistence",
    "semantic_search",
)


def _implemented_search_modes(
    *, code_availability: CodeAvailability, prefix_available: bool, text_available: bool
) -> tuple[SearchMode, ...]:
    """Return exact search modes implemented for one accepted package.

    Parameters
    ----------
    code_availability
        Profile-governed statement-code coverage.
    prefix_available
        Whether the selected profile enables delimiter-boundary prefix search.
    text_available
        Whether deterministic lexical search is enabled for the package.

    Returns
    -------
    tuple[SearchMode, ...]
        Implemented modes in stable public order.
    """

    modes: list[SearchMode] = []

    if text_available:
        modes.append(SearchMode.TEXT)

    if code_availability is not CodeAvailability.NONE:
        modes.append(SearchMode.CODE_EXACT)

        if prefix_available:
            modes.append(SearchMode.CODE_PREFIX)

    return tuple(modes)


@dataclass(frozen=True, slots=True)
class CapabilitiesService:
    """Describe exact server and package capabilities from retained application data."""

    catalog_load_result: CatalogLoadResult
    resource_service: ResourceService
    search_service: SearchService

    def __post_init__(self) -> None:
        """Require capability evidence to share one accepted catalog runtime.

        Raises
        ------
        ValueError
            If independently constructed services or catalog results are mixed.
        """

        if (
            self.resource_service.catalog_service.load_result
            is not self.catalog_load_result
        ):
            raise ValueError(
                "CapabilitiesService and ResourceService must share CatalogLoadResult."
            )

        if (
            self.search_service.catalog_service.load_result
            is not self.catalog_load_result
        ):
            raise ValueError(
                "CapabilitiesService and SearchService must share CatalogLoadResult."
            )

    def get_capabilities(self) -> GetCapabilitiesResult:
        """Return exact implemented server-level and package-level capabilities.

        Returns
        -------
        GetCapabilitiesResult
            Implemented tools, graph types, package modes, and unavailable features.

        Raises
        ------
        CatalogError
            If accepted package runtimes and search index metadata do not correspond.
        """

        metadata_by_graph_package_id: dict[str, PackageSearchIndexMetadata] = {
            str(metadata.package_identity.graph_package_id): metadata
            for metadata in self.search_service.metadata.packages
        }
        snapshots_by_id = {
            snapshot.snapshot_id: snapshot
            for family in self.catalog_load_result.catalog.frameworks
            for snapshot in family.snapshots
        }
        package_results: list[PackageCapabilityResult] = []
        available_graph_types: set[GraphType] = set()

        for runtime in self.catalog_load_result.package_runtimes:
            package = runtime.catalog_package
            identity = package.package_identity
            metadata = metadata_by_graph_package_id.get(str(identity.graph_package_id))
            snapshot = snapshots_by_id.get(identity.snapshot_id)

            if metadata is None or snapshot is None:
                raise CatalogError(
                    details={"graph_package_id": str(identity.graph_package_id)},
                    message=(
                        "Accepted package capability evidence is incomplete or "
                        "inconsistent."
                    ),
                )

            profile = runtime.loaded_package.profile
            resource_kinds, resource_artifacts = (
                self.resource_service.package_resource_capabilities(
                    identity.graph_package_id
                )
            )
            available_graph_types.add(identity.graph_type)
            package_results.append(
                PackageCapabilityResult(
                    available_resource_artifacts=resource_artifacts,
                    available_resource_kinds=tuple(
                        resource_kind.value for resource_kind in resource_kinds
                    ),
                    implemented_search_modes=_implemented_search_modes(
                        code_availability=profile.code_search_policy.availability,
                        prefix_available=(
                            profile.code_search_policy.allow_prefix_search
                        ),
                        text_available=package.capabilities.text_search,
                    ),
                    package=package,
                    search_index=metadata,
                    source_metadata=snapshot.source_metadata,
                    traversal_relationship_type=(
                        runtime.graph_store.hierarchy_relationship_type
                    ),
                )
            )

        return GetCapabilitiesResult(
            available_graph_types=tuple(
                sorted(available_graph_types, key=lambda value: value.value)
            ),
            framework_prompt_overlays_optional=True,
            implemented_features=_IMPLEMENTED_FEATURES,
            packages=tuple(package_results),
            prompt_config_schema_version=PROMPT_CONFIG_SCHEMA_VERSION,
            prompt_names=PROMPT_NAMES,
            resource_representations=("deterministic_derived", "raw_source"),
            resource_uri_templates=RESOURCE_URI_TEMPLATES,
            resource_uris=(CATALOG_URI,),
            server_name=_SERVER_NAME,
            tool_names=_TOOL_NAMES,
            unavailable_features=_UNAVAILABLE_FEATURES,
        )
