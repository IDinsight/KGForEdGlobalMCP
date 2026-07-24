"""This package exposes generic prompt workflow contracts and services.

The package contains curriculum-agnostic prompt definitions, optional versioned
framework-local soft guidance, rights-aware prompt policy, deterministic rendering, and
bootstrap-time prompt configuration loading. Importing it performs no filesystem access,
application bootstrap, package loading, or FastMCP registration.
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
