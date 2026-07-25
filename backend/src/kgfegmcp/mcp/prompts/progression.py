"""This module exposes the inferred-progression FastMCP prompt workflow.

This module defines the public ``inferred_progression_hypothesis`` prompt function. The
function accepts curriculum-agnostic, typed MCP arguments, retrieves immutable
application state from the injected FastMCP ``Context``, delegates deterministic
rendering to ``PromptService``, and converts the result into one FastMCP user-role
prompt message.

The adapter does not create Learning Progressions data, persist progression edges, load
prompt configuration, enforce rights independently, search standards, traverse graphs
during prompt retrieval, call an LLM, or use MCP sampling. Any progression produced by
the client-side model remains explicitly labeled as an LLM-inferred hypothesis.
"""

# Third Party Library
from fastmcp import Context
from fastmcp.prompts import PromptResult

# Package Library
from kgfegmcp.domain.identifiers import FrameworkId, LanguageTag, SnapshotId
from kgfegmcp.mcp.errors import prompt_error_boundary
from kgfegmcp.mcp.prompts import build_prompt_result
from kgfegmcp.mcp.prompts.arguments import (
    PromptFocusModeArgument,
    PromptFocusTextArgument,
)
from kgfegmcp.mcp.tools import get_app_state
from kgfegmcp.prompts.models import (
    ProgressionCandidateLimit,
    ProgressionDirection,
    PromptFocusMode,
    PromptGradeOrStage,
    PromptLocalContext,
)


async def inferred_progression_hypothesis(
    *,
    candidate_limit: ProgressionCandidateLimit = 8,
    context: Context,
    direction: ProgressionDirection = ProgressionDirection.BOTH,
    focus_mode: PromptFocusModeArgument = PromptFocusMode.TOPIC,
    framework_id: FrameworkId,
    grade_or_stage: PromptGradeOrStage,
    local_context: PromptLocalContext | None = None,
    output_language: LanguageTag | None = None,
    snapshot_id: SnapshotId | None = None,
    topic_or_standard: PromptFocusTextArgument,
) -> PromptResult:
    """Return a workflow for an evidence-linked inferred progression hypothesis.

    Parameters
    ----------
    candidate_limit
        Maximum number of standards candidates to review, from 2 through 20.
    context
        Injected FastMCP request context containing immutable application state.
    direction
        Earlier-to-later, later-to-earlier, or bidirectional review.
    focus_mode
        Interpretation mode for ``topic_or_standard``; statement-code support depends
        on the selected framework profile.
    framework_id
        Exact conceptual framework identifier.
    grade_or_stage
        Local or normalized grade/stage scope for candidate retrieval.
    local_context
        Optional local nuance treated as untrusted caller context.
    output_language
        Optional BCP 47-style output language tag.
    snapshot_id
        Optional exact immutable snapshot identifier; omission uses unique-current
        routing.
    topic_or_standard
        Topic text, stable statement code, or exact anchor selected by ``focus_mode``.

    Returns
    -------
    PromptResult
        One deterministic user-role prompt message with exact runtime metadata.
    """

    with prompt_error_boundary("inferred_progression_hypothesis"):
        state = get_app_state(context)
        result = state.prompt_service.inferred_progression_hypothesis(
            candidate_limit=candidate_limit,
            direction=direction,
            focus_mode=focus_mode,
            framework_id=framework_id,
            grade_or_stage=grade_or_stage,
            local_context=local_context,
            output_language=output_language,
            snapshot_id=snapshot_id,
            topic_or_standard=topic_or_standard,
        )
        return build_prompt_result(result)
