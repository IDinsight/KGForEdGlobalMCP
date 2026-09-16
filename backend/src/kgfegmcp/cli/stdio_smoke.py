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
import json

from collections.abc import Mapping, Sequence
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
    learning_component_provenance_uri,
    learning_component_uri,
    manifest_uri,
    relationship_uri,
    standard_learning_components_uri,
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
    "multigrade_lesson_plan",
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
    "get_learning_component",
    "get_learning_component_context",
    "get_learning_components_for_standard",
    "get_standard",
    "get_standard_context",
    "list_frameworks",
    "search_learning_components",
    "search_standards",
)

_SMOKE_ARTIFACT_NAME: Final[ArtifactName] = cast(ArtifactName, "validationReport")
_SMOKE_FRAMEWORK_ID: Final[FrameworkId] = cast(
    FrameworkId, "ghana-nacca-primary-english-language-basic-1-3"
)
_SMOKE_LEARNING_COMPONENT_ID: Final[NodeId] = cast(
    NodeId, "29bb3662-7e9c-5d44-83c4-084e4fb57323"
)
_SMOKE_NODE_ID: Final[NodeId] = cast(NodeId, "aa4cdccd-e5d9-589c-8094-e10d7ac0c754")
_SMOKE_RELATIONSHIP_ID: Final[RelationshipId] = cast(
    RelationshipId, "72a98493-9a16-58b6-9a80-e53012bfa4c1"
)
_SMOKE_SNAPSHOT_ID: Final[SnapshotId] = cast(
    SnapshotId,
    "ghana-nacca-primary-english-language-basic-1-3@2019+c33ab5a379fb",
)
_SMOKE_UNRESOLVED_NODE_ID: Final[NodeId] = cast(
    NodeId, "4f5d76cf-3242-52e4-8c16-7b569f84588a"
)


def _base64_payload(*, blob: str, uri: str) -> bytes:
    """Decode one strictly validated base64 resource blob.

    Parameters
    ----------
    blob
        Base64-encoded payload carried by a resource content item.
    uri
        Canonical resource URI used for error reporting.

    Returns
    -------
    bytes
        Exact decoded binary payload.

    Raises
    ------
    RuntimeError
        If the blob is not strictly valid base64.
    """

    try:
        return base64.b64decode(blob, validate=True)
    except ValueError as error:
        raise RuntimeError(
            f"Resource {uri!r} returned an invalid base64 blob."
        ) from error


def _binary_payload(value: object) -> bytes | None:
    """Return exact bytes for one bytes-like resource content value.

    Parameters
    ----------
    value
        Candidate ``bytes`` or ``bytearray`` payload from a content item.

    Returns
    -------
    bytes | None
        Exact bytes, or ``None`` when the value is not bytes-like.
    """

    if isinstance(value, bytes):
        return value

    if isinstance(value, bytearray):
        return bytes(value)

    return None


def _blob_payload(*, item: object, uri: str) -> bytes | None:
    """Return the payload carried by one content item ``blob`` attribute.

    Parameters
    ----------
    item
        Single content item returned by ``Client.read_resource``.
    uri
        Canonical resource URI used for error reporting.

    Returns
    -------
    bytes | None
        Decoded blob payload, or ``None`` when the item carries no supported blob.

    Raises
    ------
    RuntimeError
        If the item carries a string blob that is not strictly valid base64.
    """

    blob = getattr(item, "blob", None)
    binary = _binary_payload(blob)

    if binary is not None:
        return binary

    if isinstance(blob, str):
        return _base64_payload(blob=blob, uri=uri)

    return None


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


def _content_item_payload(*, item: object, uri: str) -> bytes:
    """Return the single payload carried by one MCP resource content item.

    Attributes are consulted in strict precedence order: ``text`` first, then a binary
    or base64 ``blob``, then a generic ``content`` attribute. An empty but supported
    payload is returned as-is; the caller reports emptiness.

    Parameters
    ----------
    item
        Single content item returned by ``Client.read_resource``.
    uri
        Canonical resource URI used for error reporting.

    Returns
    -------
    bytes
        Exact text bytes or decoded binary bytes returned by the resource.

    Raises
    ------
    RuntimeError
        If the item carries no supported payload attribute, or carries a string blob
        that is not strictly valid base64.
    """

    text_payload = _text_payload(item)

    if text_payload is not None:
        return text_payload

    blob_payload = _blob_payload(item=item, uri=uri)

    if blob_payload is not None:
        return blob_payload

    content_payload = _content_payload(item)

    if content_payload is None:
        raise RuntimeError(f"Resource {uri!r} returned an unsupported content item.")

    return content_payload


def _content_payload(item: object) -> bytes | None:
    """Return the payload carried by one content item ``content`` attribute.

    Parameters
    ----------
    item
        Single content item returned by ``Client.read_resource``.

    Returns
    -------
    bytes | None
        UTF-8 encoded text or exact bytes, or ``None`` when the attribute is absent
        or carries an unsupported type.
    """

    content = getattr(item, "content", None)

    if isinstance(content, str):
        return content.encode("utf-8")

    return _binary_payload(content)


async def _listed_inventory(client: Client) -> dict[str, tuple[str, ...]]:
    """Return the sorted component inventory published by the subprocess server.

    Parameters
    ----------
    client
        Connected MCP client that has completed the protocol handshake.

    Returns
    -------
    dict[str, tuple[str, ...]]
        Sorted component identities keyed by the human-readable family label used in
        inventory mismatch reporting.

    Raises
    ------
    RuntimeError
        If any listed component is missing its expected identity field.
    """

    prompts = await client.list_prompts()
    resource_templates = await client.list_resource_templates()
    resources = await client.list_resources()
    tools = await client.list_tools()
    return {
        "fixed-resource": tuple(
            sorted(
                _component_field(names=("uri",), value=resource)
                for resource in resources
            )
        ),
        "prompt": tuple(
            sorted(
                _component_field(names=("name",), value=prompt) for prompt in prompts
            )
        ),
        "resource-template": tuple(
            sorted(
                _component_field(
                    names=("uriTemplate", "uri_template"), value=resource_template
                )
                for resource_template in resource_templates
            )
        ),
        "tool": tuple(
            sorted(_component_field(names=("name",), value=tool) for tool in tools)
        ),
    }


def _project_root() -> Path:
    """Return the repository root containing ``backend``, ``config``, and ``data``.

    Returns
    -------
    Path
        Canonical repository root inferred from this installed source file.
    """

    return Path(__file__).resolve().parents[4]


def _require_approved_inventory(inventory: Mapping[str, tuple[str, ...]]) -> None:
    """Require every listed component family to match the approved server surface.

    Families are checked in a fixed order - prompt, resource template, fixed resource,
    then tool - so that a failing run reports the same first mismatch it reported
    before this check was extracted into its own function.

    Parameters
    ----------
    inventory
        Sorted component identities keyed by family label, as returned by
        ``_listed_inventory``.

    Raises
    ------
    RuntimeError
        If any component family differs from its approved identities. A family that is
        absent from the mapping is reported as an empty actual inventory.
    """

    expected_inventory = (
        ("prompt", tuple(sorted(_EXPECTED_PROMPT_NAMES))),
        ("resource-template", tuple(sorted(RESOURCE_URI_TEMPLATES))),
        ("fixed-resource", (CATALOG_URI,)),
        ("tool", tuple(sorted(_EXPECTED_TOOL_NAMES))),
    )

    for label, expected in expected_inventory:
        _require_inventory(
            actual=inventory.get(label, ()), expected=expected, label=label
        )


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

    payload = _content_item_payload(item=item, uri=uri)

    if not payload:
        raise RuntimeError(f"Resource {uri!r} returned empty content.")

    return payload


def _resource_read_targets() -> tuple[tuple[str, str, tuple[str, ...]], ...]:
    """Return one known-good read target for every approved resource family.

    Returns
    -------
    tuple[tuple[str, str, tuple[str, ...]], ...]
        Stable label, canonical URI, and expected identity tokens for the fixed catalog
        and all twelve resource templates.
    """

    framework_id = _SMOKE_FRAMEWORK_ID
    learning_component_id = _SMOKE_LEARNING_COMPONENT_ID
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
        (
            "standardLearningComponents",
            standard_learning_components_uri(
                framework_id=framework_id, node_id=node_id, snapshot_id=snapshot_id
            ),
            (str(node_id), str(learning_component_id)),
        ),
        (
            "learningComponent",
            learning_component_uri(
                framework_id=framework_id,
                node_id=learning_component_id,
                snapshot_id=snapshot_id,
            ),
            (str(learning_component_id), "placements"),
        ),
        (
            "learningComponentProvenance",
            learning_component_provenance_uri(
                framework_id=framework_id,
                node_id=learning_component_id,
                snapshot_id=snapshot_id,
            ),
            (str(learning_component_id), "provenance"),
        ),
    )


async def _resource_reads(client: Client) -> list[dict[str, object]]:
    """Read and verify one known-good resource from every approved family.

    Parameters
    ----------
    client
        Connected MCP client that has completed the protocol handshake.

    Returns
    -------
    list[dict[str, object]]
        Deterministic per-resource read summaries in approved target order.

    Raises
    ------
    RuntimeError
        If any representative resource read fails decoding, JSON parsing, or
        expected-token validation.
    """

    reads: list[dict[str, object]] = []

    for label, uri, expected_tokens in _resource_read_targets():
        contents = await client.read_resource(uri)
        byte_count = _verify_json_resource(
            contents=contents, expected_tokens=expected_tokens, uri=uri
        )
        reads.append({"byteCount": byte_count, "label": label, "uri": uri})

    return reads


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
        inventory = await _listed_inventory(client)
        _require_approved_inventory(inventory)
        resource_reads = await _resource_reads(client)

    # Every family key is guaranteed present: _require_approved_inventory has already
    # matched all four labels against the approved surface.
    return {
        "bundleRoot": str(project_root) if bundle_root is not None else None,
        "fixedResourceCount": len(inventory["fixed-resource"]),
        "promptCount": len(inventory["prompt"]),
        "resourceReadCount": len(resource_reads),
        "resourceReads": resource_reads,
        "resourceTemplateCount": len(inventory["resource-template"]),
        "status": "passed",
        "toolCount": len(inventory["tool"]),
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


def _text_payload(item: object) -> bytes | None:
    """Return the UTF-8 payload carried by one content item ``text`` attribute.

    Parameters
    ----------
    item
        Single content item returned by ``Client.read_resource``.

    Returns
    -------
    bytes | None
        UTF-8 encoded text, or ``None`` when the item carries no string text.
    """

    text = getattr(item, "text", None)

    if isinstance(text, str):
        return text.encode("utf-8")

    return None


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
