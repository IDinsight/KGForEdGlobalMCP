"""This module coordinates canonical standards search, exact lookup, and graph context.

This module provides ``StandardsService``, which adapts validated requests to the
existing framework, catalog, search, graph-store, and traversal boundaries. It resolves
the selected framework snapshots, constructs existing search scopes and filters,
delegates deterministic search, performs exact namespace-specific standard lookup, and
assembles requested hierarchy context and relationship-status evidence.

The service preserves independent package namespaces and does not merge identifiers,
graphs, relationships, lexical indexes, code indexes, or cursors across packages. It
does not reimplement code normalization, lexical matching, filtering, ranking, search
pagination, catalog routing, or graph traversal, and it does not infer preferred
parents, instructional sequence, mastery, equivalence, progression, or prerequisites.
"""

# Standard Library
from collections.abc import Iterable
from dataclasses import dataclass

# Package Library
from kgfegmcp.catalog.models import CatalogFrameworkSnapshot
from kgfegmcp.catalog.service import CatalogService
from kgfegmcp.domain.enums import GraphType
from kgfegmcp.domain.identifiers import GraphPackageId, NodeId, RelationshipId
from kgfegmcp.errors import (
    CapabilityUnavailableError,
    GraphNodeNotFoundError,
    StandardNotFoundError,
)
from kgfegmcp.graph.models import (
    DirectNodeRelationshipsResult,
    FrameworkNode,
    GraphNodeRecord,
    GraphRelationship,
    RootPathsResult,
    StandardNode,
    TraversalResult,
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
    SearchQuery,
    SearchSelectionMode,
    TextSearchQuery,
)
from kgfegmcp.search.service import SearchService
from kgfegmcp.services.frameworks import FrameworkService, selected_package_identities
from kgfegmcp.services.models import (
    CaseUriStandardIdentifier,
    CaseUuidStandardIdentifier,
    ContextNeighbor,
    ContextNode,
    ContextNodeDepth,
    ContextRelationship,
    ContextRelationshipStatus,
    ContextRootPaths,
    ContextTraversal,
    ExactCodeStandardsSearchRequest,
    GetStandardContextRequest,
    GetStandardContextResult,
    GetStandardRequest,
    GetStandardResult,
    NodeIdStandardIdentifier,
    PrefixCodeStandardsSearchRequest,
    SearchStandardsResult,
    StandardContextView,
    StandardsSearchRequest,
    TextStandardsSearchRequest,
    package_reference,
)


def _context_node(node: GraphNodeRecord) -> ContextNode:
    """Describe one hierarchy node by identity, code, type, grade, and wording.

    Parameters
    ----------
    node
        Framework root or standards item on a context path.

    Returns
    -------
    ContextNode
        Compact node description without rights or raw source properties.
    """

    if isinstance(node, FrameworkNode):
        return ContextNode(
            description=node.name, node_id=node.node_id, node_kind="framework"
        )

    return ContextNode(
        description=node.description,
        grade_level=getattr(node, "grade_level", None),
        node_id=node.node_id,
        node_kind="standard",
        normalized_statement_type=getattr(node, "normalized_statement_type", None),
        statement_code=getattr(node, "statement_code", None),
        statement_type=getattr(node, "statement_type", None),
    )


def _context_relationship(relationship: GraphRelationship) -> ContextRelationship:
    """Describe one hierarchy relationship by identity, endpoints, and status.

    Parameters
    ----------
    relationship
        Exact authored relationship on a context path.

    Returns
    -------
    ContextRelationship
        Compact relationship description without rights or entity labels.
    """

    return ContextRelationship(
        relationship_id=relationship.relationship_id,
        resolution_status=relationship.resolution_status,
        source_node_id=relationship.source_node_id,
        target_node_id=relationship.target_node_id,
    )


@dataclass(slots=True)
class _ContextTables:
    """Collect every node and relationship of one context result once, in order."""

    nodes: dict[NodeId, ContextNode]
    relationships: dict[RelationshipId, ContextRelationship]

    def add_node(self, node: GraphNodeRecord) -> NodeId:
        """Record one node the first time it is seen and return its identifier.

        Parameters
        ----------
        node
            Node referenced by a context section.

        Returns
        -------
        NodeId
            The node's identifier.
        """

        self.nodes.setdefault(node.node_id, _context_node(node))
        return node.node_id

    def add_relationship(self, relationship: GraphRelationship) -> RelationshipId:
        """Record one relationship the first time it is seen and return its identifier.

        Parameters
        ----------
        relationship
            Relationship referenced by a context section.

        Returns
        -------
        RelationshipId
            The relationship's identifier.
        """

        self.relationships.setdefault(
            relationship.relationship_id, _context_relationship(relationship)
        )
        return relationship.relationship_id

    def traversal(self, traversal: TraversalResult) -> ContextTraversal:
        """Record one traversal's nodes and relationships and refer to them by ID.

        Parameters
        ----------
        traversal
            Bounded ancestor or descendant traversal.

        Returns
        -------
        ContextTraversal
            The traversal's bounds, completion, and node and relationship references.
        """

        return ContextTraversal(
            is_complete=traversal.is_complete,
            max_depth=traversal.max_depth,
            max_nodes=traversal.max_nodes,
            nodes=tuple(
                ContextNodeDepth(depth=item.depth, node_id=self.add_node(item.node))
                for item in traversal.nodes
            ),
            relationship_ids=tuple(
                self.add_relationship(relationship)
                for relationship in traversal.relationships
            ),
            truncation_reason=traversal.truncation_reason,
        )

    def neighbors(
        self, relationships: DirectNodeRelationshipsResult
    ) -> tuple[ContextNeighbor, ...]:
        """Record direct neighbours and refer to each with its linking relationship.

        Parameters
        ----------
        relationships
            Direct parents or children of the origin.

        Returns
        -------
        tuple[ContextNeighbor, ...]
            Neighbour and relationship identifiers in source order.
        """

        return tuple(
            ContextNeighbor(
                node_id=self.add_node(neighbor.node),
                relationship_id=self.add_relationship(neighbor.relationship),
            )
            for neighbor in relationships.neighbors
        )

    def root_paths(self, root_paths: RootPathsResult) -> ContextRootPaths:
        """Record every root-path node and refer to each path as a node-ID list.

        Parameters
        ----------
        root_paths
            Bounded complete framework-root-to-origin paths.

        Returns
        -------
        ContextRootPaths
            The paths' bounds, completion, and node-ID lists.
        """

        for path in root_paths.paths:
            for relationship in path.relationships:
                self.add_relationship(relationship)

        return ContextRootPaths(
            framework_root_id=root_paths.framework_root_id,
            is_complete=root_paths.is_complete,
            max_depth=root_paths.max_depth,
            max_path_node_occurrences=root_paths.max_path_node_occurrences,
            max_paths=root_paths.max_paths,
            paths=tuple(
                tuple(self.add_node(node) for node in path.nodes)
                for path in root_paths.paths
            ),
            truncation_reason=root_paths.truncation_reason,
        )


def standard_context_view(result: GetStandardContextResult) -> StandardContextView:
    """Return one context result with each node and relationship described once.

    Parameters
    ----------
    result
        Complete direct, bounded, and root-path context of one standard.

    Returns
    -------
    StandardContextView
        The same context, with sections referring to shared node and relationship
        tables by identifier.
    """

    tables = _ContextTables(nodes={}, relationships={})
    ancestors = tables.traversal(result.ancestors)
    direct_parents = tables.neighbors(result.direct_parents)
    direct_children = (
        tables.neighbors(result.direct_children)
        if result.direct_children is not None
        else None
    )
    descendants = (
        tables.traversal(result.descendants) if result.descendants is not None else None
    )
    root_paths = (
        tables.root_paths(result.root_paths) if result.root_paths is not None else None
    )
    return StandardContextView(
        ancestors=ancestors,
        descendants=descendants,
        direct_children=direct_children,
        direct_parents=direct_parents,
        nodes=tuple(tables.nodes.values()),
        relationship_statuses=result.relationship_statuses,
        relationship_type=result.ancestors.relationship_type,
        relationships=tuple(tables.relationships.values()),
        root_paths=root_paths,
        standard=result.standard,
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
    def _relationship_statuses(
        *,
        ancestor_relationships: Iterable[GraphRelationship],
        child_relationships: Iterable[GraphRelationship],
        descendant_relationships: Iterable[GraphRelationship],
        parent_relationships: Iterable[GraphRelationship],
        root_path_relationships: Iterable[GraphRelationship],
    ) -> tuple[ContextRelationshipStatus, ...]:
        """Deduplicate gathered relationships and derive accepted resolution statuses.

        Relationships are merged in deterministic branch order (parents, children,
        ancestors, descendants, then root paths) so that a relationship appearing in
        more than one branch keeps its last-seen instance, matching the existing
        single-pass collection behavior.

        Parameters
        ----------
        ancestor_relationships
            Relationships from the bounded ancestor traversal.
        child_relationships
            Relationships from the optional direct-children lookup.
        descendant_relationships
            Relationships from the optional bounded descendant traversal.
        parent_relationships
            Relationships from the direct-parents lookup.
        root_path_relationships
            Relationships from the optional complete root-path traversal.

        Returns
        -------
        tuple[ContextRelationshipStatus, ...]
            Deterministically ordered statuses for each unique relationship that
            carries an explicit resolution status.
        """

        ordered_sources = (
            parent_relationships,
            child_relationships,
            ancestor_relationships,
            descendant_relationships,
            root_path_relationships,
        )
        unique_relationships = {
            str(relationship.relationship_id): relationship
            for source in ordered_sources
            for relationship in source
        }
        ordered_relationships = sorted(
            unique_relationships.values(), key=graph_relationship_order_key
        )
        return tuple(
            ContextRelationshipStatus(
                relationship_id=relationship.relationship_id,
                resolution_status=relationship.resolution_status,
            )
            for relationship in ordered_relationships
            if relationship.resolution_status is not None
        )

    @staticmethod
    def _require_standard_node(
        *, graph_package_id: GraphPackageId, node: GraphNodeRecord
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
            If the selected identifier resolves to the framework root or a learning
            component rather than a standard item node.
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
            package=package_reference(package),
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
        direct_children = (
            store.direct_children(
                node_id=standard.node.node_id, relationship_type=relationship_type
            )
            if request.include_direct_children
            else None
        )
        ancestors = traversal.ancestors(
            max_depth=request.ancestor_depth,
            max_nodes=request.max_nodes,
            node_id=standard.node.node_id,
            relationship_type=relationship_type,
        )
        descendants = (
            traversal.descendants(
                max_depth=request.child_depth,
                max_nodes=request.max_nodes,
                node_id=standard.node.node_id,
                relationship_type=relationship_type,
            )
            if request.include_descendants
            else None
        )
        root_paths = (
            traversal.all_root_paths(
                max_depth=request.ancestor_depth,
                max_path_node_occurrences=request.max_path_node_occurrences,
                max_paths=request.max_paths,
                node_id=standard.node.node_id,
                relationship_type=relationship_type,
            )
            if request.include_all_root_paths
            else None
        )

        relationship_statuses = self._relationship_statuses(
            ancestor_relationships=ancestors.relationships,
            child_relationships=(
                (neighbor.relationship for neighbor in direct_children.neighbors)
                if direct_children is not None
                else ()
            ),
            descendant_relationships=(
                descendants.relationships if descendants is not None else ()
            ),
            parent_relationships=(
                neighbor.relationship for neighbor in direct_parents.neighbors
            ),
            root_path_relationships=(
                (
                    relationship
                    for path in root_paths.paths
                    for relationship in path.relationships
                )
                if root_paths is not None
                else ()
            ),
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
        query: SearchQuery

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
            effective_scope=scope,
            page=page,
            selected_packages=selected_package_identities(
                selected_snapshots, graph_type=GraphType.ACADEMIC_STANDARDS
            ),
        )
