"""This module contains shared domain models independent of package transport and
FastMCP.
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
