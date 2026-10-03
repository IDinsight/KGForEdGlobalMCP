"""Reviewer diagnostic: read-only reconciliation of retained recovery evidence.

Run from repository root; stdout is a compact review receipt. No formal tests
or other roles' evidence are created or altered.
"""
import hashlib
import json
from pathlib import Path, PurePosixPath
import stat
import zipfile

CYCLE = "integrate-actual-learning-progressions-20261001T162834Z-142f2df1"
ROOT = Path.cwd()
BASE = Path("data/source_artifacts/learning_progressions")
E = BASE / "tester" / CYCLE / "reverify"
R = E.parent / "final-recovery"
REVIEW = Path(".standards/docs/reviews") / CYCLE
STAGE = BASE / "recovery-final-dev022/bundle"
ARCHIVE = STAGE.parent / "kgfegmcp-0.3.1-final-recovery.mcpb"
OLD = BASE / "recovery-dev022/kgfegmcp-0.3.1-recovery.mcpb"


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(path):
    return json.loads(Path(path).read_text())


inputs = {}
indices = {}
for path in [R / "evidence-index.json", E / "evidence-index.json",
             E / "fixture-relocation-evidence-index.json"]:
    index = read(path)
    index = index.get("files", index)
    for name, expected in index.items():
        assert digest(name) == expected, name
    indices[str(path)] = {"sha256": digest(path), "entries": len(index)}

changes = {}
for path in [E / "fixture-relocation-assessed-files.json", R / "assessed-inputs.json"]:
    files = read(path)["files"]
    changed = {name: digest(name) for name, expected in files.items()
               if digest(name) != expected}
    allowed = {".standards/STATE.md"}
    if path.parent == R:
        allowed.update({str(REVIEW / "final-deliverable.md"), str(REVIEW / "implementation.md"),
                        f".standards/docs/documentation/{CYCLE}.md",
                        "docs/data/prompt-configs.md"})
    if path.parent == E:
        allowed.update({f".standards/docs/development/{CYCLE}.md",
                        "backend/README.md", "packaging/mcpb/README.md"})
    assert set(changed) == allowed, changed
    changes[str(path)] = {"sha256": digest(path), "entries": len(files),
                          "unchanged": len(files) - len(changed), "changed": changed}

receipts = {}
for parent, names in [(E, ["fixture-relocation-suite", "fixture-relocation-black-final",
                          "fixture-relocation-isort", "fixture-relocation-ruff-final",
                          "fixture-relocation-mypy", "fixture-relocation-pylint-final",
                          "fixture-relocation-interrogate", "packages", "stdio",
                          "stage", "distribution", "stage-regression"]),
                      (R, ["stage", "stage-identity", "distribution"])]:
    for name in names:
        path = parent / (name + ".command.json")
        result = read(path)
        assert result["exitCode"] == 0, path
        for log in result["logs"].values():
            assert digest(log["path"]) == log["sha256"], log
        receipts[str(path)] = {"sha256": digest(path), "exitCode": 0,
                               "verifiedLogs": len(result["logs"])}
assert "78 passed in 99.01s" in (E / "fixture-relocation-suite.stdout").read_text()
http = read(E / "http-command.json")
assert http["clientExitCode"] == 0 and http["serverExitCodeAfterTermination"] == 143
assert "Application shutdown complete" in (E / "http-server.log").read_text()

# Reconstruct the source file set directly from the packaging recipe.
expected = {}
for src, dest in [("backend/src", "src"), ("config/profiles", "config/profiles"),
                  ("config/prompts", "config/prompts"),
                  ("data/graph_packages", "data/graph_packages")]:
    for path in Path(src).rglob("*"):
        rel = path.relative_to(src)
        if any(part in {"__pycache__", ".DS_Store", ".venv", ".mypy_cache",
                        ".pytest_cache", ".ruff_cache", "__MACOSX"}
               or part.endswith(".egg-info") for part in rel.parts):
            continue
        if path.suffix in {".pyc", ".pyo"}:
            continue
        assert not path.is_symlink(), path
        if path.is_file():
            expected[(Path(dest) / rel).as_posix()] = path
for name in ["README.md", "fastmcp.json", "pyproject.toml", "uv.lock"]:
    expected[name] = Path("backend") / name
expected["manifest.json"] = Path("packaging/mcpb/manifest.json")
member_changes = []
with zipfile.ZipFile(ARCHIVE) as current, zipfile.ZipFile(OLD) as old:
    names = current.namelist()
    assert len(names) == len(set(names)), "Duplicate ZIP entry"
    assert {n for n in names if not n.endswith("/")} == set(expected)
    assert {n for n in old.namelist() if not n.endswith("/")} == set(expected)
    assert len(expected) == 650
    for name in names:
        assert not PurePosixPath(name).is_absolute() and ".." not in PurePosixPath(name).parts
        assert not stat.S_ISLNK(current.getinfo(name).external_attr >> 16)
    for name, source in expected.items():
        data = current.read(name)
        assert not (STAGE / name).is_symlink()
        assert data == source.read_bytes() == (STAGE / name).read_bytes(), name
        if data != old.read(name):
            member_changes.append(name)
    assert member_changes == ["README.md"], member_changes
    readme = current.read("README.md").decode()
    assert "collect_progression_evidence" in old.read("README.md").decode()
    for token in ["collect_progression_evidence", "inferred_progression_hypothesis",
                  "**13 tools**", "**7 prompts**", "**12 resource templates**"]:
        assert token not in readme, token
    for token in ["**17 tools**", "**9 prompts**", "**14 resource templates**",
                  "get_learning_progression", "get_standard_progressions",
                  "search_learning_progressions", "traverse_learning_progressions",
                  "get_learning_progression_paths"]:
        assert token in readme, token
assert digest(ARCHIVE) == "adb10a43258a1115bfd74732c7d85af367f75e082a50c73f91b75e67a6cd5e04"
manifests = list((STAGE / "data/graph_packages").glob("*/*/package_manifest.json"))
assert len(manifests) == 6
for path in manifests:
    artifacts = read(path)["artifacts"]["additionalArtifacts"]
    assert sum(key.startswith("learningProgressionProvenanceShard") for key in artifacts) == 64
stage = read(R / "stage.stdout")
assert stage["status"] == "passed" and stage["bundleRoot"] == str(ROOT / STAGE)
counts = [stage[k] for k in ["toolCount", "promptCount", "fixedResourceCount",
                             "resourceTemplateCount", "resourceReadCount"]]
assert counts == [17, 9, 1, 14, 15]
for path in [E / "stdio.stdout", E / "http.json", E / "stage.stdout"]:
    prior = read(path)
    assert prior["status"] == "passed"
    for key in ["inventory", "toolSchemaIdentities", "progressions", "resourceReads"]:
        assert stage[key] == prior[key], (path, key)
identity = read(R / "stage-identity.json")
assert identity["status"] == "passed" and identity["priorStageDependencyVersionsEqual"]
for module in identity["stageModules"].values():
    assert Path(module["path"]).is_relative_to(ROOT / STAGE / "src")
    assert digest(module["path"]) == module["sha256"]


# Reconcile Documenter current final-byte claims and corrected check receipts.
doc_index = Path(".standards/docs/documentation/recovery-20261003/final-inputs.json")
doc = read(doc_index)
entry = read(REVIEW / "final-recovery/entry-inputs.json")
final_report = str(REVIEW / "final-deliverable.md")
for group in ["files", "supportingEvidence"]:
    for name, expected_hash in doc[group].items():
        expected_hash = expected_hash.removeprefix("sha256:")
        if name == final_report:
            # This review legitimately reopens its own report after receipt entry.
            assert entry["files"][name] == expected_hash
        else:
            assert digest(name) == expected_hash, name
for name, expected_exit in [("original-parser", 1), ("strict-build", 0),
                            ("corrected-examples", 0)]:
    path = doc_index.parent / (name + "-command.json")
    command = read(path)
    assert command["exit"] == command["expectedExit"] == expected_exit, path
corrected = read(doc_index.parent / "example-results.json")
assert corrected["status"] == "passed"
assert corrected["promptConfigPromptCount"] == 9
assert corrected["catalogParsingFormats"] == ["saved", "compact", "padded"]
assert corrected["renderedPages"] == 43 and corrected["renderedLocalLinks"] == 4803
assert len(corrected["tools"]) == 5 and len(corrected["prompts"]) == 3
assert len(corrected["resources"]) == 5 and len(corrected["catalog"]) == 6
# Original parser still demonstrably selects the wrong first framework.
catalog = Path("docs/data/framework-catalog.md").read_text()
table = catalog.split("## Catalog summary",1)[1].split("Across the six manifests",1)[0]
old_rows = [line for line in table.splitlines() if line.startswith("| ")][2:8]
assert old_rows[0].strip("|").split("|")[0].strip() == "Ghana Mathematics"
assert "**Total**" in old_rows[-1]
doc_reconciliation = {"indexSha256": digest(doc_index), "files":len(doc["files"]),
                      "supportingEvidence":len(doc["supportingEvidence"]),
                      "entryAllMatched":entry["documenterFinalReceiptAtEntry"]["allMatch"],
                      "onlyCurrentMutableEntry":final_report,
                      "originalParserFirstRow":"Ghana Mathematics",
                      "correctedResultSha256":digest(doc_index.parent/"example-results.json")}

for path in [Path(".standards/CONTEXT.md"), Path(".standards/PROTOCOL.md"),
             Path(f".standards/docs/scope/{CYCLE}.md"),
             Path(f".standards/docs/specs/{CYCLE}.md"),
             Path(f".standards/docs/development/{CYCLE}.md"),
             Path(f".standards/docs/verification/{CYCLE}.md"),
             Path(f".standards/docs/documentation/{CYCLE}.md"),
             REVIEW / "final-deliverable.md", Path("docs/data/prompt-configs.md"),
             Path("backend/README.md"), Path("packaging/mcpb/README.md"),
             Path(__file__)]:
    inputs[str(path)] = digest(path)
print(json.dumps({"status": "passed", "cwd": str(ROOT),
                  "inputChanges": changes, "documentationReconciliation": doc_reconciliation, "evidenceIndices": indices,
                  "commandReceipts": receipts, "inputs": inputs,
                  "archive": {"path": str(ARCHIVE), "sha256": digest(ARCHIVE),
                              "bytes": ARCHIVE.stat().st_size, "files": len(expected),
                              "changedMembers": member_changes,
                              "readmeSha256": digest(STAGE / "README.md")},
                  "packages": 6, "shardsPerPackage": 64, "stageCounts": counts,
                  "parity": "new stage equals prior STDIO, HTTP and stage",
                  "executionScope": "Reviewer read-only evidence and distribution diagnostic; prior behavioral tests were not rerun"}, indent=2))
