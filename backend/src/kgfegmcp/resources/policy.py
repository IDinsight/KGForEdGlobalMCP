"""This module applies rights, exposure, MIME-type, and size policy to resources.

This module determines whether an accepted package permits a requested resource and
which limits and MIME type apply. It evaluates standard-resource, full-text, and
bulk-resource rights independently and maps approved manifest artifact names to closed
exposure classes.

Additional manifest artifacts remain representable but fail closed until an explicit
future contract defines their exposure class, MIME type, rights requirements, and size
policy. This module makes policy decisions only; it does not resolve packages, read
files, validate checksums, query graph stores, or register MCP resources.
"""

# Future Library
from __future__ import annotations

# Standard Library
from dataclasses import dataclass
from enum import StrEnum
from typing import Final

# Package Library
from kgfegmcp.domain.enums import RightsReviewStatus
from kgfegmcp.domain.models import RightsPolicy
from kgfegmcp.errors import ResourceAccessDeniedError, ResourceNotFoundError
from kgfegmcp.resources.models import ResourceKind


class ArtifactAccessClass(StrEnum):
    """Classify the rights needed to expose one built-in manifest artifact."""

    BULK_CONTENT = "bulk_content"
    FULL_TEXT = "full_text"
    PUBLIC_METADATA = "public_metadata"


@dataclass(frozen=True, slots=True)
class ArtifactPolicyDecision:
    """Describe the MIME type and rights class for one built-in artifact."""

    access_class: ArtifactAccessClass
    mime_type: str


_ARTIFACT_POLICIES: Final[dict[str, ArtifactPolicyDecision]] = {
    "academicStandardsBundle": ArtifactPolicyDecision(
        access_class=ArtifactAccessClass.BULK_CONTENT, mime_type="application/json"
    ),
    "entityProvenance": ArtifactPolicyDecision(
        access_class=ArtifactAccessClass.BULK_CONTENT, mime_type="application/json"
    ),
    "nodes": ArtifactPolicyDecision(
        access_class=ArtifactAccessClass.BULK_CONTENT, mime_type="application/x-ndjson"
    ),
    "relationships": ArtifactPolicyDecision(
        access_class=ArtifactAccessClass.BULK_CONTENT, mime_type="application/x-ndjson"
    ),
    "relationshipsHasChild": ArtifactPolicyDecision(
        access_class=ArtifactAccessClass.BULK_CONTENT, mime_type="application/x-ndjson"
    ),
    "standardsFramework": ArtifactPolicyDecision(
        access_class=ArtifactAccessClass.BULK_CONTENT, mime_type="application/json"
    ),
    "standardsFrameworkItems": ArtifactPolicyDecision(
        access_class=ArtifactAccessClass.BULK_CONTENT, mime_type="application/x-ndjson"
    ),
    "unresolvedItems": ArtifactPolicyDecision(
        access_class=ArtifactAccessClass.FULL_TEXT, mime_type="application/json"
    ),
    "validationReport": ArtifactPolicyDecision(
        access_class=ArtifactAccessClass.PUBLIC_METADATA, mime_type="application/json"
    ),
}
_APPROVED_REVIEW_STATUSES: Final[frozenset[RightsReviewStatus]] = frozenset(
    {RightsReviewStatus.APPROVED, RightsReviewStatus.PROVISIONAL_OPERATOR_APPROVED}
)


@dataclass(frozen=True, slots=True)
class ResourcePolicy:
    """Apply independent rights and deterministic resource-size checks."""

    max_resource_bytes: int
    max_resource_source_bytes: int

    def __post_init__(self) -> None:
        """Require positive returned-content and source-read limits.

        Raises
        ------
        ValueError
            If either configured limit is not positive or the source limit is smaller
            than the returned-content limit.
        """

        if self.max_resource_bytes < 1:
            raise ValueError("max_resource_bytes must be greater than zero.")

        if self.max_resource_source_bytes < self.max_resource_bytes:
            raise ValueError(
                "max_resource_source_bytes must be at least max_resource_bytes."
            )

    @staticmethod
    def _require_bulk(rights: RightsPolicy) -> None:
        """Require explicit bulk-resource permission.

        Parameters
        ----------
        rights
            Accepted source rights and operator exposure policy.
        """

        if not rights.allow_bulk_resource:
            raise ResourceAccessDeniedError(
                message="The selected package does not permit bulk resource access."
            )

    @staticmethod
    def _require_full_text(rights: RightsPolicy) -> None:
        """Require explicit full-text permission.

        Parameters
        ----------
        rights
            Accepted source rights and operator exposure policy.
        """

        if not rights.allow_full_text:
            raise ResourceAccessDeniedError(
                message=(
                    "The selected package does not permit full-text resource access."
                )
            )

    @staticmethod
    def _require_reviewed(rights: RightsPolicy) -> None:
        """Require an approved or provisionally operator-approved review status.

        Parameters
        ----------
        rights
            Accepted source rights and operator exposure policy.
        """

        if rights.review_status not in _APPROVED_REVIEW_STATUSES:
            raise ResourceAccessDeniedError(
                message="The selected package rights have not been approved for access."
            )

    @staticmethod
    def _require_standard(rights: RightsPolicy) -> None:
        """Require explicit single-standard resource permission.

        Parameters
        ----------
        rights
            Accepted source rights and operator exposure policy.
        """

        if not rights.allow_standard_resources:
            raise ResourceAccessDeniedError(
                message="The selected package does not permit standard resources."
            )

    def artifact_decision(
        self, *, logical_name: str, rights: RightsPolicy
    ) -> ArtifactPolicyDecision:
        """Return and enforce the closed policy for one manifest artifact.

        Parameters
        ----------
        logical_name
            Exact public logical name declared by the accepted manifest.
        rights
            Accepted source rights and operator exposure policy.

        Returns
        -------
        ArtifactPolicyDecision
            Approved MIME type and access class.

        Raises
        ------
        ResourceAccessDeniedError
            If rights deny the artifact's exposure class.
        ResourceNotFoundError
            If the logical name lacks an explicit PR 10 exposure contract.
        """

        decision = _ARTIFACT_POLICIES.get(logical_name)

        if decision is None:
            raise ResourceNotFoundError(
                details={"logical_name": logical_name},
                message=(
                    "The declared artifact does not have an approved resource "
                    "exposure contract."
                ),
            )

        if decision.access_class is ArtifactAccessClass.PUBLIC_METADATA:
            return decision

        self._require_reviewed(rights)

        if decision.access_class is ArtifactAccessClass.FULL_TEXT:
            self._require_full_text(rights)
            return decision

        self._require_bulk(rights)
        self._require_full_text(rights)
        self._require_standard(rights)
        return decision

    def require_resource_access(
        self, *, resource_kind: ResourceKind, rights: RightsPolicy
    ) -> None:
        """Enforce rights for one generated or dedicated resource family.

        Parameters
        ----------
        resource_kind
            Closed resource family being requested.
        rights
            Accepted source rights and operator exposure policy.

        Raises
        ------
        ResourceAccessDeniedError
            If package rights deny the requested resource family.
        ValueError
            If called for generic artifact access, which requires artifact_decision().
        """

        if resource_kind is ResourceKind.ARTIFACT:
            raise ValueError(
                "Generic artifact access must use artifact_decision with a logical name."
            )

        if resource_kind in {
            ResourceKind.CATALOG,
            ResourceKind.FRAMEWORK,
            ResourceKind.INTERPRETATION_PROFILE,
            ResourceKind.MANIFEST,
            ResourceKind.VALIDATION,
        }:
            return

        self._require_reviewed(rights)
        self._require_full_text(rights)

        if resource_kind in {
            ResourceKind.RELATIONSHIP,
            ResourceKind.STANDARD,
            ResourceKind.STANDARD_PROVENANCE,
        }:
            self._require_standard(rights)

    def require_return_size(self, size_bytes: int) -> None:
        """Require final returned content to fit the configured resource limit.

        Parameters
        ----------
        size_bytes
            The size of the resource being returned in bytes.
        """

        if size_bytes > self.max_resource_bytes:
            raise ResourceAccessDeniedError(
                details={
                    "actual_size_bytes": size_bytes,
                    "maximum_size_bytes": self.max_resource_bytes,
                },
                message="The requested resource exceeds the configured return limit.",
            )

    def require_source_size(self, size_bytes: int) -> None:
        """Require one source artifact to fit the configured read limit.

        Parameters
        ----------
        size_bytes
            The size of the source artifact in bytes.
        """

        if size_bytes > self.max_resource_source_bytes:
            raise ResourceAccessDeniedError(
                details={
                    "actual_size_bytes": size_bytes,
                    "maximum_size_bytes": self.max_resource_source_bytes,
                },
                message=(
                    "The requested source artifact exceeds the configured read limit."
                ),
            )
