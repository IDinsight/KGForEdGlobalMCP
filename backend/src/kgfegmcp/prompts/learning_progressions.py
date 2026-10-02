"""Render bounded client retrieval of stored teaching-sequence evidence."""

# Standard Library
import hashlib
import json

from collections.abc import Mapping

# Third Party Library
from pydantic import TypeAdapter, ValidationError

# Package Library
from kgfegmcp.catalog.models import CatalogPackageRuntime
from kgfegmcp.errors import InvalidProgressionRequestError
from kgfegmcp.prompts.models import (
    LearningProgressionTeachingSequenceRequest,
    PromptFocusMode,
)
from kgfegmcp.resources.uri import learning_progressions_uri
from kgfegmcp.services.lp_discovery import normalize_progression_filters
from kgfegmcp.services.lp_models import ProgressionFilters
from kgfegmcp.services.models import StandardIdentifier


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
        selector = TypeAdapter(StandardIdentifier).validate_python(
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
        "once, one page of 25; do not follow nextCursor:",
        _tool_call(
            {**route, "connectionKind": "all", "identifier": selector, "limit": 25}
        ),
        "Keep incoming builds, outgoing builds and related connections distinct. "
        "relatesTo is read from either endpoint but retains its canonical stored "
        "orientation; it supplies related concepts, never sequence hops.",
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
