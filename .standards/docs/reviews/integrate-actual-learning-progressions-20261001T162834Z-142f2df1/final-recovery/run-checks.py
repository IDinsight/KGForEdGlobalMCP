"""Capture local Reviewer diagnostics without modifying other owners' evidence."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import time

ROOT = Path(__file__).resolve().parents[5]
OUT = Path(__file__).resolve().parent
ENV = {"UV_OFFLINE": "1", "PYTHONDONTWRITEBYTECODE": "1", "PATHS_PROJECT_DIR": str(ROOT)}
UV = ["/Users/tzz/.local/bin/uv", "--directory", "backend", "run", "--locked", "--offline", "--no-sync"]
checks = [
    ("strict-build", UV + ["mkdocs", "build", "--strict", "--config-file", str(ROOT/"mkdocs.yml"),
                           "--site-dir", "/tmp/kgfegmcp-final-recovery-review-site"], 0),
    ("saved-examples", UV + ["python", str(OUT/"check-saved-examples.py")], 0),
    ("current-evidence", ["python3", str(OUT/"check-current-evidence.py")], 0),
]
for name, argv, expected in checks:
    receipt = OUT/(name+".command.json")
    assert not receipt.exists(), receipt
    start = time.monotonic()
    process = subprocess.run(argv, cwd=ROOT, env={**os.environ, **ENV}, text=True, capture_output=True)
    logs = {}
    for channel in ["stdout", "stderr"]:
        path = OUT/(name+"."+channel)
        path.write_text(getattr(process, channel))
        logs[channel] = {"path":str(path.relative_to(ROOT)),
                         "sha256":hashlib.sha256(path.read_bytes()).hexdigest()}
    record = {"argv":argv,"cwd":str(ROOT),"environment":ENV,"exitCode":process.returncode,
              "expectedExit":expected,"durationSeconds":round(time.monotonic()-start,3),"logs":logs}
    receipt.write_text(json.dumps(record,indent=2)+"\n")
    print(json.dumps({"name":name,"exit":process.returncode,"duration":record["durationSeconds"],
                      "receipt":str(receipt.relative_to(ROOT))}),flush=True)
    if process.returncode != expected:
        print(process.stderr,flush=True)
        raise SystemExit(process.returncode or 1)
