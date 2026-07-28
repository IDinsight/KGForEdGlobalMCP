"""This module defines immutable request and result contracts for framework comparison.

This module contains the typed Pydantic contracts used by the ordinary comparison
service and its MCP adapter. The contracts describe bounded text, exact-code, and
code-prefix requests; canonical resolved request summaries; exact package-local
framework sections; retrieval-candidate matches; optional hierarchy context;
deterministic warnings; fixed disclosures; and the complete comparison result.

The models validate that framework, snapshot, graph-package, profile, node, rights,
source, cursor, context, and warning evidence remains internally consistent and within
the correct package boundary. They also enforce deterministic section and warning
ordering and distinguish deterministic retrieval evidence from later LLM-generated
interpretation.

This module defines data shapes and validation rules only. It does not resolve catalog
selections, execute searches, traverse graphs, authorize prompts, format MCP responses,
register tools or prompts, infer equivalence, persist mappings, mutate graph packages,
call a language model, or use MCP sampling.
"""

# Future Library
from __future__ import annotations

# Standard Library
from enum import StrEnum
from typing import Annotated, Literal, Self, TypeAlias

# Third Party Library
from pydantic import Field, model_validator

# Package Library
from kgfegmcp.catalog.models import CatalogSourceMetadata
from kgfegmcp.domain.enums import EpistemicStatus, GraphType
from kgfegmcp.domain.identifiers import (
    FrameworkId,
    GraphPackageId,
    NodeId,
    ProfileId,
    ProfileVersion,
    RelationshipId,
    Sha256Digest,
    SnapshotId,
)
from kgfegmcp.domain.models import RightsPolicy
from kgfegmcp.profiles.models import (
    CodeSearchPolicy,
    HierarchyPolicy,
    KnownSourceAnomaly,
    LanguagePolicy,
    SourceRoleCapabilities,
)
from kgfegmcp.schemas import FrozenSchema
from kgfegmcp.search.models import (
    CodeQueryText,
    SearchCursor,
    SearchHit,
    SearchMode,
    SearchQueryText,
    SearchWarning,
    TextMatch,
)
from kgfegmcp.services.models import (
    CatalogFilterValue,
    GetStandardContextResult,
    GetStandardResult,
)


class ComparisonWarningCode(StrEnum):
    """Identify one deterministic comparison-specific warning."""

    CODE_SEARCH_UNSUPPORTED = "code_search_unsupported"
    CONTEXT_INCOMPLETE = "context_incomplete"
    NO_MATCHES = "no_matches"
    UNRESOLVED_EVIDENCE_PRESENT = "unresolved_evidence_present"


class FrameworkComparisonRequestBase(FrozenSchema):
    """Define fields shared by deterministic cross-framework comparison requests."""

    framework_ids: tuple[FrameworkId, ...] = Field(max_length=8, min_length=2)
    include_context_paths: bool = True
    include_groupings: bool = False
    local_grade_labels: tuple[CatalogFilterValue, ...] = Field(
        default=(), max_length=64
    )
    max_matches_per_framework: int = Field(default=5, ge=1, le=10)
    normalized_grades: tuple[CatalogFilterValue, ...] = Field(default=(), max_length=64)
    snapshot_ids: tuple[SnapshotId, ...] = Field(default=(), max_length=8)

    @model_validator(mode="after")
    def validate_unique_values(self) -> Self:
        """Require every tuple selector and filter to contain unique exact values.

        Returns
        -------
        Self
            The unchanged validated comparison request.

        Raises
        ------
        ValueError
            If a framework, snapshot, or grade-filter value is repeated.
        """

        collections = (
            ("framework_ids", tuple(str(value) for value in self.framework_ids)),
            ("local_grade_labels", self.local_grade_labels),
            ("normalized_grades", self.normalized_grades),
            ("snapshot_ids", tuple(str(value) for value in self.snapshot_ids)),
        )

        for field_name, values in collections:
            if len(values) != len(set(values)):
                raise ValueError(f"{field_name} must not contain duplicate values.")

        return self


class TextFrameworkComparisonRequest(FrameworkComparisonRequestBase):
    """Request independently bounded lexical retrieval for selected frameworks."""

    match: TextMatch
    mode: Literal["text"]
    query: SearchQueryText


class ExactCodeFrameworkComparisonRequest(FrameworkComparisonRequestBase):
    """Request independently bounded exact-code retrieval for selected frameworks."""

    mode: Literal["code_exact"]
    query: CodeQueryText


class PrefixCodeFrameworkComparisonRequest(FrameworkComparisonRequestBase):
    """Request independently bounded code-prefix retrieval for selected frameworks."""

    mode: Literal["code_prefix"]
    query: CodeQueryText


FrameworkComparisonRequest: TypeAlias = Annotated[
    ExactCodeFrameworkComparisonRequest
    | PrefixCodeFrameworkComparisonRequest
    | TextFrameworkComparisonRequest,
    Field(discriminator="mode"),
]


class ComparisonRequestSummary(FrozenSchema):
    """Record the canonical resolved request used for every package-local search."""

    framework_ids: tuple[FrameworkId, ...] = Field(max_length=8, min_length=2)
    include_context_paths: bool
    include_groupings: bool
    local_grade_labels: tuple[CatalogFilterValue, ...]
    match: TextMatch | None = None
    max_matches_per_framework: int = Field(ge=1, le=10)
    mode: SearchMode
    normalized_grades: tuple[CatalogFilterValue, ...]
    query: str = Field(min_length=1)
    snapshot_ids: tuple[SnapshotId, ...] = Field(max_length=8, min_length=2)

    @model_validator(mode="after")
    def validate_summary(self) -> Self:
        """Require canonical identities and mode-appropriate text-match evidence.

        Returns
        -------
        Self
            The unchanged internally consistent request summary.

        Raises
        ------
        ValueError
            If identities repeat, counts disagree, or match evidence conflicts with mode.
        """

        framework_ids = tuple(str(value) for value in self.framework_ids)
        snapshot_ids = tuple(str(value) for value in self.snapshot_ids)

        if len(framework_ids) != len(set(framework_ids)):
            raise ValueError("Resolved framework IDs must remain unique.")

        if len(snapshot_ids) != len(set(snapshot_ids)):
            raise ValueError("Resolved snapshot IDs must remain unique.")

        if len(framework_ids) != len(snapshot_ids):
            raise ValueError("Resolved framework and snapshot counts must agree.")

        if (self.mode is SearchMode.TEXT) != (self.match is not None):
            raise ValueError("Text match evidence must be present only for text mode.")

        return self


class ComparisonWarning(FrozenSchema):
    """Describe one deterministic comparison warning with exact local identity."""

    code: ComparisonWarningCode
    framework_id: FrameworkId
    graph_package_id: GraphPackageId
    message: str = Field(min_length=1)
    node_id: NodeId | None = None
    relationship_id: RelationshipId | None = None
    snapshot_id: SnapshotId


class ComparisonMatchEvidence(FrozenSchema):
    """Return one exact retrieval candidate with optional bounded hierarchy context."""

    context: GetStandardContextResult | None = None
    context_complete: bool | None = None
    retrieval_status: Literal[  # type: ignore[valid-type]
        EpistemicStatus.RETRIEVAL_CANDIDATE
    ]
    search_hit: SearchHit
    standard: GetStandardResult

    @model_validator(mode="after")
    def validate_evidence_identity(self) -> Self:
        """Require search, standard, and optional context evidence to agree exactly.

        Returns
        -------
        Self
            The unchanged internally consistent match evidence.

        Raises
        ------
        ValueError
            If node, package, context, or completion evidence disagrees.
        """

        standard_identity = self.standard.package.package_identity

        if self.search_hit.node != self.standard.node:
            raise ValueError("Search and standard evidence must contain the same node.")

        if self.search_hit.package_identity != standard_identity:
            raise ValueError("Search and standard package identities must agree.")

        if self.context is None:
            if self.context_complete is not None:
                raise ValueError(
                    "context_complete must be absent when context was not requested."
                )
            return self

        if self.context.standard != self.standard:
            raise ValueError("Context and standard evidence must agree exactly.")

        expected_complete = self.context.ancestors.is_complete and (
            self.context.root_paths is None or self.context.root_paths.is_complete
        )

        if self.context_complete is not expected_complete:
            raise ValueError(
                "context_complete must match traversal completion evidence."
            )

        return self


class FrameworkComparisonSection(FrozenSchema):
    """Return one independently retrieved exact-package framework evidence section."""

    code_search_policy: CodeSearchPolicy
    comparison_dimensions: tuple[str, ...]
    framework_id: FrameworkId
    graph_package_id: GraphPackageId
    graph_type: GraphType
    has_more: bool
    hierarchy: HierarchyPolicy
    known_source_anomalies: tuple[KnownSourceAnomaly, ...]
    language_policy: LanguagePolicy
    local_grades_or_stages: tuple[str, ...]
    matches: tuple[ComparisonMatchEvidence, ...] = Field(max_length=10)
    next_cursor: SearchCursor | None
    normalized_grades: tuple[str, ...]
    package_search_warnings: tuple[SearchWarning, ...]
    profile_id: ProfileId
    profile_sha256: Sha256Digest
    profile_version: ProfileVersion
    required_profile_disclosures: tuple[str, ...]
    rights: RightsPolicy
    snapshot_id: SnapshotId
    source_metadata: CatalogSourceMetadata
    source_role_capabilities: SourceRoleCapabilities
    warnings: tuple[ComparisonWarning, ...]

    @model_validator(mode="after")
    def validate_section_identity(self) -> Self:
        """Require section identity, matches, cursors, and warnings to agree.

        Returns
        -------
        Self
            The unchanged internally consistent framework section.

        Raises
        ------
        ValueError
            If package-local evidence crosses a framework section boundary.
        """

        if self.has_more != (self.next_cursor is not None):
            raise ValueError("has_more and next_cursor must agree.")

        for match in self.matches:
            identity = match.search_hit.package_identity

            if (
                identity.framework_id != self.framework_id
                or identity.graph_package_id != self.graph_package_id
                or identity.graph_type is not self.graph_type
                or identity.profile_id != self.profile_id
                or identity.profile_sha256 != self.profile_sha256
                or identity.profile_version != self.profile_version
                or identity.snapshot_id != self.snapshot_id
            ):
                raise ValueError("Comparison matches must remain package-local.")

            if match.standard.package.rights != self.rights:
                raise ValueError(
                    "Comparison rights evidence must remain section-local."
                )

            if (
                match.standard.package.profile_facets.normalized_grades
                != self.normalized_grades
            ):
                raise ValueError(
                    "Comparison normalized-grade evidence must remain section-local."
                )

            if match.standard.source_metadata != self.source_metadata:
                raise ValueError(
                    "Comparison source metadata must remain section-local."
                )

        if self.local_grades_or_stages != self.source_metadata.local_grades_or_stages:
            raise ValueError(
                "Comparison local-grade evidence must match source metadata."
            )

        for warning in self.warnings:
            if (
                warning.framework_id != self.framework_id
                or warning.graph_package_id != self.graph_package_id
                or warning.snapshot_id != self.snapshot_id
            ):
                raise ValueError("Comparison warnings must remain section-local.")

        return self


class CompareFrameworkEvidenceResult(FrozenSchema):
    """Return deterministic evidence for an exploratory framework comparison."""

    disclosures: tuple[str, ...] = Field(min_length=1)
    epistemic_status: Literal[  # type: ignore[valid-type]
        EpistemicStatus.DETERMINISTIC_DERIVED
    ]
    request: ComparisonRequestSummary
    sections: tuple[FrameworkComparisonSection, ...] = Field(min_length=2)
    warnings: tuple[ComparisonWarning, ...]

    @model_validator(mode="after")
    def validate_result_order_and_warnings(self) -> Self:
        """Require canonical section order and exact warning aggregation.

        Returns
        -------
        Self
            The unchanged deterministic comparison result.

        Raises
        ------
        ValueError
            If sections are out of order or aggregate warnings differ.
        """

        section_keys = tuple(
            (
                str(section.framework_id),
                str(section.snapshot_id),
                str(section.graph_package_id),
            )
            for section in self.sections
        )

        if section_keys != tuple(sorted(section_keys)):
            raise ValueError("Comparison sections must use canonical identity order.")

        if tuple(section.framework_id for section in self.sections) != (
            self.request.framework_ids
        ):
            raise ValueError("Request and section framework identities must agree.")

        if tuple(section.snapshot_id for section in self.sections) != (
            self.request.snapshot_ids
        ):
            raise ValueError("Request and section snapshot identities must agree.")

        expected_warnings = tuple(
            sorted(
                (warning for section in self.sections for warning in section.warnings),
                key=lambda warning: (
                    warning.code.value,
                    str(warning.framework_id),
                    str(warning.snapshot_id),
                    str(warning.graph_package_id),
                    str(warning.node_id or ""),
                    str(warning.relationship_id or ""),
                    warning.message,
                ),
            )
        )

        if self.warnings != expected_warnings:
            raise ValueError(
                "Result warnings must aggregate section warnings in canonical order."
            )

        return self
