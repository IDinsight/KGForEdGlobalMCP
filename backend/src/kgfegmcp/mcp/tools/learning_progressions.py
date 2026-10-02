"""Expose five bounded stored LP queries through thin read-only MCP adapters."""

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
from kgfegmcp.services.learning_progressions import (
    progression_result_text,
    require_progression_result_size,
)
from kgfegmcp.services.lp_models import (
    GetLearningProgressionPathsRequest,
    GetLearningProgressionPathsResult,
    GetLearningProgressionRequest,
    GetLearningProgressionResult,
    GetStandardProgressionsRequest,
    ProgressionCollectionResult,
    ProgressionEvidenceResult,
    SearchLearningProgressionsRequest,
    TraverseLearningProgressionsRequest,
    TraverseLearningProgressionsResult,
)

if TYPE_CHECKING:
    # Third Party Library
    from fastmcp import FastMCP

    # Package Library
    from kgfegmcp.bootstrap import AppState


def _build_progression_result(result: ProgressionEvidenceResult) -> ToolResult:
    """Use the service's exact text and byte ceiling for the complete MCP payload.

    Parameters
    ----------
    result
        Complete bounded evidence with canonical public aliases and resource URIs.

    Returns
    -------
    ToolResult
        One concise text block and the full structured evidence, within 1 MiB.
    """

    text = progression_result_text(result=result)
    require_progression_result_size(result=result, text=text)
    return build_tool_result(content=text, result=result)


async def get_learning_progression(
    *, context: Context, request: GetLearningProgressionRequest
) -> ToolResult:
    """Retrieve one exact stored relationship and both standards.

    Parameters
    ----------
    context
        Injected immutable application state.
    request
        Required framework and relationship ID, with optional exact snapshot.

    Returns
    -------
    ToolResult
        Original generated edge, bounded judgment and exact evidence links.
    """

    with tool_error_boundary("get_learning_progression"):
        result = get_app_state(
            context
        ).learning_progressions_service.get_learning_progression(request=request)
        return _build_progression_result(result)


async def get_learning_progression_paths(
    *, context: Context, request: GetLearningProgressionPathsRequest
) -> ToolResult:
    """Retrieve bounded alternative directed buildsTowards paths.

    Parameters
    ----------
    context
        Injected immutable application state.
    request
        Same-package distinct standard selectors and positive depth/path bounds.

    Returns
    -------
    ToolResult
        Derived simple paths, original hops, frontier and completeness counters.
    """

    with tool_error_boundary("get_learning_progression_paths"):
        result = get_app_state(
            context
        ).learning_progressions_service.get_learning_progression_paths(request=request)
        return _build_progression_result(result)


async def get_standard_progressions(
    *, context: Context, request: GetStandardProgressionsRequest
) -> ToolResult:
    """Retrieve a bounded page of direct builds and symmetric related concepts.

    Parameters
    ----------
    context
        Injected immutable application state.
    request
        Standard selector, connection meaning, page bound and optional cursor.

    Returns
    -------
    ToolResult
        Original edges and endpoint tables with continuation and relative meanings.
    """

    with tool_error_boundary("get_standard_progressions"):
        result = get_app_state(
            context
        ).learning_progressions_service.get_standard_progressions(request=request)
        return _build_progression_result(result)


async def search_learning_progressions(
    *, context: Context, request: SearchLearningProgressionsRequest
) -> ToolResult:
    """Discover a bounded page of stored relationships under endpoint filters.

    Parameters
    ----------
    context
        Injected immutable application state.
    request
        Framework route, optional selectors/types/facets and explicit endpoint scope.

    Returns
    -------
    ToolResult
        Original evidence and endpoint matches, page counts and bound cursor.
    """

    with tool_error_boundary("search_learning_progressions"):
        result = get_app_state(
            context
        ).learning_progressions_service.search_learning_progressions(request=request)
        return _build_progression_result(result)


async def traverse_learning_progressions(
    *, context: Context, request: TraverseLearningProgressionsRequest
) -> ToolResult:
    """Traverse bounded upstream or downstream buildsTowards evidence.

    Parameters
    ----------
    context
        Injected immutable application state.
    request
        Exact origin selector, direction and finite depth/node/edge bounds.

    Returns
    -------
    ToolResult
        Derived subgraph with original directed hops, distances and frontier.
    """

    with tool_error_boundary("traverse_learning_progressions"):
        result = get_app_state(
            context
        ).learning_progressions_service.traverse_learning_progressions(request=request)
        return _build_progression_result(result)


def register_learning_progression_tools(
    server: FastMCP[dict[str, AppState]],
) -> None:
    """Register the five stored LP contracts with exact schemas and read-only hints.

    Parameters
    ----------
    server
        Application server receiving explicitly approved bounded query adapters.
    """

    server.tool(
        annotations=READ_ONLY_TOOL_ANNOTATIONS,
        description=(
            "Get one exact stored buildsTowards or relatesTo relationship in a "
            "framework/snapshot, with both standards, generated judgment and "
            "provenance links. Missing or non-LP IDs fail explicitly."
        ),
        name="get_learning_progression",
        output_schema=result_schema(GetLearningProgressionResult),
        title="Get Learning Progression",
    )(get_learning_progression)
    server.tool(
        annotations=READ_ONLY_TOOL_ANNOTATIONS,
        description=(
            "Find bounded alternative directed simple buildsTowards paths between "
            "distinct standards in one package. Defaults: depth 6, paths 3; maxima "
            "12/20, work/queue 5000, result 1 MiB. Incomplete absence is explicit."
        ),
        name="get_learning_progression_paths",
        output_schema=result_schema(GetLearningProgressionPathsResult),
        title="Get Learning Progression Paths",
    )(get_learning_progression_paths)
    server.tool(
        annotations=READ_ONLY_TOOL_ANNOTATIONS,
        description=(
            "Get incoming/outgoing buildsTowards and symmetric relatesTo connections "
            "of an exact standard. Default page 25, maximum 100, work 5000, result "
            "1 MiB. Preserve stored orientation and replay cursors unchanged."
        ),
        name="get_standard_progressions",
        output_schema=result_schema(ProgressionCollectionResult),
        title="Get Standard Progressions",
    )(get_standard_progressions)
    server.tool(
        annotations=READ_ONLY_TOOL_ANNOTATIONS,
        description=(
            "Discover stored LP edges using exact selectors, relationship types and "
            "endpoint facets. either/both/source/target applies the whole filter "
            "conjunction to endpoints. Default page 25, maximum 100, work 5000, "
            "result 1 MiB; cursors bind the exact route, selection and limits."
        ),
        name="search_learning_progressions",
        output_schema=result_schema(ProgressionCollectionResult),
        title="Search Learning Progressions",
    )(search_learning_progressions)
    server.tool(
        annotations=READ_ONLY_TOOL_ANNOTATIONS,
        description=(
            "Traverse upstream/downstream buildsTowards from an exact standard. "
            "Defaults: depth 8, nodes/edges 100; maxima 12/250/100, work 5000, "
            "result 1 MiB. Preserve branches, original directions and partialness; "
            "hasChild and relatesTo are not progression hops."
        ),
        name="traverse_learning_progressions",
        output_schema=result_schema(TraverseLearningProgressionsResult),
        title="Traverse Learning Progressions",
    )(traverse_learning_progressions)
