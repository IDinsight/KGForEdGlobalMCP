"""This module exposes the administrator alignment-review workflow as a FastMCP prompt.

This module provides the protocol-facing ``administrator_alignment_review`` prompt for
reviewing evidence from one source framework and one target framework. The prompt
collects typed request parameters, obtains the lifespan-owned application state,
delegates prompt construction to the ordinary ``PromptService``, and converts the
rendered result into a FastMCP ``PromptResult``.

The prompt prepares instructions for a client-side language model; it does not retrieve
standards evidence itself. The generated workflow directs the client to use
``compare_framework_evidence`` and preserves the exact framework, snapshot, package,
profile, rights, provenance, and local-guidance boundaries supplied by
``PromptService``.

This module is a thin MCP adapter. It performs no search, graph traversal, ranking,
alignment creation, equivalence determination, persistence, source-package mutation,
server-side LLM invocation, or MCP sampling. Retrieved similarities remain candidate
evidence, and any comparative interpretation remains explicitly LLM-inferred.
"""

# Third Party Library
from fastmcp import Context
from fastmcp.prompts import PromptResult

# Package Library
from kgfegmcp.domain.identifiers import FrameworkId
from kgfegmcp.mcp.errors import prompt_error_boundary
from kgfegmcp.mcp.prompts import build_multi_context_prompt_result
from kgfegmcp.mcp.prompts.arguments import (
    ComparisonMatchLimitArgument,
    ComparisonSearchModeArgument,
    IncludeContextPathsArgument,
    OptionalLanguageTagArgument,
    OptionalPromptGradeOrStageArgument,
    OptionalPromptLocalContextArgument,
    OptionalSnapshotIdArgument,
    PromptFocusTextArgument,
)
from kgfegmcp.mcp.tools import get_app_state
from kgfegmcp.prompts.models import ComparisonSearchMode


async def administrator_alignment_review(
    *,
    context: Context,
    include_context_paths: IncludeContextPathsArgument = True,
    local_context: OptionalPromptLocalContextArgument = None,
    matches_per_framework: ComparisonMatchLimitArgument = 5,
    output_language: OptionalLanguageTagArgument = None,
    search_mode: ComparisonSearchModeArgument = ComparisonSearchMode.TEXT,
    source_framework_id: FrameworkId,
    source_grade_or_stage: OptionalPromptGradeOrStageArgument = None,
    source_snapshot_id: OptionalSnapshotIdArgument = None,
    target_framework_id: FrameworkId,
    target_grade_or_stage: OptionalPromptGradeOrStageArgument = None,
    target_snapshot_id: OptionalSnapshotIdArgument = None,
    topic_or_query: PromptFocusTextArgument,
) -> PromptResult:
    """Return an evidence-grounded administrative comparison workflow.

    Parameters
    ----------
    context
        Injected FastMCP request context containing immutable application state.
    include_context_paths
        Whether the comparison call requests bounded hierarchy paths.
    local_context
        Optional untrusted administrative context.
    matches_per_framework
        Independent package-local candidate quota, from one through ten.
    output_language
        Optional BCP 47-style output language tag.
    search_mode
        Text, exact-code, or code-prefix comparison mode.
    source_framework_id
        Exact source conceptual framework identifier.
    source_grade_or_stage
        Optional source-local grade or stage review scope.
    source_snapshot_id
        Optional exact source snapshot identifier.
    target_framework_id
        Exact target conceptual framework identifier.
    target_grade_or_stage
        Optional target-local grade or stage review scope.
    target_snapshot_id
        Optional exact target snapshot identifier.
    topic_or_query
        Topic text or code query used for evidence retrieval.

    Returns
    -------
    PromptResult
        One deterministic user-role prompt with all exact package audit metadata.
    """

    with prompt_error_boundary("administrator_alignment_review"):
        state = get_app_state(context)
        result = state.prompt_service.administrator_alignment_review(
            include_context_paths=include_context_paths,
            local_context=local_context,
            matches_per_framework=matches_per_framework,
            output_language=output_language,
            search_mode=search_mode,
            source_framework_id=source_framework_id,
            source_grade_or_stage=source_grade_or_stage,
            source_snapshot_id=source_snapshot_id,
            target_framework_id=target_framework_id,
            target_grade_or_stage=target_grade_or_stage,
            target_snapshot_id=target_snapshot_id,
            topic_or_query=topic_or_query,
        )
        return build_multi_context_prompt_result(result)
