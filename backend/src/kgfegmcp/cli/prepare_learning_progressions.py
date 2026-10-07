"""Reproducibly prepare stored LP delivery/evidence from verified local copies."""

# Standard Library
import json

from pathlib import Path

# Third Party Library
import typer

from pydantic import ValidationError

# Package Library
from kgfegmcp.config import BackendSettings
from kgfegmcp.errors import KGFEGMCPError
from kgfegmcp.packages.normalization import prepare_learning_progressions
from kgfegmcp.packages.normalization_sources import LOCAL_SOURCE_ROOT

cli = typer.Typer(
    help="Prepare AS/LC/LP inputs and provenance partitions without package acceptance."
)


@cli.command(
    help="Prepare stored LP delivery, unchanged evidence and deterministic provenance partitions."
)
def prepare(
    framework_id: str | None = typer.Option(
        None, "--framework-id", help="Exact copied framework ID; omitted prepares all."
    ),
    output_root: Path = typer.Option(
        LOCAL_SOURCE_ROOT / "prepared",
        "--output-root",
        help="Separate preparation root; runtime roots are protected.",
    ),
    receipt: Path = typer.Option(
        LOCAL_SOURCE_ROOT / "copy_receipt.json",
        "--receipt",
        help="Verified repository-local copy receipt.",
    ),
) -> None:
    """Prepare deterministic local LP inputs and display relative artifact hashes.

    Parameters
    ----------
    framework_id
        Optional exact copied framework selection.
    output_root
        Separate local preparation destination.
    receipt
        Verified repository-local copy receipt.

    Raises
    ------
    typer.Exit
        If input verification, reconciliation or safe publication fails.

    Examples
    --------
    Run ``kgfegmcp-prepare-learning-progressions --framework-id FRAMEWORK`` to
    prepare one framework, or omit the selection to prepare all copied frameworks.
    """
    try:
        settings = BackendSettings()
        results = prepare_learning_progressions(
            framework_id=framework_id,
            output_root=output_root,
            project_dir=settings.project_dir,
            receipt_path=receipt,
        )
    except ValidationError as error:
        locations = [
            ".".join(str(part) for part in e["loc"])
            for e in error.errors(include_input=False, include_url=False)
        ]
        typer.echo(
            "Invalid preparation input fields: " + ", ".join(locations), err=True
        )
        raise typer.Exit(code=1) from error
    except KGFEGMCPError as error:
        typer.echo(error.public_message(), err=True)
        raise typer.Exit(code=1) from error
    except OSError as error:
        typer.echo(
            "Local preparation I/O failed; check copied inputs and output access.",
            err=True,
        )
        raise typer.Exit(code=1) from error
    typer.echo(
        json.dumps(
            ensure_ascii=False,
            indent=2,
            obj=[r.model_dump(by_alias=True, mode="json") for r in results],
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    cli()
