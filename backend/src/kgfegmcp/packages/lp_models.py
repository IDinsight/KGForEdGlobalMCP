"""LP acceptance contracts and bounded, immutable runtime evidence projections."""

# Standard Library
from typing import Annotated, Literal

# Third Party Library
from pydantic import ConfigDict, Field, StrictBool, StrictFloat, StrictInt, StrictStr

# Package Library
from kgfegmcp.domain.identifiers import CaseIdentifierUuid, RelationshipId
from kgfegmcp.schemas import FrozenSchema

Count = Annotated[StrictInt, Field(ge=0)]
Decision = Literal["buildsTowards", "relatesTo", "no_relation", "needs_review"]
RawHash = Annotated[StrictStr, Field(pattern=r"^[0-9a-f]{64}$")]


class SourceEvidence(FrozenSchema):
    """Parse retained snake-case evidence without rewriting unknown producer fields."""

    model_config = ConfigDict(alias_generator=None, extra="ignore")


# Source types follow their dependencies.
class Candidate(SourceEvidence):
    """Require the source candidate identity and its available evidence."""

    admissible_decisions: tuple[dict[str, object], ...]
    evidence: tuple[dict[str, object], ...]
    first_sfi_uuid: CaseIdentifierUuid
    pair_id: StrictStr
    second_sfi_uuid: CaseIdentifierUuid
    warnings: tuple[StrictStr, ...]


class CycleDiagnostics(SourceEvidence):
    """Read structural-only producer cycle diagnostics."""

    components: tuple[object, ...]
    cyclic_component_count: Count
    cyclic_edge_count: Count
    cyclic_node_count: Count
    graph_edge_count: Count
    graph_node_count: Count


class Eligibility(SourceEvidence):
    """Retain the upstream selection denominators and exclusion policy."""

    config_content_hash: RawHash
    eligible_sfis_content_hash: RawHash
    eligible_sfis_per_relationship: dict[StrictStr, Count]
    exclusion_reason_counts_per_relationship: dict[StrictStr, dict[StrictStr, Count]]
    framework_uuid: CaseIdentifierUuid
    total_sfis_considered: Count
    total_sfis_eligible: Count
    total_sfis_excluded: Count
    unresolved_participation: StrictStr
    unresolved_sfis_considered: Count
    unresolved_sfis_eligible: Count
    unresolved_sfis_excluded: Count
    unresolved_sfis_policy_excluded: Count
    upstream_content_hash: RawHash


class Judgment(SourceEvidence):
    """Require a finite model confidence and the complete stored explanation."""

    confidence: Annotated[
        StrictFloat | StrictInt, Field(allow_inf_nan=False, ge=0, le=1)
    ]
    decision: Decision
    direction: Literal["first_to_second", "second_to_first"] | None
    first_sfi_uuid: CaseIdentifierUuid
    pair_id: StrictStr
    rationale: StrictStr
    second_sfi_uuid: CaseIdentifierUuid
    warnings: tuple[StrictStr, ...]


class RequestManifest(SourceEvidence):
    """Require request-set identities and available source/config fingerprints."""

    artifact_byte_hashes: dict[StrictStr, RawHash]
    candidate_pairs_content_hash: RawHash
    candidate_summary_content_hash: RawHash
    config_content_hash: RawHash
    doc_key: RawHash
    eligible_sfis_content_hash: RawHash
    framework_uuid: CaseIdentifierUuid
    pair_ids: tuple[StrictStr, ...]
    request_ids: tuple[StrictStr, ...]
    requests_content_hash: RawHash
    total_candidate_pairs: Count
    total_requests: Count
    upstream_content_hash: RawHash


class SourceFramework(SourceEvidence):
    """Require source credit separately from LP generator credit."""

    attribution_statement: StrictStr
    author: StrictStr
    case_identifier_uuid: CaseIdentifierUuid
    license: StrictStr
    provider: StrictStr
    title: StrictStr


class Trace(SourceEvidence):
    """Require producer/checker trace identities without keeping them at runtime."""

    checker_checkpoint_content_hash: RawHash
    checker_outcome: Literal["accepted", "corrected"]
    checker_prompt_content_hash: RawHash
    checker_verdict_content_hash: RawHash
    execution_content_hash: RawHash
    judgment_content_hash: RawHash
    producer_checkpoint_content_hash: RawHash
    producer_judgment: Judgment
    producer_prompt_content_hash: RawHash
    producer_response_content_hash: RawHash
    request_content_hash: RawHash
    request_id: StrictStr
    response_checkpoint_content_hash: RawHash
    response_content_hash: RawHash


class Claim(SourceEvidence):
    """Read final accepted and nonpublishing decisions."""

    candidate: Candidate
    judgment: Judgment
    provenance: Trace
    source_sfi_uuid: CaseIdentifierUuid | None
    target_sfi_uuid: CaseIdentifierUuid | None


class FinalClaims(SourceEvidence):
    """Read final decisions independently of the exported edge maps."""

    checkpoint_receipt_byte_hash: RawHash
    claims: tuple[Claim, ...]
    content_hash: RawHash
    cycle_diagnostics: CycleDiagnostics
    decision_counts: dict[Decision, Count]
    execution_material: dict[str, object]
    graph_status: Literal["acyclic"]
    request_manifest: RequestManifest
    total_claims: Count


class Provenance(SourceEvidence):
    """Require identity, source credit and available generation input/config hashes."""

    approved_by: StrictStr
    attribution_statement_template: StrictStr
    candidate_artifact_byte_hashes: dict[StrictStr, RawHash]
    candidate_pairs_content_hash: RawHash
    candidate_summary_content_hash: RawHash
    claim: Claim
    config_content_hash: RawHash
    doc_key: RawHash
    effective_lp_config_content_hash: RawHash
    final_claims_content_hash: RawHash
    model_configuration: dict[str, object]
    model_configuration_content_hash: RawHash
    model_settings: dict[str, object]
    model_settings_content_hash: RawHash
    relationship_identity_key: StrictStr
    requests_content_hash: RawHash
    source_framework: SourceFramework
    upstream_content_hash: RawHash


class Summary(SourceEvidence):
    """Read report references, selection limits and source counts."""

    artifact_byte_hashes: dict[StrictStr, RawHash]
    content_hash: RawHash
    decision_counts: dict[Decision, Count]
    eligibility: Eligibility | None = None
    input_artifact_byte_hashes: dict[StrictStr, RawHash]
    input_content_hashes: dict[StrictStr, RawHash]
    object_counts: dict[StrictStr, Count]
    relationships_final_claims_content_hash: RawHash
    validation_report_content_hash: RawHash
    validation_report_passed: StrictBool


class Unresolved(SourceEvidence):
    """Read decisions explicitly excluded from delivery."""

    claims: tuple[Claim, ...]
    content_hash: RawHash
    final_claims_content_hash: RawHash
    total_needs_review: Count


class ValidationReport(SourceEvidence):
    """Require structural/process integrity evidence without semantic certification."""

    content_hash: RawHash
    cycle_diagnostics: CycleDiagnostics
    errors: tuple[StrictStr, ...]
    input_content_hashes: dict[StrictStr, RawHash]
    object_counts: dict[StrictStr, Count]
    passed: StrictBool
    pedagogical_correctness_established: StrictBool
    semantic_scope_notice: StrictStr
    semantic_validation_performed: StrictBool
    validation_checks: tuple[StrictStr, ...]
    warnings: tuple[StrictStr, ...]


# Runtime projections contain only scalars and tuples, with no rich mutable maps.
class CoverageProjection(FrozenSchema):
    """Preserve structural-only counts, eligibility denominators and policy limits."""

    eligible_sfis_per_relationship: tuple[tuple[str, int], ...] | None
    exclusion_reason_counts: tuple[tuple[str, str, int], ...] | None
    needs_review_claims: Count
    no_relation_claims: Count
    semantic_scope_notice: StrictStr
    total_sfis_considered: Count | None
    total_sfis_eligible: Count | None
    total_sfis_excluded: Count | None
    unresolved_participation: StrictStr | None
    unresolved_sfis_counts: tuple[tuple[str, int], ...] | None
    unresolved_warning_pairs: Count
    validation_warning_count: Count
    validation_warning_excerpts: tuple[StrictStr, ...]
    validation_warnings_excerpted: StrictBool
    validation_warnings_omitted: StrictBool


class JudgmentProjection(FrozenSchema):
    """Keep bounded model explanation excerpts with explicit omission metadata."""

    confidence: Annotated[float, Field(allow_inf_nan=False, ge=0, le=1)]
    confidence_notice: str = (
        "Confidence is a model judgment, not validated pedagogical correctness."
    )
    rationale_excerpt: Annotated[StrictStr, Field(max_length=512)]
    rationale_excerpted: bool
    relationship_id: RelationshipId
    warning_count: Count
    warning_excerpts: Annotated[
        tuple[Annotated[StrictStr, Field(max_length=512)], ...], Field(max_length=5)
    ]
    warnings_excerpted: bool
    warnings_omitted: bool


class LearningProgressionEvidence(FrozenSchema):
    """Retain only validated query projections; complete evidence stays on disk."""

    coverage: CoverageProjection
    judgments: tuple[JudgmentProjection, ...]
