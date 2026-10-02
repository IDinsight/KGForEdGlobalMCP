"""Select stored LP evidence through the accepted catalog without filesystem reads."""

# Standard Library
import hashlib
import json

from collections.abc import Mapping
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import cast

# Third Party Library
from pydantic import ValidationError

# Package Library
from kgfegmcp.catalog.models import CatalogPackageRuntime
from kgfegmcp.catalog.service import CatalogService
from kgfegmcp.domain.enums import CodeAvailability, GraphType
from kgfegmcp.domain.identifiers import (
    ArtifactName,
    FrameworkId,
    GraphPackageId,
    Sha256Digest,
    SnapshotId,
)
from kgfegmcp.errors import (
    AmbiguousGraphNodeError,
    CapabilityUnavailableError,
    GraphNodeNotFoundError,
    InvalidProgressionRequestError,
    LearningProgressionNotFoundError,
    ProgressionResultTooLargeError,
    StandardNotFoundError,
)
from kgfegmcp.graph.models import GraphRelationship, StandardNode
from kgfegmcp.resources.models import ResourceKind
from kgfegmcp.resources.policy import ResourcePolicy
from kgfegmcp.resources.uri import (
    artifact_uri,
    learning_progressions_uri,
    manifest_uri,
    relationship_provenance_uri,
    relationship_uri,
    standard_uri,
)
from kgfegmcp.search.models import (
    ExactCodeSearchQuery,
    ExactPackageSearchScope,
    SearchFilters,
    SearchMode,
    SearchSelectionMode,
)
from kgfegmcp.search.service import SearchService
from kgfegmcp.services.frameworks import FrameworkService
from kgfegmcp.services.lp_discovery import collection_result, ordered_progressions
from kgfegmcp.services.lp_models import (
    MAX_PROGRESSION_RESULT_BYTES,
    MAX_STATEMENT_EXCERPT_CHARACTERS,
    GetLearningProgressionPathsRequest,
    GetLearningProgressionPathsResult,
    GetLearningProgressionRequest,
    GetLearningProgressionResult,
    GetStandardProgressionsRequest,
    ProgressionArtifactIdentity,
    ProgressionCollectionResult,
    ProgressionEvidenceResult,
    ProgressionMetadata,
    ProgressionRelationshipEvidence,
    ProgressionStandardIdentifier,
    ProgressionStandardSummary,
    SearchLearningProgressionsRequest,
    StatementCodeStandardIdentifier,
    TraverseLearningProgressionsRequest,
    TraverseLearningProgressionsResult,
)
from kgfegmcp.services.lp_paths import paths_result
from kgfegmcp.services.lp_traversal import (
    TraversalAdjacency,
    traversal_adjacency,
    traversal_result,
)
from kgfegmcp.services.models import (
    CaseUriStandardIdentifier,
    CaseUuidStandardIdentifier,
    NodeIdStandardIdentifier,
    package_reference,
)


def progression_result_text(result: ProgressionEvidenceResult) -> str:
    """Format a concise tool summary without duplicating the evidence tables.

    Parameters
    ----------
    result
        Complete typed evidence for one pinned operation.

    Returns
    -------
    str
        Summary suitable for the future MCP adapter and byte-budget calculation.
    """

    identity = result.metadata.package.package_identity
    page_notice = ""

    if isinstance(result, ProgressionCollectionResult):
        page_notice = (
            f"\nPage: {result.page.returned_count} returned, "
            f"{result.page.examined_count} examined. "
            f"Selection complete: {result.page.is_complete}. "
            f"Stopping reason: {result.page.stopping_reason or 'exhausted'}. "
            f"Counts describe this page; package coverage is separate metadata. "
            f"A continuation cursor requires unchanged route, filters and limits. "
            f"Absence of a stored match does not establish absence of a "
            f"pedagogical connection."
        )

    if isinstance(result, TraverseLearningProgressionsResult):
        page_notice = (
            f"\nRequested depth complete: {result.scope_complete}. "
            f"Reachable graph exhausted: {result.graph_exhausted}. "
            f"Truncation reasons: {', '.join(result.truncation_reasons) or 'none'}. "
            f"Examined: {result.counters.examined_relationship_count} adjacency edges. "
            f"{result.traversal_notice}"
        )

    if isinstance(result, GetLearningProgressionPathsResult):
        page_notice = (
            f"\nReturned paths: {len(result.paths)}. "
            f"Requested depth complete: {result.scope_complete}. "
            f"Simple-path search exhausted: {result.graph_exhausted}. "
            f"Truncation reasons: {', '.join(result.truncation_reasons) or 'none'}. "
            f"Examined: {result.counters.examined_relationship_count} adjacency edges. "
            f"{result.path_notice}"
        )

    return (
        f"Stored learning progressions: {len(result.relationships)} relationships, "
        f"{len(result.nodes)} standards. Snapshot: {identity.snapshot_id}.\n"
        f"{result.metadata.generated_origin_notice}\n"
        f"{result.metadata.semantic_notice}\n"
        f"Summary: {result.metadata.summary_uri}{page_notice}"
    )


def require_progression_result_size(
    *, result: ProgressionEvidenceResult, text: str | tuple[str, ...]
) -> int:
    """Enforce the fixed UTF-8 ceiling on tool text plus structured evidence.

    Parameters
    ----------
    result
        Complete evidence serialized with the public schema aliases.
    text
        Single tool text block or the complete tuple of adapter text blocks.

    Returns
    -------
    int
        Encoded envelope bytes, including JSON escaping and conservative whitespace.

    Raises
    ------
    ProgressionResultTooLargeError
        If the complete result exceeds the fixed ceiling.
    """

    # Include envelope/escaping overhead; Unicode characters are measured as bytes.
    envelope = {
        "content": [
            {"text": block, "type": "text"}
            for block in ((text,) if isinstance(text, str) else text)
        ],
        "structuredContent": result.model_dump(by_alias=True, mode="json"),
    }
    size = len(json.dumps(ensure_ascii=False, obj=envelope).encode("utf-8"))

    if size > MAX_PROGRESSION_RESULT_BYTES:
        raise ProgressionResultTooLargeError(
            message="The stored progression result exceeds the 1 MiB tool ceiling.",
            recovery_hint=(
                f"Read the exact relationship, standard and provenance resource URIs "
                f"under the package rights and resource-size policy. "
                f"Package manifest: {result.metadata.manifest_uri}"
            ),
        )

    return size


@dataclass(frozen=True, slots=True)
class LearningProgressionsService:
    """Reuse one accepted runtime, standard indexes and rights policy for LP queries."""

    catalog_service: CatalogService
    framework_service: FrameworkService
    resource_policy: ResourcePolicy
    search_service: SearchService
    _progressions_by_package: Mapping[GraphPackageId, tuple[GraphRelationship, ...]] = (
        field(init=False, repr=False)
    )
    _traversal_by_package: Mapping[GraphPackageId, TraversalAdjacency] = field(
        init=False, repr=False
    )

    def __post_init__(self) -> None:
        """Index sorted original LP references once, without another graph store."""

        packages = tuple(
            package
            for family in self.catalog_service.list_frameworks().frameworks
            for snapshot in family.snapshots
            for package in snapshot.graph_packages
        )
        ordered = {
            package.package_identity.graph_package_id: ordered_progressions(
                runtime=self.catalog_service.get_package_runtime(
                    graph_package_id=package.package_identity.graph_package_id
                )
            )
            for package in packages
        }
        object.__setattr__(self, "_progressions_by_package", MappingProxyType(ordered))
        adjacency = {
            package.package_identity.graph_package_id: traversal_adjacency(
                runtime=self.catalog_service.get_package_runtime(
                    graph_package_id=package.package_identity.graph_package_id
                )
            )
            for package in packages
        }
        object.__setattr__(self, "_traversal_by_package", MappingProxyType(adjacency))

    @staticmethod
    def evidence_metadata(*, runtime: CatalogPackageRuntime) -> ProgressionMetadata:
        """Project load-time identity and retained coverage without reloading files.

        Parameters
        ----------
        runtime
            Exact accepted LP runtime pinned by the route helper.

        Returns
        -------
        ProgressionMetadata
            Artifact byte identities, rights, limits, coverage and evidence links.
        """

        identity = runtime.catalog_package.package_identity
        evidence = runtime.loaded_package.learning_progression_evidence

        if evidence is None:
            raise CapabilityUnavailableError(
                message="Stored LP evidence is unavailable."
            )

        return ProgressionMetadata(
            artifacts=tuple(
                ProgressionArtifactIdentity(
                    logical_name=artifact.logical_name,
                    sha256=artifact.sha256,
                    uri=artifact_uri(
                        artifact_name=artifact.logical_name,
                        framework_id=identity.framework_id,
                        snapshot_id=identity.snapshot_id,
                    ),
                )
                for artifact in sorted(
                    runtime.loaded_package.artifacts, key=lambda item: item.logical_name
                )
            ),
            coverage=evidence.coverage,
            manifest_sha256=cast(
                Sha256Digest,
                "sha256:"
                + hashlib.sha256(runtime.loaded_package.manifest_bytes).hexdigest(),
            ),
            manifest_uri=manifest_uri(
                framework_id=identity.framework_id, snapshot_id=identity.snapshot_id
            ),
            package=package_reference(package=runtime.catalog_package),
            stored_builds_towards_count=(
                runtime.catalog_package.counts.builds_towards_relationships
            ),
            stored_relates_to_count=runtime.catalog_package.counts.relates_to_relationships,
            summary_uri=learning_progressions_uri(
                framework_id=identity.framework_id, snapshot_id=identity.snapshot_id
            ),
            unresolved_uri=artifact_uri(
                artifact_name=cast(ArtifactName, "learningProgressionUnresolved"),
                framework_id=identity.framework_id,
                snapshot_id=identity.snapshot_id,
            ),
            validation_uri=artifact_uri(
                artifact_name=cast(ArtifactName, "learningProgressionValidation"),
                framework_id=identity.framework_id,
                snapshot_id=identity.snapshot_id,
            ),
        )

    def get_learning_progression(
        self, request: GetLearningProgressionRequest
    ) -> GetLearningProgressionResult:
        """Return exactly one accepted LP edge and its stored endpoint evidence.

        Parameters
        ----------
        request
            Framework, optional snapshot and exact relationship identifier.

        Returns
        -------
        GetLearningProgressionResult
            Original edge, bounded summaries/judgment and exact evidence identities.

        Raises
        ------
        LearningProgressionNotFoundError
            If the identifier is missing or belongs to a non-LP relationship.
        ProgressionResultTooLargeError
            If the complete result cannot fit without dropping stored evidence.
        """

        runtime = self.resolve_runtime(
            framework_id=request.framework_id, snapshot_id=request.snapshot_id
        )
        self.require_content_access(runtime=runtime)
        relationship = runtime.graph_store.relationships_by_id.get(
            request.relationship_id
        )

        if relationship is None or relationship.label not in {
            "buildsTowards",
            "relatesTo",
        }:
            raise LearningProgressionNotFoundError(
                message="The requested stored learning progression is unavailable."
            )

        result = GetLearningProgressionResult(
            metadata=self.evidence_metadata(runtime=runtime),
            nodes=tuple(
                self.standard_summary(
                    node=self.resolve_standard(
                        identifier=NodeIdStandardIdentifier(
                            identifier_type="node_id", node_id=node_id
                        ),
                        runtime=runtime,
                    ),
                    runtime=runtime,
                )
                for node_id in (
                    relationship.source_node_id,
                    relationship.target_node_id,
                )
            ),
            relationships=(
                self.relationship_evidence(relationship=relationship, runtime=runtime),
            ),
            request=request,
        )
        require_progression_result_size(
            result=result, text=progression_result_text(result=result)
        )
        return result

    def get_learning_progression_paths(
        self, request: GetLearningProgressionPathsRequest
    ) -> GetLearningProgressionPathsResult:
        """Find bounded alternative directed simple paths between exact standards.

        Parameters
        ----------
        request
            Source, target and positive depth/path bounds in one framework route.

        Returns
        -------
        GetLearningProgressionPathsResult
            Original generated hops, derived paths and honest search completeness.
        """

        runtime = self.resolve_runtime(
            framework_id=request.framework_id, snapshot_id=request.snapshot_id
        )
        self.require_content_access(runtime=runtime)
        return paths_result(
            adjacency=self._traversal_by_package[
                runtime.catalog_package.package_identity.graph_package_id
            ],
            request=request,
            runtime=runtime,
            service=self,
        )

    def get_standard_progressions(
        self, request: GetStandardProgressionsRequest
    ) -> ProgressionCollectionResult:
        """Return bounded direct builds and symmetric relates connections.

        Parameters
        ----------
        request
            Exact standard selection, connection meaning and page limits.

        Returns
        -------
        ProgressionCollectionResult
            Original edge tables, per-connection meanings and stateless continuation.
        """

        runtime = self.resolve_runtime(
            framework_id=request.framework_id, snapshot_id=request.snapshot_id
        )
        self.require_content_access(runtime=runtime)
        node = self.resolve_standard(identifier=request.identifier, runtime=runtime)
        store = runtime.graph_store
        groups = {
            "incoming_builds": store.incoming_by_type_and_node.get(
                ("buildsTowards", node.node_id), ()
            ),
            "outgoing_builds": store.outgoing_by_type_and_node.get(
                ("buildsTowards", node.node_id), ()
            ),
            "related": (
                *store.incoming_by_type_and_node.get(("relatesTo", node.node_id), ()),
                *store.outgoing_by_type_and_node.get(("relatesTo", node.node_id), ()),
            ),
        }
        keys = (
            tuple(groups)
            if request.connection_kind == "all"
            else (request.connection_kind,)
        )
        edges = {edge.relationship_id: edge for key in keys for edge in groups[key]}
        candidates = tuple(
            sorted(edges.values(), key=lambda edge: (edge.label, edge.relationship_id))
        )
        return collection_result(
            candidates=candidates, request=request, runtime=runtime, service=self
        )

    @staticmethod
    def relationship_evidence(
        *, relationship: GraphRelationship, runtime: CatalogPackageRuntime
    ) -> ProgressionRelationshipEvidence:
        """Link an original edge to its accepted bounded judgment projection.

        Parameters
        ----------
        relationship
            Exact stored LP edge from this runtime.
        runtime
            Owning accepted runtime with validated judgment projections.

        Returns
        -------
        ProgressionRelationshipEvidence
            Original record and full evidence resource references.

        Raises
        ------
        LearningProgressionNotFoundError
            If the supplied edge lacks accepted LP evidence.
        """

        evidence = runtime.loaded_package.learning_progression_evidence
        judgment = (
            next(
                (
                    item
                    for item in evidence.judgments
                    if item.relationship_id == relationship.relationship_id
                ),
                None,
            )
            if evidence is not None
            else None
        )

        if (
            judgment is None
            or runtime.graph_store.relationships_by_id.get(relationship.relationship_id)
            != relationship
        ):
            raise LearningProgressionNotFoundError(
                message="The requested edge has no accepted LP evidence."
            )

        identity = runtime.catalog_package.package_identity

        # Preserve the accepted projection's exact wording while clarifying confidence.
        judgment = judgment.model_copy(
            update={
                "confidence_notice": (
                    "Confidence is a model judgment, not a calibrated probability "
                    "of learner success or validated pedagogical correctness."
                )
            }
        )
        return ProgressionRelationshipEvidence(
            judgment=judgment,
            provenance_uri=relationship_provenance_uri(
                framework_id=identity.framework_id,
                relationship_id=relationship.relationship_id,
                snapshot_id=identity.snapshot_id,
            ),
            relationship=relationship,
            relationship_uri=relationship_uri(
                framework_id=identity.framework_id,
                relationship_id=relationship.relationship_id,
                snapshot_id=identity.snapshot_id,
            ),
        )

    def require_collection_result_size(
        self, *, result: ProgressionCollectionResult
    ) -> int:
        """Apply the shared complete text-plus-structured-content byte ceiling.

        Parameters
        ----------
        result
            Bounded collection with current continuation/count metadata.

        Returns
        -------
        int
            Encoded result bytes.
        """

        return require_progression_result_size(
            result=result, text=progression_result_text(result=result)
        )

    def require_content_access(self, *, runtime: CatalogPackageRuntime) -> None:
        """Apply the existing reviewed, full-text and single-standard rights rules.

        Parameters
        ----------
        runtime
            Owning package whose content will be returned.
        """

        self.resource_policy.require_resource_access(
            resource_kind=ResourceKind.RELATIONSHIP,
            rights=runtime.catalog_package.rights,
        )

    def require_paths_result_size(
        self, *, result: GetLearningProgressionPathsResult
    ) -> int:
        """Measure path text and structured evidence under the shared byte ceiling.

        Parameters
        ----------
        result
            Complete bounded path envelope.

        Returns
        -------
        int
            Encoded result bytes.
        """

        return require_progression_result_size(
            result=result, text=progression_result_text(result=result)
        )

    def require_traversal_result_size(
        self, *, result: TraverseLearningProgressionsResult
    ) -> int:
        """Measure the complete traversal envelope using the shared byte ceiling.

        Parameters
        ----------
        result
            Exact evidence with frontier and completeness metadata.

        Returns
        -------
        int
            Encoded result bytes.
        """

        return require_progression_result_size(
            result=result, text=progression_result_text(result=result)
        )

    def resolve_runtime(
        self, *, framework_id: FrameworkId, snapshot_id: SnapshotId | None
    ) -> CatalogPackageRuntime:
        """Resolve the route once and pin all subsequent operations to its runtime.

        Parameters
        ----------
        framework_id
            Required exact framework family.
        snapshot_id
            Optional exact snapshot, otherwise existing unique-current routing.

        Returns
        -------
        CatalogPackageRuntime
            The existing primary mixed-graph runtime with accepted LP capability.

        Raises
        ------
        CapabilityUnavailableError
            If the selected package lacks accepted stored LPs.
        """

        snapshot = self.framework_service.resolve_snapshot_selection(
            framework_id=framework_id, snapshot_id=snapshot_id
        )
        package = self.catalog_service.get_graph_package(
            framework_id=snapshot.framework_id,
            graph_type=GraphType.ACADEMIC_STANDARDS,
            snapshot_id=snapshot.snapshot_id,
        )
        runtime = self.catalog_service.get_package_runtime(
            graph_package_id=package.package_identity.graph_package_id
        )

        if not package.capabilities.has_learning_progressions or (
            runtime.loaded_package.learning_progression_evidence is None
        ):
            raise CapabilityUnavailableError(
                message="This snapshot does not provide accepted stored LPs."
            )

        return runtime

    def resolve_standard(
        self,
        *,
        identifier: ProgressionStandardIdentifier,
        runtime: CatalogPackageRuntime,
    ) -> StandardNode:
        """Resolve exact identifiers or a profile-enabled code without guessing.

        Parameters
        ----------
        identifier
            Node ID, CASE UUID/URI or exact statement code.
        runtime
            Already pinned package; selectors never choose another snapshot.

        Returns
        -------
        StandardNode
            Exact source standard, excluding framework roots and components.

        Raises
        ------
        StandardNotFoundError
            If no source standard matches.
        AmbiguousGraphNodeError
            If the identifier matches several standards.
        InvalidProgressionRequestError
            If a semantic code selection is invalid.
        """

        store = runtime.graph_store

        try:
            if isinstance(identifier, NodeIdStandardIdentifier):
                node = store.get_node_by_id(node_id=identifier.node_id).node
            elif isinstance(identifier, CaseUuidStandardIdentifier):
                node = store.get_node_by_case_identifier_uuid(
                    case_identifier_uuid=identifier.case_identifier_uuid
                ).node
            elif isinstance(identifier, CaseUriStandardIdentifier):
                node = store.get_node_by_case_identifier_uri(
                    case_identifier_uri=identifier.case_identifier_uri
                ).node
            elif isinstance(identifier, StatementCodeStandardIdentifier):
                node = self._resolve_code(identifier=identifier, runtime=runtime)
            else:
                raise InvalidProgressionRequestError(
                    message="Unsupported standard selector."
                )
        except GraphNodeNotFoundError as error:
            raise StandardNotFoundError(
                message="The selected standard is unavailable."
            ) from error

        if not isinstance(node, StandardNode):
            raise StandardNotFoundError(
                message="The selected node is not a source standard."
            )

        return node

    def search_learning_progressions(
        self, request: SearchLearningProgressionsRequest
    ) -> ProgressionCollectionResult:
        """Discover stored LP edges with profile-validated endpoint conjunctions.

        Parameters
        ----------
        request
            Type, standard and grade/type criteria with explicit endpoint scope.

        Returns
        -------
        ProgressionCollectionResult
            Bounded deduplicated evidence, matched facets and honest continuation.
        """

        runtime = self.resolve_runtime(
            framework_id=request.framework_id, snapshot_id=request.snapshot_id
        )
        self.require_content_access(runtime=runtime)
        return collection_result(
            candidates=self._progressions_by_package[
                runtime.catalog_package.package_identity.graph_package_id
            ],
            request=request,
            runtime=runtime,
            service=self,
        )

    def standard_summary(
        self, *, node: StandardNode, runtime: CatalogPackageRuntime
    ) -> ProgressionStandardSummary:
        """Retain identifiers and existing grade/type facets with a statement excerpt.

        Parameters
        ----------
        node
            Exact source standard from the selected runtime.
        runtime
            Pinned owning package and search facet machinery.

        Returns
        -------
        ProgressionStandardSummary
            Bounded wording, explicit excerpt flag and full standard resource URI.
        """

        identity = runtime.catalog_package.package_identity
        return ProgressionStandardSummary(
            case_identifier_uri=node.case_identifier_uri,
            case_identifier_uuid=node.case_identifier_uuid,
            facets=self.search_service.get_node_facet_evidence(
                graph_package_id=identity.graph_package_id, node_id=node.node_id
            ),
            node_id=node.node_id,
            standard_uri=standard_uri(
                framework_id=identity.framework_id,
                node_id=node.node_id,
                snapshot_id=identity.snapshot_id,
            ),
            statement_code=node.statement_code,
            statement_excerpt=(
                node.description[:MAX_STATEMENT_EXCERPT_CHARACTERS]
                if node.description is not None
                else None
            ),
            statement_excerpted=(
                node.description is not None
                and len(node.description) > MAX_STATEMENT_EXCERPT_CHARACTERS
            ),
            statement_type=node.statement_type,
        )

    def traverse_learning_progressions(
        self, request: TraverseLearningProgressionsRequest
    ) -> TraverseLearningProgressionsResult:
        """Return bounded upstream or downstream stored builds evidence.

        Parameters
        ----------
        request
            Exact standard selector, direction and finite service bounds.

        Returns
        -------
        TraverseLearningProgressionsResult
            Derived subgraph retaining original edge orientation and evidence.
        """

        runtime = self.resolve_runtime(
            framework_id=request.framework_id, snapshot_id=request.snapshot_id
        )
        self.require_content_access(runtime=runtime)
        return traversal_result(
            adjacency=self._traversal_by_package[
                runtime.catalog_package.package_identity.graph_package_id
            ],
            request=request,
            runtime=runtime,
            service=self,
        )

    def _resolve_code(
        self,
        *,
        identifier: StatementCodeStandardIdentifier,
        runtime: CatalogPackageRuntime,
    ) -> StandardNode:
        """Reuse profile-governed exact-code search and reject ambiguous results.

        Parameters
        ----------
        identifier
            Authored code selection whose syntax must satisfy existing search rules.
        runtime
            Pinned accepted package owning the code index.

        Returns
        -------
        StandardNode
            Unique exact matching source standard.
        """

        identity = runtime.catalog_package.package_identity

        if runtime.catalog_package.capabilities.code_search is CodeAvailability.NONE:
            raise CapabilityUnavailableError(
                message="This snapshot does not provide profile-enabled code selection."
            )

        try:
            query = ExactCodeSearchQuery(
                filters=SearchFilters(include_groupings=True),
                limit=2,
                mode=SearchMode.CODE_EXACT,
                query=identifier.statement_code,
                scope=ExactPackageSearchScope(
                    framework_id=identity.framework_id,
                    graph_type=identity.graph_type,
                    selection_mode=SearchSelectionMode.EXACT,
                    snapshot_id=identity.snapshot_id,
                ),
            )
        except ValidationError as error:
            raise InvalidProgressionRequestError(
                message="The statement-code selector is invalid."
            ) from error

        page = self.search_service.search(query=query)

        if not page.hits:
            raise StandardNotFoundError(
                message="The selected statement code is unavailable."
            )

        if len(page.hits) > 1 or page.has_more:
            raise AmbiguousGraphNodeError(
                message="The statement code selects several standards."
            )

        node = runtime.graph_store.get_node_by_id(
            node_id=page.hits[0].node.node_id
        ).node

        if not isinstance(node, StandardNode):
            raise StandardNotFoundError(
                message="The selected code is not a source standard."
            )

        return node
