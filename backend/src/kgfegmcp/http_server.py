"""This module provides the hosted HTTP entry point for the FastMCP server.

Container hosts execute this module to start the application. Like the packaged STDIO
entry point, the module contains no domain or server-assembly logic of its own. It
delegates construction to the ordinary ``create_mcp`` application factory so hosted,
packaged, and repository-local execution use the same registration, bootstrap,
configuration, and error boundaries.

The completed server runs over stateless Streamable HTTP on every interface at the port
supplied by the hosting platform through ``PORT``. A ``/health`` route lets the platform
confirm that the process is serving before it routes traffic to a new deployment.
"""

# Third Party Library
from starlette.requests import Request
from starlette.responses import JSONResponse

# Package Library
from kgfegmcp.app import create_mcp
from kgfegmcp.config import BackendSettings


def main() -> None:
    """Construct the FastMCP server and run it over stateless Streamable HTTP."""

    server = create_mcp()

    @server.custom_route("/health", methods=["GET"])
    async def health(request: Request) -> JSONResponse:
        """Report that the HTTP process is serving requests."""

        del request
        return JSONResponse({"status": "ok"})

    server.run(
        host="0.0.0.0",
        port=BackendSettings().http_port,
        show_banner=False,
        stateless_http=True,
        transport="http",
    )


if __name__ == "__main__":
    main()
