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
    build_continuation_text,
    build_tool_result,
    catalog_resource_links,
    framework_resource_links,
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
    from kgfegmcp.catalog.models import CatalogGraphPackage, CatalogSourceMetadata


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


def _format_framework(result: GetFrameworkResult) -> str:
    """Format one exact framework snapshot as deterministic readable text.

    Parameters
    ----------
    result
        Complete framework lookup result.

    Returns
    -------
    str
        Stable summary of complete source metadata and every exact graph package.
    """

    framework = result.framework
    lines = [
        f"Framework: {framework.source_metadata.name}",
        f"Framework ID: {framework.framework_id}",
        f"Snapshot ID: {framework.snapshot_id}",
        *_format_source_metadata(framework.source_metadata),
        "Graph packages:",
    ]

    for package in framework.graph_packages:
        lines.extend(_format_graph_package(package))

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
        Stable summary exposing exact source metadata and package capabilities.
    """

    lines = [
        (
            f"Framework snapshots: {result.returned_count} of "
            f"{result.total_matching_count}"
        )
    ]

    for snapshot in result.items:
        graph_types = tuple(
            graph_type.value for graph_type in snapshot.available_graph_types
        )
        metadata = snapshot.source_metadata
        lines.extend(
            (
                "",
                f"Framework: {metadata.name}",
                f"Framework ID: {snapshot.framework_id}",
                f"Snapshot ID: {snapshot.snapshot_id}",
                *_format_source_metadata(metadata),
                f"Graph types: {_format_values(graph_types)}",
                "Graph packages:",
            )
        )
        lines.extend(
            f"- {_format_package_summary(package)}"
            for package in snapshot.graph_packages
        )

    lines.extend(
        (
            "",
            f"Has more: {_format_boolean(result.has_more)}",
            "Continuation data: see the following MCP continuation block.",
        )
    )
    return "\n".join(lines)


def _format_graph_package(package: CatalogGraphPackage) -> list[str]:
    """Format complete public metadata for one accepted graph package.

    Parameters
    ----------
    package
        Accepted catalog graph package to render.

    Returns
    -------
    list[str]
        Stable line-oriented package identity, capability, count, validation, and
        rights metadata.
    """

    capabilities = package.capabilities
    identity = package.package_identity
    rights = package.rights
    return [
        f"- Graph package ID: {identity.graph_package_id}",
        f"  Graph type: {identity.graph_type.value}",
        f"  Package revision: {identity.package_revision}",
        f"  Profile: {identity.profile_id}@{identity.profile_version}",
        f"  Code search: {capabilities.code_search.value}",
        f"  Text search: {_format_boolean(capabilities.text_search)}",
        (
            "  Detailed provenance: "
            f"{_format_boolean(capabilities.has_detailed_provenance)}"
        ),
        (
            "  Official activities: "
            f"{_format_boolean(capabilities.has_official_activities)}"
        ),
        (
            "  Official assessment guidance: "
            f"{_format_boolean(capabilities.has_official_assessment_guidance)}"
        ),
        (
            "  Unresolved relationships: "
            f"{_format_boolean(capabilities.has_unresolved_relationships)}"
        ),
        f"  Multi-parent: {_format_boolean(capabilities.multi_parent)}",
        f"  Counts: {_format_package_counts(package)}",
        f"  Validation status: {package.validation.status.value}",
        f"  Rights review status: {rights.review_status.value}",
        f"  Source license: {rights.source_license}",
        (
            "  Standard resources allowed: "
            f"{_format_boolean(rights.allow_standard_resources)}"
        ),
        f"  Full text allowed: {_format_boolean(rights.allow_full_text)}",
        f"  Bulk resource allowed: {_format_boolean(rights.allow_bulk_resource)}",
        ("  Generated derivatives: " f"{rights.allow_generated_derivatives.value}"),
        f"  Attribution: {rights.attribution_statement}",
    ]


def _format_optional_value(value: object | None) -> str:
    """Format one optional value without inventing missing metadata.

    Parameters
    ----------
    value
        Source or package value that may be absent.

    Returns
    -------
    str
        Exact string representation or ``none`` when the value is absent.
    """

    return "none" if value is None else str(value)


def _format_package_counts(package: CatalogGraphPackage) -> str:
    """Format exact declared counts for one accepted graph package.

    Parameters
    ----------
    package
        Accepted catalog graph package whose counts must be rendered.

    Returns
    -------
    str
        Stable comma-separated count assignments.
    """

    count_parts = [
        f"framework_nodes={package.counts.framework_nodes}",
        f"item_nodes={package.counts.item_nodes}",
        f"relationships={package.counts.relationships}",
    ]
    count_parts.extend(
        f"{name}={value}"
        for name, value in sorted(package.counts.additional_counts.items())
    )
    return ", ".join(count_parts)


def _format_package_summary(package: CatalogGraphPackage) -> str:
    """Format one compact package summary for framework discovery output.

    Parameters
    ----------
    package
        Accepted catalog graph package to summarize.

    Returns
    -------
    str
        Stable package identity, capability, profile, and validation summary.
    """

    capabilities = package.capabilities
    identity = package.package_identity
    return (
        f"{identity.graph_package_id} | graph_type={identity.graph_type.value} | "
        f"profile={identity.profile_id}@{identity.profile_version} | "
        f"code_search={capabilities.code_search.value} | "
        f"text_search={_format_boolean(capabilities.text_search)} | "
        f"validation={package.validation.status.value}"
    )


def _format_source_metadata(metadata: CatalogSourceMetadata) -> list[str]:
    """Format complete source-facing metadata for one framework snapshot.

    Parameters
    ----------
    metadata
        Validated source metadata retained in the accepted catalog.

    Returns
    -------
    list[str]
        Stable line-oriented source metadata without inferred values.
    """

    return [
        f"Adoption status: {_format_optional_value(metadata.adoption_status)}",
        f"Current: {_format_boolean(metadata.is_current)}",
        f"Issuing authority: {_format_optional_value(metadata.issuing_authority)}",
        f"Jurisdiction: {metadata.jurisdiction}",
        f"Jurisdiction type: {_format_optional_value(metadata.jurisdiction_type)}",
        f"Languages: {_format_values(tuple(metadata.languages))}",
        (
            "Local grades or stages: "
            f"{_format_values(tuple(metadata.local_grades_or_stages))}"
        ),
        f"Local subject: {metadata.local_subject}",
        f"Provider: {_format_optional_value(metadata.provider)}",
        (
            "Source publication date: "
            f"{_format_optional_value(metadata.source_publication_date)}"
        ),
        f"Source version: {_format_optional_value(metadata.source_version)}",
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
        resource_links = framework_resource_links(
            framework_id=result.framework.framework_id,
            graph_package_count=len(result.framework.graph_packages),
            snapshot_id=result.framework.snapshot_id,
        )
        return build_tool_result(
            content=_format_framework(result),
            resource_links=resource_links,
            result=result,
        )


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
        continuation_text = build_continuation_text(
            {
                "continuationTool": "list_frameworks",
                "cursorField": "cursor",
                "hasMore": result.has_more,
                "nextCursor": (
                    result.next_cursor.root if result.next_cursor is not None else None
                ),
            }
        )
        return build_tool_result(
            additional_text=(continuation_text,),
            content=_format_framework_list(result),
            resource_links=catalog_resource_links(),
            result=result,
        )


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
            "List accepted immutable framework snapshots with exact source metadata, "
            "package capabilities, validation status, and checksum-protected pagination."
        ),
        name="list_frameworks",
        output_schema=result_schema(ListFrameworksResult),
        title="List Frameworks",
    )(list_frameworks)
    server.tool(
        annotations=READ_ONLY_TOOL_ANNOTATIONS,
        description=(
            "Return one exact or uniquely current framework snapshot with complete "
            "source metadata, package capabilities, counts, validation, and rights."
        ),
        name="get_framework",
        output_schema=result_schema(GetFrameworkResult),
        title="Get Framework",
    )(get_framework)
