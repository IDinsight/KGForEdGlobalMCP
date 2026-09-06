"""This module coordinates exact learning-component lookup and supports traversal.

This module provides ``LearningComponentService``, which resolves the selected framework
snapshot, performs exact node-identifier lookup, and follows ``supports`` relationships
in both directions: from a learning component to the standards it was decomposed from,
and from a standard to the components supporting it.
"""

# Standard Library
from dataclasses import dataclass

# Package Library
from kgfegmcp.catalog.service import CatalogService
from kgfegmcp.domain.enums import GraphType
from kgfegmcp.domain.identifiers import GraphPackageId, NodeId
from kgfegmcp.errors import GraphNodeNotFoundError, LearningComponentNotFoundError
from kgfegmcp.graph.models import (
    GraphNode,
    GraphRelationship,
    LearningComponentNode,
    StandardNode,
    graph_relationship_order_key,
)
from kgfegmcp.graph.store import GraphStore
from kgfegmcp.graph.traversal import GraphTraversal
from kgfegmcp.packages.wire import DELIVERY_SCHEMA_1_1_SUPPORTS_RELATIONSHIP_TYPE
from kgfegmcp.search.models import (
    LearningComponentSearchMode,
    LearningComponentSupportedCodeExactSearchQuery,
    LearningComponentSupportedCodePrefixSearchQuery,
    LearningComponentTagSearchQuery,
    LearningComponentTextSearchQuery,
)
from kgfegmcp.search.service import SearchService
from kgfegmcp.services.frameworks import FrameworkService, build_search_scope
from kgfegmcp.services.models import (
    CaseUuidStandardIdentifier,
    GetLearningComponentContextRequest,
    GetLearningComponentContextResult,
    GetLearningComponentRequest,
    GetLearningComponentResult,
    GetLearningComponentsForStandardRequest,
    GetLearningComponentsForStandardResult,
    LearningComponentsSearchRequest,
    NodeIdStandardIdentifier,
    SearchLearningComponentsResult,
    SupportedCodeExactLearningComponentsSearchRequest,
    SupportedStandard,
    SupportedStandardPlacement,
    SupportedStandardReference,
    SupportingLearningComponent,
    TagLearningComponentsSearchRequest,
    TextLearningComponentsSearchRequest,
)


@dataclass(frozen=True, slots=True)
class LearningComponentService:
    """Compose package-local learning-component retrieval over supports edges."""

    catalog_service: CatalogService
    framework_service: FrameworkService
    search_service: SearchService

    @staticmethod
    def _supported_standards(
        *, component_id: NodeId, store: GraphStore
    ) -> tuple[SupportedStandard, ...]:
        """Return every standard one learning component supports.

        Parameters
        ----------
        component_id
            Outer identifier of the learning component.
        store
            Read-only graph store for the selected package.

        Returns
        -------
        tuple[SupportedStandard, ...]
            Supported standards in deterministic relationship order.
        """

        relationships = store.outgoing_by_type_and_node.get(
            (DELIVERY_SCHEMA_1_1_SUPPORTS_RELATIONSHIP_TYPE, component_id), ()
        )
        supported: list[SupportedStandard] = []

        for relationship in sorted(relationships, key=graph_relationship_order_key):
            standard = store.nodes_by_id[relationship.target_node_id]

            if isinstance(standard, StandardNode):
                supported.append(
                    SupportedStandard(relationship=relationship, standard=standard)
                )

        return tuple(supported)

    @staticmethod
    def _placements(
        *,
        ancestor_depth: int,
        store: GraphStore,
        supported: tuple[SupportedStandard, ...],
    ) -> tuple[SupportedStandardPlacement, ...]:
        """Locate each supported standard by label rather than by ancestor record.

        Parameters
        ----------
        ancestor_depth
            Maximum hierarchy depth walked for each supported standard.
        store
            Read-only graph store for the selected package.
        supported
            Supported standards already resolved from the supports relationships.

        Returns
        -------
        tuple[SupportedStandardPlacement, ...]
            Placement summaries in the order the standards were supplied.
        """

        traversal = GraphTraversal(store=store)
        placements: list[SupportedStandardPlacement] = []

        for entry in supported:
            ancestors = traversal.ancestors(
                max_depth=ancestor_depth,
                max_nodes=ancestor_depth + 1,
                node_id=entry.standard.node_id,
                relationship_type=store.hierarchy_relationship_type,
            )
            ordered = sorted(ancestors.nodes, key=lambda item: -item.depth)
            placements.append(
                SupportedStandardPlacement(
                    grade_levels=entry.standard.grade_level or (),
                    hierarchy_path=tuple(_node_label(item.node) for item in ordered),
                    node_id=entry.standard.node_id,
                    statement_code=entry.standard.statement_code,
                    support_confidence=entry.relationship.support_confidence,
                )
            )

        return tuple(placements)

    @staticmethod
    def _require_component(
        *, graph_package_id: GraphPackageId, node: object
    ) -> LearningComponentNode:
        """Require an exact graph lookup to resolve to a learning component.

        Parameters
        ----------
        graph_package_id
            Exact package identifier used only for error details.
        node
            Exact graph node returned by the selected package store.

        Returns
        -------
        LearningComponentNode
            The unchanged learning-component node.

        Raises
        ------
        LearningComponentNotFoundError
            If the identifier resolves to a node that is not a learning component.
        """

        if isinstance(node, LearningComponentNode):
            return node

        raise LearningComponentNotFoundError(
            details={"graph_package_id": str(graph_package_id)},
            message=(
                "The requested identifier does not select a learning component node."
            ),
        )

    def search_learning_components(
        self, request: LearningComponentsSearchRequest
    ) -> SearchLearningComponentsResult:
        """Execute learning-component search through the existing search service.

        Parameters
        ----------
        request
            Validated public text, tag, or supported-code request.

        Returns
        -------
        SearchLearningComponentsResult
            Search page, exact effective scope, and selected snapshots.
        """

        selected_snapshots = self.framework_service.resolve_search_snapshots(
            framework_ids=request.framework_ids,
            graph_type=GraphType.ACADEMIC_STANDARDS,
            jurisdictions=request.jurisdictions,
            languages=request.languages,
            snapshot_ids=request.snapshot_ids,
            subjects=request.subjects,
        )
        scope = build_search_scope(selected_snapshots)
        common = {"cursor": request.cursor, "limit": request.limit, "scope": scope}
        query: (
            LearningComponentSupportedCodeExactSearchQuery
            | LearningComponentSupportedCodePrefixSearchQuery
            | LearningComponentTagSearchQuery
            | LearningComponentTextSearchQuery
        )

        if isinstance(request, TextLearningComponentsSearchRequest):
            query = LearningComponentTextSearchQuery(
                match=request.match,
                mode=LearningComponentSearchMode.TEXT,
                query=request.query,
                **common,
            )
        elif isinstance(request, TagLearningComponentsSearchRequest):
            query = LearningComponentTagSearchQuery(
                mode=LearningComponentSearchMode.TAG, query=request.query, **common
            )
        elif isinstance(request, SupportedCodeExactLearningComponentsSearchRequest):
            query = LearningComponentSupportedCodeExactSearchQuery(
                mode=LearningComponentSearchMode.SUPPORTED_CODE_EXACT,
                query=request.query,
                **common,
            )
        else:
            query = LearningComponentSupportedCodePrefixSearchQuery(
                mode=LearningComponentSearchMode.SUPPORTED_CODE_PREFIX,
                query=request.query,
                **common,
            )

        return SearchLearningComponentsResult(
            effective_scope=scope,
            page=self.search_service.search_learning_components(query),
            selected_snapshots=selected_snapshots,
        )

    def get_learning_component(
        self, request: GetLearningComponentRequest
    ) -> GetLearningComponentResult:
        """Return one exact learning component.
        Parameters
        ----------
        request
            Framework selection and the exact learning-component node identifier.

        Returns
        -------
        GetLearningComponentResult
            Exact component, supported standards, and package evidence.

        Raises
        ------
        LearningComponentNotFoundError
            If the identifier is unavailable or selects another node kind.
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
            graph_result = store.get_node_by_id(request.node_id)
        except GraphNodeNotFoundError as error:
            raise LearningComponentNotFoundError(
                details={
                    "graph_package_id": str(package.package_identity.graph_package_id)
                },
                message="The requested learning component identifier is unavailable.",
            ) from error

        node = self._require_component(
            graph_package_id=package.package_identity.graph_package_id,
            node=graph_result.node,
        )
        return GetLearningComponentResult(
            node=node,
            package=package,
            placements=self._placements(
                ancestor_depth=request.ancestor_depth,
                store=store,
                supported=self._supported_standards(
                    component_id=node.node_id, store=store
                ),
            ),
            source_metadata=snapshot.source_metadata,
        )

    def get_learning_component_context(
        self, request: GetLearningComponentContextRequest
    ) -> GetLearningComponentContextResult:
        """Return the standards one exact learning component supports.

        Parameters
        ----------
        request
            Framework selection and the exact learning-component node identifier.

        Returns
        -------
        GetLearningComponentContextResult
            Supported standards in deterministic relationship order.

        Raises
        ------
        LearningComponentNotFoundError
            If the identifier is unavailable or selects another node kind.
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
            graph_result = store.get_node_by_id(request.node_id)
        except GraphNodeNotFoundError as error:
            raise LearningComponentNotFoundError(
                details={
                    "graph_package_id": str(package.package_identity.graph_package_id)
                },
                message="The requested learning component identifier is unavailable.",
            ) from error

        node = self._require_component(
            graph_package_id=package.package_identity.graph_package_id,
            node=graph_result.node,
        )
        supported = self._supported_standards(component_id=node.node_id, store=store)
        return GetLearningComponentContextResult(
            node=node,
            package=package,
            placements=self._placements(
                ancestor_depth=request.ancestor_depth, store=store, supported=supported
            ),
            source_metadata=snapshot.source_metadata,
            supported_standards=supported,
        )

    def get_learning_components_for_standard(
        self, request: GetLearningComponentsForStandardRequest
    ) -> GetLearningComponentsForStandardResult:
        """Return every learning component supporting one exact standard.

        Each component reports every standard it supports, not only the requested one.

        Parameters
        ----------
        request
            Framework selection and the exact standard node identifier.

        Returns
        -------
        GetLearningComponentsForStandardResult
            Supporting components in deterministic relationship order.

        Raises
        ------
        LearningComponentNotFoundError
            If the identifier is unavailable or does not select a standard.
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
            else:
                graph_result = store.get_node_by_case_identifier_uri(
                    request.identifier.case_identifier_uri
                )
        except GraphNodeNotFoundError as error:
            raise LearningComponentNotFoundError(
                details={
                    "graph_package_id": str(package.package_identity.graph_package_id)
                },
                message="The requested standard identifier is unavailable.",
            ) from error

        standard = graph_result.node

        if not isinstance(standard, StandardNode):
            raise LearningComponentNotFoundError(
                details={
                    "graph_package_id": str(package.package_identity.graph_package_id)
                },
                message="The requested identifier does not select a standard item node.",
            )

        relationships: tuple[GraphRelationship, ...] = (
            store.incoming_by_type_and_node.get(
                (DELIVERY_SCHEMA_1_1_SUPPORTS_RELATIONSHIP_TYPE, standard.node_id), ()
            )
        )
        components: list[SupportingLearningComponent] = []

        for relationship in sorted(relationships, key=graph_relationship_order_key):
            component = store.nodes_by_id[relationship.source_node_id]

            if not isinstance(component, LearningComponentNode):
                continue

            components.append(
                SupportingLearningComponent(
                    node=component,
                    relationship=relationship,
                    supported_standards=tuple(
                        SupportedStandardReference(
                            grade_levels=supported.standard.grade_level or (),
                            node_id=supported.standard.node_id,
                            statement_code=supported.standard.statement_code,
                            support_confidence=supported.relationship.support_confidence,
                        )
                        for supported in self._supported_standards(
                            component_id=component.node_id, store=store
                        )
                    ),
                )
            )

        return GetLearningComponentsForStandardResult(
            components=tuple(components),
            package=package,
            source_metadata=snapshot.source_metadata,
            standard=standard,
        )


def _node_label(node: GraphNode) -> str:
    """Return one short human-readable label for a node in a hierarchy path.

    Parameters
    ----------
    node
        Decoded framework, framework-item, or learning-component node.

    Returns
    -------
    str
        Statement code when present, otherwise the node's description or name.
    """

    statement_code = getattr(node, "statement_code", None)

    if statement_code:
        return str(statement_code)

    return str(getattr(node, "description", None) or getattr(node, "name", "") or "")
