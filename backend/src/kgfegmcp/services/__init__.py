"""This package exposes the canonical application-service contracts.

The services package is the application orchestration layer between protocol adapters
and the existing catalog, graph, traversal, search, package, and profile domains. Its
services translate complete application requests into calls to those existing domain
boundaries and assemble immutable results for callers such as the FastMCP tools.

Importing this package exposes approved request models, result models, and service
classes. It does not construct settings, load or validate graph packages, access the
filesystem, build graph or search indexes, start FastMCP, or register MCP components.
"""

# Package Library
from kgfegmcp.services.capabilities import CapabilitiesService
from kgfegmcp.services.comparison import ComparisonService
from kgfegmcp.services.comparison_models import (
    CompareFrameworkEvidenceResult,
    ComparisonMatchEvidence,
    ComparisonRequestSummary,
    ComparisonWarning,
    ComparisonWarningCode,
    ExactCodeFrameworkComparisonRequest,
    FrameworkComparisonRequest,
    FrameworkComparisonSection,
    PrefixCodeFrameworkComparisonRequest,
    TextFrameworkComparisonRequest,
)
from kgfegmcp.services.frameworks import FrameworkService
from kgfegmcp.services.models import (
    CaseUriStandardIdentifier,
    CaseUuidStandardIdentifier,
    CodePresenceStatistics,
    ContextRelationshipStatus,
    DepthCount,
    ExactCodeStandardsSearchRequest,
    FrameworkCursor,
    FrameworkStatistics,
    GetCapabilitiesResult,
    GetFrameworkRequest,
    GetFrameworkResult,
    GetFrameworkStatisticsRequest,
    GetFrameworkStatisticsResult,
    GetStandardContextRequest,
    GetStandardContextResult,
    GetStandardRequest,
    GetStandardResult,
    ListFrameworksRequest,
    ListFrameworksResult,
    MultiParentStatistics,
    NodeIdStandardIdentifier,
    NullableValueCount,
    PackageCapabilityResult,
    ParentCountBucket,
    PrefixCodeStandardsSearchRequest,
    SearchStandardsResult,
    StandardsSearchRequest,
    TextStandardsSearchRequest,
    UnresolvedRelationshipStatistics,
)
from kgfegmcp.services.standards import StandardsService
from kgfegmcp.services.statistics import FrameworkStatisticsService

__all__ = [
    "CapabilitiesService",
    "CaseUriStandardIdentifier",
    "CaseUuidStandardIdentifier",
    "CodePresenceStatistics",
    "CompareFrameworkEvidenceResult",
    "ComparisonMatchEvidence",
    "ComparisonRequestSummary",
    "ComparisonService",
    "ComparisonWarning",
    "ComparisonWarningCode",
    "ContextRelationshipStatus",
    "DepthCount",
    "ExactCodeFrameworkComparisonRequest",
    "ExactCodeStandardsSearchRequest",
    "FrameworkComparisonRequest",
    "FrameworkComparisonSection",
    "FrameworkCursor",
    "FrameworkService",
    "FrameworkStatistics",
    "FrameworkStatisticsService",
    "GetCapabilitiesResult",
    "GetFrameworkRequest",
    "GetFrameworkResult",
    "GetFrameworkStatisticsRequest",
    "GetFrameworkStatisticsResult",
    "GetStandardContextRequest",
    "GetStandardContextResult",
    "GetStandardRequest",
    "GetStandardResult",
    "ListFrameworksRequest",
    "ListFrameworksResult",
    "MultiParentStatistics",
    "NodeIdStandardIdentifier",
    "NullableValueCount",
    "PackageCapabilityResult",
    "ParentCountBucket",
    "PrefixCodeFrameworkComparisonRequest",
    "PrefixCodeStandardsSearchRequest",
    "SearchStandardsResult",
    "StandardsSearchRequest",
    "StandardsService",
    "TextFrameworkComparisonRequest",
    "TextStandardsSearchRequest",
    "UnresolvedRelationshipStatistics",
]
