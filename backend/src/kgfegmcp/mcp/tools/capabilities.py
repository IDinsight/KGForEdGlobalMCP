"""Register and implement the canonical capability-reporting FastMCP tool.

The adapter reports only functionality implemented by the retained accepted runtime.
It does not probe the filesystem or advertise planned resources, prompts, semantic
search, comparisons, alignments, persistence, or future graph domains.
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
        Stable summary of tools, graph types, package count, and unavailable features.
    """

    graph_types = ", ".join(value.value for value in result.available_graph_types)
    return "\n".join(
        (
            f"Server: {result.server_name}",
            f"Tools: {', '.join(result.tool_names)}",
            f"Graph types: {graph_types}",
            f"Accepted packages: {len(result.packages)}",
            ("Unavailable PR 9 features: " f"{', '.join(result.unavailable_features)}"),
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
            search_service=state.search_service,
        )
        result = service.get_capabilities()
        return build_tool_result(content=_format_capabilities(result), result=result)


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
            "Report only tools, graph types, search modes, traversal behavior, and "
            "package capabilities implemented by the accepted runtime."
        ),
        name="get_capabilities",
        output_schema=result_schema(GetCapabilitiesResult),
        title="Get Capabilities",
    )(get_capabilities)
