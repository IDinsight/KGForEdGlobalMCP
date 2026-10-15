"""Synthetic topology with accepted evidence shapes and the real byte encoder."""

# Standard Library
import hashlib
import json

from collections import defaultdict, deque
from types import SimpleNamespace
from typing import Any, TypedDict, cast

# Third Party Library
from pydantic import TypeAdapter

# Package Library
from kgfegmcp.bootstrap import AppState
from kgfegmcp.catalog.models import CatalogPackageRuntime
from kgfegmcp.domain.identifiers import (
    ArtifactName,
    FrameworkId,
    RelationshipId,
    SnapshotId,
)
from kgfegmcp.services.learning_progressions import LearningProgressionsService
from kgfegmcp.services.lp_compact import rehydrate_relationships
from kgfegmcp.services.lp_models import (
    GetLearningProgressionPathsRequest,
    ProgressionRelationshipEvidence,
    TraverseLearningProgressionsRequest,
)
from kgfegmcp.services.lp_paths import paths_result
from kgfegmcp.services.lp_traversal import traversal_adjacency, traversal_result
from kgfegmcp.services.models import NodeIdStandardIdentifier


def selector(node: str) -> NodeIdStandardIdentifier:
    """Select one exact outer node ID."""
    return NodeIdStandardIdentifier(identifier_type="node_id", node_id=node)


class PackageRoute(TypedDict):
    """Exact immutable framework/snapshot keyword pair for resource calls."""

    framework_id: FrameworkId
    snapshot_id: SnapshotId


def package_route(runtime: CatalogPackageRuntime) -> PackageRoute:
    """Pin the exact accepted framework/snapshot pair of one runtime."""
    identity = runtime.catalog_package.package_identity
    return {"framework_id": identity.framework_id, "snapshot_id": identity.snapshot_id}


def relationship_id(value: str) -> RelationshipId:
    """Validate a literal relationship ID through the production identifier type."""
    return TypeAdapter(RelationshipId).validate_python(value)


def artifact_name(value: str) -> ArtifactName:
    """Validate a literal artifact name through the production identifier type."""
    return TypeAdapter(ArtifactName).validate_python(value)


class Topology:
    """Supply in-memory original-edge shapes; never claim package acceptance."""

    def __init__(
        self, state: AppState, spec: list[tuple[str, str, str, str, str]]
    ) -> None:
        """Build deterministic synthetic nodes and immutable sorted adjacency."""
        runtime = state.catalog_load_result.package_runtimes[0]
        self.service = state.learning_progressions_service
        base = next(
            e
            for e in runtime.loaded_package.relationships
            if e.label == "buildsTowards"
        )
        node = runtime.loaded_package.item_nodes[0]
        # Production metadata is compact (four derivation artifacts), so synthetic
        # topology now carries it unchanged.
        self.metadata = self.service.evidence_metadata(runtime=runtime)
        self.summary = self.service.standard_summary(node=node, runtime=runtime)
        self.evidence = self.service.relationship_evidence(
            relationship=base, runtime=runtime
        )
        self.edges = {
            identifier: base.model_copy(
                update={
                    "relationship_id": identifier,
                    "source_node_id": source,
                    "target_node_id": target,
                    "label": label,
                    "attribution_statement": text,
                }
            )
            for identifier, source, target, label, text in spec
        }
        ids = {"a", "t"} | {
            key
            for edge in self.edges.values()
            for key in (edge.source_node_id, edge.target_node_id)
        }
        self.nodes = {key: node.model_copy(update={"node_id": key}) for key in ids}
        incoming: dict[Any, list[Any]] = defaultdict(list)
        outgoing: dict[Any, list[Any]] = defaultdict(list)
        for edge in self.edges.values():
            incoming[(edge.label, edge.target_node_id)].append(edge)
            outgoing[(edge.label, edge.source_node_id)].append(edge)
        self.runtime = SimpleNamespace(
            graph_store=SimpleNamespace(
                nodes_by_id=self.nodes,
                relationships_by_id=self.edges,
                incoming_by_type_and_node=incoming,
                outgoing_by_type_and_node=outgoing,
            )
        )
        # The namespace double supplies only the graph_store indexes the real
        # algorithms read; the cast states that interface for the type checker.
        self.adjacency = traversal_adjacency(
            runtime=cast(CatalogPackageRuntime, self.runtime)
        )

    # These doubles retain the production service keyword signatures.
    # pylint: disable=unused-argument
    def resolve_standard(self, *, identifier: Any, runtime: Any) -> Any:
        """Resolve one known synthetic standard."""
        return self.nodes[identifier.node_id]

    def evidence_metadata(self, *, runtime: Any) -> Any:
        """Supply representative synthetic metadata while testing topology only."""
        return self.metadata

    def standard_summary(self, *, node: Any, runtime: Any) -> Any:
        """Project a synthetic ID into the accepted standard summary shape."""
        return self.summary.model_copy(update={"node_id": node.node_id})

    def relationship_evidence(self, *, relationship: Any, runtime: Any) -> Any:
        """Retain the whole supplied edge and matching judgment identifier."""
        return self.evidence.model_copy(
            update={
                "relationship": relationship,
                "judgment": self.evidence.judgment.model_copy(
                    update={"relationship_id": relationship.relationship_id}
                ),
            }
        )

    # pylint: enable=unused-argument

    def require_traversal_result_size(self, *, result: Any) -> int:
        """Execute the production traversal envelope encoder."""
        return self.service.require_traversal_result_size(result=result)

    def require_paths_result_size(self, *, result: Any) -> int:
        """Execute the production path envelope encoder."""
        return self.service.require_paths_result_size(result=result)

    def walk(self, origin: str = "a", /, **limits: Any) -> Any:
        """Execute real bounded BFS with the supplied topology."""
        request = TraverseLearningProgressionsRequest(
            framework_id="synthetic", identifier=selector(origin), **limits
        )
        return traversal_result(
            adjacency=self.adjacency,
            request=request,
            runtime=cast(CatalogPackageRuntime, self.runtime),
            # This double keeps the service methods the algorithm calls.
            service=cast(LearningProgressionsService, self),
        )

    def paths(self, source: str = "a", target: str = "t", **limits: Any) -> Any:
        """Execute real bounded simple paths with the supplied topology."""
        request = GetLearningProgressionPathsRequest(
            framework_id="synthetic",
            source_identifier=selector(source),
            target_identifier=selector(target),
            **limits,
        )
        return paths_result(
            adjacency=self.adjacency,
            request=request,
            runtime=cast(CatalogPackageRuntime, self.runtime),
            # This double keeps the service methods the algorithm calls.
            service=cast(LearningProgressionsService, self),
        )


def builds(
    pairs: list[tuple[str, str, str]], text: str = "original attribution"
) -> list[tuple[str, str, str, str, str]]:
    """Make explicit builds-only test edges without hierarchy semantics."""
    return [
        (identifier, source, target, "buildsTowards", text)
        for identifier, source, target in pairs
    ]


# Liftable evidence fields by nesting level, as the cycle design names them (JSON keys).
LIFTABLE_JSON_FIELDS: dict[str | None, tuple[str, ...]] = {
    None: ("epistemicStatus",),
    "judgment": ("confidenceNotice",),
    "relationship": (
        "attributionStatement",
        "author",
        "description",
        "label",
        "license",
        "provider",
        "relationshipType",
        "sourceEntity",
        "sourceEntityKey",
        "sourceLabels",
        "targetEntity",
        "targetEntityKey",
        "targetLabels",
    ),
}


def assert_compact_form(
    *, expected: tuple[ProgressionRelationshipEvidence, ...], result: Any
) -> None:
    """Check the emitted compact form against the full evidence it must encode.

    Working on the emitted JSON, a liftable field appears once in
    ``sharedRelationshipEvidence`` exactly when every entry's full value is the same
    non-null value, and is then absent from every entry. Otherwise each entry carries
    its own non-null value and omits a null one. Every other field is emitted per
    entry unchanged, so no information is lost.

    Parameters
    ----------
    expected
        Full evidence per entry, in result order.
    result
        Compact progression result to check.
    """

    emitted = result.model_dump(by_alias=True, mode="json")
    shared = emitted["sharedRelationshipEvidence"]
    entries = emitted["relationships"]
    full = [item.model_dump(by_alias=True, mode="json") for item in expected]
    assert len(entries) == len(full)

    for level, names in LIFTABLE_JSON_FIELDS.items():
        shared_level = shared if level is None else shared.get(level, {})
        full_levels = [item if level is None else item[level] for item in full]
        compact_levels = [item if level is None else item[level] for item in entries]

        for name in names:
            values = [item[name] for item in full_levels]
            lifted = bool(values) and values[0] is not None
            lifted = lifted and all(value == values[0] for value in values)
            assert shared_level.get(name) == (values[0] if lifted else None)

            for compact, value in zip(compact_levels, values):
                assert compact.get(name) == (None if lifted else value)
                assert (name in compact) == (not lifted and value is not None)

        for compact, original in zip(compact_levels, full_levels):
            kept = set(original) - set(names) - {"judgment", "relationship"}
            assert {key: compact[key] for key in kept} == {
                key: original[key] for key in kept
            }
            assert set(compact) <= set(original)

    # Nothing else is shared; the object is {} when nothing lifts.
    assert set(shared) <= {"epistemicStatus", "judgment", "relationship"}


def assert_path_invariants(
    *,
    request: GetLearningProgressionPathsRequest,
    result: Any,
    runtime: CatalogPackageRuntime,
    service: LearningProgressionsService,
) -> None:
    """Check the design's path result invariants against the stored package edges.

    Every returned path and a present ``nextUnreturnedPath`` must run from the source
    to the target over stored buildsTowards edges within ``max_depth``; paths must be
    distinct and ordered by hop count, then relationship-ID tuple; the rehydrated
    relationship table must equal, in first-appearance order, the evidence
    ``relationship_evidence`` builds for the union of the returned paths' edges; and
    an incomplete result must say so.

    Parameters
    ----------
    request
        The path request that produced ``result``.
    result
        Compact ``GetLearningProgressionPathsResult`` to check.
    runtime
        Accepted package runtime the request was pinned to.
    service
        Production service whose ``relationship_evidence`` is the expected evidence.
    """

    stored = runtime.graph_store.relationships_by_id
    unreturned = result.next_unreturned_path
    keys = []

    for path in (*result.paths, *((unreturned,) if unreturned else ())):
        assert (path.node_ids[0], path.node_ids[-1]) == (
            result.source_node_id,
            result.target_node_id,
        )
        assert 1 <= len(path.relationship_ids) <= request.max_depth
        assert len(path.node_ids) == len(path.relationship_ids) + 1

        for index, edge_id in enumerate(path.relationship_ids):
            edge = stored[edge_id]
            assert edge.label == "buildsTowards"
            assert (edge.source_node_id, edge.target_node_id) == (
                path.node_ids[index],
                path.node_ids[index + 1],
            )

        keys.append((len(path.relationship_ids), path.relationship_ids))

    # Returned paths, then any unreturned one, follow the shared total order.
    assert keys == sorted(keys) and len(keys) == len(set(keys))
    table = list(
        dict.fromkeys(
            edge_id for path in result.paths for edge_id in path.relationship_ids
        )
    )
    expected = tuple(
        service.relationship_evidence(relationship=stored[key], runtime=runtime)
        for key in table
    )
    assert rehydrated(result) == expected
    assert_compact_form(expected=expected, result=result)

    if not result.truncation_reasons:
        assert result.graph_exhausted and unreturned is None


def baseline_paths(
    *,
    downstream: dict[str, list[tuple[str, str]]],
    max_depth: int,
    max_paths: int,
    source: str,
    target: str,
) -> tuple[list[tuple[tuple[str, ...], tuple[str, ...]]], set[str]]:
    """Reference copy of the cycle-baseline breadth-first path enumerator.

    It mirrors ``services/lp_paths.py`` at ``f9fdaa2``: per-path visited sets, edges in
    relationship-ID order, a 5,000 inspection and 5,000 state budget, ``depth_limit``
    on any extension beyond ``max_depth``, and ``path_limit`` when ``max_paths`` paths
    are admitted with states still queued. Output-size stops are not modelled.

    Parameters
    ----------
    downstream
        Source node ID to its ``(relationship_id, target_node_id)`` buildsTowards
        edges, sorted by relationship ID.
    max_depth
        Requested maximum hop count.
    max_paths
        Requested maximum number of paths.
    source
        Path source node ID.
    target
        Path target node ID.

    Returns
    -------
    tuple[list[tuple[tuple[str, ...], tuple[str, ...]]], set[str]]
        Admitted ``(relationship_ids, node_ids)`` paths in order, and the truncation
        reasons the baseline would report apart from ``byte_limit``.
    """

    budget = 5000
    enqueued = 1
    examined = 0
    paths: list[tuple[tuple[str, ...], tuple[str, ...]]] = []
    queue: deque[tuple[tuple[str, ...], tuple[str, ...]]] = deque([((), (source,))])
    reasons: set[str] = set()

    while queue:
        edges, nodes = queue.popleft()

        if nodes[-1] == target:
            paths.append((edges, nodes))

            if len(paths) == max_paths and queue:
                reasons.add("path_limit")
                break

            continue

        for edge_id, head in downstream.get(nodes[-1], []):
            if examined == budget:
                reasons.add("work_limit")
                return paths, reasons

            examined += 1

            if head in nodes:
                continue

            if len(edges) == max_depth:
                reasons.add("depth_limit")
                continue

            if enqueued == budget:
                reasons.add("queue_limit")
                return paths, reasons

            queue.append(((*edges, edge_id), (*nodes, head)))
            enqueued += 1

    return paths, reasons


def rehydrated(result: Any) -> tuple[ProgressionRelationshipEvidence, ...]:
    """Rebuild full relationship evidence from a compact LP result.

    Parameters
    ----------
    result
        Any compact progression result.

    Returns
    -------
    tuple[ProgressionRelationshipEvidence, ...]
        Full evidence per entry, in result order.
    """

    return rehydrate_relationships(
        relationships=result.relationships,
        shared=result.shared_relationship_evidence,
    )


# Meaning-bearing node properties; serialization, key order and added fields are ignored.
SEMANTIC_NODE_PROPERTIES = (
    "caseIdentifierUUID",
    "description",
    "gradeLevel",
    "name",
    "normalizedStatementType",
    "statementCode",
    "statementType",
)


def semantic_baseline(
    nodes: list[dict[str, Any]], relationships: list[dict[str, Any]]
) -> dict[str, Any]:
    """Summarize AS/LC identity, text and structural edges independent of bytes."""

    def digest(rows: list[Any]) -> str:
        """Hash sorted canonical JSON so record order and formatting do not matter."""
        canonical = json.dumps(sorted(rows), ensure_ascii=False, separators=(",", ":"))
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()

    node_rows = [
        [
            row["identifier"],
            sorted(row["labels"]),
            {
                key: row["properties"][key]
                for key in SEMANTIC_NODE_PROPERTIES
                if key in row["properties"]
            },
        ]
        for row in nodes
    ]
    summary: dict[str, Any] = {
        "nodeCount": len(node_rows),
        "nodesDigest": digest(node_rows),
    }
    # LP edges are excluded: only hierarchy and component support must be preserved.
    for label in ("hasChild", "supports"):
        edges = [
            [row["identifier"], row["source_identifier"], row["target_identifier"]]
            for row in relationships
            if row["label"] == label
        ]
        summary[f"{label}Count"] = len(edges)
        summary[f"{label}Digest"] = digest(edges)
    return summary
