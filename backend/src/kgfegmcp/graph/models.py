"""This module defines immutable semantic models for decoded graph records.

The models in this module represent individual graph records after the JSONL boundary
decoder has converted delivery-specific string encodings into typed Python values. They
remain curriculum-agnostic and describe record structure without assigning
curriculum-specific meaning.

Node models preserve the outer node identifier, identifiers declared by source
properties, labels, decoded values, original raw properties, and deterministic source
export order. Relationship models preserve the outer relationship identifier, outer
source and target endpoints, property-declared endpoint information, resolution status,
labels, raw properties, and source order.

These models intentionally do not compare identifiers, resolve endpoints, enforce
uniqueness, validate topology, require a tree structure, or establish other graph-wide
invariants. Those responsibilities belong in graph validation and service layers.
"""

# Standard Library
from typing import Annotated

# Third Party Library
from pydantic import Field

# Package Library
from kgfegmcp.domain.enums import NormalizedStatementType
from kgfegmcp.domain.identifiers import (
    CaseIdentifierUri,
    CaseIdentifierUuid,
    LanguageTag,
    NodeId,
    RelationshipId,
)
from kgfegmcp.schemas import FrozenSchema

SourceExportOrder = Annotated[int, Field(ge=1)]


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


class FrameworkNode(GraphNode):
    """Represent one decoded standards-framework node."""

    name: str | None = None


class StandardNode(GraphNode):
    """Represent one decoded standards-framework-item node."""

    description: str | None = None
    grade_level: tuple[str, ...] | None = None
    normalized_statement_type: NormalizedStatementType | None = None
    statement_code: str | None = None
    statement_type: str | None = None
