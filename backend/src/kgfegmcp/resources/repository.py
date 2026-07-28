"""This module reads exact resource bytes from already accepted graph packages.

``ResourceRepository`` operates only on ``LoadedGraphPackage`` instances produced after
the approved package-validation gate. It resolves artifacts by exact logical manifest
name, reads only their retained package-local paths, enforces source-size limits, and
verifies the actual byte length and SHA-256 before returning content.

Callers never provide arbitrary filesystem paths. This module does not discover or load
packages, choose framework snapshots, evaluate graph semantics, perform graph lookup,
serialize derived resources, or register FastMCP components.
"""

# Future Library
from __future__ import annotations

# Standard Library
from dataclasses import dataclass

# Package Library
from kgfegmcp.errors import ResourceNotFoundError
from kgfegmcp.packages.checksums import calculate_bytes_sha256
from kgfegmcp.packages.models import DeclaredArtifactReference, LoadedGraphPackage
from kgfegmcp.resources.policy import ResourcePolicy


@dataclass(frozen=True, slots=True)
class ResourceRepository:
    """Provide checksum-verified byte access to accepted package evidence."""

    policy: ResourcePolicy

    @staticmethod
    def artifact_reference(
        *, loaded_package: LoadedGraphPackage, logical_name: str
    ) -> DeclaredArtifactReference:
        """Return one exact manifest-declared artifact reference.

        Parameters
        ----------
        loaded_package
            Accepted package retained by the catalog runtime.
        logical_name
            Exact public manifest logical name.

        Returns
        -------
        DeclaredArtifactReference
            Accepted package-local path and integrity evidence.

        Raises
        ------
        ResourceNotFoundError
            When the package does not identify exactly one matching declaration.
        """

        references = tuple(
            artifact
            for artifact in loaded_package.artifacts
            if str(artifact.logical_name) == logical_name
        )

        if not references:
            raise ResourceNotFoundError(
                details={"logical_name": logical_name},
                message="The selected package does not declare the requested artifact.",
            )

        if len(references) != 1:
            raise ResourceNotFoundError(
                details={
                    "logical_name": logical_name,
                    "matching_declaration_count": len(references),
                },
                message=(
                    "The accepted package does not identify one exact artifact declaration."
                ),
            )

        return references[0]

    def read_artifact(
        self, *, loaded_package: LoadedGraphPackage, logical_name: str
    ) -> tuple[bytes, DeclaredArtifactReference]:
        """Read and verify one exact manifest-declared artifact.

        Parameters
        ----------
        loaded_package
            Accepted package retained by the catalog runtime.
        logical_name
            Exact public manifest logical name.

        Returns
        -------
        tuple[bytes, DeclaredArtifactReference]
            Exact bytes and their accepted manifest reference.

        Raises
        ------
        ResourceNotFoundError
            If the artifact is unavailable or no longer matches accepted integrity
            evidence.
        ResourceAccessDeniedError
            If the declared source exceeds the configured read limit.
        """

        reference = self.artifact_reference(
            loaded_package=loaded_package, logical_name=logical_name
        )
        self.policy.require_source_size(reference.size_bytes)

        try:
            with reference.resolved_path.open("rb") as stream:
                content = stream.read(self.policy.max_resource_source_bytes + 1)
        except OSError as error:
            raise ResourceNotFoundError(
                details={"logical_name": logical_name, "reason": type(error).__name__},
                message="The accepted artifact content is unavailable.",
            ) from error

        self.policy.require_source_size(len(content))
        actual_sha256 = calculate_bytes_sha256(content)

        if len(content) != reference.size_bytes or actual_sha256 != reference.sha256:
            raise ResourceNotFoundError(
                details={
                    "actual_sha256": str(actual_sha256),
                    "actual_size_bytes": len(content),
                    "declared_sha256": str(reference.sha256),
                    "declared_size_bytes": reference.size_bytes,
                    "logical_name": logical_name,
                },
                message=(
                    "The artifact no longer matches the accepted package integrity evidence."
                ),
            )

        return content, reference

    def read_manifest(self, loaded_package: LoadedGraphPackage) -> bytes:
        """Return retained exact accepted manifest bytes.

        Parameters
        ----------
        loaded_package
            Accepted package retained by the catalog runtime.

        Returns
        -------
        bytes
            Exact manifest bytes.
        """

        self.policy.require_return_size(len(loaded_package.manifest_bytes))
        return loaded_package.manifest_bytes

    def read_profile(self, loaded_package: LoadedGraphPackage) -> bytes:
        """Return retained exact accepted interpretation-profile bytes.

        Parameters
        ----------
        loaded_package
            Accepted package retained by the catalog runtime.

        Returns
        -------
        bytes
            Exact interpretation-profile bytes.
        """

        self.policy.require_return_size(len(loaded_package.profile_bytes))
        return loaded_package.profile_bytes
