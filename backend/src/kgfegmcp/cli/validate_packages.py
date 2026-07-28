"""This module contains the entry point for graph-package validation.

This module loads environment-backed application settings, constructs the graph-package
repository, profile repository, package loader, and package validator, and serializes
public validation results as deterministic JSON. Environment variables may be populated
by a shell tool such as direnv before the command starts.

The ``one`` command validates one exact framework snapshot. The ``pending`` command
discovers and validates all pending packages beneath the configured graph-packages
root. Read-only mode reports findings without changing manifest state. When persistence
is allowed, invalid pending packages use the configured or explicitly selected
``failed`` or ``quarantined`` policy. Terminal packages selected individually are
revalidated read-only and are never rewritten.

The CLI returns success for valid results, a distinct nonzero status for invalid
packages, and a separate status for invocation, configuration, or domain failures. It
does not implement package discovery, artifact loading, checksum verification, graph
validation, profile semantics, or status persistence itself; those responsibilities
remain in the underlying repositories, loader, and validator.

Invoke from the backend directory to validate one framework snapshot without changing
its validation status:

    python -m kgfegmcp.cli.validate_packages one --framework-id FRAMEWORK_ID \
        --snapshot-id SNAPSHOT_ID --read-only

To validate every pending package beneath the configured graph-packages root:

    python -m kgfegmcp.cli.validate_packages pending --read-only

Omit ``--read-only`` to persist an allowed pending-to-terminal validation transition.
Use ``--invalid-package-policy quarantine`` to quarantine invalid pending packages
instead of marking them failed.

Terminal packages selected through ``one`` are always revalidated read-only and are
never rewritten.
"""

# Future Library
from __future__ import annotations

# Standard Library
import json

from typing import Annotated

# Third Party Library
import typer

from pydantic import TypeAdapter, ValidationError

# Package Library
from kgfegmcp.config import BackendSettings
from kgfegmcp.domain.enums import InvalidPackagePolicy
from kgfegmcp.domain.identifiers import FrameworkId, SnapshotId
from kgfegmcp.errors import KGFEGMCPError, PackageValidationError
from kgfegmcp.packages.loader import GraphPackageLoader
from kgfegmcp.packages.models import PackageValidationResult
from kgfegmcp.packages.repository import GraphPackageRepository
from kgfegmcp.packages.validator import GraphPackageValidator
from kgfegmcp.profiles.repository import ProfileRepository

_FRAMEWORK_ID_ADAPTER: TypeAdapter[FrameworkId] = TypeAdapter(FrameworkId)
_SNAPSHOT_ID_ADAPTER: TypeAdapter[SnapshotId] = TypeAdapter(SnapshotId)

cli = typer.Typer(
    help="Validate curriculum graph packages and control terminal status.",
    no_args_is_help=True,
)


def _resolved_policy(
    *, policy: InvalidPackagePolicy | None, settings: BackendSettings
) -> InvalidPackagePolicy:
    """Return an explicit CLI policy or the configured default.

    Parameters
    ----------
    policy
        Optional command-specific policy.
    settings
        Validated application settings.

    Returns
    -------
    InvalidPackagePolicy
        Effective invalid-package policy.
    """

    return policy or settings.invalid_package_policy


def _serialize_result(result: PackageValidationResult) -> str:
    """Serialize one public validation result as deterministic JSON.

    Parameters
    ----------
    result
        Structured validation result.

    Returns
    -------
    str
        Indented lower-camel-case JSON without private diagnostic details.
    """

    payload = result.model_dump(by_alias=True, mode="json")
    return json.dumps(ensure_ascii=False, indent=2, obj=payload, sort_keys=True)


def _serialize_results(results: tuple[PackageValidationResult, ...]) -> str:
    """Serialize a batch of public validation results as deterministic JSON.

    Parameters
    ----------
    results
        Ordered package validation results.

    Returns
    -------
    str
        Indented JSON array without private diagnostic details.
    """

    payload = tuple(result.model_dump(by_alias=True, mode="json") for result in results)
    return json.dumps(ensure_ascii=False, indent=2, obj=payload, sort_keys=True)


def _validator(settings: BackendSettings) -> GraphPackageValidator:
    """Construct the repository, loader, and validator service graph.

    Parameters
    ----------
    settings
        Validated application settings.

    Returns
    -------
    GraphPackageValidator
        Ready package validation service.
    """

    repository = GraphPackageRepository(
        graph_packages_root=settings.graph_packages_root
    )
    profile_repository = ProfileRepository(profile_root=settings.profile_root)
    loader = GraphPackageLoader(
        profile_repository=profile_repository, repository=repository
    )
    return GraphPackageValidator(loader=loader, repository=repository)


def _write_error(error: KGFEGMCPError) -> None:
    """Write one public domain error to standard error.

    Parameters
    ----------
    error
        Expected typed backend failure.
    """

    payload = error.public_payload()
    typer.echo(
        err=True,
        message=json.dumps(ensure_ascii=False, indent=2, obj=payload, sort_keys=True),
    )


@cli.command("one")
def validate_one(
    *,
    framework_id: Annotated[
        str, typer.Option(help="Stable framework identifier.", metavar="FRAMEWORK_ID")
    ],
    invalid_package_policy: Annotated[
        InvalidPackagePolicy | None,
        typer.Option(
            help="Terminal status for an invalid pending package.", metavar="POLICY"
        ),
    ] = None,
    read_only: Annotated[
        bool, typer.Option(help="Validate without changing package validation status.")
    ] = False,
    snapshot_id: Annotated[
        str, typer.Option(help="Immutable snapshot identifier.", metavar="SNAPSHOT_ID")
    ],
) -> None:
    """Validate one selected package and persist only an allowed pending transition.

    Parameters
    ----------
    framework_id
        Stable framework identifier.
    invalid_package_policy
        Optional invalid-package terminal policy override.
    read_only
        Whether status persistence is prohibited.
    snapshot_id
        Immutable snapshot identifier.

    Raises
    ------
    typer.Exit
        With code 1 for an invalid package or code 2 for invocation or domain errors.
    """

    try:
        validated_framework_id = _FRAMEWORK_ID_ADAPTER.validate_python(framework_id)
        validated_snapshot_id = _SNAPSHOT_ID_ADAPTER.validate_python(snapshot_id)
        settings = BackendSettings()
        validator = _validator(settings)
        candidate = validator.repository.candidate(
            framework_id=validated_framework_id, snapshot_id=validated_snapshot_id
        )
        outcome = validator.validate_candidate(
            candidate=candidate,
            invalid_package_policy=_resolved_policy(
                policy=invalid_package_policy, settings=settings
            ),
            read_only=read_only,
        )
    except ValidationError as error:
        invocation_error = PackageValidationError(
            details={
                "validation_errors": error.errors(
                    include_input=False, include_url=False
                )
            },
            message="A package identifier or CLI setting is invalid.",
        )
        _write_error(invocation_error)
        raise typer.Exit(code=2) from error
    except KGFEGMCPError as error:
        _write_error(error)
        raise typer.Exit(code=2) from error

    typer.echo(_serialize_result(outcome.result))

    if not outcome.result.is_valid:
        raise typer.Exit(code=1)


@cli.command("pending")
def validate_pending(
    *,
    invalid_package_policy: Annotated[
        InvalidPackagePolicy | None,
        typer.Option(
            help="Terminal status for invalid pending packages.", metavar="POLICY"
        ),
    ] = None,
    read_only: Annotated[
        bool, typer.Option(help="Validate without changing package validation status.")
    ] = False,
) -> None:
    """Validate every discovered pending package and report malformed candidates.

    Parameters
    ----------
    invalid_package_policy
        Optional invalid-package terminal policy override.
    read_only
        Whether status persistence is prohibited.

    Raises
    ------
    typer.Exit
        With code 1 when any package is invalid or code 2 for domain failures.
    """

    try:
        settings = BackendSettings()
        outcomes = _validator(settings).validate_pending(
            invalid_package_policy=_resolved_policy(
                policy=invalid_package_policy, settings=settings
            ),
            read_only=read_only,
        )
    except (KGFEGMCPError, ValidationError) as error:
        if isinstance(error, KGFEGMCPError):
            public_error = error
        else:
            public_error = PackageValidationError(
                details={
                    "validation_errors": error.errors(
                        include_input=False, include_url=False
                    )
                },
                message="Validation CLI settings are invalid.",
            )

        _write_error(public_error)
        raise typer.Exit(code=2) from error

    results = tuple(outcome.result for outcome in outcomes)
    typer.echo(_serialize_results(results))

    if any(not result.is_valid for result in results):
        raise typer.Exit(code=1)


if __name__ == "__main__":
    cli()
