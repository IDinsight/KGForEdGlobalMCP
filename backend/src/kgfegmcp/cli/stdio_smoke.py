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
import base64
import binascii
import json

from collections.abc import Sequence
from pathlib import Path
from typing import Annotated, Final, cast

# Third Party Library
import typer

from fastmcp import Client
from fastmcp.client.transports import StdioTransport

# Package Library
from kgfegmcp.domain.identifiers import (
    ArtifactName,
    FrameworkId,
    NodeId,
    RelationshipId,
    SnapshotId,
)
from kgfegmcp.resources.uri import (
    CATALOG_URI,
    RESOURCE_URI_TEMPLATES,
    artifact_uri,
    framework_uri,
    interpretation_profile_uri,
    manifest_uri,
    relationship_uri,
    standard_provenance_uri,
    standard_uri,
    unresolved_uri,
    validation_uri,
)

cli = typer.Typer(
    help=(
        "Launch the locked server over STDIO and verify inventory plus resource reads."
    ),
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
    "collect_progression_evidence",
    "compare_framework_evidence",
    "get_capabilities",
    "get_framework",
    "get_framework_statistics",
    "get_standard",
    "get_standard_context",
    "list_frameworks",
    "search_standards",
)

_SMOKE_ARTIFACT_NAME: Final[ArtifactName] = cast(ArtifactName, "validationReport")
_SMOKE_FRAMEWORK_ID: Final[FrameworkId] = cast(
    FrameworkId, "ghana-nacca-primary-english-language-basic-1-3"
)
_SMOKE_NODE_ID: Final[NodeId] = cast(NodeId, "aa4cdccd-e5d9-589c-8094-e10d7ac0c754")
_SMOKE_RELATIONSHIP_ID: Final[RelationshipId] = cast(
    RelationshipId, "72a98493-9a16-58b6-9a80-e53012bfa4c1"
)
_SMOKE_SNAPSHOT_ID: Final[SnapshotId] = cast(
    SnapshotId,
    "ghana-nacca-primary-english-language-basic-1-3@2019+5ea90021b08d",
)
_SMOKE_UNRESOLVED_NODE_ID: Final[NodeId] = cast(
    NodeId, "4f5d76cf-3242-52e4-8c16-7b569f84588a"
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


def _resource_payload(*, contents: Sequence[object], uri: str) -> bytes:
    """Return the one nonempty payload from a FastMCP resource read.

    Parameters
    ----------
    contents
        Content items returned by ``Client.read_resource``.
    uri
        Canonical resource URI used for error reporting.

    Returns
    -------
    bytes
        Exact text bytes or decoded binary bytes returned by the resource.

    Raises
    ------
    RuntimeError
        If the resource does not return exactly one supported, nonempty content item.
    """

    if len(contents) != 1:
        raise RuntimeError(
            f"Resource {uri!r} returned {len(contents)} content items; expected 1."
        )

    item = contents[0]
    mime_type = _component_field(names=("mimeType", "mime_type"), value=item)

    if mime_type != "application/json":
        raise RuntimeError(
            f"Resource {uri!r} returned MIME type {mime_type!r}; "
            f"expected 'application/json'."
        )

    text = getattr(item, "text", None)

    if isinstance(text, str):
        payload = text.encode("utf-8")
    else:
        blob = getattr(item, "blob", None)

        if isinstance(blob, bytes):
            payload = blob
        elif isinstance(blob, bytearray):
            payload = bytes(blob)
        elif isinstance(blob, str):
            try:
                payload = base64.b64decode(blob, validate=True)
            except (binascii.Error, ValueError) as error:
                raise RuntimeError(
                    f"Resource {uri!r} returned an invalid base64 blob."
                ) from error
        else:
            content = getattr(item, "content", None)

            if isinstance(content, str):
                payload = content.encode("utf-8")
            elif isinstance(content, bytes):
                payload = content
            elif isinstance(content, bytearray):
                payload = bytes(content)
            else:
                raise RuntimeError(
                    f"Resource {uri!r} returned an unsupported content item."
                )

    if not payload:
        raise RuntimeError(f"Resource {uri!r} returned empty content.")

    return payload


def _resource_read_targets() -> tuple[tuple[str, str, tuple[str, ...]], ...]:
    """Return one known-good read target for every approved resource family.

    Returns
    -------
    tuple[tuple[str, str, tuple[str, ...]], ...]
        Stable label, canonical URI, and expected identity tokens for the fixed catalog
        and all nine resource templates.
    """

    framework_id = _SMOKE_FRAMEWORK_ID
    node_id = _SMOKE_NODE_ID
    relationship_id = _SMOKE_RELATIONSHIP_ID
    snapshot_id = _SMOKE_SNAPSHOT_ID
    unresolved_node_id = _SMOKE_UNRESOLVED_NODE_ID
    return (
        ("catalog", CATALOG_URI, (str(framework_id), str(snapshot_id))),
        (
            "framework",
            framework_uri(framework_id),
            (str(framework_id), str(snapshot_id)),
        ),
        (
            "manifest",
            manifest_uri(framework_id=framework_id, snapshot_id=snapshot_id),
            (str(framework_id), str(snapshot_id)),
        ),
        (
            "validation",
            validation_uri(framework_id=framework_id, snapshot_id=snapshot_id),
            ("validation_checks", "passed"),
        ),
        (
            "unresolved",
            unresolved_uri(framework_id=framework_id, snapshot_id=snapshot_id),
            (str(relationship_id), str(unresolved_node_id)),
        ),
        (
            "interpretationProfile",
            interpretation_profile_uri(
                framework_id=framework_id, snapshot_id=snapshot_id
            ),
            (str(framework_id), "profileVersion"),
        ),
        (
            "artifact",
            artifact_uri(
                artifact_name=_SMOKE_ARTIFACT_NAME,
                framework_id=framework_id,
                snapshot_id=snapshot_id,
            ),
            ("validation_checks", "passed"),
        ),
        (
            "standard",
            standard_uri(
                framework_id=framework_id, node_id=node_id, snapshot_id=snapshot_id
            ),
            (str(node_id), "B1.2.7.2.6"),
        ),
        (
            "standardProvenance",
            standard_provenance_uri(
                framework_id=framework_id, node_id=node_id, snapshot_id=snapshot_id
            ),
            (str(node_id), "provenance"),
        ),
        (
            "relationship",
            relationship_uri(
                framework_id=framework_id,
                relationship_id=relationship_id,
                snapshot_id=snapshot_id,
            ),
            (str(relationship_id), "unresolvedRootFallback"),
        ),
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

        resource_reads: list[dict[str, object]] = []

        for label, uri, expected_tokens in _resource_read_targets():
            contents = await client.read_resource(uri)
            byte_count = _verify_json_resource(
                contents=contents, expected_tokens=expected_tokens, uri=uri
            )
            resource_reads.append({"byteCount": byte_count, "label": label, "uri": uri})

    return {
        "bundleRoot": str(project_root) if bundle_root is not None else None,
        "fixedResourceCount": len(resource_uris),
        "promptCount": len(prompt_names),
        "resourceReadCount": len(resource_reads),
        "resourceReads": resource_reads,
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


def _verify_json_resource(
    *, contents: Sequence[object], expected_tokens: tuple[str, ...], uri: str
) -> int:
    """Require one resource response to be nonempty JSON with identity evidence.

    Parameters
    ----------
    contents
        Content items returned by ``Client.read_resource``.
    expected_tokens
        Exact package-local identity or schema tokens that must occur in the JSON text.
    uri
        Canonical resource URI used for error reporting.

    Returns
    -------
    int
        Number of bytes returned by the resource.

    Raises
    ------
    RuntimeError
        If decoding, JSON parsing, or expected-token validation fails.
    """

    payload = _resource_payload(contents=contents, uri=uri)

    try:
        text = payload.decode("utf-8")
    except UnicodeDecodeError as error:
        raise RuntimeError(f"Resource {uri!r} is not valid UTF-8 JSON.") from error

    try:
        value = json.loads(text)
    except json.JSONDecodeError as error:
        raise RuntimeError(f"Resource {uri!r} did not return valid JSON.") from error

    if not isinstance(value, (dict, list)):
        raise RuntimeError(
            f"Resource {uri!r} returned a JSON scalar; expected an object or array."
        )

    missing = tuple(token for token in expected_tokens if token not in text)

    if missing:
        raise RuntimeError(
            f"Resource {uri!r} is missing expected identity token(s): {missing!r}."
        )

    return len(payload)


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
