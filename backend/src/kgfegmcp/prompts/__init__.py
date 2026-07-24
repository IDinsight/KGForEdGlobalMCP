"""This package provides ordinary application contracts and services for prompt
workflows.

This package contains the curriculum-agnostic prompt definitions, typed prompt and
configuration models, optional framework-local prompt-configuration loading,
correctness-critical prompt policy, and deterministic prompt-rendering service used by
the FastMCP adapter layer.

Framework-local configuration may customize only declared soft-guidance sections.
Missing configuration falls back to the generic server-level prompts, while present
configuration must pass strict bootstrap-time validation.

Importing this package performs no filesystem access, application bootstrap, curriculum
package loading, prompt rendering, FastMCP registration, LLM invocation, or MCP
sampling.
"""

# Package Library
from kgfegmcp.prompts.models import (
    FrameworkPromptConfig,
    InferredProgressionHypothesisGuidance,
    LoadedPromptConfig,
    ProgressionDirection,
    PromptConfigRegistry,
    PromptFocusMode,
    PromptGuidanceBlock,
    PromptGuidanceMode,
    PromptName,
    PromptOverlays,
    PromptRenderResult,
    SharedPromptGuidance,
    StudentHandbookSectionGuidance,
    StudentStudySupportGuidance,
    StudyDifficulty,
    TeacherGuideDraftGuidance,
)
from kgfegmcp.prompts.policy import PromptPolicy
from kgfegmcp.prompts.repository import PromptConfigRepository
from kgfegmcp.prompts.service import PromptService

__all__ = [
    "FrameworkPromptConfig",
    "InferredProgressionHypothesisGuidance",
    "LoadedPromptConfig",
    "ProgressionDirection",
    "PromptConfigRegistry",
    "PromptConfigRepository",
    "PromptFocusMode",
    "PromptGuidanceBlock",
    "PromptGuidanceMode",
    "PromptName",
    "PromptOverlays",
    "PromptPolicy",
    "PromptRenderResult",
    "PromptService",
    "SharedPromptGuidance",
    "StudentHandbookSectionGuidance",
    "StudentStudySupportGuidance",
    "StudyDifficulty",
    "TeacherGuideDraftGuidance",
]
