"""This package exposes the application's FastMCP integration boundaries.

This package contains the adapter code that connects the curriculum knowledge graph
application to FastMCP. It centralizes component registration and MCP-facing error
translation while keeping protocol-specific concerns separate from the catalog, graph,
package, profile, and search domains.

Importing this package exposes the approved MCP boundary utilities but does not
construct the FastMCP server, load application settings, validate graph packages, build
the catalog, or create search indexes.
"""

# Package Library
from kgfegmcp.mcp.errors import (
    prompt_error_boundary,
    resource_error_boundary,
    tool_error_boundary,
)
from kgfegmcp.mcp.register import register_components

__all__ = [
    "prompt_error_boundary",
    "register_components",
    "resource_error_boundary",
    "tool_error_boundary",
]
