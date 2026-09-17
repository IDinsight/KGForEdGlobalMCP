"""This module defines strict Learning Commons-shaped JSONL wire contracts.

The models in this module describe the external delivery envelopes exactly as they
arrive in ``nodes.jsonl`` and ``relationships.jsonl``. Known properties are exposed
with Pythonic field names, while every property value remains an unmodified string and
unknown properties are retained. Delivery encodings such as string booleans and JSON
arrays are intentionally decoded in `kgfegmcp.packages.decoder` rather than in these
raw wire models.
"""

# Standard Library
from collections.abc import Mapping
from typing import Final, Literal

# Third Party Library
from pydantic import ConfigDict, Field, StrictStr, model_validator

# Package Library
from kgfegmcp.domain.identifiers import NodeId, RelationshipId
from kgfegmcp.schemas import FrozenSchema

DELIVERY_SCHEMA_1_0_ENDPOINT_ENTITY_KEY: Final[str] = "caseIdentifierUUID"
DELIVERY_SCHEMA_1_0_FRAMEWORK_LABEL: Final[str] = "StandardsFramework"
DELIVERY_SCHEMA_1_0_HIERARCHY_RELATIONSHIP_TYPE: Final[str] = "hasChild"
DELIVERY_SCHEMA_1_0_ITEM_LABEL: Final[str] = "StandardsFrameworkItem"
DELIVERY_SCHEMA_1_1_COMPONENT_LABEL: Final[str] = "LearningComponent"
DELIVERY_SCHEMA_1_1_SUPPORTS_RELATIONSHIP_TYPE: Final[str] = "supports"
SUPPORTED_RELATIONSHIP_TYPES: Final[frozenset[str]] = frozenset(
    {
        DELIVERY_SCHEMA_1_0_HIERARCHY_RELATIONSHIP_TYPE,
        DELIVERY_SCHEMA_1_1_SUPPORTS_RELATIONSHIP_TYPE,
    }
)
DELIVERY_SCHEMA_1_1_COMPONENT_ENDPOINT_ENTITY_KEY: Final[str] = "identifier"
DELIVERY_SCHEMA_1_0_UNRESOLVED_ROOT_FALLBACK_STATUS: Final[str] = (
    "unresolvedRootFallback"
)
DELIVERY_SCHEMA_1_0_RELATIONSHIP_STATUS_VOCABULARY: Final[frozenset[str]] = frozenset(
    {DELIVERY_SCHEMA_1_0_UNRESOLVED_ROOT_FALLBACK_STATUS}
)
DELIVERY_SCHEMA_1_0_UNRESOLVED_RELATIONSHIP_STATUSES: Final[frozenset[str]] = frozenset(
    {DELIVERY_SCHEMA_1_0_UNRESOLVED_ROOT_FALLBACK_STATUS}
)


class WireProperties(FrozenSchema):
    """Base model for a property object whose source values must remain strings.

    Known properties are declared by subclasses. Unknown source properties are allowed
    deliberately and survive model validation so the boundary layer never discards
    source data.
    """

    model_config = ConfigDict(extra="allow", frozen=True)

    @model_validator(mode="before")
    @classmethod
    def require_string_property_values(cls, value: object) -> object:
        """Reject non-string property keys or values before field coercion.

        Parameters
        ----------
        value
            Candidate wire property object.

        Returns
        -------
        object
            The unchanged candidate property object.

        Raises
        ------
        ValueError
            If any property key or value is not a string.
        """

        if not isinstance(value, Mapping):
            return value

        invalid_keys = [
            key
            for key, property_value in value.items()
            if not isinstance(key, str) or not isinstance(property_value, str)
        ]

        if invalid_keys:
            raise ValueError("Delivery property keys and values must be strings.")

        return value


class NodeWireProperties(WireProperties):
    """Represent raw string properties carried by a node envelope."""

    academic_subject: StrictStr | None = None
    adoption_status: StrictStr | None = None
    attribution_statement: StrictStr | None = None
    author: StrictStr | None = None
    case_identifier_uri: StrictStr | None = Field(
        alias="caseIdentifierURI", default=None
    )
    case_identifier_uuid: StrictStr | None = Field(
        alias="caseIdentifierUUID", default=None
    )
    description: StrictStr | None = None
    grade_level: StrictStr | None = None
    identifier: StrictStr | None = None
    identity_key: StrictStr | None = None
    in_language: StrictStr | None = None
    is_current: StrictStr | None = None
    jurisdiction: StrictStr | None = None
    license: StrictStr | None = None
    name: StrictStr | None = None
    normalized_statement_type: StrictStr | None = None
    provider: StrictStr | None = None
    statement_code: StrictStr | None = None
    statement_type: StrictStr | None = None
    tags: StrictStr | None = None


class RelationshipWireProperties(WireProperties):
    """Represent raw string properties carried by a relationship envelope."""

    attribution_statement: StrictStr | None = None
    author: StrictStr | None = None
    description: StrictStr | None = None
    identifier: StrictStr | None = None
    license: StrictStr | None = None
    provider: StrictStr | None = None
    relationship_type: StrictStr | None = None
    resolution_status: StrictStr | None = None
    source_entity: StrictStr | None = None
    source_entity_key: StrictStr | None = None
    source_entity_value: StrictStr | None = None
    support_confidence: StrictStr | None = None
    target_entity: StrictStr | None = None
    target_entity_key: StrictStr | None = None
    target_entity_value: StrictStr | None = None


class NodeWireEnvelope(FrozenSchema):
    """Represent one strict raw node record from ``nodes.jsonl``."""

    identifier: NodeId
    labels: tuple[StrictStr, ...] = Field(min_length=1)
    properties: NodeWireProperties
    type: Literal["node"]


class RelationshipWireEnvelope(FrozenSchema):
    """Represent one strict raw relationship record from ``relationships.jsonl``."""

    identifier: RelationshipId
    label: StrictStr
    properties: RelationshipWireProperties
    source_identifier: NodeId = Field(alias="source_identifier")
    source_labels: tuple[StrictStr, ...] = Field(alias="source_labels", min_length=1)
    target_identifier: NodeId = Field(alias="target_identifier")
    target_labels: tuple[StrictStr, ...] = Field(alias="target_labels", min_length=1)
    type: Literal["relationship"]
