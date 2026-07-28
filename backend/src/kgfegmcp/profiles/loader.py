"""This module resolves and validates exact versioned curriculum profiles beneath a
trust root.
"""

# Standard Library
from dataclasses import dataclass
from pathlib import Path
from typing import NoReturn

# Third Party Library
from pydantic import ValidationError
from pydantic_core import ErrorDetails

# Package Library
from kgfegmcp.domain.identifiers import ProfileId, ProfileVersion, Sha256Digest
from kgfegmcp.errors import ProfileValidationError
from kgfegmcp.packages.checksums import calculate_bytes_sha256
from kgfegmcp.profiles.models import CurriculumProfile


@dataclass(frozen=True, slots=True)
class LoadedProfile:
    """Associate a validated profile with its exact bytes, path, and checksum."""

    bytes_: bytes
    path: Path
    profile: CurriculumProfile
    sha256: Sha256Digest


def _raise_profile_error(
    *,
    message: str,
    profile_id: ProfileId,
    profile_path: Path,
    profile_version: ProfileVersion,
    validation_errors: list[ErrorDetails] | None = None,
) -> NoReturn:
    """Raise a typed profile error with safe public and internal path context.

    Parameters
    ----------
    message
        Public error text that does not expose an arbitrary local path.
    profile_id
        Requested profile identifier.
    profile_path
        Internal path retained only for diagnostics.
    profile_version
        Requested profile version.
    validation_errors
        Optional structured Pydantic validation errors.

    Raises
    ------
    ProfileValidationError
        Always raised with the supplied diagnostic context.
    """

    details: dict[str, object] = {
        "profile_id": str(profile_id),
        "profile_path": str(profile_path),
        "profile_version": str(profile_version),
    }

    if validation_errors is not None:
        details["validation_errors"] = validation_errors

    raise ProfileValidationError(details=details, message=message)


def _read_and_validate_profile(
    *, profile_id: ProfileId, profile_version: ProfileVersion, resolved_path: Path
) -> tuple[bytes, CurriculumProfile]:
    """Read the profile document and validate it against the profile model.

    Parameters
    ----------
    profile_id
        Requested operator-controlled profile identifier.
    profile_version
        Requested immutable profile version.
    resolved_path
        Canonical profile-document path beneath the trust boundary.

    Returns
    -------
    tuple[bytes, CurriculumProfile]
        Exact document bytes and the validated profile parsed from them.

    Raises
    ------
    ProfileValidationError
        If the document is unreadable, invalid, or uses an unsupported schema version.
    """

    try:
        profile_bytes = resolved_path.read_bytes()
    except OSError as error:
        raise ProfileValidationError(
            details={
                "profile_id": str(profile_id),
                "profile_path": str(resolved_path),
                "profile_version": str(profile_version),
            },
            message=f"Profile '{profile_id}' version '{profile_version}' is unreadable.",
        ) from error

    try:
        profile = CurriculumProfile.model_validate_json(profile_bytes)
    except ValidationError as error:
        validation_errors = error.errors(include_input=False, include_url=False)
        error_fields = {
            str(validation_error["loc"][0])
            for validation_error in validation_errors
            if validation_error.get("loc")
        }
        message = f"Profile '{profile_id}' version '{profile_version}' is invalid."

        if {"profileSchemaVersion", "profile_schema_version"}.intersection(
            error_fields
        ):
            message = (
                f"Profile '{profile_id}' version '{profile_version}' uses an "
                f"unsupported profile schema version."
            )

        _raise_profile_error(
            message=message,
            profile_id=profile_id,
            profile_path=resolved_path,
            profile_version=profile_version,
            validation_errors=validation_errors,
        )

    return profile_bytes, profile


def _resolve_profile_document_path(
    *,
    profile_id: ProfileId,
    profile_version: ProfileVersion,
    requested_path: Path,
    resolved_root: Path,
) -> Path:
    """Canonicalize the profile document and confirm it stays beneath the root.

    Parameters
    ----------
    profile_id
        Requested operator-controlled profile identifier.
    profile_version
        Requested immutable profile version.
    requested_path
        Candidate ``profile.json`` path already confirmed to be a real file.
    resolved_root
        Canonical profile-root directory acting as the trust boundary.

    Returns
    -------
    Path
        Canonical profile-document path guaranteed to be beneath the root.

    Raises
    ------
    ProfileValidationError
        If the document is unreadable or resolves outside the profile root.
    """

    try:
        resolved_path = requested_path.resolve(strict=True)
    except OSError as error:
        raise ProfileValidationError(
            details={
                "profile_id": str(profile_id),
                "profile_path": str(requested_path),
                "profile_version": str(profile_version),
            },
            message=f"Profile '{profile_id}' version '{profile_version}' is unreadable.",
        ) from error

    if not resolved_path.is_relative_to(resolved_root):
        _raise_profile_error(
            message=(
                f"Profile '{profile_id}' version '{profile_version}' does not resolve "
                f"safely beneath the configured profile root."
            ),
            profile_id=profile_id,
            profile_path=requested_path,
            profile_version=profile_version,
        )

    return resolved_path


def _resolve_profile_root(profile_root: Path) -> Path:
    """Resolve the configured profile root as the filesystem trust boundary.

    Parameters
    ----------
    profile_root
        Configured central profile repository root.

    Returns
    -------
    Path
        Existing canonical profile-root directory.

    Raises
    ------
    ProfileValidationError
        If the configured root is missing, unreadable, or not a directory.
    """

    expanded_root = profile_root.expanduser()

    try:
        resolved_root = expanded_root.resolve(strict=True)
    except OSError as error:
        raise ProfileValidationError(
            details={"profile_root": str(expanded_root)},
            message="The configured curriculum-profile root is unavailable.",
        ) from error

    if not resolved_root.is_dir():
        raise ProfileValidationError(
            details={"profile_root": str(resolved_root)},
            message="The configured curriculum-profile root is not a directory.",
        )

    return resolved_root


def _verify_declared_profile_identity(
    *,
    profile: CurriculumProfile,
    profile_id: ProfileId,
    profile_version: ProfileVersion,
    resolved_path: Path,
) -> None:
    """Confirm the document's declared identity matches the requested identity.

    Parameters
    ----------
    profile
        Validated profile parsed from the document.
    profile_id
        Requested operator-controlled profile identifier.
    profile_version
        Requested immutable profile version.
    resolved_path
        Canonical profile-document path, retained only for diagnostics.

    Raises
    ------
    ProfileValidationError
        If the declared profile ID or version differs from the requested identity.
    """

    if profile.profile_id != profile_id or profile.profile_version != profile_version:
        raise ProfileValidationError(
            details={
                "declared_profile_id": str(profile.profile_id),
                "declared_profile_version": str(profile.profile_version),
                "profile_id": str(profile_id),
                "profile_path": str(resolved_path),
                "profile_version": str(profile_version),
            },
            message=(
                f"Profile '{profile_id}' version '{profile_version}' declares a "
                f"different profile identity."
            ),
        )


def _verify_profile_component_paths(
    *,
    profile_id: ProfileId,
    profile_id_directory: Path,
    profile_version: ProfileVersion,
    profile_version_directory: Path,
    requested_path: Path,
) -> None:
    """Reject symbolic links and confirm the selected components really exist.

    Each descendant component selected by the profile identity is checked without
    following symbolic links: none may be a symlink, both directories must be real
    directories, and ``profile.json`` must be a real file.

    Parameters
    ----------
    profile_id
        Requested operator-controlled profile identifier.
    profile_id_directory
        Candidate profile-ID directory beneath the resolved root.
    profile_version
        Requested immutable profile version.
    profile_version_directory
        Candidate profile-version directory beneath the profile-ID directory.
    requested_path
        Candidate ``profile.json`` path beneath the profile-version directory.

    Raises
    ------
    ProfileValidationError
        If any component is a symbolic link or the profile is not found.
    """

    for component_path, component_role in (
        (profile_id_directory, "profile-ID directory"),
        (profile_version_directory, "profile-version directory"),
        (requested_path, "profile document"),
    ):
        if component_path.is_symlink():
            _raise_profile_error(
                message=(
                    f"Profile '{profile_id}' version '{profile_version}' uses a "
                    f"symbolic link for its {component_role}."
                ),
                profile_id=profile_id,
                profile_path=component_path,
                profile_version=profile_version,
            )

    if not profile_id_directory.is_dir() or not profile_version_directory.is_dir():
        _raise_profile_error(
            message=f"Profile '{profile_id}' version '{profile_version}' was not found.",
            profile_id=profile_id,
            profile_path=requested_path,
            profile_version=profile_version,
        )

    if not requested_path.is_file():
        _raise_profile_error(
            message=f"Profile '{profile_id}' version '{profile_version}' was not found.",
            profile_id=profile_id,
            profile_path=requested_path,
            profile_version=profile_version,
        )


def load_curriculum_profile(
    *, profile_id: ProfileId, profile_root: Path, profile_version: ProfileVersion
) -> LoadedProfile:
    """Resolve and validate one profile beneath the configured profile root.

    The configured root is first resolved as the trust boundary. Every descendant
    component selected by the profile identity is then checked without following
    symbolic links: the profile-ID directory, profile-version directory, and
    ``profile.json`` must all be real filesystem entries beneath that boundary.

    Parameters
    ----------
    profile_id
        Requested operator-controlled profile identifier.
    profile_root
        Configured central profile repository root.
    profile_version
        Requested immutable profile version.

    Returns
    -------
    LoadedProfile
        Validated profile, exact bytes, source path, and exact-byte checksum.

    Raises
    ------
    ProfileValidationError
        If the profile is missing, unsafe, unreadable, invalid, or has a mismatched
        declared identity.
    """

    resolved_root = _resolve_profile_root(profile_root)
    profile_id_directory = resolved_root / str(profile_id)
    profile_version_directory = profile_id_directory / str(profile_version)
    requested_path = profile_version_directory / "profile.json"

    _verify_profile_component_paths(
        profile_id=profile_id,
        profile_id_directory=profile_id_directory,
        profile_version=profile_version,
        profile_version_directory=profile_version_directory,
        requested_path=requested_path,
    )

    resolved_path = _resolve_profile_document_path(
        profile_id=profile_id,
        profile_version=profile_version,
        requested_path=requested_path,
        resolved_root=resolved_root,
    )

    profile_bytes, profile = _read_and_validate_profile(
        profile_id=profile_id,
        profile_version=profile_version,
        resolved_path=resolved_path,
    )

    _verify_declared_profile_identity(
        profile=profile,
        profile_id=profile_id,
        profile_version=profile_version,
        resolved_path=resolved_path,
    )

    return LoadedProfile(
        bytes_=profile_bytes,
        path=resolved_path,
        profile=profile,
        sha256=calculate_bytes_sha256(profile_bytes),
    )
