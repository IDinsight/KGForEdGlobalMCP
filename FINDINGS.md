# Findings — Ghana / Nigeria / Rwanda standards over the Learning Commons MCP contract

What we observed while building and testing this server, in two parts: issues in the
source data and pipeline exports, and limitations of the Learning Commons (CZI) API
contract itself. Every claim here was verified against the data files or against the
live Learning Commons server; the recordings in `fixtures/` and the tests in
`test_contract.py` are the audit trail.

## Part 1 — Data and pipeline observations

For each item: what we saw, what it breaks, what this package does about it, and what
the upstream fix would be. Our converter only ever compensates; it never edits
descriptions, invents codes, or restructures the tree.

**1. Eleven Ghana standards have an empty `statement_code` with the real code
embedded in the description text.**
The extractor fails when a code deviates from the clean pattern — a trailing period
("B5.1.1.3.5."), a missing space ("B5.3.4.1.1Tell…"), an interior space
("B5. 1.2.3.1"). The code stays in the text; the field stays null. Breaks: these
standards are invisible to code search, and any consumer that trusts the code field
undercounts families (B5.1.1.3 has five children, not four). In this package: the
converter populates `statement_code` from the description when the field is null and
the description starts with a parseable code (normalizing the stray spacing and
punctuation); the description itself is untouched. Upstream fix: harden the code
tokenizer in extraction.

**2. Fourteen Ghana standards are attached directly to the framework root because
their parent sub-strands were lost in extraction.**
Whole sub-strand headers (e.g. B5 Number Sub-Strands 2, 4, 5) never became nodes —
likely the "CONT'D" table-continuation pages — so their content standards had no
parent to attach to. The pipeline handled this honestly: it parked them at the root
with `unresolved_root_fallback: true`, and each edge's `llm_reason` metadata names
the exact missing parent. Breaks: wrong tree position in any hierarchy view; no
grade ancestor to inherit from. In this package: grade is recovered from each
standard's own code (B5.… → grade 5); we deliberately do not re-parent or invent
sub-strand nodes. Upstream fix: emit the missing sub-strand headers (the pipeline's
own logs say which ones), and consider a validation rule: every ancestor a
statement code implies must exist.

**3. Roughly 90% of items ship with an empty `grade_level`.**
Grade lives only on Grade-type ancestor nodes. The Learning Commons API returns
`gradeLevels` on every standard, and grade is how consumers tell near-identical
standards apart across years — so per-item grades are load-bearing, not cosmetic.
In this package: the converter copies grade down from the nearest Grade ancestor.
Upstream fix: stamp grade on every item at export time.

**4. Grade labels are inconsistent within single files.**
"PRIMARY ONE", "PRIMARY: THREE", "primary two", "P2  Mathematics" (double space).
In this package: normalized to plain numerals ("3"), with the original kept in a
`local_grade_label` field. Upstream fix: normalize at export.

**5. Duplicate objectives, both across and within grades.**
Nigeria: "find missing numbers in an open sentence" appears verbatim in grades 1
and 2 (plus a singular variant in grade 3), and some grade-1 objectives appear
twice within the same grade. Rwanda has within-grade duplicate pairs as well.
Breaks: lookups and citations are ambiguous; any expected-answer key must accept
sets. Upstream: worth checking whether the within-grade duplicates are intentional
(they look like extraction repeats).

**6. Descriptions carry transcription noise, concentrated in Rwanda.**
Verified examples: "difeferent", "corectlyfrom" (fused words), "substraction",
"writeb", "explaine", "writ" in Rwanda; "sfacts" in Ghana; "exchangin" in Nigeria —
roughly 1% of descriptions by a frequency-based scan, Rwanda most affected. This
matters more than a cosmetic typo normally would: consumers are told to quote
standards verbatim, so the noise is reproduced in teacher-facing documents as
official curriculum wording, and no automated check downstream can catch it,
because the graph is the ground truth every verification compares against. This
package deliberately does not correct description text. Upstream fix: a proofread
pass over extracted statements — the stored page/bbox provenance makes it cheap to
re-verify each flagged item against the source PDF.

**7. The bundle export format differs from the graph format your own tooling reads.**
The `academic_standards_kg_bundle_*` files are report-shaped (items, links,
validation tables); the server-consumable format is node/relationship graphs. The
conversion is lossless for curriculum content and this package includes it, but
exporting the graph dialect directly (or documenting the reshape) would remove a
step for every consumer.

**8. Two smaller notes.** Production country datasets living under `examples/`
reads as sample data — consider a `data/` home as more countries land. And the
self-minted standard identifiers resolve nowhere outside these files (unlike US
standards, whose identifiers point into public CASE registries) — worth a joint
decision with Learning Commons about identity for non-US frameworks, including
whether human-usable handles matter for the two countries with no statement codes.
