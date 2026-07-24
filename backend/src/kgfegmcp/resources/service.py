"""This module assembles read-only resources from the accepted application runtime.

``ResourceService`` is the ordinary application coordinator for resource delivery. It
reuses the existing catalog and standards services, exact package-local graph stores,
accepted package models, ``ResourcePolicy``, and ``ResourceRepository`` to produce
complete ``ResourceDocument`` values.

The service resolves exact framework and snapshot identities, selects packages by their
graph contract, applies resource rights, obtains verified source bytes or accepted
in-memory records, creates deterministic derived JSON, and attaches public identity and
checksum evidence. It does not discover or reload packages, construct graph stores,
rebuild search indexes, accept caller-supplied filesystem paths, register FastMCP
components, or infer curriculum-specific semantics.
"""

# Future Library
from __future__ import annotations

# Standard Library
import json

from dataclasses import dataclass

# Third Party Library
from pydantic import BaseModel

# Package Library
from kgfegmcp.catalog.models import (
    CatalogFrameworkFamily,
    CatalogGraphPackage,
    CatalogPackageRuntime,
)
from kgfegmcp.catalog.service import CatalogService
from kgfegmcp.domain.enums import GraphType
from kgfegmcp.domain.identifiers import (
    ArtifactName,
    FrameworkId,
    GraphPackageId,
    NodeId,
    RelationshipId,
    Sha256Digest,
    SnapshotId,
)
from kgfegmcp.errors import (
    CapabilityUnavailableError,
    ResourceAccessDeniedError,
    ResourceNotFoundError,
)
from kgfegmcp.packages.checksums import calculate_bytes_sha256
from kgfegmcp.packages.models import DeclaredArtifactReference, LoadedGraphPackage
from kgfegmcp.resources.models import (
    ResourceDocument,
    ResourceKind,
    ResourceMetadata,
    ResourceRepresentation,
    ResourceSourceEvidence,
    StandardProvenanceResult,
)
from kgfegmcp.resources.policy import ResourcePolicy
from kgfegmcp.resources.repository import ResourceRepository
from kgfegmcp.resources.uri import (
    CATALOG_URI,
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
from kgfegmcp.services.models import GetStandardRequest, NodeIdStandardIdentifier
from kgfegmcp.services.standards import StandardsService


def _canonical_json(value: BaseModel | object) -> str:
    """Serialize one accepted model or JSON value deterministically.

    Parameters
    ----------
    value
        Immutable Pydantic model or JSON-compatible derived value.

    Returns
    -------
    str
        Compact UTF-8 JSON text with sorted object keys and preserved array order.
    """

    payload = (
        value.model_dump(by_alias=True, mode="json")
        if isinstance(value, BaseModel)
        else value
    )
    return json.dumps(
        ensure_ascii=False, obj=payload, separators=(",", ":"), sort_keys=True
    )


def _parse_json_object(content: bytes) -> dict[str, object]:
    """Decode one exact UTF-8 JSON object with duplicate-key rejection.

    Parameters
    ----------
    content
        Checksum-verified exact artifact bytes.

    Returns
    -------
    dict[str, object]
        Decoded top-level JSON object.

    Raises
    ------
    ResourceNotFoundError
        If the accepted artifact cannot supply the required object view.
    """

    try:
        text = content.decode("utf-8")
        value = json.loads(object_pairs_hook=_reject_duplicate_json_keys, s=text)
    except ValueError as error:
        raise ResourceNotFoundError(
            details={"reason": type(error).__name__},
            message="The accepted resource artifact is not valid JSON object content.",
        ) from error

    if not isinstance(value, dict):
        raise ResourceNotFoundError(
            message="The accepted resource artifact is not a JSON object."
        )

    return value


def _reject_duplicate_json_keys(pairs: list[tuple[str, object]]) -> dict[str, object]:
    """Build one JSON object while rejecting duplicate member names.

    Parameters
    ----------
    pairs
        Source-order object members supplied by ``json.loads``.

    Returns
    -------
    dict[str, object]
        Decoded object preserving source insertion order.

    Raises
    ------
    ValueError
        If the source object repeats a member name.
    """

    value: dict[str, object] = {}

    for key, item in pairs:
        if key in value:
            raise ValueError(f"Duplicate JSON object member: {key}.")

        value[key] = item

    return value


def _source_evidence(
    *, graph_package_id: GraphPackageId, reference: DeclaredArtifactReference
) -> ResourceSourceEvidence:
    """Convert one accepted artifact reference into public integrity evidence.

    Parameters
    ----------
    graph_package_id
        Exact graph-package identifier owning the declared artifact.
    reference
        Accepted manifest-declared artifact reference.

    Returns
    -------
    ResourceSourceEvidence
        Public logical name, package identity, byte length, and checksum.
    """

    return ResourceSourceEvidence(
        graph_package_id=graph_package_id,
        logical_name=str(reference.logical_name),
        sha256=reference.sha256,
        size_bytes=reference.size_bytes,
    )


@dataclass(frozen=True, slots=True)
class ResourceService:
    """Resolve and assemble approved resources from one accepted catalog runtime."""

    catalog_service: CatalogService
    policy: ResourcePolicy
    repository: ResourceRepository
    standards_service: StandardsService

    def __post_init__(self) -> None:
        """Require every dependency to share one exact catalog and policy.

        Raises
        ------
        ValueError
            If independently constructed services or policies are mixed.
        """

        if self.repository.policy is not self.policy:
            raise ValueError(
                "ResourceService and ResourceRepository must share policy."
            )

        if self.standards_service.catalog_service is not self.catalog_service:
            raise ValueError("ResourceService dependencies must share CatalogService.")

        if (
            self.standards_service.framework_service.catalog_service
            is not self.catalog_service
        ):
            raise ValueError("ResourceService dependencies must share CatalogService.")

    def _available_artifact_names(
        self, *, logical_names: tuple[str, ...], runtime: CatalogPackageRuntime
    ) -> tuple[ArtifactName, ...]:
        """Return permitted generic artifact names for one package in public order.

        Parameters
        ----------
        logical_names
            Sorted declared logical names for the selected package.
        runtime
            Exact accepted package runtime supplying the current access rights.

        Returns
        -------
        tuple[ArtifactName, ...]
            Generic artifact names the current rights permit, in deterministic order.
        """

        rights = runtime.catalog_package.rights
        available: list[ArtifactName] = []

        for logical_name in logical_names:
            try:
                self.policy.artifact_decision(logical_name=logical_name, rights=rights)
            except (ResourceNotFoundError, ResourceAccessDeniedError):
                continue

            available.append(ArtifactName(logical_name))

        return tuple(available)

    def _available_standards_kinds(
        self, runtime: CatalogPackageRuntime
    ) -> tuple[ResourceKind, ...]:
        """Return permitted academic-standards resource kinds for one package.

        Parameters
        ----------
        runtime
            Exact accepted package runtime supplying the graph type, detailed
            provenance capability, and current access rights.

        Returns
        -------
        tuple[ResourceKind, ...]
            Academic-standards resource kinds the current rights permit, or an empty
            tuple when the package is not an academic-standards graph.
        """

        if (
            runtime.catalog_package.package_identity.graph_type
            is not GraphType.ACADEMIC_STANDARDS
        ):
            return ()

        available: list[ResourceKind] = []

        for resource_kind in (ResourceKind.RELATIONSHIP, ResourceKind.STANDARD):
            if self._permits_resource_kind(
                resource_kind=resource_kind, runtime=runtime
            ):
                available.append(resource_kind)

        if runtime.catalog_package.capabilities.has_detailed_provenance and (
            self._permits_resource_kind(
                resource_kind=ResourceKind.STANDARD_PROVENANCE, runtime=runtime
            )
        ):
            available.append(ResourceKind.STANDARD_PROVENANCE)

        return tuple(available)

    def _build_derived_document(
        self,
        *,
        canonical_uri: str,
        package: CatalogGraphPackage | None = None,
        resource_kind: ResourceKind,
        source_artifacts: tuple[ResourceSourceEvidence, ...],
        value: BaseModel | object,
    ) -> ResourceDocument:
        """Build one deterministic JSON resource and enforce its return limit.

        Parameters
        ----------
        canonical_uri
            Exact resource URI for the derived content.
        package
            Optional package identity for the derived content.
        resource_kind
            Resource family kind for the derived content.
        source_artifacts
            Exact retained artifact evidence for the derived content.
        value
            Immutable Pydantic model or JSON-compatible derived value.

        Returns
        -------
        ResourceDocument
            Complete resource document with content and metadata.
        """

        content = _canonical_json(value)
        content_bytes = content.encode("utf-8")
        self.policy.require_return_size(len(content_bytes))
        metadata = self._metadata(
            byte_length=len(content_bytes),
            canonical_uri=canonical_uri,
            content_sha256=calculate_bytes_sha256(content_bytes),
            mime_type="application/json",
            package=package,
            representation=ResourceRepresentation.DETERMINISTIC_DERIVED,
            resource_kind=resource_kind,
            source_artifacts=source_artifacts,
        )
        return ResourceDocument(content=content, metadata=metadata)

    def _build_raw_document(
        self,
        *,
        canonical_uri: str,
        content: bytes,
        mime_type: str,
        package: CatalogGraphPackage | None = None,
        resource_kind: ResourceKind,
        source_artifacts: tuple[ResourceSourceEvidence, ...],
    ) -> ResourceDocument:
        """Build one exact-byte resource and enforce its return limit.

        Parameters
        ----------
        canonical_uri
            Exact resource URI for the derived content.
        content
            Exact retained artifact bytes for the resource.
        mime_type
            MIME type for the resource content.
        package
            Optional package identity for the derived content.
        resource_kind
            Resource family kind for the derived content.
        source_artifacts
            Exact retained artifact evidence for the derived content.

        Returns
        -------
        ResourceDocument
            Complete resource document with content and metadata.
        """

        self.policy.require_return_size(len(content))
        metadata = self._metadata(
            byte_length=len(content),
            canonical_uri=canonical_uri,
            content_sha256=calculate_bytes_sha256(content),
            mime_type=mime_type,
            package=package,
            representation=ResourceRepresentation.RAW_SOURCE,
            resource_kind=resource_kind,
            source_artifacts=source_artifacts,
        )
        return ResourceDocument(content=content, metadata=metadata)

    def _dedicated_artifact(
        self,
        *,
        canonical_uri: str,
        framework_id: FrameworkId,
        logical_name: str,
        resource_kind: ResourceKind,
        snapshot_id: SnapshotId,
    ) -> ResourceDocument:
        """Resolve one dedicated built-in artifact through shared policy and access.

        Parameters
        ----------
        canonical_uri
            Exact resource URI for the derived content.
        framework_id
            Exact framework identifier for the selected package.
        logical_name
            Exact manifest-declared logical name for the dedicated artifact.
        resource_kind
            Resource family kind for the derived content.
        snapshot_id
            Exact snapshot identifier for the selected package.

        Returns
        -------
        ResourceDocument
            Complete resource document with content and metadata.
        """

        runtime = self._package_runtime(
            framework_id=framework_id, snapshot_id=snapshot_id
        )
        self.policy.require_resource_access(
            resource_kind=resource_kind, rights=runtime.catalog_package.rights
        )
        decision = self.policy.artifact_decision(
            logical_name=logical_name, rights=runtime.catalog_package.rights
        )
        content, reference = self.repository.read_artifact(
            loaded_package=runtime.loaded_package, logical_name=logical_name
        )
        graph_package_id = runtime.catalog_package.package_identity.graph_package_id
        return self._build_raw_document(
            canonical_uri=canonical_uri,
            content=content,
            mime_type=decision.mime_type,
            package=runtime.catalog_package,
            resource_kind=resource_kind,
            source_artifacts=(
                _source_evidence(
                    graph_package_id=graph_package_id, reference=reference
                ),
            ),
        )

    def _family_manifest_evidence(
        self, family: CatalogFrameworkFamily
    ) -> tuple[ResourceSourceEvidence, ...]:
        """Return manifest evidence for every package in one framework family.

        Parameters
        ----------
        family
            Exact accepted framework family with all snapshots.

        Returns
        -------
        tuple[ResourceSourceEvidence, ...]
            Exact retained manifest-byte evidence for every package in the family.
        """

        evidence: list[ResourceSourceEvidence] = []

        for snapshot in family.snapshots:
            for package in snapshot.graph_packages:
                graph_package_id = package.package_identity.graph_package_id
                runtime = self.catalog_service.get_package_runtime(graph_package_id)
                evidence.append(
                    self._manifest_evidence(
                        graph_package_id=graph_package_id,
                        loaded_package=runtime.loaded_package,
                    )
                )

        return tuple(evidence)

    @staticmethod
    def _manifest_evidence(
        *, graph_package_id: GraphPackageId, loaded_package: LoadedGraphPackage
    ) -> ResourceSourceEvidence:
        """Return exact retained manifest-byte evidence for one package.

        Parameters
        ----------
        graph_package_id
            Graph package identifier.
        loaded_package
            Accepted loaded package containing the retained manifest bytes.

        Returns
        -------
        ResourceSourceEvidence
            Exact retained manifest-byte evidence for one package.
        """

        return ResourceSourceEvidence(
            graph_package_id=graph_package_id,
            logical_name="packageManifest",
            sha256=calculate_bytes_sha256(loaded_package.manifest_bytes),
            size_bytes=len(loaded_package.manifest_bytes),
        )

    @staticmethod
    def _metadata(
        *,
        byte_length: int,
        canonical_uri: str,
        content_sha256: Sha256Digest,
        mime_type: str,
        package: CatalogGraphPackage | None,
        representation: ResourceRepresentation,
        resource_kind: ResourceKind,
        source_artifacts: tuple[ResourceSourceEvidence, ...],
    ) -> ResourceMetadata:
        """Build complete resource metadata with optional package identity.

        Parameters
        ----------
        byte_length
            Exact byte length of the resource content.
        canonical_uri
            Exact resource URI for the derived content.
        content_sha256
            Exact SHA-256 digest of the resource content.
        mime_type
            MIME type for the resource content.
        package
            Optional package identity for the derived content.
        representation
            Resource representation type for the derived content.
        resource_kind
            Resource family kind for the derived content.
        source_artifacts
            Exact retained artifact evidence for the derived content.

        Returns
        -------
        ResourceMetadata
            Complete resource metadata with content and metadata.
        """

        identity = package.package_identity if package is not None else None
        return ResourceMetadata(
            byte_length=byte_length,
            canonical_uri=canonical_uri,
            content_sha256=content_sha256,
            framework_id=identity.framework_id if identity is not None else None,
            graph_package_id=(
                identity.graph_package_id if identity is not None else None
            ),
            graph_type=identity.graph_type if identity is not None else None,
            mime_type=mime_type,
            profile_id=identity.profile_id if identity is not None else None,
            profile_sha256=identity.profile_sha256 if identity is not None else None,
            profile_version=identity.profile_version if identity is not None else None,
            representation=representation,
            resource_kind=resource_kind,
            snapshot_id=identity.snapshot_id if identity is not None else None,
            source_artifacts=source_artifacts,
        )

    def _package_runtime(
        self,
        *,
        framework_id: FrameworkId,
        graph_type: GraphType | None = None,
        snapshot_id: SnapshotId,
    ) -> CatalogPackageRuntime:
        """Select one exact accepted runtime without first-package fallback.

        Package-level resource URIs do not currently contain a graph-type segment. They
        therefore require exactly one package in the selected snapshot. Resource
        families with a graph contract supply the required graph type explicitly.

        Parameters
        ----------
        framework_id
            Framework identifier.
        graph_type
            Optional graph type for the selected package.
        snapshot_id
            Snapshot identifier.

        Returns
        -------
        CatalogPackageRuntime
            Exact accepted package runtime for the selected framework, snapshot, and
            optional graph type.
        """

        snapshot = self.catalog_service.get_framework(
            framework_id=framework_id, snapshot_id=snapshot_id
        )

        if graph_type is not None:
            package = self.catalog_service.get_graph_package(
                framework_id=framework_id,
                graph_type=graph_type,
                snapshot_id=snapshot_id,
            )
            return self.catalog_service.get_package_runtime(
                package.package_identity.graph_package_id
            )

        if len(snapshot.graph_packages) != 1:
            raise CapabilityUnavailableError(
                details={
                    "framework_id": str(framework_id),
                    "graph_package_count": len(snapshot.graph_packages),
                    "snapshot_id": str(snapshot_id),
                },
                message=(
                    "The resource URI does not identify one unambiguous graph package."
                ),
            )

        (package,) = snapshot.graph_packages
        return self.catalog_service.get_package_runtime(
            package.package_identity.graph_package_id
        )

    def _permits_resource_kind(
        self, *, resource_kind: ResourceKind, runtime: CatalogPackageRuntime
    ) -> bool:
        """Return whether current package rights permit one resource kind.

        Parameters
        ----------
        resource_kind
            Candidate resource family kind to test against the current rights.
        runtime
            Exact accepted package runtime supplying the current access rights.

        Returns
        -------
        bool
            ``True`` when policy grants access to the resource kind, else ``False``.
        """

        try:
            self.policy.require_resource_access(
                resource_kind=resource_kind, rights=runtime.catalog_package.rights
            )
        except ResourceAccessDeniedError:
            return False

        return True

    def artifact(
        self,
        *,
        artifact_name: ArtifactName,
        framework_id: FrameworkId,
        snapshot_id: SnapshotId,
    ) -> ResourceDocument:
        """Return one approved exact manifest-declared artifact.

        Parameters
        ----------
        artifact_name
            Artifact name.
        framework_id
            Framework identifier.
        snapshot_id
            Snapshot identifier.

        Returns
        -------
        ResourceDocument
            Exact manifest-declared artifact.
        """

        runtime = self._package_runtime(
            framework_id=framework_id, snapshot_id=snapshot_id
        )
        logical_name = str(artifact_name)
        decision = self.policy.artifact_decision(
            logical_name=logical_name, rights=runtime.catalog_package.rights
        )
        content, reference = self.repository.read_artifact(
            loaded_package=runtime.loaded_package, logical_name=logical_name
        )
        graph_package_id = runtime.catalog_package.package_identity.graph_package_id
        return self._build_raw_document(
            canonical_uri=artifact_uri(
                artifact_name=artifact_name,
                framework_id=framework_id,
                snapshot_id=snapshot_id,
            ),
            content=content,
            mime_type=decision.mime_type,
            package=runtime.catalog_package,
            resource_kind=ResourceKind.ARTIFACT,
            source_artifacts=(
                _source_evidence(
                    graph_package_id=graph_package_id, reference=reference
                ),
            ),
        )

    def catalog(self) -> ResourceDocument:
        """Return the complete accepted catalog as deterministic JSON.

        Returns
        -------
        ResourceDocument
            Complete catalog document.
        """

        evidence = tuple(
            self._manifest_evidence(
                graph_package_id=(
                    runtime.catalog_package.package_identity.graph_package_id
                ),
                loaded_package=runtime.loaded_package,
            )
            for runtime in self.catalog_service.load_result.package_runtimes
        )
        return self._build_derived_document(
            canonical_uri=CATALOG_URI,
            resource_kind=ResourceKind.CATALOG,
            source_artifacts=evidence,
            value=self.catalog_service.catalog,
        )

    def framework(self, framework_id: FrameworkId) -> ResourceDocument:
        """Return one exact framework family and all accepted snapshots.

        Parameters
        ----------
        framework_id
            Framework identifier.

        Returns
        -------
        ResourceDocument
            Exact framework family document.
        """

        family = self.catalog_service.get_framework_family(framework_id)
        evidence = self._family_manifest_evidence(family)
        return self._build_derived_document(
            canonical_uri=framework_uri(framework_id),
            resource_kind=ResourceKind.FRAMEWORK,
            source_artifacts=evidence,
            value=family,
        )

    def interpretation_profile(
        self, *, framework_id: FrameworkId, snapshot_id: SnapshotId
    ) -> ResourceDocument:
        """Return exact retained bytes for the selected interpretation profile.

        Parameters
        ----------
        framework_id
            Framework identifier.
        snapshot_id
            Snapshot identifier.

        Returns
        -------
        ResourceDocument
            Exact retained bytes for the selected interpretation profile.
        """

        runtime = self._package_runtime(
            framework_id=framework_id, snapshot_id=snapshot_id
        )
        self.policy.require_resource_access(
            resource_kind=ResourceKind.INTERPRETATION_PROFILE,
            rights=runtime.catalog_package.rights,
        )
        content = self.repository.read_profile(runtime.loaded_package)
        graph_package_id = runtime.catalog_package.package_identity.graph_package_id
        evidence = ResourceSourceEvidence(
            graph_package_id=graph_package_id,
            logical_name="interpretationProfile",
            sha256=runtime.loaded_package.profile_sha256,
            size_bytes=len(content),
        )
        return self._build_raw_document(
            canonical_uri=interpretation_profile_uri(
                framework_id=framework_id, snapshot_id=snapshot_id
            ),
            content=content,
            mime_type="application/json",
            package=runtime.catalog_package,
            resource_kind=ResourceKind.INTERPRETATION_PROFILE,
            source_artifacts=(evidence,),
        )

    def manifest(
        self, *, framework_id: FrameworkId, snapshot_id: SnapshotId
    ) -> ResourceDocument:
        """Return exact retained bytes for one accepted package manifest.

        Parameters
        ----------
        framework_id
            Framework identifier.
        snapshot_id
            Snapshot identifier.

        Returns
        -------
        ResourceDocument
            Exact retained bytes for one accepted package manifest.
        """

        runtime = self._package_runtime(
            framework_id=framework_id, snapshot_id=snapshot_id
        )
        content = self.repository.read_manifest(runtime.loaded_package)
        graph_package_id = runtime.catalog_package.package_identity.graph_package_id
        return self._build_raw_document(
            canonical_uri=manifest_uri(
                framework_id=framework_id, snapshot_id=snapshot_id
            ),
            content=content,
            mime_type="application/json",
            package=runtime.catalog_package,
            resource_kind=ResourceKind.MANIFEST,
            source_artifacts=(
                self._manifest_evidence(
                    graph_package_id=graph_package_id,
                    loaded_package=runtime.loaded_package,
                ),
            ),
        )

    def package_resource_capabilities(
        self, graph_package_id: GraphPackageId
    ) -> tuple[tuple[ResourceKind, ...], tuple[ArtifactName, ...]]:
        """Return exact rights-conditioned resource availability for one package.

        Parameters
        ----------
        graph_package_id
            Exact accepted graph-package identifier.

        Returns
        -------
        tuple[tuple[ResourceKind, ...], tuple[ArtifactName, ...]]
            Available package-scoped resource families and generic artifact names in
            deterministic public order.
        """

        runtime = self.catalog_service.get_package_runtime(graph_package_id)
        logical_names = tuple(
            sorted(
                str(reference.logical_name)
                for reference in runtime.loaded_package.artifacts
            )
        )
        available_artifacts = self._available_artifact_names(
            logical_names=logical_names, runtime=runtime
        )
        available_kinds: list[ResourceKind] = [
            ResourceKind.INTERPRETATION_PROFILE,
            ResourceKind.MANIFEST,
        ]

        if "validationReport" in logical_names:
            available_kinds.append(ResourceKind.VALIDATION)

        if "unresolvedItems" in logical_names and self._permits_resource_kind(
            resource_kind=ResourceKind.UNRESOLVED, runtime=runtime
        ):
            available_kinds.append(ResourceKind.UNRESOLVED)

        available_kinds.extend(self._available_standards_kinds(runtime))

        if available_artifacts:
            available_kinds.append(ResourceKind.ARTIFACT)

        return (
            tuple(sorted(available_kinds, key=lambda value: value.value)),
            available_artifacts,
        )

    def relationship(
        self,
        *,
        framework_id: FrameworkId,
        relationship_id: RelationshipId,
        snapshot_id: SnapshotId,
    ) -> ResourceDocument:
        """Return one exact package-local relationship as deterministic JSON.

        Parameters
        ----------
        framework_id
            Framework identifier.
        relationship_id
            Exact package-local relationship identifier.
        snapshot_id
            Snapshot identifier.

        Returns
        -------
        ResourceDocument
            Complete relationship document with content and metadata.
        """

        runtime = self._package_runtime(
            framework_id=framework_id,
            graph_type=GraphType.ACADEMIC_STANDARDS,
            snapshot_id=snapshot_id,
        )
        self.policy.require_resource_access(
            resource_kind=ResourceKind.RELATIONSHIP,
            rights=runtime.catalog_package.rights,
        )
        relationship = runtime.graph_store.relationships_by_id.get(relationship_id)

        if relationship is None:
            raise ResourceNotFoundError(
                details={"relationship_id": str(relationship_id)},
                message="The requested relationship is unavailable in the package.",
            )

        reference = self.repository.artifact_reference(
            loaded_package=runtime.loaded_package, logical_name="relationships"
        )
        graph_package_id = runtime.catalog_package.package_identity.graph_package_id
        return self._build_derived_document(
            canonical_uri=relationship_uri(
                framework_id=framework_id,
                relationship_id=relationship_id,
                snapshot_id=snapshot_id,
            ),
            package=runtime.catalog_package,
            resource_kind=ResourceKind.RELATIONSHIP,
            source_artifacts=(
                _source_evidence(
                    graph_package_id=graph_package_id, reference=reference
                ),
            ),
            value=relationship,
        )

    def standard(
        self, *, framework_id: FrameworkId, node_id: NodeId, snapshot_id: SnapshotId
    ) -> ResourceDocument:
        """Return one exact outer-node-ID standard as deterministic JSON.

        Parameters
        ----------
        framework_id
            Framework identifier.
        node_id
            Exact outer node identifier.
        snapshot_id
            Snapshot identifier.

        Returns
        -------
        ResourceDocument
            Complete standard document with content and metadata.
        """

        runtime = self._package_runtime(
            framework_id=framework_id,
            graph_type=GraphType.ACADEMIC_STANDARDS,
            snapshot_id=snapshot_id,
        )
        self.policy.require_resource_access(
            resource_kind=ResourceKind.STANDARD, rights=runtime.catalog_package.rights
        )
        result = self.standards_service.get_standard(
            GetStandardRequest(
                framework_id=framework_id,
                graph_type=GraphType.ACADEMIC_STANDARDS,
                identifier=NodeIdStandardIdentifier(
                    identifier_type="node_id", node_id=node_id
                ),
                snapshot_id=snapshot_id,
            )
        )
        reference = self.repository.artifact_reference(
            loaded_package=runtime.loaded_package, logical_name="nodes"
        )
        graph_package_id = runtime.catalog_package.package_identity.graph_package_id
        return self._build_derived_document(
            canonical_uri=standard_uri(
                framework_id=framework_id, node_id=node_id, snapshot_id=snapshot_id
            ),
            package=runtime.catalog_package,
            resource_kind=ResourceKind.STANDARD,
            source_artifacts=(
                _source_evidence(
                    graph_package_id=graph_package_id, reference=reference
                ),
            ),
            value=result,
        )

    def standard_provenance(
        self,
        *,
        framework_id: FrameworkId,
        node_id: NodeId,
        snapshot_id: SnapshotId,
    ) -> ResourceDocument:
        """Return one exact standard's selected detailed provenance entry.

        Parameters
        ----------
        framework_id
            Framework identifier.
        node_id
            Exact outer node identifier.
        snapshot_id
            Snapshot identifier.

        Returns
        -------
        ResourceDocument
            Complete standard provenance document with content and metadata.
        """

        runtime = self._package_runtime(
            framework_id=framework_id,
            graph_type=GraphType.ACADEMIC_STANDARDS,
            snapshot_id=snapshot_id,
        )
        self.policy.require_resource_access(
            resource_kind=ResourceKind.STANDARD_PROVENANCE,
            rights=runtime.catalog_package.rights,
        )
        standard_result = self.standards_service.get_standard(
            GetStandardRequest(
                framework_id=framework_id,
                graph_type=GraphType.ACADEMIC_STANDARDS,
                identifier=NodeIdStandardIdentifier(
                    identifier_type="node_id", node_id=node_id
                ),
                snapshot_id=snapshot_id,
            )
        )
        case_identifier_uuid = standard_result.node.case_identifier_uuid

        if case_identifier_uuid is None:
            raise ResourceNotFoundError(
                details={"node_id": str(node_id)},
                message="The requested standard has no exact CASE UUID provenance key.",
            )

        content, reference = self.repository.read_artifact(
            loaded_package=runtime.loaded_package, logical_name="entityProvenance"
        )
        document = _parse_json_object(content)
        items = document.get("items")

        if not isinstance(items, dict):
            raise ResourceNotFoundError(
                message="The accepted provenance artifact has no item index."
            )

        provenance = items.get(str(case_identifier_uuid))

        if not isinstance(provenance, dict):
            raise ResourceNotFoundError(
                details={
                    "case_identifier_uuid": str(case_identifier_uuid),
                    "node_id": str(node_id),
                },
                message="The requested standard provenance entry is unavailable.",
            )

        result = StandardProvenanceResult(
            case_identifier_uuid=case_identifier_uuid,
            node_id=node_id,
            provenance=provenance,
        )
        graph_package_id = runtime.catalog_package.package_identity.graph_package_id
        return self._build_derived_document(
            canonical_uri=standard_provenance_uri(
                framework_id=framework_id, node_id=node_id, snapshot_id=snapshot_id
            ),
            package=runtime.catalog_package,
            resource_kind=ResourceKind.STANDARD_PROVENANCE,
            source_artifacts=(
                _source_evidence(
                    graph_package_id=graph_package_id, reference=reference
                ),
            ),
            value=result,
        )

    def unresolved(
        self, *, framework_id: FrameworkId, snapshot_id: SnapshotId
    ) -> ResourceDocument:
        """Return exact bytes for one accepted unresolved-items artifact.

        Parameters
        ----------
        framework_id
            Framework identifier.
        snapshot_id
            Snapshot identifier.

        Returns
        -------
        ResourceDocument
            Complete unresolved-items document with content and metadata.
        """

        return self._dedicated_artifact(
            canonical_uri=unresolved_uri(
                framework_id=framework_id, snapshot_id=snapshot_id
            ),
            framework_id=framework_id,
            logical_name="unresolvedItems",
            resource_kind=ResourceKind.UNRESOLVED,
            snapshot_id=snapshot_id,
        )

    def validation(
        self, *, framework_id: FrameworkId, snapshot_id: SnapshotId
    ) -> ResourceDocument:
        """Return exact bytes for one accepted detailed validation report.

        Parameters
        ----------
        framework_id
            Framework identifier.
        snapshot_id
            Snapshot identifier.

        Returns
        -------
        ResourceDocument
            Complete validation report document with content and metadata.
        """

        return self._dedicated_artifact(
            canonical_uri=validation_uri(
                framework_id=framework_id, snapshot_id=snapshot_id
            ),
            framework_id=framework_id,
            logical_name="validationReport",
            resource_kind=ResourceKind.VALIDATION,
            snapshot_id=snapshot_id,
        )
