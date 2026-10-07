"""Run one Reviewer diagnostic and keep an exact receipt beside its logs.

Usage: python3 run_check.py <label> <expected-exit> -- <argv...>

The receipt records argv, cwd, the extra environment, exit status, duration and
SHA256 of the captured stdout/stderr. Existing receipts are never overwritten,
so superseded attempts stay as history under their own labels.
"""

# Standard Library
import hashlib
import json
import os
import subprocess
import sys
import tempfile
import time

from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]
OUT = Path(__file__).resolve().parent

# Offline locked environment; uv cache in the session temp directory because the
# sandbox cannot write the default user cache. No secrets are recorded.
ENV = {
    "PATHS_PROJECT_DIR": str(ROOT),
    "PYTHONDONTWRITEBYTECODE": "1",
    "UV_CACHE_DIR": str(Path(tempfile.gettempdir()) / "kgfegmcp-final-frame1-uv-cache"),
    "UV_OFFLINE": "1",
}


def main() -> int:
    """Execute the requested command and persist its receipt."""

    label, expected = sys.argv[1], int(sys.argv[2])
    assert sys.argv[3] == "--", "separate the command with --"
    argv = sys.argv[4:]
    receipt = OUT / f"{label}.command.json"
    assert not receipt.exists(), f"receipt already exists: {receipt}"
    start = time.monotonic()
    process = subprocess.run(
        argv, capture_output=True, check=False, cwd=ROOT, env={**os.environ, **ENV}, text=True
    )
    logs = {}
    for channel in ("stdout", "stderr"):
        path = OUT / f"{label}.{channel}"
        path.write_text(getattr(process, channel), encoding="utf-8")
        logs[channel] = {
            "path": str(path.relative_to(ROOT)),
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        }
    record = {
        "argv": argv,
        "cwd": str(ROOT),
        "durationSeconds": round(time.monotonic() - start, 3),
        "environment": ENV,
        "exitCode": process.returncode,
        "expectedExit": expected,
        "logs": logs,
    }
    receipt.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"label": label, "exit": process.returncode,
                      "seconds": record["durationSeconds"]}))
    return 0 if process.returncode == expected else 1


if __name__ == "__main__":
    raise SystemExit(main())
