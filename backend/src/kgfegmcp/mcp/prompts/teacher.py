"""This module exposes the teacher-oriented FastMCP prompt workflow.

This module defines the public ``teacher_guide_draft`` prompt function. The function
accepts curriculum-agnostic, typed MCP arguments, retrieves immutable application state
from the injected FastMCP ``Context``, delegates deterministic rendering to
``PromptService``, and converts the result into one FastMCP user-role prompt message.

The adapter does not load prompt configuration, interpret curriculum packages, enforce
rights independently, search standards, traverse graphs, generate pedagogy, call an
LLM, or use MCP sampling.
"""

# Third Party Library
from fastmcp import Context
from fastmcp.prompts import PromptResult

# Package Library
from kgfegmcp.domain.identifiers import FrameworkId, LanguageTag, SnapshotId
from kgfegmcp.mcp.errors import prompt_error_boundary
from kgfegmcp.mcp.prompts import build_prompt_result
from kgfegmcp.mcp.tools import get_app_state
from kgfegmcp.prompts.models import (
    LessonDurationMinutes,
    PromptFocusMode,
    PromptFocusText,
    PromptGradeOrStage,
    PromptLearnerContext,
    PromptLocalContext,
    PromptMaterials,
)


async def teacher_guide_draft(
    *,
    available_materials: PromptMaterials | None = None,
    context: Context,
    focus_mode: PromptFocusMode = PromptFocusMode.TOPIC,
    framework_id: FrameworkId,
    grade_or_stage: PromptGradeOrStage,
    learner_context: PromptLearnerContext | None = None,
    lesson_duration_minutes: LessonDurationMinutes = 45,
    local_context: PromptLocalContext | None = None,
    output_language: LanguageTag | None = None,
    snapshot_id: SnapshotId | None = None,
    topic_or_standard: PromptFocusText,
) -> PromptResult:
    """Return a workflow for an evidence-grounded generated teacher guide.

    Parameters
    ----------
    available_materials
        Optional untrusted description of material constraints.
    context
        Injected FastMCP request context containing immutable application state.
    focus_mode
        Topic, statement code, or explicit identifier namespace.
    framework_id
        Exact conceptual framework identifier.
    grade_or_stage
        Local or normalized grade/stage context.
    learner_context
        Optional anonymous learner context without sensitive education records.
    lesson_duration_minutes
        Generated lesson duration from 10 through 240 minutes.
    local_context
        Optional local nuance treated as untrusted caller context.
    output_language
        Optional BCP 47-style output language tag.
    snapshot_id
        Optional exact immutable snapshot identifier; omission uses unique-current
        routing.
    topic_or_standard
        Topic text, statement code, or exact identifier selected by ``focus_mode``.

    Returns
    -------
    PromptResult
        One deterministic user-role prompt message with exact runtime metadata.
    """

    with prompt_error_boundary("teacher_guide_draft"):
        state = get_app_state(context)
        result = state.prompt_service.teacher_guide_draft(
            available_materials=available_materials,
            focus_mode=focus_mode,
            framework_id=framework_id,
            grade_or_stage=grade_or_stage,
            learner_context=learner_context,
            lesson_duration_minutes=lesson_duration_minutes,
            local_context=local_context,
            output_language=output_language,
            snapshot_id=snapshot_id,
            topic_or_standard=topic_or_standard,
        )
        return build_prompt_result(result)
