"""This module exposes the inferred-progression FastMCP prompt workflow.

This module defines the public ``inferred_progression_hypothesis`` prompt function. The
function accepts curriculum-agnostic, typed MCP arguments, retrieves immutable
application state from the injected FastMCP ``Context``, delegates deterministic
rendering to ``PromptService``, and converts the result into one FastMCP user-role
prompt message.

The adapter does not create Learning Progressions data, persist progression edges, load
prompt configuration, enforce rights independently, collect evidence, call an LLM, or
use MCP sampling. The rendered workflow requires Claude to use the deterministic
``collect_progression_evidence`` tool, whose retained-candidate limit is enforced by
the server.
"""

# Third Party Library
from fastmcp import Context
from fastmcp.prompts import PromptResult

# Package Library
from kgfegmcp.domain.identifiers import FrameworkId
from kgfegmcp.mcp.errors import prompt_error_boundary
from kgfegmcp.mcp.prompts import build_prompt_result
from kgfegmcp.mcp.prompts.arguments import (
    OptionalLanguageTagArgument,
    OptionalPromptLocalContextArgument,
    OptionalSnapshotIdArgument,
    ProgressionCandidateLimitArgument,
    ProgressionDirectionArgument,
    ProgressionLocalGradeLabelsArgument,
    ProgressionNormalizedGradesArgument,
    PromptFocusModeArgument,
    PromptFocusTextArgument,
)
from kgfegmcp.mcp.tools import get_app_state
from kgfegmcp.prompts.models import ProgressionDirection, PromptFocusMode


async def inferred_progression_hypothesis(
    *,
    candidate_limit: ProgressionCandidateLimitArgument = 8,
    context: Context,
    direction: ProgressionDirectionArgument = ProgressionDirection.BOTH,
    focus_mode: PromptFocusModeArgument = PromptFocusMode.TOPIC,
    framework_id: FrameworkId,
    local_context: OptionalPromptLocalContextArgument = None,
    local_grade_labels: ProgressionLocalGradeLabelsArgument = (),
    normalized_grades: ProgressionNormalizedGradesArgument = (),
    output_language: OptionalLanguageTagArgument = None,
    snapshot_id: OptionalSnapshotIdArgument = None,
    topic_or_standard: PromptFocusTextArgument,
) -> PromptResult:
    """Return a workflow for an evidence-linked inferred progression hypothesis.

    Parameters
    ----------
    candidate_limit
        Hard maximum number of unique standard-item candidates, from 2 through 20.
    context
        Injected FastMCP request context containing immutable application state.
    direction
        Earlier-to-later, later-to-earlier, or bidirectional review.
    focus_mode
        Interpretation mode for ``topic_or_standard``; statement-code support depends
        on the selected framework profile.
    framework_id
        Exact conceptual framework identifier.
    local_context
        Optional local nuance treated as untrusted caller context.
    local_grade_labels
        Exact source-facing grades or stages parsed from a JSON-array prompt value.
    normalized_grades
        Normalized retrieval facets parsed from a JSON-array prompt value.
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
            local_context=local_context,
            local_grade_labels=local_grade_labels,
            normalized_grades=normalized_grades,
            output_language=output_language,
            snapshot_id=snapshot_id,
            topic_or_standard=topic_or_standard,
        )
        return build_prompt_result(result)
