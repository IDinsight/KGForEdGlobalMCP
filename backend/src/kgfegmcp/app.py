"""This module creates and manages the standalone FastMCP application server.

This module is the main FastMCP assembly boundary. The ``create_mcp`` factory
constructs the server, applies its duplicate, validation, error-masking, lifespan, and
component-registration policies, and returns the configured server to the FastMCP
runtime.

The application lifespan constructs one complete immutable application state when the
server starts and exposes that state to registered MCP components. Importing this
module does not construct settings, access graph-package files, validate packages,
build the catalog, or create search indexes; those operations begin only when the
server lifespan starts.
"""

# Future Library
from __future__ import annotations

# Standard Library
import logging

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

# Third Party Library
from fastmcp import FastMCP

# Package Library
from kgfegmcp.bootstrap import AppState, bootstrap_application
from kgfegmcp.mcp.register import register_components

_LOGGER = logging.getLogger("fastmcp.kgfegmcp.app")


@asynccontextmanager
async def app_lifespan(
    server: FastMCP[dict[str, AppState]],
) -> AsyncIterator[dict[str, AppState]]:
    """Construct and expose application state for one FastMCP server lifespan.

    Parameters
    ----------
    server
        FastMCP server whose lifespan is starting. The current bootstrap requires no
        server-specific input.

    Yields
    ------
    dict[str, AppState]
        Lifespan context containing the one immutable application state.
    """

    del server
    state = bootstrap_application()

    try:
        yield {"state": state}
    finally:
        accepted_package_count = len(state.catalog_load_result.package_runtimes)
        _LOGGER.info(
            msg=(
                f"Application lifespan shutdown completed: "
                f"accepted_package_count={accepted_package_count}, "
                f"operation=application_shutdown."
            )
        )


def create_mcp() -> FastMCP[dict[str, AppState]]:
    """Create the standalone FastMCP server without constructing application state.

    Returns
    -------
    FastMCP[dict[str, AppState]]
        Configured server with explicit duplicate, validation, masking, lifespan, and
        registration policies.
    """

    server = FastMCP(
        lifespan=app_lifespan,
        mask_error_details=True,
        name="Knowledge Graph For Education Global MCP",
        on_duplicate="error",
        strict_input_validation=True,
    )
    register_components(server)
    return server
