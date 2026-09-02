"""This module performs complete package-wide validation and controlled status
transitions.

This module performs complete package-wide validation after package integrity and
decoding have succeeded. It validates graph-record identifiers, labels, endpoint
representations, relationship types and statuses, duplicate edges, self-loops, directed
cycles, root reachability, detached components, manifest counts, capabilities, profile
semantics, and the supported detailed validation report.

Curriculum-specific meaning is obtained exclusively from the selected versioned
profile. The validator therefore applies statement-type, parent-cardinality, code,
subject, grade, language, metadata, and rights rules without introducing
country-specific, organization-specific, subject-specific, or package-specific
conditionals. Delivery-schema rules, including the generic ``unresolvedRootFallback``
exception, are applied independently of any curriculum.

The validator preserves every distinct valid relationship, including valid multi-parent
hierarchy edges. It produces immutable structured findings and computes a target status
of ``passed``, ``failed``, or ``quarantined``. Before persistence, it requires the
loader to verify that the package and selected profile still match the immutable
load-time integrity snapshot. A changed package remains ``pending`` and must be
validated again. Otherwise, the validator delegates the controlled pending-to-terminal
manifest transition to the package repository; read-only and terminal-package
validation never rewrite package state.

Temporary validation-local mappings and sets may be used to inspect the graph, but this
module does not provide a reusable graph store, traversal API, catalog, search service,
FastMCP application, or MCP tools, resources, or prompts.
"""

# Future Library
from __future__ import annotations

# Standard Library
import re

from collections import defaultdict, deque
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Final

# Package Library
from kgfegmcp.domain.enums import (
    CodeAvailability,
    InvalidPackagePolicy,
    ValidationStatus,
)
from kgfegmcp.graph.models import (
    FrameworkNode,
    GraphNode,
    GraphRelationship,
    LearningComponentNode,
    StandardNode,
)
from kgfegmcp.packages.loader import GraphPackageLoader, GraphPackageLoadResult
from kgfegmcp.packages.models import (
    ADDITIONAL_COUNT_CODED_ITEMS,
    ADDITIONAL_COUNT_MULTI_PARENT_TARGETS,
    ADDITIONAL_COUNT_UNRESOLVED_RELATIONSHIPS,
    DELIVERY_REPORT_COUNT_FRAMEWORK_NODES,
    DELIVERY_REPORT_COUNT_ITEM_NODES,
    DELIVERY_REPORT_COUNT_RELATIONSHIPS,
    DELIVERY_REPORT_COUNT_UNRESOLVED_RELATIONSHIPS,
    FrameworkCapabilities,
    LoadedGraphPackage,
    PackageValidationFinding,
    PackageValidationResult,
)
from kgfegmcp.packages.repository import GraphPackageCandidate, GraphPackageRepository
from kgfegmcp.packages.wire import (
    DELIVERY_SCHEMA_1_0_ENDPOINT_ENTITY_KEY,
    DELIVERY_SCHEMA_1_0_FRAMEWORK_LABEL,
    DELIVERY_SCHEMA_1_0_HIERARCHY_RELATIONSHIP_TYPE,
    DELIVERY_SCHEMA_1_0_ITEM_LABEL,
    DELIVERY_SCHEMA_1_0_RELATIONSHIP_STATUS_VOCABULARY,
    DELIVERY_SCHEMA_1_1_COMPONENT_ENDPOINT_ENTITY_KEY,
    DELIVERY_SCHEMA_1_1_COMPONENT_LABEL,
    DELIVERY_SCHEMA_1_1_SUPPORTS_RELATIONSHIP_TYPE,
    SUPPORTED_RELATIONSHIP_TYPES,
    DELIVERY_SCHEMA_1_0_UNRESOLVED_ROOT_FALLBACK_STATUS,
)
from kgfegmcp.profiles.models import (
    CodeTypePolicy,
    CurriculumProfile,
    StatementTypePolicy,
)

_TERMINAL_STATUSES: Final[frozenset[ValidationStatus]] = frozenset(
    {
        ValidationStatus.FAILED,
        ValidationStatus.PASSED,
        ValidationStatus.QUARANTINED,
    }
)


@dataclass(frozen=True, slots=True)
class _GraphFacts:
    """Hold independently derived graph counts and topology evidence."""

    coded_items: int
    multi_parent_targets: int
    text_items: int
    unresolved_relationships: int


@dataclass(frozen=True, slots=True)
class GraphPackageValidator:
    """Coordinate package loading, complete validation, and status persistence."""

    loader: GraphPackageLoader
    repository: GraphPackageRepository

    def __post_init__(self) -> None:
        """Require loading and persistence to share one repository boundary.

        Raises
        ------
        ValueError
            If the loader and validator were configured with different repositories.
        """

        if self.loader.repository != self.repository:
            raise ValueError(
                "The package loader and validator must share one repository."
            )

    def _validate_load_result(
        self,
        *,
        invalid_package_policy: InvalidPackagePolicy,
        load_result: GraphPackageLoadResult,
        read_only: bool,
    ) -> PackageValidationOutcome:
        """Validate one already-loaded result and apply any allowed transition.

        Parameters
        ----------
        invalid_package_policy
            Terminal status policy for invalid pending packages.
        load_result
            Integrity-loading result for one discovered candidate.
        read_only
            Whether caller explicitly prohibited status persistence.

        Returns
        -------
        PackageValidationOutcome
            Public result and any loaded immutable aggregate.
        """

        findings = list(load_result.findings)

        if load_result.loaded_package is not None:
            findings.extend(validate_loaded_package(load_result.loaded_package))

        manifest = load_result.manifest
        observed_status = manifest.validation.status if manifest is not None else None
        terminal_revalidation = observed_status in _TERMINAL_STATUSES
        persistence_blocked = any(
            finding.code
            in {
                "graph_type_unsupported",
                "included_graph_types_unsupported",
                "manifest_framework_directory_mismatch",
                "manifest_snapshot_directory_mismatch",
                "package_revision_unsupported",
            }
            for finding in findings
        )
        persistence_context_available = (
            load_result.integrity_snapshot is not None
            and load_result.manifest_bytes is not None
            and manifest is not None
            and not persistence_blocked
        )
        effective_read_only = (
            read_only or terminal_revalidation or not persistence_context_available
        )
        persistence_suppressed = False

        if (
            not effective_read_only
            and load_result.integrity_snapshot is not None
            and manifest is not None
            and observed_status is ValidationStatus.PENDING
        ):
            change_findings = self.loader.verify_unchanged(
                candidate=load_result.candidate,
                integrity_snapshot=load_result.integrity_snapshot,
                manifest=manifest,
            )
            findings.extend(change_findings)
            persistence_suppressed = bool(change_findings)

        is_valid = not any(finding.severity == "error" for finding in findings)
        target_status = (
            ValidationStatus.PASSED
            if is_valid
            else (
                ValidationStatus.QUARANTINED
                if invalid_package_policy is InvalidPackagePolicy.QUARANTINE
                else ValidationStatus.FAILED
            )
        )
        persisted = False
        effective_status = observed_status
        validated_at = (
            manifest.validation.validated_at if manifest is not None else None
        )

        if (
            not effective_read_only
            and not persistence_suppressed
            and manifest is not None
            and load_result.manifest_bytes is not None
            and observed_status is ValidationStatus.PENDING
        ):
            transition = self.repository.persist_validation_transition(
                candidate=load_result.candidate,
                manifest=manifest,
                manifest_bytes=load_result.manifest_bytes,
                target_status=target_status,
            )
            effective_status = transition.manifest.validation.status
            persisted = True
            validated_at = transition.validated_at

        result = PackageValidationResult(
            effective_status=effective_status,
            findings=tuple(findings),
            framework_id=(manifest.framework_id if manifest is not None else None),
            graph_package_id=(
                manifest.graph_package_id if manifest is not None else None
            ),
            is_valid=is_valid,
            observed_status=observed_status,
            package_reference=load_result.candidate.reference,
            persisted=persisted,
            profile_id=(manifest.profile.profile_id if manifest is not None else None),
            profile_version=(
                manifest.profile.profile_version if manifest is not None else None
            ),
            read_only=effective_read_only,
            snapshot_id=(manifest.snapshot_id if manifest is not None else None),
            target_status=target_status,
            terminal_revalidation=terminal_revalidation,
            validated_at=validated_at,
        )
        return PackageValidationOutcome(
            loaded_package=load_result.loaded_package, result=result
        )

    def validate_candidate(
        self,
        *,
        candidate: GraphPackageCandidate,
        invalid_package_policy: InvalidPackagePolicy,
        read_only: bool,
    ) -> PackageValidationOutcome:
        """Load and validate one safely discovered package candidate.

        Parameters
        ----------
        candidate
            Candidate returned by the graph-package repository.
        invalid_package_policy
            Terminal status policy for invalid pending packages.
        read_only
            Whether status persistence is prohibited.

        Returns
        -------
        PackageValidationOutcome
            Complete validation outcome.
        """

        load_result = self.loader.load(candidate)
        return self._validate_load_result(
            invalid_package_policy=invalid_package_policy,
            load_result=load_result,
            read_only=read_only,
        )

    def validate_pending(
        self, *, invalid_package_policy: InvalidPackagePolicy, read_only: bool
    ) -> tuple[PackageValidationOutcome, ...]:
        """Validate all discovered pending packages and malformed candidates.

        Terminal manifests are intentionally skipped by this batch command. A malformed
        candidate whose status cannot be established is included so unsafe content is
        never silently ignored.

        Parameters
        ----------
        invalid_package_policy
            Terminal status policy for invalid pending packages.
        read_only
            Whether status persistence is prohibited.

        Returns
        -------
        tuple[PackageValidationOutcome, ...]
            Deterministically ordered outcomes for pending or malformed candidates.
        """

        outcomes: list[PackageValidationOutcome] = []

        for candidate in self.repository.discover():
            load_result = self.loader.load(candidate)

            if (
                load_result.manifest is not None
                and load_result.manifest.validation.status in _TERMINAL_STATUSES
            ):
                continue

            outcomes.append(
                self._validate_load_result(
                    invalid_package_policy=invalid_package_policy,
                    load_result=load_result,
                    read_only=read_only,
                )
            )

        return tuple(outcomes)


@dataclass(frozen=True, slots=True)
class PackageValidationOutcome:
    """Associate a public validation result with any loaded package aggregate."""

    loaded_package: LoadedGraphPackage | None
    result: PackageValidationResult


def _add_mismatch(
    *,
    actual: object,
    code: str,
    expected: object,
    field_name: str,
    findings: list[PackageValidationFinding],
    record_id: str | None = None,
    source_export_order: int | None = None,
) -> None:
    """Append one finding when two deterministic values disagree.

    Parameters
    ----------
    actual
        Observed value.
    code
        Stable finding code.
    expected
        Required value.
    field_name
        Safe logical field name for the public message.
    findings
        Mutable validation-local finding accumulator.
    record_id
        Optional record identifier.
    source_export_order
        Optional source order.
    """

    if actual == expected:
        return

    findings.append(
        _finding(
            code=code,
            details={"actual": actual, "expected": expected, "field": field_name},
            message=f"{field_name} does not agree with the established package contract.",
            record_id=record_id,
            source_export_order=source_export_order,
        )
    )


def _build_hierarchy_adjacency(
    *, hierarchy_relationships: tuple[GraphRelationship, ...], node_ids: set[str]
) -> dict[str, list[str]]:
    """Build a directed adjacency map from resolved hierarchy edges.

    Parameters
    ----------
    hierarchy_relationships
        Resolved delivery-schema hierarchy edges.
    node_ids
        Every package node identifier, used to discard dangling endpoints.

    Returns
    -------
    dict[str, list[str]]
        Target identifiers grouped by source identifier, source order preserved.
    """

    adjacency: dict[str, list[str]] = defaultdict(list)

    for relationship in hierarchy_relationships:
        source_id = str(relationship.source_node_id)
        target_id = str(relationship.target_node_id)

        if source_id not in node_ids or target_id not in node_ids:
            continue

        adjacency[source_id].append(target_id)

    return adjacency


def _count_ordinary_parent_types(
    *,
    findings: list[PackageValidationFinding],
    nodes_by_id: dict[str, GraphNode],
    normal_incoming: list[GraphRelationship],
    target: StandardNode,
) -> dict[str, int]:
    """Count ordinary parent statement types and reject non-item parents.

    Parameters
    ----------
    findings
        Validation-local finding accumulator.
    nodes_by_id
        Decoded nodes by outer identifier.
    normal_incoming
        Incoming hierarchy relationships without any resolution status.
    target
        Decoded framework item being validated.

    Returns
    -------
    dict[str, int]
        Ordinary parent counts grouped by source statement type.
    """

    target_id = str(target.node_id)
    counts_by_parent_type: dict[str, int] = defaultdict(int)

    for relationship in normal_incoming:
        source_id = str(relationship.source_node_id)
        source_node = nodes_by_id.get(source_id)

        if not isinstance(source_node, StandardNode):
            findings.append(
                _finding(
                    code="ordinary_parent_not_framework_item",
                    details={
                        "source_node_id": source_id,
                        "target_node_id": target_id,
                    },
                    message="An ordinary non-root hierarchy parent must be a framework item.",
                    record_id=str(relationship.relationship_id),
                    source_export_order=relationship.source_export_order,
                )
            )
            continue

        source_statement_type = source_node.statement_type

        if source_statement_type is None:
            continue

        counts_by_parent_type[source_statement_type] += 1

    return counts_by_parent_type


def _finding(
    *,
    code: str,
    details: dict[str, object] | None = None,
    message: str,
    record_id: str | None = None,
    source_export_order: int | None = None,
) -> PackageValidationFinding:
    """Construct one structured semantic-validation error.

    Parameters
    ----------
    code
        Stable machine-readable finding code.
    details
        Optional private diagnostic values.
    message
        Safe public message.
    record_id
        Optional source record identifier.
    source_export_order
        Optional one-based source order.

    Returns
    -------
    PackageValidationFinding
        Immutable error finding.
    """

    return PackageValidationFinding(
        code=code,
        details=details or {},
        message=message,
        record_id=record_id,
        severity="error",
        source_export_order=source_export_order,
    )


def _node_kind_label(node: GraphNode) -> str:
    """Return the delivery-schema label associated with a decoded node type.

    Parameters
    ----------
    node
        Decoded framework, framework-item, or learning-component node.

    Returns
    -------
    str
        Supported delivery-schema node label.

    Raises
    ------
    TypeError
        If the decoded node is not a supported delivery-schema node kind. A silent
        fallback would relabel an unrecognized node as a standards framework item.
    """

    if isinstance(node, FrameworkNode):
        return DELIVERY_SCHEMA_1_0_FRAMEWORK_LABEL

    if isinstance(node, LearningComponentNode):
        return DELIVERY_SCHEMA_1_1_COMPONENT_LABEL

    if isinstance(node, StandardNode):
        return DELIVERY_SCHEMA_1_0_ITEM_LABEL

    raise TypeError(f"Unsupported decoded node kind: {type(node).__name__}.")


def _node_endpoint_entity_key(node: GraphNode) -> str:
    """Return the property name a relationship uses to reference one endpoint node.

    Standards framework and framework-item endpoints are referenced by their CASE
    identifier. Learning components carry no CASE identity, so they are referenced by
    their own ``identifier`` instead.

    Parameters
    ----------
    node
        Decoded endpoint node.

    Returns
    -------
    str
        Delivery-schema property name used to reference the endpoint.
    """

    if isinstance(node, LearningComponentNode):
        return DELIVERY_SCHEMA_1_1_COMPONENT_ENDPOINT_ENTITY_KEY

    if isinstance(node, FrameworkNode | StandardNode):
        return DELIVERY_SCHEMA_1_0_ENDPOINT_ENTITY_KEY

    raise TypeError(f"Unsupported decoded node kind: {type(node).__name__}.")


def _node_endpoint_entity_value(node: GraphNode) -> str | None:
    """Return the value a relationship carries to reference one endpoint node.

    Parameters
    ----------
    node
        Decoded endpoint node.

    Returns
    -------
    str | None
        Endpoint reference value, or ``None`` when the node declares no CASE identity.
    """

    if isinstance(node, LearningComponentNode):
        return str(node.node_id)

    if node.case_identifier_uuid is None:
        return None

    return str(node.case_identifier_uuid)


def _ordered_unique(values: tuple[str, ...]) -> tuple[str, ...]:
    """Return values in first-seen order with duplicates removed.

    Parameters
    ----------
    values
        Source ordered values.

    Returns
    -------
    tuple[str, ...]
        First-seen unique values.
    """

    return tuple(dict.fromkeys(values))


def _snapshot_version_token(snapshot_id: str) -> str:
    """Extract the established version token from an immutable snapshot ID.

    Parameters
    ----------
    snapshot_id
        Established snapshot identifier.

    Returns
    -------
    str
        Token between ``@`` and the final ``+`` content-hash delimiter.
    """

    identity_without_hash = snapshot_id.rpartition("+")[0]
    return identity_without_hash.partition("@")[2]


def _validate_code_availability_conflict(
    *,
    coded_items: int,
    findings: list[PackageValidationFinding],
    item_count: int,
    profile_code_availability: CodeAvailability,
) -> None:
    """Reject decoded statement-code evidence that conflicts with the profile.

    Parameters
    ----------
    coded_items
        Independently counted non-blank item codes.
    findings
        Validation-local finding accumulator.
    item_count
        Total number of decoded framework items.
    profile_code_availability
        Statement-code availability declared by the selected profile.
    """

    if coded_items == 0:
        actual_code_availability = CodeAvailability.NONE
    elif coded_items == item_count:
        actual_code_availability = CodeAvailability.COMPLETE
    else:
        actual_code_availability = CodeAvailability.PARTIAL

    conflict_message: str | None = None

    if (
        profile_code_availability is CodeAvailability.NONE
        and actual_code_availability is not CodeAvailability.NONE
    ):
        conflict_message = (
            "Decoded statement-code evidence conflicts with the selected profile."
        )
    elif (
        profile_code_availability is CodeAvailability.COMPLETE
        and actual_code_availability is not CodeAvailability.COMPLETE
    ):
        conflict_message = (
            "Decoded statement-code evidence is incomplete for the selected profile."
        )
    elif (
        profile_code_availability is CodeAvailability.PARTIAL
        and actual_code_availability is CodeAvailability.NONE
    ):
        conflict_message = (
            "Decoded statement-code evidence is absent for a partial-code profile."
        )

    if conflict_message is None:
        return

    findings.append(
        _finding(
            code="profile_code_availability_conflict",
            details={
                "actual_availability": actual_code_availability.value,
                "profile_availability": profile_code_availability.value,
            },
            message=conflict_message,
        )
    )


def _validate_counts_capabilities_and_report(
    *,
    coded_items: int,
    findings: list[PackageValidationFinding],
    package: LoadedGraphPackage,
    text_items: int,
) -> _GraphFacts:
    """Validate manifest counts, capabilities, profile code evidence, and report counts.

    Parameters
    ----------
    coded_items
        Independently counted non-blank item codes.
    findings
        Validation-local finding accumulator.
    package
        Loaded package aggregate.
    text_items
        Independently counted non-blank item descriptions.

    Returns
    -------
    _GraphFacts
        Independently derived count and capability evidence.
    """

    manifest = package.manifest
    profile = package.profile
    unresolved_relationships = sum(
        relationship.resolution_status
        == DELIVERY_SCHEMA_1_0_UNRESOLVED_ROOT_FALLBACK_STATUS
        for relationship in package.relationships
    )
    parent_sources: dict[str, set[str]] = defaultdict(set)

    for relationship in package.relationships:
        if relationship.label != profile.hierarchy.relationship_type:
            continue

        parent_sources[str(relationship.target_node_id)].add(
            str(relationship.source_node_id)
        )

    multi_parent_targets = sum(
        len(source_ids) > 1 for source_ids in parent_sources.values()
    )
    item_count = len(package.item_nodes)
    relationship_count = len(package.relationships)

    count_comparisons = (
        (
            manifest.counts.framework_nodes,
            1,
            "framework node count",
            "manifest_framework_count_mismatch",
        ),
        (
            manifest.counts.item_nodes,
            item_count,
            "item node count",
            "manifest_item_count_mismatch",
        ),
        (
            manifest.counts.relationships,
            relationship_count,
            "relationship count",
            "manifest_relationship_count_mismatch",
        ),
        (
            manifest.counts.additional_counts[ADDITIONAL_COUNT_CODED_ITEMS],
            coded_items,
            "coded item count",
            "manifest_coded_item_count_mismatch",
        ),
        (
            manifest.counts.additional_counts[ADDITIONAL_COUNT_MULTI_PARENT_TARGETS],
            multi_parent_targets,
            "multi-parent target count",
            "manifest_multi_parent_count_mismatch",
        ),
        (
            manifest.counts.additional_counts[
                ADDITIONAL_COUNT_UNRESOLVED_RELATIONSHIPS
            ],
            unresolved_relationships,
            "unresolved relationship count",
            "manifest_unresolved_count_mismatch",
        ),
    )

    for actual, expected, field_name, code in count_comparisons:
        _add_mismatch(
            actual=actual,
            code=code,
            expected=expected,
            field_name=field_name,
            findings=findings,
        )

    profile_code_availability = profile.code_search_policy.availability
    _validate_code_availability_conflict(
        coded_items=coded_items,
        findings=findings,
        item_count=item_count,
        profile_code_availability=profile_code_availability,
    )

    expected_capabilities = FrameworkCapabilities(
        code_search=profile_code_availability,
        has_detailed_provenance=(
            package.manifest.artifacts.entity_provenance is not None
        ),
        has_official_activities=(
            profile.source_role_capabilities.has_official_activities
        ),
        has_official_assessment_guidance=(
            profile.source_role_capabilities.has_official_assessment_guidance
        ),
        has_unresolved_relationships=unresolved_relationships > 0,
        multi_parent=multi_parent_targets > 0,
        text_search=text_items > 0,
    )

    if manifest.capabilities != expected_capabilities:
        findings.append(
            _finding(
                code="manifest_capabilities_mismatch",
                details={
                    "actual": manifest.capabilities.model_dump(mode="json"),
                    "expected": expected_capabilities.model_dump(mode="json"),
                },
                message="Manifest capabilities do not agree with profile policy and decoded evidence.",
            )
        )

    _validate_detailed_report_counts(
        findings=findings,
        item_count=item_count,
        package=package,
        relationship_count=relationship_count,
        unresolved_relationships=unresolved_relationships,
    )

    return _GraphFacts(
        coded_items=coded_items,
        multi_parent_targets=multi_parent_targets,
        text_items=text_items,
        unresolved_relationships=unresolved_relationships,
    )


def _validate_cycle_and_reachability(
    *,
    findings: list[PackageValidationFinding],
    hierarchy_relationships: tuple[GraphRelationship, ...],
    package: LoadedGraphPackage,
) -> None:
    """Reject directed cycles and require every item to be reachable from the root.

    Parameters
    ----------
    findings
        Validation-local finding accumulator.
    hierarchy_relationships
        Resolved delivery-schema hierarchy edges.
    package
        Loaded package aggregate.
    """

    node_ids = {
        str(package.framework_root.node_id),
        *(str(node.node_id) for node in package.item_nodes),
    }
    adjacency = _build_hierarchy_adjacency(
        hierarchy_relationships=hierarchy_relationships, node_ids=node_ids
    )
    _validate_hierarchy_acyclic(
        adjacency=adjacency, findings=findings, node_ids=node_ids
    )
    _validate_root_reachability(adjacency=adjacency, findings=findings, package=package)


def _validate_detailed_report_counts(
    *,
    findings: list[PackageValidationFinding],
    item_count: int,
    package: LoadedGraphPackage,
    relationship_count: int,
    unresolved_relationships: int,
) -> None:
    """Require any detailed validation-report counts to agree with package evidence.

    Parameters
    ----------
    findings
        Validation-local finding accumulator.
    item_count
        Total number of decoded framework items.
    package
        Loaded package aggregate.
    relationship_count
        Total number of decoded relationships.
    unresolved_relationships
        Independently counted unresolved root-fallback relationships.
    """

    report = package.validation_report

    if report is None:
        return

    manifest = package.manifest
    report_comparisons = (
        (
            DELIVERY_REPORT_COUNT_FRAMEWORK_NODES,
            1,
            manifest.counts.framework_nodes,
        ),
        (
            DELIVERY_REPORT_COUNT_ITEM_NODES,
            item_count,
            manifest.counts.item_nodes,
        ),
        (
            DELIVERY_REPORT_COUNT_RELATIONSHIPS,
            relationship_count,
            manifest.counts.relationships,
        ),
        (
            DELIVERY_REPORT_COUNT_UNRESOLVED_RELATIONSHIPS,
            unresolved_relationships,
            manifest.counts.additional_counts[
                ADDITIONAL_COUNT_UNRESOLVED_RELATIONSHIPS
            ],
        ),
    )

    for count_name, decoded_count, manifest_count in report_comparisons:
        reported_count = report.object_counts[count_name]

        if reported_count != decoded_count or reported_count != manifest_count:
            findings.append(
                _finding(
                    code="detailed_validation_report_count_mismatch",
                    details={
                        "count_name": count_name,
                        "decoded_count": decoded_count,
                        "manifest_count": manifest_count,
                        "reported_count": reported_count,
                        "upstream_schema_version": (
                            report.learning_commons_export_schema_version
                        ),
                    },
                    message="A detailed validation-report graph count disagrees with package evidence.",
                )
            )


def _validate_fallback_parents(
    *,
    fallback_relationships: list[GraphRelationship],
    findings: list[PackageValidationFinding],
    incoming: list[GraphRelationship],
    root_id: str,
    target: StandardNode,
) -> None:
    """Validate one item's unresolved root-fallback incoming relationships.

    Parameters
    ----------
    fallback_relationships
        Incoming relationships carrying the unresolved root-fallback status.
    findings
        Validation-local finding accumulator.
    incoming
        Every resolved hierarchy relationship targeting the item.
    root_id
        Single framework-root identifier.
    target
        Decoded framework item being validated.
    """

    target_id = str(target.node_id)

    for relationship in fallback_relationships:
        if str(relationship.source_node_id) != root_id:
            findings.append(
                _finding(
                    code="fallback_source_not_framework_root",
                    details={
                        "source_node_id": str(relationship.source_node_id),
                        "target_node_id": target_id,
                    },
                    message="An unresolved root fallback must originate at the single framework root.",
                    record_id=str(relationship.relationship_id),
                    source_export_order=relationship.source_export_order,
                )
            )

        if relationship.relationship_type != (
            DELIVERY_SCHEMA_1_0_HIERARCHY_RELATIONSHIP_TYPE
        ):
            findings.append(
                _finding(
                    code="fallback_relationship_type_invalid",
                    details={"relationship_type": relationship.relationship_type},
                    message="An unresolved root fallback must use the hasChild relationship type.",
                    record_id=str(relationship.relationship_id),
                    source_export_order=relationship.source_export_order,
                )
            )

    if len(incoming) != 1 or len(fallback_relationships) != 1:
        findings.append(
            _finding(
                code="fallback_not_sole_incoming_relationship",
                details={
                    "fallback_relationships": len(fallback_relationships),
                    "incoming_relationships": len(incoming),
                    "target_node_id": target_id,
                },
                message="An unresolved root fallback must be the target item's sole incoming hasChild relationship.",
                record_id=target_id,
                source_export_order=target.source_export_order,
            )
        )


def _validate_framework_and_profile_semantics(
    *, package: LoadedGraphPackage, findings: list[PackageValidationFinding]
) -> None:
    """Validate manifest, framework-root, profile, and rights agreement.

    Parameters
    ----------
    package
        Loaded package aggregate.
    findings
        Validation-local finding accumulator.
    """

    manifest = package.manifest
    profile = package.profile
    root = package.framework_root
    framework = manifest.framework

    if manifest.framework_id not in profile.framework_ids:
        findings.append(
            _finding(
                code="profile_framework_id_mismatch",
                details={
                    "framework_id": str(manifest.framework_id),
                    "profile_framework_ids": tuple(
                        str(value) for value in profile.framework_ids
                    ),
                },
                message="The selected profile does not declare the package framework ID.",
            )
        )

    if profile.hierarchy.relationship_type != (
        DELIVERY_SCHEMA_1_0_HIERARCHY_RELATIONSHIP_TYPE
    ):
        findings.append(
            _finding(
                code="profile_relationship_type_unsupported",
                details={
                    "profile_relationship_type": profile.hierarchy.relationship_type
                },
                message="The selected profile hierarchy relationship type is unsupported by delivery schema 1.0.",
            )
        )

    local_grades_or_stages = _ordered_unique(
        tuple(mapping.local_label for mapping in profile.grade_mappings)
        + tuple(mapping.local_label for mapping in profile.education_stage_mappings)
    )
    normalized_grades = _ordered_unique(
        tuple(
            normalized_grade
            for mapping in profile.grade_mappings
            for normalized_grade in mapping.normalized_grades
        )
    )

    comparisons = (
        (
            framework.local_subject,
            profile.local_subject,
            "framework local subject",
            "manifest_profile_local_subject_mismatch",
        ),
        (
            framework.normalized_subjects,
            profile.normalized_subjects,
            "framework normalized subjects",
            "manifest_profile_normalized_subjects_mismatch",
        ),
        (
            framework.subject_mapping_status,
            profile.subject_mapping_status,
            "framework subject mapping status",
            "manifest_profile_subject_mapping_status_mismatch",
        ),
        (
            framework.subject_mapping_note,
            profile.subject_mapping_note,
            "framework subject mapping note",
            "manifest_profile_subject_mapping_note_mismatch",
        ),
        (
            framework.languages,
            profile.language_policy.languages,
            "framework languages",
            "manifest_profile_languages_mismatch",
        ),
        (
            framework.local_grades_or_stages,
            local_grades_or_stages,
            "framework local grades or stages",
            "manifest_profile_local_grades_mismatch",
        ),
        (
            framework.normalized_grades,
            normalized_grades,
            "framework normalized grades",
            "manifest_profile_normalized_grades_mismatch",
        ),
        (
            manifest.rights,
            profile.rights,
            "package rights policy",
            "manifest_profile_rights_mismatch",
        ),
        (
            framework.name,
            root.name,
            "framework name",
            "manifest_root_name_mismatch",
        ),
        (
            framework.local_subject,
            root.academic_subject,
            "framework academic subject",
            "manifest_root_subject_mismatch",
        ),
        (
            framework.adoption_status,
            root.adoption_status,
            "framework adoption status",
            "manifest_root_adoption_status_mismatch",
        ),
        (
            framework.is_current,
            root.is_current,
            "framework current status",
            "manifest_root_current_status_mismatch",
        ),
        (
            framework.jurisdiction,
            root.jurisdiction,
            "framework jurisdiction",
            "manifest_root_jurisdiction_mismatch",
        ),
        (
            framework.issuing_authority,
            root.author,
            "framework issuing authority",
            "manifest_root_author_mismatch",
        ),
        (
            framework.provider,
            root.provider,
            "framework provider",
            "manifest_root_provider_mismatch",
        ),
        (
            manifest.rights.attribution_statement,
            root.attribution_statement,
            "framework attribution statement",
            "manifest_root_attribution_mismatch",
        ),
        (
            manifest.rights.source_license,
            root.license,
            "framework source license",
            "manifest_root_license_mismatch",
        ),
        (
            framework.source_version,
            _snapshot_version_token(str(manifest.snapshot_id)),
            "framework source version",
            "manifest_snapshot_version_mismatch",
        ),
    )

    for actual, expected, field_name, code in comparisons:
        _add_mismatch(
            actual=actual,
            code=code,
            expected=expected,
            field_name=field_name,
            findings=findings,
        )

    if root.in_language is None or root.in_language not in framework.languages:
        findings.append(
            _finding(
                code="framework_root_language_mismatch",
                details={
                    "manifest_languages": tuple(
                        str(value) for value in framework.languages
                    ),
                    "root_language": (
                        str(root.in_language) if root.in_language is not None else None
                    ),
                },
                message="The framework-root language is absent from the manifest language policy.",
                record_id=str(root.node_id),
                source_export_order=root.source_export_order,
            )
        )


def _validate_hierarchy_acyclic(
    *,
    adjacency: dict[str, list[str]],
    findings: list[PackageValidationFinding],
    node_ids: set[str],
) -> None:
    """Reject any directed cycle in the resolved hierarchy adjacency.

    Parameters
    ----------
    adjacency
        Directed hierarchy adjacency map.
    findings
        Validation-local finding accumulator.
    node_ids
        Every package node identifier.
    """

    indegrees = {node_id: 0 for node_id in node_ids}

    for targets in adjacency.values():
        for target_id in targets:
            indegrees[target_id] += 1

    queue = deque(
        sorted(node_id for node_id, indegree in indegrees.items() if indegree == 0)
    )
    processed_count = 0

    while queue:
        source_id = queue.popleft()
        processed_count += 1

        for target_id in adjacency.get(source_id, []):
            indegrees[target_id] -= 1

            if indegrees[target_id] == 0:
                queue.append(target_id)

    if processed_count != len(node_ids):
        findings.append(
            _finding(
                code="hierarchy_cycle_detected",
                details={
                    "node_count": len(node_ids),
                    "processed_acyclic_node_count": processed_count,
                },
                message="The academic-standards hasChild hierarchy contains a directed cycle.",
            )
        )


def _validate_item_grade_levels(
    *,
    findings: list[PackageValidationFinding],
    node: StandardNode,
    normalized_grades: set[str],
) -> None:
    """Validate one item's grade-level values against manifest profile mappings.

    Parameters
    ----------
    findings
        Validation-local finding accumulator.
    node
        Decoded framework item.
    normalized_grades
        Normalized grade values permitted by the manifest profile.
    """

    if node.grade_level is None:
        return

    if not node.grade_level or len(node.grade_level) != len(set(node.grade_level)):
        findings.append(
            _finding(
                code="item_grade_levels_invalid",
                details={"grade_level": node.grade_level},
                message="A framework item has empty or duplicate grade-level values.",
                record_id=str(node.node_id),
                source_export_order=node.source_export_order,
            )
        )

    unknown_grades = set(node.grade_level) - normalized_grades

    if unknown_grades:
        findings.append(
            _finding(
                code="item_grade_level_unsupported",
                details={"unknown_grades": tuple(sorted(unknown_grades))},
                message="A framework item grade level is absent from manifest profile mappings.",
                record_id=str(node.node_id),
                source_export_order=node.source_export_order,
            )
        )


def _validate_item_semantics(
    *, package: LoadedGraphPackage, findings: list[PackageValidationFinding]
) -> tuple[int, int]:
    """Validate every item against profile statement, metadata, grade, and code policy.

    Parameters
    ----------
    package
        Loaded package aggregate.
    findings
        Validation-local finding accumulator.

    Returns
    -------
    tuple[int, int]
        Non-blank coded-item count and non-blank text-item count.
    """

    profile = package.profile
    root = package.framework_root
    policies = {
        policy.source_statement_type: policy for policy in profile.statement_types
    }
    code_types = {
        str(policy.code_type): policy
        for policy in profile.code_search_policy.code_types
    }
    normalized_grades = set(package.manifest.framework.normalized_grades)
    profile_languages = set(profile.language_policy.languages)
    observed_codes: dict[str, StandardNode] = {}
    coded_items = 0
    text_items = 0

    for node in package.item_nodes:
        node_id = str(node.node_id)
        description = node.description

        if description is not None and description.strip():
            text_items += 1

        policy = _validate_item_statement_type(
            findings=findings, node=node, policies=policies
        )

        metadata_comparisons = (
            (node.academic_subject, root.academic_subject, "item academic subject"),
            (node.adoption_status, root.adoption_status, "item adoption status"),
            (
                node.attribution_statement,
                root.attribution_statement,
                "item attribution statement",
            ),
            (node.author, root.author, "item author"),
            (node.is_current, root.is_current, "item current status"),
            (node.jurisdiction, root.jurisdiction, "item jurisdiction"),
            (node.license, root.license, "item source license"),
            (node.provider, root.provider, "item provider"),
        )

        for actual, expected, field_name in metadata_comparisons:
            _add_mismatch(
                actual=actual,
                code="item_framework_metadata_mismatch",
                expected=expected,
                field_name=field_name,
                findings=findings,
                record_id=node_id,
                source_export_order=node.source_export_order,
            )

        if node.in_language is None or node.in_language not in profile_languages:
            findings.append(
                _finding(
                    code="item_language_unsupported",
                    details={
                        "item_language": (
                            str(node.in_language)
                            if node.in_language is not None
                            else None
                        ),
                        "profile_languages": tuple(
                            str(value) for value in profile.language_policy.languages
                        ),
                    },
                    message="A framework item language is absent from the selected profile.",
                    record_id=node_id,
                    source_export_order=node.source_export_order,
                )
            )

        _validate_item_grade_levels(
            findings=findings, node=node, normalized_grades=normalized_grades
        )
        coded_items += _validate_item_statement_code(
            code_types=code_types,
            findings=findings,
            node=node,
            observed_codes=observed_codes,
            policy=policy,
            profile=profile,
        )

    return coded_items, text_items


def _validate_item_statement_code(
    *,
    code_types: dict[str, CodeTypePolicy],
    findings: list[PackageValidationFinding],
    node: StandardNode,
    observed_codes: dict[str, StandardNode],
    policy: StatementTypePolicy | None,
    profile: CurriculumProfile,
) -> int:
    """Validate one item's statement code and report whether it is a coded item.

    Parameters
    ----------
    code_types
        Profile code-type policies keyed by code-type identifier.
    findings
        Validation-local finding accumulator.
    node
        Decoded framework item.
    observed_codes
        Mutable lookup of already-seen unique statement codes.
    policy
        Resolved statement-type policy, or ``None`` when unavailable.
    profile
        Selected immutable profile.

    Returns
    -------
    int
        ``1`` when the item contributes a non-blank statement code, else ``0``.
    """

    node_id = str(node.node_id)
    statement_code = node.statement_code

    if statement_code is None:
        return 0

    if not statement_code.strip():
        findings.append(
            _finding(
                code="item_statement_code_invalid",
                details={"statement_code": statement_code},
                message="A framework item statement code is blank.",
                record_id=node_id,
                source_export_order=node.source_export_order,
            )
        )
        return 0

    if statement_code != statement_code.strip():
        findings.append(
            _finding(
                code="item_statement_code_invalid",
                details={"statement_code": statement_code},
                message="A framework item statement code has surrounding whitespace.",
                record_id=node_id,
                source_export_order=node.source_export_order,
            )
        )
        return 1

    if policy is None or policy.code_type is None:
        findings.append(
            _finding(
                code="item_statement_code_not_permitted",
                details={"statement_code": statement_code},
                message="A framework item has a code where the profile declares no code type.",
                record_id=node_id,
                source_export_order=node.source_export_order,
            )
        )
    else:
        code_type = code_types.get(str(policy.code_type))

        if code_type is None or not any(
            re.fullmatch(pattern=pattern, string=statement_code) is not None
            for pattern in code_type.patterns
        ):
            findings.append(
                _finding(
                    code="item_statement_code_pattern_mismatch",
                    details={
                        "code_type": str(policy.code_type),
                        "statement_code": statement_code,
                    },
                    message="A framework item statement code does not match its profile policy.",
                    record_id=node_id,
                    source_export_order=node.source_export_order,
                )
            )

    if profile.code_search_policy.codes_are_unique_identifiers:
        if statement_code in observed_codes:
            findings.append(
                _finding(
                    code="item_statement_code_duplicate",
                    details={
                        "first_node_id": str(observed_codes[statement_code].node_id),
                        "second_node_id": node_id,
                        "statement_code": statement_code,
                    },
                    message="A profile-unique statement code occurs more than once.",
                    record_id=node_id,
                    source_export_order=node.source_export_order,
                )
            )
        else:
            observed_codes[statement_code] = node

    return 1


def _validate_item_statement_type(
    *,
    findings: list[PackageValidationFinding],
    node: StandardNode,
    policies: dict[str, StatementTypePolicy],
) -> StatementTypePolicy | None:
    """Resolve and validate one item's statement type against the profile.

    Parameters
    ----------
    findings
        Validation-local finding accumulator.
    node
        Decoded framework item.
    policies
        Profile statement-type policies keyed by source statement type.

    Returns
    -------
    StatementTypePolicy | None
        Resolved statement-type policy, or ``None`` when unavailable.
    """

    node_id = str(node.node_id)
    statement_type = node.statement_type

    if statement_type is None or not statement_type.strip():
        findings.append(
            _finding(
                code="item_statement_type_missing",
                message="A framework item has no non-blank source statement type.",
                record_id=node_id,
                source_export_order=node.source_export_order,
            )
        )
        policy = None
    elif statement_type != statement_type.strip():
        findings.append(
            _finding(
                code="item_statement_type_whitespace",
                details={"statement_type": statement_type},
                message="A framework item statement type has surrounding whitespace.",
                record_id=node_id,
                source_export_order=node.source_export_order,
            )
        )
        policy = policies.get(statement_type)
    else:
        policy = policies.get(statement_type)

    if statement_type is not None and policy is None:
        findings.append(
            _finding(
                code="item_statement_type_unknown",
                details={"statement_type": statement_type},
                message="A framework item uses a statement type absent from the selected profile.",
                record_id=node_id,
                source_export_order=node.source_export_order,
            )
        )

    if policy is not None:
        if not policy.is_graph_node:
            findings.append(
                _finding(
                    code="item_statement_type_not_graph_node",
                    details={"statement_type": statement_type},
                    message="A delivered item uses a profile statement type that is not a graph node.",
                    record_id=node_id,
                    source_export_order=node.source_export_order,
                )
            )

        if node.normalized_statement_type != policy.normalized_statement_type:
            findings.append(
                _finding(
                    code="item_normalized_statement_type_mismatch",
                    details={
                        "actual": (
                            node.normalized_statement_type.value
                            if node.normalized_statement_type is not None
                            else None
                        ),
                        "expected": policy.normalized_statement_type.value,
                        "statement_type": statement_type,
                    },
                    message="A framework item normalized statement type disagrees with the profile.",
                    record_id=node_id,
                    source_export_order=node.source_export_order,
                )
            )

    return policy


def _validate_node_identifiers_and_labels(
    *, package: LoadedGraphPackage, findings: list[PackageValidationFinding]
) -> dict[str, GraphNode]:
    """Validate node labels, property identifiers, and package-wide uniqueness.

    Parameters
    ----------
    package
        Loaded package aggregate.
    findings
        Validation-local finding accumulator.

    Returns
    -------
    dict[str, GraphNode]
        First node observed for each outer node identifier.
    """

    nodes: tuple[GraphNode, ...] = (
        package.framework_root,
        *package.item_nodes,
        *package.learning_component_nodes,
    )
    nodes_by_id: dict[str, GraphNode] = {}
    case_identifiers: dict[str, GraphNode] = {}
    case_identifier_uris: dict[str, GraphNode] = {}

    for node in nodes:
        node_id = str(node.node_id)
        expected_label = _node_kind_label(node)

        if node.labels != (expected_label,):
            findings.append(
                _finding(
                    code="node_labels_unsupported",
                    details={
                        "actual_labels": node.labels,
                        "expected_labels": (expected_label,),
                    },
                    message="A decoded node uses unsupported delivery labels.",
                    record_id=node_id,
                    source_export_order=node.source_export_order,
                )
            )

        if node.property_identifier != node.node_id:
            findings.append(
                _finding(
                    code="node_identifier_mismatch",
                    details={
                        "outer_identifier": node_id,
                        "property_identifier": (
                            str(node.property_identifier)
                            if node.property_identifier is not None
                            else None
                        ),
                    },
                    message="A node outer identifier and property identifier disagree.",
                    record_id=node_id,
                    source_export_order=node.source_export_order,
                )
            )

        if node_id in nodes_by_id:
            findings.append(
                _finding(
                    code="node_identifier_duplicate",
                    details={
                        "first_source_export_order": nodes_by_id[
                            node_id
                        ].source_export_order,
                        "second_source_export_order": node.source_export_order,
                    },
                    message="A node identifier occurs more than once in the package.",
                    record_id=node_id,
                    source_export_order=node.source_export_order,
                )
            )
        else:
            nodes_by_id[node_id] = node

        if isinstance(node, LearningComponentNode):
            # Learning components carry no CASE identity; endpoints key on identifier.
            continue

        if node.case_identifier_uuid is None:
            findings.append(
                _finding(
                    code="node_case_identifier_missing",
                    message="A node does not declare the CASE identifier required by endpoints.",
                    record_id=node_id,
                    source_export_order=node.source_export_order,
                )
            )
        else:
            case_identifier = str(node.case_identifier_uuid)

            if case_identifier in case_identifiers:
                findings.append(
                    _finding(
                        code="node_case_identifier_duplicate",
                        details={
                            "first_node_id": str(
                                case_identifiers[case_identifier].node_id
                            ),
                            "second_node_id": node_id,
                        },
                        message="A CASE node identifier occurs more than once in the package.",
                        record_id=node_id,
                        source_export_order=node.source_export_order,
                    )
                )
            else:
                case_identifiers[case_identifier] = node

        if node.case_identifier_uri is None:
            continue

        case_identifier_uri = str(node.case_identifier_uri)

        if case_identifier_uri in case_identifier_uris:
            findings.append(
                _finding(
                    code="node_case_identifier_uri_duplicate",
                    details={
                        "first_node_id": str(
                            case_identifier_uris[case_identifier_uri].node_id
                        ),
                        "second_node_id": node_id,
                    },
                    message="A CASE node URI occurs more than once in the package.",
                    record_id=node_id,
                    source_export_order=node.source_export_order,
                )
            )
        else:
            case_identifier_uris[case_identifier_uri] = node

    return nodes_by_id


def _validate_ordinary_parents(
    *,
    findings: list[PackageValidationFinding],
    nodes_by_id: dict[str, GraphNode],
    normal_incoming: list[GraphRelationship],
    policy: StatementTypePolicy,
    profile: CurriculumProfile,
    statement_type: str,
    target: StandardNode,
) -> None:
    """Validate ordinary non-root parents, cardinality, and multi-parent policy.

    Parameters
    ----------
    findings
        Validation-local finding accumulator.
    nodes_by_id
        Decoded nodes by outer identifier.
    normal_incoming
        Incoming hierarchy relationships without any resolution status.
    policy
        Resolved statement-type policy for the target item.
    profile
        Selected immutable profile.
    statement_type
        Source statement type of the target item.
    target
        Decoded framework item being validated.
    """

    target_id = str(target.node_id)
    counts_by_parent_type = _count_ordinary_parent_types(
        findings=findings,
        nodes_by_id=nodes_by_id,
        normal_incoming=normal_incoming,
        target=target,
    )
    allowed_parents = {
        parent.parent_statement_type: parent for parent in policy.allowed_parents
    }

    for parent_type in counts_by_parent_type:
        if parent_type not in allowed_parents:
            findings.append(
                _finding(
                    code="profile_parent_type_not_allowed",
                    details={
                        "parent_statement_type": parent_type,
                        "target_statement_type": statement_type,
                        "target_node_id": target_id,
                    },
                    message="A hierarchy parent statement type is not allowed by the selected profile.",
                    record_id=target_id,
                    source_export_order=target.source_export_order,
                )
            )

    for parent_type, cardinality in allowed_parents.items():
        count = (
            counts_by_parent_type[parent_type]
            if parent_type in counts_by_parent_type
            else 0
        )

        if count < cardinality.min_count:
            findings.append(
                _finding(
                    code="profile_parent_minimum_not_met",
                    details={
                        "actual_count": count,
                        "minimum_count": cardinality.min_count,
                        "parent_statement_type": parent_type,
                        "target_statement_type": statement_type,
                        "target_node_id": target_id,
                    },
                    message="A framework item does not satisfy its profile minimum parent cardinality.",
                    record_id=target_id,
                    source_export_order=target.source_export_order,
                )
            )

        if cardinality.max_count is not None and count > cardinality.max_count:
            findings.append(
                _finding(
                    code="profile_parent_maximum_exceeded",
                    details={
                        "actual_count": count,
                        "maximum_count": cardinality.max_count,
                        "parent_statement_type": parent_type,
                        "target_statement_type": statement_type,
                        "target_node_id": target_id,
                    },
                    message="A framework item exceeds its profile maximum parent cardinality.",
                    record_id=target_id,
                    source_export_order=target.source_export_order,
                )
            )

    if not profile.hierarchy.allow_multi_parent:
        distinct_parent_ids = {
            str(relationship.source_node_id) for relationship in normal_incoming
        }

        if len(distinct_parent_ids) > 1:
            findings.append(
                _finding(
                    code="profile_multi_parent_not_allowed",
                    details={
                        "parent_node_ids": tuple(sorted(distinct_parent_ids)),
                        "target_node_id": target_id,
                    },
                    message="A framework item has multiple parents but the selected profile disallows them.",
                    record_id=target_id,
                    source_export_order=target.source_export_order,
                )
            )


def _validate_parent_policy(
    *,
    findings: list[PackageValidationFinding],
    incoming_relationships: dict[str, list[GraphRelationship]],
    nodes_by_id: dict[str, GraphNode],
    package: LoadedGraphPackage,
) -> None:
    """Validate root, normal parent, cardinality, and fallback relationship policy.

    Parameters
    ----------
    findings
        Validation-local finding accumulator.
    incoming_relationships
        Resolved hierarchy relationships grouped by target node ID.
    nodes_by_id
        Decoded nodes by outer identifier.
    package
        Loaded package aggregate.
    """

    profile = package.profile
    root_id = str(package.framework_root.node_id)
    policies: dict[str, StatementTypePolicy] = {
        policy.source_statement_type: policy for policy in profile.statement_types
    }
    root_statement_types = set(profile.hierarchy.root_statement_types)

    for target in package.item_nodes:
        target_id = str(target.node_id)
        incoming = (
            incoming_relationships[target_id]
            if target_id in incoming_relationships
            else []
        )
        fallback_relationships = [
            relationship
            for relationship in incoming
            if relationship.resolution_status
            == DELIVERY_SCHEMA_1_0_UNRESOLVED_ROOT_FALLBACK_STATUS
        ]

        if fallback_relationships:
            _validate_fallback_parents(
                fallback_relationships=fallback_relationships,
                findings=findings,
                incoming=incoming,
                root_id=root_id,
                target=target,
            )
            continue

        statement_type = target.statement_type
        policy = policies.get(statement_type) if statement_type is not None else None

        if policy is None:
            continue

        normal_incoming = [
            relationship
            for relationship in incoming
            if relationship.resolution_status is None
        ]

        for relationship in incoming:
            if relationship.resolution_status is None:
                continue

            findings.append(
                _finding(
                    code="relationship_status_not_applicable",
                    details={
                        "resolution_status": relationship.resolution_status,
                        "target_node_id": target_id,
                    },
                    message="A hierarchy relationship status is not valid for an ordinary parent edge.",
                    record_id=str(relationship.relationship_id),
                    source_export_order=relationship.source_export_order,
                )
            )

        if statement_type in root_statement_types:
            _validate_root_statement_parents(
                findings=findings,
                normal_incoming=normal_incoming,
                root_id=root_id,
                statement_type=statement_type,
                target=target,
            )
            continue

        _validate_ordinary_parents(
            findings=findings,
            nodes_by_id=nodes_by_id,
            normal_incoming=normal_incoming,
            policy=policy,
            profile=profile,
            statement_type=statement_type,
            target=target,
        )


def _validate_relationship_endpoints(
    *,
    findings: list[PackageValidationFinding],
    nodes_by_id: dict[str, GraphNode],
    relationship: GraphRelationship,
    root: FrameworkNode,
) -> GraphNode | None:
    """Resolve relationship endpoints and validate endpoint and metadata agreement.

    Parameters
    ----------
    findings
        Validation-local finding accumulator.
    nodes_by_id
        Unique first-observed node lookup.
    relationship
        Decoded relationship under validation.
    root
        Framework-root node providing shared metadata expectations.

    Returns
    -------
    GraphNode | None
        Resolved target node when both endpoints resolve, otherwise ``None``.
    """

    relationship_id = str(relationship.relationship_id)
    source_id = str(relationship.source_node_id)
    target_id = str(relationship.target_node_id)
    source_node = nodes_by_id.get(source_id)
    target_node = nodes_by_id.get(target_id)

    if source_node is None:
        findings.append(
            _finding(
                code="relationship_source_unresolved",
                details={"source_node_id": source_id},
                message="A relationship source endpoint does not resolve to a package node.",
                record_id=relationship_id,
                source_export_order=relationship.source_export_order,
            )
        )

    if target_node is None:
        findings.append(
            _finding(
                code="relationship_target_unresolved",
                details={"target_node_id": target_id},
                message="A relationship target endpoint does not resolve to a package node.",
                record_id=relationship_id,
                source_export_order=relationship.source_export_order,
            )
        )

    if source_node is None or target_node is None:
        return None

    source_label = _node_kind_label(source_node)
    target_label = _node_kind_label(target_node)
    endpoint_comparisons = (
        (
            relationship.source_labels,
            source_node.labels,
            "relationship source labels",
            "relationship_source_labels_mismatch",
        ),
        (
            relationship.target_labels,
            target_node.labels,
            "relationship target labels",
            "relationship_target_labels_mismatch",
        ),
        (
            relationship.source_entity,
            source_label,
            "relationship source entity",
            "relationship_source_entity_mismatch",
        ),
        (
            relationship.target_entity,
            target_label,
            "relationship target entity",
            "relationship_target_entity_mismatch",
        ),
        (
            relationship.source_entity_key,
            _node_endpoint_entity_key(source_node),
            "relationship source entity key",
            "relationship_source_entity_key_mismatch",
        ),
        (
            relationship.target_entity_key,
            _node_endpoint_entity_key(target_node),
            "relationship target entity key",
            "relationship_target_entity_key_mismatch",
        ),
        (
            relationship.source_entity_value,
            _node_endpoint_entity_value(source_node),
            "relationship source entity value",
            "relationship_source_entity_value_mismatch",
        ),
        (
            relationship.target_entity_value,
            _node_endpoint_entity_value(target_node),
            "relationship target entity value",
            "relationship_target_entity_value_mismatch",
        ),
    )

    for actual, expected, field_name, code in endpoint_comparisons:
        _add_mismatch(
            actual=actual,
            code=code,
            expected=expected,
            field_name=field_name,
            findings=findings,
            record_id=relationship_id,
            source_export_order=relationship.source_export_order,
        )

    metadata_comparisons = [
        (
            relationship.attribution_statement,
            root.attribution_statement,
            "relationship attribution statement",
        ),
        (relationship.license, root.license, "relationship source license"),
        (relationship.provider, root.provider, "relationship provider"),
    ]

    # A supports relationship declares its own author; the pipeline wrote it, not the
    # publishing body. Credit, licence, and provider still follow the source.
    if relationship.label != DELIVERY_SCHEMA_1_1_SUPPORTS_RELATIONSHIP_TYPE:
        metadata_comparisons.append(
            (relationship.author, root.author, "relationship author")
        )

    for actual, expected, field_name in metadata_comparisons:
        _add_mismatch(
            actual=actual,
            code="relationship_framework_metadata_mismatch",
            expected=expected,
            field_name=field_name,
            findings=findings,
            record_id=relationship_id,
            source_export_order=relationship.source_export_order,
        )

    if source_id == target_id:
        findings.append(
            _finding(
                code="relationship_self_loop",
                details={"node_id": source_id},
                message="Academic-standards hierarchy relationships may not be self-loops.",
                record_id=relationship_id,
                source_export_order=relationship.source_export_order,
            )
        )

    if not isinstance(target_node, StandardNode):
        findings.append(
            _finding(
                code="relationship_target_not_item",
                details={"target_node_id": target_id},
                message="An academic-standards hierarchy relationship must target a framework item.",
                record_id=relationship_id,
                source_export_order=relationship.source_export_order,
            )
        )

    return target_node


def _validate_relationship_identity(
    *,
    findings: list[PackageValidationFinding],
    observed_edge_keys: dict[tuple[str, str, str], GraphRelationship],
    observed_relationship_ids: dict[str, GraphRelationship],
    profile: CurriculumProfile,
    relationship: GraphRelationship,
) -> bool:
    """Validate relationship identifiers, label/type agreement, and edge uniqueness.

    Parameters
    ----------
    findings
        Validation-local finding accumulator.
    observed_edge_keys
        Mutable lookup of already-seen type/source/target edge keys.
    observed_relationship_ids
        Mutable lookup of already-seen relationship identifiers.
    profile
        Selected immutable profile.
    relationship
        Decoded relationship under validation.

    Returns
    -------
    bool
        Whether the outer label and property relationship type agree.
    """

    relationship_id = str(relationship.relationship_id)
    source_id = str(relationship.source_node_id)
    target_id = str(relationship.target_node_id)

    if relationship.property_identifier != relationship.relationship_id:
        findings.append(
            _finding(
                code="relationship_identifier_mismatch",
                details={
                    "outer_identifier": relationship_id,
                    "property_identifier": (
                        str(relationship.property_identifier)
                        if relationship.property_identifier is not None
                        else None
                    ),
                },
                message="A relationship outer identifier and property identifier disagree.",
                record_id=relationship_id,
                source_export_order=relationship.source_export_order,
            )
        )

    if relationship_id in observed_relationship_ids:
        findings.append(
            _finding(
                code="relationship_identifier_duplicate",
                details={
                    "first_source_export_order": observed_relationship_ids[
                        relationship_id
                    ].source_export_order,
                    "second_source_export_order": relationship.source_export_order,
                },
                message="A relationship identifier occurs more than once in the package.",
                record_id=relationship_id,
                source_export_order=relationship.source_export_order,
            )
        )
    else:
        observed_relationship_ids[relationship_id] = relationship

    label_type_agree = relationship.label == relationship.relationship_type

    if not label_type_agree:
        findings.append(
            _finding(
                code="relationship_label_type_mismatch",
                details={
                    "outer_label": relationship.label,
                    "property_relationship_type": relationship.relationship_type,
                },
                message="A relationship outer label and property relationship type disagree.",
                record_id=relationship_id,
                source_export_order=relationship.source_export_order,
            )
        )
    elif relationship.label not in SUPPORTED_RELATIONSHIP_TYPES:
        findings.append(
            _finding(
                code="relationship_type_unsupported",
                details={"relationship_type": relationship.label},
                message="A relationship type is unsupported by the delivery schema.",
                record_id=relationship_id,
                source_export_order=relationship.source_export_order,
            )
        )
    elif (
        relationship.label == DELIVERY_SCHEMA_1_0_HIERARCHY_RELATIONSHIP_TYPE
        and relationship.label != profile.hierarchy.relationship_type
    ):
        findings.append(
            _finding(
                code="relationship_profile_type_mismatch",
                details={
                    "profile_relationship_type": profile.hierarchy.relationship_type,
                    "relationship_type": relationship.label,
                },
                message="A relationship type disagrees with the selected profile hierarchy.",
                record_id=relationship_id,
                source_export_order=relationship.source_export_order,
            )
        )

    if label_type_agree and relationship.relationship_type is not None:
        edge_key = (relationship.relationship_type, source_id, target_id)

        if edge_key in observed_edge_keys:
            findings.append(
                _finding(
                    code="relationship_edge_duplicate",
                    details={
                        "first_relationship_id": str(
                            observed_edge_keys[edge_key].relationship_id
                        ),
                        "relationship_type": relationship.relationship_type,
                        "second_relationship_id": relationship_id,
                        "source_node_id": source_id,
                        "target_node_id": target_id,
                    },
                    message="A relationship type/source/target triple occurs more than once.",
                    record_id=relationship_id,
                    source_export_order=relationship.source_export_order,
                )
            )
        else:
            observed_edge_keys[edge_key] = relationship

    return label_type_agree


def _validate_relationship_representation(
    *,
    findings: list[PackageValidationFinding],
    nodes_by_id: dict[str, GraphNode],
    package: LoadedGraphPackage,
) -> tuple[
    tuple[GraphRelationship, ...],
    dict[str, list[GraphRelationship]],
]:
    """Validate relationship identifiers, endpoints, labels, metadata, and duplicates.

    Parameters
    ----------
    findings
        Validation-local finding accumulator.
    nodes_by_id
        Unique first-observed node lookup.
    package
        Loaded package aggregate.

    Returns
    -------
    tuple[tuple[GraphRelationship, ...], dict[str, list[GraphRelationship]]]
        Resolved hierarchy relationships and incoming hierarchy edges by target.
    """

    profile = package.profile
    root = package.framework_root
    observed_relationship_ids: dict[str, GraphRelationship] = {}
    observed_edge_keys: dict[tuple[str, str, str], GraphRelationship] = {}
    resolved_hierarchy_relationships: list[GraphRelationship] = []
    incoming_relationships: dict[str, list[GraphRelationship]] = defaultdict(list)

    for relationship in package.relationships:
        relationship_id = str(relationship.relationship_id)
        target_id = str(relationship.target_node_id)
        label_type_agree = _validate_relationship_identity(
            findings=findings,
            observed_edge_keys=observed_edge_keys,
            observed_relationship_ids=observed_relationship_ids,
            profile=profile,
            relationship=relationship,
        )
        resolution_status = relationship.resolution_status

        if (
            resolution_status is not None
            and resolution_status
            not in DELIVERY_SCHEMA_1_0_RELATIONSHIP_STATUS_VOCABULARY
        ):
            findings.append(
                _finding(
                    code="relationship_status_unsupported",
                    details={"resolution_status": resolution_status},
                    message="A relationship status is unsupported by delivery schema 1.0.",
                    record_id=relationship_id,
                    source_export_order=relationship.source_export_order,
                )
            )

        target_node = _validate_relationship_endpoints(
            findings=findings,
            nodes_by_id=nodes_by_id,
            relationship=relationship,
            root=root,
        )

        if target_node is None:
            continue

        _validate_learning_component_topology(
            findings=findings,
            nodes_by_id=nodes_by_id,
            relationship=relationship,
            target_node=target_node,
        )

        if (
            label_type_agree
            and relationship.label == DELIVERY_SCHEMA_1_0_HIERARCHY_RELATIONSHIP_TYPE
            and isinstance(target_node, StandardNode)
        ):
            resolved_hierarchy_relationships.append(relationship)
            incoming_relationships[target_id].append(relationship)

    return tuple(resolved_hierarchy_relationships), dict(incoming_relationships)


def _validate_learning_component_topology(
    *,
    findings: list[PackageValidationFinding],
    nodes_by_id: Mapping[str, GraphNode],
    relationship: GraphRelationship,
    target_node: GraphNode,
) -> None:
    """Require supports edges to run learning component to item, and never hasChild.

    Parameters
    ----------
    findings
        Accumulating validation findings.
    nodes_by_id
        Decoded package nodes keyed by node identifier.
    relationship
        Decoded relationship under validation.
    target_node
        Already-resolved relationship target node.
    """

    relationship_id = str(relationship.relationship_id)
    source_node = nodes_by_id[str(relationship.source_node_id)]

    if relationship.label == DELIVERY_SCHEMA_1_1_SUPPORTS_RELATIONSHIP_TYPE:
        if not isinstance(source_node, LearningComponentNode):
            findings.append(
                _finding(
                    code="supports_source_not_learning_component",
                    details={"source_node_id": str(relationship.source_node_id)},
                    message="A supports relationship source is not a learning component.",
                    record_id=relationship_id,
                    source_export_order=relationship.source_export_order,
                )
            )

        if not isinstance(target_node, StandardNode):
            findings.append(
                _finding(
                    code="supports_target_not_standards_item",
                    details={"target_node_id": str(relationship.target_node_id)},
                    message=(
                        "A supports relationship target is not a standards framework item."
                    ),
                    record_id=relationship_id,
                    source_export_order=relationship.source_export_order,
                )
            )

        if relationship.support_confidence is None:
            findings.append(
                _finding(
                    code="supports_confidence_absent",
                    details={"relationship_id": relationship_id},
                    message="A supports relationship does not declare supportConfidence.",
                    record_id=relationship_id,
                    source_export_order=relationship.source_export_order,
                )
            )

        return

    if relationship.label != DELIVERY_SCHEMA_1_0_HIERARCHY_RELATIONSHIP_TYPE:
        return

    if isinstance(source_node, LearningComponentNode) or isinstance(
        target_node, LearningComponentNode
    ):
        findings.append(
            _finding(
                code="learning_component_in_hierarchy",
                details={
                    "source_node_id": str(relationship.source_node_id),
                    "target_node_id": str(relationship.target_node_id),
                },
                message=(
                    "A learning component appears in the hasChild hierarchy. Generated "
                    "content must not be reachable as source-asserted structure."
                ),
                record_id=relationship_id,
                source_export_order=relationship.source_export_order,
            )
        )


def _validate_root_reachability(
    *,
    adjacency: dict[str, list[str]],
    findings: list[PackageValidationFinding],
    package: LoadedGraphPackage,
) -> None:
    """Require every framework item to be reachable from the single framework root.

    Parameters
    ----------
    adjacency
        Directed hierarchy adjacency map.
    findings
        Validation-local finding accumulator.
    package
        Loaded package aggregate.
    """

    root_id = str(package.framework_root.node_id)
    reachable = {root_id}
    pending = [root_id]

    while pending:
        source_id = pending.pop()

        for target_id in adjacency.get(source_id, []):
            if target_id in reachable:
                continue

            reachable.add(target_id)
            pending.append(target_id)

    unreachable_items = sorted(
        str(node.node_id)
        for node in package.item_nodes
        if str(node.node_id) not in reachable
    )

    for node_id in unreachable_items:
        findings.append(
            _finding(
                code="item_unreachable_from_framework_root",
                details={"node_id": node_id},
                message="A framework item is not reachable from the single framework root.",
                record_id=node_id,
            )
        )


def _validate_root_statement_parents(
    *,
    findings: list[PackageValidationFinding],
    normal_incoming: list[GraphRelationship],
    root_id: str,
    statement_type: str,
    target: StandardNode,
) -> None:
    """Require a profile root-statement item to have exactly one framework-root parent.

    Parameters
    ----------
    findings
        Validation-local finding accumulator.
    normal_incoming
        Incoming hierarchy relationships without any resolution status.
    root_id
        Single framework-root identifier.
    statement_type
        Source statement type of the target item.
    target
        Decoded framework item being validated.
    """

    target_id = str(target.node_id)
    framework_parent_count = sum(
        str(relationship.source_node_id) == root_id for relationship in normal_incoming
    )

    if framework_parent_count != 1 or len(normal_incoming) != 1:
        findings.append(
            _finding(
                code="root_statement_parent_cardinality_mismatch",
                details={
                    "framework_parent_count": framework_parent_count,
                    "incoming_relationships": len(normal_incoming),
                    "statement_type": statement_type,
                    "target_node_id": target_id,
                },
                message="A profile root statement item must have exactly one framework-root parent.",
                record_id=target_id,
                source_export_order=target.source_export_order,
            )
        )


def validate_loaded_package(
    package: LoadedGraphPackage,
) -> tuple[PackageValidationFinding, ...]:
    """Perform complete semantic and graph-wide validation of one loaded package.

    Parameters
    ----------
    package
        Integrity-verified immutable package aggregate.

    Returns
    -------
    tuple[PackageValidationFinding, ...]
        Deterministically ordered package-wide findings.
    """

    findings: list[PackageValidationFinding] = []
    nodes_by_id = _validate_node_identifiers_and_labels(
        findings=findings, package=package
    )
    _validate_framework_and_profile_semantics(findings=findings, package=package)
    coded_items, text_items = _validate_item_semantics(
        findings=findings, package=package
    )
    (
        hierarchy_relationships,
        incoming_relationships,
    ) = _validate_relationship_representation(
        findings=findings, nodes_by_id=nodes_by_id, package=package
    )
    _validate_parent_policy(
        findings=findings,
        incoming_relationships=incoming_relationships,
        nodes_by_id=nodes_by_id,
        package=package,
    )
    _validate_cycle_and_reachability(
        findings=findings,
        hierarchy_relationships=hierarchy_relationships,
        package=package,
    )
    _validate_counts_capabilities_and_report(
        coded_items=coded_items,
        findings=findings,
        package=package,
        text_items=text_items,
    )
    _validate_learning_component_package(findings=findings, package=package)
    _validate_learning_component_semantics(findings=findings, package=package)
    return tuple(findings)


def _validate_learning_component_semantics(
    *, findings: list[PackageValidationFinding], package: LoadedGraphPackage
) -> None:
    """Validate learning-component node properties against the framework root.

    Parameters
    ----------
    findings
        Validation-local finding accumulator.
    package
        Loaded package aggregate.
    """

    root = package.framework_root

    for node in package.learning_component_nodes:
        node_id = str(node.node_id)
        inherited_comparisons = (
            (
                node.academic_subject,
                root.academic_subject,
                "learning component academic subject",
            ),
            (
                node.attribution_statement,
                root.attribution_statement,
                "learning component attribution statement",
            ),
            (node.license, root.license, "learning component source license"),
            (node.provider, root.provider, "learning component provider"),
        )

        for actual, expected, field_name in inherited_comparisons:
            _add_mismatch(
                actual=actual,
                code="learning_component_framework_metadata_mismatch",
                expected=expected,
                field_name=field_name,
                findings=findings,
                record_id=node_id,
                source_export_order=node.source_export_order,
            )

        published_standard_properties = (
            ("caseIdentifierURI", node.case_identifier_uri),
            ("caseIdentifierUUID", node.case_identifier_uuid),
            ("adoptionStatus", node.adoption_status),
            ("isCurrent", node.is_current),
            ("jurisdiction", node.jurisdiction),
        )

        for property_name, value in published_standard_properties:
            if value is None:
                continue

            findings.append(
                _finding(
                    code="learning_component_published_property_present",
                    details={"property_name": property_name},
                    message=(
                        "A learning component declares a property reserved for "
                        "published standards."
                    ),
                    record_id=node_id,
                    source_export_order=node.source_export_order,
                )
            )

        required_properties = (
            ("academicSubject", node.academic_subject),
            ("attributionStatement", node.attribution_statement),
            ("author", node.author),
            ("identifier", node.property_identifier),
            ("inLanguage", node.in_language),
            ("license", node.license),
            ("provider", node.provider),
        )

        for property_name, value in required_properties:
            if value is not None and str(value).strip():
                continue

            findings.append(
                _finding(
                    code="learning_component_required_property_absent",
                    details={"property_name": property_name},
                    message=(
                        "A learning component omits a property required by the "
                        "Learning Commons contract."
                    ),
                    record_id=node_id,
                    source_export_order=node.source_export_order,
                )
            )


def _validate_learning_component_package(
    *, findings: list[PackageValidationFinding], package: LoadedGraphPackage
) -> None:
    """Validate package-level learning-component invariants.

    Requires every learning component to be reachable by at least one ``supports``
    edge, and the manifest counts to agree with the decoded content.

    Parameters
    ----------
    findings
        Validation-local finding accumulator.
    package
        Loaded package aggregate.
    """

    components = package.learning_component_nodes
    counts = package.manifest.counts
    supports_relationships = tuple(
        relationship
        for relationship in package.relationships
        if relationship.label == DELIVERY_SCHEMA_1_1_SUPPORTS_RELATIONSHIP_TYPE
    )

    supported_component_ids = {
        str(relationship.source_node_id) for relationship in supports_relationships
    }

    for component in components:
        if str(component.node_id) not in supported_component_ids:
            findings.append(
                _finding(
                    code="learning_component_without_supports_edge",
                    details={"node_id": str(component.node_id)},
                    message=(
                        "A learning component declares no supports relationship and is "
                        "unreachable from any standard."
                    ),
                    record_id=str(component.node_id),
                    source_export_order=component.source_export_order,
                )
            )

    count_comparisons = (
        (
            "learning_component_nodes",
            len(components),
            counts.learning_component_nodes,
        ),
        (
            "supports_relationships",
            len(supports_relationships),
            counts.supports_relationships,
        ),
    )

    for count_name, observed_count, declared_count in count_comparisons:
        if observed_count != declared_count:
            findings.append(
                _finding(
                    code="learning_component_count_mismatch",
                    details={
                        "count_name": count_name,
                        "declared_count": declared_count,
                        "observed_count": observed_count,
                    },
                    message=(
                        "Declared learning-component counts do not agree with decoded "
                        "package content."
                    ),
                )
            )
