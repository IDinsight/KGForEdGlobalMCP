"""This package provides curriculum-agnostic semantic records for decoded graph data.

The package contains immutable models representing nodes and relationships after
delivery-specific JSONL values have been parsed and decoded. These models form the
boundary between source-shaped wire records and graph services such as validation,
storage, traversal, and search.

The package preserves original property values, distinct identifier forms, relationship
endpoint representations, resolution information, and deterministic source order. It
does not currently validate graph-wide invariants, resolve relationship endpoints,
repair source records, or assume that the graph is a tree.
"""

# Package Library
from kgfegmcp.graph.models import FrameworkNode, GraphRelationship, StandardNode

__all__ = ["FrameworkNode", "GraphRelationship", "StandardNode"]
