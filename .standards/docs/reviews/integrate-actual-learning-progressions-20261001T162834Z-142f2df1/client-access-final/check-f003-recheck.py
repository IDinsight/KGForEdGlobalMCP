"""Reviewer recheck of F-003 against Tester's E4 evidence (standard library only).

Confirms, without modifying anything:
- the final archive still hashes to 01df98e1 and every member still equals its stage file;
- E4 receipts exit 0, their log hashes match, and the staged run used the final bundle;
- E4 staged STDIO equals Tester's f002 repository STDIO and loopback HTTP, and the
  Developer's earlier staged run of the same bundle, on inventory, schema identities,
  progression queries, native reads and the access suite;
- E4 closure binds the final archive, empty source drift and README-only delta.
Writes f003-recheck-results.json beside this file; exits 1 on any failed check.
"""

# Standard Library
import hashlib
import json
import sys
import zipfile

from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]
OUT = Path(__file__).resolve().parent / "f003-recheck-results.json"
LP = ROOT / "data/source_artifacts/learning_progressions"
CYCLE = "integrate-actual-learning-progressions-20261001T162834Z-142f2df1"
E3 = LP / "tester" / CYCLE / "f002-reverify"
E4 = LP / "tester" / CYCLE / "final-candidate"
FINAL = LP / "client-recovery-docs-dev022/kgfegmcp-0.4.0-client-recovery-docs.mcpb"
STAGE = LP / "client-recovery-docs-dev022/bundle"
KEYS = ["inventory", "toolSchemaIdentities", "progressions", "resourceReads", "access"]
FAILURES: list[str] = []
FACTS: dict[str, object] = {}


def check(name: str, ok: bool, observed: object = None) -> None:
    """Record one outcome without stopping."""

    FACTS[name] = {"pass": bool(ok), "observed": observed}
    if not ok:
        FAILURES.append(name)


def sha(path: Path) -> str:
    """Hex SHA256 of a file."""

    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    """Run the recheck."""

    archive_sha = sha(FINAL)
    check("final archive unchanged (01df98e1)", archive_sha.startswith("01df98e1"), archive_sha)
    with zipfile.ZipFile(FINAL) as archive:
        names = [n for n in archive.namelist() if not n.endswith("/")]
        differing = [n for n in names if (STAGE / n).read_bytes() != archive.read(n)]
    check("all 657 archive members still equal the stage", len(names) == 657 and not differing,
          differing[:5])

    for label in ("closure", "stdio-stage"):
        receipt = json.loads((E4 / f"{label}.command.json").read_text())
        check(f"E4 {label} exit 0", receipt.get("exitCode") == 0, receipt.get("exitCode"))
        for channel in ("stdout", "stderr"):
            recorded = receipt.get(f"{channel}Sha256")
            if recorded:
                check(f"E4 {label} {channel} hash matches receipt",
                      sha(E4 / f"{label}.{channel}") == recorded, recorded)
    stage_argv = json.loads((E4 / "stdio-stage.command.json").read_text())["argv"]
    check("E4 staged run used the final bundle", stage_argv[-1] == str(STAGE), stage_argv[-1])

    runs = {
        "e4StdioStage": json.loads((E4 / "stdio-stage.stdout").read_text()),
        "e3StdioRepository": json.loads((E3 / "stdio-repo.stdout").read_text()),
        "e3Http": json.loads((E3 / "http.json").read_text()),
        "developerStdioStageSameBundle": json.loads(
            (LP / "client-recovery-docs-dev022/checks/stdio-stage.stdout").read_text()),
    }
    for name, run in runs.items():
        counts = [run[k] for k in ("toolCount", "promptCount", "fixedResourceCount",
                                   "resourceTemplateCount", "resourceReadCount")]
        check(f"{name} passed with 19/9/1/14/15", run["status"] == "passed"
              and counts == [19, 9, 1, 14, 15], counts)
        for key in KEYS:
            check(f"{name} {key} equals E4 staged run", run[key] == runs["e4StdioStage"][key])

    closure = json.loads((E4 / "closure.json").read_text())
    check("E4 closure binds the final archive with empty drift and README-only delta",
          closure["archiveSha256"] == archive_sha and closure["sourceDrift"] == {}
          and closure["changedFromVerified15c80166"] == ["README.md"]
          and closure["readmeCurrent"] is True and closure["stageUnchangedAfterStartup"] is True,
          {k: closure[k] for k in ("status", "changedFromVerified15c80166", "manifestVersion")})

    OUT.write_text(json.dumps({"facts": FACTS, "failures": FAILURES}, indent=2) + "\n",
                   encoding="utf-8")
    print(json.dumps({"checks": len(FACTS), "failures": FAILURES}))
    return 1 if FAILURES else 0


if __name__ == "__main__":
    sys.exit(main())
