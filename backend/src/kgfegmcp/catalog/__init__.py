"""This package exposes the public interfaces for the validated graph-package catalog.

The catalog package provides a read-only directory of graph packages that have already
passed package loading and validation. It connects package discovery, validation,
immutable catalog metadata, and per-package graph-store routing without merging package
contents or weakening package isolation.

The package is divided into three main responsibilities:

* `kgfegmcp.catalog.models` defines the immutable catalog and runtime contracts.
* `kgfegmcp.catalog.repository` discovers and validates packages, applies catalog
    inclusion rules, and constructs one graph store per accepted package.
* `kgfegmcp.catalog.service` provides deterministic in-memory selection and routing
    across the constructed catalog.

Importing this package does not load settings, configure logging, access the
filesystem, validate packages, or construct application services. Application bootstrap
code must create the required repositories and services explicitly.

The catalog does not provide lexical search, semantic inference, alignments,
cross-package traversal, FastMCP tools, resources, prompts, or application startup
behavior.
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
