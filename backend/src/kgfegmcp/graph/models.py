"""This module defines semantic graph records and immutable graph-query result
contracts.

The semantic record models in this module represent individual graph records after the
existing package decoder has converted delivery-specific string encodings into typed
Python values. They remain curriculum-agnostic and preserve source identifiers,
properties, relationship status, and deterministic source export order without
assigning curriculum-specific meaning.

The graph-query models associate read-only graph records with immutable package
identity, direct-neighbor evidence, bounded traversal depth, deterministic ordering,
and explicit truncation state. They do not load packages, validate package acceptance,
mutate source records, infer instructional sequence, or perform cross-package discovery.
"""

# Future Library
from __future__ import annotations

# Standard Library
from enum import StrEnum
from typing import Annotated, Self, TypeAlias

# Third Party Library
from pydantic import Field, model_validator

# Package Library
from kgfegmcp.domain.enums import GraphType, NormalizedStatementType
from kgfegmcp.domain.identifiers import (
    CaseIdentifierUri,
    CaseIdentifierUuid,
    FrameworkId,
    GraphPackageId,
    LanguageTag,
    NodeId,
    ProfileId,
    ProfileVersion,
    RelationshipId,
    Sha256Digest,
    SnapshotId,
)
from kgfegmcp.schemas import FrozenSchema

SourceExportOrder = Annotated[int, Field(ge=1)]


class DirectNodeRelationshipsResult(FrozenSchema):
    """Return deterministic direct parents or children for one origin node."""

    direction: DirectRelationshipDirection
    neighbors: tuple[GraphNeighbor, ...]
    origin_node: GraphNodeRecord
    package_identity: GraphPackageIdentity
    relationship_type: str = Field(min_length=1)

    @model_validator(mode="after")
    def validate_direct_relationships(self) -> Self:
        """Require every neighbor relationship to match direction and origin.

        Returns
        -------
        Self
            The validated direct-neighbor result.

        Raises
        ------
        ValueError
            If a relationship has the wrong type, direction, endpoint, or a duplicate
            relationship identifier.
        """

        relationship_ids = tuple(
            neighbor.relationship.relationship_id for neighbor in self.neighbors
        )

        if len(relationship_ids) != len(set(relationship_ids)):
            raise ValueError(
                "Direct relationship results may not repeat a relationship identifier."
            )

        for neighbor in self.neighbors:
            relationship = neighbor.relationship

            if relationship.label != self.relationship_type:
                raise ValueError(
                    "Direct relationship results must use the selected relationship type."
                )

            if self.direction is DirectRelationshipDirection.PARENTS:
                source_matches = relationship.source_node_id == neighbor.node.node_id
                target_matches = relationship.target_node_id == self.origin_node.node_id
            else:
                source_matches = relationship.source_node_id == self.origin_node.node_id
                target_matches = relationship.target_node_id == neighbor.node.node_id

            if not source_matches or not target_matches:
                raise ValueError(
                    "Direct relationship endpoints do not match the declared direction."
                )

        ordered_neighbors = list(self.neighbors)
        ordered_neighbors.sort(
            key=lambda neighbor: graph_relationship_order_key(neighbor.relationship)
        )
        expected_order = tuple(ordered_neighbors)

        if self.neighbors != expected_order:
            raise ValueError(
                "Direct relationship results must use deterministic source order."
            )

        return self


class DirectRelationshipDirection(StrEnum):
    """Identify whether a direct-neighbor result contains parents or children."""

    CHILDREN = "children"
    PARENTS = "parents"


class GraphNode(FrozenSchema):
    """Represent fields shared by every decoded delivery node."""

    academic_subject: str | None = None
    adoption_status: str | None = None
    attribution_statement: str | None = None
    author: str | None = None
    case_identifier_uri: CaseIdentifierUri | None = None
    case_identifier_uuid: CaseIdentifierUuid | None = None
    in_language: LanguageTag | None = None
    is_current: bool | None = None
    jurisdiction: str | None = None
    labels: tuple[str, ...]
    license: str | None = None
    node_id: NodeId
    property_identifier: NodeId | None = None
    provider: str | None = None
    raw_properties: dict[str, str]
    source_export_order: SourceExportOrder


class FrameworkNode(GraphNode):
    """Represent one decoded standards-framework node."""

    name: str | None = None


class GraphNeighbor(FrozenSchema):
    """Associate one adjacent node with the exact authored relationship evidence."""

    node: GraphNodeRecord
    relationship: GraphRelationship


class GraphNodeResult(FrozenSchema):
    """Associate one exact graph node with its immutable package identity."""

    node: GraphNodeRecord
    package_identity: GraphPackageIdentity


class GraphPackageIdentity(FrozenSchema):
    """Identify the exact validated graph package associated with graph results."""

    framework_id: FrameworkId
    graph_package_id: GraphPackageId
    graph_type: GraphType
    package_revision: int = Field(ge=1)
    profile_id: ProfileId
    profile_sha256: Sha256Digest
    profile_version: ProfileVersion
    snapshot_id: SnapshotId


class GraphRelationship(FrozenSchema):
    """Represent one decoded relationship without resolving its endpoints."""

    attribution_statement: str | None = None
    author: str | None = None
    description: str | None = None
    label: str
    license: str | None = None
    property_identifier: RelationshipId | None = None
    provider: str | None = None
    raw_properties: dict[str, str]
    relationship_id: RelationshipId
    relationship_type: str | None = None
    resolution_status: str | None = None
    source_entity: str | None = None
    source_entity_key: str | None = None
    source_entity_value: str | None = None
    source_labels: tuple[str, ...]
    source_node_id: NodeId
    source_export_order: SourceExportOrder
    target_entity: str | None = None
    target_entity_key: str | None = None
    target_entity_value: str | None = None
    target_labels: tuple[str, ...]
    target_node_id: NodeId


class GraphTraversalDirection(StrEnum):
    """Identify whether a bounded traversal walks ancestors or descendants."""

    ANCESTORS = "ancestors"
    DESCENDANTS = "descendants"


class RootPath(FrozenSchema):
    """Represent one complete framework-root-to-origin path in source direction."""

    nodes: tuple[GraphNodeRecord, ...] = Field(min_length=1)
    relationships: tuple[GraphRelationship, ...]

    @model_validator(mode="after")
    def validate_path(self) -> Self:
        """Require a complete acyclic path with matching consecutive relationships.

        Returns
        -------
        Self
            The validated complete root path.

        Raises
        ------
        ValueError
            If nodes repeat or relationships do not connect consecutive path nodes.
        """

        if len(self.relationships) != len(self.nodes) - 1:
            raise ValueError(
                "A root path must contain exactly one fewer relationship than nodes."
            )

        node_ids = tuple(node.node_id for node in self.nodes)

        if len(node_ids) != len(set(node_ids)):
            raise ValueError("A root path may not repeat a node.")

        for index, relationship in enumerate(self.relationships):
            if relationship.source_node_id != self.nodes[index].node_id:
                raise ValueError(
                    "A root-path relationship source must match its preceding node."
                )

            if relationship.target_node_id != self.nodes[index + 1].node_id:
                raise ValueError(
                    "A root-path relationship target must match its following node."
                )

        return self


class RootPathsResult(FrozenSchema):
    """Return deterministically bounded complete paths from the root to one node."""

    framework_root_id: NodeId
    is_complete: bool
    max_depth: int = Field(ge=0)
    max_path_node_occurrences: int = Field(ge=1)
    max_paths: int = Field(ge=1)
    origin_node_id: NodeId
    package_identity: GraphPackageIdentity
    paths: tuple[RootPath, ...]
    relationship_type: str = Field(min_length=1)
    truncation_reason: TraversalTruncationReason | None = None

    @model_validator(mode="after")
    def validate_root_paths(self) -> Self:
        """Require complete ordered paths and consistent truncation metadata.

        Returns
        -------
        Self
            The validated root-path collection.

        Raises
        ------
        ValueError
            If bounds, endpoints, relationship types, path ordering, or truncation
            metadata conflict.
        """

        if len(self.paths) > self.max_paths:
            raise ValueError("Root-path results may not exceed max_paths.")

        node_occurrences = sum(len(path.nodes) for path in self.paths)

        if node_occurrences > self.max_path_node_occurrences:
            raise ValueError(
                "Root-path results may not exceed max_path_node_occurrences."
            )

        if self.is_complete:
            if self.truncation_reason is not None:
                raise ValueError(
                    "A complete root-path result may not declare a truncation reason."
                )
        elif self.truncation_reason not in {
            TraversalTruncationReason.MAX_PATH_NODE_OCCURRENCES,
            TraversalTruncationReason.MAX_PATHS,
        }:
            raise ValueError(
                "An incomplete root-path result must declare a path-size truncation."
            )

        for path in self.paths:
            if path.nodes[0].node_id != self.framework_root_id:
                raise ValueError("Every root path must begin at the framework root.")

            if path.nodes[-1].node_id != self.origin_node_id:
                raise ValueError("Every root path must end at the origin node.")

            if len(path.relationships) > self.max_depth:
                raise ValueError("A root path may not exceed max_depth.")

            if any(
                relationship.label != self.relationship_type
                for relationship in path.relationships
            ):
                raise ValueError(
                    "Root-path relationships must use the selected relationship type."
                )

        ordered_paths = list(self.paths)
        ordered_paths.sort(key=root_path_order_key)
        expected_path_order = tuple(ordered_paths)

        if self.paths != expected_path_order:
            raise ValueError(
                "Root paths must use deterministic root-to-origin relationship order."
            )

        if self.origin_node_id == self.framework_root_id:
            if len(self.paths) != 1:
                raise ValueError(
                    "The framework root must return exactly one singleton root path."
                )

            root_path = self.paths[0]

            if len(root_path.nodes) != 1 or root_path.relationships:
                raise ValueError(
                    "The framework root path must contain one node and no relationships."
                )

            if not self.is_complete:
                raise ValueError("The framework root path result must be complete.")

        return self


class StandardNode(GraphNode):
    """Represent one decoded standards-framework-item node."""

    description: str | None = None
    grade_level: tuple[str, ...] | None = None
    normalized_statement_type: NormalizedStatementType | None = None
    statement_code: str | None = None
    statement_type: str | None = None


class TraversalNode(FrozenSchema):
    """Associate one returned graph node with its minimum traversal depth."""

    depth: int = Field(ge=0)
    node: GraphNodeRecord


class TraversalResult(FrozenSchema):
    """Return one deterministic bounded ancestor or descendant traversal."""

    direction: GraphTraversalDirection
    is_complete: bool
    max_depth: int = Field(ge=0)
    max_nodes: int = Field(ge=1)
    nodes: tuple[TraversalNode, ...] = Field(min_length=1)
    origin_node_id: NodeId
    package_identity: GraphPackageIdentity
    relationships: tuple[GraphRelationship, ...]
    relationship_type: str = Field(min_length=1)
    truncation_reason: TraversalTruncationReason | None = None

    @model_validator(mode="after")
    def validate_traversal(self) -> Self:
        """Require traversal bounds, ordering, identity, and induced edges to agree.

        Returns
        -------
        Self
            The validated bounded traversal result.

        Raises
        ------
        ValueError
            If node identity, depth, ordering, relationship membership, or truncation
            metadata is inconsistent.
        """

        node_ids = tuple(traversal_node.node.node_id for traversal_node in self.nodes)

        if len(node_ids) != len(set(node_ids)):
            raise ValueError("Traversal results may not contain duplicate nodes.")

        if len(self.nodes) > self.max_nodes:
            raise ValueError("Traversal results may not exceed max_nodes.")

        origin_entries = tuple(
            traversal_node
            for traversal_node in self.nodes
            if traversal_node.node.node_id == self.origin_node_id
        )

        if len(origin_entries) != 1 or origin_entries[0].depth != 0:
            raise ValueError(
                "Traversal results must contain the origin exactly once at depth zero."
            )

        if any(traversal_node.depth > self.max_depth for traversal_node in self.nodes):
            raise ValueError("Traversal node depth may not exceed max_depth.")

        ordered_nodes = list(self.nodes)
        ordered_nodes.sort(
            key=lambda traversal_node: (
                traversal_node.depth,
                *graph_node_order_key(traversal_node.node),
            )
        )
        expected_node_order = tuple(ordered_nodes)

        if self.nodes != expected_node_order:
            raise ValueError(
                "Traversal nodes must use deterministic depth and source order."
            )

        if self.is_complete:
            if self.truncation_reason is not None:
                raise ValueError(
                    "A complete traversal result may not declare a truncation reason."
                )
        elif self.truncation_reason is not TraversalTruncationReason.MAX_NODES:
            raise ValueError(
                "An incomplete node traversal must declare max_nodes truncation."
            )

        returned_node_ids = set(node_ids)
        relationship_ids = tuple(
            relationship.relationship_id for relationship in self.relationships
        )

        if len(relationship_ids) != len(set(relationship_ids)):
            raise ValueError(
                "Traversal results may not repeat a relationship identifier."
            )

        for relationship in self.relationships:
            if relationship.label != self.relationship_type:
                raise ValueError(
                    "Traversal relationships must use the selected relationship type."
                )

            if (
                relationship.source_node_id not in returned_node_ids
                or relationship.target_node_id not in returned_node_ids
            ):
                raise ValueError(
                    "Traversal relationships must be induced by the returned node set."
                )

        ordered_relationships = list(self.relationships)
        ordered_relationships.sort(key=graph_relationship_order_key)
        expected_relationship_order = tuple(ordered_relationships)

        if self.relationships != expected_relationship_order:
            raise ValueError(
                "Traversal relationships must use deterministic source order."
            )

        return self


class TraversalTruncationReason(StrEnum):
    """Identify the deterministic size bound that prevented complete output."""

    MAX_NODES = "max_nodes"
    MAX_PATH_NODE_OCCURRENCES = "max_path_node_occurrences"
    MAX_PATHS = "max_paths"


GraphNodeRecord: TypeAlias = FrameworkNode | StandardNode


def graph_node_order_key(node: GraphNodeRecord) -> tuple[int, str]:
    """Return the deterministic display-order key for one graph node.

    Parameters
    ----------
    node
        Framework root or framework-item node.

    Returns
    -------
    tuple[int, str]
        Source export order followed by the opaque outer node identifier.
    """

    return node.source_export_order, str(node.node_id)


def graph_relationship_order_key(relationship: GraphRelationship) -> tuple[int, str]:
    """Return the deterministic display-order key for one graph relationship.

    Parameters
    ----------
    relationship
        Exact decoded graph relationship.

    Returns
    -------
    tuple[int, str]
        Source export order followed by the opaque relationship identifier.
    """

    return relationship.source_export_order, str(relationship.relationship_id)


def root_path_order_key(path: RootPath) -> tuple[tuple[int, str], ...]:
    """Return the deterministic lexicographic key for one complete root path.

    Parameters
    ----------
    path
        Complete path ordered from the framework root to its origin node.

    Returns
    -------
    tuple[tuple[int, str], ...]
        Relationship order keys from root to origin.
    """

    return tuple(
        graph_relationship_order_key(relationship)
        for relationship in path.relationships
    )
