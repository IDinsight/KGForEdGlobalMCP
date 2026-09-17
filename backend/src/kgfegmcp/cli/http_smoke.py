"""This module smoke-tests a running FastMCP server over Streamable HTTP.

This module connects as an MCP client to an already running server, such as a local
``kgfegmcp.http_server`` process, a local container, or the hosted deployment. It
completes the protocol handshake and then runs the same approved-inventory and
representative resource-read checks as the STDIO smoke command, so both transports are
held to one definition of the server surface.

The command does not start a server. Supply the full MCP endpoint, including its path,
with ``--url``. It is a deployment and protocol check, not a complete domain or
behavioral test suite.
"""

# Future Library
from __future__ import annotations

# Standard Library
import asyncio
import json

from typing import Annotated

# Third Party Library
import typer

from fastmcp import Client

# Package Library
from kgfegmcp.cli.smoke_checks import verify_server_surface

cli = typer.Typer(
    help=(
        "Connect to a running Streamable HTTP server and verify inventory plus "
        "resource reads."
    ),
    no_args_is_help=False,
)


async def _run_smoke(url: str) -> dict[str, object]:
    """Connect to the server over Streamable HTTP and verify every component family.

    Parameters
    ----------
    url
        Full MCP endpoint of the running server, including its path.

    Returns
    -------
    dict[str, object]
        Deterministic successful smoke summary.

    Raises
    ------
    RuntimeError
        If the connection, protocol exchange, inventory, or resource reads fail.
    """

    # The summary is built only after the client context closes, so a successful run
    # also proves the client disconnected cleanly.
    async with Client(url) as client:
        surface = await verify_server_surface(client)

    return {**surface, "status": "passed", "url": url}


@cli.command()
def http_smoke(
    *,
    url: Annotated[
        str,
        typer.Option(
            help="Full MCP endpoint of the running server, including its path.",
            metavar="ENDPOINT",
        ),
    ],
) -> None:
    """Run the Streamable HTTP inventory and resource-read smoke check.

    Parameters
    ----------
    url
        Full MCP endpoint of the running server, including its path.

    Raises
    ------
    typer.Exit
        If the connection or protocol inventory check fails.
    """

    try:
        result = asyncio.run(_run_smoke(url))
    except Exception as error:
        typer.echo(err=True, message=f"HTTP smoke failed: {error}")
        raise typer.Exit(code=1) from error

    typer.echo(json.dumps(ensure_ascii=False, indent=2, obj=result, sort_keys=True))


if __name__ == "__main__":
    cli()
