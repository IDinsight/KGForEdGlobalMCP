"""This module contains framework-independent enumerations used across the domain.

This module defines the fixed vocabularies shared by package validation, curriculum
profiles, graph services, search services, resources, and public results. These
enumerations provide stable values for graph types, validation states, rights review,
subject mappings, code availability, snapshot relations, and the evidentiary status of
claims.

The values in this module are intentionally curriculum-agnostic. Local curriculum
terminology, grade systems, hierarchy labels, and code conventions belong in versioned
interpretation profiles rather than additional curriculum-specific enum members.
"""

# Standard Library
from enum import StrEnum


class CodeAvailability(StrEnum):
    """Describe how completely statement codes are available in a framework."""

    COMPLETE = "complete"
    NONE = "none"
    PARTIAL = "partial"


class DerivativeGenerationPolicy(StrEnum):
    """Describe whether generated derivatives are allowed by operator policy."""

    ALLOWED = "allowed"
    PROHIBITED = "prohibited"
    REVIEW_REQUIRED = "review_required"


class EpistemicStatus(StrEnum):
    """Classify the evidentiary status of a result or claim."""

    ACCEPTED_DERIVED = "accepted_derived"
    DETERMINISTIC_DERIVED = "deterministic_derived"
    HUMAN_REVIEWED = "human_reviewed"
    LLM_INFERRED = "llm_inferred"
    RETRIEVAL_CANDIDATE = "retrieval_candidate"
    SOURCE_ASSERTED = "source_asserted"
    SOURCE_EXTRACTED = "source_extracted"
    UNRESOLVED = "unresolved"


class GraphType(StrEnum):
    """Identify a graph domain supported by a graph package."""

    ACADEMIC_STANDARDS = "academic_standards"
    ASSESSMENT = "assessment"
    CURRICULUM = "curriculum"
    LEARNING_COMPONENTS = "learning_components"
    LEARNING_PROGRESSIONS = "learning_progressions"
    REVIEWED_ALIGNMENT = "reviewed_alignment"


class InvalidPackagePolicy(StrEnum):
    """Control startup behavior when a graph package is invalid."""

    FAIL = "fail"
    QUARANTINE = "quarantine"


class NormalizedStatementType(StrEnum):
    """Represent Learning Commons-shaped statement classifications."""

    STANDARD = "Standard"
    STANDARD_GROUPING = "Standard Grouping"


class RightsReviewStatus(StrEnum):
    """Describe the operator review status of a package rights policy."""

    APPROVED = "approved"
    PROVISIONAL_OPERATOR_APPROVED = "provisional_operator_approved"
    RESTRICTED = "restricted"
    REVIEW_REQUIRED = "review_required"
    UNREVIEWED = "unreviewed"


class SnapshotRelationType(StrEnum):
    """Describe an operator-supplied relationship between immutable snapshots."""

    DERIVED_FROM = "derived_from"
    REPLACES = "replaces"
    REVISES = "revises"
    SUPERSEDES = "supersedes"


class SubjectMappingStatus(StrEnum):
    """Describe whether a local subject has a reviewed normalized mapping."""

    MAPPED = "mapped"
    OTHER = "other"
    UNREVIEWED = "unreviewed"


class ValidationStatus(StrEnum):
    """Describe the validation state of a graph package."""

    FAILED = "failed"
    PASSED = "passed"
    PENDING = "pending"
    QUARANTINED = "quarantined"
