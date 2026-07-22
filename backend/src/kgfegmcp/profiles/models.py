"""This module defines Pydantic models for versioned curriculum interpretation profiles.

This module defines immutable configuration contracts that describe how generic domain
services should interpret a curriculum framework. The models represent aspects such as
subject normalization, local grade mappings, statement-type semantics, hierarchy and
parent-cardinality rules, code-search behavior, language policy, known source
anomalies, source-role capabilities, rights policy, and required disclosures.

The models deliberately keep curriculum-specific semantics in validated data rather
than generic Python conditionals. Cross-field validation ensures that statement types,
parent types, code types, hierarchy roots, subject vocabulary, and topology constraints
reference one another consistently.

These contracts do not load graph files, mutate source packages, repair source content,
or perform MCP operations. They provide deterministic interpretation metadata for
catalog, graph, search, resource, and presentation services.
"""

# Future Library
from __future__ import annotations

# Standard Library
import re

from typing import Annotated, Final, Self, cast

# Third Party Library
from pydantic import Field, StringConstraints, field_validator, model_validator

# Package Library
from kgfegmcp.domain.enums import (
    CodeAvailability,
    NormalizedStatementType,
    SubjectMappingStatus,
)
from kgfegmcp.domain.identifiers import (
    FrameworkId,
    LanguageTag,
    ProfileId,
    ProfileVersion,
    SchemaVersion,
)
from kgfegmcp.domain.models import RightsPolicy, SubjectVocabulary
from kgfegmcp.schemas import FrozenSchema

ConfigurationKey = Annotated[
    str, StringConstraints(max_length=100, min_length=1, pattern=r"^[a-z][a-z0-9_]*$")
]
PROFILE_SCHEMA_VERSION: Final[SchemaVersion] = cast(SchemaVersion, "1.0")


def _require_unique(*, field_name: str, values: tuple[str, ...]) -> None:
    """Require a tuple of strings to contain no duplicates.

    Parameters
    ----------
    field_name
        Field name used in the validation error.
    values
        String values to validate.

    Raises
    ------
    ValueError
        If duplicate values are present.
    """

    if len(values) != len(set(values)):
        raise ValueError(f"{field_name} must not contain duplicates.")


class CodeParentRule(FrozenSchema):
    """Describe a deterministic configured transformation from child to parent code."""

    child_code_type: ConfigurationKey
    method: ConfigurationKey
    parent_code_type: ConfigurationKey
    regex: str = Field(min_length=1)
    replacement: str

    @model_validator(mode="after")
    def validate_regex(self) -> Self:
        """Compile the configured regular expression.

        Returns
        -------
        Self
            Validated parent-code rule.

        Raises
        ------
        ValueError
            If the regular expression cannot be compiled.
        """

        try:
            re.compile(self.regex)
        except re.error as error:
            raise ValueError(f"Invalid code-parent regex: {error}.") from error

        return self


class CodeSearchPolicy(FrozenSchema):
    """Define deterministic exact and optional prefix code-search behavior."""

    allow_prefix_search: bool = False
    availability: CodeAvailability
    canonicalization_notes: tuple[str, ...] = ()
    case_sensitive: bool = False
    code_parent_rules: tuple[CodeParentRule, ...] = ()
    code_types: tuple[CodeTypePolicy, ...] = ()
    codes_are_unique_identifiers: bool = False
    prefix_delimiters: tuple[str, ...] = ()
    punctuation_normalization: bool = False
    whitespace_normalization: bool = False

    @model_validator(mode="after")
    def validate_code_search(self) -> Self:
        """Validate code availability, declared types, and parent rules.

        Returns
        -------
        Self
            Validated code-search policy.

        Raises
        ------
        ValueError
            If availability conflicts with code types or a rule references no type.
        """

        code_type_names = tuple(policy.code_type for policy in self.code_types)
        _require_unique(field_name="code_types", values=code_type_names)
        _require_unique(field_name="prefix_delimiters", values=self.prefix_delimiters)

        if self.availability is CodeAvailability.NONE:
            if self.code_types or self.code_parent_rules:
                raise ValueError(
                    "Code availability 'none' may not declare code types or rules."
                )

            if self.allow_prefix_search:
                raise ValueError(
                    "Code availability 'none' may not enable prefix search."
                )
        elif not self.code_types:
            raise ValueError("Coded profiles must declare at least one code type.")

        if self.allow_prefix_search and not self.prefix_delimiters:
            raise ValueError("Prefix search requires at least one delimiter.")

        declared_code_types = set(code_type_names)

        for rule in self.code_parent_rules:
            referenced_code_types = {
                str(rule.child_code_type),
                str(rule.parent_code_type),
            }
            missing_code_types = referenced_code_types - declared_code_types

            if missing_code_types:
                formatted_types = ", ".join(sorted(missing_code_types))
                raise ValueError(
                    f"Code-parent rule references undeclared types: {formatted_types}."
                )
        return self


class CodeTypePolicy(FrozenSchema):
    """Define matching and scope behavior for one configured code type."""

    code_type: ConfigurationKey
    patterns: tuple[str, ...] = Field(min_length=1)
    scope_statement_types: tuple[str, ...] = ()
    statement_types: tuple[str, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_code_type(self) -> Self:
        """Validate regular expressions and referenced statement-type uniqueness.

        Returns
        -------
        Self
            Validated code-type policy.

        Raises
        ------
        ValueError
            If a regular expression is invalid or a collection has duplicates.
        """

        for pattern in self.patterns:
            try:
                re.compile(pattern)
            except re.error as error:
                raise ValueError(
                    f"Invalid regex for code type {self.code_type}: {error}."
                ) from error

        _require_unique(
            field_name=f"{self.code_type}.scope_statement_types",
            values=self.scope_statement_types,
        )
        _require_unique(
            field_name=f"{self.code_type}.statement_types", values=self.statement_types
        )
        return self


class ControlledValue(FrozenSchema):
    """Declare one canonical curriculum value and its source-facing aliases."""

    aliases: tuple[str, ...] = ()
    canonical_value: str = Field(min_length=1)

    @model_validator(mode="after")
    def validate_aliases(self) -> Self:
        """Validate alias uniqueness.

        Returns
        -------
        Self
            Validated controlled value.
        """

        _require_unique(field_name="controlled-value aliases", values=self.aliases)
        return self


class EducationStageMapping(FrozenSchema):
    """Map a local education stage to a normalized discovery label."""

    local_label: str = Field(min_length=1)
    normalized_stage: str | None = None


class GradeMapping(FrozenSchema):
    """Map one canonical local grade label to normalized retrieval grades."""

    aliases: tuple[str, ...] = ()
    local_label: str = Field(min_length=1)
    normalized_grades: tuple[str, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_mapping(self) -> Self:
        """Validate alias and normalized-grade uniqueness.

        Returns
        -------
        Self
            Validated grade mapping.
        """

        _require_unique(field_name="grade aliases", values=self.aliases)
        _require_unique(field_name="normalized_grades", values=self.normalized_grades)
        return self


class HierarchyPolicy(FrozenSchema):
    """Describe profile-level graph topology and source hierarchy conventions."""

    allow_multi_parent: bool
    relationship_type: str = Field(default="hasChild", min_length=1)
    root_statement_types: tuple[str, ...] = Field(min_length=1)
    statement_type_order: tuple[str, ...] = ()

    @model_validator(mode="after")
    def validate_hierarchy(self) -> Self:
        """Validate hierarchy collection uniqueness.

        Returns
        -------
        Self
            Validated hierarchy policy.
        """

        _require_unique(
            field_name="root_statement_types", values=self.root_statement_types
        )
        _require_unique(
            field_name="statement_type_order", values=self.statement_type_order
        )
        return self


class KnownSourceAnomaly(FrozenSchema):
    """Record a concise interpretation warning for a known source anomaly."""

    anomaly_id: ConfigurationKey
    description: str = Field(min_length=1)
    required_disclosure: str | None = None


class LanguagePolicy(FrozenSchema):
    """Define language handling without translating or replacing source wording."""

    allow_bilingual_pairing: bool = False
    languages: tuple[LanguageTag, ...] = Field(min_length=1)
    notes: tuple[str, ...] = ()
    preserve_source_terminology: bool = True

    @model_validator(mode="after")
    def validate_languages(self) -> Self:
        """Validate language and note uniqueness.

        Returns
        -------
        Self
            Validated language policy.
        """

        _require_unique(
            field_name="languages", values=tuple(str(value) for value in self.languages)
        )
        _require_unique(field_name="language notes", values=self.notes)
        return self


class ParentCardinalityPolicy(FrozenSchema):
    """Declare the permitted number of direct parents of one statement type."""

    max_count: int | None = Field(default=None, ge=0)
    min_count: int = Field(default=0, ge=0)
    parent_statement_type: str = Field(min_length=1)

    @model_validator(mode="after")
    def validate_cardinality(self) -> Self:
        """Validate direct-parent minimum and maximum values.

        Returns
        -------
        Self
            Validated parent-cardinality policy.

        Raises
        ------
        ValueError
            If the maximum is smaller than the minimum.
        """

        if self.max_count is not None and self.max_count < self.min_count:
            raise ValueError("max_count must be greater than or equal to min_count.")

        return self


class SourceRoleCapabilities(FrozenSchema):
    """Describe source roles available beyond Academic Standards statements."""

    has_official_activities: bool = False
    has_official_assessment_guidance: bool = False
    has_official_resources: bool = False
    role_notes: tuple[str, ...] = ()


class StatementTypePolicy(FrozenSchema):
    """Interpret one source terminology statement type through profile data."""

    aliases: tuple[str, ...] = ()
    allowed_parents: tuple[ParentCardinalityPolicy, ...] = ()
    code_type: ConfigurationKey | None = None
    controlled_values: tuple[ControlledValue, ...] = ()
    description: str = Field(min_length=1)
    identity_scope: tuple[str, ...] = ()
    is_graph_node: bool = True
    normalized_statement_type: NormalizedStatementType
    source_statement_type: str = Field(min_length=1)

    @model_validator(mode="after")
    def validate_statement_type(self) -> Self:
        """Validate aliases, scopes, parent policies, and controlled values.

        Returns
        -------
        Self
            Validated statement-type policy.

        Raises
        ------
        ValueError
            If a collection contains duplicate semantic keys.
        """

        _require_unique(
            field_name=f"{self.source_statement_type}.aliases", values=self.aliases
        )
        _require_unique(
            field_name=f"{self.source_statement_type}.identity_scope",
            values=self.identity_scope,
        )
        parent_types = tuple(
            policy.parent_statement_type for policy in self.allowed_parents
        )
        _require_unique(
            field_name=f"{self.source_statement_type}.allowed_parents",
            values=parent_types,
        )
        canonical_values = tuple(
            value.canonical_value for value in self.controlled_values
        )
        _require_unique(
            field_name=f"{self.source_statement_type}.controlled_values",
            values=canonical_values,
        )
        return self


class CurriculumProfile(FrozenSchema):
    """Provide versioned curriculum semantics to generic domain services."""

    code_search_policy: CodeSearchPolicy
    comparison_dimensions: tuple[str, ...] = ()
    education_stage_mappings: tuple[EducationStageMapping, ...] = ()
    framework_ids: tuple[FrameworkId, ...] = Field(min_length=1)
    grade_level_statement_types: tuple[str, ...] = ()
    grade_mappings: tuple[GradeMapping, ...] = ()
    hierarchy: HierarchyPolicy
    known_source_anomalies: tuple[KnownSourceAnomaly, ...] = ()
    language_policy: LanguagePolicy
    local_subject: str = Field(min_length=1)
    normalized_subjects: tuple[str, ...]
    profile_id: ProfileId
    profile_schema_version: SchemaVersion = PROFILE_SCHEMA_VERSION
    profile_version: ProfileVersion
    progression_heuristics: tuple[str, ...] = ()
    required_disclosures: tuple[str, ...] = ()
    rights: RightsPolicy
    source_role_capabilities: SourceRoleCapabilities = Field(
        default_factory=SourceRoleCapabilities
    )
    statement_types: tuple[StatementTypePolicy, ...] = Field(min_length=1)
    subject_aliases: tuple[str, ...] = ()
    subject_mapping_note: str | None = None
    subject_mapping_status: SubjectMappingStatus
    subject_vocabulary: SubjectVocabulary

    @field_validator("profile_schema_version")
    @classmethod
    def validate_profile_schema_version(cls, value: SchemaVersion) -> SchemaVersion:
        """Require the exact repository-supported curriculum-profile schema version.

        Parameters
        ----------
        value
            Declared curriculum-profile schema version.

        Returns
        -------
        SchemaVersion
            The unchanged supported schema version.

        Raises
        ------
        ValueError
            If the profile declares an unsupported schema version.
        """

        if value != PROFILE_SCHEMA_VERSION:
            raise ValueError(
                f"profile_schema_version must equal {PROFILE_SCHEMA_VERSION}."
            )

        return value

    def _validate_anomaly_uniqueness(self) -> None:
        """Require known source anomalies to have unique identifiers.

        Raises
        ------
        ValueError
            If duplicate anomaly identifiers are present.
        """

        anomaly_ids = tuple(
            anomaly.anomaly_id for anomaly in self.known_source_anomalies
        )
        _require_unique(field_name="known_source_anomalies", values=anomaly_ids)

    def _validate_code_type_references(self) -> None:
        """Require statement types and code types to reference declared code types.

        Raises
        ------
        ValueError
            If a statement type references an undeclared code type or a code type
            references undeclared statement types.
        """

        statement_types_by_name = {
            policy.source_statement_type: policy for policy in self.statement_types
        }
        declared_statement_types = set(statement_types_by_name)
        declared_code_types = {
            policy.code_type for policy in self.code_search_policy.code_types
        }

        for statement_type in self.statement_types:
            if (
                statement_type.code_type is not None
                and statement_type.code_type not in declared_code_types
            ):
                raise ValueError(
                    f"{statement_type.source_statement_type} references undeclared "
                    f"code type {statement_type.code_type}."
                )

        for code_type in self.code_search_policy.code_types:
            unknown_types = set(code_type.statement_types) - declared_statement_types
            unknown_scope_types = (
                set(code_type.scope_statement_types) - declared_statement_types
            )

            if unknown_types or unknown_scope_types:
                formatted_types = ", ".join(sorted(unknown_types | unknown_scope_types))
                raise ValueError(
                    f"Code type {code_type.code_type} references undeclared "
                    f"statement types: {formatted_types}."
                )

    def _validate_declared_parents_are_graph_nodes(
        self, graph_node_types: set[str]
    ) -> None:
        """Require every declared parent reference to be a graph-node type.

        Parameters
        ----------
        graph_node_types
            Names of statement types flagged as graph nodes.

        Raises
        ------
        ValueError
            If a statement type declares a parent that is not a graph-node type.
        """

        for policy in self.statement_types:
            non_graph_parents = {
                parent.parent_statement_type
                for parent in policy.allowed_parents
                if parent.parent_statement_type not in graph_node_types
            }

            if non_graph_parents:
                formatted_types = ", ".join(sorted(non_graph_parents))
                raise ValueError(
                    f"{policy.source_statement_type} references non-node parents: "
                    f"{formatted_types}."
                )

    def _validate_hierarchy_node_policies(self) -> None:
        """Validate graph-node hierarchy roots, parents, and cardinality rules.

        Raises
        ------
        ValueError
            If hierarchy roots or parents are not graph-node types, if root and
            non-root parent declarations are inconsistent, or if a single-parent
            profile permits multiple parents.
        """

        graph_node_types = {
            policy.source_statement_type
            for policy in self.statement_types
            if policy.is_graph_node
        }
        self._validate_hierarchy_roots_are_graph_nodes(graph_node_types)
        self._validate_declared_parents_are_graph_nodes(graph_node_types)
        self._validate_root_parent_consistency()
        self._validate_single_parent_cardinality()

    def _validate_hierarchy_roots_are_graph_nodes(
        self, graph_node_types: set[str]
    ) -> None:
        """Require every declared hierarchy root to be a graph-node type.

        Parameters
        ----------
        graph_node_types
            Names of statement types flagged as graph nodes.

        Raises
        ------
        ValueError
            If any hierarchy root is not a graph-node type.
        """

        non_graph_roots = set(self.hierarchy.root_statement_types) - graph_node_types

        if non_graph_roots:
            formatted_types = ", ".join(sorted(non_graph_roots))
            raise ValueError(
                f"Hierarchy roots must be graph-node types: {formatted_types}."
            )

    def _validate_local_label_uniqueness(self) -> None:
        """Require grade and education-stage mappings to have unique local labels.

        Raises
        ------
        ValueError
            If duplicate local labels are present in either mapping collection.
        """

        local_grade_labels = tuple(
            mapping.local_label for mapping in self.grade_mappings
        )
        _require_unique(field_name="grade_mappings", values=local_grade_labels)
        local_stage_labels = tuple(
            mapping.local_label for mapping in self.education_stage_mappings
        )
        _require_unique(
            field_name="education_stage_mappings", values=local_stage_labels
        )

    def _validate_root_parent_consistency(self) -> None:
        """Require root and non-root graph nodes to declare parents consistently.

        Raises
        ------
        ValueError
            If a root declares parents or a non-root omits them.
        """

        root_statement_types = set(self.hierarchy.root_statement_types)

        for policy in self.statement_types:
            if not policy.is_graph_node:
                continue

            statement_type = policy.source_statement_type
            is_root = statement_type in root_statement_types

            if is_root and policy.allowed_parents:
                raise ValueError(
                    f"Root statement type {statement_type} may not declare parents."
                )

            if not is_root and not policy.allowed_parents:
                raise ValueError(
                    f"Non-root statement type {statement_type} must declare parents."
                )

    def _validate_single_parent_cardinality(self) -> None:
        """Require single-parent profiles to permit at most one bounded parent.

        Raises
        ------
        ValueError
            If a single-parent profile declares an unbounded parent maximum or permits
            more than one parent for a graph-node statement type.
        """

        if self.hierarchy.allow_multi_parent:
            return

        for policy in self.statement_types:
            if not policy.is_graph_node:
                continue

            statement_type = policy.source_statement_type
            max_parent_count = 0

            for parent in policy.allowed_parents:
                if parent.max_count is None:
                    raise ValueError(
                        f"Single-parent profiles may not use an unbounded maximum for "
                        f"{statement_type}."
                    )

                max_parent_count += parent.max_count

            if max_parent_count > 1:
                raise ValueError(
                    f"Single-parent profile permits multiple parents for {statement_type}."
                )

    def _validate_statement_type_references(self) -> None:
        """Require referenced statement types to be declared and uniquely named.

        Raises
        ------
        ValueError
            If statement-type names are duplicated or a referenced statement type is
            not declared.
        """

        statement_type_names = tuple(
            policy.source_statement_type for policy in self.statement_types
        )
        _require_unique(field_name="statement_types", values=statement_type_names)
        statement_types_by_name = {
            policy.source_statement_type: policy for policy in self.statement_types
        }
        declared_statement_types = set(statement_types_by_name)

        referenced_statement_types = set(self.grade_level_statement_types)
        referenced_statement_types.update(self.hierarchy.root_statement_types)
        referenced_statement_types.update(self.hierarchy.statement_type_order)

        for policy in self.statement_types:
            referenced_statement_types.update(policy.identity_scope)
            referenced_statement_types.update(
                parent.parent_statement_type for parent in policy.allowed_parents
            )

        missing_statement_types = referenced_statement_types - declared_statement_types

        if missing_statement_types:
            formatted_types = ", ".join(sorted(missing_statement_types))
            raise ValueError(
                f"Profile references undeclared statement types: {formatted_types}."
            )

    def _validate_subject_mapping(self) -> None:
        """Validate normalized subjects against the vocabulary and mapping status.

        Raises
        ------
        ValueError
            If normalized subjects are inconsistent with the vocabulary or the declared
            subject mapping status.
        """

        vocabulary_values = set(self.subject_vocabulary.values)
        unknown_subjects = set(self.normalized_subjects) - vocabulary_values

        if unknown_subjects:
            formatted_subjects = ", ".join(sorted(unknown_subjects))
            raise ValueError(
                f"normalized_subjects are absent from the vocabulary: {formatted_subjects}."
            )

        if self.subject_mapping_status is SubjectMappingStatus.UNREVIEWED:
            if self.normalized_subjects:
                raise ValueError(
                    "Unreviewed subject mappings may not declare normalized subjects."
                )
        elif not self.normalized_subjects:
            raise ValueError(
                "Reviewed subject mappings must declare normalized subjects."
            )

        unmatched_value = self.subject_vocabulary.unmatched_value

        if (
            self.subject_mapping_status is SubjectMappingStatus.MAPPED
            and unmatched_value in self.normalized_subjects
        ):
            raise ValueError(
                "Mapped subjects may not use the vocabulary unmatched_value."
            )

        if self.subject_mapping_status is SubjectMappingStatus.OTHER:
            if unmatched_value is None:
                raise ValueError(
                    "Other subject mappings require a vocabulary unmatched_value."
                )

            if self.normalized_subjects != (unmatched_value,):
                raise ValueError(
                    "Other subject mappings must use only the vocabulary unmatched_value."
                )

            if not self.subject_mapping_note:
                raise ValueError("Other subject mappings require subject_mapping_note.")

    def _validate_unique_collections(self) -> None:
        """Require simple string collections to contain no duplicates.

        Raises
        ------
        ValueError
            If any validated collection contains duplicate values.
        """

        _require_unique(
            field_name="framework_ids",
            values=tuple(str(value) for value in self.framework_ids),
        )
        _require_unique(
            field_name="grade_level_statement_types",
            values=self.grade_level_statement_types,
        )
        _require_unique(
            field_name="normalized_subjects", values=self.normalized_subjects
        )
        _require_unique(field_name="subject_aliases", values=self.subject_aliases)
        _require_unique(
            field_name="comparison_dimensions", values=self.comparison_dimensions
        )
        _require_unique(
            field_name="progression_heuristics", values=self.progression_heuristics
        )
        _require_unique(
            field_name="required_disclosures", values=self.required_disclosures
        )

    @model_validator(mode="after")
    def validate_profile(self) -> Self:
        """Validate cross-references and configuration invariants.

        Returns
        -------
        Self
            Fully validated curriculum profile.

        Raises
        ------
        ValueError
            If a profile references undeclared types or has conflicting policies.
        """

        self._validate_unique_collections()
        self._validate_subject_mapping()
        self._validate_local_label_uniqueness()
        self._validate_statement_type_references()
        self._validate_hierarchy_node_policies()
        self._validate_code_type_references()
        self._validate_anomaly_uniqueness()
        return self
