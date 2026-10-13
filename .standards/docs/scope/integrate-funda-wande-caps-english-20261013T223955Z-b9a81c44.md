<!-- STANDARDS
Artifact: SCOPE
Cycle: integrate-funda-wande-caps-english-20261013T223955Z-b9a81c44
-->

# Integrate CAPS English Home Language (Foundation Phase, Grades R-3)

## Goal

Serve South Africa's CAPS English Home Language curriculum for the Foundation
Phase (Grades R-3, Department of Basic Education, 2011) from the MCP server as a
seventh framework, alongside the six already served. The source is the completed
`KGForEdGlobal` run for document key
`c939a3a9dcce92ed61d970f4599ced6f2ddc425d1220eeeab9828472b878d24d`, prepared for
the Funda Wande partner programme. MCP clients should be able to discover the
framework and use its standards, learning components, and learning progressions
through the same tools and resources as the existing frameworks. The framework
must be rebuildable from inputs committed to this repository, as prior
frameworks are.

## Constraints

- The external source directory
  `/Users/tzz/Projects/private/idi/KGForEdGlobal/results/kg_for_ed/c939a3a9dcce92ed61d970f4599ced6f2ddc425d1220eeeab9828472b878d24d/`
  is read-only. Only the 23 files required for preparation are consumed, through
  a verified copy receipt, following the operator guide in
  `docs/development/framework-package.md`.
- Adding the framework is a data and configuration change. Python changes are
  allowed only for a reusable, framework-generic capability. Runtime code must
  not branch on framework identity, and validation must not be weakened to admit
  this framework.
- Accepted packages are immutable. The six existing packages stay unchanged, and
  each framework keeps one unambiguous current snapshot.
- The repository stays plain git with no Git LFS (user decision, 2026-10-13).
  GitHub rejects files over 100 MB, so no committed file may exceed that size.
  The CAPS evidence that existing input sets retain must still be retained in
  full. Architect chooses how to meet this.
- Rights posture matches the six existing frameworks (user decision,
  2026-10-13): source licence `Unknown`, review status
  `provisional_operator_approved`, full text and standard resources allowed,
  bulk resources disallowed. The attribution statement credits the Department of
  Basic Education.
- Funda Wande appears only in the maintained input set's label, following the
  partner-programme naming precedent (`madhi_math`, `pratham_science`). The
  framework identity, profile, and attribution follow the source authority, DBE
  (user decision, 2026-10-13).
- Current contract versions apply: manifest `1.1`, delivery `1.2`, source `1.0`,
  profile version `2.0`, prompt-config version `2.0.0`. Framework and profile
  IDs follow the `<country>-<authority>-<subject>-<grade-band>` slug convention.
- Package receipts expose only relative paths and hashes. The local copy receipt
  under the git-ignored `data/source_artifacts/` may keep private paths.
- Every served package ships in the MCPB bundle and must validate there under
  `KGFEGMCP_INVALID_PACKAGE_POLICY=fail`.

## Non-goals

- Changing the external `KGForEdGlobal` pipeline or its artifacts, or
  re-running extraction, AS/LC construction, or LP generation.
- Editing the CAPS graph content (standards, learning components, or
  relationships) beyond what the existing generic preparation produces.
- Changing the content or behavior of the six existing frameworks.
- New MCP tools, resources, or changes to tool contracts.
- Clearing the CAPS licence or certifying pedagogical quality. Package
  acceptance remains a structural and process-integrity check.
- Adopting Git LFS or any external storage for repository data.
- CAPS First Additional Language, other phases, or other CAPS subjects.
- Release versioning, which release-please handles.

## Work

### 1. Maintained CAPS input set

**Intent:** Keep the CAPS rebuild inputs in the repository so anyone can rebuild
and audit the package from a fresh clone, as with the existing frameworks.

**Done when:**

- `AC-001`: A maintained input set for CAPS English, labelled after the Funda
  Wande partner programme, exists under `data/input_artifacts/`. It has the
  layout of the existing sets (`delivery/`, `detailed/`, `additional/`,
  `package_build.json`) and was prepared from the 23 required source files via
  a verified copy receipt. The external source directory is unchanged.
- `AC-002`: No file committed by this cycle exceeds 100 MB, and the repository
  introduces no Git LFS configuration or other non-plain-git storage.
- `AC-003`: Every evidence category the existing input sets retain is retained
  for CAPS without dropped content. This includes the LP final claims, LP
  relationship provenance, and `relatesTo` relationships, and each can be
  recovered from committed files with content identical to the prepared
  output.

**Depends on:** The external CAPS run artifacts (read-only).

### 2. Accepted CAPS graph package

**Intent:** Give the runtime an immutable, validated package for CAPS, the only
form of data it serves.

**Done when:**

- `AC-004`: A CAPS package built from the maintained input set exists under
  `data/graph_packages/<framework-id>/<snapshot-id>/`. It reaches terminal
  status `passed` under the unchanged validation rules, and it is the
  framework's only current snapshot.
- `AC-005`: The framework ID follows the `<country>-<authority>-<subject>-<grade-band>`
  convention and identifies South Africa, the Department of Basic Education,
  English Home Language, and Foundation Phase Grades R-3.
- `AC-006`: The package's content matches the source graph. It holds 1,144
  standards items across Grades R, 1, 2, and 3 as a strict single-parent tree,
  912 learning components, and 9,587 learning-progression edges (2,879
  `buildsTowards`, 6,708 `relatesTo`). Grade labels keep `Grade R` distinct.
- `AC-007`: Package receipts and other committed package files contain no
  absolute or private local source paths.
- `AC-008`: Rebuilding from the committed maintained input set in a fresh clone
  reproduces the accepted package's snapshot identity and checksums.

**Depends on:** 1, 3.

### 3. CAPS interpretation profile and prompt configuration

**Intent:** Define how the runtime interprets and presents CAPS, matching its
real structure and the agreed rights posture.

**Done when:**

- `AC-009`: A profile at version `2.0` and a prompt configuration at version
  `2.0.0` exist for the CAPS framework and load without errors. The profile
  describes the hierarchy Grade, Term, Skill Area, Sub-strand, Skill, and
  claims no code-based search, because no CAPS item has a statement code.
- `AC-010`: The profile's rights block sets source licence `Unknown`, review
  status `provisional_operator_approved`, full text and standard resources
  allowed, and bulk resources disallowed. Its attribution statement credits the
  Department of Basic Education's 2011 CAPS English Home Language Foundation
  Phase curriculum. Funda Wande is not named in the framework ID, profile, or
  attribution.

**Depends on:** None.

### 4. CAPS served through the MCP server

**Intent:** MCP clients can use CAPS exactly as they use the other frameworks.

**Done when:**

- `AC-011`: Framework discovery lists CAPS English alongside the six existing
  frameworks, seven in total.
- `AC-012`: Standards search, hierarchy context, learning components,
  comparison, and learning-progression search, get, and traverse each return
  correct CAPS results when targeted at the CAPS framework.
- `AC-013`: CAPS resources allowed by its rights policy can be read with
  default runtime configuration, without raising any default size limit.
- `AC-014`: The six existing frameworks behave as before. Their packages are
  byte-identical, and their regression baselines still pass. Test expectations
  change only where they count the whole served population.
- `AC-015`: Runtime code has no framework-specific branches. Any Python change
  is a framework-generic capability, and no validation rule is relaxed.

**Depends on:** 2, 3.

### 5. Quality gates and distribution

**Intent:** The integration passes every project check and ships in the bundle.

**Done when:**

- `AC-016`: With CAPS included, the full test suite, lint, format, type, and
  docstring-coverage checks pass, and the repository STDIO smoke passes.
- `AC-017`: An MCPB stage builds with CAPS included under the fail policy for
  invalid packages, and the stage STDIO smoke passes.

**Depends on:** 4.

### 6. Documentation

**Intent:** Operators and users can find CAPS in the project documentation, and
operators can rebuild it.

**Done when:**

- `AC-018`: The framework-facing documentation that lists current frameworks
  includes CAPS English with its correct identity, grades, and DBE attribution.
  This covers `README.md`, `backend/README.md`, the framework catalog,
  manifest, profile, and prompt-config pages, and the retained-input table in
  `docs/development/framework-package.md`.
- `AC-019`: `docs/development/framework-package.md` correctly describes how
  evidence files over GitHub's size limit are retained and recovered for
  rebuild.
- `AC-020`: The MkDocs site builds in strict mode.

**Depends on:** 4; `AC-019` also depends on 1.

## Assumptions

- All four grades in the source (R, 1, 2, 3) are served. The source filename
  mentions Grade 3, but the graph covers the whole Foundation Phase.
- The empty `.lp_generation.lock` in the external run directory is stale, since
  `kg_run.json` records a completed run. The artifacts are final.
- Landing the work as the two-commit precedent ("enable learning progressions"
  plus "add input artifacts") is a convention, not an acceptance condition.
