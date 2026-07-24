"""This module exposes canonical framework discovery and lookup as FastMCP tools.

This module implements and registers the ``list_frameworks`` and ``get_framework`` MCP
tools. The adapters retrieve immutable lifespan state, delegate framework filtering,
snapshot routing, and pagination to ``FrameworkService``, translate application errors
at the approved MCP boundary, and return deterministic readable summaries together with
complete structured results.

The module does not load packages, inspect files, validate manifests, filter framework
records itself, decode framework cursors, select standards, or guess which framework
snapshot should be used.
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
from kgfegmcp.services.models import (
    GetFrameworkRequest,
    GetFrameworkResult,
    ListFrameworksRequest,
    ListFrameworksResult,
)

if TYPE_CHECKING:
    # Third Party Library
    from fastmcp import FastMCP

    # Package Library
    from kgfegmcp.bootstrap import AppState


def _format_framework(result: GetFrameworkResult) -> str:
    """Format one exact framework snapshot as deterministic readable text.

    Parameters
    ----------
    result
        Complete framework lookup result.

    Returns
    -------
    str
        Stable summary of source identity and every exact graph package.
    """

    framework = result.framework
    lines = [
        f"Framework: {framework.source_metadata.name}",
        f"Framework ID: {framework.framework_id}",
        f"Snapshot ID: {framework.snapshot_id}",
        f"Current: {str(framework.source_metadata.is_current).lower()}",
        "Graph packages:",
    ]

    for package in framework.graph_packages:
        identity = package.package_identity
        lines.append(
            (
                f"- {identity.graph_package_id} | "
                f"graph_type={identity.graph_type.value} | "
                f"profile={identity.profile_id}@{identity.profile_version}"
            )
        )

    return "\n".join(lines)


def _format_framework_list(result: ListFrameworksResult) -> str:
    """Format one framework-discovery result as deterministic readable text.

    Parameters
    ----------
    result
        Complete framework-discovery result.

    Returns
    -------
    str
        Stable line-oriented summary retaining exact framework and snapshot IDs.
    """

    lines = [
        (
            f"Framework snapshots: {result.returned_count} of "
            f"{result.total_matching_count}"
        )
    ]

    for snapshot in result.items:
        graph_types = ",".join(
            graph_type.value for graph_type in snapshot.available_graph_types
        )
        lines.append(
            (
                f"{snapshot.framework_id} | {snapshot.snapshot_id} | "
                f"current={str(snapshot.source_metadata.is_current).lower()} | "
                f"graph_types={graph_types}"
            )
        )

    lines.append(
        f"Next cursor: {'present' if result.next_cursor is not None else 'none'}"
    )
    return "\n".join(lines)


async def get_framework(request: GetFrameworkRequest, context: Context) -> ToolResult:
    """Return one exact or unique-current accepted framework snapshot.

    Parameters
    ----------
    request
        Exact framework identifier and optional exact snapshot identifier.
    context
        Injected FastMCP request context containing immutable application state.

    Returns
    -------
    ToolResult
        Human-readable summary and complete ``GetFrameworkResult`` evidence.
    """

    with tool_error_boundary("get_framework"):
        state = get_app_state(context)
        service = FrameworkService(catalog_service=state.catalog_service)
        result = service.get_framework(request)
        return build_tool_result(content=_format_framework(result), result=result)


async def list_frameworks(
    request: ListFrameworksRequest, context: Context
) -> ToolResult:
    """List accepted framework snapshots with deterministic filtering and pagination.

    Parameters
    ----------
    request
        Typed framework discovery filters and optional continuation cursor.
    context
        Injected FastMCP request context containing immutable application state.

    Returns
    -------
    ToolResult
        Human-readable summary and complete ``ListFrameworksResult`` evidence.
    """

    with tool_error_boundary("list_frameworks"):
        state = get_app_state(context)
        service = FrameworkService(catalog_service=state.catalog_service)
        result = service.list_frameworks(request)
        return build_tool_result(content=_format_framework_list(result), result=result)


def register_framework_tools(server: FastMCP[dict[str, AppState]]) -> None:
    """Register the canonical framework discovery and lookup tools.

    Parameters
    ----------
    server
        FastMCP server receiving explicitly approved read-only tools.
    """

    server.tool(
        annotations=READ_ONLY_TOOL_ANNOTATIONS,
        description=(
            "List accepted immutable framework snapshots using exact source and "
            "normalized catalog filters with checksum-protected pagination."
        ),
        name="list_frameworks",
        output_schema=result_schema(ListFrameworksResult),
        title="List Frameworks",
    )(list_frameworks)
    server.tool(
        annotations=READ_ONLY_TOOL_ANNOTATIONS,
        description=(
            "Return one exact framework snapshot or the uniquely current snapshot "
            "for a framework family."
        ),
        name="get_framework",
        output_schema=result_schema(GetFrameworkResult),
        title="Get Framework",
    )(get_framework)
