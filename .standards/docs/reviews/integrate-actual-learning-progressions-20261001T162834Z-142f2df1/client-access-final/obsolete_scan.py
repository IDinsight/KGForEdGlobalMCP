"""Scan maintained user/maintainer docs for obsolete inventory, versions and removed names."""
import json, re, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[5]
PATTERN = re.compile(
    r"\b(seventeen|17)\s+(read-only\s+)?tools\b|0\.3\.1\.mcpb|kgfegmcp-0\.3\.1|prompt version `?1\.3\.0"
    r"|collect_progression_evidence|inferred_progression_hypothesis|progressionHeuristics"
    r"|inferredProgressionHypothesis", re.I)
targets = [ROOT / p for p in ("README.md", "backend/README.md", "packaging/mcpb/README.md", "mkdocs.yml")]
targets += sorted((ROOT / "docs").rglob("*.md")) + sorted((ROOT / "examples").rglob("*")) if (ROOT / "examples").exists() else sorted((ROOT / "docs").rglob("*.md"))
hits = []
for path in targets:
    if path.is_file():
        for number, line in enumerate(path.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
            if PATTERN.search(line):
                hits.append(f"{path.relative_to(ROOT)}:{number}: {line.strip()[:160]}")
print(json.dumps({"filesScanned": sum(1 for p in targets if p.is_file()), "hits": hits}, indent=1))
sys.exit(1 if hits else 0)
