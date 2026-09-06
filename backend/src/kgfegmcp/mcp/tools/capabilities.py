"""This module exposes the canonical runtime-capabilities operation as a FastMCP tool.

This module implements and registers the ``get_capabilities`` MCP tool. The tool
retrieves the immutable application state, delegates capability reporting to
``CapabilitiesService``, and returns both a deterministic readable summary and the
complete structured result.

The reported capabilities describe only behavior implemented by the currently accepted
runtime and graph packages. The module does not inspect the filesystem, calculate
package capabilities itself, or advertise semantic search, official alignments,
persistence, or additional graph domains.
"""

# Future Library
from __future__ import annotations

# Standard Library
from typing import TYPE_CHECKING

# Third Party Library
from fastmcp import Context
from fastmcp.tools.base import ToolResult

# Package Library
from kgfegmcp.mcp.errors import tool_error_boundary
from kgfegmcp.mcp.tools import (
    READ_ONLY_TOOL_ANNOTATIONS,
    build_tool_result,
    catalog_resource_links,
    get_app_state,
    result_schema,
)
from kgfegmcp.services.capabilities import CapabilitiesService
from kgfegmcp.services.models import GetCapabilitiesResult, PackageCapabilityResult

if TYPE_CHECKING:
    # Third Party Library
    from fastmcp import FastMCP

    # Package Library
    from kgfegmcp.bootstrap import AppState


def _format_capabilities(result: GetCapabilitiesResult) -> str:
    """Format exact implemented capabilities as deterministic readable text.

    Parameters
    ----------
    result
        Complete server and accepted-package capability evidence.

    Returns
    -------
    str
        Stable summary of tools, prompts, graph types, exact package search modes, and
        unavailable features.
    """

    graph_types = ", ".join(value.value for value in result.available_graph_types)
    lines = [
        f"Server: {result.server_name}",
        f"Tools: {', '.join(result.tool_names)}",
        f"Prompts: {', '.join(result.prompt_names)}",
        f"Graph types: {graph_types}",
        f"Accepted packages: {len(result.packages)}",
        (
            f"Resources: "
            f"{len(result.resource_uris)} fixed, "
            f"{len(result.resource_uri_templates)} templates"
        ),
        (
            f"Framework prompt overlays: optional, schema "
            f"{result.prompt_config_schema_version}"
        ),
        (
            "Package search modes are authoritative per package; generic tool schemas "
            "describe possible request variants, not package authorization."
        ),
        "Package search capabilities:",
    ]

    for package in result.packages:
        lines.extend(_format_package_capability(package))

    lines.append(f"Unavailable features: {', '.join(result.unavailable_features)}")
    return "\n".join(lines)


def _format_package_capability(
    package: PackageCapabilityResult,
) -> tuple[str, ...]:
    """Format exact search capability evidence for one accepted package.

    Parameters
    ----------
    package
        Complete accepted-package capability evidence.

    Returns
    -------
    tuple[str, ...]
        Stable readable package identity, implemented modes, and code coverage.
    """

    identity = package.package.package_identity
    implemented_modes = (
        ", ".join(mode.value for mode in package.implemented_search_modes) or "none"
    )
    implemented_component_modes = (
        ", ".join(
            mode.value for mode in package.implemented_learning_component_search_modes
        )
        or "none"
    )
    learning_component_count = package.search_index.learning_component_document_count
    return (
        f"- Graph package ID: {identity.graph_package_id}",
        f"  Framework ID: {identity.framework_id}",
        f"  Snapshot ID: {identity.snapshot_id}",
        f"  implementedSearchModes: {implemented_modes}",
        f"  implementedLearningComponentSearchModes: {implemented_component_modes}",
        f"  codeCoverage: {package.package.capabilities.code_search.value}",
        f"  codedNodes: {package.search_index.coded_node_count}",
        f"  learningComponents: {learning_component_count}",
        f"  tagVocabulary: {package.search_index.tag_vocabulary_size}",
    )


async def get_capabilities(context: Context) -> ToolResult:
    """Return exact server and accepted-package capabilities from lifespan state.

    Parameters
    ----------
    context
        Injected FastMCP request context containing immutable application state.

    Returns
    -------
    ToolResult
        Human-readable summary and complete ``GetCapabilitiesResult`` evidence.
    """

    with tool_error_boundary("get_capabilities"):
        state = get_app_state(context)
        service = CapabilitiesService(
            catalog_load_result=state.catalog_load_result,
            resource_service=state.resource_service,
            search_service=state.search_service,
        )
        result = service.get_capabilities()
        return build_tool_result(
            content=_format_capabilities(result),
            resource_links=catalog_resource_links(),
            result=result,
        )


def register_capability_tools(server: FastMCP[dict[str, AppState]]) -> None:
    """Register the canonical runtime-capabilities tool.

    Parameters
    ----------
    server
        FastMCP server receiving the explicitly approved read-only tool.
    """

    server.tool(
        annotations=READ_ONLY_TOOL_ANNOTATIONS,
        description=(
            "Report exact server-wide and per-package capabilities. Generic tool "
            "schemas describe possible request variants, not package authorization; "
            "inspect packages[].implementedSearchModes for the selected package before "
            "choosing code_exact or code_prefix. Also report tools, prompts, "
            "resources, graph types, traversal behavior, and unavailable features "
            "implemented by the accepted runtime."
        ),
        name="get_capabilities",
        output_schema=result_schema(GetCapabilitiesResult),
        title="Get Capabilities",
    )(get_capabilities)
