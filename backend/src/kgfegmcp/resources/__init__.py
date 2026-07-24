"""This package exposes the curriculum-agnostic read-only resource boundary.

The package provides immutable resource models, closed URI constructors, rights and
size policy, checksum-verified accepted-artifact access, and a service that composes
existing catalog, graph, search, and standards behavior. Importing it performs no
filesystem access, package loading, application bootstrap, or FastMCP registration.
"""

# Package Library
from kgfegmcp.resources.models import (
    ResourceDocument,
    ResourceKind,
    ResourceMetadata,
    ResourceRepresentation,
    ResourceSourceEvidence,
    StandardProvenanceResult,
)
from kgfegmcp.resources.policy import ResourcePolicy
from kgfegmcp.resources.repository import ResourceRepository
from kgfegmcp.resources.service import ResourceService

__all__ = [
    "ResourceDocument",
    "ResourceKind",
    "ResourceMetadata",
    "ResourcePolicy",
    "ResourceRepresentation",
    "ResourceRepository",
    "ResourceService",
    "ResourceSourceEvidence",
    "StandardProvenanceResult",
]
