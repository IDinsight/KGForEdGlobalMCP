"""This module builds read-only indexes for one successfully validated graph package.

This module turns the nodes and relationships from a validated ``LoadedGraphPackage``
into an efficient in-memory graph store. The store provides exact node and relationship
lookup, incoming and outgoing adjacency indexes, package identity, and the package's
deterministic source ordering.

A simple way to think about the store is as an organized filing cabinet. The loaded
package already contains the authoritative graph records; this module arranges
references to those records so callers can quickly find a node or retrieve the
relationships entering or leaving it without repeatedly scanning the entire package.

The graph-store factory may be called only after the caller has established the
following precondition from an existing ``PackageValidationOutcome``:

``outcome.loaded_package is not None and outcome.result.is_valid``

The store does not perform or repeat package validation. It also does not load files,
decode wire records, calculate checksums, repair graph data, choose a preferred parent,
infer instructional sequence, perform cross-package discovery, or persist data.

The store retains the exact decoded node and relationship instances from the loaded
package. Its own indexes use immutable collections or read-only mappings, and the
loaded package and its nested records are treated as read-only by contract.
"""

# Future Library
from __future__ import annotations

# Standard Library
from collections.abc import Mapping
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import TYPE_CHECKING, Self, cast

# Package Library
from kgfegmcp.domain.identifiers import (
    CaseIdentifierUri,
    CaseIdentifierUuid,
    NodeId,
    RelationshipId,
)
from kgfegmcp.errors import (
    AmbiguousGraphNodeError,
    GraphNodeNotFoundError,
    PackageValidationError,
)
from kgfegmcp.graph.models import (
    DirectNodeRelationshipsResult,
    DirectRelationshipDirection,
    GraphNeighbor,
    GraphNodeRecord,
    GraphNodeResult,
    GraphPackageIdentity,
    GraphRelationship,
    StandardNode,
    graph_relationship_order_key,
)

if TYPE_CHECKING:
    # Package Library
    from kgfegmcp.packages.models import LoadedGraphPackage


AdjacencyKey = tuple[str, NodeId]


def _freeze_adjacency(
    adjacency: dict[AdjacencyKey, list[GraphRelationship]],
) -> Mapping[AdjacencyKey, tuple[GraphRelationship, ...]]:
    """Freeze mutable adjacency buckets in deterministic relationship order.

    Parameters
    ----------
    adjacency
        Mutable relationship lists grouped by canonical label and endpoint node ID.

    Returns
    -------
    Mapping[AdjacencyKey, tuple[GraphRelationship, ...]]
        Read-only mapping whose values are deterministically ordered tuples.
    """

    frozen_adjacency: dict[AdjacencyKey, tuple[GraphRelationship, ...]] = {}

    for key, relationships in adjacency.items():
        ordered_relationships = list(relationships)
        ordered_relationships.sort(key=graph_relationship_order_key)
        frozen_adjacency[key] = tuple(ordered_relationships)

    return MappingProxyType(frozen_adjacency)


@dataclass(frozen=True, slots=True)
class GraphStore:
    """Hold immutable indexes for one successfully validated graph snapshot.

    The mappings and tuple collections owned by this store are immutable or read-only.
    Existing Pydantic graph records are retained by reference and remain read-only by
    contract; the store never mutates their fields or nested dictionaries.
    """

    _nodes_by_case_identifier_uri: Mapping[CaseIdentifierUri, GraphNodeRecord] = field(
        repr=False
    )
    _nodes_by_id: Mapping[NodeId, GraphNodeRecord] = field(repr=False)
    _relationships_by_id: Mapping[RelationshipId, GraphRelationship] = field(repr=False)
    framework_root_id: NodeId
    hierarchy_relationship_type: str
    items_in_deterministic_source_order: tuple[StandardNode, ...]
    package_identity: GraphPackageIdentity

    _incoming_by_type_and_node: Mapping[AdjacencyKey, tuple[GraphRelationship, ...]] = (
        field(repr=False)
    )
    _nodes_by_case_identifier_uuid: Mapping[CaseIdentifierUuid, GraphNodeRecord] = (
        field(repr=False)
    )
    _outgoing_by_type_and_node: Mapping[AdjacencyKey, tuple[GraphRelationship, ...]] = (
        field(repr=False)
    )

    @classmethod
    def from_validated_package(cls, loaded_package: LoadedGraphPackage) -> Self:
        """Build a read-only store from one successfully validated loaded package.

        Before invoking this factory, the caller must establish the construction
        precondition from an existing ``PackageValidationOutcome``:

        ``outcome.loaded_package is not None and outcome.result.is_valid``

        The caller may then pass ``outcome.loaded_package`` here. This factory does not
        revalidate package integrity or graph semantics. It never loads files, decodes
        records, recalculates checksums, repairs records, or mutates the loaded package.

        Parameters
        ----------
        loaded_package
            Frozen loaded-package aggregate from a successful PR 4 validation outcome.

        Returns
        -------
        Self
            Immutable per-package graph store containing exact source records.
        """

        nodes_by_id: dict[NodeId, GraphNodeRecord] = {
            loaded_package.framework_root.node_id: loaded_package.framework_root
        }

        for node in loaded_package.item_nodes:
            nodes_by_id[node.node_id] = node

        nodes_by_case_identifier_uri: dict[CaseIdentifierUri, GraphNodeRecord] = {}
        nodes_by_case_identifier_uuid: dict[CaseIdentifierUuid, GraphNodeRecord] = {}

        for node in nodes_by_id.values():
            if node.case_identifier_uri is not None:
                nodes_by_case_identifier_uri[node.case_identifier_uri] = node

            if node.case_identifier_uuid is not None:
                nodes_by_case_identifier_uuid[node.case_identifier_uuid] = node

        incoming_by_type_and_node: dict[AdjacencyKey, list[GraphRelationship]] = {}
        outgoing_by_type_and_node: dict[AdjacencyKey, list[GraphRelationship]] = {}
        relationships_by_id: dict[RelationshipId, GraphRelationship] = {}

        for relationship in loaded_package.relationships:
            relationships_by_id[relationship.relationship_id] = relationship
            incoming_key = (relationship.label, relationship.target_node_id)
            outgoing_key = (relationship.label, relationship.source_node_id)
            incoming_relationships = incoming_by_type_and_node.get(incoming_key)

            if incoming_relationships is None:
                incoming_relationships = []
                incoming_by_type_and_node[incoming_key] = incoming_relationships

            incoming_relationships.append(relationship)
            outgoing_relationships = outgoing_by_type_and_node.get(outgoing_key)

            if outgoing_relationships is None:
                outgoing_relationships = []
                outgoing_by_type_and_node[outgoing_key] = outgoing_relationships

            outgoing_relationships.append(relationship)

        manifest = loaded_package.manifest
        package_identity = GraphPackageIdentity(
            framework_id=manifest.framework_id,
            graph_package_id=manifest.graph_package_id,
            graph_type=manifest.graph_type,
            package_revision=manifest.package_revision,
            profile_id=manifest.profile.profile_id,
            profile_sha256=loaded_package.profile_sha256,
            profile_version=manifest.profile.profile_version,
            snapshot_id=manifest.snapshot_id,
        )

        return cls(
            _incoming_by_type_and_node=_freeze_adjacency(incoming_by_type_and_node),
            _nodes_by_case_identifier_uri=MappingProxyType(
                nodes_by_case_identifier_uri
            ),
            _nodes_by_case_identifier_uuid=MappingProxyType(
                nodes_by_case_identifier_uuid
            ),
            _nodes_by_id=MappingProxyType(nodes_by_id),
            _outgoing_by_type_and_node=_freeze_adjacency(outgoing_by_type_and_node),
            _relationships_by_id=MappingProxyType(relationships_by_id),
            framework_root_id=loaded_package.framework_root.node_id,
            hierarchy_relationship_type=(
                loaded_package.profile.hierarchy.relationship_type
            ),
            items_in_deterministic_source_order=loaded_package.item_nodes,
            package_identity=package_identity,
        )

    @property
    def incoming_by_type_and_node(
        self,
    ) -> Mapping[AdjacencyKey, tuple[GraphRelationship, ...]]:
        """Return the read-only incoming relationship adjacency index.

        Returns
        -------
        Mapping[AdjacencyKey, tuple[GraphRelationship, ...]]
            Relationships grouped by canonical label and target node ID.
        """

        return self._incoming_by_type_and_node

    @property
    def nodes_by_case_identifier_uri(
        self,
    ) -> Mapping[CaseIdentifierUri, GraphNodeRecord]:
        """Return the read-only exact CASE URI node index.

        Returns
        -------
        Mapping[CaseIdentifierUri, GraphNodeRecord]
            Nodes keyed by their distinct CASE URI values.
        """

        return self._nodes_by_case_identifier_uri

    @property
    def nodes_by_case_identifier_uuid(
        self,
    ) -> Mapping[CaseIdentifierUuid, GraphNodeRecord]:
        """Return the read-only exact CASE UUID node index.

        Returns
        -------
        Mapping[CaseIdentifierUuid, GraphNodeRecord]
            Nodes keyed by their distinct CASE UUID values.
        """

        return self._nodes_by_case_identifier_uuid

    @property
    def nodes_by_id(self) -> Mapping[NodeId, GraphNodeRecord]:
        """Return the read-only outer node identifier index.

        Returns
        -------
        Mapping[NodeId, GraphNodeRecord]
            Framework root and item nodes keyed by outer node ID.
        """

        return self._nodes_by_id

    @property
    def outgoing_by_type_and_node(
        self,
    ) -> Mapping[AdjacencyKey, tuple[GraphRelationship, ...]]:
        """Return the read-only outgoing relationship adjacency index.

        Returns
        -------
        Mapping[AdjacencyKey, tuple[GraphRelationship, ...]]
            Relationships grouped by canonical label and source node ID.
        """

        return self._outgoing_by_type_and_node

    @property
    def relationships_by_id(self) -> Mapping[RelationshipId, GraphRelationship]:
        """Return the read-only relationship identifier index.

        Returns
        -------
        Mapping[RelationshipId, GraphRelationship]
            Exact relationships keyed by outer relationship ID.
        """

        return self._relationships_by_id

    def _direct_neighbors(
        self,
        *,
        direction: DirectRelationshipDirection,
        node_id: NodeId,
        relationship_type: str | None,
    ) -> DirectNodeRelationshipsResult:
        """Build one direct parent or child result from immutable adjacency indexes.

        Parameters
        ----------
        direction
            Parent or child result direction.
        node_id
            Outer identifier of the origin node.
        relationship_type
            Explicit canonical label or ``None`` for the profile hierarchy label.

        Returns
        -------
        DirectNodeRelationshipsResult
            Exact adjacent nodes and relationships in deterministic order.

        Raises
        ------
        GraphNodeNotFoundError
            If the origin node is unavailable.
        PackageValidationError
            If an indexed relationship endpoint is unavailable despite the successful
            package-validation construction precondition.
        ValueError
            If an explicit relationship type is blank.
        """

        origin_node = self._require_node(node_id)
        selected_relationship_type = self._select_relationship_type(relationship_type)
        adjacency_key = selected_relationship_type, node_id

        if direction is DirectRelationshipDirection.PARENTS:
            relationships = self._incoming_by_type_and_node.get(adjacency_key)
        else:
            relationships = self._outgoing_by_type_and_node.get(adjacency_key)

        if relationships is None:
            relationships = ()

        neighbors: list[GraphNeighbor] = []

        for relationship in relationships:
            adjacent_node_id = (
                relationship.source_node_id
                if direction is DirectRelationshipDirection.PARENTS
                else relationship.target_node_id
            )
            adjacent_node = self._require_relationship_endpoint(
                node_id=adjacent_node_id, relationship_id=relationship.relationship_id
            )
            neighbors.append(
                GraphNeighbor(node=adjacent_node, relationship=relationship)
            )

        return DirectNodeRelationshipsResult(
            direction=direction,
            neighbors=tuple(neighbors),
            origin_node=origin_node,
            package_identity=self.package_identity,
            relationship_type=selected_relationship_type,
        )

    def _require_framework_root(self) -> GraphNodeRecord:
        """Return the indexed framework root or raise an invariant error.

        Returns
        -------
        GraphNodeRecord
            Exact framework-root record.

        Raises
        ------
        PackageValidationError
            If the store lacks its declared framework root despite the successful
            package-validation construction precondition.
        """

        node = self._nodes_by_id.get(self.framework_root_id)

        if node is None:
            raise PackageValidationError(
                details={"framework_root_id": str(self.framework_root_id)},
                message="The validated graph framework root is unavailable.",
            )

        return node

    def _require_node(self, node_id: NodeId) -> GraphNodeRecord:
        """Return one indexed node or raise a safe typed lookup error.

        Parameters
        ----------
        node_id
            Exact outer node identifier to resolve.

        Returns
        -------
        GraphNodeRecord
            Matching framework root or item node.

        Raises
        ------
        GraphNodeNotFoundError
            If the exact outer node identifier is unavailable.
        """

        node = self._nodes_by_id.get(node_id)

        if node is None:
            raise GraphNodeNotFoundError(
                details={
                    "identifier": str(node_id),
                    "identifier_namespace": "node_id",
                },
                message="No graph node matched the requested outer node identifier.",
            )

        return node

    def _require_relationship_endpoint(
        self, *, node_id: NodeId, relationship_id: RelationshipId
    ) -> GraphNodeRecord:
        """Return an indexed endpoint or raise a validated-package invariant error.

        Parameters
        ----------
        node_id
            Outer identifier declared by the relationship endpoint.
        relationship_id
            Exact relationship whose endpoint is being resolved.

        Returns
        -------
        GraphNodeRecord
            Exact endpoint record.

        Raises
        ------
        PackageValidationError
            If a relationship endpoint is absent despite the successful
            package-validation construction precondition.
        """

        node = self._nodes_by_id.get(node_id)

        if node is None:
            raise PackageValidationError(
                details={
                    "node_id": str(node_id),
                    "relationship_id": str(relationship_id),
                },
                message=(
                    "A validated graph relationship references an unavailable node."
                ),
            )

        return node

    def _select_relationship_type(self, relationship_type: str | None) -> str:
        """Return an exact explicit relationship label or the profile hierarchy label.

        Parameters
        ----------
        relationship_type
            Exact label supplied by the caller, or ``None`` for the profile default.

        Returns
        -------
        str
            Unchanged selected canonical relationship label.

        Raises
        ------
        ValueError
            If an explicit relationship type is blank.
        """

        if relationship_type is None:
            return self.hierarchy_relationship_type

        if not relationship_type.strip():
            raise ValueError("relationship_type must be non-blank.")

        return relationship_type

    def direct_children(
        self, *, node_id: NodeId, relationship_type: str | None = None
    ) -> DirectNodeRelationshipsResult:
        """Return every exact direct-child relationship for one node.

        Parameters
        ----------
        node_id
            Outer identifier of the origin node.
        relationship_type
            Exact canonical relationship label. When omitted, use the selected
            profile's hierarchy relationship type.

        Returns
        -------
        DirectNodeRelationshipsResult
            Deterministically ordered child nodes and complete relationships.

        Raises
        ------
        GraphNodeNotFoundError
            If the origin node is unavailable.
        PackageValidationError
            If an indexed relationship endpoint is unavailable despite the successful
            package-validation construction precondition.
        ValueError
            If an explicit relationship type is blank.
        """

        return self._direct_neighbors(
            direction=DirectRelationshipDirection.CHILDREN,
            node_id=node_id,
            relationship_type=relationship_type,
        )

    def direct_parents(
        self, *, node_id: NodeId, relationship_type: str | None = None
    ) -> DirectNodeRelationshipsResult:
        """Return every exact direct-parent relationship for one node.

        Parameters
        ----------
        node_id
            Outer identifier of the origin node.
        relationship_type
            Exact canonical relationship label. When omitted, use the selected
            profile's hierarchy relationship type.

        Returns
        -------
        DirectNodeRelationshipsResult
            Deterministically ordered parent nodes and complete relationships.

        Raises
        ------
        GraphNodeNotFoundError
            If the origin node is unavailable.
        PackageValidationError
            If an indexed relationship endpoint is unavailable despite the successful
            package-validation construction precondition.
        ValueError
            If an explicit relationship type is blank.
        """

        return self._direct_neighbors(
            direction=DirectRelationshipDirection.PARENTS,
            node_id=node_id,
            relationship_type=relationship_type,
        )

    def get_node_by_case_identifier_uri(
        self, case_identifier_uri: CaseIdentifierUri
    ) -> GraphNodeResult:
        """Return one node by an exact CASE URI lookup.

        Parameters
        ----------
        case_identifier_uri
            Exact opaque CASE URI without normalization.

        Returns
        -------
        GraphNodeResult
            Matching node and package identity.

        Raises
        ------
        GraphNodeNotFoundError
            If the exact CASE URI is not indexed.
        """

        node = self._nodes_by_case_identifier_uri.get(case_identifier_uri)

        if node is None:
            raise GraphNodeNotFoundError(
                details={
                    "identifier": str(case_identifier_uri),
                    "identifier_namespace": "case_identifier_uri",
                },
                message="No graph node matched the requested CASE URI.",
            )

        return GraphNodeResult(node=node, package_identity=self.package_identity)

    def get_node_by_case_identifier_uuid(
        self, case_identifier_uuid: CaseIdentifierUuid
    ) -> GraphNodeResult:
        """Return one node by an exact CASE UUID lookup.

        Parameters
        ----------
        case_identifier_uuid
            Exact opaque CASE UUID without normalization.

        Returns
        -------
        GraphNodeResult
            Matching node and package identity.

        Raises
        ------
        GraphNodeNotFoundError
            If the exact CASE UUID is not indexed.
        """

        node = self._nodes_by_case_identifier_uuid.get(case_identifier_uuid)

        if node is None:
            raise GraphNodeNotFoundError(
                details={
                    "identifier": str(case_identifier_uuid),
                    "identifier_namespace": "case_identifier_uuid",
                },
                message="No graph node matched the requested CASE UUID.",
            )

        return GraphNodeResult(node=node, package_identity=self.package_identity)

    def get_node_by_id(self, node_id: NodeId) -> GraphNodeResult:
        """Return one framework root or item by exact outer node ID.

        Parameters
        ----------
        node_id
            Exact opaque outer node identifier.

        Returns
        -------
        GraphNodeResult
            Matching node and package identity.

        Raises
        ------
        GraphNodeNotFoundError
            If the exact outer node identifier is not indexed.
        """

        node = self._require_node(node_id)
        return GraphNodeResult(node=node, package_identity=self.package_identity)

    def resolve_node(self, identifier: str) -> GraphNodeResult:
        """Resolve one exact value across outer ID, CASE UUID, and CASE URI indexes.

        Matches are deduplicated by outer node ID. The three representations remain
        separate and are never normalized or assumed equal.

        Parameters
        ----------
        identifier
            Exact opaque identifier value to probe in all three namespaces.

        Returns
        -------
        GraphNodeResult
            The single distinct matching node and package identity.

        Raises
        ------
        AmbiguousGraphNodeError
            If the value resolves to more than one distinct outer node ID.
        GraphNodeNotFoundError
            If the value resolves to no graph node.
        """

        matches: dict[NodeId, GraphNodeRecord] = {}
        outer_node = self._nodes_by_id.get(cast(NodeId, identifier))
        case_uuid_node = self._nodes_by_case_identifier_uuid.get(
            cast(CaseIdentifierUuid, identifier)
        )
        case_uri_node = self._nodes_by_case_identifier_uri.get(
            cast(CaseIdentifierUri, identifier)
        )

        for node in (outer_node, case_uuid_node, case_uri_node):
            if node is not None:
                matches[node.node_id] = node

        if not matches:
            raise GraphNodeNotFoundError(
                details={"identifier": identifier},
                message="No graph node matched the requested exact identifier.",
            )

        if len(matches) > 1:
            raise AmbiguousGraphNodeError(
                details={
                    "identifier": identifier,
                    "node_ids": tuple(sorted(str(node_id) for node_id in matches)),
                },
                message=(
                    "The identifier matches multiple graph nodes; specify the "
                    "identifier namespace."
                ),
            )

        node = next(iter(matches.values()))
        return GraphNodeResult(node=node, package_identity=self.package_identity)
