"""This package exposes the public curriculum-agnostic read-only resource boundary.

This package provides the approved resource models, URI constructors, access policy,
accepted-artifact repository, and orchestration service used to deliver read-only
catalog and graph-package resources. Its public exports allow application and MCP
modules to use one explicit resource API without depending on internal module layout.
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
