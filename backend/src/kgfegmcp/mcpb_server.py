"""This module runs the packaged FastMCP server over the local STDIO transport.

MCP Bundle hosts execute this module as the server entry point. Application settings
continue to come from the inherited process environment, including the explicit
``PATHS_PROJECT_DIR`` value supplied by the bundle manifest. The ordinary application
factory remains the single server assembly boundary.
"""

# Package Library
from kgfegmcp.app import create_mcp


def main() -> None:
    """Construct the FastMCP server and run it over protocol-only STDIO."""

    create_mcp().run(show_banner=False, transport="stdio")


if __name__ == "__main__":
    main()
