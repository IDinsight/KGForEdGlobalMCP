"""This package exposes curriculum-agnostic graph records, storage, and traversal
contracts.

The package preserves decoded source records and provides one immutable in-memory store
per successfully validated package. Exact identifier lookups, direct relationships,
bounded ancestor and descendant traversal, and complete DAG root paths remain
independent of package loading, validation, catalog routing, search, FastMCP,
resources, and prompts.
"""

# Package Library
from kgfegmcp.graph.models import (
    DirectNodeRelationshipsResult,
    DirectRelationshipDirection,
    FrameworkNode,
    GraphNeighbor,
    GraphNode,
    GraphNodeRecord,
    GraphNodeResult,
    GraphPackageIdentity,
    GraphRelationship,
    GraphTraversalDirection,
    RootPath,
    RootPathsResult,
    StandardNode,
    TraversalNode,
    TraversalResult,
    TraversalTruncationReason,
)
from kgfegmcp.graph.store import GraphStore
from kgfegmcp.graph.traversal import GraphTraversal

__all__ = [
    "DirectNodeRelationshipsResult",
    "DirectRelationshipDirection",
    "FrameworkNode",
    "GraphNeighbor",
    "GraphNode",
    "GraphNodeRecord",
    "GraphNodeResult",
    "GraphPackageIdentity",
    "GraphRelationship",
    "GraphStore",
    "GraphTraversal",
    "GraphTraversalDirection",
    "RootPath",
    "RootPathsResult",
    "StandardNode",
    "TraversalNode",
    "TraversalResult",
    "TraversalTruncationReason",
]
