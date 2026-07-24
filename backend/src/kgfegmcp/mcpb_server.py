"""This module provides the packaged STDIO entry point for the FastMCP server.

MCP Bundle hosts execute this module to start the application. The module intentionally
contains no domain or server-assembly logic of its own. It delegates construction to
the ordinary ``create_mcp`` application factory so packaged and repository-local
execution use the same registration, bootstrap, configuration, and error boundaries.

Runtime paths and other settings are inherited from the environment supplied by the
bundle host. The completed server runs over protocol-only STDIO with the startup banner
disabled so non-protocol output cannot interfere with MCP communication.
"""

# Package Library
from kgfegmcp.app import create_mcp


def main() -> None:
    """Construct the FastMCP server and run it over protocol-only STDIO."""

    create_mcp().run(show_banner=False, transport="stdio")


if __name__ == "__main__":
    main()
