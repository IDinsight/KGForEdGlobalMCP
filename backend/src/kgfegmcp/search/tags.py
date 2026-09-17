"""This module builds package-local learning-component tag indexes.

The index in this module maps normalized tag keys to the learning components that
declare them. Tags are controlled multi-word facets rather than free text, so they are
normalized with the existing facet normalizer and matched whole rather than tokenized.

The module indexes only learning components. Standards framework items carry no tags,
and the index therefore cannot return source-asserted curriculum content.
"""

# Future Library
from __future__ import annotations

# Standard Library
from collections.abc import Mapping
from dataclasses import dataclass
from types import MappingProxyType

# Package Library
from kgfegmcp.catalog.models import CatalogPackageRuntime
from kgfegmcp.graph.models import GraphPackageIdentity, LearningComponentNode
from kgfegmcp.search.normalizers import normalize_facet_value


@dataclass(frozen=True, slots=True)
class TagIndex:
    """Own one immutable learning-component tag index for one graph package."""

    components_by_tag_key: Mapping[str, tuple[LearningComponentNode, ...]]
    package_identity: GraphPackageIdentity

    @classmethod
    def from_runtime(cls, runtime: CatalogPackageRuntime) -> TagIndex:
        """Build a package-local tag index from an accepted catalog runtime.

        Parameters
        ----------
        runtime
            Exact accepted package runtime whose source node instances are retained.

        Returns
        -------
        TagIndex
            Immutable package-local learning-component tag index.
        """

        mutable_components: dict[str, list[LearningComponentNode]] = {}

        for component in runtime.loaded_package.learning_component_nodes:
            for tag in dict.fromkeys(component.tags or ()):
                key = normalize_facet_value(tag)

                if not key:
                    continue

                if key not in mutable_components:
                    mutable_components[key] = []

                mutable_components[key].append(component)

        return cls(
            components_by_tag_key=MappingProxyType(
                {
                    key: tuple(components)
                    for key, components in sorted(mutable_components.items())
                }
            ),
            package_identity=runtime.catalog_package.package_identity,
        )

    @property
    def tag_vocabulary_size(self) -> int:
        """Return the number of distinct normalized tag keys in the index.

        Returns
        -------
        int
            Number of distinct normalized tag keys.
        """

        return len(self.components_by_tag_key)

    def components_for_tag(self, tag: str) -> tuple[LearningComponentNode, ...]:
        """Return every learning component declaring one exact tag.

        Parameters
        ----------
        tag
            Caller-supplied tag value, normalized before lookup.

        Returns
        -------
        tuple[LearningComponentNode, ...]
            Learning components in deterministic source order, empty when unmatched.
        """

        return self.components_by_tag_key.get(normalize_facet_value(tag), ())
