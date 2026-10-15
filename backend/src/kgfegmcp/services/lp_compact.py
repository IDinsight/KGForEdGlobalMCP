"""Compact LP relationship tables by stating identical evidence fields once.

Learning Progression results that return several relationships repeat the same
per-edge boilerplate (attribution, author, provider, license, entity fields, the
confidence notice) in every entry. ``compact_relationships`` lifts each liftable field
whose non-null value is identical across all entries into one
``SharedRelationshipEvidence`` object and omits it from the entries.
``rehydrate_relationships`` reverses this exactly: an entry's own value wins, then the
shared value, otherwise null.
"""

# Standard Library
from collections.abc import Mapping, Sequence
from typing import Final

# Package Library
from kgfegmcp.services.lp_models import (
    CompactProgressionRelationshipEvidence,
    ProgressionRelationshipEvidence,
    SharedGraphRelationshipEvidence,
    SharedJudgmentEvidence,
    SharedRelationshipEvidence,
)

# Liftable fields by nesting level, as fixed by the cycle design.
LIFTABLE_EVIDENCE_FIELDS: Final[tuple[str, ...]] = ("epistemic_status",)
LIFTABLE_JUDGMENT_FIELDS: Final[tuple[str, ...]] = ("confidence_notice",)
LIFTABLE_RELATIONSHIP_FIELDS: Final[tuple[str, ...]] = (
    "attribution_statement",
    "author",
    "description",
    "label",
    "license",
    "provider",
    "relationship_type",
    "source_entity",
    "source_entity_key",
    "source_labels",
    "target_entity",
    "target_entity_key",
    "target_labels",
)


def _fill(
    *, entry: dict[str, object], names: tuple[str, ...], shared: Mapping[str, object]
) -> None:
    """Restore omitted liftable fields of one entry level from its shared values.

    Parameters
    ----------
    entry
        Mutable field-name mapping of one compact entry level.
    names
        Liftable field names at this level.
    shared
        Shared values at the same level; absent names restore as null.
    """

    for name in names:
        if entry.get(name) is None:
            entry[name] = shared.get(name)


def _shared_values(
    *, entries: Sequence[Mapping[str, object]], names: tuple[str, ...]
) -> dict[str, object]:
    """Select the liftable fields whose non-null value every entry shares.

    Parameters
    ----------
    entries
        Field-name mappings of one nesting level, one per relationship.
    names
        Liftable field names at this level.

    Returns
    -------
    dict[str, object]
        Field name to the common value; empty when there are no entries.

    Examples
    --------
    >>> _shared_values(entries=[{"a": 1, "b": 2}, {"a": 1, "b": 3}], names=("a", "b"))
    {'a': 1}
    """

    shared: dict[str, object] = {}

    for name in names:
        values = [entry[name] for entry in entries]

        if values and values[0] is not None and all(v == values[0] for v in values):
            shared[name] = values[0]

    return shared


def _strip(
    *, entry: Mapping[str, object], shared: Mapping[str, object]
) -> dict[str, object]:
    """Copy one entry level without the fields that were lifted.

    Parameters
    ----------
    entry
        Field-name mapping of one full entry level.
    shared
        Lifted values at the same level.

    Returns
    -------
    dict[str, object]
        Entry fields with lifted names set to ``None`` so they are omitted.
    """

    return {name: None if name in shared else value for name, value in entry.items()}


def compact_relationships(
    *, relationships: Sequence[ProgressionRelationshipEvidence]
) -> tuple[
    SharedRelationshipEvidence, tuple[CompactProgressionRelationshipEvidence, ...]
]:
    """Lift identical evidence fields once and compact every entry in order.

    Parameters
    ----------
    relationships
        Full relationship evidence in result order.

    Returns
    -------
    tuple[SharedRelationshipEvidence, tuple[CompactProgressionRelationshipEvidence, ...]]
        The shared evidence object (empty when nothing is lifted) and one compact
        entry per relationship, in the same order.

    Examples
    --------
    >>> shared, entries = compact_relationships(relationships=result.relationships)
    >>> shared.relationship.license
    'Unknown'
    """

    dumped = [item.model_dump() for item in relationships]
    top = _shared_values(entries=dumped, names=LIFTABLE_EVIDENCE_FIELDS)
    judgment = _shared_values(
        entries=[item["judgment"] for item in dumped], names=LIFTABLE_JUDGMENT_FIELDS
    )
    relationship = _shared_values(
        entries=[item["relationship"] for item in dumped],
        names=LIFTABLE_RELATIONSHIP_FIELDS,
    )
    shared = SharedRelationshipEvidence.model_validate(
        {
            **top,
            "judgment": (
                SharedJudgmentEvidence.model_validate(judgment) if judgment else None
            ),
            "relationship": (
                SharedGraphRelationshipEvidence.model_validate(relationship)
                if relationship
                else None
            ),
        }
    )
    entries = tuple(
        CompactProgressionRelationshipEvidence.model_validate(
            {
                **_strip(entry=item, shared=top),
                "judgment": _strip(entry=item["judgment"], shared=judgment),
                "relationship": _strip(entry=item["relationship"], shared=relationship),
            }
        )
        for item in dumped
    )
    return shared, entries


def rehydrate_relationships(
    *,
    relationships: Sequence[CompactProgressionRelationshipEvidence],
    shared: SharedRelationshipEvidence,
) -> tuple[ProgressionRelationshipEvidence, ...]:
    """Rebuild the full evidence of every compact entry from its shared values.

    Parameters
    ----------
    relationships
        Compact entries in result order.
    shared
        The result's shared relationship evidence.

    Returns
    -------
    tuple[ProgressionRelationshipEvidence, ...]
        Full evidence equal to what ``relationship_evidence`` builds for each entry.

    Raises
    ------
    pydantic.ValidationError
        If a required evidence field is missing from both an entry and the shared
        evidence.
    """

    shared_dump = shared.model_dump()
    rebuilt = []

    for entry in relationships:
        data = entry.model_dump()
        judgment = data.get("judgment", {})
        relationship = data.get("relationship", {})
        _fill(entry=data, names=LIFTABLE_EVIDENCE_FIELDS, shared=shared_dump)
        _fill(
            entry=judgment,
            names=LIFTABLE_JUDGMENT_FIELDS,
            shared=shared_dump.get("judgment") or {},
        )
        _fill(
            entry=relationship,
            names=LIFTABLE_RELATIONSHIP_FIELDS,
            shared=shared_dump.get("relationship") or {},
        )
        rebuilt.append(
            ProgressionRelationshipEvidence.model_validate(
                {**data, "judgment": judgment, "relationship": relationship}
            )
        )

    return tuple(rebuilt)
