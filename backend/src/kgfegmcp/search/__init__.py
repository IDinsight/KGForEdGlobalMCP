"""This package exposes the public API for deterministic package-scoped search.

The search package provides immutable request, result, evidence, warning, cursor, and
index-metadata models together with the `SearchService` entry point. It supports
lexical description search and profile-governed statement-code search over graph
packages that have already been accepted by the catalog.

Search indexes remain independently owned by their exact graph packages. The package
does not merge node, relationship, identifier, code, or lexical namespaces across
packages. Federated search combines completed package-local results only after each
selected package has been searched independently.

Importing this package does not load settings, access the filesystem, validate
packages, configure logging, construct graph stores, or build search indexes. Search
construction begins explicitly from a complete
`kgfegmcp.catalog.models.CatalogLoadResult`.
"""

# Package Library
from kgfegmcp.search.models import (
    CodeMatchEvidence,
    CodeParentDerivationEvidence,
    CodeParentDerivationStatus,
    CodeScopeEvidence,
    ExactCodeSearchQuery,
    ExactPackageSearchScope,
    ExactPhraseTextMatch,
    FederatedPackageSearchScope,
    PackageSearchIndexMetadata,
    PackageSearchScope,
    PrefixCodeSearchQuery,
    SearchCursor,
    SearchFacetEvidence,
    SearchField,
    SearchFilters,
    SearchHit,
    SearchIndexMetadata,
    SearchMatchedField,
    SearchMode,
    SearchPage,
    SearchQuery,
    SearchScore,
    SearchScoreAlgorithm,
    SearchSelectionMode,
    SearchWarning,
    SearchWarningCode,
    TextMatch,
    TextMatchMode,
    TextOperator,
    TextSearchQuery,
    TokenTextMatch,
)
from kgfegmcp.search.service import SearchService

__all__ = [
    "CodeMatchEvidence",
    "CodeParentDerivationEvidence",
    "CodeParentDerivationStatus",
    "CodeScopeEvidence",
    "ExactCodeSearchQuery",
    "ExactPackageSearchScope",
    "ExactPhraseTextMatch",
    "FederatedPackageSearchScope",
    "PackageSearchIndexMetadata",
    "PackageSearchScope",
    "PrefixCodeSearchQuery",
    "SearchCursor",
    "SearchFacetEvidence",
    "SearchField",
    "SearchFilters",
    "SearchHit",
    "SearchIndexMetadata",
    "SearchMatchedField",
    "SearchMode",
    "SearchPage",
    "SearchQuery",
    "SearchScore",
    "SearchScoreAlgorithm",
    "SearchSelectionMode",
    "SearchService",
    "SearchWarning",
    "SearchWarningCode",
    "TextMatch",
    "TextMatchMode",
    "TextOperator",
    "TextSearchQuery",
    "TokenTextMatch",
]
