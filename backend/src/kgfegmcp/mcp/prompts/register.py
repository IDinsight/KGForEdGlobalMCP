"""This module explicitly registers the four approved PR 11 FastMCP prompts.

Registration is imperative, deterministic, and invoked only by ``mcp/register.py``.
Importing this module does not construct settings, load application state, inspect
configuration files, or register components automatically.
"""

# Future Library
from __future__ import annotations

# Standard Library
from collections.abc import Callable
from typing import TYPE_CHECKING, Any

# Third Party Library
from fastmcp.prompts import Prompt

# Package Library
from kgfegmcp.mcp.prompts.progression import inferred_progression_hypothesis
from kgfegmcp.mcp.prompts.student import (
    student_handbook_section,
    student_study_support,
)
from kgfegmcp.mcp.prompts.teacher import teacher_guide_draft
from kgfegmcp.prompts.definitions import PROMPT_DESCRIPTIONS
from kgfegmcp.prompts.models import PROMPT_VERSION, PromptName

if TYPE_CHECKING:
    # Third Party Library
    from fastmcp import FastMCP

    # Package Library
    from kgfegmcp.bootstrap import AppState


def _register_prompt(
    *,
    description: str,
    function: Callable[..., Any],
    name: str,
    server: FastMCP[dict[str, AppState]],
    title: str,
) -> None:
    """Construct and register one versioned FastMCP prompt component.

    Parameters
    ----------
    description
        Stable component description shown during prompt listing.
    function
        Thin async prompt adapter used for rendering.
    name
        Exact registered MCP prompt name.
    server
        FastMCP server receiving the component.
    title
        Human-readable prompt title.
    """

    prompt = Prompt.from_function(
        description=description,
        fn=function,
        meta={"generatedContent": True, "workflowKind": "role_oriented"},
        name=name,
        task=False,
        title=title,
        version=PROMPT_VERSION,
    )
    server.add_prompt(prompt)


def register_prompt_components(server: FastMCP[dict[str, AppState]]) -> None:
    """Register the approved prompts in canonical public order.

    Parameters
    ----------
    server
        FastMCP server receiving explicitly approved prompt components.
    """

    _register_prompt(
        description=PROMPT_DESCRIPTIONS[PromptName.STUDENT_STUDY_SUPPORT],
        function=student_study_support,
        name="student_study_support",
        server=server,
        title="Student Study Support",
    )
    _register_prompt(
        description=PROMPT_DESCRIPTIONS[PromptName.TEACHER_GUIDE_DRAFT],
        function=teacher_guide_draft,
        name="teacher_guide_draft",
        server=server,
        title="Teacher Guide Draft",
    )
    _register_prompt(
        description=PROMPT_DESCRIPTIONS[PromptName.STUDENT_HANDBOOK_SECTION],
        function=student_handbook_section,
        name="student_handbook_section",
        server=server,
        title="Student Handbook Section",
    )
    _register_prompt(
        description=PROMPT_DESCRIPTIONS[PromptName.INFERRED_PROGRESSION_HYPOTHESIS],
        function=inferred_progression_hypothesis,
        name="inferred_progression_hypothesis",
        server=server,
        title="Inferred Progression Hypothesis",
    )
