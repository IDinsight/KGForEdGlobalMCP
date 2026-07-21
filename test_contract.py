"""Contract tests: each test asserts one line of the tool spec.

Run: pytest test_contract.py -v
Tests 1-9 exercise the registry directly; test 10 drives the real server over stdio.
"""

import asyncio
import json
import os
from pathlib import Path

import pytest

from kg import Registry

FIXTURES = Path(__file__).parent / "fixtures"
# packaged layout (data/ beside this file) first, dev-repo layout as fallback
_LOCAL = Path(__file__).resolve().parent / "data" / "manifest.json"
_DEV = Path(__file__).resolve().parent.parent / "examples" / "kgs" / "manifest.json"
MANIFEST = Path(os.environ.get("KG_MANIFEST") or (_LOCAL if _LOCAL.exists() else _DEV))

JURIS_ERR = "jurisdiction is required. Expected one of: 'Ghana', 'Nigeria', 'Rwanda'."
CODES_ERR = "Statement codes are not available for {}; search with keywords instead."
SUBJECT_ERR = ("Unknown academic subject 'Astrology'. Expected one of: 'Mathematics', "
               "'English Language Arts', 'Science', 'Social Studies', 'Other'.")


@pytest.fixture(scope="module")
def registry():
    return Registry(MANIFEST)


def test_response_fields_match_live_capture(registry):
    """A response carries exactly the fields CZI's live service returns — no extras, none missing."""
    capture = json.loads((FIXTURES / "fss_code.json").read_text())["payload"]["standards"][0]
    ours = registry.find_standard_statement(code="B5.1.1.3", jurisdiction="Ghana")["standards"][0]
    expected_keys = set(capture) | {"subStandards"}
    assert set(ours) <= expected_keys
    assert set(capture) <= set(ours)


def test_code_prefix_respects_dot_boundary(registry):
    """Searching a code prefix returns that standard and its children, never siblings that merely share digits."""
    codes = [s["statementCode"]
             for s in registry.find_standard_statement(code="B5.1.1.3", jurisdiction="Ghana")["standards"]]
    assert codes
    assert all(c == "B5.1.1.3" or c.startswith("B5.1.1.3.") for c in codes)


def test_keywords_are_stemmed_whole_words(registry):
    """Keyword search matches whole words by stem — "fraction" finds "fractions", a fragment like "fract" finds nothing."""
    assert registry.find_standard_statement(keywords=["fraction"], jurisdiction="Rwanda")["standards"]
    assert not registry.find_standard_statement(keywords=["fract"], jurisdiction="Rwanda")["standards"]


def test_keywords_are_any_of(registry):
    """Any one matching keyword is enough — adding a nonsense word to a working search changes nothing."""
    a = registry.find_standard_statement(keywords=["fraction"], jurisdiction="Rwanda")["standards"]
    b = registry.find_standard_statement(keywords=["zzzqqx", "fraction"], jurisdiction="Rwanda")["standards"]
    assert [s["caseIdentifierUUID"] for s in a] == [s["caseIdentifierUUID"] for s in b]


def test_results_cap_at_exactly_25(registry):
    """A broad search returns at most 25 results, even when far more standards match."""
    hits = registry.find_standard_statement(keywords=["number"], jurisdiction="Rwanda")["standards"]
    assert len(hits) == 25
    assert registry.match_count(code=None, keywords=["number"],
                                jurisdiction="Rwanda", academic_subject=None) > 25


def test_miss_is_empty_and_codeless_country_errors(registry):
    """A code that misses in Ghana returns an empty list; a code search where no codes exist at all returns a helpful error instead."""
    assert registry.find_standard_statement(code="B9.9.9", jurisdiction="Ghana") == {"standards": []}
    for juris in ("Nigeria", "Rwanda"):
        with pytest.raises(ValueError, match=CODES_ERR.format(juris).replace("(", "\\(")):
            registry.find_standard_statement(code="B5.1", jurisdiction=juris)


@pytest.mark.parametrize("query", [
    dict(code="B5.1.1.3.4", jurisdiction="Ghana"),
    dict(keywords=["shapes"], jurisdiction="Nigeria"),
    dict(keywords=["currency"], jurisdiction="Rwanda"),
])
def test_every_result_carries_numeric_grade_levels(registry, query):
    """Every returned standard carries a numeric grade, inherited from its place in the curriculum tree."""
    for s in registry.find_standard_statement(**query)["standards"]:
        assert s["gradeLevels"], s["description"][:60]
        assert all(g.isdigit() for g in s["gradeLevels"])


def test_orphan_grade_recovers_from_code(registry):
    """A standard whose parent went missing in extraction still gets its grade, recovered from its own code."""
    hit = registry.find_standard_statement(code="B5.1.2.3", jurisdiction="Ghana")["standards"][0]
    assert hit["gradeLevels"] == ["5"]


def test_jurisdiction_required_with_exact_sentence(registry):
    """Omitting or misspelling the country returns the exact required-jurisdiction sentence, naming the valid options."""
    for kwargs in (dict(keywords=["fraction"]),
                   dict(keywords=["fraction"], jurisdiction="Kenya")):
        with pytest.raises(ValueError) as exc:
            registry.find_standard_statement(**kwargs)
        assert str(exc.value) == JURIS_ERR


def test_unknown_subject_matches_live_capture(registry):
    """An unknown subject returns CZI's error sentence word for word, verified against their live capture."""
    live = json.loads((FIXTURES / "fss_badsubject.json").read_text())["payload"]["__raw_text__"]
    with pytest.raises(ValueError) as exc:
        registry.find_standard_statement(keywords=["x"], jurisdiction="Ghana",
                                         academic_subject="Astrology")
    assert str(exc.value) == SUBJECT_ERR == live


def test_stdio_surface_and_bare_errors():
    """The real server process serves exactly one tool and puts bare error sentences on the wire, the way CZI does."""
    async def check():
        from mcp import ClientSession, StdioServerParameters
        from mcp.client.stdio import stdio_client
        params = StdioServerParameters(command="python3",
                                       args=[str(Path(__file__).parent / "server.py"), str(MANIFEST)])
        async with stdio_client(params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                tools = (await session.list_tools()).tools
                assert [t.name for t in tools] == ["find_standard_statement"]
                assert all(j in tools[0].description for j in ("Ghana", "Nigeria", "Rwanda"))
                err = await session.call_tool("find_standard_statement", {"keywords": ["fraction"]})
                assert err.isError and err.content[0].text == JURIS_ERR
                ok = await session.call_tool("find_standard_statement",
                                             {"code": "B5.1.1.3.4", "jurisdiction": "Ghana"})
                assert not ok.isError and "highest common factor" in ok.content[0].text

    asyncio.run(check())


def test_recovered_codes_are_searchable(registry):
    """A standard whose code the extractor left inside the description text is still findable by code search."""
    hit = registry.find_standard_statement(code="B5.1.1.3.5", jurisdiction="Ghana")["standards"]
    assert hit and hit[0]["statementCode"] == "B5.1.1.3.5"
    assert hit[0]["description"].startswith("B5.1.1.3.5")
