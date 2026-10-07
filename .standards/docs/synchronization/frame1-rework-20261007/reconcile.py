"""Synchronizer reconciliation for the Frame 1 Desktop rework (standard library only).

Read-only for every owner artifact: it hashes and compares workflow records, owner
receipts, the retained 0.4.0 candidate built for this rework and Git state, then writes
only reconcile-results.json beside this file. It runs no tests, servers or models; formal
execution evidence stays with its owners and is checked here for identity and
applicability. Exits 1 when any check fails.
"""

# Standard Library
import hashlib
import json
import platform
import re
import stat
import subprocess
import sys
import zipfile

from pathlib import Path, PurePosixPath

ROOT = Path(__file__).resolve().parents[4]
OUT = Path(__file__).resolve().parent / "reconcile-results.json"
CYCLE = "integrate-actual-learning-progressions-20261001T162834Z-142f2df1"

RECORDS = {
    "scope": f".standards/docs/scope/{CYCLE}.md",
    "spec": f".standards/docs/specs/{CYCLE}.md",
    "plan": f".standards/docs/development/{CYCLE}.md",
    "verification": f".standards/docs/verification/{CYCLE}.md",
    "implementation": f".standards/docs/reviews/{CYCLE}/implementation.md",
    "final": f".standards/docs/reviews/{CYCLE}/final-deliverable.md",
    "documentation": f".standards/docs/documentation/{CYCLE}.md",
}
SYNC_RECORD = f".standards/docs/synchronization/{CYCLE}.md"
STATE, MODE, CONTEXT = ".standards/STATE.md", ".standards/MODE.md", ".standards/CONTEXT.md"
SYNC_DIR = ".standards/docs/synchronization/"

LP = "data/source_artifacts/learning_progressions"
FINAL = f"{LP}/frame1-rework-dev022/kgfegmcp-0.4.0-frame1-rework.mcpb"
STAGE = f"{LP}/frame1-rework-dev022/bundle"
DEV_CHECKS = f"{LP}/frame1-rework-dev022/checks"
PREVIOUS = f"{LP}/client-recovery-docs-dev022/kgfegmcp-0.4.0-client-recovery-docs.mcpb"
E1 = f"{LP}/tester/{CYCLE}/full-verification"
E6 = f"{LP}/tester/{CYCLE}/frame1-full"
REVIEW_FINAL = f".standards/docs/reviews/{CYCLE}/final-frame1"
REVIEW_IMPL = f".standards/docs/reviews/{CYCLE}/frame1-rework"
DOC_STYLE = ".standards/docs/documentation/style-rework-20261007"
DOC_FRAME1 = ".standards/docs/documentation/frame1-rework-20261007"

# Identities stated in the owner records (plan, verification, reviews, documentation).
FINAL_SHA = "2f0b981ca94a595f1e2a78c70084609dfcbc0aba1d5f434d56341228f4f1c2d3"
FINAL_BYTES = 82_183_565
PREVIOUS_SHA = "01df98e19c8cb89d312bfc9cfccff5f9ce43698000b5f341f212f633d407aec5"
README_SHA = "9ce0fc15618949b402b2d6d6e3d82e9525369334e742c6f9621c0738043d4365"
DEV_INDEX_SHA = "52d97e89d025add4c633925b56313cbaa606ed4374a4b01cb1992e56a51c3dd6"
COPY_RECEIPT_SHA = "e61d67b053a237e8fce6be86842f32ed5b398a145fb223410443d475419ae8ea"
DOC_RESULTS_SHA = "14571087e889c4d1ba279fcc9ce804c12e91c20ecaab699af502c302aab183ae"
LAST_SYNC = "a87ae15"  # synchronization commit that reached sign-off before this rework
BUILD_HEAD = "1c31450"  # clean HEAD the candidate was built from (DEV-022)
TESTER_HEAD = "108914e369d20386b530751272d27f8da24d29f5"  # Tester E6 full pass
IMPL_REVIEW_HEAD = "73455ff"  # implementation review's assessed HEAD
FINAL_REVIEW_HEAD = "87c3595f209ff0097eec6799b62a2dbbda4ec5a3"  # final review's assessed HEAD
TRANSPORT_KEYS = ["inventory", "toolSchemaIdentities", "progressions", "resourceReads", "access"]
EXPECTED_ACS = {f"AC-{n:03d}" for n in range(1, 38)}
RUNTIME_PATHS = ["backend/src", "backend/tests", "backend/pyproject.toml", "backend/uv.lock",
                 "backend/fastmcp.json", "config", "data/graph_packages",
                 "packaging/mcpb/manifest.json", ".github", ".pre-commit-config.yaml"]

FAILURES: list[str] = []
FACTS: dict[str, object] = {}


def check(name: str, ok: bool, observed: object = None) -> None:
    """Record one named outcome; collect failures instead of stopping early."""

    FACTS[name] = {"pass": bool(ok), "observed": observed}
    if not ok:
        FAILURES.append(name)


def path(relative: str) -> Path:
    """Absolute path of a repository-relative path."""

    return ROOT / relative


def sha_bytes(data: bytes) -> str:
    """Hex SHA256 of bytes."""

    return hashlib.sha256(data).hexdigest()


def sha_file(relative: str) -> str:
    """Hex SHA256 of a repository file."""

    return sha_bytes(path(relative).read_bytes())


def bare(value: str) -> str:
    """Normalize the owners' two hash spellings ("sha256:<hex>" and bare hex)."""

    return value.removeprefix("sha256:")


def git(*args: str) -> str:
    """Run a read-only Git command from the repository root and return stdout."""

    return subprocess.run(["git", *args], capture_output=True, check=True, cwd=ROOT,
                          text=True).stdout


def text_of(relative: str) -> str:
    """UTF-8 text of a repository file."""

    return path(relative).read_text(encoding="utf-8")


def section(text: str, start: str, end: str) -> str:
    """Text from the first `start` heading up to the next `end` heading after it."""

    begin = text.index(start)
    stop = text.index(end, begin + len(start))
    return text[begin:stop]


def mentioned_acs(text: str) -> set[str]:
    """Acceptance IDs named in text, expanding A..B / A–B ranges and slash shorthand."""

    found = set(re.findall(r"AC-\d{3}", text))
    for low, high in re.findall(r"AC-(\d{3})\s*(?:\.\.|–|—|through)\s*AC-(\d{3})", text):
        found |= {f"AC-{n:03d}" for n in range(int(low), int(high) + 1)}
    for first, rest in re.findall(r"AC-(\d{3})((?:/\d{3})+)", text):
        found |= {f"AC-{first}"} | {f"AC-{n}" for n in rest.strip("/").split("/")}
    return found


def provenance(text: str) -> dict[str, str]:
    """Fields of the leading STANDARDS provenance block."""

    match = re.match(r"<!-- STANDARDS\n((?:\w+: [^\n]+\n)+)-->", text)
    if not match:
        return {}
    return dict(line.split(": ", 1) for line in match.group(1).splitlines())


def field(text: str, name: str) -> str | None:
    """First backticked value of a `Name`: `value` field."""

    match = re.search(rf"`{re.escape(name)}`: `([^`]*)`", text)
    return match.group(1) if match else None


def changed(base: str, *paths: str) -> list[str]:
    """Paths changed between `base` and HEAD, optionally limited to pathspecs."""

    return git("diff", "--name-only", base, "HEAD", "--", *paths).split()


def check_git() -> None:
    """Repository state and the comparison ranges each owner assessed."""

    FACTS["head"] = git("rev-parse", "HEAD").strip()
    dirty = [line[3:] for line in git("status", "--porcelain=v1",
                                      "--untracked-files=all").splitlines()]
    check("only Synchronizer-owned files are dirty or untracked",
          all(p.startswith(SYNC_DIR) for p in dirty), dirty)
    check("index is empty", git("diff", "--cached", "--name-only") == "")
    check("no unmerged paths", git("ls-files", "-u") == "")

    since_review = changed(FINAL_REVIEW_HEAD)
    unexpected = [p for p in since_review if p not in {STATE, RECORDS["final"]}
                  and not p.startswith(REVIEW_FINAL + "/")]
    check("since final-review HEAD 87c3595 only STATE, the final review and its receipts "
          "changed", not unexpected, {"changed": len(since_review), "unexpected": unexpected})
    outside = changed(TESTER_HEAD, ".", ":(exclude).standards", ":(exclude)docs")
    check("nothing outside .standards and docs changed since Tester HEAD 108914e", not outside,
          outside)
    outside = changed(BUILD_HEAD, ".", ":(exclude).standards", ":(exclude)docs")
    check("nothing outside .standards and docs changed since the candidate build HEAD 1c31450",
          not outside, outside)
    runtime = changed(IMPL_REVIEW_HEAD, *RUNTIME_PATHS)
    check("runtime/tests/config/data/lock/manifest/CI unchanged since implementation-review "
          "HEAD 73455ff", not runtime, runtime)
    contracts = changed(LAST_SYNC, RECORDS["scope"], CONTEXT, "data/graph_packages", "config",
                        "backend/uv.lock", "README.md", "backend/README.md",
                        "packaging/mcpb/README.md", "mkdocs.yml")
    check("scope, CONTEXT, packages, config, lock, READMEs and mkdocs.yml unchanged during the "
          "rework", not contracts, contracts)
    rework = git("diff", "--name-status", LAST_SYNC, "HEAD", "--", ".",
                 ":(exclude).standards").splitlines()
    FACTS["reworkRange"] = {"base": LAST_SYNC, "paths": len(rework),
                            "added": sum(1 for r in rework if r.startswith("A")),
                            "modified": sum(1 for r in rework if r.startswith("M")),
                            "other": [r for r in rework if r[0] not in "AM"],
                            "docs": sum(1 for r in rework if r.split("\t")[1].startswith("docs/"))}


def check_records() -> dict[str, str]:
    """Provenance, completion fields and finding/discrepancy statuses of owner records."""

    texts = {key: text_of(rel) for key, rel in RECORDS.items()}
    kinds = {"scope": ("SCOPE", None), "spec": ("ARCHITECTURE", None),
             "plan": ("DEVELOPMENT", None), "verification": ("VERIFICATION", None),
             "implementation": ("REVIEW", "IMPLEMENTATION"),
             "final": ("REVIEW", "FINAL_DELIVERABLE"), "documentation": ("DOCUMENTATION", None)}
    for key, (artifact, kind) in kinds.items():
        block = provenance(texts[key])
        check(f"{key} provenance matches cycle/type/kind",
              block.get("Artifact") == artifact and block.get("Cycle") == CYCLE
              and block.get("ReviewKind") == kind, block)
    sync = provenance(text_of(SYNC_RECORD))
    check("synchronization record provenance matches cycle/type",
          sync == {"Artifact": "SYNCHRONIZATION", "Cycle": CYCLE}, sync)

    plan = texts["plan"]
    steps = section(plan, "## Build Steps", "## Plan Notes")
    entries = re.split(r"^### (?=DEV-\d{3})", steps, flags=re.M)[1:]
    statuses = {entry[:7]: field(entry, "Status") for entry in entries}
    expected_steps = {f"DEV-{n:03d}" for n in [*range(1, 6), *range(12, 30)]}
    check("plan COMPLETE, AFTER_IMPLEMENTATION, Current Increment NONE, locked tony",
          (field(plan, "Status"), field(plan, "Verification Cadence"),
           field(plan, "Current Increment"), field(plan, "User Style"),
           field(plan, "User Style Locked")) == ("COMPLETE", "AFTER_IMPLEMENTATION", "NONE",
                                                 "tony", "true"))
    check("all 23 approved DEV steps (DEV-001..005, DEV-012..029) are DONE",
          set(statuses) == expected_steps and set(statuses.values()) == {"DONE"}, statuses)

    verification = texts["verification"]
    check("verification COMPLETE, FULL/NONE",
          (field(verification, "Status"), field(verification, "Assessment Purpose"),
           field(verification, "Assessment Target")) == ("COMPLETE", "FULL", "NONE"))
    current = section(verification, "## Current Full Verification", "## Assessed Inputs")
    check("current verification names candidate 2f0b981c",
          "candidate 2f0b981c" in current and "FULL Tester gate PASSED" in current)

    for key in ("implementation", "final"):
        findings = re.findall(r"^### (F-\d{3})[^\n]*\n\n`Severity`: `(\w+)` `Status`: `(\w+)`",
                              texts[key], flags=re.M)
        check(f"{key} review COMPLETE with every finding RESOLVED",
              field(texts[key], "Status") == "COMPLETE" and findings
              and all(status == "RESOLVED" for _, _, status in findings), findings)

    documentation = texts["documentation"]
    entries = re.findall(r"^### (DOC-\d{3})[^\n]*\n\n`Status`: `(\w+)`", documentation, flags=re.M)
    check("documentation COMPLETE, style tony, every DOC entry RESOLVED",
          field(documentation, "Status") == "COMPLETE"
          and field(documentation, "User Style") == "tony" and entries
          and all(status == "RESOLVED" for _, status in entries), entries)
    check("selected Documenter style file exists",
          path(".standards/user-styles/documenter/tony.md").is_file())
    return texts


def check_state() -> None:
    """Workflow coordination needed for the SYNCHRONIZING rerun boundary."""

    state = text_of(STATE)
    expected = {"WorkflowState": "SYNCHRONIZING", "CycleMode": "STANDARD",
                "PendingCycleMode": "UNSET", "PendingCycleRequest": "UNSET",
                "PendingCycleBlockedOn": "NONE", "Id": CYCLE, "BlockedOn": "NONE",
                "PendingVerificationCadence": "NONE", "BaselineReconciliation": "NONE",
                "PromotionReason": "NONE", "AuditTarget": "NONE", "Kind": "FORWARD",
                "From": "REVIEWING_FINAL", "FailureType": "NONE"}
    observed = {name: field(state, name) for name in expected}
    check("STATE is SYNCHRONIZING after FORWARD from REVIEWING_FINAL with no blocker",
          observed == expected, observed)
    paths = {name: field(state, name) for name in ("Scope", "Architecture", "Development")}
    check("Active Work paths name this cycle's records",
          paths == {"Scope": RECORDS["scope"], "Architecture": RECORDS["spec"],
                    "Development": RECORDS["plan"]}, paths)
    frames = re.findall(r"^### Frame \d+", state, flags=re.M)
    frame = section(state, "### Frame 1", "## Outstanding Obligations")
    frame_fields = {name: field(frame, name)
                    for name in ("From", "Owner", "FailureType", "ResumeAt", "RerunThrough")}
    check("only Frame 1 (ARCHITECTING, ResumeAt AWAITING_USER_SIGNOFF, RerunThrough "
          "SYNCHRONIZING)",
          frames == ["### Frame 1"] and frame_fields == {
              "From": "AWAITING_USER_SIGNOFF", "Owner": "ARCHITECTING",
              "FailureType": "ARCHITECTURE", "ResumeAt": "AWAITING_USER_SIGNOFF",
              "RerunThrough": "SYNCHRONIZING"}, frame_fields)
    obligations = state.split("## Outstanding Obligations", 1)[1]
    check("outstanding obligations inactive", field(obligations, "Active") == "false")
    check("MODE is BROWNFIELD", field(text_of(MODE), "ProjectMode") == "BROWNFIELD")


def check_acceptance(texts: dict[str, str]) -> None:
    """Current acceptance inventory and its accounting in each completed record."""

    scope = texts["scope"]
    defined = re.findall(r"^\s*(?:[-*]|\d+\.)\s+`(AC-\d{3})`\s*[:\-–—]", scope, flags=re.M)
    check("scope defines exactly AC-001..AC-037 once each",
          len(defined) == 37 and set(defined) == EXPECTED_ACS, len(defined))
    check("scope has no retired identifiers or previous-cycle section",
          "## Retired Acceptance Identifiers" not in scope and "## Previous Cycles" not in scope)
    slices = {
        "spec Acceptance Coverage": section(texts["spec"], "## Acceptance Coverage",
                                            "## Components"),
        "verification current Acceptance Evidence": section(
            texts["verification"], "## Acceptance Evidence", "## Scenario Budget"),
        "implementation current assessment": section(
            texts["implementation"], "## Contract and Evidence Assessment",
            "## Checks and Results"),
        "final review assessment": section(texts["final"], "## Contract and Evidence Assessment",
                                           "## Checks and Results"),
        "documentation Frame 1 dispositions": section(
            texts["documentation"], "### Work and evidence (2026-10-07)",
            "### Checks (2026-10-07)"),
    }
    for name, text in slices.items():
        missing = sorted(EXPECTED_ACS - mentioned_acs(text))
        check(f"{name} accounts for all 37 current IDs", not missing, missing)
    criteria = section(texts["spec"], "## Technical Acceptance Criteria", "## Build Plan")
    technical = {f"AC-{n:03d}" for n in [*range(1, 25), *range(28, 36)]}
    check("technical criteria cover AC-001..AC-024 and AC-028..AC-035",
          technical <= mentioned_acs(criteria), sorted(technical - mentioned_acs(criteria)))
    frame1 = {"AC-019` (Frame 1", "AC-029` (Frame 1", "AC-016` (Frame 2", "AC-014` (nested Frame 2",
              "AC-015` (Frame 1"}
    missing = sorted(marker for marker in frame1 if marker not in criteria)
    check("Frame 1/2 technical criteria present for AC-013..AC-016, AC-019 and AC-029",
          not missing, missing)
    final = section(texts["final"], "## Contract and Evidence Assessment", "## Checks and Results")
    rows = [line for line in final.splitlines() if line.startswith("| AC-")]
    check("every final-review row is Supported",
          rows and all("Supported" in line.rsplit("|", 2)[1] for line in rows), len(rows))


def compare_map(name: str, recorded: dict[str, str], allowed: set[str]) -> None:
    """Rehash a recorded path->hash map; only explicitly allowed paths may differ."""

    differing = sorted(p for p, h in recorded.items()
                       if not path(p).is_file() or sha_file(p) != bare(h))
    check(name, set(differing) <= allowed,
          {"entries": len(recorded), "changed": differing,
           "unexpected": sorted(set(differing) - allowed)})


def receipt_ok(directory: str, label: str) -> tuple[bool, object]:
    """Exit and log hashes of a receipt in either owner format."""

    receipt = json.loads(text_of(f"{directory}/{label}.command.json"))
    expected = receipt.get("expectedExit", 0)
    if "logs" in receipt:
        logs = all(sha_file(log["path"]) == log["sha256"] for log in receipt["logs"].values())
    elif "stdoutSha256" in receipt:
        logs = (sha_file(f"{directory}/{label}.stdout") == bare(receipt["stdoutSha256"])
                and sha_file(f"{directory}/{label}.stderr") == bare(receipt["stderrSha256"]))
    else:
        logs = True  # Developer run_command receipts record exit only; logs are inspected below.
    return receipt["exitCode"] == expected and logs, {"exit": receipt["exitCode"],
                                                     "expected": expected, "logs": logs}


def check_review_receipts() -> None:
    """Final-review and implementation-review receipts still bind current content."""

    index = json.loads(text_of(f"{REVIEW_FINAL}/evidence-index.json"))
    check("final review assessed HEAD 87c3595 with a clean tree",
          index["head"] == FINAL_REVIEW_HEAD and index["trackedDirty"] == [])
    recorded = {entry["path"]: entry["sha256"] for entry in index["inputs"].values()}
    compare_map("final-review input identities match except STATE and this record",
                recorded, {STATE, SYNC_RECORD})
    for label in ("final-frame1-claims", "strict-build", "check-docs-copy", "pytest-suite",
                  "archive-closure-head"):
        ok, observed = receipt_ok(REVIEW_FINAL, label)
        check(f"final-review {label} receipt met its expected exit and logs match", ok, observed)
    check("final-review suite reports 117 passed",
          re.search(r"\b117 passed\b", text_of(f"{REVIEW_FINAL}/pytest-suite.stdout")) is not None)
    claims = json.loads(text_of(f"{REVIEW_FINAL}/final-frame1-claims-results.json"))
    FACTS["finalReviewClaimsKeys"] = sorted(claims)[:10]
    check("final-review checker copy output equals the Documenter results",
          sha_file(f"{REVIEW_FINAL}/check-docs-copy-results.json") == DOC_RESULTS_SHA
          == sha_file(f"{DOC_STYLE}/results.json"))

    recorded = {"behavior-head.json": "fe2f639b", "render-headroom-head.json": "ca00b7d1",
                "archive-closure-73455ff.json": "ee472c8a",
                "client-access-review-results-73455ff.json": "63d14b11",
                "check-frame1-behavior.py": "14e846ae", "check-render-headroom.py": "32b0536b",
                "check-archive-closure.py": "a40eb0cf"}
    mismatched = sorted(name for name, prefix in recorded.items()
                        if not sha_file(f"{REVIEW_IMPL}/{name}").startswith(prefix))
    check("implementation-review diagnostics match the hashes in its report", not mismatched,
          mismatched)


def check_documenter_receipts() -> None:
    """Documenter's final identities and checks still bind current content."""

    inputs = json.loads(text_of(f"{DOC_STYLE}/final-inputs.json"))
    compare_map("Documenter's 51 documentation identities unchanged", inputs["documentation"],
                set())
    compare_map("Documenter's six contract identities unchanged", inputs["contracts"], set())
    compare_map("Documenter's style-rework evidence unchanged",
                {f"{DOC_STYLE}/{name}": h for name, h in inputs["evidence"].items()}, set())
    check("Documenter binding names the current candidate",
          inputs["candidate"]["path"] == FINAL and bare(inputs["candidate"]["sha256"]) == FINAL_SHA)
    tracked = {p for p in git("ls-files", "docs", "README.md", "backend/README.md",
                              "packaging/mcpb/README.md", "mkdocs.yml").split()
               if not p.endswith((".js", ".css", ".png", ".svg", ".ico"))}
    unlisted = sorted(tracked - set(inputs["documentation"]))
    check("no tracked documentation page is missing from the Documenter binding", not unlisted,
          unlisted)
    commands = json.loads(text_of(f"{DOC_STYLE}/commands.json"))["commands"]
    check("Documenter style-rework commands all exited 0",
          len(commands) == 4 and all(c["exitCode"] == 0 for c in commands),
          [c["exitCode"] for c in commands])
    # The Frame 1 stale-phrase scan is an rg search whose exit 1 means "no matches", the
    # expected absence its note records; every other command must exit 0.
    frame1 = json.loads(text_of(f"{DOC_FRAME1}/commands.json"))["commands"]
    check("Documenter Frame 1 commands met their expected exits",
          all(c["exitCode"] == 0 or (c["exitCode"] == 1 and Path(c["argv"][0]).name == "rg"
                                     and "expected absence" in c.get("note", ""))
              for c in frame1), [c["exitCode"] for c in frame1])


def check_tester_and_developer() -> None:
    """Tester E6 and Developer DEV-022 receipts bind the offered candidate."""

    check("Tester E6 assessed HEAD 108914e with a clean tree at entry and exit",
          text_of(f"{E6}/head.txt").strip() == TESTER_HEAD
          and text_of(f"{E6}/entry-status.txt").strip() == ""
          and text_of(f"{E6}/final-status.txt").strip() == "")
    labels = sorted(p.name.removesuffix(".command.json")
                    for p in path(E6).glob("*.command.json"))
    for label in labels:
        ok, observed = receipt_ok(E6, label)
        check(f"Tester E6 {label} exit 0 with matching logs", ok, observed)
    expected = {"ci-suite", "closure", "http", "stdio-repo", "stdio-stage", *(
        f"validate-{n}" for n in range(1, 7)), *(f"static-{name}" for name in (
            "black", "interrogate", "isort", "mypy-src", "mypy-tests", "pylint-src",
            "pylint-tests", "ruff-src", "ruff-tests"))}
    check("Tester E6 has every relied-on receipt", expected <= set(labels),
          sorted(expected - set(labels)))
    check("Tester E6 CI suite reports 117 passed",
          re.search(r"\b117 passed\b", text_of(f"{E6}/ci-suite.stdout")) is not None)
    stage_argv = json.loads(text_of(f"{E6}/stdio-stage.command.json"))["argv"]
    check("Tester E6 staged run used the offered bundle root",
          stage_argv[-2:] == ["--bundle-root", str(path(STAGE))], stage_argv[-2:])
    closure = json.loads(text_of(f"{E6}/closure.stdout").splitlines()[0])
    detail = json.loads(text_of(f"{E6}/closure.json"))
    check("Tester E6 closure binds the offered archive with no drift",
          closure["status"] == "passed" and closure["sourceDrift"] == {}
          and closure["archiveSha256"] == FINAL_SHA and closure["archiveFiles"] == 657
          and closure["manifestVersion"] == "0.4.0" and closure["stageUnchangedAfterStartup"]
          and closure["copyFiles"] == 138 and closure["copyReceiptSha256"] == COPY_RECEIPT_SHA
          and closure["shippedReadme"]["sha256"] == README_SHA,
          {k: closure[k] for k in ("status", "archiveFiles", "manifestVersion")})
    FACTS["testerDeltaFrom01df98e1"] = detail["changedFromVerified01df98e1"]

    runs = {"e6StdioStage": json.loads(text_of(f"{E6}/stdio-stage.stdout")),
            "e6StdioRepository": json.loads(text_of(f"{E6}/stdio-repo.stdout")),
            "e6LoopbackHttp": json.loads(text_of(f"{E6}/http.json")),
            "developerStdioStage": json.loads(text_of(f"{DEV_CHECKS}/stdio-stage.stdout")),
            "developerStdioRepository": json.loads(text_of(f"{DEV_CHECKS}/stdio-repo.stdout")),
            "developerLoopbackHttp": json.loads(text_of(f"{DEV_CHECKS}/http.json"))}
    for name, run in runs.items():
        counts = [run[k] for k in ("toolCount", "promptCount", "fixedResourceCount",
                                   "resourceTemplateCount", "resourceReadCount")]
        same = [k for k in TRANSPORT_KEYS if run[k] == runs["e6StdioStage"][k]]
        check(f"{name} passed 19/9/1/14/15 and equals the E6 staged run",
              run["status"] == "passed" and counts == [19, 9, 1, 14, 15]
              and same == TRANSPORT_KEYS, {"counts": counts, "equalKeys": same})
    discovery = runs["e6StdioStage"]["access"]["discovery"]
    check("staged smoke sees LP in all six snapshots and Nigeria 189/297",
          discovery == {"diagnosticBuildsTowards": 189, "diagnosticRelatesTo": 297,
                        "learningProgressionSnapshots": 6}, discovery)

    packages = json.loads(text_of(f"{E1}/packages.json"))
    check("Tester E1 six read-only package validations still describe unchanged packages",
          packages["status"] == "passed" and packages["packageCount"] == 6
          and not changed("e837818", "data/graph_packages"), packages["status"])
    for label in ("build-mcpb", "closure", "stdio-repo", "stdio-stage", "http-harness",
                  "transport-agreement", "inprocess-smoke", "regression"):
        ok, observed = receipt_ok(DEV_CHECKS, label)
        check(f"Developer {label} exit 0", ok, observed)
    check("Developer evidence index matches the plan",
          sha_file(f"{DEV_CHECKS}/evidence-index.json") == DEV_INDEX_SHA)


def repo_path(member: str) -> str:
    """Map an archive member to its repository source under the builder recipe."""

    fixed = {"README.md": "backend/README.md", "fastmcp.json": "backend/fastmcp.json",
             "manifest.json": "packaging/mcpb/manifest.json",
             "pyproject.toml": "backend/pyproject.toml", "uv.lock": "backend/uv.lock"}
    if member in fixed:
        return fixed[member]
    if member.startswith("src/"):
        return "backend/" + member
    if member.startswith(("config/profiles/", "config/prompts/", "data/graph_packages/")):
        return member
    return ""


def members_of(relative: str) -> tuple[list[zipfile.ZipInfo], dict[str, bytes]]:
    """File entries and their bytes in an archive."""

    with zipfile.ZipFile(path(relative)) as archive:
        infos = [i for i in archive.infolist() if not i.is_dir()]
        return infos, {i.filename: archive.read(i) for i in infos}


def check_candidate() -> None:
    """Independent closure of the offered archive against HEAD, stage and manifests."""

    data = path(FINAL).read_bytes()
    check("offered archive identity", sha_bytes(data) == FINAL_SHA and len(data) == FINAL_BYTES,
          {"sha256": sha_bytes(data), "bytes": len(data)})
    blobs = {}
    for line in git("ls-tree", "-r", "HEAD").splitlines():
        meta, name = line.split("\t", 1)
        blobs[name] = meta.split()[2]
    infos, members = members_of(FINAL)
    unsafe = [i.filename for i in infos
              if PurePosixPath(i.filename).is_absolute() or ".." in PurePosixPath(i.filename).parts
              or stat.S_ISLNK(i.external_attr >> 16)]
    check("657 unique safe non-symlink members",
          len(infos) == len(members) == 657 and not unsafe, unsafe[:5])
    unmapped = sorted(m for m in members if not repo_path(m))
    check("every member maps to a repository input", not unmapped, unmapped[:5])

    def blob(content: bytes) -> str:
        return hashlib.sha1(b"blob %d\0" % len(content) + content).hexdigest()

    not_head = sorted(m for m in members if blobs.get(repo_path(m)) != blob(members[m]))
    check("every member equals its committed HEAD blob", not not_head, not_head[:5])
    not_tree = sorted(m for m in members if path(repo_path(m)).read_bytes() != members[m])
    check("every member equals the working tree", not not_tree, not_tree[:5])
    roots = ("backend/src/", "config/profiles/", "config/prompts/", "data/graph_packages/")
    expected = {p for p in blobs if p.startswith(roots) and "__pycache__" not in p}
    expected |= {"backend/README.md", "backend/fastmcp.json", "packaging/mcpb/manifest.json",
                 "backend/pyproject.toml", "backend/uv.lock"}
    missing = sorted(expected - {repo_path(m) for m in members})
    check("no tracked runtime/config/package input is missing", not missing, missing[:5])

    stage_root = path(STAGE)
    stage = {str(p.relative_to(stage_root)): p for p in stage_root.rglob("*") if p.is_file()}
    stage_diff = sorted(m for m in members
                        if m not in stage or stage[m].read_bytes() != members[m])
    check("every member equals the retained stage", not stage_diff, stage_diff[:5])
    extras = sorted(p for p in stage if p not in members and p != ".mcpbignore"
                    and not p.startswith((".venv/", "src/kgfegmcp.egg-info/")))
    check("stage extras limited to .mcpbignore and startup environment", not extras, extras[:5])

    # The previous offered candidate was built at a87ae15's tree; the new one must differ
    # from it in exactly the archived files whose sources changed since then.
    check("previous candidate 01df98e1 preserved as history", sha_file(PREVIOUS) == PREVIOUS_SHA)
    _, previous = members_of(PREVIOUS)
    delta = sorted(m for m in set(members) | set(previous) if members.get(m) != previous.get(m))
    sources = set(changed(LAST_SYNC))
    expected_delta = sorted(m for m in members if repo_path(m) in sources)
    check("delta from 01df98e1 equals the archived sources changed since a87ae15 and the "
          "Tester's list", delta == expected_delta == sorted(FACTS["testerDeltaFrom01df98e1"]),
          {"delta": len(delta), "expected": len(expected_delta),
           "extra": sorted(set(delta) - set(expected_delta)),
           "missing": sorted(set(expected_delta) - set(delta))})
    readme = members["README.md"]
    text = readme.decode("utf-8")
    check("shipped README equals backend/README.md and states the 0.4.0 / 19-tool surface",
          sha_bytes(readme) == README_SHA == sha_file("backend/README.md")
          and "0.4.0" in text and "19 tools" in text and "17 tools" not in text)
    stale = re.compile(r"page of 25|pages of 25|at most 75|^Graph types:", re.I | re.M)
    check("shipped README makes no superseded page or discovery-format claim",
          not stale.search(text))
    check("archived manifest version 0.4.0",
          json.loads(members["manifest.json"])["version"] == "0.4.0")

    totals = {"buildsTowards": 0, "relatesTo": 0}
    packages = {}
    for name in sorted(m for m in members if m.endswith("/package_manifest.json")):
        manifest = json.loads(members[name])
        base = name.rsplit("/", 1)[0]
        bad = sorted(rel for rel, value in manifest["checksums"].items()
                     if f"{base}/{rel}" not in members
                     or sha_bytes(members[f"{base}/{rel}"]) != bare(value))
        shards = [k for k in manifest["artifacts"]["additionalArtifacts"]
                  if k.startswith("learningProgressionProvenanceShard")]
        packages[base] = {"checksums": len(manifest["checksums"]), "bad": bad,
                          "shards": len(shards),
                          "included": manifest.get("included_graph_types")
                          or manifest.get("includedGraphTypes")}
        totals["buildsTowards"] += manifest["counts"]["buildsTowardsRelationships"]
        totals["relatesTo"] += manifest["counts"]["relatesToRelationships"]
    check("six packages; every declared checksum matches archived bytes; 64 shards each",
          len(packages) == 6 and all(not p["bad"] and p["shards"] == 64
                                     for p in packages.values()), packages)
    check("archived package counts total 3,039 buildsTowards and 5,041 relatesTo",
          totals == {"buildsTowards": 3039, "relatesTo": 5041}, totals)


def check_copies() -> None:
    """Local copies still equal the first-step copy receipt (external originals not reread)."""

    receipt_path = f"{LP}/copy_receipt.json"
    receipt = json.loads(text_of(receipt_path))
    bad = []
    frameworks: dict[str, int] = {}
    for row in receipt["files"]:
        content = path(row["destinationPath"]).read_bytes()
        value = "sha256:" + sha_bytes(content)
        if not (len(content) == row["sizeBytes"] and value == row["destinationSha256"]
                == row["sourceSha256Before"] == row["sourceSha256After"]):
            bad.append(row["destinationPath"])
        frameworks[row["frameworkId"]] = frameworks.get(row["frameworkId"], 0) + 1
    check("138 local copies (6 x 23) equal the copy receipt",
          sha_file(receipt_path) == COPY_RECEIPT_SHA and len(receipt["files"]) == 138
          and sorted(frameworks.values()) == [23] * 6 and not bad, bad[:5])


def check_obsolete() -> None:
    """Removed surface, superseded workflow wording and history stay out of maintained content."""

    removed = re.compile(r"collect_progression_evidence|inferred_progression_hypothesis"
                         r"|progressionHeuristics|inferredProgressionHypothesis")
    stale_docs = re.compile(r"\b(seventeen|17)\s+(read-only\s+)?tools\b|0\.3\.1\.mcpb"
                            r"|kgfegmcp-0\.3\.1|prompt version `?1\.3\.0|page of 25|pages of 25"
                            r"|at most 75", re.I)
    # Development-history phrases the user asked to remove from public documentation.
    history = re.compile(r"\brework\b|first 0\.4\.0|Desktop testing of|rebuilt candidate"
                         r"|fixed in (the |version )?0\.4|not part of this release", re.I)
    docs = [path(p) for p in ("README.md", "backend/README.md", "packaging/mcpb/README.md",
                              "mkdocs.yml")]
    docs += sorted(path("docs").rglob("*.md"))
    runtime = [path(p) for p in git("ls-files", "backend/src", "config").splitlines()]
    runtime.append(path("packaging/mcpb/manifest.json"))
    smoke = path("backend/src/kgfegmcp/cli/smoke_access.py")
    hits, rejection_checks, history_hits = [], [], []
    for file in docs + runtime:
        lines = file.read_text(encoding="utf-8", errors="replace").splitlines()
        for number, line in enumerate(lines, 1):
            where = f"{file.relative_to(ROOT)}:{number}"
            if file in runtime and removed.search(line) and any(
                    "_expect_error(" in earlier for earlier in lines[max(0, number - 6):number]):
                # A smoke assertion that the removed name is rejected is AC-017 evidence.
                rejection_checks.append(where)
            elif removed.search(line) or (file in docs and stale_docs.search(line)):
                hits.append(where)
            elif file in runtime and file != smoke and re.search(r"page of 25|at most 75", line):
                hits.append(where)
            if file in docs and history.search(line):
                history_hits.append(where)
    check("no removed names, superseded page wording or stale inventory in maintained "
          "docs/runtime/config", not hits,
          {"files": len(docs) + len(runtime), "hits": hits[:10],
           "rejectionChecks": rejection_checks})
    check("no development-history phrases in public documentation", not history_hits,
          history_hits[:10])
    walkthrough = text_of("docs/getting-started/claude-clients.md")
    status = section(walkthrough, "| Surface |", "\n\n")
    check("Claude page status table separates user observations, prepared Desktop and untested "
          "claude.ai",
          "User observations" in status and "Prepared; not yet run in Desktop" in status
          and "Untested" in status and "passed" not in status.split("Claude Desktop", 1)[1])


def main() -> int:
    """Run every reconciliation group and persist the results."""

    FACTS["environment"] = {"python": platform.python_version(), "cwd": str(ROOT)}
    check_git()
    texts = check_records()
    check_state()
    check_acceptance(texts)
    check_review_receipts()
    check_documenter_receipts()
    check_tester_and_developer()
    check_candidate()
    check_copies()
    check_obsolete()
    FACTS["identities"] = {rel: sha_file(rel) for rel in
                           [CONTEXT, STATE, MODE, *RECORDS.values(), FINAL, "backend/README.md"]}
    OUT.write_text(json.dumps({"facts": FACTS, "failures": FAILURES}, indent=2) + "\n",
                   encoding="utf-8")
    print(json.dumps({"checks": sum(1 for v in FACTS.values()
                                    if isinstance(v, dict) and "pass" in v),
                      "failures": FAILURES}, indent=1))
    return 1 if FAILURES else 0


if __name__ == "__main__":
    sys.exit(main())
