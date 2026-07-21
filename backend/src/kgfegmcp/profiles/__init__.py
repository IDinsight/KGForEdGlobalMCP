"""This package contains versioned curriculum interpretation profile contracts.

This package defines the configuration contracts and supporting services used to
interpret curriculum-specific terminology without embedding those semantics in generic
application code.

A curriculum profile acts as a versioned interpretation guide for one or more
frameworks. It describes local and normalized subjects, grade mappings, statement-type
meanings, hierarchy rules, code-search behavior, language policy, known source
anomalies, rights policy, and required disclosures.

Profiles supplement accepted graph packages; they do not modify source nodes or
relationships, repair source data, or assert educational equivalence. Generic catalog,
graph, search, and MCP services consume validated profiles to interpret each framework
deterministically while preserving its source terminology, topology, provenance, and
uncertainty.
"""

# Package Library
from kgfegmcp.profiles.models import (
    CodeParentRule,
    CodeSearchPolicy,
    CodeTypePolicy,
    ControlledValue,
    CurriculumProfile,
    EducationStageMapping,
    GradeMapping,
    HierarchyPolicy,
    KnownSourceAnomaly,
    LanguagePolicy,
    ParentCardinalityPolicy,
    SourceRoleCapabilities,
    StatementTypePolicy,
)

__all__ = [
    "CodeParentRule",
    "CodeSearchPolicy",
    "CodeTypePolicy",
    "ControlledValue",
    "CurriculumProfile",
    "EducationStageMapping",
    "GradeMapping",
    "HierarchyPolicy",
    "KnownSourceAnomaly",
    "LanguagePolicy",
    "ParentCardinalityPolicy",
    "SourceRoleCapabilities",
    "StatementTypePolicy",
]
