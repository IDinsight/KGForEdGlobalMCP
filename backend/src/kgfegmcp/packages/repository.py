"""This module discovers graph packages and persists controlled validation transitions.

This module provides the filesystem boundary for graph packages. It treats the
configured graph-packages root as trusted and discovers packages only through the
established ``<frameworkId>/<snapshotId>`` directory structure. Package candidates are
validated against their directory names, kept beneath the configured root, and rejected
when selected path components are symbolic links, malformed entries, or unsupported
filesystem objects.

The repository also owns validation-status persistence. It permits only a one-time
transition from ``pending`` to ``passed``, ``failed``, or ``quarantined``. The loader
and validator verify package integrity before requesting persistence; this repository
then reconfirms the candidate location and exact manifest bytes immediately before the
write. It assigns ``validatedAt`` and replaces the manifest atomically without changing
``createdAt``, artifact bytes, or package-defining manifest fields.

This module does not load profiles, verify artifact checksums, decode graph records, or
determine whether graph contents satisfy package and profile semantics. Those
responsibilities belong to the package loader and validator.
"""

# Future Library
from __future__ import annotations

# Standard Library
import json
import os
import stat
import tempfile

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Final

# Third Party Library
from pydantic import TypeAdapter, ValidationError

# Package Library
from kgfegmcp.domain.enums import GraphType, ValidationStatus
from kgfegmcp.domain.identifiers import FrameworkId, SnapshotId
from kgfegmcp.errors import PackageValidationError
from kgfegmcp.packages.models import (
    SUPPORTED_PACKAGE_REVISION,
    GraphPackageManifest,
    PackageValidation,
)

_FRAMEWORK_ID_ADAPTER: TypeAdapter[FrameworkId] = TypeAdapter(FrameworkId)
_SNAPSHOT_ID_ADAPTER: TypeAdapter[SnapshotId] = TypeAdapter(SnapshotId)
_TERMINAL_STATUSES: Final[frozenset[ValidationStatus]] = frozenset(
    {ValidationStatus.FAILED, ValidationStatus.PASSED, ValidationStatus.QUARANTINED}
)
PACKAGE_MANIFEST_FILENAME: Final[str] = "package_manifest.json"


@dataclass(frozen=True, slots=True)
class GraphPackageCandidate:
    """Identify one safely discovered package directory beneath the trust root."""

    framework_id: FrameworkId
    package_path: Path
    snapshot_id: SnapshotId

    @property
    def manifest_path(self) -> Path:
        """Return the established manifest path inside the package directory.

        Returns
        -------
        Path
            Internal package-manifest path.
        """

        return self.package_path / PACKAGE_MANIFEST_FILENAME

    @property
    def reference(self) -> str:
        """Return a safe public package reference without a local filesystem path.

        Returns
        -------
        str
            ``<frameworkId>/<snapshotId>`` reference.
        """

        return f"{self.framework_id}/{self.snapshot_id}"


@dataclass(frozen=True, slots=True)
class GraphPackageRepository:
    """Discover packages and own controlled validation-status persistence."""

    graph_packages_root: Path

    @staticmethod
    def _atomically_replace_manifest(
        *,
        candidate: GraphPackageCandidate,
        manifest_bytes: bytes,
        manifest_path: Path,
        updated_bytes: bytes,
    ) -> None:
        """Atomically replace the manifest file with verified updated bytes.

        Parameters
        ----------
        candidate
            Safely discovered package candidate.
        manifest_bytes
            Exact bytes expected to still be present immediately before replacement.
        manifest_path
            Manifest path proven safe to replace.
        updated_bytes
            Canonical bytes to persist in place of the current manifest.

        Raises
        ------
        PackageValidationError
            If the manifest changed just before replacement, or the same-directory
            atomic replacement could not be completed and verified safely.
        """

        temporary_path: Path | None = None

        try:
            with tempfile.NamedTemporaryFile(
                delete=False,
                dir=manifest_path.parent,
                mode="wb",
                prefix=".package_manifest.",
                suffix=".tmp",
            ) as stream:
                temporary_path = Path(stream.name)
                stream.write(updated_bytes)
                stream.flush()
                os.fsync(stream.fileno())

            original_mode = stat.S_IMODE(os.lstat(manifest_path).st_mode)
            temporary_path.chmod(original_mode)
            staged_bytes = _read_regular_file_without_following(temporary_path)

            if staged_bytes != updated_bytes:
                raise OSError("The staged manifest bytes changed unexpectedly.")

            GraphPackageManifest.model_validate_json(staged_bytes)
            latest_bytes = _read_regular_file_without_following(manifest_path)

            if latest_bytes != manifest_bytes:
                # This concurrent-change signal is a PackageValidationError, which is
                # deliberately not among the wrapped types below, so it propagates
                # unchanged with its specific message rather than the generic one.
                raise _package_error(
                    details={"package_reference": candidate.reference},
                    message="The package manifest changed during validation.",
                )

            os.replace(dst=manifest_path, src=temporary_path)
            temporary_path = None

            persisted_bytes = _read_regular_file_without_following(manifest_path)

            if persisted_bytes != updated_bytes:
                raise OSError("The persisted manifest bytes changed unexpectedly.")

            GraphPackageManifest.model_validate_json(persisted_bytes)

            if os.name != "nt":
                directory_descriptor = os.open(
                    flags=os.O_RDONLY, path=manifest_path.parent
                )

                try:
                    os.fsync(directory_descriptor)
                finally:
                    os.close(directory_descriptor)
        except (OSError, ValidationError, ValueError) as error:
            raise _package_error(
                details={
                    "manifest_path": str(manifest_path),
                    "package_reference": candidate.reference,
                },
                message="The package validation status could not be persisted safely.",
            ) from error
        finally:
            if temporary_path is not None:
                try:
                    temporary_path.unlink(missing_ok=True)
                except OSError:
                    pass

    @staticmethod
    def _build_terminal_manifest(
        *,
        candidate: GraphPackageCandidate,
        manifest: GraphPackageManifest,
        target_status: ValidationStatus,
        validated_at: datetime,
    ) -> GraphPackageManifest:
        """Build the terminal manifest, changing only its validation block.

        Parameters
        ----------
        candidate
            Safely discovered package candidate.
        manifest
            Validated pending manifest to transition.
        target_status
            Terminal status to record in the new validation block.
        validated_at
            One-time validation timestamp to record.

        Returns
        -------
        GraphPackageManifest
            Validated manifest identical to the original except its validation block.

        Raises
        ------
        PackageValidationError
            If the transitioned manifest is invalid or any package-defining field
            (including ``createdAt``) would change.
        """

        updated_payload = manifest.model_dump(mode="python")
        updated_payload["validation"] = PackageValidation(
            status=target_status, validated_at=validated_at
        )

        try:
            updated_manifest = GraphPackageManifest.model_validate(updated_payload)
        except ValidationError as error:
            raise _package_error(
                details={
                    "package_reference": candidate.reference,
                    "validation_errors": error.errors(
                        include_input=False, include_url=False
                    ),
                },
                message="The terminal manifest transition is invalid.",
            ) from error

        defining_before = manifest.model_dump(exclude={"validation"}, mode="python")
        defining_after = updated_manifest.model_dump(
            exclude={"validation"}, mode="python"
        )

        if (
            defining_before != defining_after
            or updated_manifest.created_at != manifest.created_at
        ):
            raise _package_error(
                details={"package_reference": candidate.reference},
                message="Validation attempted to change package-defining manifest fields.",
            )

        return updated_manifest

    @staticmethod
    def _candidate_from_names(
        *, framework_name: str, root: Path, snapshot_name: str
    ) -> GraphPackageCandidate:
        """Validate identity names and construct one safe package candidate.

        Parameters
        ----------
        framework_name
            Direct child name under the configured root.
        root
            Resolved graph-packages trust boundary.
        snapshot_name
            Direct child name under the framework directory.

        Returns
        -------
        GraphPackageCandidate
            Safely resolved candidate.

        Raises
        ------
        PackageValidationError
            If names are invalid, the snapshot namespace disagrees, or any selected
            descendant is a symlink or non-directory.
        """

        try:
            framework_id = _FRAMEWORK_ID_ADAPTER.validate_python(framework_name)
            snapshot_id = _SNAPSHOT_ID_ADAPTER.validate_python(snapshot_name)
        except ValidationError as error:
            raise _package_error(
                details={
                    "framework_entry": framework_name,
                    "snapshot_entry": snapshot_name,
                    "validation_errors": error.errors(
                        include_input=False, include_url=False
                    ),
                },
                message="A graph-package directory has an invalid identifier name.",
            ) from error

        if str(snapshot_id).partition("@")[0] != str(framework_id):
            raise _package_error(
                details={
                    "framework_id": str(framework_id),
                    "snapshot_id": str(snapshot_id),
                },
                message="A graph-package snapshot directory is under the wrong framework.",
            )

        framework_path = root / str(framework_id)
        package_path = framework_path / str(snapshot_id)

        for path, role in (
            (framework_path, "framework directory"),
            (package_path, "snapshot directory"),
        ):
            if path.is_symlink():
                raise _package_error(
                    details={"entry_path": str(path), "entry_role": role},
                    message=f"A graph-package {role} may not be a symbolic link.",
                )

            if not path.is_dir():
                raise _package_error(
                    details={"entry_path": str(path), "entry_role": role},
                    message=f"A graph-package {role} is not a directory.",
                )

        try:
            resolved_package_path = package_path.resolve(strict=True)
        except OSError as error:
            raise _package_error(
                details={"package_path": str(package_path)},
                message="A graph-package directory is unavailable.",
            ) from error

        if not resolved_package_path.is_relative_to(root):
            raise _package_error(
                details={
                    "graph_packages_root": str(root),
                    "package_path": str(resolved_package_path),
                },
                message="A graph-package directory escapes the configured root.",
            )

        return GraphPackageCandidate(
            framework_id=framework_id,
            package_path=resolved_package_path,
            snapshot_id=snapshot_id,
        )

    @staticmethod
    def _require_no_name_collision(
        *,
        entries: list[os.DirEntry[str]],
        extra_details: dict[str, object],
        message: str,
        names_key: str,
    ) -> tuple[str, ...]:
        """Require that entry names are distinct ignoring case.

        Parameters
        ----------
        entries
            Directory entries to check.
        extra_details
            Extra private diagnostics merged into a collision error alongside the
            offending names.
        message
            Safe public message for a case-insensitive name collision.
        names_key
            Diagnostics key under which the entry names are reported on a collision.

        Returns
        -------
        tuple[str, ...]
            The entry names in their original order.

        Raises
        ------
        PackageValidationError
            If two entry names differ only by case.
        """

        names = tuple(entry.name for entry in entries)

        if len(names) != len({name.casefold() for name in names}):
            raise _package_error(
                details={**extra_details, names_key: names}, message=message
            )

        return names

    @staticmethod
    def _require_safe_directory_entry(
        *, entry: os.DirEntry[str], inspection_message: str, unsafe_message: str
    ) -> None:
        """Require that a directory entry is a real, non-symlink subdirectory.

        Parameters
        ----------
        entry
            Directory entry selected beneath a trusted directory.
        inspection_message
            Safe public message if the entry cannot be inspected safely.
        unsafe_message
            Safe public message if the entry is a symlink or not a directory.

        Raises
        ------
        PackageValidationError
            If the entry cannot be inspected, is a symbolic link, or is not a directory.
        """

        entry_path = str(Path(entry.path))

        try:
            is_directory = entry.is_dir(follow_symlinks=False)
            is_symlink = entry.is_symlink()
        except OSError as error:
            raise _package_error(
                details={"entry_path": entry_path}, message=inspection_message
            ) from error

        if is_symlink or not is_directory:
            raise _package_error(
                details={"entry_path": entry_path}, message=unsafe_message
            )

    def _resolved_root(self) -> Path:
        """Resolve the configured graph-packages root as the trust boundary.

        Returns
        -------
        Path
            Existing canonical graph-packages directory.

        Raises
        ------
        PackageValidationError
            If the configured root is unavailable or is not a directory.
        """

        expanded_root = self.graph_packages_root.expanduser()

        try:
            resolved_root = expanded_root.resolve(strict=True)
        except OSError as error:
            raise _package_error(
                details={"graph_packages_root": str(expanded_root)},
                message="The configured graph-packages root is unavailable.",
            ) from error

        if not resolved_root.is_dir():
            raise _package_error(
                details={"graph_packages_root": str(resolved_root)},
                message="The configured graph-packages root is not a directory.",
            )

        return resolved_root

    def _snapshot_candidates_for_framework(
        self, *, framework_entry: os.DirEntry[str], root: Path
    ) -> list[GraphPackageCandidate]:
        """Resolve every safe snapshot candidate under one framework entry.

        Parameters
        ----------
        framework_entry
            Framework directory entry directly beneath the trust root.
        root
            Resolved graph-packages trust boundary.

        Returns
        -------
        list[GraphPackageCandidate]
            Name-ordered safe candidates for the framework entry.

        Raises
        ------
        PackageValidationError
            If the framework name or any snapshot entry is invalid or unsafe, or a
            directory cannot be enumerated.
        """

        try:
            _FRAMEWORK_ID_ADAPTER.validate_python(framework_entry.name)
        except ValidationError as error:
            raise _package_error(
                details={
                    "framework_entry": framework_entry.name,
                    "validation_errors": error.errors(
                        include_input=False, include_url=False
                    ),
                },
                message=(
                    "A graph-packages framework directory has an invalid "
                    "identifier name."
                ),
            ) from error

        self._require_safe_directory_entry(
            entry=framework_entry,
            inspection_message=(
                "A graph-packages framework entry could not be inspected safely."
            ),
            unsafe_message=(
                "The graph-packages root contains an unsafe framework entry."
            ),
        )

        framework_path = Path(framework_entry.path)
        snapshot_entries = self._sorted_directory_entries(
            directory=framework_path,
            enumeration_details={"framework_path": str(framework_path)},
            enumeration_message=(
                "A framework package directory could not be enumerated."
            ),
        )
        self._require_no_name_collision(
            entries=snapshot_entries,
            extra_details={"framework_entry": framework_entry.name},
            message=("Snapshot directories have a case-insensitive name collision."),
            names_key="snapshot_entries",
        )

        candidates: list[GraphPackageCandidate] = []

        for snapshot_entry in snapshot_entries:
            self._require_safe_directory_entry(
                entry=snapshot_entry,
                inspection_message=(
                    "A graph-package entry could not be inspected safely."
                ),
                unsafe_message=(
                    "A framework directory contains an unsafe package entry."
                ),
            )
            candidates.append(
                self._candidate_from_names(
                    framework_name=framework_entry.name,
                    root=root,
                    snapshot_name=snapshot_entry.name,
                )
            )

        return candidates

    @staticmethod
    def _sorted_directory_entries(
        *,
        directory: Path,
        enumeration_details: dict[str, object],
        enumeration_message: str,
    ) -> list[os.DirEntry[str]]:
        """Enumerate a directory into name-sorted entries.

        Parameters
        ----------
        directory
            Directory to enumerate as a filesystem trust member.
        enumeration_details
            Private diagnostics reported if enumeration fails.
        enumeration_message
            Safe public message reported if enumeration fails.

        Returns
        -------
        list[os.DirEntry[str]]
            Directory entries sorted by name.

        Raises
        ------
        PackageValidationError
            If the directory cannot be enumerated.
        """

        try:
            with os.scandir(directory) as iterator:
                return sorted(iterator, key=lambda entry: entry.name)
        except OSError as error:
            raise _package_error(
                details=enumeration_details, message=enumeration_message
            ) from error

    @staticmethod
    def _verify_manifest_contract(
        *,
        candidate: GraphPackageCandidate,
        manifest: GraphPackageManifest,
        target_status: ValidationStatus,
    ) -> None:
        """Verify the in-memory status, identity, and package contract.

        Parameters
        ----------
        candidate
            Safely discovered package candidate.
        manifest
            Validated manifest originally loaded from the candidate.
        target_status
            Computed terminal status to persist.

        Raises
        ------
        PackageValidationError
            If the target status is not terminal, the identity disagrees, the revision
            or graph-type contract is unsupported, or the manifest is not pending.
        """

        if target_status not in _TERMINAL_STATUSES:
            raise _package_error(
                details={"target_status": target_status.value},
                message="Only a terminal validation status may be persisted.",
            )

        if (
            manifest.framework_id != candidate.framework_id
            or manifest.snapshot_id != candidate.snapshot_id
        ):
            raise _package_error(
                details={
                    "candidate_framework_id": str(candidate.framework_id),
                    "candidate_snapshot_id": str(candidate.snapshot_id),
                    "manifest_framework_id": str(manifest.framework_id),
                    "manifest_snapshot_id": str(manifest.snapshot_id),
                },
                message="The manifest identity disagrees with the discovered package.",
            )

        if manifest.package_revision != SUPPORTED_PACKAGE_REVISION:
            raise _package_error(
                details={
                    "package_reference": candidate.reference,
                    "package_revision": manifest.package_revision,
                },
                message="The package revision is unsupported by validation persistence.",
            )

        if (
            manifest.graph_type is not GraphType.ACADEMIC_STANDARDS
            or manifest.included_graph_types != (GraphType.ACADEMIC_STANDARDS,)
        ):
            raise _package_error(
                details={
                    "graph_type": manifest.graph_type.value,
                    "included_graph_types": tuple(
                        graph_type.value for graph_type in manifest.included_graph_types
                    ),
                    "package_reference": candidate.reference,
                },
                message="The package graph-type contract is unsupported by validation persistence.",
            )

        if manifest.validation.status is not ValidationStatus.PENDING:
            raise _package_error(
                details={
                    "current_status": manifest.validation.status.value,
                    "package_reference": candidate.reference,
                },
                message="Only a pending package may transition to a terminal status.",
            )

    def _verify_transition_preconditions(
        self,
        *,
        candidate: GraphPackageCandidate,
        manifest: GraphPackageManifest,
        manifest_bytes: bytes,
        target_status: ValidationStatus,
    ) -> Path:
        """Verify every precondition for a pending-to-terminal transition.

        Parameters
        ----------
        candidate
            Safely discovered package candidate.
        manifest
            Validated manifest originally loaded from the candidate.
        manifest_bytes
            Exact bytes observed when the manifest was loaded.
        target_status
            Computed terminal status to persist.

        Returns
        -------
        Path
            Freshly re-resolved manifest path proven safe to replace.

        Raises
        ------
        PackageValidationError
            If the transition is unsupported, the identity or contract disagrees, the
            manifest is not pending, its location became unsafe, or it changed since it
            was loaded.
        """

        self._verify_manifest_contract(
            candidate=candidate, manifest=manifest, target_status=target_status
        )

        current_candidate = self.candidate(
            framework_id=candidate.framework_id, snapshot_id=candidate.snapshot_id
        )

        if current_candidate.package_path != candidate.package_path:
            raise _package_error(
                details={"package_reference": candidate.reference},
                message="The package location changed during validation.",
            )

        manifest_path = current_candidate.manifest_path

        if manifest_path.is_symlink():
            raise _package_error(
                details={"manifest_path": str(manifest_path)},
                message="The package manifest may not be a symbolic link.",
            )

        try:
            current_bytes = _read_regular_file_without_following(manifest_path)
        except (OSError, ValueError) as error:
            raise _package_error(
                details={"manifest_path": str(manifest_path)},
                message="The package manifest could not be safely reread.",
            ) from error

        if current_bytes != manifest_bytes:
            raise _package_error(
                details={"package_reference": candidate.reference},
                message="The package manifest changed during validation.",
            )

        try:
            loaded_manifest = GraphPackageManifest.model_validate_json(manifest_bytes)
        except ValidationError as error:
            raise _package_error(
                details={
                    "package_reference": candidate.reference,
                    "validation_errors": error.errors(
                        include_input=False, include_url=False
                    ),
                },
                message="The originally loaded package manifest is no longer valid.",
            ) from error

        if loaded_manifest != manifest:
            raise _package_error(
                details={"package_reference": candidate.reference},
                message="The supplied manifest model does not match its originally loaded bytes.",
            )

        return manifest_path

    def candidate(
        self, *, framework_id: FrameworkId, snapshot_id: SnapshotId
    ) -> GraphPackageCandidate:
        """Resolve one requested package strictly beneath the configured root.

        Parameters
        ----------
        framework_id
            Requested stable framework identifier.
        snapshot_id
            Requested immutable snapshot identifier.

        Returns
        -------
        GraphPackageCandidate
            Safe existing package candidate.
        """

        return self._candidate_from_names(
            framework_name=str(framework_id),
            root=self._resolved_root(),
            snapshot_name=str(snapshot_id),
        )

    def discover(self) -> tuple[GraphPackageCandidate, ...]:
        """Discover every package in the established two-level directory layout.

        Returns
        -------
        tuple[GraphPackageCandidate, ...]
            Deterministically ordered safe package candidates.

        Raises
        ------
        PackageValidationError
            If discovery encounters a symlink, file, special entry, invalid identity,
            case-insensitive collision, or unreadable directory.
        """

        root = self._resolved_root()
        framework_entries = self._sorted_directory_entries(
            directory=root,
            enumeration_details={"graph_packages_root": str(root)},
            enumeration_message="The graph-packages root could not be enumerated.",
        )
        self._require_no_name_collision(
            entries=framework_entries,
            extra_details={},
            message=("Framework directories have a case-insensitive name collision."),
            names_key="framework_entries",
        )

        candidates: list[GraphPackageCandidate] = []

        for framework_entry in framework_entries:
            candidates.extend(
                self._snapshot_candidates_for_framework(
                    framework_entry=framework_entry, root=root
                )
            )

        return tuple(candidates)

    def persist_validation_transition(
        self,
        *,
        candidate: GraphPackageCandidate,
        manifest: GraphPackageManifest,
        manifest_bytes: bytes,
        target_status: ValidationStatus,
    ) -> PersistedManifestTransition:
        """Atomically transition one unchanged pending manifest to a terminal status.

        Parameters
        ----------
        candidate
            Safely discovered package candidate.
        manifest
            Validated manifest originally loaded from the candidate.
        manifest_bytes
            Exact bytes observed when the manifest was loaded.
        target_status
            Computed terminal status to persist.

        Returns
        -------
        PersistedManifestTransition
            Updated manifest, exact persisted bytes, and one-time validation timestamp.

        Raises
        ------
        PackageValidationError
            If the transition is unsupported, the manifest changed concurrently, its
            location became unsafe, or atomic persistence fails.
        """

        manifest_path = self._verify_transition_preconditions(
            candidate=candidate,
            manifest=manifest,
            manifest_bytes=manifest_bytes,
            target_status=target_status,
        )

        validated_at = datetime.now(timezone.utc).replace(microsecond=0)
        updated_manifest = self._build_terminal_manifest(
            candidate=candidate,
            manifest=manifest,
            target_status=target_status,
            validated_at=validated_at,
        )
        updated_bytes = _canonical_manifest_bytes(updated_manifest)

        self._atomically_replace_manifest(
            candidate=candidate,
            manifest_bytes=manifest_bytes,
            manifest_path=manifest_path,
            updated_bytes=updated_bytes,
        )

        return PersistedManifestTransition(
            manifest=updated_manifest,
            manifest_bytes=updated_bytes,
            validated_at=validated_at,
        )


@dataclass(frozen=True, slots=True)
class PersistedManifestTransition:
    """Return the exact result of one pending-to-terminal manifest transition."""

    manifest: GraphPackageManifest
    manifest_bytes: bytes
    validated_at: datetime


def _canonical_manifest_bytes(manifest: GraphPackageManifest) -> bytes:
    """Serialize a manifest exactly as the package builder serializes it.

    Parameters
    ----------
    manifest
        Validated graph-package manifest.

    Returns
    -------
    bytes
        Stable UTF-8, lower-camel-case, sorted, indented JSON ending in one LF.
    """

    payload = manifest.model_dump(by_alias=True, mode="json")
    serialized = json.dumps(ensure_ascii=False, indent=2, obj=payload, sort_keys=True)
    return f"{serialized}\n".encode("utf-8")


def _package_error(
    *, details: dict[str, object], message: str
) -> PackageValidationError:
    """Build a typed package error with separated private diagnostics.

    Parameters
    ----------
    details
        Internal diagnostics that may include local paths.
    message
        Safe public error message.

    Returns
    -------
    PackageValidationError
        Typed error ready to raise.
    """

    return PackageValidationError(details=details, message=message)


def _read_regular_file_without_following(path: Path) -> bytes:
    """Read exact bytes from a regular file without following a final symlink.

    Parameters
    ----------
    path
        Existing file selected beneath a trusted package root.

    Returns
    -------
    bytes
        Exact file bytes.

    Raises
    ------
    OSError
        If the path cannot be opened or read.
    ValueError
        If the final filesystem entry is not a regular file.
    """

    flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
    descriptor = os.open(flags=flags, path=path)

    try:
        file_stat = os.fstat(descriptor)

        if not stat.S_ISREG(file_stat.st_mode):
            raise ValueError("The selected manifest is not a regular file.")

        chunks: list[bytes] = []

        while chunk := os.read(descriptor, 1024 * 1024):
            chunks.append(chunk)

        return b"".join(chunks)
    finally:
        os.close(descriptor)
