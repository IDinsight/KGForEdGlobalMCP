"""This module collects deterministic bounded evidence for inferred-progression
workflows.

``ProgressionEvidenceService`` resolves one exact Academic Standards package, validates
explicit local and normalized grade scopes, discovers related standard-item candidates,
expands matching grouping nodes, deduplicates candidates by exact node identity,
applies a deterministic grade-balanced quota, and retrieves complete source and
hierarchy evidence for every retained candidate.

The service does not infer, score, or persist progression relationships. Its retained
standards remain retrieval candidates for a later client-side LLM hypothesis.
"""

# Future Library
from __future__ import annotations

# Standard Library
from dataclasses import dataclass, field
from typing import Final

# Package Library
from kgfegmcp.catalog.models import CatalogFrameworkSnapshot, CatalogGraphPackage
from kgfegmcp.catalog.service import CatalogService
from kgfegmcp.domain.enums import EpistemicStatus, GraphType, NormalizedStatementType
from kgfegmcp.domain.identifiers import NodeId
from kgfegmcp.errors import CapabilityUnavailableError
from kgfegmcp.graph.models import (
    FrameworkNode,
    GraphNodeRecord,
    GraphRelationship,
    RootPath,
    StandardNode,
)
from kgfegmcp.search.models import (
    SearchFacetEvidence,
    SearchHit,
    SearchWarning,
    TextMatchMode,
    TextOperator,
    TokenTextMatch,
)
from kgfegmcp.search.normalizers import normalize_lexical_text
from kgfegmcp.services.models import (
    CaseUriStandardIdentifier,
    CaseUuidStandardIdentifier,
    ExactCodeStandardsSearchRequest,
    GetStandardContextRequest,
    GetStandardRequest,
    NodeIdStandardIdentifier,
    TextStandardsSearchRequest,
)
from kgfegmcp.services.progression_models import (
    CollectProgressionEvidenceRequest,
    CollectProgressionEvidenceResult,
    ProgressionCandidateContextEvidence,
    ProgressionCandidateDiscoveryMethod,
    ProgressionCandidateEvidence,
    ProgressionCandidateSelectionPolicy,
    ProgressionContextNodeEvidence,
    ProgressionContextNodeKind,
    ProgressionContextRelationshipEvidence,
    ProgressionEvidenceFocusMode,
    ProgressionEvidenceRequestSummary,
    ProgressionEvidenceWarning,
    ProgressionEvidenceWarningCode,
    ProgressionRootPathEvidence,
    ProgressionScopeCoverage,
    ProgressionScopeKind,
)
from kgfegmcp.services.standards import StandardsService

_CONTEXT_ANCESTOR_DEPTH: Final[int] = 16
_CONTEXT_MAX_NODES: Final[int] = 250
_CONTEXT_MAX_PATH_NODE_OCCURRENCES: Final[int] = 2_048
_CONTEXT_MAX_PATHS: Final[int] = 32
_DISCOVERY_LIMIT: Final[int] = 100
_GROUPING_DESCENDANT_DEPTH: Final[int] = 16
_GROUPING_DESCENDANT_NODE_LIMIT: Final[int] = 2_000
_METHOD_PRIORITY: Final[dict[ProgressionCandidateDiscoveryMethod, int]] = {
    ProgressionCandidateDiscoveryMethod.EXACT_ANCHOR: 0,
    ProgressionCandidateDiscoveryMethod.GROUPING_DESCENDANT: 1,
    ProgressionCandidateDiscoveryMethod.DIRECT_SEARCH_HIT: 2,
    ProgressionCandidateDiscoveryMethod.ANCHOR_TERM_SEARCH: 3,
}


@dataclass(slots=True)
class _CandidateRecord:
    """Accumulate one deduplicated standard candidate before final selection."""

    discovery_methods: set[ProgressionCandidateDiscoveryMethod]
    facets: SearchFacetEvidence
    node: StandardNode
    ranking_position: tuple[int, int, int, str]
    search_hit: SearchHit | None = None


@dataclass(slots=True)
class _DiscoveryState:
    """Accumulate one bounded deterministic candidate-discovery operation."""

    candidates: dict[NodeId, _CandidateRecord] = field(default_factory=dict)
    discovery_complete: bool = True
    warnings: list[ProgressionEvidenceWarning] = field(default_factory=list)


@dataclass(frozen=True, slots=True)
class ProgressionEvidenceService:
    """Collect exact, bounded standards evidence without inferring progression."""

    catalog_service: CatalogService
    standards_service: StandardsService

    def __post_init__(self) -> None:
        """Require the retained services to share one accepted catalog runtime.

        Raises
        ------
        ValueError
            If the supplied services were constructed over different catalogs.
        """

        if self.standards_service.catalog_service is not self.catalog_service:
            raise ValueError(
                "ProgressionEvidenceService and StandardsService must share "
                "CatalogService."
            )

    def collect_progression_evidence(
        self, request: CollectProgressionEvidenceRequest
    ) -> CollectProgressionEvidenceResult:
        """Return one deterministically limited multi-grade standards evidence set.

        Parameters
        ----------
        request
            Exact framework route, explicit grade scopes, focus interpretation, and
            retained-candidate limit.

        Returns
        -------
        CollectProgressionEvidenceResult
            Resolved request, discovery counts, bounded retained candidates, complete
            source and hierarchy evidence, scope coverage, exclusions, and warnings.

        Raises
        ------
        CapabilityUnavailableError
            If a requested grade scope is unavailable in the selected package.
        """

        snapshot = self.standards_service.framework_service.resolve_snapshot_selection(
            framework_id=request.framework_id, snapshot_id=request.snapshot_id
        )
        package = self.catalog_service.get_graph_package(
            framework_id=snapshot.framework_id,
            graph_type=GraphType.ACADEMIC_STANDARDS,
            snapshot_id=snapshot.snapshot_id,
        )
        self._validate_grade_scope(
            local_grade_labels=request.local_grade_labels,
            normalized_grades=request.normalized_grades,
            package=package,
            snapshot=snapshot,
        )
        request = self._canonicalize_request_scope(
            package=package, request=request, snapshot=snapshot
        )
        discovery = self._discover_candidates(
            package=package, request=request, snapshot=snapshot
        )
        ranked_candidates = tuple(
            sorted(
                discovery.candidates.values(),
                key=lambda candidate: candidate.ranking_position,
            )
        )
        retained_records = self._select_candidates(
            candidate_limit=request.candidate_limit,
            local_grade_labels=request.local_grade_labels,
            normalized_grades=request.normalized_grades,
            ranked_candidates=ranked_candidates,
        )
        retained_node_ids = {candidate.node.node_id for candidate in retained_records}
        excluded_records = tuple(
            candidate
            for candidate in ranked_candidates
            if candidate.node.node_id not in retained_node_ids
        )
        retained_candidates = tuple(
            self._build_candidate_evidence(
                candidate=candidate,
                package=package,
                request=request,
                selection_rank=selection_rank,
                snapshot=snapshot,
                warnings=discovery.warnings,
            )
            for selection_rank, candidate in enumerate(retained_records, start=1)
        )

        if not ranked_candidates:
            discovery.warnings.append(
                ProgressionEvidenceWarning(
                    code=ProgressionEvidenceWarningCode.NO_CANDIDATES,
                    message=(
                        "No eligible standard-item candidates matched the exact focus "
                        "and grade scope."
                    ),
                )
            )

        scope_coverage = self._scope_coverage(
            local_grade_labels=request.local_grade_labels,
            normalized_grades=request.normalized_grades,
            ranked_candidates=ranked_candidates,
            retained_candidates=retained_records,
        )
        self._record_scope_coverage_warnings(
            scope_coverage=scope_coverage, warnings=discovery.warnings
        )
        request_summary = ProgressionEvidenceRequestSummary(
            candidate_limit=request.candidate_limit,
            focus_mode=request.focus_mode,
            framework_id=snapshot.framework_id,
            graph_package_id=package.package_identity.graph_package_id,
            local_grade_labels=request.local_grade_labels,
            normalized_grades=request.normalized_grades,
            snapshot_id=snapshot.snapshot_id,
            topic_or_standard=request.topic_or_standard,
        )
        return CollectProgressionEvidenceResult(
            candidate_limit_applied=(len(ranked_candidates) > request.candidate_limit),
            discovered_candidate_count=len(ranked_candidates),
            discovery_complete=discovery.discovery_complete,
            excluded_candidate_count=len(excluded_records),
            excluded_candidate_node_ids=tuple(
                candidate.node.node_id for candidate in excluded_records
            ),
            package=package,
            request=request_summary,
            retained_candidate_count=len(retained_candidates),
            retained_candidates=retained_candidates,
            scope_coverage=scope_coverage,
            selection_policy=(
                ProgressionCandidateSelectionPolicy.BALANCED_SCOPE_THEN_RANK
            ),
            source_metadata=snapshot.source_metadata,
            warnings=tuple(discovery.warnings),
        )

    @staticmethod
    def _add_candidate(
        *,
        discovery_index: int,
        discovery_method: ProgressionCandidateDiscoveryMethod,
        facets: SearchFacetEvidence,
        node: StandardNode,
        search_hit: SearchHit | None,
        state: _DiscoveryState,
    ) -> None:
        """Add or merge one exact standard candidate in the discovery pool.

        Parameters
        ----------
        discovery_index
            Stable zero-based position of the originating search or traversal record.
        discovery_method
            Deterministic route through which the candidate was discovered.
        facets
            Package-local source and normalized grade evidence.
        node
            Exact Academic Standards item node.
        search_hit
            Optional direct lexical or code-search evidence for the same node.
        state
            Mutable discovery accumulator owned by the current service call.
        """

        if node.normalized_statement_type is not NormalizedStatementType.STANDARD:
            return

        ranking_position = (
            _METHOD_PRIORITY[discovery_method],
            discovery_index,
            node.source_export_order,
            str(node.node_id),
        )
        existing = state.candidates.get(node.node_id)

        if existing is None:
            state.candidates[node.node_id] = _CandidateRecord(
                discovery_methods={discovery_method},
                facets=facets,
                node=node,
                ranking_position=ranking_position,
                search_hit=search_hit,
            )
            return

        existing.discovery_methods.add(discovery_method)
        existing.ranking_position = min(existing.ranking_position, ranking_position)

        if existing.search_hit is None and search_hit is not None:
            existing.search_hit = search_hit

    def _anchor_search_query(
        self,
        *,
        node: StandardNode,
        package: CatalogGraphPackage,
        snapshot: CatalogFrameworkSnapshot,
    ) -> str | None:
        """Derive one deterministic lexical query from the nearest grouping label.

        Parameters
        ----------
        node
            Exact identifier- or code-resolved anchor node.
        package
            Exact accepted Academic Standards package.
        snapshot
            Exact selected framework snapshot.

        Returns
        -------
        str | None
            Bounded nonnumeric grouping terms, or anchor terms when no grouping label
            is available.
        """

        context = self.standards_service.get_standard_context(
            GetStandardContextRequest(
                ancestor_depth=_CONTEXT_ANCESTOR_DEPTH,
                child_depth=0,
                framework_id=snapshot.framework_id,
                graph_type=package.package_identity.graph_type,
                include_all_root_paths=False,
                include_descendants=False,
                include_direct_children=False,
                include_unresolved=True,
                max_nodes=_CONTEXT_MAX_NODES,
                max_path_node_occurrences=1,
                max_paths=1,
                node_id=node.node_id,
                relationship_types=(),
                snapshot_id=snapshot.snapshot_id,
            )
        )
        grouping_descriptions = tuple(
            traversal_node.node.description
            for traversal_node in context.ancestors.nodes
            if traversal_node.depth > 0
            and isinstance(traversal_node.node, StandardNode)
            and traversal_node.node.normalized_statement_type
            is NormalizedStatementType.STANDARD_GROUPING
            and traversal_node.node.description
        )
        if (
            node.normalized_statement_type is NormalizedStatementType.STANDARD_GROUPING
            and node.description
        ):
            source_text = node.description
        elif grouping_descriptions:
            source_text = grouping_descriptions[0]
        else:
            source_text = node.description or ""
        tokens = tuple(
            token
            for token in dict.fromkeys(normalize_lexical_text(source_text))
            if not token.isdecimal()
        )
        return " ".join(tokens[:8]) or None

    def _build_candidate_evidence(
        self,
        *,
        candidate: _CandidateRecord,
        package: CatalogGraphPackage,
        request: CollectProgressionEvidenceRequest,
        selection_rank: int,
        snapshot: CatalogFrameworkSnapshot,
        warnings: list[ProgressionEvidenceWarning],
    ) -> ProgressionCandidateEvidence:
        """Retrieve exact source and hierarchy evidence for one retained candidate.

        Parameters
        ----------
        candidate
            Selected deduplicated candidate record.
        package
            Exact accepted Academic Standards package.
        request
            Validated progression evidence request.
        selection_rank
            One-based deterministic rank in the retained set.
        snapshot
            Exact selected framework snapshot.
        warnings
            Mutable result-warning accumulator.

        Returns
        -------
        ProgressionCandidateEvidence
            Exact standard, complete bounded context, discovery methods, scope matches,
            and optional direct search evidence.
        """

        standard = self.standards_service.get_standard(
            GetStandardRequest(
                framework_id=snapshot.framework_id,
                graph_type=package.package_identity.graph_type,
                identifier=NodeIdStandardIdentifier(
                    identifier_type="node_id", node_id=candidate.node.node_id
                ),
                snapshot_id=snapshot.snapshot_id,
            )
        )
        context = self.standards_service.get_standard_context(
            GetStandardContextRequest(
                ancestor_depth=_CONTEXT_ANCESTOR_DEPTH,
                child_depth=0,
                framework_id=snapshot.framework_id,
                graph_type=package.package_identity.graph_type,
                include_all_root_paths=True,
                include_descendants=False,
                include_direct_children=False,
                include_unresolved=True,
                max_nodes=_CONTEXT_MAX_NODES,
                max_path_node_occurrences=_CONTEXT_MAX_PATH_NODE_OCCURRENCES,
                max_paths=_CONTEXT_MAX_PATHS,
                node_id=candidate.node.node_id,
                relationship_types=(),
                snapshot_id=snapshot.snapshot_id,
            )
        )
        root_paths = context.root_paths

        if root_paths is None:
            raise RuntimeError(
                "Requested progression context did not return root-path evidence."
            )

        context_complete = context.ancestors.is_complete and root_paths.is_complete

        if not context_complete:
            warnings.append(
                ProgressionEvidenceWarning(
                    code=ProgressionEvidenceWarningCode.CONTEXT_INCOMPLETE,
                    message=(
                        "A retained candidate has incomplete bounded hierarchy context."
                    ),
                    node_id=candidate.node.node_id,
                )
            )

        return ProgressionCandidateEvidence(
            context=ProgressionCandidateContextEvidence(
                ancestor_traversal_complete=context.ancestors.is_complete,
                ancestor_truncation_reason=context.ancestors.truncation_reason,
                framework_root_id=root_paths.framework_root_id,
                is_complete=context_complete,
                origin_node_id=root_paths.origin_node_id,
                relationship_statuses=context.relationship_statuses,
                relationship_type=root_paths.relationship_type,
                root_paths=tuple(
                    self._compact_root_path(path=path) for path in root_paths.paths
                ),
                root_paths_complete=root_paths.is_complete,
                root_paths_truncation_reason=root_paths.truncation_reason,
            ),
            discovery_methods=tuple(
                sorted(
                    candidate.discovery_methods,
                    key=lambda method: (_METHOD_PRIORITY[method], method.value),
                )
            ),
            facets=standard.facets,
            matched_local_grade_labels=tuple(
                value
                for value in request.local_grade_labels
                if value in candidate.facets.resolved_local_grade_labels
            ),
            matched_normalized_grades=tuple(
                value
                for value in request.normalized_grades
                if value in candidate.facets.normalized_grades
            ),
            node=standard.node,
            retrieval_status=EpistemicStatus.RETRIEVAL_CANDIDATE,
            search_hit=candidate.search_hit,
            selection_rank=selection_rank,
        )

    @staticmethod
    def _compact_context_node(node: GraphNodeRecord) -> ProgressionContextNodeEvidence:
        """Return one compact exact node reference for hierarchy evidence.

        Parameters
        ----------
        node
            Exact framework or standard node from a validated root path.

        Returns
        -------
        ProgressionContextNodeEvidence
            Essential source label, type, order, and identity without raw properties.
        """

        if isinstance(node, FrameworkNode):
            return ProgressionContextNodeEvidence(
                label=node.name,
                node_id=node.node_id,
                node_kind=ProgressionContextNodeKind.FRAMEWORK,
                normalized_statement_type=None,
                source_export_order=node.source_export_order,
                statement_code=None,
                statement_type=None,
            )

        return ProgressionContextNodeEvidence(
            label=node.description,
            node_id=node.node_id,
            node_kind=ProgressionContextNodeKind.STANDARD,
            normalized_statement_type=node.normalized_statement_type,
            source_export_order=node.source_export_order,
            statement_code=node.statement_code,
            statement_type=node.statement_type,
        )

    @staticmethod
    def _compact_context_relationship(
        relationship: GraphRelationship,
    ) -> ProgressionContextRelationshipEvidence:
        """Return one compact exact relationship reference for hierarchy evidence.

        Parameters
        ----------
        relationship
            Exact authored relationship from a validated root path.

        Returns
        -------
        ProgressionContextRelationshipEvidence
            Essential relationship identity, endpoints, order, and status.
        """

        return ProgressionContextRelationshipEvidence(
            label=relationship.label,
            relationship_id=relationship.relationship_id,
            resolution_status=relationship.resolution_status,
            source_export_order=relationship.source_export_order,
            source_node_id=relationship.source_node_id,
            target_node_id=relationship.target_node_id,
        )

    @classmethod
    def _compact_root_path(cls, path: RootPath) -> ProgressionRootPathEvidence:
        """Return one compact exact root path without repeating raw graph properties.

        Parameters
        ----------
        path
            Validated complete framework-root-to-candidate path.

        Returns
        -------
        ProgressionRootPathEvidence
            Compact node and relationship evidence in source direction.
        """

        return ProgressionRootPathEvidence(
            nodes=tuple(cls._compact_context_node(node) for node in path.nodes),
            relationships=tuple(
                cls._compact_context_relationship(relationship)
                for relationship in path.relationships
            ),
        )

    @staticmethod
    def _canonicalize_request_scope(
        *,
        package: CatalogGraphPackage,
        request: CollectProgressionEvidenceRequest,
        snapshot: CatalogFrameworkSnapshot,
    ) -> CollectProgressionEvidenceRequest:
        """Return the request with grade sets in package-declared canonical order.

        Parameters
        ----------
        package
            Exact accepted Academic Standards package.
        request
            Validated request whose grade values are available in the package.
        snapshot
            Exact selected framework snapshot.

        Returns
        -------
        CollectProgressionEvidenceRequest
            Equivalent request with order-independent canonical grade tuples.
        """

        requested_local = set(request.local_grade_labels)
        requested_normalized = set(request.normalized_grades)
        local_grade_labels = tuple(
            value
            for value in snapshot.source_metadata.local_grades_or_stages
            if value in requested_local
        )
        normalized_grades = tuple(
            value
            for value in package.profile_facets.normalized_grades
            if value in requested_normalized
        )
        return request.model_copy(
            update={
                "local_grade_labels": local_grade_labels,
                "normalized_grades": normalized_grades,
            }
        )

    def _discover_candidates(
        self,
        *,
        package: CatalogGraphPackage,
        request: CollectProgressionEvidenceRequest,
        snapshot: CatalogFrameworkSnapshot,
    ) -> _DiscoveryState:
        """Build one deduplicated bounded discovery pool for the requested focus.

        Parameters
        ----------
        package
            Exact accepted Academic Standards package.
        request
            Validated focus, scope, and candidate limit.
        snapshot
            Exact selected framework snapshot.

        Returns
        -------
        _DiscoveryState
            Unique eligible candidates, completion state, and warnings.
        """

        state = _DiscoveryState()

        if request.focus_mode is ProgressionEvidenceFocusMode.TOPIC:
            self._search_and_expand(
                discovery_method=(
                    ProgressionCandidateDiscoveryMethod.DIRECT_SEARCH_HIT
                ),
                match_operator=TextOperator.ALL,
                package=package,
                query=request.topic_or_standard,
                request=request,
                snapshot=snapshot,
                state=state,
            )
            return state

        anchors = self._resolve_anchors(
            package=package, request=request, snapshot=snapshot, state=state
        )
        derived_queries: list[str] = []

        for anchor in anchors:
            query = self._anchor_search_query(
                node=anchor, package=package, snapshot=snapshot
            )

            if query is not None and query not in derived_queries:
                derived_queries.append(query)

        for query in derived_queries:
            self._search_and_expand(
                discovery_method=(
                    ProgressionCandidateDiscoveryMethod.ANCHOR_TERM_SEARCH
                ),
                match_operator=TextOperator.ALL,
                package=package,
                query=query,
                request=request,
                snapshot=snapshot,
                state=state,
            )

        return state

    def _expand_grouping(
        self,
        *,
        discovery_index: int,
        grouping_node: StandardNode,
        package: CatalogGraphPackage,
        request: CollectProgressionEvidenceRequest,
        snapshot: CatalogFrameworkSnapshot,
        state: _DiscoveryState,
    ) -> None:
        """Expand one matching grouping to eligible descendant standard items.

        Parameters
        ----------
        discovery_index
            Stable position of the grouping in the originating discovery result.
        grouping_node
            Exact grouping item whose descendants are inspected.
        package
            Exact accepted Academic Standards package.
        request
            Validated explicit grade scope.
        snapshot
            Exact selected framework snapshot.
        state
            Mutable discovery accumulator owned by the current service call.
        """

        context = self.standards_service.get_standard_context(
            GetStandardContextRequest(
                ancestor_depth=0,
                child_depth=_GROUPING_DESCENDANT_DEPTH,
                framework_id=snapshot.framework_id,
                graph_type=package.package_identity.graph_type,
                include_all_root_paths=False,
                include_descendants=True,
                include_direct_children=False,
                include_unresolved=True,
                max_nodes=_GROUPING_DESCENDANT_NODE_LIMIT,
                max_path_node_occurrences=1,
                max_paths=1,
                node_id=grouping_node.node_id,
                relationship_types=(),
                snapshot_id=snapshot.snapshot_id,
            )
        )
        descendants = context.descendants

        if descendants is None:
            return

        if not descendants.is_complete:
            state.discovery_complete = False
            state.warnings.append(
                ProgressionEvidenceWarning(
                    code=ProgressionEvidenceWarningCode.DISCOVERY_INCOMPLETE,
                    message=(
                        "A matching grouping exceeded the bounded descendant discovery "
                        "limit."
                    ),
                    node_id=grouping_node.node_id,
                )
            )

        for traversal_index, traversal_node in enumerate(descendants.nodes):
            node = traversal_node.node

            if (
                not isinstance(node, StandardNode)
                or node.node_id == grouping_node.node_id
                or node.normalized_statement_type
                is not NormalizedStatementType.STANDARD
            ):
                continue

            facets = self.standards_service.search_service.get_node_facet_evidence(
                graph_package_id=package.package_identity.graph_package_id,
                node_id=node.node_id,
            )

            if not self._matches_scope(
                facets=facets,
                local_grade_labels=request.local_grade_labels,
                normalized_grades=request.normalized_grades,
            ):
                continue

            combined_index = (
                discovery_index * _GROUPING_DESCENDANT_NODE_LIMIT + traversal_index
            )
            self._add_candidate(
                discovery_index=combined_index,
                discovery_method=(
                    ProgressionCandidateDiscoveryMethod.GROUPING_DESCENDANT
                ),
                facets=facets,
                node=node,
                search_hit=None,
                state=state,
            )

    @staticmethod
    def _matches_scope(
        *,
        facets: SearchFacetEvidence,
        local_grade_labels: tuple[str, ...],
        normalized_grades: tuple[str, ...],
    ) -> bool:
        """Return whether one candidate satisfies both populated scope dimensions.

        Parameters
        ----------
        facets
            Exact package-local source and normalized grade evidence.
        local_grade_labels
            Requested exact local grade labels, using OR semantics within the tuple.
        normalized_grades
            Requested exact normalized grades, using OR semantics within the tuple.

        Returns
        -------
        bool
            ``True`` only when every populated dimension matches.
        """

        local_matches = not local_grade_labels or bool(
            set(local_grade_labels).intersection(facets.resolved_local_grade_labels)
        )
        normalized_matches = not normalized_grades or bool(
            set(normalized_grades).intersection(facets.normalized_grades)
        )
        return local_matches and normalized_matches

    def _process_search_hit(
        self,
        *,
        discovery_index: int,
        discovery_method: ProgressionCandidateDiscoveryMethod,
        hit: SearchHit,
        package: CatalogGraphPackage,
        request: CollectProgressionEvidenceRequest,
        snapshot: CatalogFrameworkSnapshot,
        state: _DiscoveryState,
    ) -> None:
        """Add one standard hit or expand one grouping hit deterministically.

        Parameters
        ----------
        discovery_index
            Stable zero-based search-result position.
        discovery_method
            Direct-topic or anchor-term search route.
        hit
            Exact package-local search evidence.
        package
            Exact accepted Academic Standards package.
        request
            Validated focus and grade scope.
        snapshot
            Exact selected framework snapshot.
        state
            Mutable discovery accumulator owned by the current service call.
        """

        node = hit.node

        if node.normalized_statement_type is NormalizedStatementType.STANDARD_GROUPING:
            self._expand_grouping(
                discovery_index=discovery_index,
                grouping_node=node,
                package=package,
                request=request,
                snapshot=snapshot,
                state=state,
            )
            return

        self._add_candidate(
            discovery_index=discovery_index,
            discovery_method=discovery_method,
            facets=hit.facets,
            node=node,
            search_hit=hit,
            state=state,
        )

    def _resolve_anchors(
        self,
        *,
        package: CatalogGraphPackage,
        request: CollectProgressionEvidenceRequest,
        snapshot: CatalogFrameworkSnapshot,
        state: _DiscoveryState,
    ) -> tuple[StandardNode, ...]:
        """Resolve exact identifier or statement-code anchors without reinterpretation.

        Parameters
        ----------
        package
            Exact accepted Academic Standards package.
        request
            Validated non-topic focus request.
        snapshot
            Exact selected framework snapshot.
        state
            Mutable discovery accumulator receiving resolved eligible anchors.

        Returns
        -------
        tuple[StandardNode, ...]
            Exact resolved anchor nodes in deterministic order.
        """

        if request.focus_mode is ProgressionEvidenceFocusMode.STATEMENT_CODE:
            result = self.standards_service.search_standards(
                ExactCodeStandardsSearchRequest(
                    cursor=None,
                    framework_ids=(snapshot.framework_id,),
                    include_groupings=True,
                    jurisdictions=(),
                    languages=(),
                    limit=_DISCOVERY_LIMIT,
                    local_grade_labels=request.local_grade_labels,
                    mode="code_exact",
                    normalized_grades=request.normalized_grades,
                    normalized_statement_types=(),
                    normalized_subjects=(),
                    query=request.topic_or_standard,
                    snapshot_ids=(snapshot.snapshot_id,),
                    statement_types=(),
                    subjects=(),
                )
            )
            self._record_search_warnings(
                search_warnings=result.page.warnings, state=state
            )
            if result.page.has_more:
                state.discovery_complete = False
                state.warnings.append(
                    ProgressionEvidenceWarning(
                        code=ProgressionEvidenceWarningCode.DISCOVERY_INCOMPLETE,
                        message=(
                            "Exact-code anchor discovery exceeded the bounded search "
                            "pool."
                        ),
                    )
                )

            anchors: list[StandardNode] = []

            for discovery_index, hit in enumerate(result.page.hits):
                anchors.append(hit.node)
                self._process_search_hit(
                    discovery_index=discovery_index,
                    discovery_method=(ProgressionCandidateDiscoveryMethod.EXACT_ANCHOR),
                    hit=hit,
                    package=package,
                    request=request,
                    snapshot=snapshot,
                    state=state,
                )

            return tuple(anchors)

        identifier = {
            ProgressionEvidenceFocusMode.CASE_IDENTIFIER_URI: (
                CaseUriStandardIdentifier(
                    case_identifier_uri=request.topic_or_standard,
                    identifier_type="case_identifier_uri",
                )
            ),
            ProgressionEvidenceFocusMode.CASE_IDENTIFIER_UUID: (
                CaseUuidStandardIdentifier(
                    case_identifier_uuid=request.topic_or_standard,
                    identifier_type="case_identifier_uuid",
                )
            ),
            ProgressionEvidenceFocusMode.NODE_ID: NodeIdStandardIdentifier(
                identifier_type="node_id", node_id=request.topic_or_standard
            ),
        }.get(request.focus_mode)

        if identifier is None:
            raise CapabilityUnavailableError(
                details={"focus_mode": request.focus_mode.value},
                message="The requested progression evidence focus mode is unsupported.",
            )

        standard = self.standards_service.get_standard(
            GetStandardRequest(
                framework_id=snapshot.framework_id,
                graph_type=package.package_identity.graph_type,
                identifier=identifier,
                snapshot_id=snapshot.snapshot_id,
            )
        )
        node = standard.node

        if node.normalized_statement_type is NormalizedStatementType.STANDARD_GROUPING:
            self._expand_grouping(
                discovery_index=0,
                grouping_node=node,
                package=package,
                request=request,
                snapshot=snapshot,
                state=state,
            )
        elif self._matches_scope(
            facets=standard.facets,
            local_grade_labels=request.local_grade_labels,
            normalized_grades=request.normalized_grades,
        ):
            self._add_candidate(
                discovery_index=0,
                discovery_method=ProgressionCandidateDiscoveryMethod.EXACT_ANCHOR,
                facets=standard.facets,
                node=node,
                search_hit=None,
                state=state,
            )

        return (node,)

    @staticmethod
    def _record_search_warnings(
        *, search_warnings: tuple[SearchWarning, ...], state: _DiscoveryState
    ) -> None:
        """Copy exact search warnings into progression evidence warnings.

        Parameters
        ----------
        search_warnings
            Existing package-local search warnings in deterministic order.
        state
            Mutable discovery accumulator receiving public warning wrappers.
        """

        for warning in search_warnings:
            state.warnings.append(
                ProgressionEvidenceWarning(
                    code=ProgressionEvidenceWarningCode.SEARCH_WARNING,
                    message=warning.message,
                    node_id=warning.node_id,
                    search_warning=warning,
                )
            )

    @staticmethod
    def _record_scope_coverage_warnings(
        *,
        scope_coverage: tuple[ProgressionScopeCoverage, ...],
        warnings: list[ProgressionEvidenceWarning],
    ) -> None:
        """Record explicit warnings for requested scopes lacking retained evidence.

        Parameters
        ----------
        scope_coverage
            Deterministic discovered and retained counts for every requested scope.
        warnings
            Mutable result-warning accumulator.
        """

        for coverage in scope_coverage:
            if coverage.discovered_candidate_count == 0:
                warnings.append(
                    ProgressionEvidenceWarning(
                        code=(ProgressionEvidenceWarningCode.SCOPE_WITHOUT_CANDIDATES),
                        message=(
                            f"Requested {coverage.scope_kind.value} "
                            f"'{coverage.scope_value}' has no discovered candidates."
                        ),
                    )
                )
            elif coverage.retained_candidate_count == 0:
                warnings.append(
                    ProgressionEvidenceWarning(
                        code=ProgressionEvidenceWarningCode.SCOPE_NOT_RETAINED,
                        message=(
                            f"Requested {coverage.scope_kind.value} "
                            f"'{coverage.scope_value}' has discovered evidence but no "
                            f"retained candidate within the hard limit."
                        ),
                    )
                )

    @staticmethod
    def _scope_coverage(
        *,
        local_grade_labels: tuple[str, ...],
        normalized_grades: tuple[str, ...],
        ranked_candidates: tuple[_CandidateRecord, ...],
        retained_candidates: tuple[_CandidateRecord, ...],
    ) -> tuple[ProgressionScopeCoverage, ...]:
        """Build deterministic discovered and retained counts for every scope value.

        Parameters
        ----------
        local_grade_labels
            Requested exact local grade labels in caller order.
        normalized_grades
            Requested exact normalized grades in caller order.
        ranked_candidates
            Complete unique discovery pool.
        retained_candidates
            Deterministically selected bounded subset.

        Returns
        -------
        tuple[ProgressionScopeCoverage, ...]
            Local coverage followed by normalized coverage in caller order.
        """

        coverage: list[ProgressionScopeCoverage] = []

        for value in local_grade_labels:
            coverage.append(
                ProgressionScopeCoverage(
                    discovered_candidate_count=sum(
                        value in candidate.facets.resolved_local_grade_labels
                        for candidate in ranked_candidates
                    ),
                    retained_candidate_count=sum(
                        value in candidate.facets.resolved_local_grade_labels
                        for candidate in retained_candidates
                    ),
                    scope_kind=ProgressionScopeKind.LOCAL_GRADE_LABEL,
                    scope_value=value,
                )
            )

        for value in normalized_grades:
            coverage.append(
                ProgressionScopeCoverage(
                    discovered_candidate_count=sum(
                        value in candidate.facets.normalized_grades
                        for candidate in ranked_candidates
                    ),
                    retained_candidate_count=sum(
                        value in candidate.facets.normalized_grades
                        for candidate in retained_candidates
                    ),
                    scope_kind=ProgressionScopeKind.NORMALIZED_GRADE,
                    scope_value=value,
                )
            )

        return tuple(coverage)

    def _search_and_expand(
        self,
        *,
        discovery_method: ProgressionCandidateDiscoveryMethod,
        match_operator: TextOperator,
        package: CatalogGraphPackage,
        query: str,
        request: CollectProgressionEvidenceRequest,
        snapshot: CatalogFrameworkSnapshot,
        state: _DiscoveryState,
    ) -> None:
        """Run one bounded exact-package lexical search and expand grouping hits.

        Parameters
        ----------
        discovery_method
            Direct topic or anchor-derived search route assigned to standard hits.
        match_operator
            Any- or all-token deterministic lexical policy.
        package
            Exact accepted Academic Standards package.
        query
            Bounded source or caller topic terms.
        request
            Validated explicit grade scope.
        snapshot
            Exact selected framework snapshot.
        state
            Mutable discovery accumulator owned by the current service call.
        """

        result = self.standards_service.search_standards(
            TextStandardsSearchRequest(
                cursor=None,
                framework_ids=(snapshot.framework_id,),
                include_groupings=True,
                jurisdictions=(),
                languages=(),
                limit=_DISCOVERY_LIMIT,
                local_grade_labels=request.local_grade_labels,
                match=TokenTextMatch(
                    match_mode=TextMatchMode.TOKENS, operator=match_operator
                ),
                mode="text",
                normalized_grades=request.normalized_grades,
                normalized_statement_types=(),
                normalized_subjects=(),
                query=query,
                snapshot_ids=(snapshot.snapshot_id,),
                statement_types=(),
                subjects=(),
            )
        )
        self._record_search_warnings(search_warnings=result.page.warnings, state=state)

        if result.page.has_more:
            state.discovery_complete = False
            state.warnings.append(
                ProgressionEvidenceWarning(
                    code=ProgressionEvidenceWarningCode.DISCOVERY_INCOMPLETE,
                    message=(
                        "Candidate discovery exceeded the bounded lexical search pool."
                    ),
                )
            )

        for discovery_index, hit in enumerate(result.page.hits):
            self._process_search_hit(
                discovery_index=discovery_index,
                discovery_method=discovery_method,
                hit=hit,
                package=package,
                request=request,
                snapshot=snapshot,
                state=state,
            )

    @staticmethod
    def _select_candidates(
        *,
        candidate_limit: int,
        local_grade_labels: tuple[str, ...],
        normalized_grades: tuple[str, ...],
        ranked_candidates: tuple[_CandidateRecord, ...],
    ) -> tuple[_CandidateRecord, ...]:
        """Select a bounded grade-balanced set, then fill by deterministic rank.

        Parameters
        ----------
        candidate_limit
            Maximum unique standard-item candidates retained.
        local_grade_labels
            Requested local scopes, preferred as balance buckets when present.
        normalized_grades
            Requested normalized scopes used when no local scopes were supplied.
        ranked_candidates
            Complete unique candidates ordered by deterministic relevance and source
            position.

        Returns
        -------
        tuple[_CandidateRecord, ...]
            At most ``candidate_limit`` unique records in deterministic selection order.
        """

        scope_values = local_grade_labels or normalized_grades
        use_local_scope = bool(local_grade_labels)
        buckets = {
            scope_value: tuple(
                candidate
                for candidate in ranked_candidates
                if (
                    scope_value in candidate.facets.resolved_local_grade_labels
                    if use_local_scope
                    else scope_value in candidate.facets.normalized_grades
                )
            )
            for scope_value in scope_values
        }
        selected: list[_CandidateRecord] = []
        selected_node_ids: set[NodeId] = set()
        positions = {scope_value: 0 for scope_value in scope_values}

        while len(selected) < candidate_limit:
            selected_in_round = False

            for scope_value in scope_values:
                bucket = buckets[scope_value]
                position = positions[scope_value]

                while (
                    position < len(bucket)
                    and bucket[position].node.node_id in selected_node_ids
                ):
                    position += 1

                positions[scope_value] = position

                if position >= len(bucket):
                    continue

                candidate = bucket[position]
                positions[scope_value] = position + 1
                selected.append(candidate)
                selected_node_ids.add(candidate.node.node_id)
                selected_in_round = True

                if len(selected) == candidate_limit:
                    break

            if not selected_in_round:
                break

        for candidate in ranked_candidates:
            if len(selected) == candidate_limit:
                break

            if candidate.node.node_id in selected_node_ids:
                continue

            selected.append(candidate)
            selected_node_ids.add(candidate.node.node_id)

        return tuple(selected)

    @staticmethod
    def _validate_grade_scope(
        *,
        local_grade_labels: tuple[str, ...],
        normalized_grades: tuple[str, ...],
        package: CatalogGraphPackage,
        snapshot: CatalogFrameworkSnapshot,
    ) -> None:
        """Require every grade filter to exist in the selected exact package.

        Parameters
        ----------
        local_grade_labels
            Exact source-facing grade or stage labels.
        normalized_grades
            Exact normalized retrieval facets.
        package
            Exact accepted Academic Standards package.
        snapshot
            Exact selected framework snapshot.

        Raises
        ------
        CapabilityUnavailableError
            If any requested local or normalized grade is unavailable.
        """

        unavailable_local = tuple(
            value
            for value in local_grade_labels
            if value not in snapshot.source_metadata.local_grades_or_stages
        )
        unavailable_normalized = tuple(
            value
            for value in normalized_grades
            if value not in package.profile_facets.normalized_grades
        )

        if not unavailable_local and not unavailable_normalized:
            return

        raise CapabilityUnavailableError(
            details={
                "available_local_grade_labels": (
                    snapshot.source_metadata.local_grades_or_stages
                ),
                "available_normalized_grades": package.profile_facets.normalized_grades,
                "unavailable_local_grade_labels": unavailable_local,
                "unavailable_normalized_grades": unavailable_normalized,
            },
            message=(
                "One or more requested progression grade scopes are unavailable in "
                "the selected framework snapshot."
            ),
            recovery_hint=(
                "Use exact values reported by get_framework. Supply each local grade "
                "in local_grade_labels or each normalized retrieval facet in "
                "normalized_grades as a separate array item."
            ),
        )
