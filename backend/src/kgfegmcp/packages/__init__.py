"""This package contains immutable curriculum graph-package contracts and
package-boundary services.

This package defines the boundary between accepted curriculum graph artifacts and the
application services that consume them. A graph package represents one immutable,
versioned snapshot containing delivery artifacts, optional detailed artifacts,
framework metadata, checksums, counts, validation state, rights policy, and a reference
to its curriculum interpretation profile.

The package layer is responsible for describing, loading, verifying, and validating
graph packages without changing their source nodes or relationships. It preserves exact
framework and snapshot identities so that graph retrieval, comparison, provenance, and
audit results remain reproducible.

Curriculum-specific meaning does not belong in this package. Local grade semantics,
statement-type interpretation, hierarchy conventions, and code policies are supplied
through versioned profiles (i.e., the ``profiles`` package). Package services use those
profiles during validation but remain general across jurisdictions, subjects,
languages, grade systems, and graph topologies.
"""

# Package Library
from kgfegmcp.packages.models import (
    FrameworkCapabilities,
    FrameworkMetadata,
    GraphPackageManifest,
    PackageArtifacts,
    PackageCounts,
    PackageValidation,
    ProfileReference,
    SnapshotRelation,
)

__all__ = [
    "FrameworkCapabilities",
    "FrameworkMetadata",
    "GraphPackageManifest",
    "PackageArtifacts",
    "PackageCounts",
    "PackageValidation",
    "ProfileReference",
    "SnapshotRelation",
]
