"""This module smoke-tests the real FastMCP server through a locked STDIO subprocess.

This module starts the server in a separate process using the locked ``uv`` project and
the same explicit application paths supplied by the MCP Bundle manifest. It then
connects as an MCP client, completes the protocol handshake, and requests the published
tools, prompts, fixed resources, and resource templates.

The smoke check requires those component inventories to match the approved server
surface exactly. A successful run also confirms that normal logging does not corrupt
protocol stdout and that the subprocess closes cleanly when the client disconnects.

The command can exercise either the repository layout or a retained MCPB staging
directory. It is a deployment and protocol check, not a complete domain or behavioral
test suite.

The command launches the real server through the locked ``uv`` project, passes the
application paths explicitly, completes an MCP client handshake, lists every component
family, and verifies the approved fixed inventory. A successful run also demonstrates
that protocol traffic is not corrupted by stdout logging and that the subprocess exits
cleanly when the client context closes.

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
from kgfegmcp.resources.uri import CATALOG_URI, RESOURCE_URI_TEMPLATES

cli = typer.Typer(
    help="Launch the locked server over STDIO and verify its fixed MCP inventory.",
    no_args_is_help=False,
)

_EXPECTED_PROMPT_NAMES = (
    "administrator_alignment_review",
    "cross_framework_comparison",
    "inferred_progression_hypothesis",
    "student_handbook_section",
    "student_study_support",
    "teacher_guide_draft",
)
_EXPECTED_TOOL_NAMES = (
    "compare_framework_evidence",
    "get_capabilities",
    "get_framework",
    "get_framework_statistics",
    "get_standard",
    "get_standard_context",
    "list_frameworks",
    "search_standards",
)


def _component_field(*, names: tuple[str, ...], value: object) -> str:
    """Return one string field from an MCP model or mapping.

    Parameters
    ----------
    names
        Accepted serialized field names in priority order.
    value
        MCP component model or mapping returned by the client.

    Returns
    -------
    str
        Selected nonempty string value.

    Raises
    ------
    RuntimeError
        If no accepted field contains a nonempty string.
    """

    model_dump = getattr(value, "model_dump", None)

    if callable(model_dump):
        payload = model_dump(by_alias=True, mode="json")
    elif isinstance(value, dict):
        payload = value
    else:
        payload = {name: getattr(value, name, None) for name in names}

    if not isinstance(payload, dict):
        raise RuntimeError("MCP component serialization did not produce an object.")

    for name in names:
        candidate = payload.get(name)

        if isinstance(candidate, str) and candidate:
            return candidate

    raise RuntimeError(
        "MCP component is missing expected field(s): " + ", ".join(names) + "."
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


def _require_inventory(
    *, actual: tuple[str, ...], expected: tuple[str, ...], label: str
) -> None:
    """Require one listed MCP component inventory to match exactly.

    Parameters
    ----------
    actual
        Sorted component identities returned by the subprocess server.
    expected
        Sorted approved component identities.
    label
        Human-readable component family name.

    Raises
    ------
    RuntimeError
        If the actual and expected identities differ.
    """

    if actual != expected:
        raise RuntimeError(
            f"Unexpected {label} inventory: expected={expected!r}, actual={actual!r}."
        )


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

    async with Client(transport) as client:
        prompts = await client.list_prompts()
        resource_templates = await client.list_resource_templates()
        resources = await client.list_resources()
        tools = await client.list_tools()

        prompt_names = tuple(
            sorted(
                _component_field(names=("name",), value=prompt) for prompt in prompts
            )
        )
        resource_template_uris = tuple(
            sorted(
                _component_field(
                    names=("uriTemplate", "uri_template"), value=resource_template
                )
                for resource_template in resource_templates
            )
        )
        resource_uris = tuple(
            sorted(
                _component_field(names=("uri",), value=resource)
                for resource in resources
            )
        )
        tool_names = tuple(
            sorted(_component_field(names=("name",), value=tool) for tool in tools)
        )

        _require_inventory(
            actual=prompt_names,
            expected=tuple(sorted(_EXPECTED_PROMPT_NAMES)),
            label="prompt",
        )
        _require_inventory(
            actual=resource_template_uris,
            expected=tuple(sorted(RESOURCE_URI_TEMPLATES)),
            label="resource-template",
        )
        _require_inventory(
            actual=resource_uris, expected=(CATALOG_URI,), label="fixed-resource"
        )
        _require_inventory(
            actual=tool_names,
            expected=tuple(sorted(_EXPECTED_TOOL_NAMES)),
            label="tool",
        )

    return {
        "bundleRoot": str(project_root) if bundle_root is not None else None,
        "fixedResourceCount": len(resource_uris),
        "promptCount": len(prompt_names),
        "resourceTemplateCount": len(resource_template_uris),
        "status": "passed",
        "toolCount": len(tool_names),
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
    """Run the locked subprocess STDIO inventory smoke check.

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
