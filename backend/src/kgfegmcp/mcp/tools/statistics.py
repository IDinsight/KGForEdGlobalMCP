"""Register and implement the canonical framework-statistics FastMCP tool.

The adapter delegates structural aggregation to ``FrameworkStatisticsService``. The
reported counts remain descriptive graph and metadata evidence and make no claims about
mastery, difficulty, equivalence, progression, prerequisites, or instructional order.
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
from kgfegmcp.services.models import (
    GetFrameworkStatisticsRequest,
    GetFrameworkStatisticsResult,
)
from kgfegmcp.services.statistics import FrameworkStatisticsService

if TYPE_CHECKING:
    # Third Party Library
    from fastmcp import FastMCP

    # Package Library
    from kgfegmcp.bootstrap import AppState


def _format_statistics(result: GetFrameworkStatisticsResult) -> str:
    """Format one framework-statistics result as deterministic readable text.

    Parameters
    ----------
    result
        Complete package identity, source metadata, and structural statistics.

    Returns
    -------
    str
        Stable summary of non-interpretive package structure and code presence.
    """

    identity = result.package.package_identity
    statistics = result.statistics
    return "\n".join(
        (
            f"Framework statistics: {identity.framework_id}",
            f"Snapshot: {identity.snapshot_id}",
            f"Package: {identity.graph_package_id}",
            f"Items: {statistics.total_item_nodes}",
            f"Relationships: {statistics.total_relationships}",
            f"Coded items: {statistics.code_presence.coded_item_count}",
            f"Uncoded items: {statistics.code_presence.uncoded_item_count}",
            f"Multi-parent targets: {statistics.multi_parent.target_count}",
            (
                f"Unresolved relationships: "
                f"{statistics.unresolved_relationships.unresolved_count}"
            ),
            f"Maximum structural depth: {statistics.maximum_structural_depth}",
        )
    )


async def get_framework_statistics(
    request: GetFrameworkStatisticsRequest, context: Context
) -> ToolResult:
    """Return structural statistics for one exact or unique-current graph package.

    Parameters
    ----------
    request
        Framework route and supported graph type.
    context
        Injected FastMCP request context containing immutable application state.

    Returns
    -------
    ToolResult
        Human-readable summary and complete statistics with package evidence.
    """

    with tool_error_boundary("get_framework_statistics"):
        state = get_app_state(context)
        service = FrameworkStatisticsService(
            catalog_service=state.catalog_service, search_service=state.search_service
        )
        result = service.get_framework_statistics(request)
        return build_tool_result(content=_format_statistics(result), result=result)


def register_statistics_tools(server: FastMCP[dict[str, AppState]]) -> None:
    """Register the canonical framework structural-statistics tool.

    Parameters
    ----------
    server
        FastMCP server receiving the explicitly approved read-only tool.
    """

    server.tool(
        annotations=READ_ONLY_TOOL_ANNOTATIONS,
        description=(
            "Return deterministic source, normalized, code-presence, hierarchy-depth, "
            "multi-parent, and unresolved-status counts for one accepted graph package."
        ),
        name="get_framework_statistics",
        output_schema=result_schema(GetFrameworkStatisticsResult),
        title="Get Framework Statistics",
    )(get_framework_statistics)
