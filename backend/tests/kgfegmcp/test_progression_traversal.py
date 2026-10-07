"""Offline traversal byte-boundary checks with validated synthetic evidence."""

# Third Party Library
import pytest

# Package Library
from kgfegmcp.errors import ProgressionResultTooLargeError
from kgfegmcp.services.lp_models import MAX_PROGRESSION_RESULT_BYTES
from tests.fixtures.progression_fixtures import Topology, builds


@pytest.mark.parametrize("oversized_position", [0, 1], ids=["first", "later"])
def test_individually_oversized_traversal_entry_is_an_error(
    oversized_position: int,
) -> None:
    """Reject an unreturnable edge whether it appears first or after a fitting edge."""
    spec = builds([("a", "a", "b"), ("b", "a", "c")])
    identifier, source, target, label, _ = spec[oversized_position]
    spec[oversized_position] = (
        identifier,
        source,
        target,
        label,
        "x" * (MAX_PROGRESSION_RESULT_BYTES + 1),
    )
    graph = Topology(spec)
    with pytest.raises(ProgressionResultTooLargeError) as failure:
        observed = graph.walk(max_depth=1)
        pytest.fail(
            "An individually oversized edge was silently omitted: "
            f"returned={observed.counters.returned_relationship_count}, "
            f"examined={observed.counters.examined_relationship_count}, "
            f"reasons={observed.truncation_reasons}, "
            f"scope_complete={observed.scope_complete}."
        )
    assert failure.value.error_code == "progression_result_too_large"
    assert failure.value.recovery_hint is not None
    assert "resource" in failure.value.recovery_hint.lower()
