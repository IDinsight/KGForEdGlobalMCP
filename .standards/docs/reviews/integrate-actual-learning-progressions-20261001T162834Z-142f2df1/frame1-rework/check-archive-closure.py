"""Reviewer diagnostic: retained 0.4.0 candidate members equal committed HEAD blobs.

Independent supporting evidence for IMPLEMENTATION review (not formal Tester
evidence). Maps each archive member to its repository source with the MCPB
builder recipe convention (backend/ for runtime files, config/, data/graph_packages/,
packaging/mcpb/ for the manifest) and compares bytes with ``git show HEAD:<path>``.
Usage (repository root): python3 <this file> <archive>
"""

import hashlib
import json
import subprocess
import sys
import zipfile

archive = sys.argv[1]
head = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True, check=True).stdout.strip()
tracked = set(subprocess.run(["git", "ls-files"], capture_output=True, text=True, check=True).stdout.split("\n"))
# The builder ships backend/README.md as README.md and packaging/mcpb/manifest.json.
candidates = lambda m: ["backend/README.md"] if m == "README.md" else [m, "backend/" + m, "packaging/mcpb/" + m]
equal, unmatched, differs = 0, [], []
with zipfile.ZipFile(archive) as zf:
    names = [n for n in zf.namelist() if not n.endswith("/")]
    for name in names:
        data = zf.read(name)
        for path in candidates(name):
            if path in tracked:
                blob = subprocess.run(["git", "show", f"HEAD:{path}"], capture_output=True, check=True).stdout
                if blob == data:
                    equal += 1
                else:
                    differs.append(path)
                break
        else:
            unmatched.append(name)
    manifest = json.loads(zf.read("manifest.json"))
digest = hashlib.sha256(open(archive, "rb").read()).hexdigest()
runtime_tracked = sorted(
    p for p in tracked
    if (p.startswith("backend/src/") and "/__pycache__/" not in p) or p.startswith("config/") or p.startswith("data/graph_packages/")
)
member_set = set(names)
missing = [p for p in runtime_tracked if not ({p, p.removeprefix("backend/")} & member_set)]
result = {"head": head, "archiveSha256": digest, "members": len(names), "equalToHead": equal,
          "differs": differs, "unmatched": unmatched, "trackedRuntimeMissing": missing,
          "manifestVersion": manifest.get("version")}
print(json.dumps(result, indent=1))
sys.exit(0 if not differs and not unmatched and not missing else 1)
