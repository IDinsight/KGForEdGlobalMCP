"""This module exposes deterministic bounded progression evidence as a FastMCP tool.

The public ``collect_progression_evidence`` tool accepts one exact framework route,
explicit local and normalized grade arrays, a typed focus mode, and a hard candidate
limit. It delegates all discovery, grouping expansion, deduplication, grade-balanced
selection, and hierarchy retrieval to ``ProgressionEvidenceService``.

The adapter returns retrieval candidates only. It does not infer, create, persist, or
approve a learning progression, call a language model, or use MCP sampling.
"""

# Standard Library
from typing import TYPE_CHECKING, Annotated

# Third Party Library
from fastmcp import Context
from fastmcp.tools.base import ToolResult
from pydantic import Field

# Package Library
from kgfegmcp.domain.identifiers import FrameworkId, SnapshotId
from kgfegmcp.mcp.errors import tool_error_boundary
from kgfegmcp.mcp.tools import (
    READ_ONLY_TOOL_ANNOTATIONS,
    build_tool_result,
    get_app_state,
    result_schema,
)
from kgfegmcp.services.models import CatalogFilterValue
from kgfegmcp.services.progression_models import (
    CollectProgressionEvidenceRequest,
    CollectProgressionEvidenceResult,
    ProgressionEvidenceFocusMode,
)

if TYPE_CHECKING:
    # Third Party Library
    from fastmcp import FastMCP

    # Package Library
    from kgfegmcp.bootstrap import AppState

ProgressionGradeFilters = Annotated[
    tuple[CatalogFilterValue, ...],
    Field(
        description=(
            "Supply each grade or stage as a separate array item. Do not combine "
            "multiple grades into one comma-separated string."
        ),
        max_length=32,
    ),
]
ProgressionFocusText = Annotated[
    str,
    Field(
        description=(
            "Topic text, stable statement code, graph node ID, CASE UUID, or CASE URI "
            "interpreted according to focus_mode."
        ),
        max_length=512,
        min_length=1,
    ),
]


def _format_progression_evidence(result: CollectProgressionEvidenceResult) -> str:
    """Format one bounded progression evidence result as readable source evidence.

    Parameters
    ----------
    result
        Complete deterministic candidate discovery and selection result.

    Returns
    -------
    str
        Stable summary of scope, counts, retained identities, and warnings.
    """

    lines = [
        f"Framework ID: {result.request.framework_id}",
        f"Snapshot ID: {result.request.snapshot_id}",
        f"Graph-package ID: {result.request.graph_package_id}",
        f"Selection policy: {result.selection_policy.value}",
        f"Candidate limit: {result.request.candidate_limit}",
        f"Discovered candidates: {result.discovered_candidate_count}",
        f"Retained candidates: {result.retained_candidate_count}",
        f"Excluded candidates: {result.excluded_candidate_count}",
        f"Candidate limit applied: {str(result.candidate_limit_applied).lower()}",
        f"Discovery complete: {str(result.discovery_complete).lower()}",
        "",
        "Retained candidate standards:",
    ]

    if not result.retained_candidates:
        lines.append("- none")

    for candidate in result.retained_candidates:
        node = candidate.node
        description = " ".join((node.description or "[no description]").split())
        lines.extend(
            (
                (
                    f"{candidate.selection_rank}. {node.statement_code or '[uncoded]'} "
                    f"| {node.node_id}"
                ),
                f"   Description: {description}",
                (
                    "   Local grade labels: "
                    + (", ".join(candidate.matched_local_grade_labels) or "none")
                ),
                (
                    "   Normalized grades: "
                    + (", ".join(candidate.matched_normalized_grades) or "none")
                ),
                (
                    "   Discovery methods: "
                    + ", ".join(method.value for method in candidate.discovery_methods)
                ),
                f"   Context complete: {str(candidate.context.is_complete).lower()}",
            )
        )

    lines.extend(("", "Scope coverage:"))

    for coverage in result.scope_coverage:
        lines.append(
            f"- {coverage.scope_kind.value}={coverage.scope_value}: "
            f"discovered={coverage.discovered_candidate_count}, "
            f"retained={coverage.retained_candidate_count}"
        )

    lines.extend(("", f"Warnings: {len(result.warnings)}"))

    if result.warnings:
        lines.extend(
            f"- {warning.code.value}: {warning.message}" for warning in result.warnings
        )
    else:
        lines.append("- none")

    lines.extend(
        (
            "",
            "Interpretation: Every retained node is a retrieval candidate. The tool "
            "does not assert a source-authored prerequisite, sequence, progression, "
            "difficulty relation, or learner mastery.",
        )
    )
    return "\n".join(lines)


async def collect_progression_evidence(
    *,
    candidate_limit: Annotated[int, Field(alias="candidateLimit", ge=2, le=20)] = 8,
    context: Context,
    focus_mode: Annotated[
        ProgressionEvidenceFocusMode, Field(alias="focusMode")
    ] = ProgressionEvidenceFocusMode.TOPIC,
    framework_id: Annotated[FrameworkId, Field(alias="frameworkId")],
    local_grade_labels: Annotated[
        ProgressionGradeFilters, Field(alias="localGradeLabels")
    ] = (),
    normalized_grades: Annotated[
        ProgressionGradeFilters, Field(alias="normalizedGrades")
    ] = (),
    snapshot_id: Annotated[SnapshotId | None, Field(alias="snapshotId")] = None,
    topic_or_standard: Annotated[ProgressionFocusText, Field(alias="topicOrStandard")],
) -> ToolResult:
    """Return a hard-bounded multi-grade standards evidence candidate set.

    Parameters
    ----------
    candidate_limit
        Maximum number of unique standard-item candidates returned, from 2 through 20.
    context
        Injected FastMCP request context containing immutable application state.
    focus_mode
        Topic, statement code, graph node ID, CASE UUID, or CASE URI interpretation.
    framework_id
        Exact conceptual framework identifier.
    local_grade_labels
        Exact source-facing grades or stages, each supplied as a separate array item.
    normalized_grades
        Normalized retrieval facets, each supplied as a separate array item.
    snapshot_id
        Optional exact immutable snapshot; omission uses unique-current routing.
    topic_or_standard
        Focus value interpreted according to ``focus_mode``.

    Returns
    -------
    ToolResult
        Readable summary and complete ``CollectProgressionEvidenceResult`` evidence.
    """

    request = CollectProgressionEvidenceRequest(
        candidate_limit=candidate_limit,
        focus_mode=focus_mode,
        framework_id=framework_id,
        local_grade_labels=local_grade_labels,
        normalized_grades=normalized_grades,
        snapshot_id=snapshot_id,
        topic_or_standard=topic_or_standard,
    )

    with tool_error_boundary("collect_progression_evidence"):
        state = get_app_state(context)
        result = state.progression_evidence_service.collect_progression_evidence(
            request
        )
        return build_tool_result(
            content=_format_progression_evidence(result), result=result
        )


def register_progression_tools(server: "FastMCP[dict[str, AppState]]") -> None:
    """Register the deterministic progression evidence tool explicitly.

    Parameters
    ----------
    server
        FastMCP server receiving the approved read-only evidence tool.
    """

    server.tool(
        annotations=READ_ONLY_TOOL_ANNOTATIONS,
        description=(
            "Collect a deterministic, grade-scoped, deduplicated, and hard-bounded "
            "set of Academic Standards retrieval candidates for an inferred "
            "progression review. Grouping and hierarchy nodes provide context but do "
            "not count toward the candidate limit."
        ),
        name="collect_progression_evidence",
        output_schema=result_schema(CollectProgressionEvidenceResult),
        title="Collect Progression Evidence",
    )(collect_progression_evidence)
