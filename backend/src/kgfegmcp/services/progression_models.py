"""This module defines immutable contracts for deterministic progression-evidence
collection.

The models in this module describe one exact framework request, explicit local and
normalized grade scopes, deterministic candidate discovery and selection evidence,
bounded hierarchy context, scope coverage, warnings, and the complete result consumed
by the inferred-progression prompt workflow.

These contracts do not infer or persist learning progressions. Retained standards
remain retrieval candidates, while any relationship proposed later by a client-side
model must remain explicitly LLM-inferred.
"""

# Future Library
from __future__ import annotations

# Standard Library
from enum import StrEnum
from typing import Literal, Self

# Third Party Library
from pydantic import Field, model_validator

# Package Library
from kgfegmcp.catalog.models import CatalogGraphPackage, CatalogSourceMetadata
from kgfegmcp.domain.enums import EpistemicStatus, NormalizedStatementType
from kgfegmcp.domain.identifiers import (
    FrameworkId,
    GraphPackageId,
    NodeId,
    RelationshipId,
    SnapshotId,
)
from kgfegmcp.graph.models import (
    SourceExportOrder,
    StandardNode,
    TraversalTruncationReason,
)
from kgfegmcp.schemas import FrozenSchema
from kgfegmcp.search.models import SearchFacetEvidence, SearchHit, SearchWarning
from kgfegmcp.services.models import CatalogFilterValue, ContextRelationshipStatus


class ProgressionCandidateDiscoveryMethod(StrEnum):
    """Identify how one standard entered the deterministic discovery pool."""

    ANCHOR_TERM_SEARCH = "anchor_term_search"
    DIRECT_SEARCH_HIT = "direct_search_hit"
    EXACT_ANCHOR = "exact_anchor"
    GROUPING_DESCENDANT = "grouping_descendant"


class ProgressionCandidateSelectionPolicy(StrEnum):
    """Identify the deterministic retained-candidate allocation policy."""

    BALANCED_SCOPE_THEN_RANK = "balanced_scope_then_rank"


class ProgressionEvidenceFocusMode(StrEnum):
    """Identify how the progression evidence focus value must be interpreted."""

    CASE_IDENTIFIER_URI = "case_identifier_uri"
    CASE_IDENTIFIER_UUID = "case_identifier_uuid"
    NODE_ID = "node_id"
    STATEMENT_CODE = "statement_code"
    TOPIC = "topic"


class ProgressionEvidenceWarningCode(StrEnum):
    """Identify one deterministic progression-evidence warning."""

    CONTEXT_INCOMPLETE = "context_incomplete"
    DISCOVERY_INCOMPLETE = "discovery_incomplete"
    NO_CANDIDATES = "no_candidates"
    SCOPE_NOT_RETAINED = "scope_not_retained"
    SCOPE_WITHOUT_CANDIDATES = "scope_without_candidates"
    SEARCH_WARNING = "search_warning"


class ProgressionScopeKind(StrEnum):
    """Identify whether one scope value is local or normalized."""

    LOCAL_GRADE_LABEL = "local_grade_label"
    NORMALIZED_GRADE = "normalized_grade"


class CollectProgressionEvidenceRequest(FrozenSchema):
    """Request one bounded deterministic progression-evidence candidate set."""

    candidate_limit: int = Field(default=8, ge=2, le=20)
    focus_mode: ProgressionEvidenceFocusMode = ProgressionEvidenceFocusMode.TOPIC
    framework_id: FrameworkId
    local_grade_labels: tuple[CatalogFilterValue, ...] = Field(
        default=(), max_length=32
    )
    normalized_grades: tuple[CatalogFilterValue, ...] = Field(default=(), max_length=32)
    snapshot_id: SnapshotId | None = None
    topic_or_standard: str = Field(max_length=512, min_length=1)

    @model_validator(mode="after")
    def validate_scope(self) -> Self:
        """Require explicit, unique grade scopes and nonblank focus text.

        Returns
        -------
        Self
            The unchanged validated request.

        Raises
        ------
        ValueError
            If both scope arrays are empty, a scope value repeats, or the focus value
            contains only whitespace.
        """

        if not self.local_grade_labels and not self.normalized_grades:
            raise ValueError(
                "At least one local_grade_label or normalized_grade is required."
            )

        collections = (
            ("local_grade_labels", self.local_grade_labels),
            ("normalized_grades", self.normalized_grades),
        )

        for field_name, values in collections:
            if len(values) != len(set(values)):
                raise ValueError(f"{field_name} must not contain duplicate values.")

            if any(not value.strip() for value in values):
                raise ValueError(f"{field_name} must not contain blank values.")

        if not self.topic_or_standard.strip():
            raise ValueError("topic_or_standard must contain non-whitespace text.")

        return self


class ProgressionEvidenceRequestSummary(FrozenSchema):
    """Record the exact resolved package and filters used for evidence collection."""

    candidate_limit: int = Field(ge=2, le=20)
    focus_mode: ProgressionEvidenceFocusMode
    framework_id: FrameworkId
    graph_package_id: GraphPackageId
    local_grade_labels: tuple[CatalogFilterValue, ...]
    normalized_grades: tuple[CatalogFilterValue, ...]
    snapshot_id: SnapshotId
    topic_or_standard: str = Field(min_length=1)


class ProgressionScopeCoverage(FrozenSchema):
    """Describe discovered and retained evidence for one requested grade scope."""

    discovered_candidate_count: int = Field(ge=0)
    retained_candidate_count: int = Field(ge=0)
    scope_kind: ProgressionScopeKind
    scope_value: str = Field(min_length=1)

    @model_validator(mode="after")
    def validate_counts(self) -> Self:
        """Require retained evidence not to exceed discovered evidence.

        Returns
        -------
        Self
            The unchanged internally consistent scope coverage.

        Raises
        ------
        ValueError
            If the retained count exceeds the discovered count.
        """

        if self.retained_candidate_count > self.discovered_candidate_count:
            raise ValueError(
                "retained_candidate_count may not exceed discovered_candidate_count."
            )

        return self


class ProgressionEvidenceWarning(FrozenSchema):
    """Describe one deterministic warning produced during evidence collection."""

    code: ProgressionEvidenceWarningCode
    message: str = Field(min_length=1)
    node_id: NodeId | None = None
    search_warning: SearchWarning | None = None


class ProgressionContextNodeKind(StrEnum):
    """Identify the graph-node kind retained in compact hierarchy evidence."""

    FRAMEWORK = "framework"
    STANDARD = "standard"


class ProgressionContextNodeEvidence(FrozenSchema):
    """Describe one exact hierarchy node without repeating raw source properties."""

    label: str | None = None
    node_id: NodeId
    node_kind: ProgressionContextNodeKind
    normalized_statement_type: NormalizedStatementType | None = None
    source_export_order: SourceExportOrder
    statement_code: str | None = None
    statement_type: str | None = None


class ProgressionContextRelationshipEvidence(FrozenSchema):
    """Describe one exact hierarchy relationship in compact endpoint form."""

    label: str = Field(min_length=1)
    relationship_id: RelationshipId
    resolution_status: str | None = None
    source_export_order: SourceExportOrder
    source_node_id: NodeId
    target_node_id: NodeId


class ProgressionRootPathEvidence(FrozenSchema):
    """Describe one compact complete framework-root-to-candidate hierarchy path."""

    nodes: tuple[ProgressionContextNodeEvidence, ...] = Field(min_length=1)
    relationships: tuple[ProgressionContextRelationshipEvidence, ...]

    @model_validator(mode="after")
    def validate_path(self) -> Self:
        """Require compact relationships to connect consecutive unique path nodes.

        Returns
        -------
        Self
            The unchanged internally consistent path evidence.

        Raises
        ------
        ValueError
            If nodes repeat or relationships do not connect consecutive nodes.
        """

        if len(self.relationships) != len(self.nodes) - 1:
            raise ValueError(
                "A compact root path must contain one fewer relationship than nodes."
            )

        node_ids = tuple(node.node_id for node in self.nodes)

        if len(node_ids) != len(set(node_ids)):
            raise ValueError("A compact root path may not repeat a node.")

        if self.nodes[0].node_kind is not ProgressionContextNodeKind.FRAMEWORK:
            raise ValueError("A compact root path must begin with a framework node.")

        if self.nodes[-1].node_kind is not ProgressionContextNodeKind.STANDARD:
            raise ValueError("A compact root path must end with a standard node.")

        for index, relationship in enumerate(self.relationships):
            if relationship.source_node_id != self.nodes[index].node_id:
                raise ValueError(
                    "A compact root-path source must match its preceding node."
                )

            if relationship.target_node_id != self.nodes[index + 1].node_id:
                raise ValueError(
                    "A compact root-path target must match its following node."
                )

        return self


class ProgressionCandidateContextEvidence(FrozenSchema):
    """Return compact bounded hierarchy evidence for one retained candidate."""

    ancestor_traversal_complete: bool
    ancestor_truncation_reason: TraversalTruncationReason | None = None
    framework_root_id: NodeId
    is_complete: bool
    origin_node_id: NodeId
    relationship_statuses: tuple[ContextRelationshipStatus, ...]
    relationship_type: str = Field(min_length=1)
    root_paths: tuple[ProgressionRootPathEvidence, ...]
    root_paths_complete: bool
    root_paths_truncation_reason: TraversalTruncationReason | None = None

    @model_validator(mode="after")
    def validate_completion(self) -> Self:
        """Require aggregate completion and truncation evidence to agree.

        Returns
        -------
        Self
            The unchanged internally consistent context evidence.

        Raises
        ------
        ValueError
            If completion flags, truncation reasons, or root paths conflict.
        """

        self._check_aggregate_completion()
        self._check_truncation_reasons()
        self._check_root_path_bounds()

        return self

    def _check_aggregate_completion(self) -> None:
        """Require the aggregate completion flag to match its component flags.

        Raises
        ------
        ValueError
            If ``is_complete`` disagrees with the ancestor and root-path flags.
        """

        expected_complete = (
            self.ancestor_traversal_complete and self.root_paths_complete
        )

        if self.is_complete is not expected_complete:
            raise ValueError(
                "is_complete must match ancestor and root-path completion evidence."
            )

    def _check_root_path_bounds(self) -> None:
        """Require every root path to span framework_root_id to origin_node_id.

        Raises
        ------
        ValueError
            If a path starts or ends at the wrong node, or uses an unexpected
            relationship type.
        """

        for path in self.root_paths:
            if path.nodes[0].node_id != self.framework_root_id:
                raise ValueError(
                    "Every compact root path must begin at framework_root_id."
                )

            if path.nodes[-1].node_id != self.origin_node_id:
                raise ValueError("Every compact root path must end at origin_node_id.")

            if any(
                relationship.label != self.relationship_type
                for relationship in path.relationships
            ):
                raise ValueError(
                    "Compact root paths must use the selected relationship type."
                )

    def _check_truncation_reasons(self) -> None:
        """Require each completion flag to match its recorded truncation reason.

        Raises
        ------
        ValueError
            If a complete traversal records a reason, or an incomplete one omits
            it.
        """

        self._require_truncation_consistency(
            complete_message=(
                "A complete ancestor traversal may not have a truncation reason."
            ),
            incomplete_message=(
                "An incomplete ancestor traversal must have a truncation reason."
            ),
            is_complete=self.ancestor_traversal_complete,
            truncation_reason=self.ancestor_truncation_reason,
        )
        self._require_truncation_consistency(
            complete_message="Complete root paths may not have a truncation reason.",
            incomplete_message="Incomplete root paths must have a truncation reason.",
            is_complete=self.root_paths_complete,
            truncation_reason=self.root_paths_truncation_reason,
        )

    @staticmethod
    def _require_truncation_consistency(
        *,
        complete_message: str,
        incomplete_message: str,
        is_complete: bool,
        truncation_reason: TraversalTruncationReason | None,
    ) -> None:
        """Require one completion flag to match its recorded truncation reason.

        Parameters
        ----------
        complete_message
            Error text raised when a completed traversal records a reason.
        incomplete_message
            Error text raised when an incomplete traversal omits a reason.
        is_complete
            Whether the traversal the flag describes ran to completion.
        truncation_reason
            The recorded truncation reason, or ``None`` when the traversal
            completed.

        Raises
        ------
        ValueError
            If a complete traversal records a reason, or an incomplete one omits it.
        """

        if is_complete:
            if truncation_reason is not None:
                raise ValueError(complete_message)
        elif truncation_reason is None:
            raise ValueError(incomplete_message)


class ProgressionCandidateEvidence(FrozenSchema):
    """Return one retained standard with exact source and hierarchy evidence."""

    context: ProgressionCandidateContextEvidence
    discovery_methods: tuple[ProgressionCandidateDiscoveryMethod, ...] = Field(
        min_length=1
    )
    facets: SearchFacetEvidence
    matched_local_grade_labels: tuple[str, ...]
    matched_normalized_grades: tuple[str, ...]
    node: StandardNode
    retrieval_status: Literal[  # type: ignore[valid-type]
        EpistemicStatus.RETRIEVAL_CANDIDATE
    ]
    search_hit: SearchHit | None = None
    selection_rank: int = Field(ge=1)

    @model_validator(mode="after")
    def validate_evidence(self) -> Self:
        """Require candidate node, facets, methods, and search evidence to agree.

        Returns
        -------
        Self
            The unchanged internally consistent candidate evidence.

        Raises
        ------
        ValueError
            If methods repeat or direct search evidence identifies another node.
        """

        if len(self.discovery_methods) != len(set(self.discovery_methods)):
            raise ValueError("discovery_methods must not contain duplicate values.")

        if self.search_hit is not None and self.search_hit.node != self.node:
            raise ValueError("Search-hit and candidate nodes must agree.")

        if self.context.origin_node_id != self.node.node_id:
            raise ValueError("Candidate node and compact context origin must agree.")

        return self


class CollectProgressionEvidenceResult(FrozenSchema):
    """Return one deterministically bounded progression-evidence candidate set."""

    candidate_limit_applied: bool
    discovered_candidate_count: int = Field(ge=0)
    discovery_complete: bool
    excluded_candidate_count: int = Field(ge=0)
    excluded_candidate_node_ids: tuple[NodeId, ...]
    package: CatalogGraphPackage
    request: ProgressionEvidenceRequestSummary
    retained_candidate_count: int = Field(ge=0)
    retained_candidates: tuple[ProgressionCandidateEvidence, ...] = Field(max_length=20)
    scope_coverage: tuple[ProgressionScopeCoverage, ...] = Field(min_length=1)
    selection_policy: ProgressionCandidateSelectionPolicy
    source_metadata: CatalogSourceMetadata
    warnings: tuple[ProgressionEvidenceWarning, ...]

    @model_validator(mode="after")
    def validate_result(self) -> Self:
        """Require candidate counts, identities, ranks, and limit evidence to agree.

        Returns
        -------
        Self
            The unchanged internally consistent progression evidence result.

        Raises
        ------
        ValueError
            If counts, identities, ranks, exclusions, or limit status disagree.
        """

        self._check_package_identity()
        self._check_candidate_counts()
        self._check_candidate_node_ids()
        self._check_candidate_scopes()
        self._check_scope_coverage()
        self._check_selection_ranks()

        return self

    def _check_package_identity(self) -> None:
        """Require the request identities to match the resolved package identity.

        Raises
        ------
        ValueError
            If the graph package, framework, or snapshot identities disagree.
        """

        identity = self.package.package_identity

        if self.request.graph_package_id != identity.graph_package_id:
            raise ValueError("Request and package graph identities must agree.")

        if self.request.framework_id != identity.framework_id:
            raise ValueError("Request and package framework identities must agree.")

        if self.request.snapshot_id != identity.snapshot_id:
            raise ValueError("Request and package snapshot identities must agree.")

    def _check_candidate_counts(self) -> None:
        """Require the recorded candidate counts and limit flag to be consistent.

        Raises
        ------
        ValueError
            If any count disagrees with its collection, the totals fail to add up, the
            retained count exceeds the limit, or the limit flag is wrong.
        """

        if self.retained_candidate_count != len(self.retained_candidates):
            raise ValueError(
                "retained_candidate_count must equal retained_candidates length."
            )

        if self.excluded_candidate_count != len(self.excluded_candidate_node_ids):
            raise ValueError(
                "excluded_candidate_count must equal excluded_candidate_node_ids length."
            )

        if self.discovered_candidate_count != (
            self.retained_candidate_count + self.excluded_candidate_count
        ):
            raise ValueError(
                "discovered_candidate_count must equal retained plus excluded counts."
            )

        if self.retained_candidate_count > self.request.candidate_limit:
            raise ValueError("Retained candidates may not exceed candidate_limit.")

        expected_limit_applied = (
            self.discovered_candidate_count > self.request.candidate_limit
        )

        if self.candidate_limit_applied is not expected_limit_applied:
            raise ValueError(
                "candidate_limit_applied must reflect whether candidates were excluded."
            )

    def _check_candidate_node_ids(self) -> None:
        """Require retained and excluded candidate node IDs to be unique and disjoint.

        Raises
        ------
        ValueError
            If retained IDs repeat, excluded IDs repeat, or the two sets overlap.
        """

        retained_node_ids = tuple(
            candidate.node.node_id for candidate in self.retained_candidates
        )

        if len(retained_node_ids) != len(set(retained_node_ids)):
            raise ValueError("Retained candidate node IDs must be unique.")

        if set(retained_node_ids).intersection(self.excluded_candidate_node_ids):
            raise ValueError(
                "Retained and excluded candidate node IDs must be disjoint."
            )

        if len(self.excluded_candidate_node_ids) != len(
            set(self.excluded_candidate_node_ids)
        ):
            raise ValueError("Excluded candidate node IDs must be unique.")

    def _check_candidate_scopes(self) -> None:
        """Require every retained candidate to match the resolved request scopes.

        Raises
        ------
        ValueError
            If any retained candidate's search-hit identity or matched grades disagree
            with the resolved request.
        """

        requested_local = set(self.request.local_grade_labels)
        requested_normalized = set(self.request.normalized_grades)

        for candidate in self.retained_candidates:
            self._check_candidate_scope(
                candidate=candidate,
                requested_local=requested_local,
                requested_normalized=requested_normalized,
            )

    def _check_candidate_scope(
        self,
        *,
        candidate: ProgressionCandidateEvidence,
        requested_local: set[str],
        requested_normalized: set[str],
    ) -> None:
        """Require one retained candidate to match the resolved request scopes.

        Parameters
        ----------
        candidate
            The retained candidate whose search-hit identity and matched grades
            are validated against the resolved request.
        requested_local
            The local grade labels the resolved request scopes to.
        requested_normalized
            The normalized grades the resolved request scopes to.

        Raises
        ------
        ValueError
            If the candidate's search-hit identity disagrees, a matched grade falls
            outside the request, or a populated scope is left unmatched.
        """

        identity = self.package.package_identity

        if (
            candidate.search_hit is not None
            and candidate.search_hit.package_identity != identity
        ):
            raise ValueError(
                "Candidate search-hit and result package identities must agree."
            )

        matched_local = set(candidate.matched_local_grade_labels)
        matched_normalized = set(candidate.matched_normalized_grades)

        if not matched_local.issubset(requested_local):
            raise ValueError(
                "Matched local grades must be drawn from the resolved request."
            )

        if not matched_normalized.issubset(requested_normalized):
            raise ValueError(
                "Matched normalized grades must be drawn from the resolved request."
            )

        if requested_local and not matched_local:
            raise ValueError(
                "Every retained candidate must match the populated local scope."
            )

        if requested_normalized and not matched_normalized:
            raise ValueError(
                "Every retained candidate must match the populated normalized scope."
            )

    def _check_scope_coverage(self) -> None:
        """Require scope coverage to list the resolved request scopes in order.

        Raises
        ------
        ValueError
            If the scope coverage entries differ from the resolved request
            scopes or appear in a different order.
        """

        expected_scope = tuple(
            (ProgressionScopeKind.LOCAL_GRADE_LABEL, value)
            for value in self.request.local_grade_labels
        ) + tuple(
            (ProgressionScopeKind.NORMALIZED_GRADE, value)
            for value in self.request.normalized_grades
        )
        actual_scope = tuple(
            (coverage.scope_kind, coverage.scope_value)
            for coverage in self.scope_coverage
        )

        if actual_scope != expected_scope:
            raise ValueError(
                "scope_coverage must match resolved request scopes in canonical order."
            )

    def _check_selection_ranks(self) -> None:
        """Require retained candidate ranks to be contiguous starting from one.

        Raises
        ------
        ValueError
            If the retained candidate ranks are not the contiguous sequence from one to
            ``retained_candidate_count``.
        """

        expected_ranks = tuple(range(1, self.retained_candidate_count + 1))
        actual_ranks = tuple(
            candidate.selection_rank for candidate in self.retained_candidates
        )

        if actual_ranks != expected_ranks:
            raise ValueError("Retained candidate ranks must be contiguous from one.")
