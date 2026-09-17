"""This module defines the approved resource URI templates and link constructors.

This module contains the fixed ``kgfegmcp://`` catalog URI, the approved FastMCP
resource-template strings, and deterministic constructors for server-generated resource
links. Identifier values are percent-encoded as individual URI path segments before
being inserted into a constructed link.

FastMCP remains responsible for matching incoming resource templates and decoding their
parameters. This module does not parse raw request URIs, resolve frameworks or
packages, enforce rights, access artifacts, query graph stores, or register resources.
"""

# Standard Library
from urllib.parse import quote

# Package Library
from kgfegmcp.domain.identifiers import (
    ArtifactName,
    FrameworkId,
    NodeId,
    RelationshipId,
    SnapshotId,
)

ARTIFACT_URI_TEMPLATE = (
    "kgfegmcp://framework/{framework_id}/snapshot/{snapshot_id}/"
    "artifact/{artifact_name}"
)
CATALOG_URI = "kgfegmcp://catalog"
LEARNING_COMPONENT_PROVENANCE_URI_TEMPLATE = (
    "kgfegmcp://framework/{framework_id}/snapshot/{snapshot_id}/"
    "learning-component/{node_id}/provenance"
)
LEARNING_COMPONENT_URI_TEMPLATE = (
    "kgfegmcp://framework/{framework_id}/snapshot/{snapshot_id}/"
    "learning-component/{node_id}"
)
FRAMEWORK_URI_TEMPLATE = "kgfegmcp://framework/{framework_id}"
INTERPRETATION_PROFILE_URI_TEMPLATE = (
    "kgfegmcp://framework/{framework_id}/snapshot/{snapshot_id}/"
    "interpretation-profile"
)
MANIFEST_URI_TEMPLATE = (
    "kgfegmcp://framework/{framework_id}/snapshot/{snapshot_id}/manifest"
)
RELATIONSHIP_URI_TEMPLATE = (
    "kgfegmcp://framework/{framework_id}/snapshot/{snapshot_id}/"
    "relationship/{relationship_id}"
)
STANDARD_PROVENANCE_URI_TEMPLATE = (
    "kgfegmcp://framework/{framework_id}/snapshot/{snapshot_id}/"
    "standard/{node_id}/provenance"
)
STANDARD_LEARNING_COMPONENTS_URI_TEMPLATE = (
    "kgfegmcp://framework/{framework_id}/snapshot/{snapshot_id}/"
    "standard/{node_id}/learning-components"
)
STANDARD_URI_TEMPLATE = (
    "kgfegmcp://framework/{framework_id}/snapshot/{snapshot_id}/standard/{node_id}"
)
UNRESOLVED_URI_TEMPLATE = (
    "kgfegmcp://framework/{framework_id}/snapshot/{snapshot_id}/unresolved"
)
VALIDATION_URI_TEMPLATE = (
    "kgfegmcp://framework/{framework_id}/snapshot/{snapshot_id}/validation"
)
RESOURCE_URI_TEMPLATES: tuple[str, ...] = (
    FRAMEWORK_URI_TEMPLATE,
    MANIFEST_URI_TEMPLATE,
    VALIDATION_URI_TEMPLATE,
    UNRESOLVED_URI_TEMPLATE,
    INTERPRETATION_PROFILE_URI_TEMPLATE,
    ARTIFACT_URI_TEMPLATE,
    STANDARD_URI_TEMPLATE,
    STANDARD_PROVENANCE_URI_TEMPLATE,
    STANDARD_LEARNING_COMPONENTS_URI_TEMPLATE,
    LEARNING_COMPONENT_URI_TEMPLATE,
    LEARNING_COMPONENT_PROVENANCE_URI_TEMPLATE,
    RELATIONSHIP_URI_TEMPLATE,
)


def _segment(value: object) -> str:
    """Percent-encode one typed identifier as a single URI path segment.

    Parameters
    ----------
    value
        Validated identifier value supplied by an ordinary application service.

    Returns
    -------
    str
        RFC 3986 percent-encoded path-segment text.
    """

    return quote(safe="", string=str(value))


def artifact_uri(
    *, artifact_name: ArtifactName, framework_id: FrameworkId, snapshot_id: SnapshotId
) -> str:
    """Build the URI for one manifest-declared artifact.

    Parameters
    ----------
    artifact_name
        Validated name of the manifest-declared artifact to address.
    framework_id
        Validated identifier of the framework family that owns the snapshot.
    snapshot_id
        Validated identifier of the snapshot that declares the artifact.

    Returns
    -------
    str
        Constructed kgfegmcp URI addressing the artifact, with each identifier
        percent-encoded as a single path segment.
    """

    return (
        f"kgfegmcp://framework/{_segment(framework_id)}/snapshot/"
        f"{_segment(snapshot_id)}/artifact/{_segment(artifact_name)}"
    )


def framework_uri(framework_id: FrameworkId) -> str:
    """Build the URI for one exact framework family.

    Parameters
    ----------
    framework_id
        Validated identifier of the exact framework family to address.

    Returns
    -------
    str
        Constructed kgfegmcp URI addressing the framework family, with the identifier
        percent-encoded as a single path segment.
    """

    return f"kgfegmcp://framework/{_segment(framework_id)}"


def interpretation_profile_uri(
    *, framework_id: FrameworkId, snapshot_id: SnapshotId
) -> str:
    """Build the URI for the accepted interpretation profile of one snapshot.

    Parameters
    ----------
    framework_id
        Validated identifier of the framework family that owns the snapshot.
    snapshot_id
        Validated identifier of the snapshot whose interpretation profile is addressed.

    Returns
    -------
    str
        Constructed kgfegmcp URI addressing the snapshot's interpretation profile, with
        each identifier percent-encoded as a single path segment.
    """

    return (
        f"kgfegmcp://framework/{_segment(framework_id)}/snapshot/"
        f"{_segment(snapshot_id)}/interpretation-profile"
    )


def manifest_uri(*, framework_id: FrameworkId, snapshot_id: SnapshotId) -> str:
    """Build the URI for one accepted package manifest.

    Parameters
    ----------
    framework_id
        Validated identifier of the framework family that owns the snapshot.
    snapshot_id
        Validated identifier of the snapshot whose manifest is addressed.

    Returns
    -------
    str
        Constructed kgfegmcp URI addressing the snapshot's manifest, with each
        identifier percent-encoded as a single path segment.
    """

    return (
        f"kgfegmcp://framework/{_segment(framework_id)}/snapshot/"
        f"{_segment(snapshot_id)}/manifest"
    )


def relationship_uri(
    *,
    framework_id: FrameworkId,
    relationship_id: RelationshipId,
    snapshot_id: SnapshotId,
) -> str:
    """Build the URI for one exact package-local relationship.

    Parameters
    ----------
    framework_id
        Validated identifier of the framework family that owns the snapshot.
    relationship_id
        Validated identifier of the package-local relationship to address.
    snapshot_id
        Validated identifier of the snapshot that contains the relationship.

    Returns
    -------
    str
        Constructed kgfegmcp URI addressing the relationship, with each identifier
        percent-encoded as a single path segment.
    """

    return (
        f"kgfegmcp://framework/{_segment(framework_id)}/snapshot/"
        f"{_segment(snapshot_id)}/relationship/{_segment(relationship_id)}"
    )


def learning_component_provenance_uri(
    *, framework_id: FrameworkId, node_id: NodeId, snapshot_id: SnapshotId
) -> str:
    """Build the URI for one learning component's detailed provenance entry.

    Parameters
    ----------
    framework_id
        Validated identifier of the framework family that owns the snapshot.
    node_id
        Validated outer node ID selecting the exact learning component.
    snapshot_id
        Validated identifier of the snapshot that contains the component.

    Returns
    -------
    str
        Constructed kgfegmcp URI, with each identifier percent-encoded as a single
        path segment.
    """

    return (
        f"kgfegmcp://framework/{_segment(framework_id)}/snapshot/"
        f"{_segment(snapshot_id)}/learning-component/{_segment(node_id)}/provenance"
    )


def learning_component_uri(
    *, framework_id: FrameworkId, node_id: NodeId, snapshot_id: SnapshotId
) -> str:
    """Build the URI for one exact learning component selected by outer node ID.

    Parameters
    ----------
    framework_id
        Validated identifier of the framework family that owns the snapshot.
    node_id
        Validated outer node ID selecting the exact learning component.
    snapshot_id
        Validated identifier of the snapshot that contains the component.

    Returns
    -------
    str
        Constructed kgfegmcp URI, with each identifier percent-encoded as a single
        path segment.
    """

    return (
        f"kgfegmcp://framework/{_segment(framework_id)}/snapshot/"
        f"{_segment(snapshot_id)}/learning-component/{_segment(node_id)}"
    )


def standard_learning_components_uri(
    *, framework_id: FrameworkId, node_id: NodeId, snapshot_id: SnapshotId
) -> str:
    """Build the URI for the learning components supporting one exact standard.

    Parameters
    ----------
    framework_id
        Validated identifier of the framework family that owns the snapshot.
    node_id
        Validated outer node ID selecting the exact standard.
    snapshot_id
        Validated identifier of the snapshot that contains the standard.

    Returns
    -------
    str
        Constructed kgfegmcp URI, with each identifier percent-encoded as a single
        path segment.
    """

    return (
        f"kgfegmcp://framework/{_segment(framework_id)}/snapshot/"
        f"{_segment(snapshot_id)}/standard/{_segment(node_id)}/learning-components"
    )


def standard_provenance_uri(
    *, framework_id: FrameworkId, node_id: NodeId, snapshot_id: SnapshotId
) -> str:
    """Build the URI for one exact standard's detailed provenance.

    Parameters
    ----------
    framework_id
        Validated identifier of the framework family that owns the snapshot.
    node_id
        Validated outer node ID selecting the exact standard.
    snapshot_id
        Validated identifier of the snapshot that contains the standard.

    Returns
    -------
    str
        Constructed kgfegmcp URI addressing the standard's provenance, with each
        identifier percent-encoded as a single path segment.
    """

    return (
        f"kgfegmcp://framework/{_segment(framework_id)}/snapshot/"
        f"{_segment(snapshot_id)}/standard/{_segment(node_id)}/provenance"
    )


def standard_uri(
    *, framework_id: FrameworkId, node_id: NodeId, snapshot_id: SnapshotId
) -> str:
    """Build the URI for one exact standard selected by outer node ID.

    Parameters
    ----------
    framework_id
        Validated identifier of the framework family that owns the snapshot.
    node_id
        Validated outer node ID selecting the exact standard to address.
    snapshot_id
        Validated identifier of the snapshot that contains the standard.

    Returns
    -------
    str
        Constructed kgfegmcp URI addressing the standard, with each identifier
        percent-encoded as a single path segment.
    """

    return (
        f"kgfegmcp://framework/{_segment(framework_id)}/snapshot/"
        f"{_segment(snapshot_id)}/standard/{_segment(node_id)}"
    )


def unresolved_uri(*, framework_id: FrameworkId, snapshot_id: SnapshotId) -> str:
    """Build the URI for one accepted unresolved-items artifact.

    Parameters
    ----------
    framework_id
        Validated identifier of the framework family that owns the snapshot.
    snapshot_id
        Validated identifier of the snapshot whose unresolved-items artifact is
        addressed.

    Returns
    -------
    str
        Constructed kgfegmcp URI addressing the snapshot's unresolved-items artifact,
        with each identifier percent-encoded as a single path segment.
    """

    return (
        f"kgfegmcp://framework/{_segment(framework_id)}/snapshot/"
        f"{_segment(snapshot_id)}/unresolved"
    )


def validation_uri(*, framework_id: FrameworkId, snapshot_id: SnapshotId) -> str:
    """Build the URI for one accepted detailed validation report.

    Parameters
    ----------
    framework_id
        Validated identifier of the framework family that owns the snapshot.
    snapshot_id
        Validated identifier of the snapshot whose validation report is
        addressed.

    Returns
    -------
    str
        Constructed kgfegmcp URI addressing the snapshot's validation report, with each
        identifier percent-encoded as a single path segment.
    """

    return (
        f"kgfegmcp://framework/{_segment(framework_id)}/snapshot/"
        f"{_segment(snapshot_id)}/validation"
    )
