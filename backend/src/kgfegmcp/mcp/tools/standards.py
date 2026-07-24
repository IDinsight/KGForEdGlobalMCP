"""This module exposes canonical standards search and exact lookup as FastMCP tools.

This module implements and registers the ``search_standards`` and ``get_standard`` MCP
tools. The adapters retrieve immutable application state, construct the ordinary
framework and standards services, delegate the requested operation, and return a
deterministic human-readable summary alongside the complete structured result.

The module may format or truncate text for display, but it does not select packages,
normalize codes, tokenize text, apply filters, rank results, handle search cursors,
resolve identifier namespaces, inspect graph stores, or calculate facet evidence. Those
responsibilities remain in the existing framework, standards, search, catalog, and
graph services.
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
    standard_resource_links,
)
from kgfegmcp.search.models import ExactPackageSearchScope
from kgfegmcp.services.frameworks import FrameworkService
from kgfegmcp.services.models import (
    GetStandardRequest,
    GetStandardResult,
    SearchStandardsResult,
    StandardsSearchRequest,
)
from kgfegmcp.services.standards import StandardsService

if TYPE_CHECKING:
    # Third Party Library
    from fastmcp import FastMCP

    # Package Library
    from kgfegmcp.bootstrap import AppState


def _collapse_whitespace(value: str) -> str:
    """Collapse whitespace for deterministic human-readable summaries only.

    Parameters
    ----------
    value
        Exact source text retained unchanged in the structured result.

    Returns
    -------
    str
        Single-line display text without modifying structured source evidence.
    """

    return " ".join(value.split())


def _format_search_result(result: SearchStandardsResult) -> str:
    """Format one standards search page as deterministic readable text.

    Parameters
    ----------
    result
        Complete search result including selected snapshots and package-local hits.

    Returns
    -------
    str
        Stable line-oriented summary of mode, packages, hits, warnings, and cursor.
    """

    scope = result.effective_scope
    graph_types = (
        (scope.graph_type,)
        if isinstance(scope, ExactPackageSearchScope)
        else scope.graph_types
    )
    package_ids = {
        str(package.package_identity.graph_package_id)
        for snapshot in result.selected_snapshots
        for package in snapshot.graph_packages
        if package.package_identity.graph_type in graph_types
    }
    lines = [
        f"Search mode: {result.page.mode.value}",
        f"Selected packages: {len(package_ids)}",
        f"Returned hits: {result.page.returned_count}",
    ]

    for index, hit in enumerate(result.page.hits, start=1):
        code = hit.node.statement_code or "[uncoded]"
        description = _truncate_display_text(
            limit=240,
            value=_collapse_whitespace(hit.node.description or "[no description]"),
        )
        lines.extend(
            (
                (
                    f"{index}. {code} | {hit.node.node_id} | "
                    f"{hit.package_identity.graph_package_id}"
                ),
                f"   {description}",
            )
        )

    lines.extend(
        (
            f"Warnings: {len(result.page.warnings)}",
            (
                f"Next cursor: "
                f"{'present' if result.page.next_cursor is not None else 'none'}"
            ),
        )
    )
    return "\n".join(lines)


def _format_standard(result: GetStandardResult) -> str:
    """Format one exact standard record as deterministic readable text.

    Parameters
    ----------
    result
        Complete standard lookup result with package and facet evidence.

    Returns
    -------
    str
        Stable source-facing summary without altering exact structured values.
    """

    node = result.node
    identity = result.package.package_identity
    return "\n".join(
        (
            f"Standard: {node.statement_code or '[uncoded]'}",
            f"Node ID: {node.node_id}",
            f"CASE UUID: {node.case_identifier_uuid or 'none'}",
            f"CASE URI: {node.case_identifier_uri or 'none'}",
            f"Package: {identity.graph_package_id}",
            f"Profile: {identity.profile_id}@{identity.profile_version}",
            f"Description: {node.description or '[no description]'}",
        )
    )


def _standards_service(state: AppState) -> StandardsService:
    """Construct one stateless standards orchestrator over retained application data.

    Parameters
    ----------
    state
        Immutable application state created by the FastMCP lifespan.

    Returns
    -------
    StandardsService
        Stateless ordinary service delegating to retained domain services.
    """

    framework_service = FrameworkService(catalog_service=state.catalog_service)
    return StandardsService(
        catalog_service=state.catalog_service,
        framework_service=framework_service,
        search_service=state.search_service,
    )


def _truncate_display_text(*, limit: int, value: str) -> str:
    """Truncate display-only text deterministically at a Unicode character limit.

    Parameters
    ----------
    limit
        Maximum number of characters in the display string.
    value
        Whitespace-collapsed display text.

    Returns
    -------
    str
        Original value when short enough, otherwise an ellipsis-terminated prefix.
    """

    if len(value) <= limit:
        return value

    return f"{value[: max(limit - 1, 0)]}…"


async def get_standard(request: GetStandardRequest, context: Context) -> ToolResult:
    """Return one exact package-local standard through an explicit identifier namespace.

    Parameters
    ----------
    request
        Exact framework or snapshot route and typed standard identifier.
    context
        Injected FastMCP request context containing immutable application state.

    Returns
    -------
    ToolResult
        Human-readable summary and complete ``GetStandardResult`` evidence.
    """

    with tool_error_boundary("get_standard"):
        state = get_app_state(context)
        result = _standards_service(state).get_standard(request)
        resource_links = standard_resource_links(
            node=result.node, package=result.package, state=state
        )
        return build_tool_result(
            content=_format_standard(result),
            resource_links=resource_links,
            result=result,
        )


def register_standard_tools(server: FastMCP[dict[str, AppState]]) -> None:
    """Register canonical standards search and exact lookup tools.

    Parameters
    ----------
    server
        FastMCP server receiving explicitly approved read-only tools.
    """

    server.tool(
        annotations=READ_ONLY_TOOL_ANNOTATIONS,
        description=(
            "Search accepted standards using existing package-local lexical, "
            "exact-code, or prefix-code indexes and their established cursor "
            "semantics."
        ),
        name="search_standards",
        output_schema=result_schema(SearchStandardsResult),
        title="Search Standards",
    )(search_standards)
    server.tool(
        annotations=READ_ONLY_TOOL_ANNOTATIONS,
        description=(
            "Return one exact standard by node ID, CASE UUID, or CASE URI within one "
            "routed immutable graph package."
        ),
        name="get_standard",
        output_schema=result_schema(GetStandardResult),
        title="Get Standard",
    )(get_standard)


async def search_standards(
    request: StandardsSearchRequest, context: Context
) -> ToolResult:
    """Search standards through existing package-local indexes and cursor semantics.

    Parameters
    ----------
    request
        Discriminated text, exact-code, or prefix-code search request.
    context
        Injected FastMCP request context containing immutable application state.

    Returns
    -------
    ToolResult
        Human-readable summary and complete ``SearchStandardsResult`` evidence.
    """

    with tool_error_boundary("search_standards"):
        state = get_app_state(context)
        result = _standards_service(state).search_standards(request)
        return build_tool_result(content=_format_search_result(result), result=result)
