"""Synchronizer reconciliation for the client-access rerun (standard library only).

Read-only for every owner artifact: it hashes and compares workflow records, owner
receipts, the final retained 0.4.0 candidate and Git state, then writes only
reconcile-results.json beside this file. It does not run tests, servers or models;
formal execution evidence stays with its owners and is checked here for identity and
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
STATE, MODE, CONTEXT = ".standards/STATE.md", ".standards/MODE.md", ".standards/CONTEXT.md"
SYNC_DIR = ".standards/docs/synchronization/"

LP = "data/source_artifacts/learning_progressions"
FINAL = f"{LP}/client-recovery-docs-dev022/kgfegmcp-0.4.0-client-recovery-docs.mcpb"
STAGE = f"{LP}/client-recovery-docs-dev022/bundle"
TESTED = f"{LP}/client-recovery-f001-dev022/kgfegmcp-0.4.0-client-recovery-f001.mcpb"
DEV_CHECKS = f"{LP}/client-recovery-docs-dev022/checks"
E1 = f"{LP}/tester/{CYCLE}/full-verification"
E3 = f"{LP}/tester/{CYCLE}/f002-reverify"
E4 = f"{LP}/tester/{CYCLE}/final-candidate"
REVIEW_EVIDENCE = f".standards/docs/reviews/{CYCLE}/client-access-final"
DOC_EVIDENCE = ".standards/docs/documentation/client-access-20261006"

# Identities stated in the owner records (plan, verification, reviews, documentation).
FINAL_SHA = "01df98e19c8cb89d312bfc9cfccff5f9ce43698000b5f341f212f633d407aec5"
FINAL_BYTES = 82_178_548
TESTED_SHA = "15c80166f186ce08628fd7ee170b095d9c6fe32730d19eed15818e1673885d72"
README_SHA = "9ce0fc15618949b402b2d6d6e3d82e9525369334e742c6f9621c0738043d4365"
DEV_INDEX_SHA = "03882557b100852bb957e5a012091012ea23a95adcd4d3e348e8d8e3926be973"
COPY_RECEIPT_SHA = "e61d67b053a237e8fce6be86842f32ed5b398a145fb223410443d475419ae8ea"
TESTER_EVIDENCE_TEST_PREFIX = "55367197"
FINAL_REVIEW_ENTRY_HEAD = "e837818766e44b87e14430304cb4a68628599ea3"
CANDIDATE_BUILD_HEAD = "4fb23fe"
RUNTIME_ASSESSED_HEAD = "a2ee9a0"
PRE_REPLAN_SIGNOFF = "19f47ae"
TRANSPORT_KEYS = ["inventory", "toolSchemaIdentities", "progressions", "resourceReads", "access"]
EXPECTED_ACS = {f"AC-{n:03d}" for n in range(1, 38)}

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
    """Text from the first heading line equal to `start` up to the next `end` heading."""

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


def check_git() -> None:
    """Repository state and the comparison ranges the owners assessed."""

    FACTS["head"] = git("rev-parse", "HEAD").strip()
    dirty = [line[3:] for line in git("status", "--porcelain=v1",
                                      "--untracked-files=all").splitlines()]
    check("only Synchronizer-owned files are dirty or untracked",
          all(p.startswith(SYNC_DIR) for p in dirty), dirty)
    check("index is empty", git("diff", "--cached", "--name-only") == "")
    check("no unmerged paths", git("ls-files", "-u") == "")

    allowed = {STATE, RECORDS["verification"], RECORDS["final"]}
    since_entry = git("diff", "--name-only", FINAL_REVIEW_ENTRY_HEAD, "HEAD").split()
    unexpected = [p for p in since_entry
                  if p not in allowed and not p.startswith(REVIEW_EVIDENCE + "/")]
    check("since final-review entry e837818 only STATE, verification, final review and its "
          "evidence changed", not unexpected, {"changed": len(since_entry),
                                                "unexpected": unexpected})
    outside = git("diff", "--name-only", CANDIDATE_BUILD_HEAD, "HEAD", "--", ".",
                  ":(exclude).standards").split()
    check("nothing outside .standards changed since the candidate build HEAD 4fb23fe",
          not outside, outside)
    runtime = git("diff", "--name-only", RUNTIME_ASSESSED_HEAD, "HEAD", "--", "backend/src",
                  "backend/pyproject.toml", "backend/uv.lock", "backend/fastmcp.json", "config",
                  "data/graph_packages", "packaging/mcpb/manifest.json", ".github").split()
    check("runtime/config/data/lock/manifest/CI unchanged since Tester-assessed a2ee9a0",
          not runtime, runtime)
    tests = git("diff", "--name-only", RUNTIME_ASSESSED_HEAD, "HEAD", "--",
                "backend/tests").split()
    evidence_test = "backend/tests/kgfegmcp/test_progression_evidence.py"
    check("only Tester's assessed evidence test changed in backend/tests since a2ee9a0",
          tests == [evidence_test]
          and sha_file(evidence_test).startswith(TESTER_EVIDENCE_TEST_PREFIX),
          {"changed": tests, "sha256": sha_file(evidence_test)})
    data = git("diff", "--name-only", PRE_REPLAN_SIGNOFF, "HEAD", "--", "data/graph_packages",
               "config", ".standards/CONTEXT.md").split()
    check("accepted packages, configuration and CONTEXT unchanged during the rework", not data,
          data)
    rework = git("diff", "--name-status", PRE_REPLAN_SIGNOFF, "HEAD", "--", ".",
                 ":(exclude).standards").splitlines()
    FACTS["reworkRange"] = {"base": PRE_REPLAN_SIGNOFF, "paths": len(rework),
                            "added": sum(1 for r in rework if r.startswith("A")),
                            "modified": sum(1 for r in rework if r.startswith("M")),
                            "other": [r for r in rework if r[0] not in "AM"]}


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

    plan = texts["plan"]
    steps = section(plan, "## Build Steps", "## Plan Notes")
    entries = re.split(r"^### (?=DEV-\d{3})", steps, flags=re.M)[1:]
    statuses = {entry[:7]: field(entry, "Status") for entry in entries}
    check("plan COMPLETE, AFTER_IMPLEMENTATION, Current Increment NONE",
          (field(plan, "Status"), field(plan, "Verification Cadence"),
           field(plan, "Current Increment")) == ("COMPLETE", "AFTER_IMPLEMENTATION", "NONE"))
    check("all 19 approved DEV steps are DONE",
          len(statuses) == 19 and set(statuses.values()) == {"DONE"}, statuses)

    verification = texts["verification"]
    check("verification COMPLETE, FULL/NONE",
          (field(verification, "Status"), field(verification, "Assessment Purpose"),
           field(verification, "Assessment Target")) == ("COMPLETE", "FULL", "NONE"))

    for key in ("implementation", "final"):
        findings = re.findall(r"^### (F-\d{3})[^\n]*\n\n`Severity`: `(\w+)` `Status`: `(\w+)`",
                              texts[key], flags=re.M)
        check(f"{key} review COMPLETE with every finding RESOLVED",
              field(texts[key], "Status") == "COMPLETE" and findings
              and all(status == "RESOLVED" for _, _, status in findings), findings)

    documentation = texts["documentation"]
    entries = re.findall(r"^### (DOC-\d{3})[^\n]*\n\n`Status`: `(\w+)`", documentation, flags=re.M)
    check("documentation COMPLETE with every DOC entry RESOLVED",
          field(documentation, "Status") == "COMPLETE" and entries
          and all(status == "RESOLVED" for _, status in entries), entries)
    return texts


def check_state() -> None:
    """Workflow coordination needed for the SYNCHRONIZING boundary."""

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
    frames = re.findall(r"^### Frame \d+", state, flags=re.M)
    frame = section(state, "### Frame 1", "## Outstanding Obligations")
    frame_fields = {name: field(frame, name)
                    for name in ("From", "Owner", "FailureType", "ResumeAt", "RerunThrough")}
    check("only Frame 1 (SCOPING, ResumeAt AWAITING_USER_SIGNOFF, RerunThrough SYNCHRONIZING)",
          frames == ["### Frame 1"] and frame_fields == {
              "From": "AWAITING_USER_SIGNOFF", "Owner": "SCOPING", "FailureType": "SCOPING",
              "ResumeAt": "AWAITING_USER_SIGNOFF", "RerunThrough": "SYNCHRONIZING"},
          frame_fields)
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
        "verification current section": section(
            texts["verification"], "## Current Full Verification",
            "## Historical Full Verification For Candidate"),
        "implementation current assessment": section(
            texts["implementation"], "## Contract and Evidence Assessment",
            "## Checks and Results"),
        "final review assessment": section(texts["final"], "## Contract and Evidence Assessment",
                                           "## Checks and Results"),
        "documentation current dispositions": section(
            texts["documentation"], "### Work and evidence (2026-10-06)",
            "### Checks (2026-10-06)"),
    }
    for name, text in slices.items():
        missing = sorted(EXPECTED_ACS - mentioned_acs(text))
        check(f"{name} accounts for all 37 current IDs", not missing, missing)
    criteria = section(texts["spec"], "## Technical Acceptance Criteria", "## Build Plan")
    technical = {f"AC-{n:03d}" for n in [*range(1, 25), *range(28, 36)]}
    check("technical criteria cover AC-001..AC-024 and AC-028..AC-035",
          technical <= mentioned_acs(criteria), sorted(technical - mentioned_acs(criteria)))


def compare_map(name: str, recorded: dict[str, str], allowed: set[str]) -> None:
    """Rehash a recorded path->hash map; only explicitly allowed paths may differ."""

    changed = sorted(p for p, h in recorded.items()
                     if not path(p).is_file() or sha_file(p) != bare(h))
    check(name, set(changed) <= allowed,
          {"entries": len(recorded), "changed": changed,
           "unexpected": sorted(set(changed) - allowed)})


def check_owner_receipts() -> None:
    """Reviewer, Documenter, Tester and Developer receipts still bind current content."""

    index = json.loads(text_of(f"{REVIEW_EVIDENCE}/evidence-index.json"))
    compare_map("final-review entry identities match except Tester/Reviewer/STATE updates",
                index["files"], {STATE, RECORDS["verification"], RECORDS["final"]})
    compare_map("final-review receipts unchanged", index["reviewerEvidence"], set())
    resume = json.loads(text_of(f"{REVIEW_EVIDENCE}/evidence-index-resume.json"))
    compare_map("final-review resume identities match except its own completion and STATE",
                resume["files"], {STATE, RECORDS["final"]})
    for label in ("pytest-suite", "strict-build", "check-docs-copy", "walkthrough-claims-corrected",
                  "final-candidate", "obsolete-scan", "f003-recheck"):
        receipt = json.loads(text_of(f"{REVIEW_EVIDENCE}/{label}.command.json"))
        logs_ok = all(sha_file(log["path"]) == log["sha256"]
                      for log in receipt["logs"].values())
        check(f"Reviewer {label} receipt met its expected exit and logs match",
              receipt["exitCode"] == receipt["expectedExit"] and logs_ok,
              {"exit": receipt["exitCode"], "expected": receipt["expectedExit"]})

    inputs = json.loads(text_of(f"{DOC_EVIDENCE}/inputs.json"))
    resume_inputs = json.loads(text_of(f"{DOC_EVIDENCE}/resume-inputs.json"))
    compare_map("Documenter's 51 documentation identities unchanged", inputs["documentation"],
                set())
    compare_map("Documenter contract identities match except plan/verification/final review",
                inputs["contracts"], {RECORDS["plan"], RECORDS["verification"], RECORDS["final"]})
    plan_resume = bare(resume_inputs["contractsChanged"][RECORDS["plan"]])
    check("plan equals Documenter's resume binding", sha_file(RECORDS["plan"]) == plan_resume,
          plan_resume)
    compare_map("Documenter checker/results receipts unchanged",
                {f"{DOC_EVIDENCE}/{name}": h for name, h in inputs["checker"].items()}, set())
    for command in resume_inputs["commands"]:
        log = command.get("stdout")
        if log and command.get("sha256"):
            check(f"Documenter resume log {log} matches and exited 0",
                  command["exitCode"] == 0
                  and sha_file(f"{DOC_EVIDENCE}/{log}") == bare(command["sha256"]))
    candidate = resume_inputs["candidate"]
    check("Documenter's resume binding names the final candidate and current README",
          bare(candidate["sha256"]) == FINAL_SHA and candidate["path"] == FINAL
          and bare(candidate["backendReadme"]) == sha_file("backend/README.md") == README_SHA,
          candidate)

    for label in ("closure", "stdio-stage"):
        receipt = json.loads(text_of(f"{E4}/{label}.command.json"))
        check(f"Tester E4 {label} exit 0 with matching logs",
              receipt["exitCode"] == 0
              and sha_file(f"{E4}/{label}.stdout") == receipt["stdoutSha256"]
              and sha_file(f"{E4}/{label}.stderr") == receipt["stderrSha256"],
              receipt["exitCode"])
    stage_argv = json.loads(text_of(f"{E4}/stdio-stage.command.json"))["argv"]
    check("Tester E4 staged run used the final bundle root",
          stage_argv[-2:] == ["--bundle-root", str(path(STAGE))], stage_argv[-2:])
    closure = json.loads(text_of(f"{E4}/closure.stdout").splitlines()[0])
    closure_detail = json.loads(text_of(f"{E4}/closure.json"))
    check("Tester E4 closure binds the final archive, no drift, README-only delta",
          closure["status"] == "passed" and closure["sourceDrift"] == {}
          and closure["archiveSha256"] == FINAL_SHA and closure["archiveFiles"] == 657
          and closure["manifestVersion"] == "0.4.0" and closure["stageUnchangedAfterStartup"]
          and closure["copyFiles"] == 138 and closure["copyReceiptSha256"] == COPY_RECEIPT_SHA
          and closure["shippedReadme"]["sha256"] == README_SHA
          and closure_detail.get("changedFromVerified15c80166") == ["README.md"],
          {k: closure[k] for k in ("status", "archiveFiles", "manifestVersion")})

    relied = ["ci-suite", "final-suite", "stdio-repo", "http", "closure", "isort", "black",
              "ruff-src", "ruff-tests", "interrogate", "mypy-src", "mypy-tests", "pylint-src",
              "pylint-tests"]
    for label in relied:
        receipt = json.loads(text_of(f"{E3}/{label}.command.json"))
        check(f"Tester E3 {label} exit 0 with matching logs",
              receipt["exitCode"] == 0
              and sha_file(f"{E3}/{label}.stdout") == receipt["stdoutSha256"]
              and sha_file(f"{E3}/{label}.stderr") == receipt["stderrSha256"],
              receipt["exitCode"])
    for label in ("ci-suite", "final-suite"):
        check(f"Tester E3 {label} reports 104 passed",
              "104 passed" in text_of(f"{E3}/{label}.stdout"))
    packages = json.loads(text_of(f"{E1}/packages.json"))
    receipt = json.loads(text_of(f"{E1}/packages.command.json"))
    check("Tester E1 six read-only package validations valid with no findings",
          receipt["exitCode"] == 0 and packages["status"] == "passed"
          and packages["packageCount"] == 6 and len(packages["checks"]) == 6
          and all(c["exitCode"] == 0 and c["result"]["isValid"] and not c["result"]["findings"]
                  and c["result"]["persisted"] is False for c in packages["checks"]),
          packages["status"])

    runs = {"e4StdioStage": json.loads(text_of(f"{E4}/stdio-stage.stdout")),
            "e3StdioRepository": json.loads(text_of(f"{E3}/stdio-repo.stdout")),
            "e3LoopbackHttp": json.loads(text_of(f"{E3}/http.json")),
            "developerStdioStage": json.loads(text_of(f"{DEV_CHECKS}/stdio-stage.stdout"))}
    for name, run in runs.items():
        counts = [run[k] for k in ("toolCount", "promptCount", "fixedResourceCount",
                                   "resourceTemplateCount", "resourceReadCount")]
        same = [k for k in TRANSPORT_KEYS if run[k] == runs["e4StdioStage"][k]]
        check(f"{name} passed 19/9/1/14/15 and equals the E4 staged run",
              run["status"] == "passed" and counts == [19, 9, 1, 14, 15]
              and same == TRANSPORT_KEYS, {"counts": counts, "equalKeys": same})

    for label in ("build-mcpb", "closure", "stdio-stage", "stage-agreement"):
        receipt = json.loads(text_of(f"{DEV_CHECKS}/{label}.command.json"))
        check(f"Developer {label} exit 0", receipt["exitCode"] == 0, receipt["exitCode"])
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


def check_candidate() -> None:
    """Independent closure of the final retained archive against HEAD, stage and manifests."""

    data = path(FINAL).read_bytes()
    check("final archive identity", sha_bytes(data) == FINAL_SHA and len(data) == FINAL_BYTES,
          {"sha256": sha_bytes(data), "bytes": len(data)})
    blobs = {}
    for line in git("ls-tree", "-r", "HEAD").splitlines():
        meta, name = line.split("\t", 1)
        blobs[name] = meta.split()[2]
    with zipfile.ZipFile(path(FINAL)) as archive:
        infos = [i for i in archive.infolist() if not i.is_dir()]
        members = {i.filename: archive.read(i) for i in infos}
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

    with zipfile.ZipFile(path(TESTED)) as archive:
        tested = {i.filename: archive.read(i) for i in archive.infolist() if not i.is_dir()}
    check("Tester-verified 15c80166 archive preserved as history",
          sha_file(TESTED) == TESTED_SHA)
    delta = sorted(m for m in set(members) | set(tested) if members.get(m) != tested.get(m))
    check("final differs from the verified 15c80166 archive only in README.md",
          delta == ["README.md"], delta)
    readme = members["README.md"]
    readme_text = readme.decode("utf-8")
    check("shipped README equals backend/README.md and states the 0.4.0 / 19-tool surface",
          sha_bytes(readme) == README_SHA == sha_file("backend/README.md")
          and "0.4.0" in readme_text and "19 tools" in readme_text
          and "17 tools" not in readme_text and "0.3.1" not in readme_text)
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
                          "shards": len(shards)}
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
    """Removed hypothesis surface and stale inventory stay absent from maintained content."""

    removed = re.compile(r"collect_progression_evidence|inferred_progression_hypothesis"
                         r"|progressionHeuristics|inferredProgressionHypothesis")
    stale = re.compile(r"\b(seventeen|17)\s+(read-only\s+)?tools\b|0\.3\.1\.mcpb|kgfegmcp-0\.3\.1"
                       r"|prompt version `?1\.3\.0", re.I)
    docs = [path(p) for p in ("README.md", "backend/README.md", "packaging/mcpb/README.md",
                              "mkdocs.yml")]
    docs += sorted(path("docs").rglob("*.md"))
    if path("examples").exists():
        docs += sorted(p for p in path("examples").rglob("*") if p.is_file())
    # Tracked files only: ignored local build metadata (for example egg-info) is not runtime.
    runtime = [path(p) for p in git("ls-files", "backend/src", "config").splitlines()]
    runtime.append(path("packaging/mcpb/manifest.json"))
    hits, rejection_checks = [], []
    for file in docs + runtime:
        lines = file.read_text(encoding="utf-8", errors="replace").splitlines()
        for number, line in enumerate(lines, 1):
            if file in runtime and removed.search(line) and any(
                    "_expect_error(" in earlier for earlier in lines[max(0, number - 6):number]):
                # A smoke assertion that the removed name is rejected is AC-017 evidence,
                # not a callable alias; record it separately instead of hiding it.
                rejection_checks.append(f"{file.relative_to(ROOT)}:{number}")
            elif removed.search(line) or (file in docs and stale.search(line)):
                hits.append(f"{file.relative_to(ROOT)}:{number}")
    check("no removed hypothesis names in maintained docs/runtime/config and no stale "
          "0.3.1/17-tool docs", not hits,
          {"files": len(docs) + len(runtime), "hits": hits[:10],
           "rejectionChecks": rejection_checks})


def main() -> int:
    """Run every reconciliation group and persist the results."""

    FACTS["environment"] = {"python": platform.python_version(), "cwd": str(ROOT)}
    check_git()
    texts = check_records()
    check_state()
    check_acceptance(texts)
    check_owner_receipts()
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
