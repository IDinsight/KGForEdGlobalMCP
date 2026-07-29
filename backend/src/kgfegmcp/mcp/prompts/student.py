"""This module exposes the student-oriented FastMCP prompt workflows.

This module defines the public ``student_study_support`` and
``student_handbook_section`` prompt functions. Each function accepts
curriculum-agnostic, typed MCP arguments, retrieves immutable application state from
the injected FastMCP ``Context``, delegates deterministic rendering to
``PromptService``, and converts the result into one FastMCP user-role prompt message.

The adapters contain no curriculum-specific branching and do not load files, resolve
prompt configuration, enforce rights independently, search standards, traverse graphs,
generate educational content, call an LLM, or use MCP sampling.
"""

# Third Party Library
from fastmcp import Context
from fastmcp.prompts import PromptResult

# Package Library
from kgfegmcp.domain.identifiers import FrameworkId
from kgfegmcp.mcp.errors import prompt_error_boundary
from kgfegmcp.mcp.prompts import build_prompt_result
from kgfegmcp.mcp.prompts.arguments import (
    HandbookWordCountArgument,
    OptionalLanguageTagArgument,
    OptionalPromptLocalContextArgument,
    OptionalSnapshotIdArgument,
    PracticeCountArgument,
    PromptFocusModeArgument,
    PromptFocusTextArgument,
    StudyDifficultyArgument,
)
from kgfegmcp.mcp.tools import get_app_state
from kgfegmcp.prompts.models import (
    PromptFocusMode,
    PromptGradeOrStage,
    StudyDifficulty,
)


async def student_handbook_section(
    *,
    context: Context,
    focus_mode: PromptFocusModeArgument = PromptFocusMode.TOPIC,
    framework_id: FrameworkId,
    grade_or_stage: PromptGradeOrStage,
    local_context: OptionalPromptLocalContextArgument = None,
    output_language: OptionalLanguageTagArgument = None,
    snapshot_id: OptionalSnapshotIdArgument = None,
    target_word_count: HandbookWordCountArgument = 500,
    topic_or_standard: PromptFocusTextArgument,
) -> PromptResult:
    """Return a workflow for an evidence-grounded generated handbook section.

    Parameters
    ----------
    context
        Injected FastMCP request context containing immutable application state.
    focus_mode
        Interpretation mode for ``topic_or_standard``; statement-code support depends
        on the selected framework profile.
    framework_id
        Exact conceptual framework identifier.
    grade_or_stage
        Anonymous local or normalized grade/stage context.
    local_context
        Optional anonymous local nuance treated as untrusted caller context.
    output_language
        Optional BCP 47-style output language tag.
    snapshot_id
        Optional exact immutable snapshot identifier; omission uses unique-current
        routing.
    target_word_count
        Approximate generated section length, from 150 through 1500 words.
    topic_or_standard
        Topic text, stable statement code, or exact identifier selected by
        ``focus_mode``.

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
    difficulty: StudyDifficultyArgument = StudyDifficulty.ON_LEVEL,
    focus_mode: PromptFocusModeArgument = PromptFocusMode.TOPIC,
    framework_id: FrameworkId,
    grade_or_stage: PromptGradeOrStage,
    local_context: OptionalPromptLocalContextArgument = None,
    output_language: OptionalLanguageTagArgument = None,
    practice_count: PracticeCountArgument = 5,
    snapshot_id: OptionalSnapshotIdArgument = None,
    topic_or_standard: PromptFocusTextArgument,
) -> PromptResult:
    """Return a workflow for evidence-grounded generated student study support.

    Parameters
    ----------
    context
        Injected FastMCP request context containing immutable application state.
    difficulty
        Requested generated support level.
    focus_mode
        Interpretation mode for ``topic_or_standard``; statement-code support depends
        on the selected framework profile.
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
        Topic text, stable statement code, or exact identifier selected by
        ``focus_mode``.

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
