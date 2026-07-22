"""This module contains functionalities for resolving and validating versioned
curriculum profiles beneath the configured root.
"""

# Standard Library
from dataclasses import dataclass
from pathlib import Path

# Third Party Library
from pydantic import ValidationError

# Package Library
from kgfegmcp.domain.identifiers import ProfileId, ProfileVersion, Sha256Digest
from kgfegmcp.errors import ProfileValidationError
from kgfegmcp.packages.checksums import calculate_bytes_sha256
from kgfegmcp.profiles.models import CurriculumProfile


@dataclass(frozen=True, slots=True)
class LoadedProfile:
    """Associate a validated profile with its exact bytes and checksum."""

    bytes_: bytes
    path: Path
    profile: CurriculumProfile
    sha256: Sha256Digest


def load_curriculum_profile(
    *, profile_id: ProfileId, profile_root: Path, profile_version: ProfileVersion
) -> LoadedProfile:
    """Resolve and validate one profile beneath the configured profile root.

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

    resolved_root = profile_root.expanduser().resolve(strict=False)
    requested_path = (
        resolved_root / str(profile_id) / str(profile_version) / "profile.json"
    )
    resolved_path = requested_path.resolve(strict=False)

    if not resolved_path.is_relative_to(resolved_root) or requested_path.is_symlink():
        raise ProfileValidationError(
            details={
                "profile_id": str(profile_id),
                "profile_path": str(requested_path),
                "profile_version": str(profile_version),
            },
            message=(
                f"Profile '{profile_id}' version '{profile_version}' does not resolve "
                f"safely beneath the configured profile root."
            ),
        )

    if not resolved_path.is_file():
        raise ProfileValidationError(
            details={
                "profile_id": str(profile_id),
                "profile_path": str(resolved_path),
                "profile_version": str(profile_version),
            },
            message=(
                f"Profile '{profile_id}' version '{profile_version}' was not found."
            ),
        )

    try:
        profile_bytes = resolved_path.read_bytes()
    except OSError as error:
        raise ProfileValidationError(
            details={
                "profile_id": str(profile_id),
                "profile_path": str(resolved_path),
                "profile_version": str(profile_version),
            },
            message=(
                f"Profile '{profile_id}' version '{profile_version}' is unreadable."
            ),
        ) from error

    try:
        profile = CurriculumProfile.model_validate_json(profile_bytes)
    except ValidationError as error:
        raise ProfileValidationError(
            details={
                "profile_id": str(profile_id),
                "profile_path": str(resolved_path),
                "profile_version": str(profile_version),
                "validation_errors": error.errors(
                    include_input=False, include_url=False
                ),
            },
            message=f"Profile '{profile_id}' version '{profile_version}' is invalid.",
        ) from error

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

    return LoadedProfile(
        bytes_=profile_bytes,
        path=resolved_path,
        profile=profile,
        sha256=calculate_bytes_sha256(profile_bytes),
    )
