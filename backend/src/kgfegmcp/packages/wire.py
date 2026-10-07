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
from typing import Final, Literal, Self

# Third Party Library
from pydantic import ConfigDict, Field, StrictStr, TypeAdapter, model_validator

# Package Library
from kgfegmcp.domain.identifiers import CaseIdentifierUuid, NodeId, RelationshipId
from kgfegmcp.schemas import FrozenSchema

DELIVERY_SCHEMA_1_0_ENDPOINT_ENTITY_KEY: Final[str] = "caseIdentifierUUID"
DELIVERY_SCHEMA_1_0_FRAMEWORK_LABEL: Final[str] = "StandardsFramework"
DELIVERY_SCHEMA_1_0_HIERARCHY_RELATIONSHIP_TYPE: Final[str] = "hasChild"
DELIVERY_SCHEMA_1_0_ITEM_LABEL: Final[str] = "StandardsFrameworkItem"
DELIVERY_SCHEMA_1_1_COMPONENT_LABEL: Final[str] = "LearningComponent"
DELIVERY_SCHEMA_1_1_SUPPORTS_RELATIONSHIP_TYPE: Final[str] = "supports"
DELIVERY_SCHEMA_1_2_BUILDS_TOWARDS_RELATIONSHIP_TYPE: Final[str] = "buildsTowards"
DELIVERY_SCHEMA_1_2_RELATES_TO_RELATIONSHIP_TYPE: Final[str] = "relatesTo"
LEARNING_PROGRESSION_RELATIONSHIP_TYPES: Final[frozenset[str]] = frozenset(
    {
        DELIVERY_SCHEMA_1_2_BUILDS_TOWARDS_RELATIONSHIP_TYPE,
        DELIVERY_SCHEMA_1_2_RELATES_TO_RELATIONSHIP_TYPE,
    }
)
SUPPORTED_RELATIONSHIP_TYPES: Final[frozenset[str]] = frozenset(
    {
        DELIVERY_SCHEMA_1_0_HIERARCHY_RELATIONSHIP_TYPE,
        DELIVERY_SCHEMA_1_1_SUPPORTS_RELATIONSHIP_TYPE,
        *LEARNING_PROGRESSION_RELATIONSHIP_TYPES,
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

_CASE_IDENTIFIER_UUID_ADAPTER: TypeAdapter[CaseIdentifierUuid] = TypeAdapter(
    CaseIdentifierUuid
)


def _require_learning_progression_endpoint(
    *,
    entity: str | None,
    entity_key: str | None,
    entity_value: str | None,
    labels: tuple[str, ...],
) -> None:
    """Require an exact standards CASE selector without resolving a graph node.

    Parameters
    ----------
    entity
        Stored endpoint entity label.
    entity_key
        Stored endpoint namespace key.
    entity_value
        Unmodified source-controlled CASE identifier.
    labels
        Outer endpoint labels.

    Raises
    ------
    ValueError
        If the endpoint is not a standards item with an exact CASE selector.

    Examples
    --------
    >>> _require_learning_progression_endpoint(
    ...     entity="StandardsFrameworkItem", entity_key="caseIdentifierUUID",
    ...     entity_value="source-case-id", labels=("StandardsFrameworkItem",)
    ... )
    """

    if (
        labels != (DELIVERY_SCHEMA_1_0_ITEM_LABEL,)
        or entity != DELIVERY_SCHEMA_1_0_ITEM_LABEL
    ):
        raise ValueError("LP endpoints must be StandardsFrameworkItem records.")

    if entity_key != DELIVERY_SCHEMA_1_0_ENDPOINT_ENTITY_KEY:
        raise ValueError("LP endpoints require caseIdentifierUUID selectors.")

    _CASE_IDENTIFIER_UUID_ADAPTER.validate_python(entity_value)


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

    @model_validator(mode="after")
    def validate_learning_progression(self) -> Self:
        """Validate LP identity and endpoint shape without graph-wide acceptance.

        Returns
        -------
        Self
            Unmodified LP envelope with exact identity and standards selectors.

        Raises
        ------
        ValueError
            If LP labels, identifiers or endpoint declarations disagree.

        Examples
        --------
        >>> RelationshipWireEnvelope.model_validate(lp_record).label
        'buildsTowards'
        """

        properties = self.properties

        if (
            self.label not in LEARNING_PROGRESSION_RELATIONSHIP_TYPES
            and properties.relationship_type
            not in LEARNING_PROGRESSION_RELATIONSHIP_TYPES
        ):
            return self

        if self.label != properties.relationship_type:
            raise ValueError("LP label and relationshipType must agree.")

        if self.identifier != properties.identifier:
            raise ValueError("LP outer and property identifiers must agree.")

        _require_learning_progression_endpoint(
            entity=properties.source_entity,
            entity_key=properties.source_entity_key,
            entity_value=properties.source_entity_value,
            labels=self.source_labels,
        )
        _require_learning_progression_endpoint(
            entity=properties.target_entity,
            entity_key=properties.target_entity_key,
            entity_value=properties.target_entity_value,
            labels=self.target_labels,
        )
        return self
