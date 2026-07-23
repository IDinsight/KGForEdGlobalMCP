"""This package exposes immutable catalog contracts, construction, selection, and graph
routing.

The catalog federates accepted graph packages by exact framework and snapshot identity
while retaining one independent graph store per package. It does not merge source graph
namespaces, infer framework relationships, implement search, or depend on FastMCP.
"""

# Package Library
from kgfegmcp.catalog.models import (
    CatalogFrameworkFamily,
    CatalogFrameworkSnapshot,
    CatalogGraphPackage,
    CatalogLoadResult,
    CatalogPackageRuntime,
    CatalogProfileFacets,
    CatalogResult,
    CatalogSourceMetadata,
)
from kgfegmcp.catalog.repository import CatalogRepository
from kgfegmcp.catalog.service import CatalogService

__all__ = [
    "CatalogFrameworkFamily",
    "CatalogFrameworkSnapshot",
    "CatalogGraphPackage",
    "CatalogLoadResult",
    "CatalogPackageRuntime",
    "CatalogProfileFacets",
    "CatalogRepository",
    "CatalogResult",
    "CatalogService",
    "CatalogSourceMetadata",
]
