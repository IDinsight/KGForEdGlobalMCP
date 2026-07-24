"""This module registers approved FastMCP components on the application server.

This module is the single explicit boundary through which tools, resources, and prompts
are added to the FastMCP server. Centralized registration keeps the public MCP surface
deliberate and prevents import-time decorators or automatic module discovery from
adding tools, resources, resource templates, or prompts.
"""

# Future Library
from __future__ import annotations

# Standard Library
from typing import TYPE_CHECKING

# Package Library
from kgfegmcp.mcp.prompts.register import register_prompt_components
from kgfegmcp.mcp.resources.register import register_resource_components
from kgfegmcp.mcp.tools.capabilities import register_capability_tools
from kgfegmcp.mcp.tools.context import register_context_tools
from kgfegmcp.mcp.tools.frameworks import register_framework_tools
from kgfegmcp.mcp.tools.standards import register_standard_tools
from kgfegmcp.mcp.tools.statistics import register_statistics_tools

if TYPE_CHECKING:
    # Third Party Library
    from fastmcp import FastMCP

    # Package Library
    from kgfegmcp.bootstrap import AppState


def register_components(server: FastMCP[dict[str, AppState]]) -> None:
    """Register approved read-only tools, resources, and prompt workflows.

    Parameters
    ----------
    server
        FastMCP server receiving explicitly approved components.
    """

    register_capability_tools(server)
    register_context_tools(server)
    register_framework_tools(server)
    register_standard_tools(server)
    register_statistics_tools(server)
    register_resource_components(server)
    register_prompt_components(server)
