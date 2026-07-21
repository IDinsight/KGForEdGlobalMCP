"""This module contains shared framework-independent domain models.

This module defines immutable models that are used across multiple application layers
and are not owned by a particular package format, curriculum profile, storage
implementation, or MCP transport.

The current models separate source rights metadata from operator-controlled exposure
decisions and define versioned normalized-subject vocabularies. Package manifests,
curriculum profiles, catalog services, resource policies, and public results can
therefore rely on the same validated domain contracts.

Curriculum-specific subjects, grade systems, terminology, hierarchy rules, and code
conventions remain in versioned interpretation profiles rather than being embedded in
these shared models.
"""

# Standard Library
from typing import Self

# Third Party Library
from pydantic import AnyUrl, Field, model_validator

# Package Library
from kgfegmcp.domain.enums import DerivativeGenerationPolicy, RightsReviewStatus
from kgfegmcp.domain.identifiers import SchemaVersion
from kgfegmcp.schemas import FrozenSchema


class RightsPolicy(FrozenSchema):
    """Preserve source rights metadata and operator exposure decisions separately."""

    allow_bulk_resource: bool = False
    allow_full_text: bool = False
    allow_generated_derivatives: DerivativeGenerationPolicy = (
        DerivativeGenerationPolicy.REVIEW_REQUIRED
    )
    allow_standard_resources: bool = False
    attribution_statement: str = Field(min_length=1)
    license_uri: AnyUrl | None = None
    review_status: RightsReviewStatus
    source_license: str = Field(min_length=1)


class SubjectVocabulary(FrozenSchema):
    """Define a versioned normalized-subject vocabulary through configuration."""

    unmatched_value: str | None = None
    values: tuple[str, ...] = Field(min_length=1)
    vocabulary_id: str = Field(min_length=1)
    vocabulary_version: SchemaVersion

    @model_validator(mode="after")
    def validate_vocabulary(self) -> Self:
        """Validate normalized-subject values and the optional unmatched value.

        Returns
        -------
        Self
            The validated subject vocabulary.

        Raises
        ------
        ValueError
            If values are duplicated or unmatched_value is not declared.
        """

        if any(not value.strip() for value in self.values):
            raise ValueError("Subject vocabulary values must be non-empty.")

        if len(self.values) != len(set(self.values)):
            raise ValueError("Subject vocabulary values must not contain duplicates.")

        if self.unmatched_value and self.unmatched_value not in self.values:
            raise ValueError(
                "unmatched_value must appear in subject vocabulary values."
            )

        return self
