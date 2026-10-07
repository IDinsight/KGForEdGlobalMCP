"""Synthetic topology with validated evidence shapes and the real byte encoder."""

# Standard Library
import hashlib
import json

from collections import defaultdict
from pathlib import Path
from types import SimpleNamespace
from typing import Any, TypedDict, cast

# Third Party Library
from pydantic import TypeAdapter

# Package Library
from kgfegmcp.catalog.models import CatalogPackageRuntime
from kgfegmcp.domain.identifiers import (
    ArtifactName,
    FrameworkId,
    RelationshipId,
    SnapshotId,
)
from kgfegmcp.graph.models import StandardNode
from kgfegmcp.services.learning_progressions import (
    LearningProgressionsService,
    progression_result_text,
    require_progression_result_size,
)
from kgfegmcp.services.lp_models import (
    GetLearningProgressionPathsRequest,
    ProgressionMetadata,
    ProgressionRelationshipEvidence,
    ProgressionStandardSummary,
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

    def __init__(self, spec: list[tuple[str, str, str, str, str]]) -> None:
        """Build synthetic evidence without bootstrapping installed graph packages."""
        seed = json.loads(
            Path(__file__)
            .with_name("synthetic_progression_evidence.json")
            .read_text(encoding="utf-8")
        )
        self.metadata = ProgressionMetadata.model_validate(seed["metadata"]).model_copy(
            update={
                "stored_builds_towards_count": sum(
                    row[3] == "buildsTowards" for row in spec
                ),
                "stored_relates_to_count": sum(row[3] == "relatesTo" for row in spec),
            }
        )
        self.summary = ProgressionStandardSummary.model_validate(seed["summary"])
        self.evidence = ProgressionRelationshipEvidence.model_validate(seed["evidence"])
        base = self.evidence.relationship
        node = StandardNode(
            labels=("StandardsFrameworkItem",), node_id="a", source_export_order=1
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
        return self.summary.model_copy(
            update={
                "node_id": node.node_id,
                "standard_uri": f"test://synthetic/standards/{node.node_id}",
            }
        )

    def relationship_evidence(self, *, relationship: Any, runtime: Any) -> Any:
        """Retain the whole supplied edge and matching judgment identifier."""
        return self.evidence.model_copy(
            update={
                "relationship": relationship,
                "relationship_uri": f"test://synthetic/relationships/{relationship.relationship_id}",
                "provenance_uri": f"test://synthetic/provenance/{relationship.relationship_id}",
                "judgment": self.evidence.judgment.model_copy(
                    update={"relationship_id": relationship.relationship_id}
                ),
            }
        )

    # pylint: enable=unused-argument

    def require_traversal_result_size(self, *, result: Any) -> int:
        """Execute the production traversal envelope encoder."""
        return require_progression_result_size(
            result=result, text=progression_result_text(result=result)
        )

    def require_paths_result_size(self, *, result: Any) -> int:
        """Execute the production path envelope encoder."""
        return require_progression_result_size(
            result=result, text=progression_result_text(result=result)
        )

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


def assert_envelope_bounds(result: Any) -> None:
    """Independently measure complete text and structured evidence under both ceilings."""
    text = progression_result_text(result=result)
    structured = result.model_dump(by_alias=True, mode="json")
    assert json.loads(text) == structured
    serialized = json.dumps(
        {
            "_meta": None,
            "content": [{"text": text, "type": "text"}],
            "isError": False,
            "structuredContent": structured,
        },
        ensure_ascii=False,
        sort_keys=True,
    )
    assert len(serialized) <= 100000
    assert len(serialized.encode("utf-8")) <= 1048576


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
