"""This module registers approved FastMCP components on the application server.

This module defines the single explicit boundary through which tools, resources,
resource templates, and prompts are added to the FastMCP server. Centralized
registration keeps the server's public MCP surface deliberate and prevents components
from being registered through import-time decorators or automatic module discovery.
"""

# Future Library
from __future__ import annotations

# Standard Library
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    # Third Party Library
    from fastmcp import FastMCP

    # Package Library
    from kgfegmcp.bootstrap import AppState


def register_components(server: FastMCP[dict[str, AppState]]) -> None:
    """Register the components implemented for the current application phase.

    This establishes the explicit registration boundary but intentionally registers no
    tools, resources, resource templates, or prompts. Later implementation units must
    add components through this function rather than through import-time decorators or
    automatic discovery.

    Parameters
    ----------
    server
        FastMCP server receiving explicitly approved components.
    """

    del server
