"""This module contains functionalities to calculate exact-byte checksums and canonical
snapshot artifact-set digests.

This module provides domain-neutral checksum operations used during graph-package
construction and validation. It calculates qualified SHA-256 digests for in-memory
bytes, binary streams, and files without decoding, rewriting, normalizing, or otherwise
changing their contents.

It also calculates the canonical immutable snapshot artifact-set hash. To produce that
hash, all declared artifact checksums are converted to their qualified sha256:<hex>
representation, sorted in ascending ASCII order, preserved even when duplicate checksum
values occur, and serialized with one line-feed byte after every entry. The SHA-256
digest of that canonical byte sequence becomes the artifact-set hash used by the
existing snapshot identifier builder.

Artifact paths and filenames are intentionally excluded from this canonicalization.
Package paths are protected separately by the manifest's artifact mapping and checksum
validation, while the snapshot hash represents the immutable artifact contents.
"""

# Standard Library
import hashlib

from collections.abc import Iterable, Iterator
from pathlib import Path
from typing import BinaryIO

# Third Party Library
from pydantic import TypeAdapter

# Package Library
from kgfegmcp.domain.identifiers import Sha256Digest

_READ_CHUNK_SIZE = 1024 * 1024
_SHA256_ADAPTER: TypeAdapter[Sha256Digest] = TypeAdapter(Sha256Digest)


def _calculate_sha256(chunks: Iterable[bytes]) -> Sha256Digest:
    """Calculate one qualified SHA-256 digest from ordered byte chunks.

    Parameters
    ----------
    chunks
        Ordered exact-byte chunks to hash without decoding or normalization.

    Returns
    -------
    Sha256Digest
        Lowercase digest in ``sha256:<64-hex>`` form.
    """

    hasher = hashlib.sha256()

    for chunk in chunks:
        hasher.update(chunk)

    return _SHA256_ADAPTER.validate_python(f"sha256:{hasher.hexdigest()}")


def _iter_stream_chunks(stream: BinaryIO) -> Iterator[bytes]:
    """Yield exact byte chunks from an open binary stream.

    Parameters
    ----------
    stream
        Open binary stream positioned at the first byte to hash.

    Yields
    ------
    bytes
        Consecutive non-empty chunks through end-of-file.
    """

    while chunk := stream.read(_READ_CHUNK_SIZE):
        yield chunk


def calculate_bytes_sha256(value: bytes) -> Sha256Digest:
    """Calculate a qualified SHA-256 digest from exact bytes.

    Parameters
    ----------
    value
        Bytes to hash without decoding or normalization.

    Returns
    -------
    Sha256Digest
        Lowercase digest in ``sha256:<64-hex>`` form.
    """

    return _calculate_sha256((value,))


def calculate_file_sha256(path: Path) -> Sha256Digest:
    """Calculate a qualified SHA-256 digest from exact file bytes.

    Parameters
    ----------
    path
        File to read in binary mode.

    Returns
    -------
    Sha256Digest
        Lowercase digest in ``sha256:<64-hex>`` form.

    Raises
    ------
    OSError
        If the file cannot be opened or read completely.
    """

    with path.open("rb") as stream:
        return calculate_stream_sha256(stream)


def calculate_snapshot_artifact_set_sha256(
    checksums: Iterable[Sha256Digest],
) -> Sha256Digest:
    """Hash the canonical ordered list of immutable artifact checksums.

    The canonical byte sequence contains every qualified checksum, including duplicate
    values, sorted in ascending ASCII order and terminated by one LF byte per entry.

    Parameters
    ----------
    checksums
        Qualified checksums for all declared immutable snapshot artifacts.

    Returns
    -------
    Sha256Digest
        Qualified SHA-256 digest of the canonical checksum sequence.

    Raises
    ------
    ValueError
        If no artifact checksums are supplied.
    """

    ordered_checksums = sorted(str(checksum) for checksum in checksums)

    if not ordered_checksums:
        raise ValueError("At least one artifact checksum is required.")

    canonical_bytes = "".join(f"{checksum}\n" for checksum in ordered_checksums).encode(
        "utf-8"
    )
    return calculate_bytes_sha256(canonical_bytes)


def calculate_stream_sha256(stream: BinaryIO) -> Sha256Digest:
    """Calculate a qualified SHA-256 digest from an open binary stream.

    The stream is consumed from its current position through end-of-file and is not
    closed by this function.

    Parameters
    ----------
    stream
        Open binary stream positioned at the first byte to hash.

    Returns
    -------
    Sha256Digest
        Lowercase digest in ``sha256:<64-hex>`` form.

    Raises
    ------
    OSError
        If the stream cannot be read completely.
    """

    return _calculate_sha256(_iter_stream_chunks(stream))
