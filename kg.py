"""In-memory registry over the exported curriculum graphs.

Serves find_standard_statement in the Learning Commons response shape
(fields verified against live captures in fixtures/, July 2026).
Errors are raised as ValueError with the bare sentence the server must return.
"""

import json
import re
import unicodedata
from pathlib import Path

SUBJECTS = ("Mathematics", "English Language Arts", "Science", "Social Studies", "Other")

_WORD_NUM = {"one": "1", "two": "2", "three": "3", "four": "4", "five": "5",
             "six": "6", "seven": "7", "eight": "8", "nine": "9", "ten": "10"}
_FR_GRADE = {"ci": "1", "cp": "2", "ce1": "3", "ce2": "4", "cm1": "5", "cm2": "6"}


def normalize_grade_label(label):
    """'Basic 5' -> '5', 'PRIMARY: THREE' -> '3', 'P2  Mathematics' -> '2', 'CE1' -> '3'."""
    if not label:
        return None
    s = label.strip().lower()
    fr = _FR_GRADE.get(re.sub(r"[^a-z0-9]", "", s))
    if fr:  # CE1's digit is not a grade — the lookup must win over digit extraction
        return fr
    m = re.search(r"\d+", s)
    if m:
        return str(int(m.group()))
    for w, n in _WORD_NUM.items():
        if re.search(r"\b" + w + r"\b", s):
            return n
    return None


def _stem(w):
    w = w.lower().rstrip("'\u2019")
    if w.endswith(("'s", "\u2019s")):
        w = w[:-2]
    if len(w) > 4 and w.endswith("ies"):
        return w[:-3] + "y"
    # "s" must beat "es": stripping "es" turns "sentences" into "sentenc",
    # which no singular query stem can reach
    for suf in ("ing", "ed", "s"):
        if len(w) > len(suf) + 2 and w.endswith(suf):
            return w[: -len(suf)]
    return w


def _tokens(text):
    text = unicodedata.normalize("NFC", text or "")
    return {_stem(t) for t in re.findall(r"[\w'’-]+", text, re.UNICODE)}


class Graph:
    def __init__(self, path: Path):
        data = json.loads(path.read_text())
        self.nodes = {n["id"]: n for n in data["nodes"]}
        self.framework = next(n for n in data["nodes"] if "StandardsFramework" in n["labels"])
        p = self.framework["properties"]
        self.jurisdiction = p.get("jurisdiction")
        self.subject = p.get("academic_subject")
        self.children = {}
        parent = {}
        for rel in data["relationships"]:
            if rel["type"] == "hasChild":
                self.children.setdefault(rel["start"], []).append(rel["end"])
                parent[rel["end"]] = rel["start"]
        self.items = [n for n in data["nodes"] if "StandardsFrameworkItem" in n["labels"]]
        self.has_codes = any(n["properties"].get("statement_code") for n in self.items)
        self.grades = {}
        self._stamp(self.framework["id"], None)
        self._toks = {n["id"]: _tokens(n["properties"].get("description")) for n in self.items}

    def _stamp(self, nid, inherited):
        p = self.nodes[nid]["properties"]
        own = [g for g in (normalize_grade_label(x) for x in p.get("grade_level") or []) if g]
        if own:
            inherited = own
        self.grades[nid] = inherited or []
        for c in self.children.get(nid, []):
            self._stamp(c, inherited)


class Registry:
    def __init__(self, manifest_path: Path):
        base = manifest_path.parent
        self.graphs = {}
        for m in json.loads(manifest_path.read_text()):
            g = Graph(base / m["path"])
            self.graphs[g.jurisdiction] = g

    def _matches(self, code, keywords, jurisdiction, academic_subject):
        """One matching implementation for the server and the query tests."""
        if academic_subject is not None and academic_subject not in SUBJECTS:
            allowed = ", ".join(f"'{s}'" for s in SUBJECTS)
            raise ValueError(f"Unknown academic subject '{academic_subject}'. Expected one of: {allowed}.")
        g = self.graphs.get(jurisdiction or "")
        if g is None:
            allowed = ", ".join(f"'{j}'" for j in self.graphs)
            raise ValueError(f"jurisdiction is required. Expected one of: {allowed}.")
        if academic_subject and academic_subject.lower() != (g.subject or "").lower():
            return g, []
        if code:  # code wins when both arrive, matching the hosted server
            if not g.has_codes:
                raise ValueError(f"Statement codes are not available for {g.jurisdiction}; "
                                 "search with keywords instead.")
            cl = code.lower()
            hits = [n for n in g.items
                    if (sc := (n["properties"].get("statement_code") or "").lower())
                    and (sc == cl or sc.startswith(cl + "."))]
        elif keywords:
            stems = {_stem(w) for k in keywords for w in re.findall(r"[\w'’-]+", k)}
            hits = [n for n in g.items if stems & g._toks[n["id"]]]
        else:
            raise ValueError("Provide one of `code` or `keywords`.")
        return g, hits

    def match_count(self, **kw):
        """True match count before the cap — used by the query tests, not the server."""
        return len(self._matches(**kw)[1])

    def find_standard_statement(self, code=None, keywords=None,
                                academic_subject=None, jurisdiction=None):
        g, hits = self._matches(code=code, keywords=keywords,
                                jurisdiction=jurisdiction, academic_subject=academic_subject)
        out = []
        for n in hits[:25]:
            p = n["properties"]
            item = {
                "academicSubject": p.get("academic_subject") or g.subject,
                "caseIdentifierUUID": p.get("case_identifier_uuid") or n["id"],
                "description": p.get("description"),
                "gradeLevels": g.grades.get(n["id"], []),
                "jurisdiction": p.get("jurisdiction") or g.jurisdiction,
                "statementCode": p.get("statement_code"),
            }
            subs = [{"caseIdentifierUUID": g.nodes[c]["properties"].get("case_identifier_uuid") or c,
                     "description": g.nodes[c]["properties"].get("description"),
                     "statementCode": g.nodes[c]["properties"].get("statement_code")}
                    for c in g.children.get(n["id"], [])]
            if subs:
                item["subStandards"] = subs
            out.append(item)
        return {"standards": out}
