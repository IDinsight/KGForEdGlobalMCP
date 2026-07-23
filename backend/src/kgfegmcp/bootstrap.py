"""This module constructs the immutable application state for one server lifespan.

This module is the composition root for the application's existing configuration,
profile, graph-package, validation, catalog, and search components. It creates those
dependencies in their approved order, builds the complete accepted catalog through the
existing validation gate, and constructs independent package-local search indexes from
that catalog result.

The resulting ``AppState`` retains the settings, catalog result, catalog service, and
search service that MCP components use during one server lifespan. Importing this
module defines the construction process but does not execute it or access runtime files.
"""

# Future Library
from __future__ import annotations

# Standard Library
import logging

from dataclasses import dataclass
from time import perf_counter

# Package Library
from kgfegmcp.catalog.models import CatalogLoadResult
from kgfegmcp.catalog.repository import CatalogRepository
from kgfegmcp.catalog.service import CatalogService
from kgfegmcp.config import BackendSettings
from kgfegmcp.packages.loader import GraphPackageLoader
from kgfegmcp.packages.repository import GraphPackageRepository
from kgfegmcp.packages.validator import GraphPackageValidator
from kgfegmcp.profiles.repository import ProfileRepository
from kgfegmcp.search.service import SearchService

_LOGGER = logging.getLogger("fastmcp.kgfegmcp.bootstrap")


@dataclass(frozen=True, slots=True)
class AppState:
    """Retain one complete accepted catalog and its package-scoped services.

    Attributes
    ----------
    catalog_load_result
        Complete all-or-nothing catalog result and read-only validation evidence.
    catalog_service
        Exact and unique-current in-memory catalog routing service.
    search_service
        Deterministic search service with independent package-local indexes.
    settings
        Immutable settings used to construct this application state.
    """

    catalog_load_result: CatalogLoadResult
    catalog_service: CatalogService
    search_service: SearchService
    settings: BackendSettings

    def __post_init__(self) -> None:
        """Require catalog and search services to share the retained load result.

        Raises
        ------
        ValueError
            If the application state mixes independently constructed catalog objects.
        """

        if self.catalog_service is not self.search_service.catalog_service:
            raise ValueError(
                "AppState must retain the CatalogService owned by SearchService."
            )

        if self.catalog_service.load_result is not self.catalog_load_result:
            raise ValueError(
                "AppState services must share the retained CatalogLoadResult."
            )


def bootstrap_application() -> AppState:
    """Construct one immutable application state from the process environment.

    Settings are instantiated exactly once for this application lifespan. Catalog
    construction retains the existing package validation gate, and search construction
    begins only from the complete accepted catalog result.

    Returns
    -------
    AppState
        Complete immutable state for one FastMCP lifespan.

    Raises
    ------
    Exception
        Re-raises any settings, repository, validation, catalog, graph-store, or search
        construction failure after recording an internal startup diagnostic.
    """

    started_at = perf_counter()

    try:
        settings = BackendSettings()
        profile_repository = ProfileRepository(profile_root=settings.profile_root)
        package_repository = GraphPackageRepository(
            graph_packages_root=settings.graph_packages_root
        )
        package_loader = GraphPackageLoader(
            profile_repository=profile_repository, repository=package_repository
        )
        package_validator = GraphPackageValidator(
            loader=package_loader, repository=package_repository
        )
        catalog_repository = CatalogRepository(
            invalid_package_policy=settings.invalid_package_policy,
            package_repository=package_repository,
            validator=package_validator,
        )
        catalog_load_result = catalog_repository.load()
        search_service = SearchService.from_catalog_load_result(catalog_load_result)
        state = AppState(
            catalog_load_result=catalog_load_result,
            catalog_service=search_service.catalog_service,
            search_service=search_service,
            settings=settings,
        )
    except Exception:
        _LOGGER.exception(
            msg=(
                "Application state construction failed: operation=application_bootstrap."
            )
        )
        raise

    accepted_package_count = len(state.catalog_load_result.package_runtimes)
    elapsed_milliseconds = round((perf_counter() - started_at) * 1_000)
    _LOGGER.info(
        msg=(
            f"Application state construction completed: "
            f"accepted_package_count={accepted_package_count}, "
            f"discovered_package_count="
            f"{state.catalog_load_result.discovered_package_count}, "
            f"elapsed_milliseconds={elapsed_milliseconds}, "
            f"excluded_package_count="
            f"{state.catalog_load_result.excluded_package_count}, "
            f"operation=application_bootstrap."
        )
    )
    return state
