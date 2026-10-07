"""Prepare reproducible AS/LC/LP delivery and provenance from verified local copies.

Preparation preserves producer/checker evidence and creates no package acceptance.
Only receipt-bound repository copies are read; external source paths are ignored.
"""

# Standard Library
import hashlib
import json
import shutil
import tempfile

from pathlib import Path

# Package Library
from kgfegmcp.errors import ManifestBuildError
from kgfegmcp.graph.models import FrameworkNode, StandardNode
from kgfegmcp.packages.checksums import calculate_file_sha256
from kgfegmcp.packages.decoder import iter_decoded_nodes, iter_decoded_relationships
from kgfegmcp.packages.normalization_models import (
    CopiedFramework,
    CopyReceipt,
    DetailedLearningProgression,
    LearningProgressionProvenanceIndex,
    NormalizationReceipt,
    PreparationResult,
    ProvenancePartition,
    StandardIdentity,
)
from kgfegmcp.packages.normalization_sources import (
    LOCAL_SOURCE_ROOT,
    checked_copy_files,
    iter_json_objects,
    read_json_object,
    require_no_symlinks,
)
from kgfegmcp.packages.wire import RelationshipWireEnvelope
from kgfegmcp.schemas import FrozenSchema

_PROPERTY_ALIASES = {
    "attribution_statement": "attributionStatement",
    "author": "author",
    "date_created": "dateCreated",
    "date_modified": "dateModified",
    "description": "description",
    "identifier": "identifier",
    "license": "license",
    "provider": "provider",
    "relationship_type": "relationshipType",
    "source_entity": "sourceEntity",
    "source_entity_key": "sourceEntityKey",
    "source_entity_value": "sourceEntityValue",
    "target_entity": "targetEntity",
    "target_entity_key": "targetEntityKey",
    "target_entity_value": "targetEntityValue",
}
_RECONCILIATION_ONLY = frozenset(
    {"as_lc_lp_kg_bundle.json", "as_lc_lp_nodes.jsonl", "as_lc_lp_relationships.jsonl"}
)


def _canonical_bytes(value: object) -> bytes:
    """Serialize deterministic UTF-8 JSON with sorted keys and one final newline.

    Parameters
    ----------
    value
        Original JSON evidence or a generated frozen contract.

    Returns
    -------
    bytes
        Canonical bytes without nonfinite numbers.

    Examples
    --------
    >>> _canonical_bytes({"id": "edge"})
    b'{"id":"edge"}\\n'
    """

    payload = (
        value.model_dump(by_alias=True, mode="json")
        if isinstance(value, FrozenSchema)
        else value
    )
    return (
        json.dumps(
            allow_nan=False,
            ensure_ascii=False,
            obj=payload,
            separators=(",", ":"),
            sort_keys=True,
        )
        + "\n"
    ).encode("utf-8")


def _check_bundle(
    *, edges: dict[str, DetailedLearningProgression], files: dict[str, Path]
) -> None:
    """Reconcile rich combined-bundle LP entries with both original split files.

    Parameters
    ----------
    edges
        Validated split records by stored ID.
    files
        Verified source files.

    Raises
    ------
    ManifestBuildError
        If the combined bundle loses or alters any split edge or its metadata.

    Examples
    --------
    >>> _check_bundle(edges=edges, files=files)
    """

    bundle = read_json_object(
        data=files["as_lc_lp_kg_bundle.json"].read_bytes(),
        label="as_lc_lp_kg_bundle.json",
    )
    combined: dict[str, DetailedLearningProgression] = {}

    for kind in ("buildsTowards", "relatesTo"):
        key = (
            "relationships_builds_towards"
            if kind == "buildsTowards"
            else "relationships_relates_to"
        )
        rows = bundle.get(key)

        if not isinstance(rows, list):
            raise ManifestBuildError(
                message="Combined LP bundle is missing its split arrays."
            )

        for row in rows:
            edge = DetailedLearningProgression.model_validate(row)

            if edge.relationship_type != kind or edge.identifier in combined:
                raise ManifestBuildError(
                    message="Combined LP bundle has conflicting entries."
                )

            combined[str(edge.identifier)] = edge

    if combined != edges:
        raise ManifestBuildError(
            message="Combined LP bundle and split records disagree."
        )


def _check_combined_export(
    *,
    edges: dict[str, DetailedLearningProgression],
    files: dict[str, Path],
    wire: dict[str, RelationshipWireEnvelope],
) -> None:
    """Compare explicit flat/envelope exports without inventing missing evidence.

    Parameters
    ----------
    edges
        Original split records and rich metadata.
    files
        Verified source paths.
    wire
        Normalized wire envelopes by relationship ID.

    Raises
    ------
    ManifestBuildError
        If combined LP coverage, metadata or wire selectors differ.

    Examples
    --------
    >>> _check_combined_export(edges=edges, files=files, wire=wire)
    """

    seen: set[str] = set()

    for row in iter_json_objects(files["as_lc_lp_relationships.jsonl"]):
        kind = row.get("label") if "properties" in row else row.get("relationship_type")

        if kind in {"hasChild", "supports"}:
            continue

        if kind not in {"buildsTowards", "relatesTo"}:
            raise ManifestBuildError(
                message="Combined export contains an unknown relationship type."
            )

        identifier = row.get("identifier")

        if (
            not isinstance(identifier, str)
            or identifier not in edges
            or identifier in seen
        ):
            raise ManifestBuildError(
                message="Combined LP export has unexpected or duplicate IDs."
            )

        if "properties" in row:
            matches = RelationshipWireEnvelope.model_validate(row) == wire[identifier]
        else:
            matches = (
                DetailedLearningProgression.model_validate(row) == edges[identifier]
            )

        if not matches:
            raise ManifestBuildError(
                message="Combined LP export differs from its split evidence."
            )

        seen.add(identifier)

    if seen != set(edges):
        raise ManifestBuildError(
            message="Combined LP export does not cover every split edge."
        )


def _check_provenance(
    *, edges: dict[str, DetailedLearningProgression], files: dict[str, Path]
) -> dict[str, object]:
    """Reconcile complete original provenance and accepted final claims with splits.

    Parameters
    ----------
    edges
        Stored split records.
    files
        Verified source paths.

    Returns
    -------
    dict[str, object]
        Original provenance entries, unmodified.

    Raises
    ------
    ManifestBuildError
        If metadata or accepted-claim coverage differs.

    Examples
    --------
    >>> provenance = _check_provenance(edges=edges, files=files)
    >>> set(provenance) == set(edges)
    True
    """

    provenance = read_json_object(
        data=files["lp_relationship_provenance.json"].read_bytes(),
        label="lp_relationship_provenance.json",
    )

    if provenance != {identifier: edge.metadata for identifier, edge in edges.items()}:
        raise ManifestBuildError(
            message="Original LP provenance and split metadata disagree."
        )

    final = read_json_object(
        data=files["lp_final_claims.json"].read_bytes(), label="lp_final_claims.json"
    )
    claims = final.get("claims")

    if not isinstance(claims, list):
        raise ManifestBuildError(message="Final claims must contain a claims array.")

    accepted: list[bytes] = []

    for claim in claims:
        if not isinstance(claim, dict) or not isinstance(claim.get("judgment"), dict):
            raise ManifestBuildError(message="Final claim is missing its judgment.")

        if claim["judgment"].get("decision") in {"buildsTowards", "relatesTo"}:
            accepted.append(_canonical_bytes(claim))

    expected = [_canonical_bytes(edge.metadata.get("claim")) for edge in edges.values()]

    if sorted(accepted) != sorted(expected):
        raise ManifestBuildError(
            message="Exported LP edges and accepted final claims disagree."
        )

    return provenance


def _normalize_edge(
    *, edge: DetailedLearningProgression, standards: dict[str, StandardIdentity]
) -> RelationshipWireEnvelope:
    """Resolve exact CASE endpoints and map slim string properties without changes.

    Parameters
    ----------
    edge
        Original detailed LP record.
    standards
        Existing CASE selectors and outer delivery IDs.

    Returns
    -------
    RelationshipWireEnvelope
        Strict slim delivery record with unaltered semantic property values.

    Raises
    ------
    ManifestBuildError
        If either exact endpoint is absent from the existing standards.

    Examples
    --------
    >>> record = _normalize_edge(edge=edge, standards=standards)
    >>> record.identifier == edge.identifier
    True
    """

    source = standards.get(str(edge.source_entity_value))
    target = standards.get(str(edge.target_entity_value))

    if source is None or target is None:
        raise ManifestBuildError(
            message="LP CASE endpoint does not resolve to an existing standard."
        )

    original = edge.model_dump(mode="json")
    properties = {
        alias: original[name]
        for name, alias in _PROPERTY_ALIASES.items()
        if original[name] is not None
    }
    properties["sourceEntityKey"] = properties["targetEntityKey"] = "caseIdentifierUUID"
    return RelationshipWireEnvelope.model_validate(
        {
            "identifier": edge.identifier,
            "label": edge.relationship_type,
            "properties": properties,
            "source_identifier": source.node_id,
            "source_labels": ["StandardsFrameworkItem"],
            "target_identifier": target.node_id,
            "target_labels": ["StandardsFrameworkItem"],
            "type": "relationship",
        }
    )


def _prepare_one(
    *,
    copy_receipt_sha256: str,
    files: dict[str, Path],
    framework: CopiedFramework,
    output_root: Path,
    project_dir: Path,
    receipt: CopyReceipt,
) -> PreparationResult:
    """Stage and publish one complete, verified preparation tree atomically.

    Parameters
    ----------
    copy_receipt_sha256
        Exact-byte local copy receipt identity.
    files
        Verified local copied files.
    framework
        Selected framework mapping.
    output_root
        Separate preparation root.
    project_dir
        Repository root.
    receipt
        Copy-time hash evidence.

    Returns
    -------
    PreparationResult
        Deterministic generated hashes and outcome.

    Examples
    --------
    >>> result = _prepare_one(
    ...     copy_receipt_sha256=receipt_hash, files=files, framework=mapping,
    ...     output_root=prepared, project_dir=root, receipt=receipt
    ... )
    >>> result.outcome
    'created'
    """

    standards = _read_standards(files=files, framework=framework)
    edges = _read_split_edges(files)
    wire = {
        identifier: _normalize_edge(edge=edge, standards=standards)
        for identifier, edge in edges.items()
    }
    _check_combined_export(edges=edges, files=files, wire=wire)
    _check_bundle(edges=edges, files=files)
    provenance = _check_provenance(edges=edges, files=files)
    _require_new_ids(files=files, identifiers=set(edges))
    target = output_root / str(framework.framework_id)
    require_no_symlinks(target)

    with tempfile.TemporaryDirectory(
        dir=output_root, prefix=".lp-preparation-"
    ) as scratch:
        stage = Path(scratch) / "inputs"
        stage.mkdir()
        separator = _write_delivery(
            files=files, stage=stage, token=str(framework.framework_id), wire=wire
        )
        _write_original_evidence(files=files, stage=stage)
        _write_partitions(files=files, provenance=provenance, stage=stage)
        hashes = _tree_hashes(stage)
        input_hashes = {
            name: calculate_file_sha256(path) for name, path in sorted(files.items())
        }
        normalization = NormalizationReceipt.model_validate(
            {
                "asLcRelationshipPrefixBytes": files["as_lc_relationships.jsonl"]
                .stat()
                .st_size,
                "buildsTowardsRelationships": sum(
                    e.relationship_type == "buildsTowards" for e in edges.values()
                ),
                "copyReceiptSha256": copy_receipt_sha256,
                "documentKey": framework.document_key,
                "frameworkCaseUuid": framework.framework_case_uuid,
                "frameworkId": framework.framework_id,
                "inputSha256": input_hashes,
                "newlineSeparatorAdded": separator,
                "outputSha256": hashes,
                "relatesToRelationships": sum(
                    e.relationship_type == "relatesTo" for e in edges.values()
                ),
            }
        )
        (stage / "detailed/lp_normalization_receipt.json").write_bytes(
            _canonical_bytes(normalization)
        )

        # Detect input drift before publishing, including changes during copying.
        checked_copy_files(
            framework=framework, project_dir=project_dir, receipt=receipt
        )
        hashes = _tree_hashes(stage)
        outcome = _publish_prepared(hashes=hashes, stage=stage, target=target)

    return PreparationResult.model_validate(
        {
            "buildsTowardsRelationships": normalization.builds_towards_relationships,
            "frameworkId": framework.framework_id,
            "outputDirectory": str(framework.framework_id),
            "outcome": outcome,
            "relatesToRelationships": normalization.relates_to_relationships,
            "sha256": hashes,
        }
    )


def _publish_prepared(*, hashes: dict[str, str], stage: Path, target: Path) -> str:
    """Publish a new preparation or recognize an exactly identical existing tree.

    Parameters
    ----------
    hashes
        Complete generated relative file identities.
    stage
        Complete staged directory.
    target
        Final preparation directory.

    Returns
    -------
    str
        Created or existing-identical outcome.

    Raises
    ------
    ManifestBuildError
        If an existing destination conflicts or is not a directory.

    Examples
    --------
    >>> _publish_prepared(hashes=hashes, stage=stage, target=target)
    'created'
    """

    if target.exists():
        if not target.is_dir() or _tree_hashes(target) != hashes:
            raise ManifestBuildError(
                message="Existing preparation differs; choose a separate output root."
            )

        return "existing_identical"

    stage.rename(target)
    return "created"


def _read_split_edges(files: dict[str, Path]) -> dict[str, DetailedLearningProgression]:
    """Read only stored split relationships with strict fields and unique IDs.

    Parameters
    ----------
    files
        Receipt-bound source paths.

    Returns
    -------
    dict[str, DetailedLearningProgression]
        Original edges keyed by source ID.

    Raises
    ------
    ManifestBuildError
        If a split type or identifier conflicts.

    Examples
    --------
    >>> edges = _read_split_edges(files)
    >>> all(e.identifier == k for k, e in edges.items())
    True
    """

    edges: dict[str, DetailedLearningProgression] = {}

    for kind, name in (
        ("buildsTowards", "lp_relationships_builds_towards.jsonl"),
        ("relatesTo", "lp_relationships_relates_to.jsonl"),
    ):
        for row in iter_json_objects(files[name]):
            edge = DetailedLearningProgression.model_validate(row)

            if edge.relationship_type != kind or edge.identifier in edges:
                raise ManifestBuildError(
                    message="Split LP record type or identifier conflicts."
                )

            edges[str(edge.identifier)] = edge

    return edges


def _read_standards(
    *, files: dict[str, Path], framework: CopiedFramework
) -> dict[str, StandardIdentity]:
    """Read exact standards selectors and confirm the copied framework identity.

    Parameters
    ----------
    files
        Receipt-bound source paths.
    framework
        Expected framework CASE mapping.

    Returns
    -------
    dict[str, StandardIdentity]
        Unique exact CASE UUIDs mapped to existing outer IDs.

    Raises
    ------
    ManifestBuildError
        If node IDs, CASE selectors or framework identity conflict.

    Examples
    --------
    >>> standards = _read_standards(files=files, framework=mapping)
    >>> standards[case_uuid].case_identifier_uuid == case_uuid
    True
    """

    identifiers: set[str] = set()
    roots: list[str | None] = []
    standards: dict[str, StandardIdentity] = {}

    for node in iter_decoded_nodes(source=files["as_lc_nodes.jsonl"]):
        if node.node_id in identifiers:
            raise ManifestBuildError(
                message="Copied nodes contain duplicate outer IDs."
            )

        identifiers.add(str(node.node_id))

        if isinstance(node, FrameworkNode):
            roots.append(node.case_identifier_uuid)

        if isinstance(node, StandardNode):
            case = node.case_identifier_uuid

            if case is None or case in standards:
                raise ManifestBuildError(
                    message="Standard CASE selector is missing or duplicated."
                )

            standards[str(case)] = StandardIdentity(
                case_identifier_uuid=case, node_id=node.node_id
            )

    if roots != [framework.framework_case_uuid]:
        raise ManifestBuildError(
            message="Copied framework CASE UUID differs from its receipt."
        )

    return standards


def _require_new_ids(*, files: dict[str, Path], identifiers: set[str]) -> None:
    """Prevent appended LP IDs from colliding with preserved AS/LC relationships.

    Parameters
    ----------
    files
        Original delivery paths.
    identifiers
        Unique stored LP IDs.

    Raises
    ------
    ManifestBuildError
        If original relationships are duplicated, contain LP or overlap LP IDs.

    Examples
    --------
    >>> _require_new_ids(files=files, identifiers=set(edges))
    """

    seen: set[str] = set()

    for edge in iter_decoded_relationships(source=files["as_lc_relationships.jsonl"]):
        identifier = str(edge.relationship_id)

        if (
            edge.label not in {"hasChild", "supports"}
            or identifier in seen
            or identifier in identifiers
        ):
            raise ManifestBuildError(
                message="Original AS/LC relationships contain conflicting IDs or types."
            )

        seen.add(identifier)


def _tree_hashes(directory: Path) -> dict[str, str]:
    """Hash a preparation tree while rejecting links and nonregular entries.

    Parameters
    ----------
    directory
        Staged or existing preparation directory.

    Returns
    -------
    dict[str, str]
        Sorted repository-independent relative identities.

    Raises
    ------
    ManifestBuildError
        If a tree contains a symlink or nonregular entry.

    Examples
    --------
    >>> _tree_hashes(empty_directory)
    {}
    """

    hashes: dict[str, str] = {}

    for path in sorted(directory.rglob("*")):
        if path.is_symlink() or not (path.is_file() or path.is_dir()):
            raise ManifestBuildError(
                message="Preparation trees require regular files and directories."
            )

        if path.is_file():
            hashes[path.relative_to(directory).as_posix()] = str(
                calculate_file_sha256(path)
            )

    return hashes


def _write_delivery(
    *,
    files: dict[str, Path],
    stage: Path,
    token: str,
    wire: dict[str, RelationshipWireEnvelope],
) -> bool:
    """Preserve node bytes and relationship prefix, appending sorted LP wire lines.

    Parameters
    ----------
    files
        Original delivery paths.
    stage
        Staged preparation root.
    token
        Safe framework ID filename token.
    wire
        Normalized LP records.

    Returns
    -------
    bool
        Whether an LF separator was needed after the original relationship bytes.

    Examples
    --------
    >>> _write_delivery(files=files, stage=stage, token="framework", wire=wire)
    False
    """

    delivery = stage / "delivery"
    delivery.mkdir()
    nodes = delivery / f"as_lc_lp_nodes_{token}.jsonl"
    shutil.copyfile(dst=nodes, src=files["as_lc_nodes.jsonl"])

    if calculate_file_sha256(nodes) != calculate_file_sha256(
        files["as_lc_nodes.jsonl"]
    ):
        raise ManifestBuildError(message="Node delivery bytes changed during copying.")

    source = files["as_lc_relationships.jsonl"]
    destination = delivery / f"as_lc_lp_relationships_{token}.jsonl"
    shutil.copyfile(dst=destination, src=source)

    if calculate_file_sha256(destination) != calculate_file_sha256(source):
        raise ManifestBuildError(
            message="Relationship prefix bytes changed during copying."
        )

    with source.open("rb") as stream:
        length = source.stat().st_size

        if length:
            stream.seek(length - 1)

        separator = bool(wire and length and stream.read(1) != b"\n")

    with destination.open("ab") as stream:
        if separator:
            stream.write(b"\n")

        for record in sorted(wire.values(), key=lambda e: (e.label, e.identifier)):
            stream.write(
                _canonical_bytes(
                    record.model_dump(by_alias=True, exclude_none=True, mode="json")
                )
            )

    return separator


def _write_original_evidence(*, files: dict[str, Path], stage: Path) -> None:
    """Copy required evidence unchanged, excluding duplicate combined inputs.

    Parameters
    ----------
    files
        Original copied inputs.
    stage
        Staged preparation tree.

    Raises
    ------
    ManifestBuildError
        If copying changes an evidence file's byte identity.

    Examples
    --------
    >>> _write_original_evidence(files=files, stage=stage)
    """

    detailed = stage / "detailed"
    detailed.mkdir()
    excluded = _RECONCILIATION_ONLY | {"as_lc_nodes.jsonl", "as_lc_relationships.jsonl"}

    for name, source in sorted(files.items()):
        if name not in excluded:
            destination = detailed / name
            shutil.copyfile(dst=destination, src=source)

            if calculate_file_sha256(destination) != calculate_file_sha256(source):
                raise ManifestBuildError(
                    message="Original evidence bytes changed during copying."
                )


def _write_partitions(
    *, files: dict[str, Path], provenance: dict[str, object], stage: Path
) -> None:
    """Write every canonical partition and an index bound to the original map.

    Parameters
    ----------
    files
        Original provenance path.
    provenance
        Original entries reconciled to exported LP IDs.
    stage
        Complete staged delivery/evidence root.

    Examples
    --------
    >>> _write_partitions(files=files, provenance=provenance, stage=stage)
    """

    buckets: list[dict[str, object]] = [{} for _ in range(64)]

    for identifier, entry in provenance.items():
        buckets[provenance_partition(identifier)][identifier] = entry

    additional = stage / "additional"
    additional.mkdir()
    partitions: dict[str, ProvenancePartition] = {}

    for number, bucket in enumerate(buckets):
        relative = f"additional/lp_relationship_provenance_shard_{number:02d}.json"
        path = stage / relative
        path.write_bytes(_canonical_bytes(bucket))
        partitions[f"learningProgressionProvenanceShard{number:02d}"] = (
            ProvenancePartition.model_validate(
                {
                    "artifactPath": relative,
                    "entryCount": len(bucket),
                    "sha256": calculate_file_sha256(path),
                }
            )
        )

    index = LearningProgressionProvenanceIndex(
        original_provenance_sha256=calculate_file_sha256(
            files["lp_relationship_provenance.json"]
        ),
        partitions=partitions,
    )
    (stage / "detailed/lp_relationship_provenance_index.json").write_bytes(
        _canonical_bytes(index)
    )


def _validate_output(
    *, destination: Path, project_dir: Path, receipt: CopyReceipt
) -> None:
    """Keep preparation separate from copied inputs and active runtime/config roots.

    Parameters
    ----------
    destination
        Resolved proposed output root.
    project_dir
        Repository root.
    receipt
        Known copied input mappings.

    Raises
    ------
    ManifestBuildError
        If output intersects a protected tree or contains the local copy receipt.

    Examples
    --------
    >>> _validate_output(destination=prepared, project_dir=root, receipt=receipt)
    """

    protected = [
        project_dir / name
        for name in ("config", "data/graph_packages", "data/input_artifacts")
    ]
    protected.extend(
        project_dir / str(f.destination_directory) for f in receipt.frameworks
    )
    protected.append(project_dir / LOCAL_SOURCE_ROOT / "copy_receipt.json")

    if any(
        destination == p
        or destination.is_relative_to(p)
        or p.is_relative_to(destination)
        for p in protected
    ):
        raise ManifestBuildError(
            message="Preparation output overlaps copied inputs or active roots."
        )


def _validate_selection(*, framework_id: str | None, receipt: CopyReceipt) -> None:
    """Require unique receipt mappings and an exact optional framework selection.

    Parameters
    ----------
    framework_id
        Requested exact ID or all mappings.
    receipt
        Selected local receipt.

    Raises
    ------
    ManifestBuildError
        If coverage, mapping uniqueness or framework selection is invalid.

    Examples
    --------
    >>> _validate_selection(framework_id=None, receipt=receipt)
    """

    identifiers = [str(f.framework_id) for f in receipt.frameworks]
    documents = [f.document_key for f in receipt.frameworks]
    paths = [str(f.destination_path) for f in receipt.files]

    if (
        not identifiers
        or len(set(identifiers)) != len(identifiers)
        or len(set(documents)) != len(documents)
        or len(set(paths)) != len(paths)
        or receipt.selected_file_count != len(paths)
        or set(f.framework_id for f in receipt.files) != set(identifiers)
    ):
        raise ManifestBuildError(message="Copy receipt coverage or mappings conflict.")

    if framework_id is not None and framework_id not in identifiers:
        raise ManifestBuildError(
            message="Framework ID is not present in the local copy receipt."
        )


def prepare_learning_progressions(
    *,
    framework_id: str | None = None,
    output_root: Path,
    project_dir: Path,
    receipt_path: Path,
) -> tuple[PreparationResult, ...]:
    """Prepare selected receipt-bound frameworks without modifying runtime roots.

    Parameters
    ----------
    framework_id
        Optional exact copied framework ID; omitted selects all mappings.
    output_root
        Separate destination for deterministic local preparation trees.
    project_dir
        Repository root containing the verified source copies.
    receipt_path
        Repository-local copy receipt, never an external source location.

    Returns
    -------
    tuple[PreparationResult, ...]
        Stable framework-ordered hashes and publication outcomes.

    Raises
    ------
    ManifestBuildError
        If inputs drift, paths are unsafe, reconciliation fails or output conflicts.

    Examples
    --------
    >>> results = prepare_learning_progressions(
    ...     output_root=prepared, project_dir=root, receipt_path=copy_receipt
    ... )
    >>> len(results)
    6
    """

    root = project_dir.resolve()
    source_root = root / LOCAL_SOURCE_ROOT
    local_receipt = receipt_path if receipt_path.is_absolute() else root / receipt_path
    require_no_symlinks(local_receipt)

    if local_receipt != source_root / "copy_receipt.json":
        raise ManifestBuildError(
            message="Preparation requires the repository-local copy receipt."
        )

    receipt = CopyReceipt.model_validate(
        read_json_object(data=local_receipt.read_bytes(), label="copy_receipt.json")
    )
    _validate_selection(framework_id=framework_id, receipt=receipt)
    destination = output_root if output_root.is_absolute() else root / output_root
    require_no_symlinks(destination)
    destination = destination.resolve()
    _validate_output(destination=destination, project_dir=root, receipt=receipt)
    selected = sorted(
        (
            f
            for f in receipt.frameworks
            if framework_id is None or f.framework_id == framework_id
        ),
        key=lambda f: f.framework_id,
    )
    results: list[PreparationResult] = []
    receipt_hash = calculate_file_sha256(local_receipt)

    for framework in selected:
        files = checked_copy_files(
            framework=framework, project_dir=root, receipt=receipt
        )
        destination.mkdir(parents=True, exist_ok=True)
        results.append(
            _prepare_one(
                copy_receipt_sha256=str(receipt_hash),
                files=files,
                framework=framework,
                output_root=destination,
                project_dir=root,
                receipt=receipt,
            )
        )

    if calculate_file_sha256(local_receipt) != receipt_hash:
        raise ManifestBuildError(message="Copy receipt changed during preparation.")

    return tuple(results)


def provenance_partition(relationship_id: str) -> int:
    """Return the fixed deterministic provenance bucket for an unchanged ID.

    Parameters
    ----------
    relationship_id
        Original stored relationship identifier.

    Returns
    -------
    int
        Bucket number from zero through 63.

    Examples
    --------
    >>> 0 <= provenance_partition("stored-edge-id") < 64
    True
    """

    return hashlib.sha256(relationship_id.encode("utf-8")).digest()[0] % 64
