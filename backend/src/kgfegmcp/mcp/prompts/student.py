"""This module exposes the student-oriented generic FastMCP prompts.

The module implements ``student_study_support`` and ``student_handbook_section`` as thin
adapters over the ordinary prompt service. The functions accept curriculum-agnostic
parameters, obtain exact lifespan state through FastMCP ``Context``, and return one
rights-gated deterministic prompt workflow.
"""

# Future Library
from __future__ import annotations

# Third Party Library
from fastmcp import Context
from fastmcp.prompts import PromptResult

# Package Library
from kgfegmcp.domain.identifiers import FrameworkId, LanguageTag, SnapshotId
from kgfegmcp.mcp.errors import prompt_error_boundary
from kgfegmcp.mcp.prompts import build_prompt_result
from kgfegmcp.mcp.tools import get_app_state
from kgfegmcp.prompts.models import (
    HandbookWordCount,
    PracticeCount,
    PromptFocusMode,
    PromptFocusText,
    PromptGradeOrStage,
    PromptLocalContext,
    StudyDifficulty,
)


async def student_handbook_section(
    *,
    context: Context,
    focus_mode: PromptFocusMode = PromptFocusMode.TOPIC,
    framework_id: FrameworkId,
    grade_or_stage: PromptGradeOrStage,
    local_context: PromptLocalContext | None = None,
    output_language: LanguageTag | None = None,
    snapshot_id: SnapshotId | None = None,
    target_word_count: HandbookWordCount = 500,
    topic_or_standard: PromptFocusText,
) -> PromptResult:
    """Return a workflow for an evidence-grounded generated handbook section.

    Parameters
    ----------
    context
        Injected FastMCP request context containing immutable application state.
    focus_mode
        Topic, statement code, or explicit identifier namespace.
    framework_id
        Exact conceptual framework identifier.
    grade_or_stage
        Anonymous local or normalized grade/stage context.
    local_context
        Optional anonymous local nuance treated as untrusted caller context.
    output_language
        Optional BCP 47-style output language tag.
    snapshot_id
        Optional exact immutable snapshot identifier; omission uses unique-current routing.
    target_word_count
        Approximate generated section length, from 150 through 1500 words.
    topic_or_standard
        Topic text, statement code, or exact identifier selected by ``focus_mode``.

    Returns
    -------
    PromptResult
        One deterministic user-role prompt message with exact runtime metadata.
    """

    with prompt_error_boundary("student_handbook_section"):
        state = get_app_state(context)
        result = state.prompt_service.student_handbook_section(
            focus_mode=focus_mode,
            framework_id=framework_id,
            grade_or_stage=grade_or_stage,
            local_context=local_context,
            output_language=output_language,
            snapshot_id=snapshot_id,
            target_word_count=target_word_count,
            topic_or_standard=topic_or_standard,
        )
        return build_prompt_result(result)


async def student_study_support(
    *,
    context: Context,
    difficulty: StudyDifficulty = StudyDifficulty.ON_LEVEL,
    focus_mode: PromptFocusMode = PromptFocusMode.TOPIC,
    framework_id: FrameworkId,
    grade_or_stage: PromptGradeOrStage,
    local_context: PromptLocalContext | None = None,
    output_language: LanguageTag | None = None,
    practice_count: PracticeCount = 5,
    snapshot_id: SnapshotId | None = None,
    topic_or_standard: PromptFocusText,
) -> PromptResult:
    """Return a workflow for evidence-grounded generated student study support.

    Parameters
    ----------
    context
        Injected FastMCP request context containing immutable application state.
    difficulty
        Requested generated support level.
    focus_mode
        Topic, statement code, or explicit identifier namespace.
    framework_id
        Exact conceptual framework identifier.
    grade_or_stage
        Anonymous local or normalized grade/stage context.
    local_context
        Optional anonymous local nuance treated as untrusted caller context.
    output_language
        Optional BCP 47-style output language tag.
    practice_count
        Number of generated practice items requested, from 1 through 10.
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

    with prompt_error_boundary("student_study_support"):
        state = get_app_state(context)
        result = state.prompt_service.student_study_support(
            difficulty=difficulty,
            focus_mode=focus_mode,
            framework_id=framework_id,
            grade_or_stage=grade_or_stage,
            local_context=local_context,
            output_language=output_language,
            practice_count=practice_count,
            snapshot_id=snapshot_id,
            topic_or_standard=topic_or_standard,
        )
        return build_prompt_result(result)
