"""This module provides the versioned curriculum-profile repository used at package
boundaries.
"""

# Standard Library
from dataclasses import dataclass
from pathlib import Path

# Package Library
from kgfegmcp.domain.identifiers import ProfileId, ProfileVersion
from kgfegmcp.profiles.loader import LoadedProfile, load_curriculum_profile


@dataclass(frozen=True, slots=True)
class ProfileRepository:
    """Resolve exact immutable profiles beneath one configured repository root."""

    profile_root: Path

    def load(
        self, *, profile_id: ProfileId, profile_version: ProfileVersion
    ) -> LoadedProfile:
        """Load one exact profile through the strengthened profile loader.

        Parameters
        ----------
        profile_id
            Requested profile identifier.
        profile_version
            Requested immutable profile version.

        Returns
        -------
        LoadedProfile
            Exact profile bytes, checksum, path, and validated model.
        """

        return load_curriculum_profile(
            profile_id=profile_id,
            profile_root=self.profile_root,
            profile_version=profile_version,
        )
