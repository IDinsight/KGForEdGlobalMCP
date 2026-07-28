"""This module composes deterministic comparison evidence from independent framework
packages.

This module contains the ordinary, transport-independent ``ComparisonService``. For
each selected framework, the service resolves one exact accepted snapshot, graph
package, and interpretation profile; executes one existing package-local search; keeps
that search's original ranking, warnings, result limit, and continuation cursor; and
optionally attaches the established bounded hierarchy context to each retained match.

Every framework is processed independently before the resulting sections are combined.
A failure or capability limitation in one package is therefore handled within that
package's section and does not change another package's retrieval behavior. The final
result includes exact identities, source and normalized evidence, rights, provenance,
profile disclosures, deterministic warnings, and fixed comparison disclosures.

The service composes existing catalog, search, standards, and context behavior. It does
not modify global or federated search ranking, merge namespaces or graph packages,
choose preferred parent paths, infer official equivalence, create mappings, persist
alignments, mutate source data, perform semantic search, call a language model, use MCP
sampling, or contain curriculum-specific branches.
"""

# Future Library
from __future__ import annotations

# Standard Library
from dataclasses import dataclass

# Package Library
from kgfegmcp.catalog.models import CatalogFrameworkSnapshot, CatalogGraphPackage
from kgfegmcp.catalog.service import CatalogService
from kgfegmcp.domain.enums import CodeAvailability, EpistemicStatus, GraphType
from kgfegmcp.domain.identifiers import FrameworkId, SnapshotId
from kgfegmcp.errors import InvalidComparisonSelectionError
from kgfegmcp.profiles.models import CurriculumProfile
from kgfegmcp.search.models import SearchHit, SearchMode
from kgfegmcp.services.comparison_models import (
    CompareFrameworkEvidenceResult,
    ComparisonMatchEvidence,
    ComparisonRequestSummary,
    ComparisonWarning,
    ComparisonWarningCode,
    ExactCodeFrameworkComparisonRequest,
    FrameworkComparisonRequest,
    FrameworkComparisonSection,
    PrefixCodeFrameworkComparisonRequest,
    TextFrameworkComparisonRequest,
)
from kgfegmcp.services.models import (
    ExactCodeStandardsSearchRequest,
    GetStandardContextRequest,
    GetStandardRequest,
    NodeIdStandardIdentifier,
    PrefixCodeStandardsSearchRequest,
    StandardsSearchRequest,
    TextStandardsSearchRequest,
)
from kgfegmcp.services.standards import StandardsService

_COMPARISON_DISCLOSURES: tuple[str, ...] = (
    "Normalized grades are retrieval facets, not international grade equivalence.",
    "A hasChild relationship is structural, not a source-authored progression or "
    "prerequisite.",
    "A standard statement does not prove learner mastery.",
    "Code, identifier, grade, hierarchy, or text similarity does not establish "
    "official equivalence.",
    "Cross-framework matches are exploratory retrieval evidence.",
    "Generated comparative conclusions are LLM-inferred.",
    "Rights, attribution, and provenance apply independently to every selected package.",
)


@dataclass(frozen=True, slots=True)
class _ResolvedComparisonSelection:
    """Carry one exact accepted framework, package, and profile selection."""

    package: CatalogGraphPackage
    profile: CurriculumProfile
    snapshot: CatalogFrameworkSnapshot


@dataclass(frozen=True, slots=True)
class ComparisonService:
    """Compose independently bounded exact-package comparison evidence."""

    catalog_service: CatalogService
    standards_service: StandardsService

    def __post_init__(self) -> None:
        """Require comparison and standards services to share one catalog runtime.

        Raises
        ------
        ValueError
            If independently constructed catalog or search services are mixed.
        """

        if self.standards_service.catalog_service is not self.catalog_service:
            raise ValueError(
                "ComparisonService and StandardsService must share CatalogService."
            )

    @staticmethod
    def _comparison_warning_order_key(
        warning: ComparisonWarning,
    ) -> tuple[str, str, str, str, str, str, str]:
        """Return the canonical deterministic comparison-warning ordering key.

        Parameters
        ----------
        warning
            Validated comparison warning to order.

        Returns
        -------
        tuple[str, str, str, str, str, str, str]
            Warning code, exact identities, optional evidence identities, and message.
        """

        return (
            warning.code.value,
            str(warning.framework_id),
            str(warning.snapshot_id),
            str(warning.graph_package_id),
            str(warning.node_id or ""),
            str(warning.relationship_id or ""),
            warning.message,
        )

    @staticmethod
    def _is_code_mode_supported(
        *, profile: CurriculumProfile, request: FrameworkComparisonRequest
    ) -> bool:
        """Return whether one exact profile supports the requested code mode.

        Parameters
        ----------
        profile
            Exact accepted interpretation profile.
        request
            Validated comparison request.

        Returns
        -------
        bool
            ``True`` for text requests and supported exact or prefix code requests.
        """

        if isinstance(request, TextFrameworkComparisonRequest):
            return True

        if profile.code_search_policy.availability is CodeAvailability.NONE:
            return False

        return (
            not isinstance(request, PrefixCodeFrameworkComparisonRequest)
            or profile.code_search_policy.allow_prefix_search
        )

    def _match_evidence(
        self,
        *,
        include_context_paths: bool,
        search_hit: SearchHit,
        selection: _ResolvedComparisonSelection,
    ) -> tuple[ComparisonMatchEvidence, tuple[ComparisonWarning, ...]]:
        """Retrieve exact standard and optional hierarchy evidence for one search hit.

        Parameters
        ----------
        include_context_paths
            Whether bounded direct-parent and root-path context was requested.
        search_hit
            Existing exact package-local ``SearchHit`` retained in search order.
        selection
            Exact framework selection owning the hit.

        Returns
        -------
        tuple[ComparisonMatchEvidence, tuple[ComparisonWarning, ...]]
            Match evidence and any deterministic context or unresolved warnings.
        """

        identity = selection.package.package_identity
        standard_request = GetStandardRequest(
            framework_id=identity.framework_id,
            graph_type=identity.graph_type,
            identifier=NodeIdStandardIdentifier(
                identifier_type="node_id", node_id=search_hit.node.node_id
            ),
            snapshot_id=identity.snapshot_id,
        )
        standard = self.standards_service.get_standard(standard_request)

        if not include_context_paths:
            return (
                ComparisonMatchEvidence(
                    context=None,
                    context_complete=None,
                    retrieval_status=EpistemicStatus.RETRIEVAL_CANDIDATE,
                    search_hit=search_hit,
                    standard=standard,
                ),
                (),
            )

        context = self.standards_service.get_standard_context(
            GetStandardContextRequest(
                ancestor_depth=16,
                child_depth=0,
                framework_id=identity.framework_id,
                graph_type=identity.graph_type,
                include_all_root_paths=True,
                include_descendants=False,
                include_direct_children=False,
                include_unresolved=True,
                max_nodes=250,
                max_path_node_occurrences=8_192,
                max_paths=128,
                node_id=search_hit.node.node_id,
                relationship_types=(),
                snapshot_id=identity.snapshot_id,
            )
        )
        context_complete = context.ancestors.is_complete and (
            context.root_paths is None or context.root_paths.is_complete
        )
        warnings: list[ComparisonWarning] = []

        if not context_complete:
            warnings.append(
                ComparisonWarning(
                    code=ComparisonWarningCode.CONTEXT_INCOMPLETE,
                    framework_id=identity.framework_id,
                    graph_package_id=identity.graph_package_id,
                    message=(
                        "Requested hierarchy context reached an established traversal "
                        "bound; returned paths must not be described as complete."
                    ),
                    node_id=search_hit.node.node_id,
                    relationship_id=None,
                    snapshot_id=identity.snapshot_id,
                )
            )

        warnings.extend(
            ComparisonWarning(
                code=ComparisonWarningCode.UNRESOLVED_EVIDENCE_PRESENT,
                framework_id=identity.framework_id,
                graph_package_id=identity.graph_package_id,
                message=(
                    "The returned hierarchy context contains an unresolved "
                    "relationship "
                    "status that must remain unresolved."
                ),
                node_id=search_hit.node.node_id,
                relationship_id=status.relationship_id,
                snapshot_id=identity.snapshot_id,
            )
            for status in context.relationship_statuses
        )
        warnings.sort(key=self._comparison_warning_order_key)
        return (
            ComparisonMatchEvidence(
                context=context,
                context_complete=context_complete,
                retrieval_status=EpistemicStatus.RETRIEVAL_CANDIDATE,
                search_hit=search_hit,
                standard=standard,
            ),
            tuple(warnings),
        )

    @staticmethod
    def _request_summary(
        *,
        request: FrameworkComparisonRequest,
        selections: tuple[_ResolvedComparisonSelection, ...],
    ) -> ComparisonRequestSummary:
        """Build the canonical exact-selection summary for one comparison request.

        Parameters
        ----------
        request
            Validated caller request.
        selections
            Exact independently resolved package selections in canonical order.

        Returns
        -------
        ComparisonRequestSummary
            Resolved framework and snapshot identities with shared search parameters.
        """

        match = (
            request.match
            if isinstance(request, TextFrameworkComparisonRequest)
            else None
        )
        return ComparisonRequestSummary(
            framework_ids=tuple(
                selection.snapshot.framework_id for selection in selections
            ),
            include_context_paths=request.include_context_paths,
            include_groupings=request.include_groupings,
            local_grade_labels=request.local_grade_labels,
            match=match,
            max_matches_per_framework=request.max_matches_per_framework,
            mode=SearchMode(request.mode),
            normalized_grades=request.normalized_grades,
            query=str(request.query),
            snapshot_ids=tuple(
                selection.snapshot.snapshot_id for selection in selections
            ),
        )

    def _resolve_selections(
        self, request: FrameworkComparisonRequest
    ) -> tuple[_ResolvedComparisonSelection, ...]:
        """Resolve each selected framework to one exact independent package runtime.

        Parameters
        ----------
        request
            Validated comparison request containing framework and optional snapshot IDs.

        Returns
        -------
        tuple[_ResolvedComparisonSelection, ...]
            Exact selections in framework, snapshot, and package identity order.

        Raises
        ------
        AssertionError
            If a snapshot lookup fails to raise a catalog error.
        InvalidComparisonSelectionError
            If a snapshot is outside the selected families or more than one selected
            snapshot belongs to a framework.
        """

        selected_frameworks = set(request.framework_ids)
        snapshots_by_framework: dict[FrameworkId, list[SnapshotId]] = {
            framework_id: [] for framework_id in request.framework_ids
        }

        snapshots_by_id = {
            snapshot.snapshot_id: snapshot
            for family in self.catalog_service.catalog.frameworks
            for snapshot in family.snapshots
        }

        for snapshot_id in request.snapshot_ids:
            snapshot = snapshots_by_id.get(snapshot_id)

            if snapshot is None:
                self.catalog_service.get_framework(
                    framework_id=request.framework_ids[0], snapshot_id=snapshot_id
                )
                raise AssertionError(
                    "Missing snapshot lookup must raise a catalog error."
                )

            if snapshot.framework_id not in selected_frameworks:
                raise InvalidComparisonSelectionError(
                    details={"snapshot_id": str(snapshot_id)},
                    message=(
                        "Every selected snapshot must belong to exactly one selected "
                        "framework."
                    ),
                )

            snapshots_by_framework[snapshot.framework_id].append(snapshot_id)

        duplicate_frameworks = tuple(
            sorted(
                str(framework_id)
                for framework_id, snapshot_ids in snapshots_by_framework.items()
                if len(snapshot_ids) > 1
            )
        )

        if duplicate_frameworks:
            raise InvalidComparisonSelectionError(
                details={"framework_ids": duplicate_frameworks},
                message=(
                    "At most one selected snapshot may belong to each selected framework."
                ),
            )

        selections: list[_ResolvedComparisonSelection] = []

        for framework_id in request.framework_ids:
            selected_snapshot_ids = snapshots_by_framework[framework_id]
            snapshot_id = selected_snapshot_ids[0] if selected_snapshot_ids else None
            snapshot = self.catalog_service.get_framework(
                framework_id=framework_id, snapshot_id=snapshot_id
            )
            package = self.catalog_service.get_graph_package(
                framework_id=framework_id,
                graph_type=GraphType.ACADEMIC_STANDARDS,
                snapshot_id=snapshot.snapshot_id,
            )
            loaded_package = self.catalog_service.get_loaded_package(
                framework_id=framework_id,
                graph_type=GraphType.ACADEMIC_STANDARDS,
                snapshot_id=snapshot.snapshot_id,
            )
            selections.append(
                _ResolvedComparisonSelection(
                    package=package, profile=loaded_package.profile, snapshot=snapshot
                )
            )

        selections.sort(
            key=lambda selection: (
                str(selection.snapshot.framework_id),
                str(selection.snapshot.snapshot_id),
                str(selection.package.package_identity.graph_package_id),
            )
        )
        return tuple(selections)

    @staticmethod
    def _search_request(
        *, request: FrameworkComparisonRequest, selection: _ResolvedComparisonSelection
    ) -> StandardsSearchRequest:
        """Adapt one comparison request to an existing exact-package search request.

        Parameters
        ----------
        request
            Validated comparison request.
        selection
            Exact accepted framework selection.

        Returns
        -------
        StandardsSearchRequest
            Existing standards-service request preserving search behavior.
        """

        if isinstance(request, TextFrameworkComparisonRequest):
            return TextStandardsSearchRequest(
                framework_ids=(selection.snapshot.framework_id,),
                include_groupings=request.include_groupings,
                limit=request.max_matches_per_framework,
                local_grade_labels=request.local_grade_labels,
                match=request.match,
                mode="text",
                normalized_grades=request.normalized_grades,
                query=request.query,
                snapshot_ids=(selection.snapshot.snapshot_id,),
            )

        if isinstance(request, ExactCodeFrameworkComparisonRequest):
            return ExactCodeStandardsSearchRequest(
                framework_ids=(selection.snapshot.framework_id,),
                include_groupings=request.include_groupings,
                limit=request.max_matches_per_framework,
                local_grade_labels=request.local_grade_labels,
                mode="code_exact",
                normalized_grades=request.normalized_grades,
                query=request.query,
                snapshot_ids=(selection.snapshot.snapshot_id,),
            )

        return PrefixCodeStandardsSearchRequest(
            framework_ids=(selection.snapshot.framework_id,),
            include_groupings=request.include_groupings,
            limit=request.max_matches_per_framework,
            local_grade_labels=request.local_grade_labels,
            mode="code_prefix",
            normalized_grades=request.normalized_grades,
            query=request.query,
            snapshot_ids=(selection.snapshot.snapshot_id,),
        )

    def _section(
        self,
        *,
        request: FrameworkComparisonRequest,
        selection: _ResolvedComparisonSelection,
    ) -> FrameworkComparisonSection:
        """Build one exact independently bounded framework comparison section.

        Parameters
        ----------
        request
            Validated comparison request shared across selected frameworks.
        selection
            Exact accepted snapshot, package, and profile.

        Returns
        -------
        FrameworkComparisonSection
            Complete package-local evidence, warnings, and continuation state.
        """

        identity = selection.package.package_identity
        warnings: list[ComparisonWarning] = []

        if not self._is_code_mode_supported(profile=selection.profile, request=request):
            warnings.append(
                ComparisonWarning(
                    code=ComparisonWarningCode.CODE_SEARCH_UNSUPPORTED,
                    framework_id=identity.framework_id,
                    graph_package_id=identity.graph_package_id,
                    message=(
                        "The selected framework does not support the requested exact "
                        "package code-search mode; its comparison section is empty."
                    ),
                    node_id=None,
                    relationship_id=None,
                    snapshot_id=identity.snapshot_id,
                )
            )
            matches: tuple[ComparisonMatchEvidence, ...] = ()
            package_search_warnings = ()
            has_more = False
            next_cursor = None
        else:
            search_result = self.standards_service.search_standards(
                self._search_request(request=request, selection=selection)
            )
            page = search_result.page
            match_values: list[ComparisonMatchEvidence] = []

            for search_hit in page.hits:
                match, match_warnings = self._match_evidence(
                    include_context_paths=request.include_context_paths,
                    search_hit=search_hit,
                    selection=selection,
                )
                match_values.append(match)
                warnings.extend(match_warnings)

            matches = tuple(match_values)
            package_search_warnings = page.warnings
            has_more = page.has_more
            next_cursor = page.next_cursor

            if not matches:
                warnings.append(
                    ComparisonWarning(
                        code=ComparisonWarningCode.NO_MATCHES,
                        framework_id=identity.framework_id,
                        graph_package_id=identity.graph_package_id,
                        message=(
                            "No package-local retrieval candidates matched the "
                            "requested query and filters."
                        ),
                        node_id=None,
                        relationship_id=None,
                        snapshot_id=identity.snapshot_id,
                    )
                )

        warnings.sort(key=self._comparison_warning_order_key)
        profile = selection.profile
        return FrameworkComparisonSection(
            code_search_policy=profile.code_search_policy,
            comparison_dimensions=profile.comparison_dimensions,
            framework_id=identity.framework_id,
            graph_package_id=identity.graph_package_id,
            graph_type=identity.graph_type,
            has_more=has_more,
            hierarchy=profile.hierarchy,
            known_source_anomalies=profile.known_source_anomalies,
            language_policy=profile.language_policy,
            local_grades_or_stages=(
                selection.snapshot.source_metadata.local_grades_or_stages
            ),
            matches=matches,
            next_cursor=next_cursor,
            normalized_grades=selection.package.profile_facets.normalized_grades,
            package_search_warnings=package_search_warnings,
            profile_id=identity.profile_id,
            profile_sha256=identity.profile_sha256,
            profile_version=identity.profile_version,
            required_profile_disclosures=profile.required_disclosures,
            rights=selection.package.rights,
            snapshot_id=identity.snapshot_id,
            source_metadata=selection.snapshot.source_metadata,
            source_role_capabilities=profile.source_role_capabilities,
            warnings=tuple(warnings),
        )

    def compare_framework_evidence(
        self, request: FrameworkComparisonRequest
    ) -> CompareFrameworkEvidenceResult:
        """Return deterministic independently bounded evidence for selected frameworks.

        Parameters
        ----------
        request
            Text, exact-code, or code-prefix comparison request.

        Returns
        -------
        CompareFrameworkEvidenceResult
            Canonical request summary, package-local sections, disclosures, and
            warnings.
        """

        selections = self._resolve_selections(request)
        sections = tuple(
            self._section(request=request, selection=selection)
            for selection in selections
        )
        warnings = tuple(
            sorted(
                (warning for section in sections for warning in section.warnings),
                key=self._comparison_warning_order_key,
            )
        )
        return CompareFrameworkEvidenceResult(
            disclosures=_COMPARISON_DISCLOSURES,
            epistemic_status=EpistemicStatus.DETERMINISTIC_DERIVED,
            request=self._request_summary(request=request, selections=selections),
            sections=sections,
            warnings=warnings,
        )
