"""This module registers the experimental multi-grade classroom planning workflow.

A multi-grade classroom holds several grades at once, and planning for it needs one
thing standards alone cannot give: what is shared across the grades in the room versus
what is specific to each. Learning components carry that, because a component supporting
standards in more than one grade is the teach-together core and a component supporting
only one is that grade's differentiated work.

This workflow has no source-only fallback. A package without learning components is
refused rather than degraded into parallel mono-grade plans under a multi-grade heading.
"""

# Third Party Library
from fastmcp import Context
from fastmcp.prompts import PromptResult

# Package Library
from kgfegmcp.domain.identifiers import FrameworkId
from kgfegmcp.mcp.errors import prompt_error_boundary
from kgfegmcp.mcp.prompts import build_prompt_result
from kgfegmcp.mcp.prompts.arguments import (
    LessonDurationMinutesArgument,
    MultigradeGradesInRoomArgument,
    OptionalLanguageTagArgument,
    OptionalPromptLearnerContextArgument,
    OptionalPromptLocalContextArgument,
    OptionalSnapshotIdArgument,
    PromptFocusModeArgument,
    PromptFocusTextArgument,
)
from kgfegmcp.mcp.tools import get_app_state
from kgfegmcp.prompts.models import PromptFocusMode


async def multigrade_lesson_plan(
    *,
    context: Context,
    focus_mode: PromptFocusModeArgument = PromptFocusMode.TOPIC,
    framework_id: FrameworkId,
    grades_in_room: MultigradeGradesInRoomArgument,
    learner_context: OptionalPromptLearnerContextArgument = None,
    lesson_duration_minutes: LessonDurationMinutesArgument = 45,
    local_context: OptionalPromptLocalContextArgument = None,
    output_language: OptionalLanguageTagArgument = None,
    snapshot_id: OptionalSnapshotIdArgument = None,
    topic_or_standard: PromptFocusTextArgument,
) -> PromptResult:
    """Return a workflow for planning one lesson across several grades at once.

    Parameters
    ----------
    context
        Injected FastMCP request context containing immutable application state.
    focus_mode
        Interpretation mode for ``topic_or_standard``; statement-code support depends
        on the selected framework profile.
    framework_id
        Exact conceptual framework family identifier.
    grades_in_room
        Two to eight distinct grades or stages sharing the classroom.
    learner_context
        Optional untrusted description of the learners.
    lesson_duration_minutes
        Planned lesson length in minutes.
    local_context
        Optional untrusted description of the setting.
    output_language
        Optional requested output language tag.
    snapshot_id
        Optional exact snapshot; omission uses unique-current routing.
    topic_or_standard
        Topic text, stable statement code, or exact identifier selected by
        ``focus_mode``.

    Returns
    -------
    PromptResult
        One deterministic user-role prompt message with exact runtime metadata.
    """

    with prompt_error_boundary("multigrade_lesson_plan"):
        state = get_app_state(context)
        result = state.prompt_service.multigrade_lesson_plan(
            focus_mode=focus_mode,
            framework_id=framework_id,
            grades_in_room=grades_in_room,
            learner_context=learner_context,
            lesson_duration_minutes=lesson_duration_minutes,
            local_context=local_context,
            output_language=output_language,
            snapshot_id=snapshot_id,
            topic_or_standard=topic_or_standard,
        )
        return build_prompt_result(result)
