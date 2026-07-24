"""This module loads optional framework-local prompt configuration during application
bootstrap.

``PromptConfigRepository`` resolves only the exact ``prompts.json`` path derived from
each accepted curriculum profile identifier and version. A missing file is valid and
means that the generic server-level prompt defaults apply. A present file is bounded,
read safely, checksumed, strictly validated, and required to declare framework and
profile identities that match the accepted runtime package.

The loader enforces the configured prompt-root trust boundary, rejects unsafe symbolic
links and path escapes, and does not perform directory scanning or automatic prompt
discovery.

This module does not mutate graph packages, search standards, traverse graphs, merge
prompt guidance, render prompt text, register FastMCP components, call an LLM, or use
MCP sampling.
"""

# Future Library
from __future__ import annotations

# Standard Library
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path

# Third Party Library
from pydantic import ValidationError

# Package Library
from kgfegmcp.catalog.models import CatalogLoadResult
from kgfegmcp.domain.identifiers import ProfileId, ProfileVersion
from kgfegmcp.errors import PromptConfigurationError
from kgfegmcp.packages.checksums import calculate_bytes_sha256
from kgfegmcp.profiles.models import CurriculumProfile
from kgfegmcp.prompts.models import (
    MAX_PROMPT_CONFIG_BYTES,
    FrameworkPromptConfig,
    LoadedPromptConfig,
    PromptConfigRegistry,
)


def _configuration_error(
    *,
    message: str,
    path: Path,
    validation_errors: Sequence[Mapping[str, object]] | None = None,
) -> PromptConfigurationError:
    """Build one stable prompt-configuration error with internal diagnostics.

    Parameters
    ----------
    message
        Public actionable error message.
    path
        Configuration path retained only in internal error details.
    validation_errors
        Optional structured Pydantic validation details.

    Returns
    -------
    PromptConfigurationError
        Typed domain error ready to be raised by the caller.
    """

    details: dict[str, object] = {"prompt_config_path": str(path)}

    if validation_errors is not None:
        details["validation_errors"] = validation_errors

    return PromptConfigurationError(details=details, message=message)


def _read_bounded_bytes(
    *, max_file_bytes: int, profile: CurriculumProfile, resolved_path: Path
) -> bytes:
    """Read one prompt configuration while enforcing the exact-byte size limit.

    The reported size is checked before reading and the materialized bytes are checked
    afterwards, so a file that grows between the two calls is still rejected rather
    than read past the configured bound.

    Parameters
    ----------
    max_file_bytes
        Maximum exact byte length accepted for one configuration document.
    profile
        Exact accepted profile that selected the configuration.
    resolved_path
        Canonical configuration path contained by the prompt root.

    Returns
    -------
    bytes
        Exact configuration bytes bounded by the configured size limit.

    Raises
    ------
    PromptConfigurationError
        If the file is unreadable or exceeds the configured size limit.
    """

    try:
        stat_result = resolved_path.stat()
    except OSError as error:
        raise _configuration_error(
            message=(
                f"Prompt configuration for profile '{profile.profile_id}' version "
                f"'{profile.profile_version}' is unreadable."
            ),
            path=resolved_path,
        ) from error

    if stat_result.st_size > max_file_bytes:
        raise _configuration_error(
            message=(
                f"Prompt configuration for profile '{profile.profile_id}' version "
                f"'{profile.profile_version}' exceeds the configured size limit."
            ),
            path=resolved_path,
        )

    try:
        config_bytes = resolved_path.read_bytes()
    except OSError as error:
        raise _configuration_error(
            message=(
                f"Prompt configuration for profile '{profile.profile_id}' version "
                f"'{profile.profile_version}' is unreadable."
            ),
            path=resolved_path,
        ) from error

    if len(config_bytes) > max_file_bytes:
        raise _configuration_error(
            message=(
                f"Prompt configuration for profile '{profile.profile_id}' version "
                f"'{profile.profile_version}' exceeds the configured size limit."
            ),
            path=resolved_path,
        )

    return config_bytes


def _read_configuration(
    *,
    max_file_bytes: int,
    profile: CurriculumProfile,
    requested_path: Path,
    resolved_root: Path,
) -> LoadedPromptConfig:
    """Read, validate, checksum, and identity-check one prompt configuration.

    Parameters
    ----------
    max_file_bytes
        Maximum exact byte length accepted for one configuration document.
    profile
        Exact accepted profile that selected the configuration.
    requested_path
        Existing non-symlink ``prompts.json`` path.
    resolved_root
        Canonical prompt-root trust boundary.

    Returns
    -------
    LoadedPromptConfig
        Validated configuration and exact-byte checksum evidence.

    Raises
    ------
    PromptConfigurationError
        If path containment, size, JSON schema, or identity checks fail.
    """

    resolved_path = _resolve_within_root(
        profile=profile, requested_path=requested_path, resolved_root=resolved_root
    )
    config_bytes = _read_bounded_bytes(
        max_file_bytes=max_file_bytes, profile=profile, resolved_path=resolved_path
    )

    try:
        config = FrameworkPromptConfig.model_validate_json(config_bytes)
    except ValidationError as error:
        raise _configuration_error(
            message=(
                f"Prompt configuration for profile '{profile.profile_id}' version "
                f"'{profile.profile_version}' is invalid."
            ),
            path=resolved_path,
            validation_errors=error.errors(include_input=False, include_url=False),
        ) from error

    _verify_declared_identity(config=config, profile=profile, source_path=resolved_path)

    return LoadedPromptConfig(
        config=config,
        sha256=calculate_bytes_sha256(config_bytes),
        source_path=resolved_path,
    )


def _resolve_optional_root(prompt_root: Path) -> Path | None:
    """Resolve the optional prompt root as a filesystem trust boundary.

    Parameters
    ----------
    prompt_root
        Configured root for versioned framework-local prompt configuration.

    Returns
    -------
    Path | None
        Existing canonical directory, or ``None`` when no root was provided.

    Raises
    ------
    PromptConfigurationError
        If a present root is a symbolic link, unreadable, or not a directory.
    """

    expanded_root = prompt_root.expanduser()

    if not expanded_root.exists():
        return None

    if expanded_root.is_symlink():
        raise _configuration_error(
            message="The configured prompt root may not be a symbolic link.",
            path=expanded_root,
        )

    try:
        resolved_root = expanded_root.resolve(strict=True)
    except OSError as error:
        raise _configuration_error(
            message="The configured prompt root is unavailable.", path=expanded_root
        ) from error

    if not resolved_root.is_dir():
        raise _configuration_error(
            message="The configured prompt root is not a directory.", path=resolved_root
        )

    return resolved_root


def _resolve_within_root(
    *, profile: CurriculumProfile, requested_path: Path, resolved_root: Path
) -> Path:
    """Resolve one prompt path and confirm it stays beneath the prompt root.

    Parameters
    ----------
    profile
        Exact accepted profile that selected the configuration.
    requested_path
        Existing non-symlink ``prompts.json`` path.
    resolved_root
        Canonical prompt-root trust boundary.

    Returns
    -------
    Path
        Canonical configuration path contained by the prompt root.

    Raises
    ------
    PromptConfigurationError
        If the path is unreadable or resolves outside the prompt root.
    """

    try:
        resolved_path = requested_path.resolve(strict=True)
    except OSError as error:
        raise _configuration_error(
            message=(
                f"Prompt configuration for profile '{profile.profile_id}' version "
                f"'{profile.profile_version}' is unreadable."
            ),
            path=requested_path,
        ) from error

    if not resolved_path.is_relative_to(resolved_root):
        raise _configuration_error(
            message=(
                f"Prompt configuration for profile '{profile.profile_id}' version "
                f"'{profile.profile_version}' does not resolve safely beneath the "
                f"configured prompt root."
            ),
            path=resolved_path,
        )

    return resolved_path


def _verify_declared_identity(
    *, config: FrameworkPromptConfig, profile: CurriculumProfile, source_path: Path
) -> None:
    """Confirm a configuration declares the accepted profile and framework identities.

    Parameters
    ----------
    config
        Parsed configuration whose declared identities are checked.
    profile
        Exact accepted profile that selected the configuration.
    source_path
        Canonical configuration path retained only in internal error details.

    Raises
    ------
    PromptConfigurationError
        If the declared profile or framework identities differ from the profile.
    """

    if (
        config.profile_id != profile.profile_id
        or config.profile_version != profile.profile_version
    ):
        raise _configuration_error(
            message=(
                f"Prompt configuration for profile '{profile.profile_id}' version "
                f"'{profile.profile_version}' declares a different profile identity."
            ),
            path=source_path,
        )

    if config.framework_ids != profile.framework_ids:
        raise _configuration_error(
            message=(
                f"Prompt configuration for profile '{profile.profile_id}' version "
                f"'{profile.profile_version}' declares different framework identities."
            ),
            path=source_path,
        )


def _verify_optional_components(
    *,
    profile_id: ProfileId,
    profile_id_directory: Path,
    profile_version: ProfileVersion,
    profile_version_directory: Path,
    requested_path: Path,
) -> bool:
    """Validate exact descendant components and report whether the file exists.

    Parameters
    ----------
    profile_id
        Exact accepted profile identifier used to derive the path.
    profile_id_directory
        Candidate profile-ID directory beneath the prompt root.
    profile_version
        Exact accepted profile version used to derive the path.
    profile_version_directory
        Candidate profile-version directory beneath the profile-ID directory.
    requested_path
        Candidate ``prompts.json`` path.

    Returns
    -------
    bool
        ``True`` when a real prompt file exists; otherwise ``False``.

    Raises
    ------
    PromptConfigurationError
        If a present component is a symbolic link or has the wrong filesystem type.
    """

    for component_path, component_role in (
        (profile_id_directory, "profile-ID directory"),
        (profile_version_directory, "profile-version directory"),
        (requested_path, "prompt configuration"),
    ):
        if component_path.is_symlink():
            raise _configuration_error(
                message=(
                    f"Prompt configuration for profile '{profile_id}' version "
                    f"'{profile_version}' uses a symbolic link for its "
                    f"{component_role}."
                ),
                path=component_path,
            )

    if profile_id_directory.exists() and not profile_id_directory.is_dir():
        raise _configuration_error(
            message=(
                f"Prompt configuration for profile '{profile_id}' version "
                f"'{profile_version}' has an invalid profile-ID directory."
            ),
            path=profile_id_directory,
        )

    if profile_version_directory.exists() and not profile_version_directory.is_dir():
        raise _configuration_error(
            message=(
                f"Prompt configuration for profile '{profile_id}' version "
                f"'{profile_version}' has an invalid profile-version directory."
            ),
            path=profile_version_directory,
        )

    if not requested_path.exists():
        return False

    if not requested_path.is_file():
        raise _configuration_error(
            message=(
                f"Prompt configuration for profile '{profile_id}' version "
                f"'{profile_version}' is not a file."
            ),
            path=requested_path,
        )

    return True


@dataclass(frozen=True, slots=True)
class PromptConfigRepository:
    """Load optional exact prompt configuration for accepted profile identities."""

    max_file_bytes: int = MAX_PROMPT_CONFIG_BYTES
    prompt_root: Path = Path("config/prompts")

    def __post_init__(self) -> None:
        """Validate the configured exact-byte file limit.

        Raises
        ------
        ValueError
            If the file-size limit is not positive.
        """

        if self.max_file_bytes < 1:
            raise ValueError("max_file_bytes must be positive.")

    def load_registry(
        self, catalog_load_result: CatalogLoadResult
    ) -> PromptConfigRegistry:
        """Load optional configurations for every distinct accepted profile.

        Parameters
        ----------
        catalog_load_result
            Complete accepted catalog whose exact retained profiles select paths.

        Returns
        -------
        PromptConfigRegistry
            Deterministically ordered loaded configurations; missing files are omitted.

        Raises
        ------
        PromptConfigurationError
            If a present root, path component, file, schema, or identity is invalid.
        """

        resolved_root = _resolve_optional_root(self.prompt_root)

        if resolved_root is None:
            return PromptConfigRegistry()

        profiles_by_identity: dict[tuple[str, str], CurriculumProfile] = {}

        for runtime in catalog_load_result.package_runtimes:
            profile = runtime.loaded_package.profile
            identity = (str(profile.profile_id), str(profile.profile_version))
            existing_profile = profiles_by_identity.get(identity)

            if existing_profile is not None and existing_profile != profile:
                raise PromptConfigurationError(
                    details={
                        "profile_id": str(profile.profile_id),
                        "profile_version": str(profile.profile_version),
                    },
                    message=(
                        "Accepted packages retain inconsistent profiles for one prompt "
                        "configuration identity."
                    ),
                )

            profiles_by_identity[identity] = profile

        loaded_configurations: list[LoadedPromptConfig] = []

        for identity in sorted(profiles_by_identity):
            profile = profiles_by_identity[identity]
            profile_id_directory = resolved_root / str(profile.profile_id)
            profile_version_directory = profile_id_directory / str(
                profile.profile_version
            )
            requested_path = profile_version_directory / "prompts.json"
            exists = _verify_optional_components(
                profile_id=profile.profile_id,
                profile_id_directory=profile_id_directory,
                profile_version=profile.profile_version,
                profile_version_directory=profile_version_directory,
                requested_path=requested_path,
            )

            if not exists:
                continue

            loaded_configurations.append(
                _read_configuration(
                    max_file_bytes=self.max_file_bytes,
                    profile=profile,
                    requested_path=requested_path,
                    resolved_root=resolved_root,
                )
            )

        return PromptConfigRegistry(configurations=tuple(loaded_configurations))
