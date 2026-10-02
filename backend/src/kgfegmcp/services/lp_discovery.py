"""Profile-governed endpoint matching and stateless bounded LP page assembly."""

# Future Library
from __future__ import annotations

# Standard Library
import base64
import hashlib
import json
import unicodedata

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Annotated, Literal, cast

# Third Party Library
from pydantic import Field, StrictInt, ValidationError

# Package Library
from kgfegmcp.catalog.models import CatalogPackageRuntime
from kgfegmcp.domain.identifiers import NodeId, Sha256Digest
from kgfegmcp.errors import (
    InvalidCursorError,
    InvalidProgressionRequestError,
    ProgressionResultTooLargeError,
)
from kgfegmcp.graph.models import GraphPackageIdentity, GraphRelationship, StandardNode
from kgfegmcp.schemas import FrozenSchema
from kgfegmcp.search.models import SearchFacetEvidence
from kgfegmcp.search.normalizers import (
    FACET_NORMALIZER_VERSION,
    normalize_facet_value,
)
from kgfegmcp.services.lp_models import (
    GetStandardProgressionsRequest,
    ProgressionCollectionRequest,
    ProgressionCollectionResult,
    ProgressionConnection,
    ProgressionEndpointMatch,
    ProgressionFilters,
    ProgressionMetadata,
    ProgressionPage,
    ProgressionRelationshipEvidence,
    ProgressionStandardSummary,
)

if TYPE_CHECKING:
    # Package Library
    from kgfegmcp.services.learning_progressions import LearningProgressionsService


class _CursorState(FrozenSchema):
    """Bind a private candidate position to exact identity and effective selection."""

    cursor_kind: Literal["learning_progressions_v1"] = "learning_progressions_v1"
    manifest_sha256: Sha256Digest
    package_identity: GraphPackageIdentity
    position: Annotated[StrictInt, Field(ge=0)]
    selection_sha256: Sha256Digest
    version: Annotated[StrictInt, Field(ge=1, le=1)] = 1


class _SignedCursorState(_CursorState):
    """Retain the canonical payload checksum under existing cursor conventions."""

    payload_sha256: Sha256Digest


@dataclass(frozen=True, slots=True)
class _Selection:
    """Keep only normalized bounded criteria and exact resolved node identities."""

    endpoint_scope: str
    filters: ProgressionFilters
    node_ids: tuple[NodeId, ...]
    relationship_types: tuple[str, ...]


@dataclass(slots=True)
class _PageRows:
    """Own a query-local bounded evidence cache; never mutate accepted graph state."""

    connections: list[ProgressionConnection] = field(default_factory=list)
    nodes: dict[NodeId, ProgressionStandardSummary] = field(default_factory=dict)
    positions: list[int] = field(default_factory=list)
    relationships: list[ProgressionRelationshipEvidence] = field(default_factory=list)


@dataclass(frozen=True, slots=True)
class _PageContext:
    """Pin page inputs independently of the mutable query-local output buffers."""

    candidates: tuple[GraphRelationship, ...]
    metadata: ProgressionMetadata
    request: ProgressionCollectionRequest
    runtime: CatalogPackageRuntime
    selection: _Selection
    selection_sha256: Sha256Digest
    service: LearningProgressionsService


def collection_result(
    *,
    candidates: tuple[GraphRelationship, ...],
    request: ProgressionCollectionRequest,
    runtime: CatalogPackageRuntime,
    service: LearningProgressionsService,
) -> ProgressionCollectionResult:
    """Scan at most 5,000 candidates and assemble a byte-bounded direct/discovery page.

    Parameters
    ----------
    candidates
        Existing edge references sorted by type and ID.
    request
        Strict bounded direct/discovery inputs and optional stateless continuation.
    runtime
        Exact accepted runtime selected before checking content rights.
    service
        Shared route, selector, projection and byte-budget helpers.

    Returns
    -------
    ProgressionCollectionResult
        Bounded evidence and truthful continuation/completeness metadata.
    """

    selection = _resolve_selection(request=request, runtime=runtime, service=service)
    metadata = service.evidence_metadata(runtime=runtime)
    context = _PageContext(
        candidates=candidates,
        metadata=metadata,
        request=request,
        runtime=runtime,
        selection=selection,
        selection_sha256=_selection_hash(request=request, selection=selection),
        service=service,
    )
    position = _cursor_position(context=context)
    start = position
    examined = 0
    reason: Literal["byte_limit", "page_limit", "work_limit"] | None = None
    rows = _PageRows()

    while position < len(candidates):
        if len(rows.relationships) == request.limit:
            reason = "page_limit"
            break

        if examined == 5000:
            reason = "work_limit"
            break

        edge = candidates[position]
        examined += 1
        connection = _connection(context=context, edge=edge, rows=rows)

        if connection is None:
            position += 1
            continue

        rows.connections.append(connection)
        rows.positions.append(position)
        rows.relationships.append(
            service.relationship_evidence(relationship=edge, runtime=runtime)
        )
        trial = _build_result(
            context=context,
            examined=examined,
            position=position + 1,
            reason=None,
            rows=rows,
            start=start,
        )

        try:
            service.require_collection_result_size(result=trial)
        except ProgressionResultTooLargeError:
            if len(rows.relationships) == 1:
                raise

            _remove_last(rows=rows)
            reason = "byte_limit"
            break

        position += 1

    # Later nonmatches/cursor/count fields can increase envelope bytes at a boundary.
    # Roll back whole entries, including their candidate position, before returning.
    return _finish_result(
        context=context,
        examined=examined,
        position=position,
        reason=reason,
        rows=rows,
        start=start,
    )


def normalize_progression_filters(
    *, request: ProgressionFilters, runtime: CatalogPackageRuntime
) -> ProgressionFilters:
    """Validate profile-supported facets using existing normalized token rules.

    Parameters
    ----------
    request
        Bounded caller values, including possible source-facing aliases.
    runtime
        Profile of the already selected package.

    Returns
    -------
    ProgressionFilters
        Sorted normalized canonical values for matching and cursor identity.

    Raises
    ------
    InvalidProgressionRequestError
        If a criterion is blank, duplicate, unsafe or unsupported by the profile.
    """

    profile = runtime.loaded_package.profile
    local_grades = {
        normalize_facet_value(value): normalize_facet_value(mapping.local_label)
        for mapping in profile.grade_mappings
        for value in (mapping.local_label, *mapping.aliases)
    }
    statement_types = {
        normalize_facet_value(value): normalize_facet_value(
            policy.source_statement_type
        )
        for policy in profile.statement_types
        for value in (policy.source_statement_type, *policy.aliases)
    }
    normalized_grades = {
        normalize_facet_value(value): normalize_facet_value(value)
        for mapping in profile.grade_mappings
        for value in mapping.normalized_grades
    }
    normalized_types = {
        normalize_facet_value(
            policy.normalized_statement_type.value
        ): normalize_facet_value(policy.normalized_statement_type.value)
        for policy in profile.statement_types
    }
    allowed = {
        "local_grade_labels": local_grades,
        "normalized_grades": normalized_grades,
        "normalized_statement_types": normalized_types,
        "statement_types": statement_types,
    }
    normalized: dict[str, tuple[str, ...]] = {}

    for name, values in request.model_dump().items():
        # Only the four shared facet dimensions are normalized here.
        if name in allowed:
            normalized[name] = _normalize_values(allowed=allowed[name], values=values)

    return ProgressionFilters(**normalized)


def ordered_progressions(
    runtime: CatalogPackageRuntime,
) -> tuple[GraphRelationship, ...]:
    """Build an immutable ordering index over original LP edge references once.

    Parameters
    ----------
    runtime
        Accepted package whose existing GraphStore owns all source records.

    Returns
    -------
    tuple[GraphRelationship, ...]
        LP references in file-order-independent type/ID order, without another store.
    """

    return tuple(
        sorted(
            (
                edge
                for edge in runtime.graph_store.relationships_by_id.values()
                if edge.label in {"buildsTowards", "relatesTo"}
            ),
            key=lambda edge: (edge.label, edge.relationship_id),
        )
    )


def _build_result(
    *,
    context: _PageContext,
    examined: int,
    position: int,
    reason: Literal["byte_limit", "page_limit", "work_limit"] | None,
    rows: _PageRows,
    start: int,
) -> ProgressionCollectionResult:
    """Assemble a deduplicated page with only endpoint rows used by emitted edges.

    Parameters
    ----------
    context
        Pinned operation inputs and selection identity.
    examined
        Candidates inspected on this page, including a byte-stopped entry.
    position
        Next unconsumed candidate position.
    reason
        Active page stopping bound or None on exhaustion.
    rows
        Query-local bounded evidence buffers.
    start
        Initial candidate position for exact whole-selection count eligibility.

    Returns
    -------
    ProgressionCollectionResult
        Result whose totals distinguish candidates from fully computed matches.
    """

    remaining = position < len(context.candidates)
    used_nodes = {
        node_id
        for item in rows.relationships
        for node_id in (
            item.relationship.source_node_id,
            item.relationship.target_node_id,
        )
    }
    return ProgressionCollectionResult(
        connections=tuple(rows.connections),
        endpoint_scope=context.selection.endpoint_scope,
        filters=context.selection.filters,
        metadata=context.metadata,
        nodes=tuple(rows.nodes[node_id] for node_id in sorted(used_nodes)),
        page=ProgressionPage(
            candidate_count=len(context.candidates),
            examined_count=examined,
            has_more=remaining,
            is_complete=not remaining,
            next_cursor=(
                _encode_cursor(context=context, position=position)
                if remaining
                else None
            ),
            returned_count=len(rows.relationships),
            stopping_reason=reason if remaining else None,
            total_matching_count=(
                len(rows.relationships) if start == 0 and not remaining else None
            ),
        ),
        relationships=tuple(rows.relationships),
        request=context.request,
        resolved_standard_node_ids=context.selection.node_ids,
    )


def _canonical_hash(payload: object) -> Sha256Digest:
    """Hash compact sorted public JSON using the established cursor convention.

    Parameters
    ----------
    payload
        JSON-compatible canonical identity or selection data.

    Returns
    -------
    Sha256Digest
        Qualified deterministic SHA-256.
    """

    encoded = json.dumps(
        ensure_ascii=False, obj=payload, separators=(",", ":"), sort_keys=True
    ).encode("utf-8")
    return cast(Sha256Digest, "sha256:" + hashlib.sha256(encoded).hexdigest())


def _connection(
    *, context: _PageContext, edge: GraphRelationship, rows: _PageRows
) -> ProgressionConnection | None:
    """Match conjunctions on each stored endpoint and preserve direct meanings.

    Parameters
    ----------
    context
        Pinned filters, selectors and existing evidence helpers.
    edge
        One candidate LP edge in its original orientation.
    rows
        Bounded query-local cache of summaries for matched candidates only.

    Returns
    -------
    ProgressionConnection | None
        Per-endpoint match evidence, or None when this candidate does not qualify.
    """

    selection = context.selection

    if edge.label not in selection.relationship_types:
        return None

    identity = context.runtime.catalog_package.package_identity
    source = _endpoint_match(
        evidence=context.service.search_service.get_node_facet_evidence(
            graph_package_id=identity.graph_package_id, node_id=edge.source_node_id
        ),
        node_id=edge.source_node_id,
        selection=selection,
    )
    target = _endpoint_match(
        evidence=context.service.search_service.get_node_facet_evidence(
            graph_package_id=identity.graph_package_id, node_id=edge.target_node_id
        ),
        node_id=edge.target_node_id,
        selection=selection,
    )
    qualifies = {
        "both": source.matches and target.matches,
        "either": source.matches or target.matches,
        "source": source.matches,
        "target": target.matches,
    }[selection.endpoint_scope]

    if not qualifies:
        return None

    for node_id in (edge.source_node_id, edge.target_node_id):
        if node_id not in rows.nodes:
            rows.nodes[node_id] = context.service.standard_summary(
                node=cast(
                    StandardNode, context.runtime.graph_store.nodes_by_id[node_id]
                ),
                runtime=context.runtime,
            )

    kind: Literal["incoming_builds", "outgoing_builds", "related"] | None = None

    if isinstance(context.request, GetStandardProgressionsRequest):
        if edge.label == "relatesTo":
            kind = "related"
        else:
            kind = (
                "outgoing_builds"
                if edge.source_node_id == selection.node_ids[0]
                else "incoming_builds"
            )

    return ProgressionConnection(
        connection_kind=kind,
        relationship_id=edge.relationship_id,
        source_match=source,
        target_match=target,
    )


def _cursor_position(*, context: _PageContext) -> int:
    """Reject malformed, stale, mismatched or out-of-range continuation state.

    Parameters
    ----------
    context
        Exact current identity, selection fingerprint and candidate range.

    Returns
    -------
    int
        Verified next candidate position, or zero for a new request.

    Raises
    ------
    InvalidCursorError
        If shape, encoding, checksum, identity, fingerprint or range is invalid.
    """

    cursor = context.request.cursor

    if cursor is None:
        return 0

    try:
        raw = base64.urlsafe_b64decode(cursor + "=" * (-len(cursor) % 4))

        if base64.urlsafe_b64encode(raw).decode("ascii").rstrip("=") != cursor:
            raise ValueError("Noncanonical cursor encoding")

        state = _SignedCursorState.model_validate(json.loads(raw.decode("utf-8")))
    except (ValidationError, ValueError) as error:
        raise InvalidCursorError(
            message="The LP continuation cursor is malformed."
        ) from error

    unsigned = state.model_dump(by_alias=True, exclude={"payload_sha256"}, mode="json")

    if (
        state.payload_sha256 != _canonical_hash(payload=unsigned)
        or state.package_identity != context.metadata.package.package_identity
        or state.manifest_sha256 != context.metadata.manifest_sha256
        or state.selection_sha256 != context.selection_sha256
        or state.position >= len(context.candidates)
    ):
        raise InvalidCursorError(
            message="The LP cursor does not match this selection or accepted package.",
            recovery_hint=(
                "Restart without a cursor; keep the route, filters and limits."
            ),
        )

    return state.position


def _encode_cursor(*, context: _PageContext, position: int) -> str:
    """Encode checksum-bound exact identity and next candidate position statelessly.

    Parameters
    ----------
    context
        Accepted identity and normalized semantic inputs.
    position
        Next candidate, including progress through examined nonmatches.

    Returns
    -------
    str
        Bounded unpadded base64url continuation.
    """

    state = _CursorState(
        manifest_sha256=context.metadata.manifest_sha256,
        package_identity=context.metadata.package.package_identity,
        position=position,
        selection_sha256=context.selection_sha256,
    )
    payload = state.model_dump(by_alias=True, mode="json")
    signed = _SignedCursorState(
        **state.model_dump(), payload_sha256=_canonical_hash(payload=payload)
    )
    raw = json.dumps(
        ensure_ascii=False,
        obj=signed.model_dump(by_alias=True, mode="json"),
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return base64.urlsafe_b64encode(raw).decode("ascii").rstrip("=")


def _endpoint_match(
    *, evidence: SearchFacetEvidence, node_id: NodeId, selection: _Selection
) -> ProgressionEndpointMatch:
    """Apply all facet dimensions and selector membership on the same endpoint.

    Parameters
    ----------
    evidence
        Existing profile facet evidence, including established structural grades.
    node_id
        Stored endpoint identity.
    selection
        Normalized requested facet values and selected node set.

    Returns
    -------
    ProgressionEndpointMatch
        Matched values and whole-conjunction outcome for this endpoint alone.
    """

    actual = {
        "local_grade_labels": evidence.resolved_local_grade_labels,
        "normalized_grades": evidence.normalized_grades,
        "normalized_statement_types": (
            (evidence.normalized_statement_type.value,)
            if evidence.normalized_statement_type is not None
            else ()
        ),
        "statement_types": (
            (evidence.statement_type,) if evidence.statement_type else ()
        ),
    }
    requested = selection.filters.model_dump()
    matched = {
        name: tuple(
            value
            for value in values
            if value in {normalize_facet_value(item) for item in actual[name]}
        )
        for name, values in requested.items()
    }
    selected = not selection.node_ids or node_id in selection.node_ids
    return ProgressionEndpointMatch(
        **matched,
        matches=selected
        and all(not requested[name] or matched[name] for name in requested),
        node_id=node_id,
        selected_standard=selected,
    )


def _finish_result(
    *,
    context: _PageContext,
    examined: int,
    position: int,
    reason: Literal["byte_limit", "page_limit", "work_limit"] | None,
    rows: _PageRows,
    start: int,
) -> ProgressionCollectionResult:
    """Check final cursor/count overhead and rewind complete entries if needed.

    Parameters
    ----------
    context
        Pinned request and accepted evidence.
    examined
        All work actually performed on this page.
    position
        Candidate position after successful examination.
    reason
        Current stopping reason.
    rows
        Bounded query-local evidence buffers.
    start
        Initial candidate position.

    Returns
    -------
    ProgressionCollectionResult
        A fully budget-checked page with no lost entry or zero-progress byte cursor.
    """

    while True:
        result = _build_result(
            context=context,
            examined=examined,
            position=position,
            reason=reason,
            rows=rows,
            start=start,
        )

        try:
            context.service.require_collection_result_size(result=result)
        except ProgressionResultTooLargeError:
            if len(rows.relationships) <= 1:
                raise

            position = _remove_last(rows=rows)
            reason = "byte_limit"
        else:
            return result


def _normalize_values(*, allowed: dict[str, str], values: list[str]) -> tuple[str, ...]:
    """Reject unsupported or duplicate normalized canonical facet values.

    Parameters
    ----------
    allowed
        Profile-governed normalized aliases mapped to canonical normalized keys.
    values
        Caller-supplied bounded criterion array.

    Returns
    -------
    tuple[str, ...]
        Sorted canonical normalized keys.

    Examples
    --------
    >>> _normalize_values(allowed={"one": "1"}, values=["one"])
    ('1',)
    """

    normalized: list[str] = []

    for value in values:
        key = normalize_facet_value(value)

        if not key or any(unicodedata.category(char).startswith("C") for char in value):
            raise InvalidProgressionRequestError(
                message="LP facet values must be nonblank and safe."
            )

        canonical = allowed.get(key)

        if canonical is None or canonical in normalized:
            raise InvalidProgressionRequestError(
                message="LP facets must be supported and unique after normalization."
            )

        normalized.append(canonical)

    return tuple(sorted(normalized))


def _remove_last(*, rows: _PageRows) -> int:
    """Rewind an entire emitted entry to prevent skipping byte-stopped evidence.

    Parameters
    ----------
    rows
        Query-local output buffers with at least one emitted entry.

    Returns
    -------
    int
        Unconsumed candidate position of the removed entry.
    """

    rows.connections.pop()
    rows.relationships.pop()
    return rows.positions.pop()


def _resolve_selection(
    *,
    request: ProgressionCollectionRequest,
    runtime: CatalogPackageRuntime,
    service: LearningProgressionsService,
) -> _Selection:
    """Validate every selector before scanning and retain exact resolved membership.

    Parameters
    ----------
    request
        Direct selection or filtered discovery operation.
    runtime
        Exact owning accepted package.
    service
        Existing exact-standard resolver and profile search machinery.

    Returns
    -------
    _Selection
        Canonical filters, type set and deduplicated resolved standards.
    """

    if isinstance(request, GetStandardProgressionsRequest):
        node = service.resolve_standard(identifier=request.identifier, runtime=runtime)
        return _Selection(
            endpoint_scope="either",
            filters=ProgressionFilters(),
            node_ids=(node.node_id,),
            relationship_types=("buildsTowards", "relatesTo"),
        )

    if len(request.relationship_types) != len(set(request.relationship_types)):
        raise InvalidProgressionRequestError(
            message="LP relationship types must be unique."
        )

    selector_keys = tuple(
        item.model_dump_json(by_alias=True) for item in request.standard_identifiers
    )

    if len(selector_keys) != len(set(selector_keys)):
        raise InvalidProgressionRequestError(
            message="LP standard selectors must be unique."
        )

    return _Selection(
        endpoint_scope=request.endpoint_scope,
        filters=normalize_progression_filters(request=request, runtime=runtime),
        node_ids=tuple(
            sorted(
                {
                    service.resolve_standard(identifier=item, runtime=runtime).node_id
                    for item in request.standard_identifiers
                }
            )
        ),
        relationship_types=tuple(
            sorted(request.relationship_types or ("buildsTowards", "relatesTo"))
        ),
    )


def _selection_hash(
    *, request: ProgressionCollectionRequest, selection: _Selection
) -> Sha256Digest:
    """Bind semantic bounds and normalized inputs independently of raw aliases/order.

    Parameters
    ----------
    request
        Original operation with its page limit and direct connection meaning.
    selection
        Validated canonical endpoint criteria.

    Returns
    -------
    Sha256Digest
        Effective operation fingerprint, separate from exact accepted identity.
    """

    return _canonical_hash(
        payload={
            "connection_kind": (
                request.connection_kind
                if isinstance(request, GetStandardProgressionsRequest)
                else None
            ),
            "endpoint_scope": selection.endpoint_scope,
            "facet_normalizer": FACET_NORMALIZER_VERSION,
            "filters": selection.filters.model_dump(mode="json"),
            "limit": request.limit,
            "max_examined_relationships": 5000,
            "max_result_bytes": 1048576,
            "node_ids": selection.node_ids,
            "operation": (
                "direct"
                if isinstance(request, GetStandardProgressionsRequest)
                else "discovery"
            ),
            "relationship_types": selection.relationship_types,
        }
    )
