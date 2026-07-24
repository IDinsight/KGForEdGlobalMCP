"""This package exposes deterministic cross-framework evidence retrieval as a FastMCP
tool.

This module provides the protocol-facing ``compare_framework_evidence`` tool and its
explicit registration function. The tool accepts the typed discriminated comparison
request, obtains the lifespan-owned ``ComparisonService``, delegates the complete
operation to that ordinary service, and returns both a stable readable summary and the
full structured comparison result.

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
    catalog_resource_links,
    get_app_state,
    result_schema,
)
from kgfegmcp.services.comparison_models import (
    CompareFrameworkEvidenceResult,
    FrameworkComparisonRequest,
)

if TYPE_CHECKING:
    # Third Party Library
    from fastmcp import FastMCP

    # Package Library
    from kgfegmcp.bootstrap import AppState


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
    request: FrameworkComparisonRequest, context: Context
) -> ToolResult:
    """Return independently bounded exact-package evidence for selected frameworks.

    Parameters
    ----------
    request
        Discriminated text, exact-code, or code-prefix comparison request.
    context
        Injected FastMCP request context containing immutable application state.

    Returns
    -------
    ToolResult
        Readable summary and complete ``CompareFrameworkEvidenceResult`` evidence.
    """

    with tool_error_boundary("compare_framework_evidence"):
        state = get_app_state(context)
        result = state.comparison_service.compare_framework_evidence(request)
        return build_tool_result(
            content=_format_comparison_result(result),
            resource_links=catalog_resource_links(),
            result=result,
        )


def register_comparison_tools(server: FastMCP[dict[str, AppState]]) -> None:
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
