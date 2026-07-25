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
from kgfegmcp.graph.models import (
    DirectNodeRelationshipsResult,
    FrameworkNode,
    GraphNodeRecord,
    GraphRelationship,
    RootPathsResult,
    TraversalResult,
)
from kgfegmcp.mcp.errors import tool_error_boundary
from kgfegmcp.mcp.tools import (
    READ_ONLY_TOOL_ANNOTATIONS,
    build_tool_result,
    get_app_state,
    result_schema,
    standard_resource_links,
)
from kgfegmcp.services.frameworks import FrameworkService
from kgfegmcp.services.models import GetStandardContextRequest, GetStandardContextResult
from kgfegmcp.services.standards import StandardsService

if TYPE_CHECKING:
    # Third Party Library
    from fastmcp import FastMCP

    # Package Library
    from kgfegmcp.bootstrap import AppState


_CONTEXT_INTERPRETATION = (
    "Hierarchy relationships are structural curriculum-placement evidence. They do "
    "not by themselves establish prerequisite order, instructional sequence, "
    "progression, difficulty, learner mastery, official equivalence, or alignment."
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


def _format_context(result: GetStandardContextResult) -> str:
    """Format one graph-context result as deterministic readable evidence.

    Parameters
    ----------
    result
        Complete direct, bounded, and root-path graph context.

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
            f"{_format_node_description(limit=320, node=standard.node)}"
        ),
        "",
        f"Interpretation: {_CONTEXT_INTERPRETATION}",
        "",
    ]
    lines.extend(
        _format_direct_relationships(
            relationships=result.direct_parents, title="Direct parents"
        )
    )
    lines.append("")

    if result.direct_children is None:
        lines.append("Direct children: not requested")
    else:
        lines.extend(
            _format_direct_relationships(
                relationships=result.direct_children, title="Direct children"
            )
        )
    lines.append("")

    lines.extend(_format_traversal(title="Ancestors", traversal=result.ancestors))
    lines.append("")

    if result.descendants is None:
        lines.append("Descendants: not requested")
    else:
        lines.extend(
            _format_traversal(title="Descendants", traversal=result.descendants)
        )
    lines.append("")

    if result.root_paths is None:
        lines.append("Complete root paths: not requested")
    else:
        lines.extend(_format_root_paths(result.root_paths))
    lines.append("")

    lines.append(
        f"Unresolved-status relationships in result: {len(result.relationship_statuses)}"
    )
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


def _format_direct_relationships(
    *, relationships: DirectNodeRelationshipsResult, title: str
) -> list[str]:
    """Format direct parent or child evidence with exact authored relationships.

    Parameters
    ----------
    relationships
        Deterministically ordered direct-neighbor result.
    title
        Human-readable section title.

    Returns
    -------
    list[str]
        Stable neighbor nodes and relationship evidence.
    """

    lines = [
        f"{title}: {len(relationships.neighbors)}",
        f"Relationship type: {relationships.relationship_type}",
    ]
    if not relationships.neighbors:
        lines.append("- none")
        return lines

    for index, neighbor in enumerate(relationships.neighbors, start=1):
        lines.extend(
            (
                f"{index}. " f"{_format_node(node=neighbor.node, prefix='Neighbor')}",
                "   Relationship: " f"{_format_relationship(neighbor.relationship)}",
            )
        )

    return lines


def _format_node(*, node: GraphNodeRecord, prefix: str) -> str:
    """Format one exact graph node without assigning curriculum-specific meaning.

    Parameters
    ----------
    node
        Framework or standards-framework-item record.
    prefix
        Display label identifying the node's role in the current section.

    Returns
    -------
    str
        Stable node type, source label, identifiers, and available grade evidence.
    """

    if isinstance(node, FrameworkNode):
        return (
            f"{prefix} type=Framework | name="
            f"{_format_optional_value(node.name)} | node_id={node.node_id}"
        )

    return (
        f"{prefix} type={_format_optional_value(node.statement_type)} | "
        f"normalized_type={_format_optional_value(node.normalized_statement_type)} | "
        f"description={_format_node_description(limit=240, node=node)} | "
        f"node_id={node.node_id} | code={node.statement_code or '[uncoded]'} | "
        f"grade_levels={_format_values(tuple(node.grade_level or ()))}"
    )


def _format_node_description(*, limit: int, node: GraphNodeRecord) -> str:
    """Format one node's primary readable source label for display.

    Parameters
    ----------
    node
        Framework or standards-framework-item record.
    limit
        Maximum display characters after whitespace collapse.

    Returns
    -------
    str
        Framework name or standard description, deterministically truncated.
    """

    if isinstance(node, FrameworkNode):
        value = node.name or "[unnamed framework]"
    else:
        value = node.description or "[no description]"

    return _truncate_display_text(limit=limit, value=_collapse_whitespace(value))


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


def _format_relationship(relationship: GraphRelationship) -> str:
    """Format one exact authored relationship and resolution status.

    Parameters
    ----------
    relationship
        Exact source relationship connecting returned graph nodes.

    Returns
    -------
    str
        Stable relationship identity, type, endpoints, and status.
    """

    return (
        f"label={relationship.label} | "
        f"relationship_type={_format_optional_value(relationship.relationship_type)} | "
        f"relationship_id={relationship.relationship_id} | "
        f"source={relationship.source_node_id} | "
        f"target={relationship.target_node_id} | "
        f"resolution_status={_format_optional_value(relationship.resolution_status)}"
    )


def _format_root_paths(result: RootPathsResult) -> list[str]:
    """Format every returned complete root path in authored source direction.

    Parameters
    ----------
    result
        Deterministically bounded complete root-path collection.

    Returns
    -------
    list[str]
        Stable path nodes, connecting relationships, and completeness evidence.
    """

    lines = [
        f"Complete root paths returned: {len(result.paths)}",
        f"Root paths complete: {_format_boolean(result.is_complete)}",
        f"Maximum depth: {result.max_depth}",
        f"Maximum paths: {result.max_paths}",
        "Maximum path-node occurrences: " f"{result.max_path_node_occurrences}",
        (
            f"Root-path truncation reason: "
            f"{_format_optional_value(result.truncation_reason)}"
        ),
        f"Relationship type: {result.relationship_type}",
    ]
    if not result.paths:
        lines.append("- none")
        return lines

    for path_index, path in enumerate(result.paths, start=1):
        lines.append(f"Root path {path_index}:")
        for node_index, node in enumerate(path.nodes, start=1):
            lines.append(f"  {node_index}. {_format_node(node=node, prefix='Node')}")
            if node_index <= len(path.relationships):
                relationship = path.relationships[node_index - 1]
                lines.append(f"     -> {_format_relationship(relationship)}")

    return lines


def _format_traversal(*, title: str, traversal: TraversalResult) -> list[str]:
    """Format one bounded ancestor or descendant traversal completely.

    Parameters
    ----------
    title
        Human-readable section title.
    traversal
        Deterministically ordered bounded traversal result.

    Returns
    -------
    list[str]
        Stable traversal nodes, relationships, limits, and completeness evidence.
    """

    lines = [
        f"{title}: {len(traversal.nodes)} nodes including the origin",
        f"Direction: {traversal.direction.value}",
        f"Traversal complete: {_format_boolean(traversal.is_complete)}",
        f"Maximum depth: {traversal.max_depth}",
        f"Maximum nodes: {traversal.max_nodes}",
        (
            f"Traversal truncation reason: "
            f"{_format_optional_value(traversal.truncation_reason)}"
        ),
        f"Relationship type: {traversal.relationship_type}",
        "Nodes:",
    ]
    lines.extend(
        (
            f"- depth={traversal_node.depth} | "
            f"{_format_node(node=traversal_node.node, prefix='Node')}"
        )
        for traversal_node in traversal.nodes
    )
    lines.append(f"Relationships: {len(traversal.relationships)}")
    if traversal.relationships:
        lines.extend(
            f"- {_format_relationship(relationship)}"
            for relationship in traversal.relationships
        )
    else:
        lines.append("- none")

    return lines


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
        resource_links = standard_resource_links(
            node=result.standard.node, package=result.standard.package, state=state
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
            "descendants, and every requested complete root path with source node, "
            "relationship, resolution, and completeness evidence. Hierarchy is "
            "reported as structural placement without progression inference."
        ),
        name="get_standard_context",
        output_schema=result_schema(GetStandardContextResult),
        title="Get Standard Context",
    )(get_standard_context)
