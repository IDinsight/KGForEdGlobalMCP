"""Expose deterministic stored-progression teaching instructions through FastMCP."""

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
    ProgressionLocalGradeLabelsArgument,
    ProgressionNormalizedGradesArgument,
    PromptFocusModeArgument,
    PromptFocusTextArgument,
)
from kgfegmcp.mcp.tools import get_app_state
from kgfegmcp.prompts.models import PromptFocusMode


async def learning_progression_teaching_sequence(
    *,
    context: Context,
    focus_mode: PromptFocusModeArgument = PromptFocusMode.TOPIC,
    framework_id: FrameworkId,
    local_context: OptionalPromptLocalContextArgument = None,
    local_grade_labels: ProgressionLocalGradeLabelsArgument = (),
    normalized_grades: ProgressionNormalizedGradesArgument = (),
    output_language: OptionalLanguageTagArgument = None,
    snapshot_id: OptionalSnapshotIdArgument = None,
    topic_or_standard: PromptFocusTextArgument,
) -> PromptResult:
    """Return a cited teaching-sequence workflow using bounded stored evidence.

    Parameters
    ----------
    context
        Injected FastMCP context holding the shared immutable application state.
    focus_mode
        Topic or exact identifier namespace; codes require profile support.
    framework_id
        Exact conceptual framework identifier.
    local_context
        Optional untrusted teacher context, at most 4,000 characters.
    local_grade_labels
        Up to 32 unique profile-valid source grade values, sent as a JSON array.
    normalized_grades
        Up to 32 unique normalized retrieval facets, sent as a JSON array.
    output_language
        Optional BCP 47-style output language tag.
    snapshot_id
        Optional exact snapshot; omission pins unique-current once.
    topic_or_standard
        Topic or exact selector text, at most 512 characters.

    Returns
    -------
    PromptResult
        One deterministic user-role message and exact runtime metadata.
    """

    with prompt_error_boundary("learning_progression_teaching_sequence"):
        state = get_app_state(context)
        result = state.prompt_service.learning_progression_teaching_sequence(
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
