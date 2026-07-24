"""This module provides canonical standards search, lookup, and context orchestration.

The service adapts public PR 9 requests to the existing catalog, graph, traversal, and
search contracts. It preserves package isolation and exact identifier namespaces and
does not reimplement code normalization, lexical matching, filtering, ranking, cursor
logic, graph traversal, or package routing.
"""

# Standard Library
from dataclasses import dataclass

# Package Library
from kgfegmcp.catalog.models import CatalogFrameworkSnapshot
from kgfegmcp.catalog.service import CatalogService
from kgfegmcp.domain.enums import GraphType
from kgfegmcp.domain.identifiers import GraphPackageId
from kgfegmcp.errors import (
    CapabilityUnavailableError,
    GraphNodeNotFoundError,
    StandardNotFoundError,
)
from kgfegmcp.graph.models import (
    FrameworkNode,
    GraphRelationship,
    StandardNode,
    graph_relationship_order_key,
)
from kgfegmcp.graph.traversal import GraphTraversal
from kgfegmcp.search.models import (
    ExactCodeSearchQuery,
    ExactPackageSearchScope,
    FederatedPackageSearchScope,
    PrefixCodeSearchQuery,
    SearchFilters,
    SearchMode,
    SearchSelectionMode,
    TextSearchQuery,
)
from kgfegmcp.search.service import SearchService
from kgfegmcp.services.frameworks import FrameworkService
from kgfegmcp.services.models import (
    CaseUriStandardIdentifier,
    CaseUuidStandardIdentifier,
    ContextRelationshipStatus,
    ExactCodeStandardsSearchRequest,
    GetStandardContextRequest,
    GetStandardContextResult,
    GetStandardRequest,
    GetStandardResult,
    NodeIdStandardIdentifier,
    PrefixCodeStandardsSearchRequest,
    SearchStandardsResult,
    StandardsSearchRequest,
    TextStandardsSearchRequest,
)


@dataclass(frozen=True, slots=True)
class StandardsService:
    """Compose existing package-local standards retrieval and graph services."""

    catalog_service: CatalogService
    framework_service: FrameworkService
    search_service: SearchService

    @staticmethod
    def _build_search_scope(
        snapshots: tuple[CatalogFrameworkSnapshot, ...],
    ) -> ExactPackageSearchScope | FederatedPackageSearchScope:
        """Build an existing exact or federated search scope from exact snapshots.

        Parameters
        ----------
        snapshots
            Deterministically selected accepted snapshots.

        Returns
        -------
        ExactPackageSearchScope | FederatedPackageSearchScope
            Existing search-service package-selection contract.
        """

        if len(snapshots) == 1:
            snapshot = snapshots[0]
            return ExactPackageSearchScope(
                framework_id=snapshot.framework_id,
                graph_type=GraphType.ACADEMIC_STANDARDS,
                selection_mode=SearchSelectionMode.EXACT,
                snapshot_id=snapshot.snapshot_id,
            )

        return FederatedPackageSearchScope(
            graph_types=(GraphType.ACADEMIC_STANDARDS,),
            selection_mode=SearchSelectionMode.FEDERATED,
            snapshot_ids=tuple(snapshot.snapshot_id for snapshot in snapshots),
        )

    @staticmethod
    def _build_search_filters(request: StandardsSearchRequest) -> SearchFilters:
        """Adapt public standards filters to the existing search filter contract.

        Parameters
        ----------
        request
            Validated canonical standards-search request.

        Returns
        -------
        SearchFilters
            Existing package-local filter contract.
        """

        return SearchFilters(
            include_groupings=request.include_groupings,
            local_grade_labels=request.local_grade_labels,
            local_subjects=request.subjects,
            normalized_grades=request.normalized_grades,
            normalized_statement_types=request.normalized_statement_types,
            normalized_subjects=request.normalized_subjects,
            statement_types=request.statement_types,
        )

    @staticmethod
    def _require_standard_node(
        *, graph_package_id: GraphPackageId, node: FrameworkNode | StandardNode
    ) -> StandardNode:
        """Require an exact graph lookup to resolve to a standard item node.

        Parameters
        ----------
        graph_package_id
            Exact package identifier used only for error details.
        node
            Exact graph node returned by the selected package store.

        Returns
        -------
        StandardNode
            The unchanged exact standard or grouping node.

        Raises
        ------
        StandardNotFoundError
            If the selected identifier resolves to the framework root.
        """

        if isinstance(node, StandardNode):
            return node

        raise StandardNotFoundError(
            details={
                "graph_package_id": str(graph_package_id),
                "node_id": str(node.node_id),
            },
            message="The requested identifier does not select a standard item node.",
        )

    def get_standard(self, request: GetStandardRequest) -> GetStandardResult:
        """Return one exact standard or grouping from one selected package.

        Parameters
        ----------
        request
            Framework selection and one explicitly typed identifier namespace.

        Returns
        -------
        GetStandardResult
            Exact source node, package metadata, source metadata, and facet evidence.

        Raises
        ------
        StandardNotFoundError
            If the exact identifier is unavailable or resolves to the framework root.
        """

        snapshot = self.framework_service.resolve_snapshot_selection(
            framework_id=request.framework_id, snapshot_id=request.snapshot_id
        )
        package = self.catalog_service.get_graph_package(
            framework_id=snapshot.framework_id,
            graph_type=request.graph_type,
            snapshot_id=snapshot.snapshot_id,
        )
        store = self.catalog_service.get_graph_store(
            framework_id=snapshot.framework_id,
            graph_type=request.graph_type,
            snapshot_id=snapshot.snapshot_id,
        )

        try:
            if isinstance(request.identifier, NodeIdStandardIdentifier):
                graph_result = store.get_node_by_id(request.identifier.node_id)
            elif isinstance(request.identifier, CaseUuidStandardIdentifier):
                graph_result = store.get_node_by_case_identifier_uuid(
                    request.identifier.case_identifier_uuid
                )
            elif isinstance(request.identifier, CaseUriStandardIdentifier):
                graph_result = store.get_node_by_case_identifier_uri(
                    request.identifier.case_identifier_uri
                )
            else:
                raise StandardNotFoundError(
                    message="The requested standard identifier type is unsupported."
                )
        except GraphNodeNotFoundError as error:
            raise StandardNotFoundError(
                details={
                    "graph_package_id": str(package.package_identity.graph_package_id)
                },
                message="The requested standard identifier is unavailable.",
            ) from error

        node = self._require_standard_node(
            graph_package_id=package.package_identity.graph_package_id,
            node=graph_result.node,
        )
        facets = self.search_service.get_node_facet_evidence(
            graph_package_id=package.package_identity.graph_package_id,
            node_id=node.node_id,
        )
        return GetStandardResult(
            facets=facets,
            node=node,
            package=package,
            source_metadata=snapshot.source_metadata,
        )

    def get_standard_context(
        self, request: GetStandardContextRequest
    ) -> GetStandardContextResult:
        """Return deterministic direct, bounded, and complete-path hierarchy context.

        Parameters
        ----------
        request
            Exact standard selection and explicit traversal bounds.

        Returns
        -------
        GetStandardContextResult
            Existing graph results with every requested parent branch and status.

        Raises
        ------
        CapabilityUnavailableError
            If unresolved evidence would be hidden or a foreign relationship type is
            requested.
        StandardNotFoundError
            If the exact node is unavailable or is the framework root.
        """

        if not request.include_unresolved:
            raise CapabilityUnavailableError(
                message=(
                    "Canonical standard context cannot hide accepted unresolved "
                    "relationship statuses."
                )
            )

        standard = self.get_standard(
            GetStandardRequest(
                framework_id=request.framework_id,
                graph_type=request.graph_type,
                identifier=NodeIdStandardIdentifier(
                    identifier_type="node_id", node_id=request.node_id
                ),
                snapshot_id=request.snapshot_id,
            )
        )
        identity = standard.package.package_identity
        store = self.catalog_service.get_graph_store(
            framework_id=identity.framework_id,
            graph_type=identity.graph_type,
            snapshot_id=identity.snapshot_id,
        )
        relationship_type = store.hierarchy_relationship_type

        if request.relationship_types:
            requested_relationship_type = request.relationship_types[0]

            if requested_relationship_type != relationship_type:
                raise CapabilityUnavailableError(
                    details={
                        "available_relationship_type": relationship_type,
                        "requested_relationship_type": requested_relationship_type,
                    },
                    message=(
                        "The canonical context tool supports only the selected package "
                        "hierarchy relationship type."
                    ),
                )

        traversal = GraphTraversal(store=store)
        direct_parents = store.direct_parents(
            node_id=standard.node.node_id, relationship_type=relationship_type
        )
        direct_children = None

        if request.include_direct_children:
            direct_children = store.direct_children(
                node_id=standard.node.node_id, relationship_type=relationship_type
            )

        ancestors = traversal.ancestors(
            max_depth=request.ancestor_depth,
            max_nodes=request.max_nodes,
            node_id=standard.node.node_id,
            relationship_type=relationship_type,
        )
        descendants = None

        if request.include_descendants:
            descendants = traversal.descendants(
                max_depth=request.child_depth,
                max_nodes=request.max_nodes,
                node_id=standard.node.node_id,
                relationship_type=relationship_type,
            )

        root_paths = None

        if request.include_all_root_paths:
            root_paths = traversal.all_root_paths(
                max_depth=request.ancestor_depth,
                max_path_node_occurrences=request.max_path_node_occurrences,
                max_paths=request.max_paths,
                node_id=standard.node.node_id,
                relationship_type=relationship_type,
            )

        relationships: dict[str, GraphRelationship] = {}

        for neighbor in direct_parents.neighbors:
            relationships[str(neighbor.relationship.relationship_id)] = (
                neighbor.relationship
            )

        if direct_children is not None:
            for neighbor in direct_children.neighbors:
                relationships[str(neighbor.relationship.relationship_id)] = (
                    neighbor.relationship
                )

        for relationship in ancestors.relationships:
            relationships[str(relationship.relationship_id)] = relationship

        if descendants is not None:
            for relationship in descendants.relationships:
                relationships[str(relationship.relationship_id)] = relationship

        if root_paths is not None:
            for path in root_paths.paths:
                for relationship in path.relationships:
                    relationships[str(relationship.relationship_id)] = relationship

        ordered_relationships = tuple(
            sorted(relationships.values(), key=graph_relationship_order_key)
        )
        relationship_statuses = tuple(
            ContextRelationshipStatus(
                relationship_id=relationship.relationship_id,
                resolution_status=relationship.resolution_status,
            )
            for relationship in ordered_relationships
            if relationship.resolution_status is not None
        )
        return GetStandardContextResult(
            ancestors=ancestors,
            descendants=descendants,
            direct_children=direct_children,
            direct_parents=direct_parents,
            relationship_statuses=relationship_statuses,
            root_paths=root_paths,
            standard=standard,
        )

    def search_standards(
        self, request: StandardsSearchRequest
    ) -> SearchStandardsResult:
        """Execute canonical standards search through the existing search service.

        Parameters
        ----------
        request
            Validated lexical, exact-code, or prefix-code public request.

        Returns
        -------
        SearchStandardsResult
            Existing search page, exact effective scope, and selected snapshots.
        """

        selected_snapshots = self.framework_service.resolve_search_snapshots(
            framework_ids=request.framework_ids,
            graph_type=GraphType.ACADEMIC_STANDARDS,
            jurisdictions=request.jurisdictions,
            languages=request.languages,
            snapshot_ids=request.snapshot_ids,
            subjects=request.subjects,
        )
        scope = self._build_search_scope(selected_snapshots)
        filters = self._build_search_filters(request)

        if isinstance(request, TextStandardsSearchRequest):
            query = TextSearchQuery(
                cursor=request.cursor,
                filters=filters,
                limit=request.limit,
                match=request.match,
                mode=SearchMode.TEXT,
                query=request.query,
                scope=scope,
            )
        elif isinstance(request, ExactCodeStandardsSearchRequest):
            query = ExactCodeSearchQuery(
                cursor=request.cursor,
                filters=filters,
                limit=request.limit,
                mode=SearchMode.CODE_EXACT,
                query=request.query,
                scope=scope,
            )
        elif isinstance(request, PrefixCodeStandardsSearchRequest):
            query = PrefixCodeSearchQuery(
                cursor=request.cursor,
                filters=filters,
                limit=request.limit,
                mode=SearchMode.CODE_PREFIX,
                query=request.query,
                scope=scope,
            )
        else:
            raise CapabilityUnavailableError(
                message="The requested canonical standards search mode is unsupported."
            )

        page = self.search_service.search(query)
        return SearchStandardsResult(
            effective_scope=scope, page=page, selected_snapshots=selected_snapshots
        )
