"""Register and implement the canonical standard-context FastMCP tool.

The adapter in this module delegates exact lookup and every graph operation to the
ordinary standards service. It does not infer preferred parents, instructional
sequence, equivalence, progression, or mastery from source order or graph topology.
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
from kgfegmcp.services.frameworks import FrameworkService
from kgfegmcp.services.models import GetStandardContextRequest, GetStandardContextResult
from kgfegmcp.services.standards import StandardsService

if TYPE_CHECKING:
    # Third Party Library
    from fastmcp import FastMCP

    # Package Library
    from kgfegmcp.bootstrap import AppState


def _format_context(result: GetStandardContextResult) -> str:
    """Format one graph-context result as deterministic readable text.

    Parameters
    ----------
    result
        Complete direct, bounded, and root-path graph context.

    Returns
    -------
    str
        Stable summary of requested result sizes and completeness evidence.
    """

    descendants_count = (
        str(len(result.descendants.nodes))
        if result.descendants is not None
        else "not requested"
    )
    descendants_complete = (
        str(result.descendants.is_complete).lower()
        if result.descendants is not None
        else "not requested"
    )
    direct_children_count = (
        str(len(result.direct_children.neighbors))
        if result.direct_children is not None
        else "not requested"
    )
    root_path_count = (
        str(len(result.root_paths.paths))
        if result.root_paths is not None
        else "not requested"
    )
    return "\n".join(
        (
            f"Context for node: {result.standard.node.node_id}",
            (
                "Package: "
                f"{result.standard.package.package_identity.graph_package_id}"
            ),
            f"Direct parents: {len(result.direct_parents.neighbors)}",
            f"Direct children: {direct_children_count}",
            (
                f"Ancestors: {len(result.ancestors.nodes)}, "
                f"complete={str(result.ancestors.is_complete).lower()}"
            ),
            (f"Descendants: {descendants_count}, " f"complete={descendants_complete}"),
            f"Complete root paths returned: {root_path_count}",
            (
                "Unresolved-status relationships in result: "
                f"{len(result.relationship_statuses)}"
            ),
        )
    )


async def get_standard_context(
    request: GetStandardContextRequest, context: Context
) -> ToolResult:
    """Return direct, bounded, and complete-path context for one exact standard.

    Parameters
    ----------
    request
        Exact standard route and explicit graph traversal bounds.
    context
        Injected FastMCP request context containing immutable application state.

    Returns
    -------
    ToolResult
        Human-readable summary and complete ``GetStandardContextResult`` evidence.
    """

    with tool_error_boundary("get_standard_context"):
        state = get_app_state(context)
        framework_service = FrameworkService(catalog_service=state.catalog_service)
        service = StandardsService(
            catalog_service=state.catalog_service,
            framework_service=framework_service,
            search_service=state.search_service,
        )
        result = service.get_standard_context(request)
        return build_tool_result(content=_format_context(result), result=result)


def register_context_tools(server: FastMCP[dict[str, AppState]]) -> None:
    """Register the canonical standard hierarchy-context tool.

    Parameters
    ----------
    server
        FastMCP server receiving the explicitly approved read-only tool.
    """

    server.tool(
        annotations=READ_ONLY_TOOL_ANNOTATIONS,
        description=(
            "Return exact direct parents and children, bounded ancestors or "
            "descendants, and all requested complete root paths without selecting "
            "a preferred parent."
        ),
        name="get_standard_context",
        output_schema=result_schema(GetStandardContextResult),
        title="Get Standard Context",
    )(get_standard_context)
