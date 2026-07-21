"""Convert an academic-standards KG bundle into the export dialect the MCP server loads.

A bundle (produced by the backend's stage-5 export) is a report-shaped file:
    {framework, items[], relationships_has_child[], entity_provenance, summary, validation_report}
The export dialect (what `senegal_reading.json` uses) is graph-shaped:
    {export_dialect, graph_type, included_graph_types, nodes[], relationships[]}

Usage:
    python convert_bundle.py <bundle.json> [more bundles...]   # writes kg_export_<name>.json next to each
    python convert_bundle.py --manifest <dir>                  # scan dir for export-dialect files, write manifest.json
"""

import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

from kg import normalize_grade_label


def inherit_grades(nodes: list, relationships: list) -> None:
    """R1/R2: stamp normalized grade_level on every item, inherited from the nearest
    Grade-type ancestor; keep the country's own label in local_grade_label.
    R5: items with no Grade ancestor (Ghana's unresolved roots) fall back to the
    grade digit embedded in their statement code (B5.… -> "5")."""
    by_id = {n["id"]: n for n in nodes}
    children = {}
    for r in relationships:
        children.setdefault(r["start"], []).append(r["end"])
    root = next(n["id"] for n in nodes if "StandardsFramework" in n["labels"])

    def walk(nid, grade, label):
        p = by_id[nid]["properties"]
        own = p.get("grade_level") or []
        if p.get("statement_type") == "Grade" or own:
            raw = ", ".join(own) if own else (p.get("description") or "")
            norm = normalize_grade_label(raw)
            if norm:
                grade, label = norm, raw.strip()
        if "StandardsFrameworkItem" in by_id[nid]["labels"]:
            if grade is None and p.get("statement_code"):
                m = re.match(r"^[A-Za-z]*(\d)\.", p["statement_code"])
                if m:
                    grade = m.group(1)
            if grade is not None:
                p["grade_level"] = [grade]
                if label:
                    p["local_grade_label"] = label
        for c in children.get(nid, []):
            walk(c, grade, label)

    walk(root, None, None)


CODE_IN_DESC = re.compile(r"^\s*(B\s*\d(?:\s*\.\s*\d+)+)")


def recover_codes(items: list) -> None:
    """Eleven Ghana standards carry their code only in the description (extraction fails
    on trailing periods and stray spaces, e.g. 'B5. 1.2.3.1') — populate the field
    from the item's own text; the description is untouched. See FINDINGS.md #1."""
    for item in items:
        if not item.get("statement_code"):
            m = CODE_IN_DESC.match(item.get("description") or "")
            if m:
                item["statement_code"] = re.sub(r"\s+", "", m.group(1)).rstrip(".")
                item["code_recovered_from_description"] = True


def bundle_to_export(bundle: dict) -> dict:
    fw = bundle["framework"]
    nodes = [{
        "id": fw["case_identifier_uuid"],
        "labels": ["StandardsFramework"],
        "properties": fw,
    }]
    for item in bundle["items"]:
        nodes.append({
            "id": item["case_identifier_uuid"],
            "labels": ["StandardsFrameworkItem"],
            "properties": item,
        })

    relationships = []
    for rel in bundle["relationships_has_child"]:
        props = {k: v for k, v in rel.items()
                 if k not in ("relationship_type", "source_entity_value", "target_entity_value")}
        relationships.append({
            "id": rel["identifier"],
            "type": rel["relationship_type"],
            "start": rel["source_entity_value"],
            "end": rel["target_entity_value"],
            "properties": props,
        })

    recover_codes([n["properties"] for n in nodes[1:]])
    inherit_grades(nodes, relationships)
    return {
        "export_dialect": "global_relaxed",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "graph_type": "academic_standards",
        "included_graph_types": ["academic_standards"],
        "source_summary": bundle.get("summary"),
        "nodes": nodes,
        "relationships": relationships,
    }


def write_manifest(kgs_dir: Path) -> Path:
    """Catalog the converter's own outputs (kg_export_*.json) by framework metadata."""
    entries = []
    for path in sorted(kgs_dir.glob("kg_export_*.json")):
        try:
            data = json.loads(path.read_text())
        except json.JSONDecodeError:
            continue
        if "nodes" not in data:
            continue  # bundles and other shapes are skipped
        fw = next((n for n in data["nodes"] if "StandardsFramework" in n["labels"]), None)
        if fw is None:
            continue
        p = fw["properties"]
        entries.append({
            "name": p.get("name"),
            "jurisdiction": p.get("jurisdiction"),
            "academic_subject": p.get("academic_subject"),
            "in_language": p.get("in_language"),
            "included_graph_types": data.get("included_graph_types", []),
            "node_count": len(data["nodes"]),
            "path": path.name,
        })
    manifest_path = kgs_dir / "manifest.json"
    manifest_path.write_text(json.dumps(entries, indent=2, ensure_ascii=False))
    return manifest_path


def main(argv: list[str]) -> None:
    if not argv:
        sys.exit(__doc__)
    if argv[0] == "--manifest":
        path = write_manifest(Path(argv[1]))
        print(f"wrote {path}")
        return
    for arg in argv:
        src = Path(arg)
        bundle = json.loads(src.read_text())
        export = bundle_to_export(bundle)
        name = src.stem.replace("academic_standards_kg_bundle_", "")
        dst = src.parent / f"kg_export_{name}.json"
        dst.write_text(json.dumps(export, ensure_ascii=False))
        print(f"{src.name} -> {dst.name}: {len(export['nodes'])} nodes, "
              f"{len(export['relationships'])} relationships")


if __name__ == "__main__":
    main(sys.argv[1:])
