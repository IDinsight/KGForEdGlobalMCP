"""This module contains environment-backed application settings and repository path
resolution.
"""

# Standard Library
import os

from pathlib import Path
from typing import Literal, Self

# Third Party Library
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Package Library
from kgfegmcp.domain.enums import InvalidPackagePolicy

LogLevel = Literal["CRITICAL", "DEBUG", "ERROR", "INFO", "WARNING"]
RuntimeEnvironment = Literal["dev", "local", "prod", "testing"]


def _default_project_dir() -> Path:
    """Resolve the repository root from the installed source layout.

    Returns
    -------
    Path
        Repository root containing ``backend``, ``config``, ``data``, etc.
    """

    return Path(__file__).resolve().parents[3]


def _resolve_project_path(
    *, configured_path: Path | None, default_relative_path: Path, project_dir: Path
) -> Path:
    """Resolve an optional configured path against the project root.

    Parameters
    ----------
    configured_path
        Explicit absolute path or project-relative override.
    default_relative_path
        Project-relative path used when no override is configured.
    project_dir
        Absolute repository root.

    Returns
    -------
    Path
        Canonical absolute path.
    """

    candidate = configured_path or default_relative_path

    if not candidate.is_absolute():
        candidate = project_dir / candidate

    return candidate.expanduser().resolve(strict=False)


class BackendSettings(BaseSettings):
    """Validated settings for catalog, profile, data, and runtime paths."""

    cache_root_override: Path | None = Field(
        default=None, validation_alias="KGFEGMCP_CACHE_ROOT"
    )
    catalog_path_override: Path | None = Field(
        default=None, validation_alias="KGFEGMCP_CATALOG"
    )
    config_root_override: Path | None = Field(
        default=None, validation_alias="KGFEGMCP_CONFIG_ROOT"
    )
    data_root_override: Path | None = Field(
        default=None, validation_alias="KGFEGMCP_DATA_ROOT"
    )
    environment: RuntimeEnvironment = Field(
        default="local", validation_alias="KGFEGMCP_ENV"
    )
    invalid_package_policy: InvalidPackagePolicy = Field(
        default=InvalidPackagePolicy.FAIL,
        validation_alias="KGFEGMCP_INVALID_PACKAGE_POLICY",
    )
    log_level: LogLevel = Field(default="INFO", validation_alias="KGFEGMCP_LOG_LEVEL")
    log_root_override: Path | None = Field(
        default=None, validation_alias="KGFEGMCP_LOG_ROOT"
    )
    profile_root_override: Path | None = Field(
        default=None, validation_alias="KGFEGMCP_PROFILE_ROOT"
    )
    project_dir: Path = Field(
        default_factory=_default_project_dir, validation_alias="PATHS_PROJECT_DIR"
    )
    results_root_override: Path | None = Field(
        default=None, validation_alias="KGFEGMCP_RESULTS_ROOT"
    )
    server_config_path_override: Path | None = Field(
        default=None, validation_alias="KGFEGMCP_CONFIG"
    )

    model_config = SettingsConfigDict(
        case_sensitive=True,
        env_file_encoding="utf-8",
        env_ignore_empty=True,
        extra="ignore",
        frozen=True,
        populate_by_name=True,
        validate_default=True,
    )

    @field_validator(
        "cache_root_override",
        "catalog_path_override",
        "config_root_override",
        "data_root_override",
        "log_root_override",
        "profile_root_override",
        "project_dir",
        "results_root_override",
        "server_config_path_override",
        mode="before",
    )
    @classmethod
    def expand_user_paths(cls, value: object) -> object:
        """Expand user-home markers before Pydantic converts values to paths.

        Parameters
        ----------
        value
            Environment or constructor value supplied for a path field.

        Returns
        -------
        object
            Expanded path string, original non-path value, or ``None``.
        """

        if isinstance(value, (Path, str)):
            return str(Path(value).expanduser())

        return value

    @field_validator("project_dir")
    @classmethod
    def require_absolute_project_dir(cls, value: Path) -> Path:
        """Validate and canonicalize the configured project root.

        Parameters
        ----------
        value
            Expanded project-root path.

        Returns
        -------
        Path
            Canonical absolute project-root path.

        Raises
        ------
        ValueError
            If the project root is relative.
        """

        if not value.is_absolute():
            raise ValueError("project_dir must be an absolute path.")

        return value.resolve(strict=False)

    @property
    def cache_root(self) -> Path:
        """Return the repository cache directory.

        Returns
        -------
        Path
            The resolved repository cache directory.
        """

        return _resolve_project_path(
            configured_path=self.cache_root_override,
            default_relative_path=Path("caches"),
            project_dir=self.project_dir,
        )

    @property
    def catalog_path(self) -> Path:
        """Return the catalog configuration path.

        Returns
        -------
        Path
            The resolved catalog configuration path.
        """

        return _resolve_project_path(
            configured_path=self.catalog_path_override,
            default_relative_path=Path("config/catalog.json"),
            project_dir=self.project_dir,
        )

    @property
    def config_root(self) -> Path:
        """Return the repository configuration root.

        Returns
        -------
        Path
            The resolved repository configuration root.
        """

        return _resolve_project_path(
            configured_path=self.config_root_override,
            default_relative_path=Path("config"),
            project_dir=self.project_dir,
        )

    @property
    def data_root(self) -> Path:
        """Return the repository data root.

        Returns
        -------
        Path
            The resolved repository data root.
        """

        return _resolve_project_path(
            configured_path=self.data_root_override,
            default_relative_path=Path("data"),
            project_dir=self.project_dir,
        )

    @property
    def derived_root(self) -> Path:
        """Return the derived-overlay data root.

        Returns
        -------
        Path
            The resolved derived-overlay data root.
        """

        return self.data_root / "derived"

    @classmethod
    def from_env_file(cls, env_file: Path) -> Self:
        """Load settings from an explicit environment file.

        Parameters
        ----------
        env_file
            Path to the environment file.

        Returns
        -------
        Self
            Validated backend settings.
        """

        return cls(_env_file=env_file.expanduser().resolve(strict=False))

    @property
    def graph_packages_root(self) -> Path:
        """Return the immutable graph-package data root.

        Returns
        -------
        Path
            The resolved immutable graph-package data root.
        """

        return self.data_root / "graph_packages"

    @property
    def log_root(self) -> Path:
        """Return the repository log directory.

        Returns
        -------
        Path
            The resolved repository log directory.
        """

        return _resolve_project_path(
            configured_path=self.log_root_override,
            default_relative_path=Path("logs"),
            project_dir=self.project_dir,
        )

    @property
    def profile_root(self) -> Path:
        """Return the central versioned curriculum-profile root.

        Returns
        -------
        Path
            The resolved central versioned curriculum-profile root.
        """

        return _resolve_project_path(
            configured_path=self.profile_root_override,
            default_relative_path=Path("config/profiles"),
            project_dir=self.project_dir,
        )

    @property
    def results_root(self) -> Path:
        """Return the repository result directory.

        Returns
        -------
        Path
            The resolved repository result directory.
        """

        return _resolve_project_path(
            configured_path=self.results_root_override,
            default_relative_path=Path("results"),
            project_dir=self.project_dir,
        )

    @property
    def server_config_path(self) -> Path:
        """Return the server configuration path.

        Returns
        -------
        Path
            The resolved server configuration path.
        """

        return _resolve_project_path(
            configured_path=self.server_config_path_override,
            default_relative_path=Path("config/server.json"),
            project_dir=self.project_dir,
        )


def load_settings(env_file: Path | None = None) -> BackendSettings:
    """Load settings without import-time configuration side effects.

    Parameters
    ----------
    env_file
        Optional explicit environment-file path. When omitted, the loader checks the
        project root from ``PATHS_PROJECT_DIR`` and then the source-layout default.

    Returns
    -------
    BackendSettings
        Validated immutable application settings.
    """

    if env_file is not None:
        return BackendSettings.from_env_file(env_file)

    project_dir_value = os.getenv("PATHS_PROJECT_DIR")
    project_dir = (
        Path(project_dir_value).expanduser().resolve(strict=False)
        if project_dir_value
        else _default_project_dir()
    )
    default_env_file = project_dir / ".env"

    if default_env_file.is_file():
        return BackendSettings.from_env_file(default_env_file)

    return BackendSettings()
