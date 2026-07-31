"""This module coordinates deterministic search over independent accepted package
indexes.

The `SearchService` is the public execution boundary for search. It is constructed only
from a complete `~kgfegmcp.catalog.models.CatalogLoadResult`, after package loading,
validation, graph-store construction, and catalog construction have already succeeded.

During construction, the service creates one immutable lexical index, code index, and
controlled-facet resolver for each accepted package runtime. It retains the existing
independent graph store and exact source node instances owned by that runtime. It does
not reload packages, repeat validation, or create replacement graph stores.

For each request, the service resolves exact package selection through
`~kgfegmcp.catalog.service.CatalogService` or filters the accepted runtimes for
federated search. It then executes each selected package-local index independently,
applies package-governed filters, builds provenance and warning evidence, ranks results
deterministically, and returns an immutable cursor-paginated page.

Federated search aggregates completed results without merging graph, relationship,
identifier, lexical, or code namespaces. The service does not perform fuzzy search,
embeddings, semantic inference, alignments, framework comparison, instructional
sequence inference, filesystem access, configuration loading, or FastMCP registration.
"""

# Future Library
from __future__ import annotations

# Standard Library
import base64
import hashlib
import json

from collections.abc import Mapping
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Final, Literal

# Third Party Library
from pydantic import TypeAdapter, ValidationError

# Package Library
from kgfegmcp.catalog.models import CatalogLoadResult, CatalogPackageRuntime
from kgfegmcp.catalog.service import CatalogService
from kgfegmcp.domain.enums import (
    CodeAvailability,
    EpistemicStatus,
    NormalizedStatementType,
)
from kgfegmcp.domain.identifiers import GraphPackageId, NodeId, Sha256Digest
from kgfegmcp.errors import (
    CapabilityUnavailableError,
    CatalogError,
    InvalidCursorError,
    UnsupportedSearchModeError,
)
from kgfegmcp.graph.models import GraphPackageIdentity, StandardNode
from kgfegmcp.profiles.models import (
    CurriculumProfile,
    GradeMapping,
    StatementTypePolicy,
)
from kgfegmcp.schemas import FrozenSchema
from kgfegmcp.search.code import CodeCandidate, CodeIndex
from kgfegmcp.search.lexical import LexicalCandidate, LexicalIndex
from kgfegmcp.search.models import (
    CodeMatchEvidence,
    CodeParentDerivationEvidence,
    CodeParentDerivationStatus,
    CodeScopeEvidence,
    ExactCodeSearchQuery,
    ExactPackageSearchScope,
    FederatedPackageSearchScope,
    PackageSearchIndexMetadata,
    PrefixCodeSearchQuery,
    SearchCursor,
    SearchFacetEvidence,
    SearchField,
    SearchFilters,
    SearchHit,
    SearchIndexMetadata,
    SearchMatchedField,
    SearchMode,
    SearchPage,
    SearchQuery,
    SearchScore,
    SearchScoreAlgorithm,
    SearchSelectionMode,
    SearchWarning,
    SearchWarningCode,
    TextSearchQuery,
)
from kgfegmcp.search.normalizers import (
    CODE_NORMALIZER_VERSION,
    FACET_NORMALIZER_VERSION,
    LEXICAL_NORMALIZER_VERSION,
    normalize_facet_value,
    normalize_lexical_text,
)

_SHA256_ADAPTER: Final[TypeAdapter[Sha256Digest]] = TypeAdapter(Sha256Digest)
CURSOR_VERSION: Final[Literal[1]] = 1
OrderingPosition = tuple[int | str, ...]
RANKING_VERSION: Final[str] = "deterministic_search_ranking_v1"


class _UnsignedCursorState(FrozenSchema):
    """Represent stable cursor fields covered by the payload checksum."""

    cursor_version: Literal[1] = CURSOR_VERSION
    effective_query_sha256: Sha256Digest
    index_set_sha256: Sha256Digest
    last_ordering_position: OrderingPosition
    mode: SearchMode


class _CursorState(_UnsignedCursorState):
    """Represent the complete private checksum-protected cursor payload."""

    payload_sha256: Sha256Digest


@dataclass(frozen=True, slots=True)
class _RankedHit:
    """Associate one public hit with its complete deterministic ordering position."""

    hit: SearchHit
    ordering_position: OrderingPosition


@dataclass(frozen=True, slots=True)
class _FacetResolver:
    """Resolve source and normalized facets for exactly one loaded package profile."""

    grade_mappings_by_key: Mapping[str, GradeMapping]
    normalized_grades_by_key: Mapping[str, str]
    normalized_subjects_by_key: Mapping[str, str]
    profile: CurriculumProfile
    statement_policies_by_key: Mapping[str, StatementTypePolicy]
    subjects_by_key: Mapping[str, str]

    @classmethod
    def from_runtime(cls, runtime: CatalogPackageRuntime) -> _FacetResolver:
        """Build collision-checked package-local facet resolution maps.

        Parameters
        ----------
        runtime
            Exact accepted package runtime and loaded profile.

        Returns
        -------
        _FacetResolver
            Immutable package-local controlled-facet resolver.

        Raises
        ------
        CatalogError
            If profile values collide after deterministic facet normalization.
        """

        profile = runtime.loaded_package.profile
        grade_mappings_by_key: dict[str, GradeMapping] = {}
        normalized_grades_by_key: dict[str, str] = {}
        normalized_subjects_by_key: dict[str, str] = {}
        statement_policies_by_key: dict[str, StatementTypePolicy] = {}
        subjects_by_key: dict[str, str] = {}

        for mapping in profile.grade_mappings:
            for value in (mapping.local_label, *mapping.aliases):
                _insert_controlled_value(
                    canonical_value=mapping.local_label,
                    existing_value=(
                        grade_mappings_by_key.get(normalize_facet_value(value))
                    ),
                    facet_key=normalize_facet_value(value),
                    facet_name="local grade",
                    profile=profile,
                )
                grade_mappings_by_key[normalize_facet_value(value)] = mapping

            for normalized_grade in mapping.normalized_grades:
                _insert_string_value(
                    canonical_value=normalized_grade,
                    existing_value=normalized_grades_by_key.get(
                        normalize_facet_value(normalized_grade)
                    ),
                    facet_key=normalize_facet_value(normalized_grade),
                    facet_name="normalized grade",
                    profile=profile,
                )
                normalized_grades_by_key[normalize_facet_value(normalized_grade)] = (
                    normalized_grade
                )

        for (
            normalized_grade
        ) in runtime.loaded_package.manifest.framework.normalized_grades:
            _insert_string_value(
                canonical_value=normalized_grade,
                existing_value=normalized_grades_by_key.get(
                    normalize_facet_value(normalized_grade)
                ),
                facet_key=normalize_facet_value(normalized_grade),
                facet_name="normalized grade",
                profile=profile,
            )
            normalized_grades_by_key[normalize_facet_value(normalized_grade)] = (
                normalized_grade
            )

        for normalized_subject in profile.normalized_subjects:
            _insert_string_value(
                canonical_value=normalized_subject,
                existing_value=normalized_subjects_by_key.get(
                    normalize_facet_value(normalized_subject)
                ),
                facet_key=normalize_facet_value(normalized_subject),
                facet_name="normalized subject",
                profile=profile,
            )
            normalized_subjects_by_key[normalize_facet_value(normalized_subject)] = (
                normalized_subject
            )

        for policy in profile.statement_types:
            for value in (policy.source_statement_type, *policy.aliases):
                facet_key = normalize_facet_value(value)
                existing_policy = statement_policies_by_key.get(facet_key)
                _insert_controlled_value(
                    canonical_value=policy.source_statement_type,
                    existing_value=existing_policy,
                    facet_key=facet_key,
                    facet_name="statement type",
                    profile=profile,
                )
                statement_policies_by_key[facet_key] = policy

        for value in (profile.local_subject, *profile.subject_aliases):
            facet_key = normalize_facet_value(value)
            _insert_string_value(
                canonical_value=profile.local_subject,
                existing_value=subjects_by_key.get(facet_key),
                facet_key=facet_key,
                facet_name="local subject",
                profile=profile,
            )
            subjects_by_key[facet_key] = profile.local_subject

        return cls(
            grade_mappings_by_key=MappingProxyType(grade_mappings_by_key),
            normalized_grades_by_key=MappingProxyType(normalized_grades_by_key),
            normalized_subjects_by_key=MappingProxyType(normalized_subjects_by_key),
            profile=profile,
            statement_policies_by_key=MappingProxyType(statement_policies_by_key),
            subjects_by_key=MappingProxyType(subjects_by_key),
        )

    def evidence(
        self, *, node: StandardNode, scopes: tuple[StandardNode, ...]
    ) -> SearchFacetEvidence:
        """Build source and normalized facet evidence for one exact search node.

        Parameters
        ----------
        node
            Exact source node returned by one package-local index.
        scopes
            Exact configured code-scope nodes for code results.

        Returns
        -------
        SearchFacetEvidence
            Separate source-facing and normalized deterministic facet evidence.
        """

        node_grade_levels = node.grade_level or ()
        scope_grade_levels = tuple(
            grade for scope in scopes for grade in (scope.grade_level or ())
        )
        normalized_grades = _ordered_unique_strings(
            (*node_grade_levels, *scope_grade_levels)
        )
        normalized_grade_keys = {
            normalize_facet_value(value) for value in normalized_grades
        }
        resolved_local_grade_labels = tuple(
            mapping.local_label
            for mapping in self.profile.grade_mappings
            if normalized_grade_keys.intersection(
                normalize_facet_value(value) for value in mapping.normalized_grades
            )
        )
        local_subject = node.academic_subject
        subject_is_resolved = (
            local_subject is not None
            and normalize_facet_value(local_subject) in self.subjects_by_key
        )
        normalized_subjects = (
            self.profile.normalized_subjects if subject_is_resolved else ()
        )

        return SearchFacetEvidence(
            local_subject=local_subject,
            node_grade_levels=node_grade_levels,
            normalized_grades=normalized_grades,
            normalized_statement_type=node.normalized_statement_type,
            normalized_subjects=normalized_subjects,
            resolved_local_grade_labels=resolved_local_grade_labels,
            statement_type=node.statement_type,
        )

    def matches(self, *, evidence: SearchFacetEvidence, filters: SearchFilters) -> bool:
        """Return whether one hit satisfies all package-local filter dimensions.

        Parameters
        ----------
        evidence
            Source and normalized facets calculated for one candidate.
        filters
            Caller-supplied OR-within and AND-across filter contract.

        Returns
        -------
        bool
            ``True`` only when every populated filter dimension is satisfied.
        """

        if (
            not filters.include_groupings
            and evidence.normalized_statement_type
            is NormalizedStatementType.STANDARD_GROUPING
        ):
            return False

        if filters.normalized_statement_types and (
            evidence.normalized_statement_type not in filters.normalized_statement_types
        ):
            return False

        return (
            self._matches_local_grades(
                evidence=evidence, requested_values=filters.local_grade_labels
            )
            and _matches_normalized_values(
                actual_values=evidence.normalized_grades,
                requested_values=filters.normalized_grades,
            )
            and self._matches_local_subjects(
                actual_value=evidence.local_subject,
                requested_values=filters.local_subjects,
            )
            and _matches_normalized_values(
                actual_values=evidence.normalized_subjects,
                requested_values=filters.normalized_subjects,
            )
            and self._matches_statement_types(
                actual_value=evidence.statement_type,
                requested_values=filters.statement_types,
            )
        )

    def _matches_local_grades(
        self, *, evidence: SearchFacetEvidence, requested_values: tuple[str, ...]
    ) -> bool:
        """Match local grade labels and aliases against effective normalized grades.

        Parameters
        ----------
        evidence
            Candidate facet evidence including source-node and scope grades.
        requested_values
            Caller-supplied local grade labels or aliases.

        Returns
        -------
        bool
            ``True`` when no filter is present or one resolved local grade matches.
        """

        if not requested_values:
            return True

        requested_normalized_grades: set[str] = set()

        for value in requested_values:
            mapping = self.grade_mappings_by_key.get(normalize_facet_value(value))

            if mapping is None:
                continue

            requested_normalized_grades.update(
                normalize_facet_value(grade) for grade in mapping.normalized_grades
            )

        if not requested_normalized_grades:
            return False

        actual_normalized_grades = {
            normalize_facet_value(grade) for grade in evidence.normalized_grades
        }
        return not requested_normalized_grades.isdisjoint(actual_normalized_grades)

    def _matches_local_subjects(
        self, *, actual_value: str | None, requested_values: tuple[str, ...]
    ) -> bool:
        """Match source subject values through package-local canonical aliases.

        Parameters
        ----------
        actual_value
            Exact source node academic subject.
        requested_values
            Caller-supplied local subjects or aliases.

        Returns
        -------
        bool
            ``True`` when no filter is present or one canonical subject matches.
        """

        if not requested_values:
            return True

        if actual_value is None:
            return False

        actual_subject = self.subjects_by_key.get(normalize_facet_value(actual_value))
        requested_subjects = {
            subject
            for value in requested_values
            if (subject := self.subjects_by_key.get(normalize_facet_value(value)))
            is not None
        }
        return actual_subject is not None and actual_subject in requested_subjects

    def _matches_statement_types(
        self, *, actual_value: str | None, requested_values: tuple[str, ...]
    ) -> bool:
        """Match source statement types through package-local canonical aliases.

        Parameters
        ----------
        actual_value
            Exact source node statement type.
        requested_values
            Caller-supplied source statement types or aliases.

        Returns
        -------
        bool
            ``True`` when no filter is present or one canonical type matches.
        """

        if not requested_values:
            return True

        if actual_value is None:
            return False

        actual_policy = self.statement_policies_by_key.get(
            normalize_facet_value(actual_value)
        )
        requested_policies = {
            policy.source_statement_type
            for value in requested_values
            if (
                policy := self.statement_policies_by_key.get(
                    normalize_facet_value(value)
                )
            )
            is not None
        }
        return (
            actual_policy is not None
            and actual_policy.source_statement_type in requested_policies
        )


@dataclass(frozen=True, slots=True)
class _PackageSearchRuntime:
    """Retain one accepted runtime and its independent immutable search indexes."""

    catalog_runtime: CatalogPackageRuntime
    code_index: CodeIndex
    facets: _FacetResolver
    lexical_index: LexicalIndex
    metadata: PackageSearchIndexMetadata

    @classmethod
    def from_catalog_runtime(
        cls, catalog_runtime: CatalogPackageRuntime
    ) -> _PackageSearchRuntime:
        """Build every independent search structure for one accepted package runtime.

        Parameters
        ----------
        catalog_runtime
            Exact PR 6 package runtime and existing graph store.

        Returns
        -------
        _PackageSearchRuntime
            Package-local lexical, code, facet, and metadata structures.
        """

        code_index = CodeIndex.from_runtime(catalog_runtime)
        facets = _FacetResolver.from_runtime(catalog_runtime)
        lexical_index = LexicalIndex.from_runtime(catalog_runtime)
        metadata = _build_package_metadata(
            catalog_runtime=catalog_runtime,
            code_index=code_index,
            lexical_index=lexical_index,
        )
        return cls(
            catalog_runtime=catalog_runtime,
            code_index=code_index,
            facets=facets,
            lexical_index=lexical_index,
            metadata=metadata,
        )


@dataclass(frozen=True, slots=True)
class SearchService:
    """Search accepted package runtimes without filesystem or validation access."""

    catalog_service: CatalogService
    metadata: SearchIndexMetadata
    _packages: tuple[_PackageSearchRuntime, ...] = field(repr=False)
    _packages_by_graph_package_id: Mapping[GraphPackageId, _PackageSearchRuntime] = (
        field(repr=False)
    )

    @classmethod
    def from_catalog_load_result(cls, load_result: CatalogLoadResult) -> SearchService:
        """Build immutable package-scoped indexes from one complete catalog load.

        Parameters
        ----------
        load_result
            All-or-nothing PR 6 catalog result containing accepted package runtimes.

        Returns
        -------
        SearchService
            Pure in-memory deterministic search service.

        Raises
        ------
        CatalogError
            If package identities repeat or accepted source/profile data cannot be
            indexed without violating PR 7 contracts.
        """

        catalog_service = CatalogService.from_load_result(load_result)
        packages = tuple(
            _PackageSearchRuntime.from_catalog_runtime(runtime)
            for runtime in load_result.package_runtimes
        )
        packages_by_graph_package_id: dict[GraphPackageId, _PackageSearchRuntime] = {}

        for package in packages:
            package_identity = package.catalog_runtime.catalog_package.package_identity
            graph_package_id = package_identity.graph_package_id

            if graph_package_id in packages_by_graph_package_id:
                raise CatalogError(
                    details={"graph_package_id": str(graph_package_id)},
                    message=(
                        "Search construction encountered a duplicate package identity."
                    ),
                )

            packages_by_graph_package_id[graph_package_id] = package

        package_metadata = tuple(package.metadata for package in packages)
        index_set_sha256 = _canonical_sha256(
            {
                "packages": tuple(
                    {
                        "graph_package_id": str(
                            metadata.package_identity.graph_package_id
                        ),
                        "index_sha256": str(metadata.index_sha256),
                    }
                    for metadata in package_metadata
                )
            }
        )
        metadata = SearchIndexMetadata(
            cursor_version=CURSOR_VERSION,
            index_set_sha256=index_set_sha256,
            packages=package_metadata,
        )
        return cls(
            _packages=packages,
            _packages_by_graph_package_id=MappingProxyType(
                packages_by_graph_package_id
            ),
            catalog_service=catalog_service,
            metadata=metadata,
        )

    def get_node_facet_evidence(
        self, *, graph_package_id: GraphPackageId, node_id: NodeId
    ) -> SearchFacetEvidence:
        """Return package-local source and normalized facets for one item node.

        Parameters
        ----------
        graph_package_id
            Exact accepted graph-package identifier.
        node_id
            Exact outer node identifier within the selected package namespace.

        Returns
        -------
        SearchFacetEvidence
            Facet evidence produced by the package's existing profile resolver.

        Raises
        ------
        CatalogError
            If the package has no search runtime or the selected node is not an item.
        GraphNodeNotFoundError
            If the exact node identifier is unavailable in the selected package.
        """

        package = self._packages_by_graph_package_id.get(graph_package_id)

        if package is None:
            raise CatalogError(
                details={"graph_package_id": str(graph_package_id)},
                message="The selected graph package has no search runtime.",
            )

        node = package.catalog_runtime.graph_store.get_node_by_id(node_id).node

        if not isinstance(node, StandardNode):
            raise CatalogError(
                details={
                    "graph_package_id": str(graph_package_id),
                    "node_id": str(node_id),
                },
                message="Facet evidence is available only for standard item nodes.",
            )

        return package.facets.evidence(node=node, scopes=())

    def search(self, query: SearchQuery) -> SearchPage:
        """Execute one deterministic exact-package or federated search request.

        Parameters
        ----------
        query
            Validated immutable text, exact-code, or prefix-code query.

        Returns
        -------
        SearchPage
            One immutable page preserving exact package and source-node provenance.

        Raises
        ------
        CapabilityUnavailableError
            If an exact package lacks the requested search capability.
        InvalidCursorError
            If a cursor is malformed, mismatched, stale, or no longer locatable.
        UnsupportedSearchModeError
            If a future unsupported search mode reaches defensive dispatch.
        """

        packages = self._select_packages(query.scope)

        if isinstance(query, TextSearchQuery):
            ranked_hits, warnings, normalized_queries = self._search_text(
                packages=packages, query=query
            )
        elif isinstance(query, ExactCodeSearchQuery):
            ranked_hits, warnings, normalized_queries = self._search_code(
                packages=packages, query=query
            )
        elif isinstance(query, PrefixCodeSearchQuery):
            ranked_hits, warnings, normalized_queries = self._search_code(
                packages=packages, query=query
            )
        else:
            raise UnsupportedSearchModeError(
                details={"mode": str(query.mode)},
                message="The requested deterministic search mode is unsupported.",
            )

        ranked_hits.sort(key=_ranked_hit_order_key)
        selected_index_sha256 = _selected_index_sha256(packages)
        effective_query_sha256 = _effective_query_sha256(
            normalized_queries=normalized_queries, packages=packages, query=query
        )
        page_hits, next_cursor = _paginate_hits(
            cursor=query.cursor,
            effective_query_sha256=effective_query_sha256,
            index_set_sha256=selected_index_sha256,
            limit=query.limit,
            mode=query.mode,
            ranked_hits=tuple(ranked_hits),
        )
        return SearchPage(
            has_more=next_cursor is not None,
            hits=tuple(ranked_hit.hit for ranked_hit in page_hits),
            mode=query.mode,
            next_cursor=next_cursor,
            returned_count=len(page_hits),
            warnings=_ordered_warnings(warnings=tuple(warnings)),
        )

    @staticmethod
    def _search_code(
        *,
        packages: tuple[_PackageSearchRuntime, ...],
        query: ExactCodeSearchQuery | PrefixCodeSearchQuery,
    ) -> tuple[list[_RankedHit], list[SearchWarning], Mapping[str, str]]:
        """Execute package-local exact or prefix code search and aggregate hits.

        Parameters
        ----------
        packages
            Exact selected package search runtimes in catalog order.
        query
            Exact-code or prefix-code request.

        Returns
        -------
        tuple[list[_RankedHit], list[SearchWarning], Mapping[str, str]]
            Ranked-hit accumulator, package warnings, and per-package normalized query
            values used by cursor binding.
        """

        ranked_hits: list[_RankedHit] = []
        warnings: list[SearchWarning] = []
        normalized_queries: dict[str, str] = {}
        is_exact_scope = query.scope.selection_mode is SearchSelectionMode.EXACT

        for package in packages:
            identity = package.catalog_runtime.catalog_package.package_identity
            graph_package_id = str(identity.graph_package_id)
            availability = package.code_index.availability
            implemented_modes = implemented_search_modes(
                code_availability=availability,
                prefix_available=package.code_index.allow_prefix_search,
                text_available=(
                    package.catalog_runtime.catalog_package.capabilities.text_search
                ),
            )
            implemented_mode_text = (
                ", ".join(mode.value for mode in implemented_modes) or "none"
            )

            if availability is CodeAvailability.NONE:
                if is_exact_scope:
                    _raise_code_capability_unavailable(
                        code_availability=availability,
                        identity=identity,
                        implemented_modes=implemented_modes,
                        mode=query.mode,
                    )

                warnings.append(
                    _package_warning(
                        code=SearchWarningCode.CODE_SEARCH_UNAVAILABLE,
                        identity=identity,
                        message=(
                            f"The selected package has no source statement-code "
                            f"coverage and was skipped for code search. Available "
                            f"package search modes: {implemented_mode_text}."
                        ),
                    )
                )
                normalized_queries[graph_package_id] = "unavailable"
                continue

            if (
                query.mode is SearchMode.CODE_PREFIX
                and not package.code_index.allow_prefix_search
            ):
                if is_exact_scope:
                    _raise_code_capability_unavailable(
                        code_availability=availability,
                        identity=identity,
                        implemented_modes=implemented_modes,
                        mode=query.mode,
                    )

                warnings.append(
                    _package_warning(
                        code=SearchWarningCode.CODE_PREFIX_UNAVAILABLE,
                        identity=identity,
                        message=(
                            f"The selected package does not implement code_prefix "
                            f"search and was skipped. Available package search modes: "
                            f"{implemented_mode_text}."
                        ),
                    )
                )
                normalized_queries[graph_package_id] = "prefix_unavailable"
                continue

            if availability is CodeAvailability.PARTIAL:
                warnings.append(
                    _package_warning(
                        code=SearchWarningCode.PARTIAL_CODE_COVERAGE,
                        identity=identity,
                        message=(
                            "The selected package has partial source statement-code "
                            "coverage; uncoded nodes remain available to text search."
                        ),
                    )
                )

            if query.mode is SearchMode.CODE_EXACT:
                candidates = package.code_index.exact_candidates(query.query)
                normalized_query = package.code_index.normalizer.normalize(query.query)
            else:
                candidates = package.code_index.prefix_candidates(query.query)
                normalized_query = package.code_index.normalizer.normalize_prefix(
                    query.query
                )

            normalized_queries[graph_package_id] = normalized_query
            filtered_candidates = tuple(
                candidate
                for candidate in candidates
                if package.facets.matches(
                    evidence=package.facets.evidence(
                        node=candidate.posting.node, scopes=candidate.posting.scopes
                    ),
                    filters=query.filters,
                )
            )
            has_multiple_exact_matches = (
                query.mode is SearchMode.CODE_EXACT and len(filtered_candidates) > 1
            )

            for candidate in filtered_candidates:
                ranked_hits.append(
                    _build_code_ranked_hit(
                        candidate=candidate,
                        has_multiple_exact_matches=has_multiple_exact_matches,
                        package=package,
                        retrieval_method=query.mode,
                    )
                )

        return ranked_hits, warnings, MappingProxyType(normalized_queries)

    @staticmethod
    def _search_text(
        *, packages: tuple[_PackageSearchRuntime, ...], query: TextSearchQuery
    ) -> tuple[list[_RankedHit], list[SearchWarning], Mapping[str, str]]:
        """Execute package-local lexical search and aggregate deterministic hits.

        Parameters
        ----------
        packages
            Exact selected package search runtimes in catalog order.
        query
            Validated lexical request.

        Returns
        -------
        tuple[list[_RankedHit], list[SearchWarning], Mapping[str, str]]
            Ranked-hit accumulator, package warnings, and normalized query evidence.
        """

        ranked_hits: list[_RankedHit] = []
        warnings: list[SearchWarning] = []
        normalized_query = "\u001f".join(normalize_lexical_text(query.query))
        normalized_queries: dict[str, str] = {}
        is_exact_scope = query.scope.selection_mode is SearchSelectionMode.EXACT

        for package in packages:
            identity = package.catalog_runtime.catalog_package.package_identity
            graph_package_id = str(identity.graph_package_id)
            normalized_queries[graph_package_id] = normalized_query
            text_search_available = (
                package.catalog_runtime.loaded_package.manifest.capabilities.text_search
            )

            if not text_search_available:
                if is_exact_scope:
                    raise CapabilityUnavailableError(
                        details={
                            "graph_package_id": graph_package_id,
                            "mode": query.mode.value,
                        },
                        message=(
                            "The selected package does not provide deterministic text "
                            "search."
                        ),
                    )

                warnings.append(
                    _package_warning(
                        code=SearchWarningCode.TEXT_SEARCH_UNAVAILABLE,
                        identity=identity,
                        message=(
                            "The selected package disables text search and was skipped."
                        ),
                    )
                )
                continue

            candidates = package.lexical_index.candidates(
                match=query.match, query=query.query
            )

            for candidate in candidates:
                evidence = package.facets.evidence(node=candidate.node, scopes=())

                if not package.facets.matches(evidence=evidence, filters=query.filters):
                    continue

                ranked_hits.append(
                    _build_text_ranked_hit(
                        candidate=candidate, evidence=evidence, package=package
                    )
                )

        return ranked_hits, warnings, MappingProxyType(normalized_queries)

    def _select_packages(
        self, scope: ExactPackageSearchScope | FederatedPackageSearchScope
    ) -> tuple[_PackageSearchRuntime, ...]:
        """Resolve exact catalog routing or deterministic federated package filtering.

        Parameters
        ----------
        scope
            Exact-package or federated package-selection contract.

        Returns
        -------
        tuple[_PackageSearchRuntime, ...]
            Selected package search runtimes in established catalog order.
        """

        if isinstance(scope, ExactPackageSearchScope):
            catalog_package = self.catalog_service.get_graph_package(
                framework_id=scope.framework_id,
                graph_type=scope.graph_type,
                snapshot_id=scope.snapshot_id,
            )
            graph_package_id = catalog_package.package_identity.graph_package_id
            package = self._packages_by_graph_package_id.get(graph_package_id)

            if package is None:
                raise CatalogError(
                    details={"graph_package_id": str(graph_package_id)},
                    message=(
                        "Catalog routing selected a package without a search runtime."
                    ),
                )

            return (package,)

        framework_ids = set(scope.framework_ids)
        graph_types = set(scope.graph_types)
        snapshot_ids = set(scope.snapshot_ids)
        return tuple(
            package
            for package in self._packages
            if (
                not framework_ids
                or package.catalog_runtime.catalog_package.package_identity.framework_id
                in framework_ids
            )
            and (
                not graph_types
                or package.catalog_runtime.catalog_package.package_identity.graph_type
                in graph_types
            )
            and (
                not snapshot_ids
                or package.catalog_runtime.catalog_package.package_identity.snapshot_id
                in snapshot_ids
            )
        )


def _build_code_ranked_hit(
    *,
    candidate: CodeCandidate,
    has_multiple_exact_matches: bool,
    package: _PackageSearchRuntime,
    retrieval_method: SearchMode,
) -> _RankedHit:
    """Build one public code hit and complete deterministic ordering position.

    Parameters
    ----------
    candidate
        Exact package-local code posting and normalized query evidence.
    has_multiple_exact_matches
        Whether filtered exact lookup returned several source records.
    package
        Exact package search runtime that owns the posting.
    retrieval_method
        Exact-code or code-prefix mode.

    Returns
    -------
    _RankedHit
        Public hit and stable ordering position.
    """

    posting = candidate.posting
    identity = package.catalog_runtime.catalog_package.package_identity
    evidence = package.facets.evidence(node=posting.node, scopes=posting.scopes)
    parent_derivations = package.code_index.parent_derivations(posting)
    public_derivations = tuple(
        CodeParentDerivationEvidence(
            child_code_type=derivation.child_code_type,
            derived_code=derivation.derived_code,
            matched_parent_node_ids=tuple(
                node.node_id for node in derivation.matched_parent_nodes
            ),
            normalized_derived_code=derivation.normalized_derived_code,
            parent_code_type=derivation.parent_code_type,
            status=derivation.status,
        )
        for derivation in parent_derivations
    )
    hit_warnings = _code_hit_warnings(
        has_multiple_exact_matches=has_multiple_exact_matches,
        identity=identity,
        node=posting.node,
        parent_derivations=public_derivations,
    )
    scopes = tuple(
        CodeScopeEvidence(
            scope_node=scope, scope_statement_type=_require_scope_statement_type(scope)
        )
        for scope in posting.scopes
    )
    code_match = CodeMatchEvidence(
        authored_code=posting.authored_code,
        code_type=posting.code_type,
        normalized_code=posting.normalized_code,
        parent_derivations=public_derivations,
        scopes=scopes,
    )
    score_algorithm = (
        SearchScoreAlgorithm.CODE_EXACT_V1
        if retrieval_method is SearchMode.CODE_EXACT
        else SearchScoreAlgorithm.CODE_PREFIX_V1
    )
    score_value = 1_000_000 if candidate.is_exact_match else 500_000
    score = SearchScore(
        algorithm=score_algorithm,
        matched_term_count=1,
        phrase_matched=False,
        query_term_count=1,
        value=score_value,
    )
    matched_field = SearchMatchedField(
        field=SearchField.STATEMENT_CODE,
        matched_terms=(candidate.normalized_query,),
        phrase_matched=False,
        source_value=posting.authored_code,
    )
    hit = SearchHit(
        code_match=code_match,
        epistemic_status=EpistemicStatus.RETRIEVAL_CANDIDATE,
        facets=evidence,
        matched_fields=(matched_field,),
        matched_terms=(candidate.normalized_query,),
        node=posting.node,
        package_identity=identity,
        retrieval_method=retrieval_method,
        score=score,
        warnings=hit_warnings,
    )
    ordering_position = (
        posting.normalized_code,
        str(identity.framework_id),
        str(identity.snapshot_id),
        identity.graph_type.value,
        identity.package_revision,
        str(identity.graph_package_id),
        str(posting.node.node_id),
        posting.node.source_export_order,
    )
    return _RankedHit(hit=hit, ordering_position=ordering_position)


def _build_package_metadata(
    *,
    catalog_runtime: CatalogPackageRuntime,
    code_index: CodeIndex,
    lexical_index: LexicalIndex,
) -> PackageSearchIndexMetadata:
    """Build deterministic metadata and digest for one package-local index pair.

    Parameters
    ----------
    catalog_runtime
        Exact accepted package runtime whose profile and source facets govern search.
    code_index
        Immutable package-local code index.
    lexical_index
        Immutable package-local lexical index.

    Returns
    -------
    PackageSearchIndexMetadata
        Public deterministic index counts, versions, identity, and digest.
    """

    loaded_package = catalog_runtime.loaded_package
    profile = loaded_package.profile
    payload = {
        "capabilities": loaded_package.manifest.capabilities.model_dump(
            by_alias=True, mode="json"
        ),
        "code_normalizer_version": CODE_NORMALIZER_VERSION,
        "code_policy": code_index.policy.model_dump(by_alias=True, mode="json"),
        "code_postings": tuple(
            {
                "academic_subject": posting.node.academic_subject,
                "authored_code": posting.authored_code,
                "code_type": posting.code_type,
                "grade_level": posting.node.grade_level,
                "node_id": str(posting.node.node_id),
                "normalized_code": posting.normalized_code,
                "normalized_statement_type": (
                    posting.node.normalized_statement_type.value
                    if posting.node.normalized_statement_type is not None
                    else None
                ),
                "scopes": tuple(
                    {
                        "grade_level": scope.grade_level,
                        "node_id": str(scope.node_id),
                        "source_export_order": scope.source_export_order,
                        "statement_type": scope.statement_type,
                    }
                    for scope in posting.scopes
                ),
                "source_export_order": posting.node.source_export_order,
                "statement_type": posting.node.statement_type,
            }
            for posting in code_index.postings
        ),
        "cursor_version": CURSOR_VERSION,
        "facet_normalizer_version": FACET_NORMALIZER_VERSION,
        "facet_policy": {
            "grade_mappings": tuple(
                mapping.model_dump(by_alias=True, mode="json")
                for mapping in profile.grade_mappings
            ),
            "local_subject": profile.local_subject,
            "manifest_normalized_grades": (
                loaded_package.manifest.framework.normalized_grades
            ),
            "normalized_subjects": profile.normalized_subjects,
            "statement_types": tuple(
                policy.model_dump(by_alias=True, mode="json")
                for policy in profile.statement_types
            ),
            "subject_aliases": profile.subject_aliases,
        },
        "lexical_documents": tuple(
            {
                "academic_subject": document.node.academic_subject,
                "grade_level": document.node.grade_level,
                "description": document.node.description,
                "node_id": str(document.node.node_id),
                "normalized_statement_type": (
                    document.node.normalized_statement_type.value
                    if document.node.normalized_statement_type is not None
                    else None
                ),
                "source_export_order": document.node.source_export_order,
                "statement_type": document.node.statement_type,
                "tokens": document.tokens,
            }
            for document in lexical_index.documents_by_id.values()
        ),
        "lexical_normalizer_version": LEXICAL_NORMALIZER_VERSION,
        "package_identity": code_index.package_identity.model_dump(
            by_alias=True, mode="json"
        ),
        "ranking_version": RANKING_VERSION,
    }
    index_sha256 = _canonical_sha256(payload)
    return PackageSearchIndexMetadata(
        code_normalizer_version=CODE_NORMALIZER_VERSION,
        coded_node_count=code_index.coded_node_count,
        cursor_version=CURSOR_VERSION,
        index_sha256=index_sha256,
        lexical_document_count=lexical_index.document_count,
        lexical_normalizer_version=LEXICAL_NORMALIZER_VERSION,
        lexical_posting_count=lexical_index.posting_count,
        lexical_unique_token_count=lexical_index.unique_token_count,
        normalized_code_key_count=code_index.normalized_code_key_count,
        package_identity=code_index.package_identity,
        ranking_version=RANKING_VERSION,
    )


def _build_text_ranked_hit(
    *,
    candidate: LexicalCandidate,
    evidence: SearchFacetEvidence,
    package: _PackageSearchRuntime,
) -> _RankedHit:
    """Build one public lexical hit and complete deterministic ordering position.

    Parameters
    ----------
    candidate
        Exact package-local lexical candidate evidence.
    evidence
        Source and normalized facets for the exact node.
    package
        Exact package search runtime that owns the node.

    Returns
    -------
    _RankedHit
        Public lexical hit and stable ordering position.
    """

    identity = package.catalog_runtime.catalog_package.package_identity
    matched_field = SearchMatchedField(
        field=SearchField.DESCRIPTION,
        matched_terms=candidate.matched_terms,
        phrase_matched=candidate.phrase_matched,
        source_value=candidate.source_value,
    )
    score = SearchScore(
        algorithm=SearchScoreAlgorithm.LEXICAL_TOKEN_COVERAGE_V1,
        matched_term_count=len(tuple(dict.fromkeys(candidate.matched_terms))),
        phrase_matched=candidate.phrase_matched,
        query_term_count=candidate.query_term_count,
        value=candidate.score_value,
    )
    hit = SearchHit(
        code_match=None,
        epistemic_status=EpistemicStatus.RETRIEVAL_CANDIDATE,
        facets=evidence,
        matched_fields=(matched_field,),
        matched_terms=candidate.matched_terms,
        node=candidate.node,
        package_identity=identity,
        retrieval_method=SearchMode.TEXT,
        score=score,
        warnings=(),
    )
    ordering_position = (
        -candidate.score_value,
        str(identity.framework_id),
        str(identity.snapshot_id),
        identity.graph_type.value,
        identity.package_revision,
        str(identity.graph_package_id),
        str(candidate.node.node_id),
        candidate.node.source_export_order,
    )
    return _RankedHit(hit=hit, ordering_position=ordering_position)


def _canonical_sha256(payload: object) -> Sha256Digest:
    """Return a prefixed SHA-256 digest over canonical UTF-8 JSON.

    Parameters
    ----------
    payload
        JSON-serializable deterministic value.

    Returns
    -------
    Sha256Digest
        Lowercase prefixed SHA-256 digest.
    """

    canonical_json = json.dumps(
        ensure_ascii=False, obj=payload, separators=(",", ":"), sort_keys=True
    )
    digest = f"sha256:{hashlib.sha256(canonical_json.encode()).hexdigest()}"
    return _SHA256_ADAPTER.validate_python(digest)


def _code_hit_warnings(
    *,
    has_multiple_exact_matches: bool,
    identity: GraphPackageIdentity,
    node: StandardNode,
    parent_derivations: tuple[CodeParentDerivationEvidence, ...],
) -> tuple[SearchWarning, ...]:
    """Build deterministic hit-level code ambiguity and derivation warnings.

    Parameters
    ----------
    has_multiple_exact_matches
        Whether exact lookup returned several filtered source records.
    identity
        Exact package identity.
    node
        Exact matched source node.
    parent_derivations
        Public configured parent-code evidence.

    Returns
    -------
    tuple[SearchWarning, ...]
        Deterministically ordered hit-level warnings.
    """

    warnings: list[SearchWarning] = []

    if has_multiple_exact_matches:
        warnings.append(
            SearchWarning(
                code=SearchWarningCode.MULTIPLE_CODE_MATCHES,
                message=(
                    "The normalized code matches multiple source records; every "
                    "matching record is returned without selecting a preferred one."
                ),
                node_id=node.node_id,
                package_identity=identity,
            )
        )

    for derivation in parent_derivations:
        if derivation.status is CodeParentDerivationStatus.NOT_FOUND:
            warnings.append(
                SearchWarning(
                    code=SearchWarningCode.DERIVED_PARENT_CODE_NOT_FOUND,
                    message=(
                        "A configured derived parent code has no compatible source "
                        "record; graph parentage remains unchanged."
                    ),
                    node_id=node.node_id,
                    package_identity=identity,
                )
            )
        elif derivation.status is CodeParentDerivationStatus.MATCHED_MULTIPLE:
            warnings.append(
                SearchWarning(
                    code=SearchWarningCode.DERIVED_PARENT_CODE_MULTIPLE,
                    message=(
                        "A configured derived parent code matches multiple compatible "
                        "source records; no preferred graph parent is inferred."
                    ),
                    node_id=node.node_id,
                    package_identity=identity,
                )
            )

    return _ordered_warnings(tuple(warnings))


def _decode_cursor(cursor: SearchCursor) -> _CursorState:
    """Decode and checksum-validate one opaque cursor.

    Parameters
    ----------
    cursor
        Opaque base64url cursor supplied by the caller.

    Returns
    -------
    _CursorState
        Validated private continuation state.

    Raises
    ------
    InvalidCursorError
        If decoding, schema validation, or checksum verification fails.
    """

    padding = "=" * (-len(cursor.root) % 4)

    try:
        decoded_bytes = base64.urlsafe_b64decode(cursor.root + padding)
        payload = json.loads(decoded_bytes.decode())
        state = _CursorState.model_validate(payload)
    except (ValidationError, ValueError) as error:
        raise InvalidCursorError(
            details={"reason": "malformed_cursor"},
            message="The search cursor is malformed or unsupported.",
        ) from error

    unsigned_state = _UnsignedCursorState(
        cursor_version=state.cursor_version,
        effective_query_sha256=state.effective_query_sha256,
        index_set_sha256=state.index_set_sha256,
        last_ordering_position=state.last_ordering_position,
        mode=state.mode,
    )
    expected_payload_sha256 = _canonical_sha256(
        unsigned_state.model_dump(by_alias=True, mode="json")
    )

    if state.payload_sha256 != expected_payload_sha256:
        raise InvalidCursorError(
            details={"reason": "checksum_mismatch"},
            message="The search cursor checksum is invalid.",
        )

    return state


def _effective_query_sha256(
    *,
    normalized_queries: Mapping[str, str],
    packages: tuple[_PackageSearchRuntime, ...],
    query: SearchQuery,
) -> Sha256Digest:
    """Bind pagination to the complete effective request and resolved package set.

    Parameters
    ----------
    normalized_queries
        Per-package normalized query values.
    packages
        Exact resolved package search runtimes.
    query
        Validated request excluding its current cursor.

    Returns
    -------
    Sha256Digest
        Deterministic effective-query digest.
    """

    payload = {
        "normalized_queries": dict(normalized_queries),
        "query": query.model_dump(by_alias=True, exclude={"cursor"}, mode="json"),
        "resolved_packages": tuple(
            package.catalog_runtime.catalog_package.package_identity.model_dump(
                by_alias=True, mode="json"
            )
            for package in packages
        ),
    }
    return _canonical_sha256(payload)


def _encode_cursor(
    *,
    effective_query_sha256: Sha256Digest,
    index_set_sha256: Sha256Digest,
    last_ordering_position: OrderingPosition,
    mode: SearchMode,
) -> SearchCursor:
    """Encode one checksum-protected canonical JSON continuation cursor.

    Parameters
    ----------
    effective_query_sha256
        Digest of the complete effective request.
    index_set_sha256
        Digest of the exact selected package index set.
    last_ordering_position
        Complete ordering position of the final returned hit.
    mode
        Exact deterministic search mode.

    Returns
    -------
    SearchCursor
        Opaque unpadded base64url cursor.
    """

    unsigned_state = _UnsignedCursorState(
        effective_query_sha256=effective_query_sha256,
        index_set_sha256=index_set_sha256,
        last_ordering_position=last_ordering_position,
        mode=mode,
    )
    payload_sha256 = _canonical_sha256(
        unsigned_state.model_dump(by_alias=True, mode="json")
    )
    state = _CursorState(
        cursor_version=CURSOR_VERSION,
        effective_query_sha256=effective_query_sha256,
        index_set_sha256=index_set_sha256,
        last_ordering_position=last_ordering_position,
        mode=mode,
        payload_sha256=payload_sha256,
    )
    canonical_json = json.dumps(
        ensure_ascii=False,
        obj=state.model_dump(by_alias=True, mode="json"),
        separators=(",", ":"),
        sort_keys=True,
    ).encode()
    encoded = base64.urlsafe_b64encode(canonical_json).decode().rstrip("=")
    return SearchCursor(encoded)


def _insert_controlled_value(
    *,
    canonical_value: str,
    existing_value: GradeMapping | StatementTypePolicy | None,
    facet_key: str,
    facet_name: str,
    profile: CurriculumProfile,
) -> None:
    """Reject one normalized controlled-value collision between profile objects.

    Parameters
    ----------
    canonical_value
        Canonical string belonging to the candidate profile object.
    existing_value
        Existing controlled profile object at the normalized key.
    facet_key
        Deterministic normalized key.
    facet_name
        Logical facet name used in the error details.
    profile
        Exact loaded profile containing the values.

    Raises
    ------
    CatalogError
        If the existing object has a different canonical value.
    """

    if existing_value is None:
        return

    if isinstance(existing_value, GradeMapping):
        existing_canonical_value = existing_value.local_label
    else:
        existing_canonical_value = existing_value.source_statement_type

    if existing_canonical_value == canonical_value:
        return

    raise CatalogError(
        details={
            "facet_key": facet_key,
            "facet_name": facet_name,
            "profile_id": str(profile.profile_id),
            "profile_version": str(profile.profile_version),
        },
        message="Profile facet values collide after deterministic normalization.",
    )


def _insert_string_value(
    *,
    canonical_value: str,
    existing_value: str | None,
    facet_key: str,
    facet_name: str,
    profile: CurriculumProfile,
) -> None:
    """Reject one normalized string-facet collision between canonical values.

    Parameters
    ----------
    canonical_value
        Candidate canonical profile value.
    existing_value
        Existing canonical value at the normalized key.
    facet_key
        Deterministic normalized key.
    facet_name
        Logical facet name used in the error details.
    profile
        Exact loaded profile containing the values.

    Raises
    ------
    CatalogError
        If the normalized key already maps to a different canonical value.
    """

    if existing_value is None or existing_value == canonical_value:
        return

    raise CatalogError(
        details={
            "facet_key": facet_key,
            "facet_name": facet_name,
            "profile_id": str(profile.profile_id),
            "profile_version": str(profile.profile_version),
        },
        message="Profile facet values collide after deterministic normalization.",
    )


def _matches_normalized_values(
    *, actual_values: tuple[str, ...], requested_values: tuple[str, ...]
) -> bool:
    """Match one optional normalized-value OR filter against actual values.

    Parameters
    ----------
    actual_values
        Candidate normalized facet values.
    requested_values
        Caller-supplied normalized facet values.

    Returns
    -------
    bool
        ``True`` when no filter is present or one normalized value intersects.
    """

    if not requested_values:
        return True

    actual_keys = {normalize_facet_value(value) for value in actual_values}
    requested_keys = {normalize_facet_value(value) for value in requested_values}
    return not actual_keys.isdisjoint(requested_keys)


def _ordered_unique_strings(values: tuple[str, ...]) -> tuple[str, ...]:
    """Return first-occurrence string order without duplicate exact values.

    Parameters
    ----------
    values
        Source-ordered string values.

    Returns
    -------
    tuple[str, ...]
        Duplicate-free values preserving first occurrence.
    """

    return tuple(dict.fromkeys(values))


def _ordered_warnings(warnings: tuple[SearchWarning, ...]) -> tuple[SearchWarning, ...]:
    """Return duplicate-free warnings in deterministic package and code order.

    Parameters
    ----------
    warnings
        Package-level or hit-level warning values.

    Returns
    -------
    tuple[SearchWarning, ...]
        Deterministically ordered unique warnings.
    """

    warnings_by_key = {
        (
            str(warning.package_identity.framework_id),
            str(warning.package_identity.snapshot_id),
            warning.package_identity.graph_type.value,
            warning.package_identity.package_revision,
            str(warning.package_identity.graph_package_id),
            warning.code.value,
            str(warning.node_id or ""),
            warning.message,
        ): warning
        for warning in warnings
    }
    ordered_keys = list(warnings_by_key)
    ordered_keys.sort()
    return tuple(warnings_by_key[key] for key in ordered_keys)


def _package_warning(
    *, code: SearchWarningCode, identity: GraphPackageIdentity, message: str
) -> SearchWarning:
    """Build one package-level warning without node-specific evidence.

    Parameters
    ----------
    code
        Stable warning code.
    identity
        Exact selected package identity.
    message
        Actionable deterministic warning text.

    Returns
    -------
    SearchWarning
        Immutable package-level warning.
    """

    return SearchWarning(
        code=code, message=message, node_id=None, package_identity=identity
    )


def _paginate_hits(
    *,
    cursor: SearchCursor | None,
    effective_query_sha256: Sha256Digest,
    index_set_sha256: Sha256Digest,
    limit: int,
    mode: SearchMode,
    ranked_hits: tuple[_RankedHit, ...],
) -> tuple[tuple[_RankedHit, ...], SearchCursor | None]:
    """Apply immutable cursor continuation to a complete deterministic hit sequence.

    Parameters
    ----------
    cursor
        Optional opaque continuation cursor.
    effective_query_sha256
        Digest binding continuation to request semantics.
    index_set_sha256
        Digest binding continuation to selected immutable indexes.
    limit
        Requested page size.
    mode
        Exact deterministic search mode.
    ranked_hits
        Complete ordered result sequence.

    Returns
    -------
    tuple[tuple[_RankedHit, ...], SearchCursor | None]
        Current page and optional continuation cursor.

    Raises
    ------
    InvalidCursorError
        If the cursor mismatches the request, indexes, mode, or result ordering.
    """

    start_index = 0

    if cursor is not None:
        state = _decode_cursor(cursor)

        if (
            state.effective_query_sha256 != effective_query_sha256
            or state.index_set_sha256 != index_set_sha256
            or state.mode is not mode
        ):
            raise InvalidCursorError(
                details={"reason": "cursor_context_mismatch"},
                message=(
                    "The search cursor does not match the current request or package "
                    "index set."
                ),
                recovery_hint=(
                    "Retry with the exact previous search_standards request. "
                    "Replace only the cursor field. Keep the query, mode, match settings, "
                    "framework and snapshot scope, filters, includeGroupings value, "
                    "and limit unchanged. If the mismatch persists, restart pagination "
                    "without a cursor because the accepted package indexes may have "
                    "changed."
                ),
            )

        ordering_positions = tuple(
            ranked_hit.ordering_position for ranked_hit in ranked_hits
        )

        try:
            previous_index = ordering_positions.index(state.last_ordering_position)
        except ValueError as error:
            raise InvalidCursorError(
                details={"reason": "cursor_position_missing"},
                message=(
                    "The search cursor position is unavailable in the current result "
                    "ordering."
                ),
                recovery_hint=(
                    "Restart the search_standards pagination sequence without a cursor."
                ),
            ) from error

        start_index = previous_index + 1

    stop_index = start_index + limit
    page_hits = ranked_hits[start_index:stop_index]
    has_more = stop_index < len(ranked_hits)

    if not has_more or not page_hits:
        return page_hits, None

    next_cursor = _encode_cursor(
        effective_query_sha256=effective_query_sha256,
        index_set_sha256=index_set_sha256,
        last_ordering_position=page_hits[-1].ordering_position,
        mode=mode,
    )
    return page_hits, next_cursor


def _raise_code_capability_unavailable(
    *,
    code_availability: CodeAvailability,
    identity: GraphPackageIdentity,
    implemented_modes: tuple[SearchMode, ...],
    mode: SearchMode,
) -> None:
    """Raise a stable exact-package code capability error.

    Parameters
    ----------
    code_availability
        Profile-governed statement-code coverage for the selected package.
    identity
        Exact selected package identity.
    implemented_modes
        Exact search modes enabled for the selected package.
    mode
        Exact-code or code-prefix search mode.

    Raises
    ------
    CapabilityUnavailableError
        Always raised for the unavailable exact-package capability.
    """

    implemented_mode_values = tuple(
        implemented_mode.value for implemented_mode in implemented_modes
    )
    implemented_mode_text = ", ".join(implemented_mode_values) or "none"
    raise CapabilityUnavailableError(
        details={
            "code_availability": code_availability.value,
            "graph_package_id": str(identity.graph_package_id),
            "implemented_search_modes": implemented_mode_values,
            "requested_mode": mode.value,
        },
        message=(
            f"The selected package does not implement {mode.value} search. "
            f"Available package search modes: {implemented_mode_text}. A mode present "
            f"in the generic tool schema is not necessarily enabled for every package."
        ),
        recovery_hint=(
            "Inspect get_capabilities packages[].implementedSearchModes for the "
            "selected package and retry with one of the listed modes."
        ),
    )


def _ranked_hit_order_key(ranked_hit: _RankedHit) -> OrderingPosition:
    """Return the complete deterministic ordering position for list sorting.

    Parameters
    ----------
    ranked_hit
        Public hit and its already-calculated stable ordering position.

    Returns
    -------
    OrderingPosition
        Stable sort and cursor continuation key.
    """

    return ranked_hit.ordering_position


def _require_scope_statement_type(node: StandardNode) -> str:
    """Return the required source statement type for one resolved scope node.

    Parameters
    ----------
    node
        Exact source scope node retained by the package-local code index.

    Returns
    -------
    str
        Non-empty exact source statement type.

    Raises
    ------
    CatalogError
        If an accepted resolved scope node lacks a source statement type.
    """

    if node.statement_type is None or not node.statement_type.strip():
        raise CatalogError(
            details={"node_id": str(node.node_id)},
            message=(
                "An accepted resolved code-scope node has no source statement type."
            ),
        )

    return node.statement_type


def _selected_index_sha256(packages: tuple[_PackageSearchRuntime, ...]) -> Sha256Digest:
    """Digest the exact selected package-index set in catalog runtime order.

    Parameters
    ----------
    packages
        Exact selected package search runtimes.

    Returns
    -------
    Sha256Digest
        Deterministic selected-index-set digest.
    """

    payload = {
        "packages": tuple(
            {
                "graph_package_id": str(
                    package.metadata.package_identity.graph_package_id
                ),
                "index_sha256": str(package.metadata.index_sha256),
            }
            for package in packages
        )
    }
    return _canonical_sha256(payload)


def implemented_search_modes(
    *, code_availability: CodeAvailability, prefix_available: bool, text_available: bool
) -> tuple[SearchMode, ...]:
    """Return exact search modes implemented for one accepted package.

    Parameters
    ----------
    code_availability
        Profile-governed statement-code coverage.
    prefix_available
        Whether the selected profile enables delimiter-boundary prefix search.
    text_available
        Whether deterministic lexical search is enabled for the package.

    Returns
    -------
    tuple[SearchMode, ...]
        Implemented modes in stable public order.
    """

    modes: list[SearchMode] = []

    if text_available:
        modes.append(SearchMode.TEXT)

    if code_availability is not CodeAvailability.NONE:
        modes.append(SearchMode.CODE_EXACT)

        if prefix_available:
            modes.append(SearchMode.CODE_PREFIX)

    return tuple(modes)
