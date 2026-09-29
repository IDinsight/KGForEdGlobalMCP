"""This module exposes canonical standard hierarchy context as a FastMCP tool.

This module implements and registers the ``get_standard_context`` MCP tool. It
retrieves immutable application state, constructs the ordinary framework and standards
services, delegates exact lookup and graph-context retrieval to those services, and
returns deterministic readable hierarchy evidence alongside the complete structured
result.

The adapter does not traverse the graph, choose a preferred parent, remove unresolved
relationship evidence, or infer instructional sequence, mastery, equivalence,
progression, prerequisites, difficulty, or official alignment from graph topology or
source ordering.
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
    catalog_package,
    get_app_state,
    result_schema,
    standard_resource_links,
)
from kgfegmcp.services.frameworks import FrameworkService
from kgfegmcp.services.models import GetStandardContextRequest, StandardContextView
from kgfegmcp.services.standards import StandardsService, standard_context_view

if TYPE_CHECKING:
    # Third Party Library
    from fastmcp import FastMCP

    # Package Library
    from kgfegmcp.bootstrap import AppState
    from kgfegmcp.services.models import (
        ContextNeighbor,
        ContextNode,
        ContextRelationship,
        ContextRootPaths,
        ContextTraversal,
    )


_CONTEXT_INTERPRETATION = (
    "Hierarchy relationships are structural placement evidence; they do not by "
    "themselves establish prerequisite order, sequence, progression, difficulty, "
    "mastery, equivalence, or alignment."
)


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


def _format_boolean(value: bool) -> str:
    """Format one boolean as deterministic lower-case text.

    Parameters
    ----------
    value
        Boolean value to format.

    Returns
    -------
    str
        ``true`` or ``false``.
    """

    return str(value).lower()


def _format_context(result: StandardContextView) -> str:
    """Format one standard-context view as deterministic readable evidence.

    Each node and relationship is described once, in the node and relationship
    tables; the sections after the tables refer to them by identifier.

    Parameters
    ----------
    result
        Direct, bounded, and root-path context with shared node and relationship
        tables.

    Returns
    -------
    str
        Stable source-facing hierarchy, relationship, completeness, and caveat text.
    """

    standard = result.standard
    identity = standard.package.package_identity
    lines = [
        f"Context for node: {standard.node.node_id}",
        f"Framework ID: {identity.framework_id}",
        f"Snapshot ID: {identity.snapshot_id}",
        f"Package: {identity.graph_package_id}",
        f"Graph type: {identity.graph_type.value}",
        f"Statement code: {standard.node.statement_code or '[uncoded]'}",
        f"Statement type: {_format_optional_value(standard.facets.statement_type)}",
        (
            f"Normalized statement type: "
            f"{_format_optional_value(standard.facets.normalized_statement_type)}"
        ),
        (
            f"Resolved local grade labels: "
            f"{_format_values(tuple(standard.facets.resolved_local_grade_labels))}"
        ),
        (
            f"Normalized grades: "
            f"{_format_values(tuple(standard.facets.normalized_grades))}"
        ),
        (
            f"Origin description: "
            f"{_truncate_display_text(limit=320, value=_collapse_whitespace(standard.node.description or '[no description]'))}"
        ),
        "",
        f"Interpretation: {_CONTEXT_INTERPRETATION}",
        "",
        f"Relationship type: {result.relationship_type}",
        (
            f"Nodes: {len(result.nodes)}, each described once; the sections below "
            f"refer to them by node_id"
        ),
        *(f"- {_format_node(node)}" for node in result.nodes),
        f"Relationships: {len(result.relationships)}",
        *(
            [
                f"- {_format_relationship(relationship)}"
                for relationship in result.relationships
            ]
            or ["- none"]
        ),
        "",
        *_format_neighbors(title="Direct parents", neighbors=result.direct_parents),
        *(
            ["Direct children: not requested"]
            if result.direct_children is None
            else _format_neighbors(
                title="Direct children", neighbors=result.direct_children
            )
        ),
        "",
        *_format_traversal(title="Ancestors", traversal=result.ancestors),
        "",
        *(
            ["Descendants: not requested"]
            if result.descendants is None
            else _format_traversal(title="Descendants", traversal=result.descendants)
        ),
        "",
        *(
            ["Complete root paths: not requested"]
            if result.root_paths is None
            else _format_root_paths(result.root_paths)
        ),
        "",
        f"Unresolved-status relationships in result: {len(result.relationship_statuses)}",
    ]

    if result.relationship_statuses:
        lines.extend(
            (
                f"- relationship_id={status.relationship_id} | "
                f"resolution_status={status.resolution_status}"
            )
            for status in result.relationship_statuses
        )
    else:
        lines.append("- none")

    return "\n".join(lines)


def _format_neighbors(
    *, neighbors: tuple[ContextNeighbor, ...], title: str
) -> list[str]:
    """Format direct parents or children by node and relationship identifier.

    Parameters
    ----------
    neighbors
        Direct neighbours in source order.
    title
        Human-readable section title.

    Returns
    -------
    list[str]
        Count line and one reference line per neighbour.
    """

    if not neighbors:
        return [f"{title}: none"]

    return [
        f"{title}: {len(neighbors)}",
        *(
            f"- node_id={neighbor.node_id} | relationship_id={neighbor.relationship_id}"
            for neighbor in neighbors
        ),
    ]


def _format_node(node: ContextNode) -> str:
    """Format one node of the context node table on one line.

    Parameters
    ----------
    node
        Compact framework-root or standards-item description.

    Returns
    -------
    str
        Stable identifier, type, code, grade, and source label.
    """

    if node.node_kind == "framework":
        return (
            f"node_id={node.node_id} | type=Framework | "
            f"name={_format_optional_value(node.description)}"
        )

    description = _truncate_display_text(
        limit=240, value=_collapse_whitespace(node.description or "[no description]")
    )
    return (
        f"node_id={node.node_id} | type={_format_optional_value(node.statement_type)} | "
        f"normalized_type={_format_optional_value(node.normalized_statement_type)} | "
        f"code={node.statement_code or '[uncoded]'} | "
        f"grade_levels={_format_values(tuple(node.grade_level or ()))} | "
        f"description={description}"
    )


def _format_optional_value(value: object | None) -> str:
    """Format one optional value without inventing missing metadata.

    Parameters
    ----------
    value
        Source or relationship value that may be absent.

    Returns
    -------
    str
        Exact string representation or ``none`` when the value is absent.
    """

    return "none" if value is None else str(value)


def _format_relationship(relationship: ContextRelationship) -> str:
    """Format one relationship of the context relationship table on one line.

    Parameters
    ----------
    relationship
        Compact hierarchy relationship.

    Returns
    -------
    str
        Stable relationship identity, endpoints, and resolution status.
    """

    return (
        f"relationship_id={relationship.relationship_id} | "
        f"source={relationship.source_node_id} | "
        f"target={relationship.target_node_id} | "
        f"resolution_status={_format_optional_value(relationship.resolution_status)}"
    )


def _format_root_paths(result: ContextRootPaths) -> list[str]:
    """Format every returned complete root path as a node-ID chain.

    Parameters
    ----------
    result
        Bounded complete root paths referring to the node table.

    Returns
    -------
    list[str]
        Bounds and completion line, then one line per path, root first.
    """

    lines = [
        (
            f"Complete root paths: {len(result.paths)} | "
            f"complete: {_format_boolean(result.is_complete)} | "
            f"max depth: {result.max_depth} | max paths: {result.max_paths} | "
            f"max path-node occurrences: {result.max_path_node_occurrences} | "
            f"truncation: {_format_optional_value(result.truncation_reason)}"
        )
    ]

    if not result.paths:
        lines.append("- none")

    lines.extend(
        f"- Path {index}: {' > '.join(str(node_id) for node_id in path)}"
        for index, path in enumerate(result.paths, start=1)
    )
    return lines


def _format_traversal(*, title: str, traversal: ContextTraversal) -> list[str]:
    """Format one bounded traversal as depth-ordered node references.

    Parameters
    ----------
    title
        Human-readable section title.
    traversal
        Bounded ancestor or descendant traversal referring to the node table.

    Returns
    -------
    list[str]
        Bounds and completion line, then one line per traversed node.
    """

    return [
        (
            f"{title}: {len(traversal.nodes)} nodes including the origin | "
            f"complete: {_format_boolean(traversal.is_complete)} | "
            f"max depth: {traversal.max_depth} | max nodes: {traversal.max_nodes} | "
            f"truncation: {_format_optional_value(traversal.truncation_reason)}"
        ),
        *(f"- depth={item.depth} | node_id={item.node_id}" for item in traversal.nodes),
    ]


def _format_values(values: tuple[object, ...]) -> str:
    """Format one ordered tuple while preserving its source order.

    Parameters
    ----------
    values
        Ordered values to render.

    Returns
    -------
    str
        Comma-separated exact values or ``none`` for an empty tuple.
    """

    return ", ".join(str(value) for value in values) or "none"


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
        Human-readable summary and the ``StandardContextView`` evidence.
    """

    with tool_error_boundary("get_standard_context"):
        state = get_app_state(context)
        framework_service = FrameworkService(catalog_service=state.catalog_service)
        service = StandardsService(
            catalog_service=state.catalog_service,
            framework_service=framework_service,
            search_service=state.search_service,
        )
        result = standard_context_view(service.get_standard_context(request))
        resource_links = standard_resource_links(
            node=result.standard.node,
            package=catalog_package(result.standard.package.package_identity, state),
            state=state,
        )
        return build_tool_result(
            content=_format_context(result),
            resource_links=resource_links,
            result=result,
        )


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
            "Return exact readable direct parents and children, bounded ancestors or "
            "descendants, and every requested complete root path with relationship, "
            "resolution, and completeness evidence. Each node and relationship is "
            "described once, in nodes and relationships, and the sections refer to "
            "them by ID; a node's complete record is one get_standard call away. "
            "Hierarchy is reported as structural placement without progression "
            "inference."
        ),
        name="get_standard_context",
        output_schema=result_schema(StandardContextView),
        title="Get Standard Context",
    )(get_standard_context)
