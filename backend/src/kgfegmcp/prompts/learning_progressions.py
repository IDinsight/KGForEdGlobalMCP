"""Render bounded client retrieval of stored curriculum and teaching evidence."""

# Standard Library
import hashlib
import json

from collections.abc import Mapping
from typing import Annotated, Final, Self

# Third Party Library
from pydantic import Field, TypeAdapter, ValidationError, model_validator

# Package Library
from kgfegmcp.catalog.models import CatalogPackageRuntime
from kgfegmcp.domain.identifiers import FrameworkId, LanguageTag, SnapshotId
from kgfegmcp.errors import InvalidProgressionRequestError
from kgfegmcp.prompts.models import (
    LearningProgressionTeachingSequenceRequest,
    PromptFocusMode,
    PromptLocalContext,
)
from kgfegmcp.resources.uri import learning_progressions_uri
from kgfegmcp.schemas import FrozenSchema
from kgfegmcp.services.lp_discovery import normalize_progression_filters
from kgfegmcp.services.lp_models import (
    EndpointScope,
    ProgressionFilters,
    ProgressionStandardIdentifier,
    RelationshipTypes,
)
from kgfegmcp.services.models import StandardIdentifier

CurriculumReviewSelectors = Annotated[
    tuple[ProgressionStandardIdentifier, ...], Field(max_length=20)
]

# Fixed orders keep rendering deterministic and give each kind/type its own budget,
# so buildsTowards (listed first by discovery) cannot starve relatesTo.
_DIRECT_CONNECTION_KINDS: Final[tuple[str, ...]] = (
    "outgoing_builds",
    "incoming_builds",
    "related",
)
_REVIEW_RELATIONSHIP_TYPES: Final[tuple[str, ...]] = ("buildsTowards", "relatesTo")


class LearningProgressionCurriculumReviewRequest(ProgressionFilters):
    """Reuse exact discovery selectors and facets for a bounded client review."""

    endpoint_scope: EndpointScope = "either"
    framework_id: FrameworkId
    local_context: PromptLocalContext | None = None
    output_language: LanguageTag | None = None
    relationship_types: RelationshipTypes = ()
    snapshot_id: SnapshotId | None = None
    standard_identifiers: CurriculumReviewSelectors = ()

    @model_validator(mode="after")
    def validate_selectors(self) -> Self:
        """Reject repeated types or selectors and overlong selector text.

        Returns
        -------
        Self
            Bounded request preserving exact namespaces for client resolution.

        Raises
        ------
        ValueError
            If a relationship type or selector repeats, or any selector text
            exceeds 512 characters.
        """

        # Same rule search_learning_progressions applies to its relationshipTypes.
        if len(self.relationship_types) != len(set(self.relationship_types)):
            raise ValueError("Curriculum-review relationship types must be unique.")

        keys = [item.model_dump_json() for item in self.standard_identifiers]

        if len(keys) != len(set(keys)):
            raise ValueError("Curriculum-review standard selectors must be unique.")

        for item in self.standard_identifiers:
            values = item.model_dump(exclude={"identifier_type"}).values()

            if any(len(value) > 512 or not value.strip() for value in values):
                raise ValueError("Selector text must contain 1 through 512 characters.")

        return self


class LearningProgressionSupportPlanRequest(FrozenSchema):
    """Bound exact-target support inputs using existing standard selector models."""

    framework_id: FrameworkId
    identifier: StandardIdentifier
    local_context: PromptLocalContext | None = None
    output_language: LanguageTag | None = None
    snapshot_id: SnapshotId | None = None

    @model_validator(mode="after")
    def validate_selector_size(self) -> Self:
        """Keep each caller-supplied exact selector within the prompt text bound.

        Returns
        -------
        Self
            Validated request preserving the existing opaque identifier namespace.

        Raises
        ------
        ValueError
            If the exact selector text exceeds 512 characters.
        """

        values = self.identifier.model_dump(exclude={"identifier_type"}).values()

        if any(len(value) > 512 for value in values):
            raise ValueError(
                "Support-plan selector text must not exceed 512 characters."
            )

        return self


def _direct_kind_calls(
    *, route: Mapping[str, object], selector: Mapping[str, object]
) -> tuple[str, ...]:
    """Render one single-page direct call per connection kind for one standard.

    Parameters
    ----------
    route
        Exact framework and snapshot shared by every call.
    selector
        Outer node selector with the client-substituted placeholder.

    Returns
    -------
    tuple[str, ...]
        Labelled get_standard_progressions templates in the fixed kind order.

    Examples
    --------
    >>> _direct_kind_calls(route=route, selector=selector)[0]
    '- outgoing_builds:'
    """

    lines: list[str] = []

    for kind in _DIRECT_CONNECTION_KINDS:
        lines.extend(
            (
                f"- {kind}:",
                _tool_call(
                    {
                        **route,
                        "connectionKind": kind,
                        "identifier": selector,
                        "limit": 25,
                    }
                ),
            )
        )

    return tuple(lines)


def _render_focus(
    *,
    filters: ProgressionFilters,
    request: LearningProgressionTeachingSequenceRequest,
    route: Mapping[str, object],
) -> tuple[str, ...]:
    """Render topic/code discovery or a namespaced exact standard lookup.

    Parameters
    ----------
    filters
        Canonical profile-validated grade filters.
    request
        Strict bounded prompt inputs.
    route
        Pinned camel-case framework and snapshot selectors.

    Returns
    -------
    tuple[str, ...]
        Client selection instructions and a valid existing-tool argument template.

    Raises
    ------
    InvalidProgressionRequestError
        If an exact identifier is malformed.
    """

    if request.focus_mode in (PromptFocusMode.TOPIC, PromptFocusMode.STATEMENT_CODE):
        search: dict[str, object] = {
            "frameworkIds": [route["frameworkId"]],
            "limit": 10,
            "localGradeLabels": list(filters.local_grade_labels),
            "mode": (
                "text" if request.focus_mode is PromptFocusMode.TOPIC else "code_exact"
            ),
            "normalizedGrades": list(filters.normalized_grades),
            "query": request.topic_or_standard,
            "snapshotIds": [route["snapshotId"]],
        }

        if request.focus_mode is PromptFocusMode.TOPIC:
            search["match"] = {"matchMode": "tokens", "operator": "all"}

        return (
            "1. Call search_standards once with this input; inspect only the first "
            "page of 10. Do not follow nextCursor or issue expanded searches here:",
            _tool_call(search),
            "Retain up to 3 explicitly identified standard items, reporting the "
            "selection basis and excluded hits. Search rank and shared wording "
            "are retrieval aids, not progression evidence. Preserve ambiguity and "
            "partial code coverage; do not guess an exact match.",
        )

    field = {
        PromptFocusMode.CASE_IDENTIFIER_URI: "caseIdentifierUri",
        PromptFocusMode.CASE_IDENTIFIER_UUID: "caseIdentifierUuid",
        PromptFocusMode.NODE_ID: "nodeId",
    }[request.focus_mode]

    try:
        selector: StandardIdentifier = TypeAdapter(StandardIdentifier).validate_python(
            {
                "identifierType": request.focus_mode.value,
                field: request.topic_or_standard,
            }
        )
    except ValidationError as error:
        raise InvalidProgressionRequestError(
            message="Teaching-sequence exact standard identifier is invalid.",
            recovery_hint="Use the exact identifier namespace selected by focus_mode.",
        ) from error
    return (
        "1. Call get_standard with this exact namespaced input:",
        _tool_call(
            {**route, "identifier": selector.model_dump(by_alias=True, mode="json")}
        ),
        "Retain that one exact standard and its outer nodeId. Do not reinterpret "
        "the selector or silently add standards. Check the returned grade facets "
        "against the supplied filters: values within a field are OR, local and "
        "normalized fields are AND. A mismatch is out of scope; report it and stop.",
    )


def _render_progressions(route: Mapping[str, object]) -> tuple[str, ...]:
    """Render finite direct, downstream and conditional path retrieval.

    Parameters
    ----------
    route
        Exact framework and snapshot shared by every call.

    Returns
    -------
    tuple[str, ...]
        Bounded stored-edge instructions with complete nested tool templates.
    """

    selector = {"identifierType": "node_id", "nodeId": "<selected-node-id>"}
    return (
        "3. For each of at most 3 retained standards, call get_standard_progressions "
        "three times, once per connection kind in this order (at most 9 direct calls "
        "in total). Each call reads one page: limit 25 is the maximum requested and "
        "a size-limited page may return fewer; do not follow nextCursor. A non-null "
        "nextCursor means that kind is incomplete for that standard; report it:",
        *_direct_kind_calls(route=route, selector=selector),
        "Keep results grouped by kind and deduplicate relationship IDs across calls "
        "and standards. Outgoing and incoming builds are directional steps. relatesTo "
        "is read from either endpoint but retains its canonical stored orientation; "
        "it supplies related concepts, never sequence hops.",
        "4. For each retained standard call traverse_learning_progressions once "
        "with this bounded downstream request:",
        _tool_call(
            {
                **route,
                "direction": "downstream",
                "identifier": selector,
                "maxDepth": 8,
                "maxEdges": 40,
                "maxNodes": 30,
            }
        ),
        "5. Only when two of the retained standards are explicitly selected for "
        "connection, call get_learning_progression_paths once in the selected "
        "source-to-target direction, with distinct endpoints:",
        _tool_call(
            {
                **route,
                "maxDepth": 6,
                "maxPaths": 3,
                "sourceIdentifier": {
                    "identifierType": "node_id",
                    "nodeId": "<source-node-id>",
                },
                "targetIdentifier": {
                    "identifierType": "node_id",
                    "nodeId": "<target-node-id>",
                },
            }
        ),
        "Replace only named node placeholders using the retained exact IDs. Do not "
        "probe every pair, reverse the chosen direction automatically, expand limits "
        "or rerun to bypass a bound. Traversal/paths use buildsTowards only. Every "
        "hop must cite an existing correctly directed relationship ID; retain "
        "alternative paths and branching/merging evidence, not a single forced order.",
    )


def _render_support_progressions(route: Mapping[str, object]) -> tuple[str, ...]:
    """Render separate incoming/related pages and bounded upstream support.

    Parameters
    ----------
    route
        Exact framework/snapshot selected once for all retrieval.

    Returns
    -------
    tuple[str, ...]
        Valid nested-request templates and finite client inspection instructions.
    """

    selector = {"identifierType": "node_id", "nodeId": "<target-node-id>"}
    return (
        "2. Call get_standard_progressions once for incoming builds. It reads one "
        "page; limit 25 is the maximum requested and a size-limited page may return "
        "fewer; do not follow nextCursor. A non-null nextCursor means incoming "
        "builds are incomplete for the target; report it:",
        _tool_call(
            {
                **route,
                "connectionKind": "incoming_builds",
                "identifier": selector,
                "limit": 25,
            }
        ),
        "3. Call get_standard_progressions once for related concepts. It reads one "
        "page; limit 25 is the maximum requested and a size-limited page may return "
        "fewer; do not follow nextCursor. A non-null nextCursor means related "
        "concepts are incomplete for the target; report it:",
        _tool_call(
            {**route, "connectionKind": "related", "identifier": selector, "limit": 25}
        ),
        "Preserve the original IDs/orientation; incoming buildsTowards points from "
        "a supporting source to this target. relatesTo is accessible from either "
        "endpoint but its canonical stored orientation is not a teaching direction. "
        "Keep related concepts separate from directional support and sequencing.",
        "4. Call traverse_learning_progressions once for upstream support:",
        _tool_call(
            {
                **route,
                "direction": "upstream",
                "identifier": selector,
                "maxDepth": 3,
                "maxEdges": 30,
                "maxNodes": 20,
            }
        ),
        "Use buildsTowards only; retain branching/merging alternatives, exact edge "
        "directions, depth/distances and frontier/completeness. Each used hop must "
        "cite its original relationship ID. Derived multi-hop support is not an "
        "asserted direct edge. Do not reverse stored arrows, use hasChild/relatesTo "
        "as support hops, enlarge bounds or rerun to bypass a limit.",
    )


def _tool_call(request: Mapping[str, object]) -> str:
    """Encode one existing tool's nested request as deterministic client input.

    Parameters
    ----------
    request
        Exact camel-case fields, with explicitly named client substitutions.

    Returns
    -------
    str
        Canonical JSON argument object with the required request wrapper.
    """

    return json.dumps({"request": request}, ensure_ascii=False, sort_keys=True)


def render_curriculum_review_workflow(
    *,
    request: LearningProgressionCurriculumReviewRequest,
    runtime: CatalogPackageRuntime,
) -> str:
    """Render pinned discovery and provenance inspection without executing queries.

    Parameters
    ----------
    request
        Strict bounded selectors, endpoint scope, facets and caller context.
    runtime
        Shared accepted runtime already routed and derivative-rights checked.

    Returns
    -------
    str
        Deterministic client retrieval sequence with explicit review limits.
    """

    identity = runtime.catalog_package.package_identity
    filters = normalize_progression_filters(request=request, runtime=runtime)
    route: dict[str, object] = {
        "frameworkId": str(identity.framework_id),
        "snapshotId": str(identity.snapshot_id),
    }
    lines = [
        "PINNED EVIDENCE IDENTITY\n"
        f"Profile SHA-256: {runtime.loaded_package.profile_sha256}\n"
        "Manifest SHA-256: sha256:"
        f"{hashlib.sha256(runtime.loaded_package.manifest_bytes).hexdigest()}\n"
        "Use this exact framework/snapshot in every call; never reroute to current. "
        "Retain source-artifact hashes, rights and attribution separately from "
        "caller observations and generated review questions.",
        "1. Call get_framework_statistics once for package-wide structural and "
        "separate stored LP counts; these are not filtered review counts:",
        _tool_call(route),
    ]

    if not runtime.catalog_package.capabilities.has_learning_progressions:
        lines.append(
            "STORED LP CAPABILITY UNAVAILABLE in this pinned package. Skip all LP "
            "tools/resources and dependent relationship review. Report unavailable "
            "evidence alongside permitted package statistics; do not equate this "
            "with zero relationships, infer curriculum omission or use an "
            "inferred-edge fallback."
        )
        return "\n".join(lines)

    scan_types = tuple(
        relationship_type
        for relationship_type in _REVIEW_RELATIONSHIP_TYPES
        if not request.relationship_types
        or relationship_type in request.relationship_types
    )
    scan_calls: list[str] = []

    # Every scan shares identical filters, selectors, scope and limit; only the
    # single relationship type differs.
    for relationship_type in scan_types:
        scan_calls.extend(
            (
                f"- {relationship_type} scan:",
                _tool_call(
                    {
                        **route,
                        **filters.model_dump(by_alias=True, mode="json"),
                        "endpointScope": request.endpoint_scope,
                        "limit": 25,
                        "relationshipTypes": [relationship_type],
                        "standardIdentifiers": [
                            item.model_dump(by_alias=True, mode="json")
                            for item in request.standard_identifiers
                        ],
                    }
                ),
            )
        )

    lines.extend(
        (
            "2. Read the sanitized LP summary and its validation, unresolved and "
            "generation-summary artifact links within resource policy:",
            learning_progressions_uri(
                framework_id=identity.framework_id, snapshot_id=identity.snapshot_id
            ),
            "Read linked learningProgressionValidation, learningProgressionUnresolved "
            "and learningProgressionSummary only when permitted and within byte "
            "limits. The raw generation summary is bulk content and may be denied; "
            "keep the public sanitized summary and disclose denied evidence. Do not "
            "read bulk provenance maps, raise limits or retry to bypass policy. "
            "Retain warnings, needs_review/no_relation exclusions, selected candidate "
            "coverage, unknown eligibility denominators and structural-only "
            "validation. Zero incidents do not erase individual edge warnings.",
            "3. Run one separate search_learning_progressions scan per selected "
            "relationship type, in this fixed order: "
            f"{', '.join(scan_types)}. Each scan has its own budget of at most 3 "
            "pages, so one type never uses up another type's pages. limit 25 is the "
            "maximum requested per page; a page may return fewer relationships "
            "because of the result-size ceiling. Record each page's actual "
            "returnedCount, examinedCount, totalMatchingCount, stoppingReason, "
            "nextCursor and isComplete. First-page request of each scan:",
            *scan_calls,
            "Pass every exact supplied selector through standardIdentifiers; never "
            "replace it with topic search or silently skip unresolved/ambiguous "
            "selectors. Retain resolvedStandardNodeIds and effective filters from "
            "the result. A failed selection stops dependent review. For pages 2 "
            "and 3 of a scan only, copy that scan's identical request and add "
            "cursor equal to that scan's preceding page.nextCursor; never reuse a "
            "cursor from another scan. Stop a scan on null; never follow a fourth "
            "page of a scan, restart pagination or change filters/limit to bypass "
            "a cap. A zero-match work-limited page still consumes one of that "
            "scan's pages and may continue. A remaining cursor after a scan's "
            "third page means that type's review is incomplete.",
            "Values within each field are OR; different fields and selector "
            "membership are AND on one endpoint. either means at least one endpoint "
            "satisfies the whole conjunction; both means each does; source/target "
            "mean stored orientation. Never mix grade/type criteria across "
            "endpoints. For relatesTo, source/target is canonical order, not "
            "instructional direction. Keep per-endpoint matched facets.",
            "4. Deduplicate returned relationships by exact ID. Select at most 10 "
            "distinct relationships in total for full inspection. When two types "
            "were scanned and both returned relationships, select up to 5 per type "
            "and give any unused slots to the other type; otherwise select up to 10 "
            "from the type that returned relationships. Explain the selection, type "
            "balance, warnings and excluded items. For each selected relationship "
            "call get_learning_progression once:",
            _tool_call({**route, "relationshipId": "<selected-relationship-id>"}),
            "Replace the placeholder only with a returned relationship ID. Read its "
            "exact relationshipUri and full provenanceUri under resource policy. "
            "Inspect at most 10 distinct full edge-provenance resources across the "
            "entire workflow. Preserve exact endpoint standard URIs/IDs, stored "
            "direction, rationale, model-judgment confidence, all warnings, candidate "
            "references, producer/checker trace and source/config/content hashes. "
            "Returned excerpts or clipped warnings are not full provenance. Every "
            "edge used in a recommendation must be fully inspected; reduce or "
            "clearly defer recommendations beyond the cap or with denied/oversized "
            "evidence. Do not substitute uninspected links as recommendations.",
            "5. Before composition, report separately for each scanned type its "
            "package-wide stored total (statistics/summary), its filtered matching "
            "count when known, pages read, distinct returned relationships and "
            "fully inspected count. Retain each page's examinedCount, "
            "returnedCount, totalMatchingCount, nextCursor, isComplete and "
            "stoppingReason. Never sum candidateCount, matching counts or package "
            "totals across pages or across types, and never treat one type's "
            "coverage as the other's. Null totals/unknown denominators stay "
            "unknown; returned relationships are a bounded sample, not global "
            "coverage. A remaining cursor after a scan's third page means that "
            "type's review is incomplete. Explain "
            "unavailable, empty, sparse, clipped, incomplete and policy-denied "
            "evidence; absence never implies curriculum omission or alignment.",
            "Compose evidence-linked review questions only after permitted "
            "retrieval. Keep caller observations, source standards, stored "
            "generated judgments and generated suggestions distinct. Never invent "
            "a missing edge or cross-framework/snapshot alignment, certify "
            "curriculum quality, or turn structural validation into pedagogy.",
        )
    )
    return "\n".join(lines)


def render_optional_progression_workflow(*, runtime: CatalogPackageRuntime) -> str:
    """Render optional stored links without changing the role's useful core output.

    Parameters
    ----------
    runtime
        Already selected accepted runtime, including exact capability and identity.

    Returns
    -------
    str
        Shared finite retrieval and citation instructions, or unavailable disclosure.
    """

    if not runtime.catalog_package.capabilities.has_learning_progressions:
        return (
            "OPTIONAL STORED PROGRESSION EVIDENCE: CAPABILITY UNAVAILABLE in this "
            "pinned package. Skip LP tools/resources, disclose unavailable evidence "
            "and continue the existing standards/component workflow and useful "
            "output. Do not invent edges or use an inferred-edge fallback."
        )

    identity = runtime.catalog_package.package_identity
    route = {
        "frameworkId": str(identity.framework_id),
        "snapshotId": str(identity.snapshot_id),
    }
    selector = {"identifierType": "node_id", "nodeId": "<selected-node-id>"}
    return "\n".join(
        (
            "OPTIONAL STORED PROGRESSION EVIDENCE (after exact standard selection)",
            "Use stored links only when useful to this role's requested output. "
            "Retain at most 3 distinct already-resolved standards for this optional "
            "step across the entire workflow, including all grades in a multigrade "
            "room; explain selection and omitted standards. This cap does not "
            "replace the existing standards, shared-component or grade workflow.",
            "For each retained standard, call get_standard_progressions three "
            "times, once per connection kind in this order, at most 9 calls in "
            "total. Each call reads one page: limit 25 is the maximum requested and "
            "a size-limited page may return fewer. Replace <selected-node-id> with "
            "its exact node ID; do not follow nextCursor, traverse, request paths or "
            "expand through returned neighbors. A non-null nextCursor means that "
            "kind is incomplete for that standard; report it:",
            *_direct_kind_calls(route=route, selector=selector),
            "Keep results grouped by kind (outgoing builds, incoming builds, related "
            "concepts) and deduplicate relationship IDs across calls and standards. "
            "buildsTowards follows stored source-to-target direction and may "
            "motivate an optional teaching order, not a mandatory prerequisite or "
            "proof of learner mastery/readiness. relatesTo is readable from either "
            "endpoint but retains canonical stored orientation and has no "
            "sequence/dependency meaning. Neither hasChild nor supports nor shared "
            "Learning Components establish LP edges.",
            "Read the sanitized LP summary if using this optional evidence:",
            learning_progressions_uri(
                framework_id=identity.framework_id, snapshot_id=identity.snapshot_id
            ),
            "Preserve package-wide totals separately from the returned and reviewed "
            "subset; never equate them. Retain coverage notices, warnings, "
            "needs_review/no_relation exclusions, unknown denominators and linked "
            "validation/unresolved evidence when material and permitted. Do not "
            "invent percentages. Structural-only validation does not establish "
            "semantic or pedagogical correctness.",
            "Before using any edge in a recommendation, call get_learning_progression "
            "for its exact returned relationship ID and read its full provenanceUri:",
            _tool_call({**route, "relationshipId": "<returned-relationship-id>"}),
            "Inspect at most 10 distinct full edge-provenance resources in this "
            "entire workflow, deduplicating relationship IDs across standards. "
            "Preserve original rationale, model-judgment confidence, all warnings, "
            "candidate references, producer/checker trace and source/config/content "
            "hashes. Cite exact relationshipUri and provenanceUri with endpoint "
            "node/CASE IDs, framework, snapshot, package and attribution. Excerpts "
            "or clipped warnings are not full provenance. Reduce or clearly defer "
            "recommendations needing over-cap, unread or denied provenance.",
            "Use get_learning_components_for_standard through the existing exact "
            "support links for retained standards; reuse earlier results. Keep "
            "component/support IDs and URIs, confidence, supportedStandards and "
            "their grade evidence, and inspect material linked component provenance "
            "under policy. Preserve existing hierarchy/DAG and shared-core behavior; "
            "a shared component does not create an LP edge or grade equivalence.",
            "Retain all query bounds, cursors, counts and completeness/truncation "
            "flags. Distinguish unavailable, empty, sparse, incomplete and "
            "rights/byte-denied evidence. No bulk-map reads or retries to bypass "
            "policy. If optional evidence cannot be used, continue the original "
            "useful output from permitted standards/components with explicit "
            "limitations. Absence of returned evidence does not establish "
            "curriculum omission, no pedagogical connection or cross-framework "
            "alignment. Never invent a replacement progression edge. Keep caller "
            "observations, source standards, stored generated judgments and "
            "generated teaching/study suggestions visibly separate.",
        )
    )


def render_support_plan_workflow(
    *, request: LearningProgressionSupportPlanRequest, runtime: CatalogPackageRuntime
) -> str:
    """Render pinned support evidence without searching, diagnosing or composing.

    Parameters
    ----------
    request
        Validated exact target and untrusted teacher context.
    runtime
        Shared accepted runtime already routed and rights-checked by PromptService.

    Returns
    -------
    str
        Deterministic mandatory client retrieval with finite inspection caps.
    """

    identity = runtime.catalog_package.package_identity
    route: dict[str, object] = {
        "frameworkId": str(identity.framework_id),
        "snapshotId": str(identity.snapshot_id),
    }
    target = {"identifierType": "node_id", "nodeId": "<target-node-id>"}
    supporting = {"identifierType": "node_id", "nodeId": "<supporting-node-id>"}
    lines = [
        "PINNED EVIDENCE IDENTITY\n"
        f"Profile SHA-256: {runtime.loaded_package.profile_sha256}\n"
        "Manifest SHA-256: sha256:"
        f"{hashlib.sha256(runtime.loaded_package.manifest_bytes).hexdigest()}\n"
        "Use this exact framework/snapshot in every call; never reroute to current. "
        "Retain original source-artifact hashes, rights and attribution separately "
        "from caller-reported observations and generated suggestions.",
        "1. Call get_standard once with this exact target selector:",
        _tool_call(
            {
                **route,
                "identifier": request.identifier.model_dump(by_alias=True, mode="json"),
            }
        ),
        "Retain its exact outer nodeId as <target-node-id>, CASE IDs, statement text, "
        "grade/facets, package identity, rights and standard URI. Missing target, "
        "ambiguous selector or denied standard evidence means stop retrieval and "
        "dependent composition, reporting the failure. Do not guess a replacement "
        "standard or switch identifier namespaces.",
        "Teacher observations in local_context are unverified caller reports, "
        "not measured mastery/readiness or source statements. If absent, report "
        "missing context and offer general optional choices only. Never invent "
        "observations, learner deficits or a diagnosis.",
    ]

    if runtime.catalog_package.capabilities.has_learning_progressions:
        lines.extend(_render_support_progressions(route))
        lines.extend(
            (
                "5. Retain up to 3 explicitly identified supporting standards "
                "from the returned incoming/upstream builds evidence. Explain the "
                "selection basis, alternatives and excluded evidence; do not select "
                "supporting standards from related concepts or unrelated searches. "
                "For each retained supporting standard, call get_standard once:",
                _tool_call({**route, "identifier": supporting}),
                "Replace <supporting-node-id> only with a returned builds endpoint. "
                "Preserve each original stored support chain to the target; cite "
                "every hop. Unavailable full standard evidence limits dependent "
                "recommendations, rather than licensing invented source text.",
                "6. Read the sanitized LP summary with coverage/validation/"
                "unresolved links, and read material linked evidence under policy:",
                learning_progressions_uri(
                    framework_id=identity.framework_id, snapshot_id=identity.snapshot_id
                ),
                "Retain warnings, needs_review exclusions, selected candidate "
                "coverage and unknown denominators; structural/process acceptance "
                "does not certify pedagogy or remove per-edge warnings.",
                "Before recommending any direct/derived support or related link, "
                "read each used edge's full provenanceUri. Inspect at most 10 "
                "distinct full edge-provenance resources in this entire workflow, "
                "deduplicating IDs across incoming/related/upstream results. Retain "
                "original rationale, model-judgment confidence, warnings, candidate "
                "references, producer/checker trace and source/config/content hashes. "
                "Cite exact relationshipUri/provenanceUri. Reduce or clearly defer "
                "recommendations beyond this cap or with denied/oversized evidence; "
                "excerpts/clipped warnings are not full inspected provenance.",
            )
        )
    else:
        lines.append(
            "STORED LP CAPABILITY UNAVAILABLE in this pinned package. Skip steps "
            "2–6 and all LP tools/resources; do not select supporting standards or "
            "invent an inferred-edge fallback. Continue only from the exact target "
            "and its available components, with explicitly generated optional choices."
        )

    lines.extend(
        (
            "7. Call get_learning_components_for_standard once for the target:",
            _tool_call({**route, "identifier": target}),
            "For each of up to 3 retained supporting standards, call "
            "get_learning_components_for_standard once:",
            _tool_call({**route, "identifier": supporting}),
            "Retain at most 5 returned supporting Learning Components per standard "
            "in client evidence (target plus at most 3 supporting standards). Explain "
            "the chosen subset and omitted items: this evidence-retention cap is not "
            "an LC tool return limit. Cite component/support relationship IDs and "
            "URIs, retain confidence/generated origin, and inspect material component "
            "provenance under policy. Shared components never establish LP edges. "
            "If LC capability is unavailable or evidence is empty, say so and "
            "continue from the standards alone without inventing decomposition.",
            "8. Preserve query limits, examined/returned counts and every cursor, "
            "scope/completeness/frontier/truncation indicator. No next-page or "
            "unbounded retries are part of this workflow. Report unavailable, empty, "
            "sparse, clipped, incomplete and rights/byte-denied evidence; absence "
            "does not prove no pedagogical connection. Do not read bulk maps or "
            "widen limits to bypass policy. Compose cited review/practice options "
            "and alternative next steps only after the permitted retrieval; "
            "observations remain caller reports, suggestions generated pedagogy.",
        )
    )
    return "\n".join(lines)


def render_teaching_sequence_workflow(
    *,
    request: LearningProgressionTeachingSequenceRequest,
    runtime: CatalogPackageRuntime,
) -> str:
    """Render exact local routes, capability disclosures and client evidence caps.

    Parameters
    ----------
    request
        Validated focus, scope, output language and caller context.
    runtime
        Already selected immutable catalog runtime; no file reads occur here.

    Returns
    -------
    str
        Mandatory client retrieval steps, including honest unavailable evidence.
    """

    identity = runtime.catalog_package.package_identity
    filters = normalize_progression_filters(
        request=ProgressionFilters(
            local_grade_labels=request.local_grade_labels,
            normalized_grades=request.normalized_grades,
        ),
        runtime=runtime,
    )
    route: dict[str, object] = {
        "frameworkId": str(identity.framework_id),
        "snapshotId": str(identity.snapshot_id),
    }
    selector = {"identifierType": "node_id", "nodeId": "<selected-node-id>"}
    lines = [
        f"PINNED EVIDENCE IDENTITY\n"
        f"Profile SHA-256: {runtime.loaded_package.profile_sha256}\n"
        f"Manifest SHA-256: sha256:"
        f"{hashlib.sha256(runtime.loaded_package.manifest_bytes).hexdigest()}\n"
        f"Use this exact framework/snapshot for every call; never reroute to current. "
        f"Retain source-artifact hashes and original "
        f"author/provider/attribution/license "
        f"from returned evidence, separately from generated activities.",
        *_render_focus(filters=filters, request=request, route=route),
        "2. For each retained search hit call get_standard with this exact outer "
        "nodeId shape; reuse an exact-focus result without fetching it again:",
        _tool_call({**route, "identifier": selector}),
        "Replace <selected-node-id> from the hit; preserve exact CASE IDs, statement "
        "text, facets, rights, package identity and citations. No matches, missing "
        "standard, unresolved ambiguity or out-of-scope focus means insufficient "
        "evidence: stop selection and composition without inventing a standard.",
    ]

    if runtime.catalog_package.capabilities.has_learning_progressions:
        lines.extend(_render_progressions(route))
        lines.extend(
            (
                "6. Read the sanitized LP summary resource and preserve its coverage "
                "notices and validation/unresolved links:",
                learning_progressions_uri(
                    framework_id=identity.framework_id, snapshot_id=identity.snapshot_id
                ),
                "Read validation/unresolved evidence when material and permitted, "
                "including warning pairs and needs_review claims. These are not "
                "accepted edges. Coverage denominators may be unknown; acceptance "
                "and zero incident counts do not erase relationship warnings.",
                "Before recommending a relationship or path, read each used edge's "
                "full per-relationship provenanceUri from the tool result. Inspect "
                "at most 10 distinct full provenance resources in this entire "
                "workflow, deduplicating IDs across direct/traversal/path results. "
                "Retain original rationale, confidence as a model judgment, warnings, "
                "candidate references, producer/checker trace and "
                "source/config/content "
                "hashes. Cite exact relationshipUri and provenanceUri. If more than "
                "10 edges would be used, reduce or clearly defer the recommendation "
                "set; do not present excerpted or uninspected evidence as full.",
            )
        )
    else:
        lines.append(
            "STORED LP CAPABILITY UNAVAILABLE in this pinned package. Skip steps "
            "3–6 and all LP tools/resources. Report unavailable evidence, continue "
            "only with resolved standards/components and labeled generated activities, "
            "and make no stored progression or inferred-edge fallback claim."
        )
    lines.extend(
        (
            "7. For each of at most 3 selected standards call "
            "get_learning_components_for_standard once:",
            _tool_call({**route, "identifier": selector}),
            "Retain at most 5 returned supporting Learning Components per standard "
            "in client evidence, explaining the subset and omitted items. This is "
            "an evidence-retention cap, not an LC tool return limit. Cite component "
            "and support relationship IDs/URIs and inspect material linked component "
            "provenance under policy. Components/overlap never create LP edges. "
            "If LC capability is unavailable or components are empty, state that "
            "and continue from the selected standards alone.",
            "8. Preserve query limits and all completeness/truncation metadata before "
            "composition. Empty means no stored evidence in this bounded scope; "
            "sparse/selected candidate coverage does not prove no pedagogical "
            "connection. Excerpts/clipped warnings are not complete provenance. "
            "If rights or byte policy denies any tool/resource, disclose the denied "
            "evidence and reduce/defer dependent recommendations; do not widen "
            "limits, read bulk maps or invent a fallback edge. Generate the cited, "
            "adaptable output only after the permitted retrieval above.",
        )
    )
    return "\n".join(lines)
