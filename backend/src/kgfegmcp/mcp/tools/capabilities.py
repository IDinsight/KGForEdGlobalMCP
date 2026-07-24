"""This module exposes the canonical runtime-capabilities operation as a FastMCP tool.

This module implements and registers the ``get_capabilities`` MCP tool. The tool
retrieves the immutable application state, delegates capability reporting to
``CapabilitiesService``, and returns both a deterministic readable summary and the
complete structured result.

The reported capabilities describe only behavior implemented by the currently accepted
runtime and graph packages. The module does not inspect the filesystem, calculate
package capabilities itself, or advertise semantic search, comparisons, alignments,
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
from kgfegmcp.services.models import GetCapabilitiesResult

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
        Stable summary of tools, prompts, graph types, package count, and unavailable
        features.
    """

    graph_types = ", ".join(value.value for value in result.available_graph_types)
    return "\n".join(
        (
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
            f"Unavailable features: {', '.join(result.unavailable_features)}",
        )
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
            "Report only tools, prompts, resources, graph types, search modes, "
            "traversal behavior, and package capabilities implemented by the accepted "
            "runtime."
        ),
        name="get_capabilities",
        output_schema=result_schema(GetCapabilitiesResult),
        title="Get Capabilities",
    )(get_capabilities)
