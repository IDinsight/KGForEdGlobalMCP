"""This module provides deterministic framework discovery and snapshot orchestration.

The service composes the existing in-memory ``CatalogService`` with framework-level
filtering and a separate catalog cursor namespace. It does not access the filesystem,
validate packages, construct graph stores, select standards, or execute search.
"""

# Standard Library
import base64
import binascii
import hashlib
import json
import unicodedata

from dataclasses import dataclass
from json import JSONDecodeError
from typing import Final

# Third Party Library
from pydantic import TypeAdapter, ValidationError

# Package Library
from kgfegmcp.catalog.models import CatalogFrameworkSnapshot
from kgfegmcp.catalog.service import CatalogService
from kgfegmcp.domain.enums import GraphType
from kgfegmcp.domain.identifiers import (
    FrameworkId,
    LanguageTag,
    Sha256Digest,
    SnapshotId,
)
from kgfegmcp.errors import (
    CapabilityUnavailableError,
    FrameworkNotFoundError,
    InvalidCursorError,
)
from kgfegmcp.schemas import FrozenSchema
from kgfegmcp.services.models import (
    FrameworkCursor,
    GetFrameworkRequest,
    GetFrameworkResult,
    ListFrameworksRequest,
    ListFrameworksResult,
)

_FRAMEWORK_CURSOR_KIND: Final[str] = "framework_catalog_v1"
_FRAMEWORK_CURSOR_VERSION: Final[int] = 1
_SHA256_ADAPTER: TypeAdapter[Sha256Digest] = TypeAdapter(Sha256Digest)


class _UnsignedFrameworkCursorState(FrozenSchema):
    """Describe the checksum-covered framework-catalog cursor payload."""

    catalog_sha256: Sha256Digest
    cursor_kind: str
    cursor_version: int
    effective_query_sha256: Sha256Digest
    last_framework_id: FrameworkId
    last_snapshot_id: SnapshotId


class _FrameworkCursorState(_UnsignedFrameworkCursorState):
    """Describe one complete checksum-protected framework-catalog cursor."""

    payload_sha256: Sha256Digest


def _canonical_sha256(payload: object) -> Sha256Digest:
    """Calculate a qualified SHA-256 digest of canonical JSON-compatible data.

    Parameters
    ----------
    payload
        JSON-compatible value to encode with sorted keys and compact separators.

    Returns
    -------
    Sha256Digest
        Qualified lowercase digest of the canonical UTF-8 bytes.
    """

    encoded = json.dumps(
        payload, ensure_ascii=False, separators=(",", ":"), sort_keys=True
    ).encode("utf-8")
    hexdigest = hashlib.sha256(encoded).hexdigest()
    return _SHA256_ADAPTER.validate_python(f"sha256:{hexdigest}")


def _decode_cursor(cursor: FrameworkCursor) -> _FrameworkCursorState:
    """Decode and verify one framework-catalog pagination cursor.

    Parameters
    ----------
    cursor
        Opaque cursor supplied by the caller.

    Returns
    -------
    _FrameworkCursorState
        Verified private cursor state.

    Raises
    ------
    InvalidCursorError
        If decoding, schema validation, version checks, or checksum verification fails.
    """

    padding = "=" * (-len(cursor.root) % 4)

    try:
        decoded = base64.urlsafe_b64decode(f"{cursor.root}{padding}".encode("ascii"))
        payload = json.loads(decoded.decode("utf-8"))
        state = _FrameworkCursorState.model_validate(payload)
    except (
        binascii.Error,
        JSONDecodeError,
        UnicodeDecodeError,
        ValidationError,
        ValueError,
    ) as error:
        raise InvalidCursorError(
            details={"cursor_kind": _FRAMEWORK_CURSOR_KIND},
            message="The framework pagination cursor is malformed.",
        ) from error

    unsigned = _UnsignedFrameworkCursorState(
        catalog_sha256=state.catalog_sha256,
        cursor_kind=state.cursor_kind,
        cursor_version=state.cursor_version,
        effective_query_sha256=state.effective_query_sha256,
        last_framework_id=state.last_framework_id,
        last_snapshot_id=state.last_snapshot_id,
    )
    expected_checksum = _canonical_sha256(
        unsigned.model_dump(by_alias=True, mode="json")
    )

    if (
        state.cursor_kind != _FRAMEWORK_CURSOR_KIND
        or state.cursor_version != _FRAMEWORK_CURSOR_VERSION
        or state.payload_sha256 != expected_checksum
    ):
        raise InvalidCursorError(
            details={"cursor_kind": state.cursor_kind},
            message="The framework pagination cursor is invalid or unsupported.",
        )

    return state


def _encode_cursor(
    *,
    catalog_sha256: Sha256Digest,
    effective_query_sha256: Sha256Digest,
    framework_id: FrameworkId,
    snapshot_id: SnapshotId,
) -> FrameworkCursor:
    """Encode one deterministic continuation position as an opaque cursor.

    Parameters
    ----------
    catalog_sha256
        Digest of the complete accepted public catalog.
    effective_query_sha256
        Digest of the cursor-free framework discovery request.
    framework_id
        Framework identity of the last returned snapshot.
    snapshot_id
        Snapshot identity of the last returned snapshot.

    Returns
    -------
    FrameworkCursor
        Unpadded base64url cursor containing a checksum-protected payload.
    """

    unsigned = _UnsignedFrameworkCursorState(
        catalog_sha256=catalog_sha256,
        cursor_kind=_FRAMEWORK_CURSOR_KIND,
        cursor_version=_FRAMEWORK_CURSOR_VERSION,
        effective_query_sha256=effective_query_sha256,
        last_framework_id=framework_id,
        last_snapshot_id=snapshot_id,
    )
    unsigned_payload = unsigned.model_dump(by_alias=True, mode="json")
    state = _FrameworkCursorState(
        **unsigned.model_dump(), payload_sha256=_canonical_sha256(unsigned_payload)
    )
    raw = json.dumps(
        state.model_dump(by_alias=True, mode="json"),
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    encoded = base64.urlsafe_b64encode(raw).decode("ascii").rstrip("=")
    return FrameworkCursor(encoded)


def _matches_requested_values(
    *, actual_values: tuple[str, ...], requested_values: tuple[str, ...]
) -> bool:
    """Apply OR-within exact normalized matching for one catalog dimension.

    Parameters
    ----------
    actual_values
        Exact source or normalized values available on one snapshot.
    requested_values
        Caller-supplied values for the same dimension.

    Returns
    -------
    bool
        ``True`` when the filter is empty or any requested value matches.
    """

    if not requested_values:
        return True

    actual_keys = {_normalize_catalog_value(value) for value in actual_values}
    requested_keys = {_normalize_catalog_value(value) for value in requested_values}
    return bool(actual_keys.intersection(requested_keys))


def _normalize_catalog_value(value: str) -> str:
    """Normalize one catalog comparison value without replacing source evidence.

    Parameters
    ----------
    value
        Exact source or caller-supplied catalog value.

    Returns
    -------
    str
        NFKC, case-folded, whitespace-collapsed comparison key.
    """

    normalized = unicodedata.normalize("NFKC", value).casefold()
    return " ".join(normalized.split())


def _snapshot_order_key(snapshot: CatalogFrameworkSnapshot) -> tuple[str, str]:
    """Return the deterministic framework and snapshot ordering key.

    Parameters
    ----------
    snapshot
        Accepted catalog snapshot to order.

    Returns
    -------
    tuple[str, str]
        Exact framework and snapshot identifier strings.
    """

    return str(snapshot.framework_id), str(snapshot.snapshot_id)


@dataclass(frozen=True, slots=True)
class FrameworkService:
    """Compose catalog discovery, exact lookup, and public snapshot selection."""

    catalog_service: CatalogService

    @property
    def catalog_sha256(self) -> Sha256Digest:
        """Return the deterministic digest of the complete accepted catalog.

        Returns
        -------
        Sha256Digest
            Digest of the public catalog's canonical serialized form.
        """

        return _canonical_sha256(
            self.catalog_service.catalog.model_dump(by_alias=True, mode="json")
        )

    def _all_snapshots(self) -> tuple[CatalogFrameworkSnapshot, ...]:
        """Return every accepted snapshot in deterministic catalog order.

        Returns
        -------
        tuple[CatalogFrameworkSnapshot, ...]
            Flattened accepted snapshots ordered by framework and snapshot identity.
        """

        return tuple(
            snapshot
            for family in self.catalog_service.list_frameworks().frameworks
            for snapshot in family.snapshots
        )

    @staticmethod
    def _matches_list_request(
        *, request: ListFrameworksRequest, snapshot: CatalogFrameworkSnapshot
    ) -> bool:
        """Return whether one snapshot satisfies every populated discovery filter.

        Parameters
        ----------
        request
            Validated framework-discovery request.
        snapshot
            Accepted snapshot to evaluate.

        Returns
        -------
        bool
            ``True`` only when every filter dimension is satisfied.
        """

        source = snapshot.source_metadata
        packages = snapshot.graph_packages

        if (
            request.is_current is not None
            and source.is_current is not request.is_current
        ):
            return False

        if request.graph_types and not set(request.graph_types).intersection(
            snapshot.available_graph_types
        ):
            return False

        if not _matches_requested_values(
            actual_values=(source.jurisdiction,), requested_values=request.jurisdictions
        ):
            return False

        if not _matches_requested_values(
            actual_values=(
                (source.jurisdiction_type,) if source.jurisdiction_type else ()
            ),
            requested_values=request.jurisdiction_types,
        ):
            return False

        if not _matches_requested_values(
            actual_values=(
                (source.issuing_authority,) if source.issuing_authority else ()
            ),
            requested_values=request.issuing_authorities,
        ):
            return False

        if not _matches_requested_values(
            actual_values=(source.local_subject,), requested_values=request.subjects
        ):
            return False

        if not _matches_requested_values(
            actual_values=tuple(str(value) for value in source.languages),
            requested_values=tuple(str(value) for value in request.languages),
        ):
            return False

        if not _matches_requested_values(
            actual_values=source.local_grades_or_stages,
            requested_values=request.local_grades,
        ):
            return False

        normalized_grades = tuple(
            value
            for package in packages
            for value in package.profile_facets.normalized_grades
        )

        if not _matches_requested_values(
            actual_values=normalized_grades, requested_values=request.normalized_grades
        ):
            return False

        if request.validation_status and not set(
            request.validation_status
        ).intersection(package.validation.status for package in packages):
            return False

        if request.query is not None:
            fields = (
                str(snapshot.framework_id),
                str(snapshot.snapshot_id),
                source.issuing_authority or "",
                source.jurisdiction,
                source.jurisdiction_type or "",
                source.local_subject,
                source.name,
                source.provider or "",
                source.source_version or "",
            )
            haystack = "\u001f".join(
                _normalize_catalog_value(value) for value in fields
            )
            tokens = tuple(_normalize_catalog_value(request.query).split())

            if not all(token in haystack for token in tokens):
                return False

        return True

    def get_framework(self, request: GetFrameworkRequest) -> GetFrameworkResult:
        """Return one exact or unique-current framework snapshot.

        Parameters
        ----------
        request
            Exact framework family and optional immutable snapshot selector.

        Returns
        -------
        GetFrameworkResult
            Complete selected snapshot metadata and package capabilities.
        """

        framework = self.catalog_service.get_framework(
            framework_id=request.framework_id, snapshot_id=request.snapshot_id
        )
        return GetFrameworkResult(framework=framework)

    def get_snapshot_by_id(self, snapshot_id: SnapshotId) -> CatalogFrameworkSnapshot:
        """Return one exact snapshot without inferring its framework identity.

        Parameters
        ----------
        snapshot_id
            Exact immutable snapshot identifier.

        Returns
        -------
        CatalogFrameworkSnapshot
            Matching accepted catalog snapshot.

        Raises
        ------
        FrameworkNotFoundError
            If no accepted snapshot has the exact identifier.
        """

        for snapshot in self._all_snapshots():
            if snapshot.snapshot_id == snapshot_id:
                return snapshot

        raise FrameworkNotFoundError(
            details={"snapshot_id": str(snapshot_id)},
            message="The requested framework snapshot is unavailable.",
        )

    def list_frameworks(self, request: ListFrameworksRequest) -> ListFrameworksResult:
        """Filter and paginate accepted framework snapshots deterministically.

        Parameters
        ----------
        request
            Validated discovery filters, limit, and optional continuation cursor.

        Returns
        -------
        ListFrameworksResult
            One deterministic page with exact source and package evidence.

        Raises
        ------
        InvalidCursorError
            If the cursor is malformed, stale, mismatched, or references no result.
        """

        catalog_sha256 = self.catalog_sha256
        effective_query_sha256 = _canonical_sha256(
            request.model_dump(by_alias=True, exclude={"cursor"}, mode="json")
        )
        matching = tuple(
            snapshot
            for snapshot in self._all_snapshots()
            if self._matches_list_request(request=request, snapshot=snapshot)
        )
        start_index = 0

        if request.cursor is not None:
            state = _decode_cursor(request.cursor)

            if state.catalog_sha256 != catalog_sha256:
                raise InvalidCursorError(
                    details={"cursor_kind": state.cursor_kind},
                    message=(
                        "The framework pagination cursor belongs to a different "
                        "catalog state."
                    ),
                )

            if state.effective_query_sha256 != effective_query_sha256:
                raise InvalidCursorError(
                    details={"cursor_kind": state.cursor_kind},
                    message=(
                        "The framework pagination cursor does not match this request."
                    ),
                )

            position = (str(state.last_framework_id), str(state.last_snapshot_id))

            try:
                start_index = next(
                    index + 1
                    for index, snapshot in enumerate(matching)
                    if _snapshot_order_key(snapshot) == position
                )
            except StopIteration as error:
                raise InvalidCursorError(
                    details={"cursor_kind": state.cursor_kind},
                    message=(
                        "The framework pagination cursor references an unavailable "
                        "continuation position."
                    ),
                ) from error

        items = matching[start_index : start_index + request.limit]
        has_more = start_index + len(items) < len(matching)
        next_cursor = None

        if has_more and items:
            last_item = items[-1]
            next_cursor = _encode_cursor(
                catalog_sha256=catalog_sha256,
                effective_query_sha256=effective_query_sha256,
                framework_id=last_item.framework_id,
                snapshot_id=last_item.snapshot_id,
            )

        return ListFrameworksResult(
            catalog_sha256=catalog_sha256,
            has_more=has_more,
            items=items,
            next_cursor=next_cursor,
            returned_count=len(items),
            total_matching_count=len(matching),
        )

    def resolve_snapshot_selection(
        self, *, framework_id: FrameworkId | None, snapshot_id: SnapshotId | None
    ) -> CatalogFrameworkSnapshot:
        """Resolve a framework-or-snapshot selector without jurisdiction inference.

        Parameters
        ----------
        framework_id
            Optional exact conceptual framework identifier.
        snapshot_id
            Optional exact immutable snapshot identifier.

        Returns
        -------
        CatalogFrameworkSnapshot
            Exact selected snapshot.

        Raises
        ------
        FrameworkNotFoundError
            If selection is absent, unavailable, or internally inconsistent.
        """

        if snapshot_id is not None:
            snapshot = self.get_snapshot_by_id(snapshot_id)

            if framework_id is not None and snapshot.framework_id != framework_id:
                raise FrameworkNotFoundError(
                    details={
                        "framework_id": str(framework_id),
                        "snapshot_id": str(snapshot_id),
                    },
                    message="The requested snapshot does not belong to the framework.",
                )

            return snapshot

        if framework_id is None:
            raise FrameworkNotFoundError(
                message="A framework_id or snapshot_id is required."
            )

        return self.catalog_service.get_framework(framework_id=framework_id)

    def resolve_search_snapshots(
        self,
        *,
        framework_ids: tuple[FrameworkId, ...],
        graph_type: GraphType,
        jurisdictions: tuple[str, ...],
        languages: tuple[LanguageTag, ...],
        snapshot_ids: tuple[SnapshotId, ...],
        subjects: tuple[str, ...],
    ) -> tuple[CatalogFrameworkSnapshot, ...]:
        """Resolve canonical public search selection into exact accepted snapshots.

        Explicit snapshots remain exact. Frameworks without an explicit snapshot use
        the existing unique-current catalog rule. With no identifiers, every framework
        family contributes its unique current snapshot before catalog-level filters are
        applied.

        Parameters
        ----------
        framework_ids
            Optional exact framework family identifiers.
        graph_type
            Required graph type for every selected snapshot.
        jurisdictions
            Optional catalog source-jurisdiction filters.
        languages
            Optional catalog source-language filters.
        snapshot_ids
            Optional exact immutable snapshot identifiers.
        subjects
            Optional source-authored local subject filters.

        Returns
        -------
        tuple[CatalogFrameworkSnapshot, ...]
            Deterministically ordered exact snapshots with the requested graph type.

        Raises
        ------
        CapabilityUnavailableError
            If an explicitly selected snapshot lacks the requested graph type.
        FrameworkNotFoundError
            If identifiers conflict or no accepted snapshot matches the selection.
        """

        selected: dict[SnapshotId, CatalogFrameworkSnapshot] = {}
        framework_id_set = set(framework_ids)

        for snapshot_id in snapshot_ids:
            snapshot = self.get_snapshot_by_id(snapshot_id)

            if framework_id_set and snapshot.framework_id not in framework_id_set:
                raise FrameworkNotFoundError(
                    details={
                        "framework_ids": tuple(str(value) for value in framework_ids),
                        "snapshot_id": str(snapshot_id),
                    },
                    message=(
                        "An explicit snapshot does not belong to a selected framework."
                    ),
                )

            if graph_type not in snapshot.available_graph_types:
                raise CapabilityUnavailableError(
                    details={
                        "graph_type": graph_type.value,
                        "snapshot_id": str(snapshot_id),
                    },
                    message=(
                        "An explicit snapshot does not provide the requested graph type."
                    ),
                )

            selected[snapshot.snapshot_id] = snapshot

        explicit_framework_ids = {
            snapshot.framework_id for snapshot in selected.values()
        }
        unresolved_framework_ids = tuple(
            framework_id
            for framework_id in framework_ids
            if framework_id not in explicit_framework_ids
        )

        if unresolved_framework_ids:
            for framework_id in unresolved_framework_ids:
                snapshot = self.catalog_service.get_framework(framework_id=framework_id)

                if graph_type not in snapshot.available_graph_types:
                    raise CapabilityUnavailableError(
                        details={
                            "framework_id": str(framework_id),
                            "graph_type": graph_type.value,
                            "snapshot_id": str(snapshot.snapshot_id),
                        },
                        message=(
                            "A selected framework does not provide the requested graph type."
                        ),
                    )

                selected[snapshot.snapshot_id] = snapshot
        elif not snapshot_ids and not framework_ids:
            for family in self.catalog_service.list_frameworks().frameworks:
                snapshot = self.catalog_service.get_framework(
                    framework_id=family.framework_id
                )
                selected[snapshot.snapshot_id] = snapshot

        filtered = tuple(
            snapshot
            for snapshot in selected.values()
            if graph_type in snapshot.available_graph_types
            and _matches_requested_values(
                actual_values=(snapshot.source_metadata.jurisdiction,),
                requested_values=jurisdictions,
            )
            and _matches_requested_values(
                actual_values=tuple(
                    str(value) for value in snapshot.source_metadata.languages
                ),
                requested_values=tuple(str(value) for value in languages),
            )
            and _matches_requested_values(
                actual_values=(snapshot.source_metadata.local_subject,),
                requested_values=subjects,
            )
        )
        ordered = tuple(sorted(filtered, key=_snapshot_order_key))

        if not ordered:
            raise FrameworkNotFoundError(
                details={
                    "framework_ids": tuple(str(value) for value in framework_ids),
                    "graph_type": graph_type.value,
                    "snapshot_ids": tuple(str(value) for value in snapshot_ids),
                },
                message="No accepted framework snapshot matched the requested scope.",
            )

        return ordered
