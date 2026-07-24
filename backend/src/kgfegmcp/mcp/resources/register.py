"""Register the approved read-only FastMCP resource surface.

Every adapter retrieves the one lifespan ``AppState`` and delegates to its ordinary
``ResourceService``. This module contains no catalog routing, package loading, checksum
validation, graph lookup, rights logic, artifact selection, or curriculum-specific
behavior.
"""

# Future Library
from __future__ import annotations

# Standard Library
from typing import TYPE_CHECKING

# Third Party Library
from fastmcp import Context
from fastmcp.resources import ResourceResult

# Package Library
from kgfegmcp.domain.identifiers import (
    ArtifactName,
    FrameworkId,
    NodeId,
    RelationshipId,
    SnapshotId,
)
from kgfegmcp.mcp.errors import resource_error_boundary
from kgfegmcp.mcp.resources import build_resource_result, get_resource_state
from kgfegmcp.resources.uri import (
    ARTIFACT_URI_TEMPLATE,
    CATALOG_URI,
    FRAMEWORK_URI_TEMPLATE,
    INTERPRETATION_PROFILE_URI_TEMPLATE,
    MANIFEST_URI_TEMPLATE,
    RELATIONSHIP_URI_TEMPLATE,
    STANDARD_PROVENANCE_URI_TEMPLATE,
    STANDARD_URI_TEMPLATE,
    UNRESOLVED_URI_TEMPLATE,
    VALIDATION_URI_TEMPLATE,
)

if TYPE_CHECKING:
    # Third Party Library
    from fastmcp import FastMCP

    # Package Library
    from kgfegmcp.bootstrap import AppState


async def read_artifact(
    *,
    artifact_name: ArtifactName,
    context: Context,
    framework_id: FrameworkId,
    snapshot_id: SnapshotId,
) -> ResourceResult:
    """Return one approved exact manifest-declared artifact.

    Parameters
    ----------
    artifact_name
        Exact logical artifact name declared by the accepted manifest.
    context
        Injected FastMCP request context.
    framework_id
        Exact conceptual framework identifier.
    snapshot_id
        Exact immutable framework snapshot identifier.

    Returns
    -------
    ResourceResult
        Exact source bytes and verified public identity evidence.
    """

    with resource_error_boundary("read_artifact_resource"):
        state = get_resource_state(context)
        document = state.resource_service.artifact(
            artifact_name=artifact_name,
            framework_id=framework_id,
            snapshot_id=snapshot_id,
        )
        return build_resource_result(document)


async def read_catalog(context: Context) -> ResourceResult:
    """Return the complete accepted catalog as deterministic JSON.

    Parameters
    ----------
    context
        Injected FastMCP request context.

    Returns
    -------
    ResourceResult
        Deterministic catalog content and source identity evidence.
    """

    with resource_error_boundary("read_catalog_resource"):
        state = get_resource_state(context)
        return build_resource_result(state.resource_service.catalog())


async def read_framework(
    *, context: Context, framework_id: FrameworkId
) -> ResourceResult:
    """Return one exact accepted framework family.

    Parameters
    ----------
    context
        Injected FastMCP request context.
    framework_id
        Exact conceptual framework identifier.

    Returns
    -------
    ResourceResult
        Deterministic framework-family content and source identity evidence.
    """

    with resource_error_boundary("read_framework_resource"):
        state = get_resource_state(context)
        return build_resource_result(state.resource_service.framework(framework_id))


async def read_interpretation_profile(
    *, context: Context, framework_id: FrameworkId, snapshot_id: SnapshotId
) -> ResourceResult:
    """Return exact retained bytes for one accepted interpretation profile.

    Parameters
    ----------
    context
        Injected FastMCP request context.
    framework_id
        Exact conceptual framework identifier.
    snapshot_id
        Exact immutable framework snapshot identifier.

    Returns
    -------
    ResourceResult
        Exact profile bytes and verified public identity evidence.
    """

    with resource_error_boundary("read_interpretation_profile_resource"):
        state = get_resource_state(context)
        document = state.resource_service.interpretation_profile(
            framework_id=framework_id, snapshot_id=snapshot_id
        )
        return build_resource_result(document)


async def read_manifest(
    *, context: Context, framework_id: FrameworkId, snapshot_id: SnapshotId
) -> ResourceResult:
    """Return exact retained bytes for one accepted package manifest.

    Parameters
    ----------
    context
        Injected FastMCP request context.
    framework_id
        Exact conceptual framework identifier.
    snapshot_id
        Exact immutable framework snapshot identifier.

    Returns
    -------
    ResourceResult
        Exact manifest bytes and verified public identity evidence.
    """

    with resource_error_boundary("read_manifest_resource"):
        state = get_resource_state(context)
        document = state.resource_service.manifest(
            framework_id=framework_id, snapshot_id=snapshot_id
        )
        return build_resource_result(document)


async def read_relationship(
    *,
    context: Context,
    framework_id: FrameworkId,
    relationship_id: RelationshipId,
    snapshot_id: SnapshotId,
) -> ResourceResult:
    """Return one exact package-local relationship.

    Parameters
    ----------
    context
        Injected FastMCP request context.
    framework_id
        Exact conceptual framework identifier.
    relationship_id
        Exact package-local relationship identifier.
    snapshot_id
        Exact immutable framework snapshot identifier.

    Returns
    -------
    ResourceResult
        Deterministic relationship content and source identity evidence.
    """

    with resource_error_boundary("read_relationship_resource"):
        state = get_resource_state(context)
        document = state.resource_service.relationship(
            framework_id=framework_id,
            relationship_id=relationship_id,
            snapshot_id=snapshot_id,
        )
        return build_resource_result(document)


async def read_standard(
    *,
    context: Context,
    framework_id: FrameworkId,
    node_id: NodeId,
    snapshot_id: SnapshotId,
) -> ResourceResult:
    """Return one exact standard selected through the outer node-ID namespace.

    Parameters
    ----------
    context
        Injected FastMCP request context.
    framework_id
        Exact conceptual framework identifier.
    node_id
        Exact package-local outer node identifier.
    snapshot_id
        Exact immutable framework snapshot identifier.

    Returns
    -------
    ResourceResult
        Deterministic standard content and source identity evidence.
    """

    with resource_error_boundary("read_standard_resource"):
        state = get_resource_state(context)
        document = state.resource_service.standard(
            framework_id=framework_id, node_id=node_id, snapshot_id=snapshot_id
        )
        return build_resource_result(document)


async def read_standard_provenance(
    *,
    context: Context,
    framework_id: FrameworkId,
    node_id: NodeId,
    snapshot_id: SnapshotId,
) -> ResourceResult:
    """Return one exact standard's selected detailed provenance entry.

    Parameters
    ----------
    context
        Injected FastMCP request context.
    framework_id
        Exact conceptual framework identifier.
    node_id
        Exact package-local outer node identifier.
    snapshot_id
        Exact immutable framework snapshot identifier.

    Returns
    -------
    ResourceResult
        Deterministic provenance content and verified source evidence.
    """

    with resource_error_boundary("read_standard_provenance_resource"):
        state = get_resource_state(context)
        document = state.resource_service.standard_provenance(
            framework_id=framework_id, node_id=node_id, snapshot_id=snapshot_id
        )
        return build_resource_result(document)


async def read_unresolved(
    *, context: Context, framework_id: FrameworkId, snapshot_id: SnapshotId
) -> ResourceResult:
    """Return exact bytes for one accepted unresolved-items report.

    Parameters
    ----------
    context
        Injected FastMCP request context.
    framework_id
        Exact conceptual framework identifier.
    snapshot_id
        Exact immutable framework snapshot identifier.

    Returns
    -------
    ResourceResult
        Exact unresolved-report bytes and verified public identity evidence.
    """

    with resource_error_boundary("read_unresolved_resource"):
        state = get_resource_state(context)
        document = state.resource_service.unresolved(
            framework_id=framework_id, snapshot_id=snapshot_id
        )
        return build_resource_result(document)


async def read_validation(
    *, context: Context, framework_id: FrameworkId, snapshot_id: SnapshotId
) -> ResourceResult:
    """Return exact bytes for one accepted detailed validation report.

    Parameters
    ----------
    context
        Injected FastMCP request context.
    framework_id
        Exact conceptual framework identifier.
    snapshot_id
        Exact immutable framework snapshot identifier.

    Returns
    -------
    ResourceResult
        Exact validation-report bytes and verified public identity evidence.
    """

    with resource_error_boundary("read_validation_resource"):
        state = get_resource_state(context)
        document = state.resource_service.validation(
            framework_id=framework_id, snapshot_id=snapshot_id
        )
        return build_resource_result(document)


def register_resource_components(server: FastMCP[dict[str, AppState]]) -> None:
    """Register the complete approved fixed-resource and template surface.

    Parameters
    ----------
    server
        FastMCP server receiving explicitly approved read-only resources.
    """

    server.resource(
        description="Return the complete accepted package catalog.",
        mime_type="application/json",
        name="catalog",
        title="Catalog",
        uri=CATALOG_URI,
    )(read_catalog)
    server.resource(
        description="Return one exact framework family and all accepted snapshots.",
        mime_type="application/json",
        name="framework",
        title="Framework",
        uri=FRAMEWORK_URI_TEMPLATE,
    )(read_framework)
    server.resource(
        description="Return exact accepted package-manifest bytes.",
        mime_type="application/json",
        name="package_manifest",
        title="Package Manifest",
        uri=MANIFEST_URI_TEMPLATE,
    )(read_manifest)
    server.resource(
        description="Return exact accepted detailed validation-report bytes.",
        mime_type="application/json",
        name="validation_report",
        title="Validation Report",
        uri=VALIDATION_URI_TEMPLATE,
    )(read_validation)
    server.resource(
        description="Return exact accepted unresolved-items report bytes.",
        mime_type="application/json",
        name="unresolved_items",
        title="Unresolved Items",
        uri=UNRESOLVED_URI_TEMPLATE,
    )(read_unresolved)
    server.resource(
        description="Return exact retained interpretation-profile bytes.",
        mime_type="application/json",
        name="interpretation_profile",
        title="Interpretation Profile",
        uri=INTERPRETATION_PROFILE_URI_TEMPLATE,
    )(read_interpretation_profile)
    server.resource(
        description=(
            "Return one approved exact manifest-declared artifact subject to its "
            "explicit exposure and rights policy."
        ),
        mime_type="application/octet-stream",
        name="manifest_artifact",
        title="Manifest Artifact",
        uri=ARTIFACT_URI_TEMPLATE,
    )(read_artifact)
    server.resource(
        description="Return one exact standard selected by outer node identifier.",
        mime_type="application/json",
        name="standard",
        title="Standard",
        uri=STANDARD_URI_TEMPLATE,
    )(read_standard)
    server.resource(
        description="Return one exact standard's selected detailed provenance entry.",
        mime_type="application/json",
        name="standard_provenance",
        title="Standard Provenance",
        uri=STANDARD_PROVENANCE_URI_TEMPLATE,
    )(read_standard_provenance)
    server.resource(
        description="Return one exact package-local relationship.",
        mime_type="application/json",
        name="relationship",
        title="Relationship",
        uri=RELATIONSHIP_URI_TEMPLATE,
    )(read_relationship)
