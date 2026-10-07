"""Reviewer diagnostic: reconcile the final retained 0.4.0 candidate with HEAD and history.

Standard library only (system python3). Checks, without modifying any file:
- the designated archive `client-recovery-docs-dev022` against committed HEAD blobs
  (builder recipe mapping), the working tree and its own retained stage;
- member-by-member difference from the Tester-verified `client-recovery-f001-dev022`
  archive (expected: README.md only);
- presence of all six package trees with 64 provenance shards each, manifest 0.4.0,
  shipped README content, and stage extras limited to startup-created environment files;
- Developer receipts for the rebuilt stage (exit codes and evidence-index hashes).
Writes final-candidate-results.json beside this file and exits 1 on any failed check.
"""

# Standard Library
import hashlib
import json
import subprocess
import sys
import zipfile

from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]
OUT = Path(__file__).resolve().parent / "final-candidate-results.json"
LP = ROOT / "data/source_artifacts/learning_progressions"
FINAL = LP / "client-recovery-docs-dev022/kgfegmcp-0.4.0-client-recovery-docs.mcpb"
FINAL_STAGE = LP / "client-recovery-docs-dev022/bundle"
TESTED = LP / "client-recovery-f001-dev022/kgfegmcp-0.4.0-client-recovery-f001.mcpb"
FAILURES: list[str] = []
FACTS: dict[str, object] = {}


def check(name: str, ok: bool, observed: object = None) -> None:
    """Record one named outcome; collect failures instead of stopping early."""

    FACTS[name] = {"pass": bool(ok), "observed": observed}
    if not ok:
        FAILURES.append(name)


def sha256(data: bytes) -> str:
    """Hex SHA256 of bytes."""

    return hashlib.sha256(data).hexdigest()


def git_blob_sha1(data: bytes) -> str:
    """Git object ID of a blob with these bytes."""

    return hashlib.sha1(b"blob %d\0" % len(data) + data).hexdigest()


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


def members(path: Path) -> dict[str, bytes]:
    """Read every file member of a ZIP archive."""

    with zipfile.ZipFile(path) as archive:
        return {i.filename: archive.read(i) for i in archive.infolist() if not i.is_dir()}


def main() -> int:
    """Run all reconciliation checks."""

    head = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, check=True,
                          cwd=ROOT, text=True).stdout.strip()
    tree = {}
    listing = subprocess.run(["git", "ls-tree", "-r", "HEAD"], capture_output=True,
                             check=True, cwd=ROOT, text=True).stdout
    for line in listing.splitlines():
        meta, path = line.split("\t", 1)
        tree[path] = meta.split()[2]
    FACTS["head"] = head

    final_bytes = FINAL.read_bytes()
    final = members(FINAL)
    tested = members(TESTED)
    FACTS["finalArchive"] = {"path": str(FINAL.relative_to(ROOT)), "sha256": sha256(final_bytes),
                             "bytes": len(final_bytes), "members": len(final)}
    FACTS["testedArchive"] = {"path": str(TESTED.relative_to(ROOT)),
                              "sha256": sha256(TESTED.read_bytes()), "members": len(tested)}
    check("final archive sha256 is the designated 01df98e1 candidate",
          sha256(final_bytes).startswith("01df98e1"), sha256(final_bytes))

    unmapped = sorted(m for m in final if not repo_path(m))
    check("every archive member maps to a repository source", not unmapped, unmapped)
    not_head = sorted(m for m in final if repo_path(m)
                      and tree.get(repo_path(m)) != git_blob_sha1(final[m]))
    check("every archive member equals its committed HEAD blob", not not_head, not_head[:10])
    not_work = sorted(m for m in final if repo_path(m)
                      and (ROOT / repo_path(m)).read_bytes() != final[m])
    check("every archive member equals the working tree", not not_work, not_work[:10])

    # Every tracked runtime input under the recipe roots is shipped (no omission).
    roots = ("backend/src/", "config/profiles/", "config/prompts/", "data/graph_packages/")
    expected = {p for p in tree if p.startswith(roots) and "__pycache__" not in p}
    expected |= {"backend/README.md", "backend/fastmcp.json", "packaging/mcpb/manifest.json",
                 "backend/pyproject.toml", "backend/uv.lock"}
    shipped = {repo_path(m) for m in final}
    missing = sorted(expected - shipped)
    check("no tracked runtime/config/package input is missing from the archive", not missing,
          missing[:10])

    differing = sorted(m for m in set(final) | set(tested) if final.get(m) != tested.get(m))
    check("final differs from the Tester-verified f001 archive only in README.md",
          differing == ["README.md"], differing)

    stage_files = {str(p.relative_to(FINAL_STAGE)): p for p in FINAL_STAGE.rglob("*")
                   if p.is_file()}
    stage_diff = sorted(m for m in final if stage_files.get(m) is None
                        or stage_files[m].read_bytes() != final[m])
    check("every archive member equals the retained stage file", not stage_diff, stage_diff[:10])
    extras = sorted(p for p in stage_files if p not in final)
    allowed = (".venv/", "src/kgfegmcp.egg-info/")
    unexpected = sorted(p for p in extras if not p.startswith(allowed) and p != ".mcpbignore")
    check("stage extras are only .mcpbignore and startup-created .venv/egg-info", not unexpected,
          unexpected[:10])

    manifest = json.loads(final["manifest.json"])
    check("archived manifest version is 0.4.0", manifest.get("version") == "0.4.0",
          manifest.get("version"))
    readme = final["README.md"].decode("utf-8")
    check("shipped README states 19 tools and 0.4.0 without 17 tools/0.3.1",
          "19" in readme and "0.4.0" in readme and "17 tools" not in readme
          and "0.3.1" not in readme, sha256(final["README.md"]))
    packages = sorted({m.split("/")[2] for m in final if m.startswith("data/graph_packages/")})
    shards = {pkg: sum(1 for m in final if m.startswith(f"data/graph_packages/{pkg}/")
                       and "provenance_shard" in m.lower().replace("-", "_")) for pkg in packages}
    check("six package trees are shipped", len(packages) == 6, packages)
    FACTS["shardMembersPerPackage"] = shards

    # Developer receipts for the rebuilt stage.
    checks_dir = LP / "client-recovery-docs-dev022/checks"
    receipts = {}
    for receipt in sorted(checks_dir.glob("*.command.json")):
        data = json.loads(receipt.read_text())
        receipts[receipt.name] = data.get("exitCode", data.get("exit"))
    FACTS["developerReceipts"] = receipts
    index = checks_dir / "evidence-index.json"
    FACTS["developerEvidenceIndexSha256"] = sha256(index.read_bytes()) if index.exists() else None

    OUT.write_text(json.dumps({"facts": FACTS, "failures": FAILURES}, indent=2) + "\n",
                   encoding="utf-8")
    print(json.dumps({"failures": FAILURES, "final": FACTS["finalArchive"],
                      "shards": shards, "receipts": receipts}, indent=1))
    return 1 if FAILURES else 0


if __name__ == "__main__":
    sys.exit(main())
