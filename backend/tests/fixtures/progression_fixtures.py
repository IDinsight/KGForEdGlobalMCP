"""Synthetic topology with accepted evidence shapes and the real byte encoder."""

# Standard Library
import hashlib
import json

from collections import defaultdict
from types import SimpleNamespace
from typing import Any

# Package Library
from kgfegmcp.bootstrap import AppState
from kgfegmcp.services.lp_models import (
    GetLearningProgressionPathsRequest,
    TraverseLearningProgressionsRequest,
)
from kgfegmcp.services.lp_paths import paths_result
from kgfegmcp.services.lp_traversal import traversal_adjacency, traversal_result
from kgfegmcp.services.models import NodeIdStandardIdentifier


def selector(node: str) -> NodeIdStandardIdentifier:
    """Select one exact outer node ID."""
    return NodeIdStandardIdentifier(identifier_type="node_id", node_id=node)


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
        self.adjacency = traversal_adjacency(runtime=self.runtime)

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
            runtime=self.runtime,
            service=self,
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
            runtime=self.runtime,
            service=self,
        )


def builds(
    pairs: list[tuple[str, str, str]], text: str = "original attribution"
) -> list[tuple[str, str, str, str, str]]:
    """Make explicit builds-only test edges without hierarchy semantics."""
    return [
        (identifier, source, target, "buildsTowards", text)
        for identifier, source, target in pairs
    ]


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
