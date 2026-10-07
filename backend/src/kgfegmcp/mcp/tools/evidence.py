"""Expose paged native resource evidence through one thin read-only MCP tool."""

# Future Library
from __future__ import annotations

# Standard Library
from typing import TYPE_CHECKING

# Third Party Library
from fastmcp import Context
from fastmcp.tools.base import ToolResult
from mcp.types import CallToolResult

# Package Library
from kgfegmcp.mcp.errors import tool_error_boundary
from kgfegmcp.mcp.tools import (
    READ_ONLY_TOOL_ANNOTATIONS,
    build_tool_result,
    get_app_state,
    result_schema,
)
from kgfegmcp.resources.evidence import (
    evidence_result_text,
    read_evidence_window,
    require_evidence_result_size,
)
from kgfegmcp.resources.evidence_models import ReadEvidenceRequest, ReadEvidenceResult

if TYPE_CHECKING:
    # Third Party Library
    from fastmcp import FastMCP

    # Package Library
    from kgfegmcp.bootstrap import AppState


async def read_evidence(
    *, context: Context, request: ReadEvidenceRequest
) -> ToolResult:
    """Return one bounded window of a native resource's authorized content.

    Parameters
    ----------
    context
        Injected immutable application state.
    request
        Resource URI, window size and optional continuation cursor.

    Returns
    -------
    ToolResult
        Canonical JSON text and structured content within both envelope ceilings.
    """

    with tool_error_boundary("read_evidence"):
        result = read_evidence_window(
            request=request, resource_service=get_app_state(context).resource_service
        )
        tool_result = build_tool_result(
            content=evidence_result_text(result), result=result
        )

        # Measure what is actually emitted, not only the candidate estimate.
        emitted = CallToolResult(
            _meta=tool_result.meta,
            content=tool_result.content,
            isError=tool_result.is_error,
            structuredContent=tool_result.structured_content,
        )
        require_evidence_result_size(
            emitted.model_dump(by_alias=True, exclude_none=True, mode="json")
        )
        return tool_result


def register_evidence_tools(server: FastMCP[dict[str, AppState]]) -> None:
    """Register the read-only evidence reader with its exact schemas.

    Parameters
    ----------
    server
        Application server receiving the approved evidence adapter.
    """

    server.tool(
        annotations=READ_ONLY_TOOL_ANNOTATIONS,
        description=(
            "Read the full permitted content of one kgfegmcp resource URI copied "
            "from a tool result (or kgfegmcp://catalog) in UTF-8 windows, under "
            "native rights and size limits. Default 16384 bytes, maximum 32768. "
            "Replay page.nextRequest until page.isComplete; joined windows match "
            "metadata.contentSha256."
        ),
        name="read_evidence",
        output_schema=result_schema(ReadEvidenceResult),
        title="Read Evidence",
    )(read_evidence)
