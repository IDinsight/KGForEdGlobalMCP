"""Read receipt-bound repository-local copies without consulting external sources."""

# Standard Library
import json

from collections.abc import Iterator
from math import isfinite
from pathlib import Path

# Package Library
from kgfegmcp.errors import ManifestBuildError
from kgfegmcp.packages.checksums import calculate_file_sha256
from kgfegmcp.packages.normalization_models import (
    CopiedFile,
    CopiedFramework,
    CopyReceipt,
)

COPIED_BASENAMES = frozenset(
    {
        "as_entity_provenance.json",
        "as_kg_bundle.json",
        "as_lc_kg_bundle.json",
        "as_lc_lp_kg_bundle.json",
        "as_lc_lp_nodes.jsonl",
        "as_lc_lp_relationships.jsonl",
        "as_lc_nodes.jsonl",
        "as_lc_relationships.jsonl",
        "as_lc_validation_report.json",
        "as_relationships_has_child.jsonl",
        "as_standards_framework.json",
        "as_standards_framework_items.jsonl",
        "as_unresolved_items.json",
        "lc_dedup_groups.json",
        "lc_entity_provenance.json",
        "lc_generation_summary.json",
        "lp_final_claims.json",
        "lp_generation_summary.json",
        "lp_relationship_provenance.json",
        "lp_relationships_builds_towards.jsonl",
        "lp_relationships_relates_to.jsonl",
        "lp_unresolved_items.json",
        "lp_validation_report.json",
    }
)
LOCAL_SOURCE_ROOT = Path("data/source_artifacts/learning_progressions")


def _finite_float(value: str) -> float:
    """Reject JSON numeric overflow instead of retaining an infinite float.

    Parameters
    ----------
    value
        Source JSON decimal token.

    Returns
    -------
    float
        Finite decoded source value.

    Raises
    ------
    ValueError
        If the token overflows the finite float range.

    Examples
    --------
    >>> _finite_float("0.75")
    0.75
    """

    result = float(value)

    if not isfinite(result):
        raise ValueError("Nonfinite JSON number.")

    return result


def _unique_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    """Read JSON members without silently replacing duplicate keys.

    Parameters
    ----------
    pairs
        Source-ordered JSON object members.

    Returns
    -------
    dict[str, object]
        Original members with unique keys.

    Raises
    ------
    ValueError
        If a member is repeated.

    Examples
    --------
    >>> _unique_object([("id", "edge")])
    {'id': 'edge'}
    """

    result: dict[str, object] = {}

    for key, value in pairs:
        if key in result:
            raise ValueError("Duplicate JSON member.")

        result[key] = value

    return result


def _unsupported_constant(value: str) -> None:
    """Reject nonfinite constants outside standard JSON.

    Parameters
    ----------
    value
        Invalid JSON numeric token.

    Raises
    ------
    ValueError
        Always, because nonfinite evidence cannot be retained as canonical JSON.

    Examples
    --------
    >>> _unsupported_constant("NaN")
    Traceback (most recent call last):
        ...
    ValueError: Nonfinite JSON constant.
    """

    raise ValueError("Nonfinite JSON constant.")


def checked_copy_files(
    *, framework: CopiedFramework, project_dir: Path, receipt: CopyReceipt
) -> dict[str, Path]:
    """Verify the selected framework's exact receipt-bound copied input set.

    Parameters
    ----------
    framework
        Repository-local source mapping.
    project_dir
        Resolved project root.
    receipt
        Verified local copy receipt.

    Returns
    -------
    dict[str, Path]
        All 23 selected files keyed by basename.

    Raises
    ------
    ManifestBuildError
        If coverage, local paths, sizes or recorded hashes disagree.

    Examples
    --------
    >>> files = checked_copy_files(
    ...     framework=mapping, project_dir=root, receipt=receipt
    ... )
    >>> len(files)
    23
    """

    expected_directory = LOCAL_SOURCE_ROOT / framework.document_key / "kgs"

    if str(framework.destination_directory) != expected_directory.as_posix():
        raise ManifestBuildError(
            message="Copy mapping is outside its local source slot."
        )

    entries = [f for f in receipt.files if f.framework_id == framework.framework_id]
    files: dict[str, Path] = {}

    for entry in entries:
        path = project_dir / str(entry.destination_path)

        if (
            entry.document_key != framework.document_key
            or path.parent != project_dir / expected_directory
            or path.name not in COPIED_BASENAMES
            or path.name in files
        ):
            raise ManifestBuildError(
                message="Copied file coverage or mapping conflicts."
            )

        require_no_symlinks(path)
        verify_copied_file(entry=entry, path=path)
        files[path.name] = path

    if set(files) != COPIED_BASENAMES:
        raise ManifestBuildError(message="Preparation requires all 23 copied inputs.")

    return files


def iter_json_objects(path: Path) -> Iterator[dict[str, object]]:
    """Stream strict source JSONL objects without rewriting their data.

    Parameters
    ----------
    path
        Verified local JSONL file.

    Yields
    ------
    dict[str, object]
        Each physical nonblank record.

    Examples
    --------
    >>> rows = list(iter_json_objects(split_path))
    >>> isinstance(rows[0], dict)
    True
    """

    with path.open(encoding="utf-8") as stream:
        for line_number, line in enumerate(iterable=stream, start=1):
            if line.strip():
                yield read_json_object(data=line, label=f"{path.name}:{line_number}")


def read_json_object(*, data: bytes | str, label: str) -> dict[str, object]:
    """Parse a JSON object while rejecting duplicate keys and nonfinite values.

    Parameters
    ----------
    data
        Source bytes or one source line.
    label
        Safe file/line identity for diagnostics.

    Returns
    -------
    dict[str, object]
        Unaltered parsed evidence.

    Raises
    ------
    ManifestBuildError
        If JSON is malformed or is not an object.

    Examples
    --------
    >>> read_json_object(data=b'{"id":"edge"}', label="source.json")
    {'id': 'edge'}
    """

    try:
        value = json.loads(
            object_pairs_hook=_unique_object,
            parse_constant=_unsupported_constant,
            parse_float=_finite_float,
            s=data,
        )
    except ValueError as error:
        raise ManifestBuildError(message=f"Malformed JSON in {label}.") from error

    if not isinstance(value, dict):
        raise ManifestBuildError(message=f"Expected a JSON object in {label}.")

    return value


def require_no_symlinks(path: Path) -> None:
    """Reject symlinks in existing path components before filesystem operations.

    Parameters
    ----------
    path
        Absolute local input or output path.

    Raises
    ------
    ManifestBuildError
        If any component is a symlink.

    Examples
    --------
    >>> require_no_symlinks(root / "data")
    """

    if any(p.is_symlink() for p in (path, *path.parents)):
        raise ManifestBuildError(message="Preparation paths may not contain symlinks.")


def verify_copied_file(*, entry: CopiedFile, path: Path) -> None:
    """Compare current copied bytes against all recorded copy-time hashes.

    Parameters
    ----------
    entry
        Verified receipt entry.
    path
        Exact local copy to check.

    Raises
    ------
    ManifestBuildError
        If the file is missing, changed or its verification hashes conflict.

    Examples
    --------
    >>> verify_copied_file(entry=entry, path=copied_path)
    """

    if (
        not path.is_file()
        or path.stat().st_size != entry.size_bytes
        or calculate_file_sha256(path) != entry.destination_sha256
        or entry.destination_sha256 != entry.source_sha256_before
        or entry.source_sha256_before != entry.source_sha256_after
    ):
        raise ManifestBuildError(message=f"Copy receipt mismatch for {path.name}.")
