"""This package exposes deterministic cross-framework evidence retrieval as a FastMCP
tool.

This module provides the protocol-facing ``compare_framework_evidence`` tool and its
explicit registration function. The public tool accepts comparison fields directly at
the top level, constructs the existing typed ordinary comparison request, obtains the
lifespan-owned ``ComparisonService``, delegates the complete operation to that service,
and returns both a stable readable summary and the full structured comparison result.

Each selected framework is represented by an independently retrieved exact-package
section. Package-local match order, search warnings, hierarchy evidence, result limits,
continuation state, rights, provenance, and profile identity are preserved in the
structured response. Optional resource links are supplementary and do not affect the
comparison evidence.

This module is a thin MCP adapter. It performs no catalog selection logic, search
ranking, cursor construction, graph traversal, equivalence inference, mapping,
persistence, semantic search, source-package mutation, server-side LLM invocation, MCP
sampling, or curriculum-specific branching.
"""

# Standard Library
from typing import TYPE_CHECKING, Annotated, Final

# Third Party Library
from fastmcp import Context
from fastmcp.tools.base import ToolResult
from pydantic import Field, TypeAdapter

# Package Library
from kgfegmcp.domain.identifiers import FrameworkId, SnapshotId
from kgfegmcp.mcp.errors import tool_error_boundary
from kgfegmcp.mcp.tools import (
    READ_ONLY_TOOL_ANNOTATIONS,
    build_tool_result,
    catalog_resource_links,
    get_app_state,
    result_schema,
)
from kgfegmcp.search.models import SearchMode, SearchQueryText, TextMatch
from kgfegmcp.services.comparison_models import (
    CompareFrameworkEvidenceResult,
    FrameworkComparisonRequest,
)
from kgfegmcp.services.models import CatalogFilterValue

if TYPE_CHECKING:
    # Third Party Library
    from fastmcp import FastMCP

    # Package Library
    from kgfegmcp.bootstrap import AppState


_COMPARISON_REQUEST_ADAPTER: Final[TypeAdapter[FrameworkComparisonRequest]] = (
    TypeAdapter(FrameworkComparisonRequest)
)
ComparisonFrameworkIds = Annotated[
    tuple[FrameworkId, ...], Field(alias="frameworkIds", max_length=8, min_length=2)
]
ComparisonGradeFilters = Annotated[tuple[CatalogFilterValue, ...], Field(max_length=64)]
ComparisonSnapshotIds = Annotated[
    tuple[SnapshotId, ...], Field(alias="snapshotIds", max_length=8)
]


def _build_comparison_request(
    *,
    framework_ids: ComparisonFrameworkIds,
    include_context_paths: bool,
    include_groupings: bool,
    local_grade_labels: ComparisonGradeFilters,
    match: TextMatch | None,
    max_matches_per_framework: int,
    mode: SearchMode,
    normalized_grades: ComparisonGradeFilters,
    query: SearchQueryText,
    snapshot_ids: ComparisonSnapshotIds,
) -> FrameworkComparisonRequest:
    """Construct one existing ordinary comparison request from public tool fields.

    Parameters
    ----------
    framework_ids
        Two through eight distinct conceptual framework identifiers.
    include_context_paths
        Whether bounded hierarchy paths are included for returned matches.
    include_groupings
        Whether grouping nodes are eligible for comparison retrieval.
    local_grade_labels
        Shared exact local grade or stage filters.
    match
        Text matching policy, required only for text mode.
    max_matches_per_framework
        Independent package-local candidate quota from one through ten.
    mode
        Text, exact-code, or code-prefix comparison mode.
    normalized_grades
        Shared normalized retrieval-facet filters.
    query
        Topic text or code query used for evidence retrieval.
    snapshot_ids
        Optional exact snapshots, with at most one per selected framework.

    Returns
    -------
    FrameworkComparisonRequest
        Existing validated ordinary request for the selected mode.

    Raises
    ------
    pydantic.ValidationError
        If the direct fields do not satisfy the existing discriminated request union.
    """

    request_data: dict[str, object] = {
        "framework_ids": framework_ids,
        "include_context_paths": include_context_paths,
        "include_groupings": include_groupings,
        "local_grade_labels": local_grade_labels,
        "max_matches_per_framework": max_matches_per_framework,
        "mode": mode.value,
        "normalized_grades": normalized_grades,
        "query": query,
        "snapshot_ids": snapshot_ids,
    }

    if match is not None:
        request_data["match"] = match

    return _COMPARISON_REQUEST_ADAPTER.validate_python(request_data)


def _format_comparison_result(result: CompareFrameworkEvidenceResult) -> str:
    """Format one deterministic comparison result as readable line-oriented text.

    Parameters
    ----------
    result
        Complete typed cross-framework comparison evidence.

    Returns
    -------
    str
        Stable summary preserving exact section identities and continuation state.
    """

    lines = [
        f"Epistemic status: {result.epistemic_status.value}",
        f"Mode: {result.request.mode.value}",
        f"Selected frameworks: {len(result.sections)}",
        f"Query: {result.request.query}",
    ]

    for section in result.sections:
        lines.extend(
            (
                "",
                (
                    f"Framework: {section.framework_id} | "
                    f"Snapshot: {section.snapshot_id} | "
                    f"Package: {section.graph_package_id}"
                ),
                f"Matches: {len(section.matches)}",
                f"Search warnings: {len(section.package_search_warnings)}",
                f"Comparison warnings: {len(section.warnings)}",
                (
                    "Next cursor: "
                    f"{'present' if section.next_cursor is not None else 'none'}"
                ),
            )
        )

        for index, match in enumerate(section.matches, start=1):
            node = match.standard.node
            lines.append(
                f"  {index}. {node.statement_code or '[uncoded]'} | {node.node_id}"
            )

    lines.extend(("", f"Fixed disclosures: {len(result.disclosures)}"))
    return "\n".join(lines)


async def compare_framework_evidence(
    *,
    context: Context,
    framework_ids: ComparisonFrameworkIds,
    include_context_paths: Annotated[bool, Field(alias="includeContextPaths")] = True,
    include_groupings: Annotated[bool, Field(alias="includeGroupings")] = False,
    local_grade_labels: Annotated[
        ComparisonGradeFilters, Field(alias="localGradeLabels")
    ] = (),
    match: TextMatch | None = None,
    max_matches_per_framework: Annotated[
        int, Field(alias="maxMatchesPerFramework", ge=1, le=10)
    ] = 5,
    mode: SearchMode,
    normalized_grades: Annotated[
        ComparisonGradeFilters, Field(alias="normalizedGrades")
    ] = (),
    query: SearchQueryText,
    snapshot_ids: ComparisonSnapshotIds = (),
) -> ToolResult:
    """Return independently bounded exact-package evidence for selected frameworks.

    Parameters
    ----------
    context
        Injected FastMCP request context containing immutable application state.
    framework_ids
        Two through eight distinct conceptual framework identifiers.
    include_context_paths
        Whether bounded hierarchy paths are included for returned matches.
    include_groupings
        Whether grouping nodes are eligible for comparison retrieval.
    local_grade_labels
        Shared exact local grade or stage filters.
    match
        Text matching policy, required only for text mode.
    max_matches_per_framework
        Independent package-local candidate quota from one through ten.
    mode
        Text, exact-code, or code-prefix comparison mode.
    normalized_grades
        Shared normalized retrieval-facet filters.
    query
        Topic text or code query used for evidence retrieval.
    snapshot_ids
        Optional exact snapshots, with at most one per selected framework.

    Returns
    -------
    ToolResult
        Readable summary and complete ``CompareFrameworkEvidenceResult`` evidence.
    """

    request = _build_comparison_request(
        framework_ids=framework_ids,
        include_context_paths=include_context_paths,
        include_groupings=include_groupings,
        local_grade_labels=local_grade_labels,
        match=match,
        max_matches_per_framework=max_matches_per_framework,
        mode=mode,
        normalized_grades=normalized_grades,
        query=query,
        snapshot_ids=snapshot_ids,
    )

    with tool_error_boundary("compare_framework_evidence"):
        state = get_app_state(context)
        result = state.comparison_service.compare_framework_evidence(request)
        return build_tool_result(
            content=_format_comparison_result(result),
            resource_links=catalog_resource_links(),
            result=result,
        )


def register_comparison_tools(server: "FastMCP[dict[str, AppState]]") -> None:
    """Register the deterministic cross-framework evidence tool explicitly.

    Parameters
    ----------
    server
        FastMCP server receiving the approved read-only comparison tool.
    """

    server.tool(
        annotations=READ_ONLY_TOOL_ANNOTATIONS,
        description=(
            "Retrieve independently bounded exact-package evidence for two through "
            "eight selected frameworks while preserving each package's search order, "
            "warnings, hierarchy context, and continuation cursor."
        ),
        name="compare_framework_evidence",
        output_schema=result_schema(CompareFrameworkEvidenceResult),
        title="Compare Framework Evidence",
    )(compare_framework_evidence)
