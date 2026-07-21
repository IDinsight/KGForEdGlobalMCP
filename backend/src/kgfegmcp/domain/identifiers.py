"""This module contains validated identifier types and deterministic identifier
builders.
"""

# Standard Library
from pathlib import PurePosixPath
from typing import Annotated, NewType

# Third Party Library
from pydantic import AfterValidator, StringConstraints, TypeAdapter

# Package Library
from kgfegmcp.domain.enums import GraphType
from kgfegmcp.regexes import (
    ARTIFACT_NAME_RE,
    CONTROL_CHARACTER_RE,
    GRAPH_PACKAGE_ID_RE,
    KEBAB_CASE_ID_RE,
    LANGUAGE_TAG_RE,
    SHA256_RE,
    SNAPSHOT_ID_RE,
    VERSION_TOKEN_RE,
)


def _validate_artifact_path(value: str) -> str:
    """Validate a manifest-relative POSIX artifact path.

    Parameters
    ----------
    value
        Candidate artifact path from an operator-controlled manifest.

    Returns
    -------
    str
        The unchanged validated relative path.

    Raises
    ------
    ValueError
        If the path is absolute, contains traversal segments, uses backslashes, has
        surrounding whitespace, or is otherwise unsafe for package-root resolution.
    """

    if value != value.strip():
        raise ValueError("Artifact paths may not contain surrounding whitespace.")

    if CONTROL_CHARACTER_RE.search(value):
        raise ValueError("Artifact paths may not contain control characters.")

    if "\\" in value:
        raise ValueError("Artifact paths must use POSIX forward slashes.")

    raw_parts = value.split("/")

    if any(part in {"", ".", ".."} for part in raw_parts):
        raise ValueError("Artifact paths may not contain empty or traversal segments.")

    path = PurePosixPath(value)

    if path.is_absolute():
        raise ValueError("Artifact paths must be relative to the package root.")

    return value


def _validate_opaque_identifier(value: str) -> str:
    """Validate an opaque identifier without normalizing source data.

    Parameters
    ----------
    value
        Candidate identifier value.

    Returns
    -------
    str
        The unchanged validated identifier.

    Raises
    ------
    ValueError
        If the identifier has surrounding whitespace or control characters.
    """

    if value != value.strip():
        raise ValueError("Identifiers may not contain surrounding whitespace.")

    if CONTROL_CHARACTER_RE.search(value):
        raise ValueError("Identifiers may not contain control characters.")

    return value


_ArtifactName = NewType("_ArtifactName", str)
_ArtifactPath = NewType("_ArtifactPath", str)
_CaseIdentifierUri = NewType("_CaseIdentifierUri", str)
_CaseIdentifierUuid = NewType("_CaseIdentifierUuid", str)
_FrameworkId = NewType("_FrameworkId", str)
_GraphPackageId = NewType("_GraphPackageId", str)
_LanguageTag = NewType("_LanguageTag", str)
_ManifestVersion = NewType("_ManifestVersion", str)
_NodeId = NewType("_NodeId", str)
_ProfileId = NewType("_ProfileId", str)
_ProfileVersion = NewType("_ProfileVersion", str)
_RelationshipId = NewType("_RelationshipId", str)
_SchemaVersion = NewType("_SchemaVersion", str)
_Sha256Digest = NewType("_Sha256Digest", str)
_SnapshotId = NewType("_SnapshotId", str)
_SnapshotVersionToken = NewType("_SnapshotVersionToken", str)
ArtifactName = Annotated[
    _ArtifactName,
    StringConstraints(max_length=100, min_length=1, pattern=ARTIFACT_NAME_RE),
]
ArtifactPath = Annotated[
    _ArtifactPath,
    StringConstraints(max_length=512, min_length=1),
    AfterValidator(_validate_artifact_path),
]
CaseIdentifierUri = Annotated[
    _CaseIdentifierUri,
    StringConstraints(max_length=2_048, min_length=1),
    AfterValidator(_validate_opaque_identifier),
]
CaseIdentifierUuid = Annotated[
    _CaseIdentifierUuid,
    StringConstraints(max_length=1_024, min_length=1),
    AfterValidator(_validate_opaque_identifier),
]
FrameworkId = Annotated[
    _FrameworkId,
    StringConstraints(max_length=200, min_length=3, pattern=KEBAB_CASE_ID_RE),
]
GraphPackageId = Annotated[
    _GraphPackageId,
    StringConstraints(max_length=320, min_length=18, pattern=GRAPH_PACKAGE_ID_RE),
]
LanguageTag = Annotated[
    _LanguageTag,
    StringConstraints(max_length=64, min_length=2, pattern=LANGUAGE_TAG_RE),
]
ManifestVersion = Annotated[
    _ManifestVersion,
    StringConstraints(max_length=64, min_length=1, pattern=VERSION_TOKEN_RE),
]
NodeId = Annotated[
    _NodeId,
    StringConstraints(max_length=1_024, min_length=1),
    AfterValidator(_validate_opaque_identifier),
]
ProfileId = Annotated[
    _ProfileId,
    StringConstraints(max_length=200, min_length=3, pattern=KEBAB_CASE_ID_RE),
]
ProfileVersion = Annotated[
    _ProfileVersion,
    StringConstraints(max_length=64, min_length=1, pattern=VERSION_TOKEN_RE),
]
RelationshipId = Annotated[
    _RelationshipId,
    StringConstraints(max_length=1_024, min_length=1),
    AfterValidator(_validate_opaque_identifier),
]
SchemaVersion = Annotated[
    _SchemaVersion,
    StringConstraints(max_length=64, min_length=1, pattern=VERSION_TOKEN_RE),
]
Sha256Digest = Annotated[
    _Sha256Digest, StringConstraints(max_length=71, min_length=71, pattern=SHA256_RE)
]
SnapshotId = Annotated[
    _SnapshotId,
    StringConstraints(max_length=280, min_length=18, pattern=SNAPSHOT_ID_RE),
]
SnapshotVersionToken = Annotated[
    _SnapshotVersionToken,
    StringConstraints(max_length=96, min_length=1, pattern=VERSION_TOKEN_RE),
]

_FRAMEWORK_ID_ADAPTER: TypeAdapter[FrameworkId] = TypeAdapter(FrameworkId)
_GRAPH_PACKAGE_ID_ADAPTER: TypeAdapter[GraphPackageId] = TypeAdapter(GraphPackageId)
_SHA256_DIGEST_ADAPTER: TypeAdapter[Sha256Digest] = TypeAdapter(Sha256Digest)
_SNAPSHOT_ID_ADAPTER: TypeAdapter[SnapshotId] = TypeAdapter(SnapshotId)
_SNAPSHOT_VERSION_TOKEN_ADAPTER: TypeAdapter[SnapshotVersionToken] = TypeAdapter(
    SnapshotVersionToken
)


def build_initial_graph_package_id(snapshot_id: SnapshotId) -> GraphPackageId:
    """Build the initial graph package ID for a one-package snapshot.

    Parameters
    ----------
    snapshot_id
        Immutable snapshot identifier.

    Returns
    -------
    GraphPackageId
        A graph package identifier equal to the snapshot identifier.
    """

    return _GRAPH_PACKAGE_ID_ADAPTER.validate_python(str(snapshot_id))


def build_snapshot_id(
    *,
    content_sha256: Sha256Digest,
    framework_id: FrameworkId,
    version_token: SnapshotVersionToken,
) -> SnapshotId:
    """Build an immutable snapshot identifier from accepted artifact content.

    Parameters
    ----------
    content_sha256
        Full package-content digest prefixed with ``sha256:``.
    framework_id
        Stable conceptual framework identifier.
    version_token
        Official version, publication date, release label, or ``undated`` token.

    Returns
    -------
    SnapshotId
        Identifier in the form ``<framework>@<version>+<12-character-hash>``.
    """

    validated_content_sha256 = _SHA256_DIGEST_ADAPTER.validate_python(
        str(content_sha256)
    )
    validated_framework_id = _FRAMEWORK_ID_ADAPTER.validate_python(str(framework_id))
    validated_version_token = _SNAPSHOT_VERSION_TOKEN_ADAPTER.validate_python(
        str(version_token)
    )
    short_hash = str(validated_content_sha256).removeprefix("sha256:")[:12]
    candidate = f"{validated_framework_id}@{validated_version_token}+{short_hash}"
    return _SNAPSHOT_ID_ADAPTER.validate_python(candidate)


def build_versioned_graph_package_id(
    *, graph_type: GraphType, package_revision: int, snapshot_id: SnapshotId
) -> GraphPackageId:
    """Build a graph-type-specific package identifier for a snapshot.

    Parameters
    ----------
    graph_type
        Graph type represented by the package.
    package_revision
        Positive packaging revision for the unchanged source snapshot.
    snapshot_id
        Immutable source snapshot identifier.

    Returns
    -------
    GraphPackageId
        Package identifier extending the snapshot with graph type and revision.

    Raises
    ------
    ValueError
        If ``package_revision`` is less than one.
    """

    if package_revision < 1:
        raise ValueError("package_revision must be greater than zero.")

    validated_snapshot_id = _SNAPSHOT_ID_ADAPTER.validate_python(str(snapshot_id))
    graph_type_token = graph_type.value.replace("_", "-")
    candidate = f"{validated_snapshot_id}--{graph_type_token}--p{package_revision}"
    return _GRAPH_PACKAGE_ID_ADAPTER.validate_python(candidate)
