"""Derive slim runtime artifacts and the evidence archive record from legacy evidence.

Every function here is a pure, deterministic bytes-in/bytes-out derivation. The package
builder writes its outputs, and acceptance re-derives them from the archived evidence
and requires byte equality, so this module is the single definition of what a slim
artifact is.

Slimming is field removal plus a hash link: each slim entry is the original entry
without the named bulky fields, plus the SHA-256 of the original entry's canonical
JSON. All other fields are kept verbatim, and output uses the canonical JSON encoding
that LP preparation already uses.
"""

# Standard Library
from collections.abc import Mapping

# Package Library
from kgfegmcp.domain.identifiers import FrameworkId, Sha256Digest
from kgfegmcp.errors import ManifestBuildError
from kgfegmcp.packages.checksums import calculate_bytes_sha256
from kgfegmcp.packages.evidence_models import (
    REMOVED_ENTITY_ITEM_FIELDS,
    EvidenceArchiveEntry,
    EvidenceArchiveRecord,
    SlimEntityProvenance,
    SlimLearningComponentProvenance,
    SlimLearningProgressionProvenanceIndex,
)
from kgfegmcp.packages.models import LP_PROVENANCE_SHARD_NAMES
from kgfegmcp.packages.normalization import _canonical_bytes, provenance_partition
from kgfegmcp.packages.normalization_models import ProvenancePartition
from kgfegmcp.packages.normalization_sources import read_json_object

EVIDENCE_ARCHIVE_RECORD_PATH = "evidence/evidence_archive_record.json"
SLIM_ENTITY_PROVENANCE_PATH = "slim/as_entity_provenance.json"
SLIM_LEARNING_COMPONENT_PROVENANCE_PATH = "slim/lc_entity_provenance.json"
SLIM_LP_INDEX_PATH = "slim/lp_relationship_provenance_index.json"
SLIM_LP_SHARD_PATHS: dict[str, str] = {
    name: f"slim/lp_relationship_provenance_shard_{number:02d}.json"
    for number, name in enumerate(LP_PROVENANCE_SHARD_NAMES)
}

# Full-evidence inputs that the slim derivations read.
SLIM_SOURCE_NAMES: tuple[str, ...] = (
    "entityProvenance",
    "learningComponentProvenance",
    "learningProgressionProvenance",
    "learningProgressionProvenanceIndex",
)
SLIM_ARTIFACT_PATHS: dict[str, str] = {
    "entityProvenance": SLIM_ENTITY_PROVENANCE_PATH,
    "learningComponentProvenance": SLIM_LEARNING_COMPONENT_PROVENANCE_PATH,
    "learningProgressionProvenanceIndex": SLIM_LP_INDEX_PATH,
    **SLIM_LP_SHARD_PATHS,
}


def _object_field(
    *, field_name: str, label: str, value: Mapping[str, object]
) -> dict[str, object]:
    """Return one nested JSON object, rejecting any other shape.

    Parameters
    ----------
    field_name
        Key that must hold a JSON object.
    label
        Safe artifact label for diagnostics.
    value
        Parent JSON object.

    Returns
    -------
    dict[str, object]
        A shallow copy of the nested object, safe to edit without touching the parent.

    Raises
    ------
    ManifestBuildError
        If the key is absent or does not hold a JSON object.
    """

    nested = value.get(field_name)

    if not isinstance(nested, dict):
        raise ManifestBuildError(
            details={"artifact": label, "field": field_name},
            message="Legacy evidence is missing a required JSON object.",
        )

    return dict(nested)


def _original_sha256(value: object) -> Sha256Digest:
    """Hash one original entry's canonical JSON, without the trailing newline.

    Parameters
    ----------
    value
        Original parsed JSON entry.

    Returns
    -------
    Sha256Digest
        Qualified ``sha256:<hex>`` digest linking a slim entry to its original.

    Examples
    --------
    >>> _original_sha256({"id": "edge"})  # doctest: +ELLIPSIS
    'sha256:...'
    """

    return calculate_bytes_sha256(_canonical_bytes(value)[:-1])


def derive_entity_provenance(original: bytes) -> bytes:
    """Derive slim standards provenance from the archived AS entity provenance.

    Parameters
    ----------
    original
        Exact bytes of the legacy ``as_entity_provenance.json``.

    Returns
    -------
    bytes
        Canonical slim document: the source ``framework`` object verbatim and every
        item without ``candidate_source_refs``, plus each item's original hash.

    Raises
    ------
    ManifestBuildError
        If the original is not a JSON object with ``framework`` and ``items`` objects.
    """

    label = "AS entity provenance"
    document = read_json_object(data=original, label=label)
    items = _object_field(field_name="items", label=label, value=document)
    slim_items: dict[str, dict[str, object]] = {}

    for key, item in items.items():
        if not isinstance(item, dict):
            raise ManifestBuildError(
                details={"artifact": label, "item": key},
                message="Legacy entity provenance item is not a JSON object.",
            )

        slim_item = {
            name: value
            for name, value in item.items()
            if name not in REMOVED_ENTITY_ITEM_FIELDS
        }
        slim_item["original_item_sha256"] = _original_sha256(item)
        slim_items[key] = slim_item

    return _canonical_bytes(
        SlimEntityProvenance(
            items=slim_items,
            original_sha256=calculate_bytes_sha256(original),
            source_document=_object_field(
                field_name="framework", label=label, value=document
            ),
        )
    )


def derive_learning_component_provenance(original: bytes) -> bytes:
    """Derive slim learning-component provenance from the archived LC provenance.

    Parameters
    ----------
    original
        Exact bytes of the legacy ``lc_entity_provenance.json``.

    Returns
    -------
    bytes
        Canonical slim document: source ``doc_key`` and ``pdf_name``, and every
        component record verbatim plus its original hash.

    Raises
    ------
    ManifestBuildError
        If the original lacks its components object or source document fields.
    """

    label = "LC entity provenance"
    document = read_json_object(data=original, label=label)
    components = _object_field(
        field_name="learning_components", label=label, value=document
    )
    slim_components: dict[str, dict[str, object]] = {}

    for key, component in components.items():
        if not isinstance(component, dict):
            raise ManifestBuildError(
                details={"artifact": label, "item": key},
                message="Legacy learning component provenance is not a JSON object.",
            )

        slim_components[key] = {
            **component,
            "original_component_sha256": _original_sha256(component),
        }

    if "doc_key" not in document or "pdf_name" not in document:
        raise ManifestBuildError(
            details={"artifact": label},
            message="Legacy LC provenance is missing its source document fields.",
        )

    return _canonical_bytes(
        SlimLearningComponentProvenance(
            learning_components=slim_components,
            original_sha256=calculate_bytes_sha256(original),
            source_document={
                "doc_key": document["doc_key"],
                "pdf_name": document["pdf_name"],
            },
        )
    )


def derive_lp_provenance(
    *, original_index: bytes, original_provenance: bytes
) -> dict[str, bytes]:
    """Derive the slim LP index and its 64 slim shards from the archived map.

    Parameters
    ----------
    original_index
        Exact bytes of the legacy ``lp_relationship_provenance_index.json``.
    original_provenance
        Exact bytes of the legacy ``lp_relationship_provenance.json``.

    Returns
    -------
    dict[str, bytes]
        Canonical bytes by runtime logical name: ``learningProgressionProvenanceIndex``
        and ``learningProgressionProvenanceShard00`` through ``63``.

    Raises
    ------
    ManifestBuildError
        If the original map or any entry is not a JSON object.

    Examples
    --------
    >>> artifacts = derive_lp_provenance(
    ...     original_index=index_bytes, original_provenance=provenance_bytes
    ... )
    >>> len(artifacts)
    65
    """

    provenance = read_json_object(data=original_provenance, label="LP provenance")
    buckets: list[dict[str, object]] = [{} for _ in range(64)]

    for identifier, entry in provenance.items():
        if not isinstance(entry, dict):
            raise ManifestBuildError(
                details={"relationship_id": identifier},
                message="Legacy LP provenance entry is not a JSON object.",
            )

        buckets[provenance_partition(identifier)][identifier] = slim_lp_record(entry)

    artifacts: dict[str, bytes] = {}
    partitions: dict[str, ProvenancePartition] = {}

    for name, bucket in zip(LP_PROVENANCE_SHARD_NAMES, buckets, strict=True):
        content = _canonical_bytes(bucket)
        artifacts[name] = content
        partitions[name] = ProvenancePartition.model_validate(
            {
                "artifactPath": SLIM_LP_SHARD_PATHS[name],
                "entryCount": len(bucket),
                "sha256": calculate_bytes_sha256(content),
            }
        )

    artifacts["learningProgressionProvenanceIndex"] = _canonical_bytes(
        SlimLearningProgressionProvenanceIndex(
            original_provenance_index_sha256=calculate_bytes_sha256(original_index),
            original_provenance_sha256=calculate_bytes_sha256(original_provenance),
            partitions=partitions,
        )
    )
    return artifacts


def derive_slim_artifacts(contents: Mapping[str, bytes]) -> dict[str, bytes]:
    """Derive every slim runtime artifact that a full-evidence set supports.

    Parameters
    ----------
    contents
        Exact full-evidence bytes by logical name; only ``SLIM_SOURCE_NAMES`` are
        read.

    Returns
    -------
    dict[str, bytes]
        Canonical slim bytes by runtime logical name: the slim LP index and shards
        when LP provenance is present, and slim AS and LC entity provenance when
        their full documents are present.

    Raises
    ------
    ManifestBuildError
        If LP provenance is present without its index, or the reverse, or any
        derivation fails.
    """

    derived: dict[str, bytes] = {}
    provenance = contents.get("learningProgressionProvenance")
    index = contents.get("learningProgressionProvenanceIndex")

    if (provenance is None) != (index is None):
        raise ManifestBuildError(
            details={
                "has_provenance": provenance is not None,
                "has_provenance_index": index is not None,
            },
            message="LP provenance and its index must be supplied together.",
        )

    if provenance is not None and index is not None:
        derived.update(
            derive_lp_provenance(original_index=index, original_provenance=provenance)
        )

    if "entityProvenance" in contents:
        derived["entityProvenance"] = derive_entity_provenance(
            contents["entityProvenance"]
        )

    if "learningComponentProvenance" in contents:
        derived["learningComponentProvenance"] = derive_learning_component_provenance(
            contents["learningComponentProvenance"]
        )

    return derived


def evidence_archive_record_bytes(
    *,
    evidence_artifacts: Mapping[str, EvidenceArchiveEntry],
    framework_id: FrameworkId,
) -> bytes:
    """Serialize the deterministic evidence archive record for one package.

    Parameters
    ----------
    evidence_artifacts
        Complete legacy declaration by logical name, excluding the manifest.
    framework_id
        Owning framework.

    Returns
    -------
    bytes
        Canonical record bytes with the fixed archive location.
    """

    return _canonical_bytes(
        EvidenceArchiveRecord(
            evidence_artifacts=dict(evidence_artifacts), framework_id=framework_id
        )
    )


def slim_lp_record(entry: Mapping[str, object]) -> dict[str, object]:
    """Remove the archived bulky fields from one LP record and link its original.

    Parameters
    ----------
    entry
        One original per-edge provenance record.

    Returns
    -------
    dict[str, object]
        The record without candidate evidence, admissible decisions and the
        duplicate producer judgment, plus ``original_entry_sha256``.

    Raises
    ------
    ManifestBuildError
        If ``claim``, ``claim.candidate`` or ``claim.provenance`` is not an object.

    Examples
    --------
    >>> slim = slim_lp_record(original_entry)
    >>> "evidence" in slim["claim"]["candidate"]
    False
    """

    label = "LP provenance record"
    claim = _object_field(field_name="claim", label=label, value=entry)
    candidate = _object_field(field_name="candidate", label=label, value=claim)
    trace = _object_field(field_name="provenance", label=label, value=claim)

    # Field paths match REMOVED_LP_RECORD_FIELDS.
    candidate.pop("admissible_decisions", None)
    candidate.pop("evidence", None)
    trace.pop("producer_judgment", None)

    claim["candidate"] = candidate
    claim["provenance"] = trace
    return {**entry, "claim": claim, "original_entry_sha256": _original_sha256(entry)}
