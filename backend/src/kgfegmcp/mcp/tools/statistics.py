"""This module exposes canonical framework statistics as a FastMCP tool.

This module implements and registers the ``get_framework_statistics`` MCP tool. It
retrieves immutable application state, delegates all structural aggregation to
``FrameworkStatisticsService``, and returns a deterministic readable summary together
with the complete structured statistics result.

The adapter does not count nodes, relationships, grades, statement types, codes,
parents, depths, or unresolved statuses itself. It also makes no claims about mastery,
difficulty, equivalence, progression, prerequisites, preferred parentage, or
instructional order.
"""

# Future Library
from __future__ import annotations

# Standard Library
import logging

from typing import TYPE_CHECKING

# Third Party Library
from fastmcp import Context
from fastmcp.tools.base import ToolResult

# Package Library
from kgfegmcp.mcp.errors import tool_error_boundary
from kgfegmcp.mcp.tools import (
    READ_ONLY_TOOL_ANNOTATIONS,
    build_tool_result,
    framework_resource_links,
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

_LOGGER = logging.getLogger("fastmcp.kgfegmcp.mcp.tools.statistics")


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
    components = statistics.learning_components
    return "\n".join(
        (
            f"Framework statistics: {identity.framework_id}",
            f"Snapshot: {identity.snapshot_id}",
            f"Package: {identity.graph_package_id}",
            "",
            "Academic standards",
            f"Items: {statistics.total_item_nodes}",
            f"Relationships (hasChild): {statistics.total_relationships}",
            f"Coded items: {statistics.code_presence.coded_item_count}",
            f"Uncoded items: {statistics.code_presence.uncoded_item_count}",
            f"Multi-parent targets: {statistics.multi_parent.target_count}",
            (
                f"Unresolved relationships: "
                f"{statistics.unresolved_relationships.unresolved_count}"
            ),
            f"Maximum structural depth: {statistics.maximum_structural_depth}",
            "",
            "Learning components",
            f"Components: {components.total_learning_components}",
            f"Relationships (supports): {components.total_supports_relationships}",
            f"Components supporting more than one standard: "
            f"{components.multi_standard_component_count}",
            f"Supported statement types: "
            f"{', '.join(components.supported_statement_types) or 'none'}",
            f"Items of those types with no component: "
            f"{components.standards_without_components}",
            f"Tag vocabulary: {components.tag_vocabulary_size}",
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
        identity = result.package.package_identity

        try:
            snapshot = state.catalog_service.get_framework(
                framework_id=identity.framework_id, snapshot_id=identity.snapshot_id
            )
            resource_links = framework_resource_links(
                framework_id=identity.framework_id,
                graph_package_count=len(snapshot.graph_packages),
                snapshot_id=identity.snapshot_id,
            )
        except Exception as error:  # pylint: disable=W0718
            _LOGGER.warning(
                msg=(
                    f"Optional statistics resource-link construction failed without "
                    f"affecting the tool result: "
                    f"error_type={type(error).__name__}, "
                    f"graph_package_id={identity.graph_package_id}."
                )
            )
            resource_links = ()
        return build_tool_result(
            content=_format_statistics(result),
            resource_links=resource_links,
            result=result,
        )


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
