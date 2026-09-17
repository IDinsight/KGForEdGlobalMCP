"""This module smoke-tests the real FastMCP server through a locked STDIO subprocess.

This module starts the server in a separate process using the locked ``uv`` project and
the same explicit application paths supplied by the MCP Bundle manifest. It then
connects as an MCP client, completes the protocol handshake, and requests the published
tools, prompts, fixed resources, and resource templates. It then reads the fixed
catalog and one known-good URI from every approved resource template.

The smoke check requires those component inventories to match the approved server
surface exactly and requires every representative resource read to return nonempty,
valid JSON containing its expected package-local identity evidence. A successful run
also confirms that normal logging does not corrupt protocol stdout and that the
subprocess closes cleanly when the client disconnects.

The command can exercise either the repository layout or a retained MCPB staging
directory. It is a deployment and protocol check, not a complete domain or behavioral
test suite.

The command launches the real server through the locked ``uv`` project, passes the
application paths explicitly, completes an MCP client handshake, lists every component
family, verifies the approved fixed inventory, and reads the complete representative
resource set. A successful run also demonstrates that protocol traffic is not corrupted
by stdout logging and that the subprocess exits cleanly when the client context closes.

By default the command exercises the repository layout. Supply ``--bundle-root`` to
exercise a retained MCPB staging directory assembled by ``kgfegmcp-build-mcpb``.
"""

# Future Library
from __future__ import annotations

# Standard Library
import asyncio
import json

from pathlib import Path
from typing import Annotated

# Third Party Library
import typer

from fastmcp import Client
from fastmcp.client.transports import StdioTransport

# Package Library
from kgfegmcp.cli.smoke_checks import verify_server_surface

cli = typer.Typer(
    help=(
        "Launch the locked server over STDIO and verify inventory plus resource reads."
    ),
    no_args_is_help=False,
)


def _project_root() -> Path:
    """Return the repository root containing ``backend``, ``config``, and ``data``.

    Returns
    -------
    Path
        Canonical repository root inferred from this installed source file.
    """

    return Path(__file__).resolve().parents[4]


def _require_bundle_root(bundle_root: Path) -> Path:
    """Validate and return one retained MCPB staging directory.

    Parameters
    ----------
    bundle_root
        Operator-supplied bundle staging directory.

    Returns
    -------
    Path
        Canonical validated bundle root.

    Raises
    ------
    RuntimeError
        If required packaged files are missing.
    """

    resolved = bundle_root.expanduser().resolve(strict=False)
    required_paths = (
        resolved / "manifest.json",
        resolved / "pyproject.toml",
        resolved / "src" / "kgfegmcp" / "mcpb_server.py",
        resolved / "uv.lock",
    )
    missing = tuple(str(path) for path in required_paths if not path.is_file())

    if missing:
        raise RuntimeError(
            "Bundle staging directory is incomplete: " + ", ".join(missing) + "."
        )

    return resolved


async def _run_smoke(bundle_root: Path | None) -> dict[str, object]:
    """Launch the server over STDIO and verify every fixed component family.

    Parameters
    ----------
    bundle_root
        Optional retained MCPB staging directory.

    Returns
    -------
    dict[str, object]
        Deterministic successful smoke summary.

    Raises
    ------
    RuntimeError
        If startup, protocol exchange, environment-based bootstrap, inventory, or clean
        shutdown fails.
    """

    repository_root = _project_root()
    runtime_root, project_root = _runtime_paths(
        bundle_root=bundle_root, repository_root=repository_root
    )
    transport = StdioTransport(
        args=[
            "run",
            "--directory",
            str(runtime_root),
            "--locked",
            "--no-dev",
            "python",
            "-m",
            "kgfegmcp.mcpb_server",
        ],
        command="uv",
        cwd=str(runtime_root),
        env=_stdio_environment(project_root),
        keep_alive=False,
    )

    # The summary is built only after the client context closes, so a successful run
    # also proves the subprocess shut down cleanly.
    async with Client(transport) as client:
        surface = await verify_server_surface(client)

    return {
        **surface,
        "bundleRoot": str(project_root) if bundle_root is not None else None,
        "status": "passed",
    }


def _runtime_paths(
    *, bundle_root: Path | None, repository_root: Path
) -> tuple[Path, Path]:
    """Resolve the runtime directory and application project root for one smoke run.

    Parameters
    ----------
    bundle_root
        Optional retained MCPB staging directory.
    repository_root
        Canonical repository root.

    Returns
    -------
    tuple[Path, Path]
        Runtime directory containing ``pyproject.toml`` followed by the application
        project root containing ``config`` and ``data``.
    """

    if bundle_root is not None:
        resolved_bundle_root = _require_bundle_root(bundle_root)
        return resolved_bundle_root, resolved_bundle_root

    return repository_root / "backend", repository_root


def _stdio_environment(project_root: Path) -> dict[str, str]:
    """Build the explicit application environment used by a desktop STDIO host.

    Parameters
    ----------
    project_root
        Root containing packaged or repository-local configuration and graph data.

    Returns
    -------
    dict[str, str]
        Explicit generic application settings required by the subprocess.
    """

    return {
        "KGFEGMCP_CONFIG_ROOT": str(project_root / "config"),
        "KGFEGMCP_DATA_ROOT": str(project_root / "data"),
        "KGFEGMCP_ENV": "local",
        "KGFEGMCP_GRAPH_PACKAGES_ROOT": str(project_root / "data" / "graph_packages"),
        "KGFEGMCP_INVALID_PACKAGE_POLICY": "fail",
        "KGFEGMCP_LOG_LEVEL": "INFO",
        "KGFEGMCP_PROFILE_ROOT": str(project_root / "config" / "profiles"),
        "KGFEGMCP_PROMPT_ROOT": str(project_root / "config" / "prompts"),
        "PATHS_PROJECT_DIR": str(project_root),
    }


@cli.command()
def stdio_smoke(
    *,
    bundle_root: Annotated[
        Path | None,
        typer.Option(
            help="Optional retained MCPB staging directory to exercise.", metavar="PATH"
        ),
    ] = None,
) -> None:
    """Run the locked subprocess STDIO inventory and resource-read smoke check.

    Parameters
    ----------
    bundle_root
        Optional retained MCPB staging directory.

    Raises
    ------
    typer.Exit
        If the subprocess or protocol inventory check fails.
    """

    try:
        result = asyncio.run(_run_smoke(bundle_root))
    except Exception as error:
        typer.echo(err=True, message=f"STDIO smoke failed: {error}")
        raise typer.Exit(code=1) from error

    typer.echo(json.dumps(ensure_ascii=False, indent=2, obj=result, sort_keys=True))


if __name__ == "__main__":
    cli()
