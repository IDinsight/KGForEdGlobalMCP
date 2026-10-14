<!-- STANDARDS
Artifact: SCOPE
Cycle: integrate-the-caps-english-curriculum-kg-20261014T193052Z-d6b750d3
-->

# Integrate CAPS English Home Language (Grades R-3)

## Goal

Serve the South African CAPS English Home Language, Foundation Phase, Grades R-3
curriculum knowledge graph as a seventh framework in the MCP server. The source
is the external KGForEdGlobal export at
`/Users/tzz/Projects/private/idi/KGForEdGlobal/results/kg_for_ed/c939a3a9dcce92ed61d970f4599ced6f2ddc425d1220eeeab9828472b878d24d/`.

MCP clients should be able to discover CAPS and use its Academic Standards,
Learning Components, and stored Learning Progressions with the same tools,
resources, prompts, rights gating, and disclosures as the six existing
frameworks. The six existing packages and the server's set of tools,
resources, and prompts stay as they are.

CAPS connections are longer than any in the existing corpus, up to 13 hops
compared with 8. So that clients can find them, Learning Progression path search
becomes target-aware and its maximum path depth rises. Results that path search
already returns completely stay the same.

## Constraints

- The external source export is read-only. It must not be modified.
- Onboarding follows the established data-and-configuration route for adding a
  framework (`docs/development/framework-package.md`). Generic code must not
  branch on the CAPS framework ID, and validation must not be weakened to admit
  it.
- Sealed packages are immutable and builds are deterministic. The six existing
  packages must keep their snapshot IDs and bytes.
- Rights posture (user decision, 2026-10-14): CAPS is served under the same
  posture as the six existing frameworks. That means `reviewStatus`
  `provisional_operator_approved`, generated derivatives allowed, full text
  allowed, and bulk resources not allowed. The source license stays recorded as
  it appears in the source ("Unknown").
- Footprint (user decision, 2026-10-14): a committed CAPS package of roughly
  85–90 MB is acceptable, even though it roughly doubles
  `data/graph_packages/`, the Docker image, and the MCPB bundle. No size budget
  applies beyond existing per-file limits: GitHub's 100 MB, and the server's
  resource limits in `config.py`.
- Grade R (user decision, 2026-10-14): MCP clients see the grade the source
  encodes as `"K"` labelled as "Grade R".
- Path search (user decisions, 2026-10-14): `get_learning_progression_paths`
  becomes target-aware. It stops extending partial paths that cannot reach the
  target within the requested depth. Its maximum `max_depth` rises from 12 to
  16. Every connected CAPS `buildsTowards` pair must be found while the
  existing queue and work budgets stay fixed. The change is generic, applying
  to every framework.
- Archive-only build inputs stay out of Git. Uploading them to the IDinsight
  Google Drive evidence archive is a manual, user-owned step.
- Tests must not call live or paid LLM services.

## Non-goals

- Changing CAPS curriculum content, Learning Components, or Learning
  Progression judgments. This includes regenerating them or reviewing them
  pedagogically.
- Rebuilding, revising, or re-validating the six existing packages.
- Adding, removing, or renaming MCP tools, resources, resource templates, or
  prompts.
- Changing traversal limits, the default path depth, the path queue and work
  budgets, or any other tool's bounds.
- Adopting Git LFS, external package hosting, or any other way of storing
  packages.
- Changing catalog loading so it tolerates stray non-framework directories
  under `data/graph_packages/`.
- Deploying, publishing, or cutting a release. This includes uploading to the
  Google Drive evidence archive and editing `CHANGELOG.md` by hand.
- Supporting other CAPS phases, subjects, or languages.

## Work

### 1. Verified local copy of the CAPS source

**Intent:** The package must come from a faithful, verifiable copy of the
external export. Builds accept only inputs inside the repository, and the
source project must stay untouched.

**Done when:**

- `AC-001`: The required CAPS copy set has been copied into the repository's
  local preparation area. A verified record of each copied file's hash and size
  matches the external export, and the external export is unchanged.

**Depends on:** None.

### 2. Sealed, accepted CAPS package

**Intent:** Produce an immutable CAPS graph package that passes the same
acceptance standard as the existing six.

**Done when:**

- `AC-002`: A new CAPS package is committed under `data/graph_packages/` with
  terminal `passed` status, and its committed build inputs are in a new input
  set under `data/input_artifacts/`.
- `AC-003`: The package's node and relationship counts match the source
  export: 1 framework, 1,144 framework items, 912 Learning Components, 1,144
  `hasChild`, 1,204 `supports`, 2,879 `buildsTowards`, and 6,708 `relatesTo`.
  Any difference is documented and justified by an existing normalization
  rule.
- `AC-004`: Rebuilding the package from its committed and archived inputs
  produces an identical package.
- `AC-005`: Every committed CAPS file is within GitHub's 100 MB per-file limit,
  and every served CAPS resource is within the server's resource size limits.
  Archive-only inputs are git-ignored and are listed in the package's evidence
  archive record.
- `AC-006`: With the archive-only inputs present locally, evidence-archive
  verification and full (evidence-tier) package validation both pass for CAPS.

**Depends on:** 1, 3.

### 3. CAPS interpretation profile

**Intent:** Tell the server how to interpret and gate CAPS, consistently with
the source and with the user's rights and grade decisions.

**Done when:**

- `AC-007`: The CAPS profile's rights posture is `provisional_operator_approved`,
  with generated derivatives allowed, full text allowed, and bulk resources not
  allowed. Its subject, license, and attribution exactly match the source
  framework root.
- `AC-008`: Every CAPS item's grade is mapped. Clients see the source's `"K"`
  items as "Grade R" and the rest as Grades 1, 2, and 3. Grade filters return
  the matching CAPS items.
- `AC-009`: The source has no statement codes, and clients are told that code
  lookup is unavailable for CAPS. Code-based searches return no false CAPS
  matches.
- `AC-010`: CAPS is identified to clients with its source title, South Africa
  as its jurisdiction, the Department of Basic Education as its author, English
  Home Language as its subject, and Grades R-3 as its grade span.

**Depends on:** None.

### 4. CAPS available through the MCP server

**Intent:** Clients can actually use CAPS through the existing MCP surface.

**Done when:**

- `AC-011`: The framework catalog lists seven frameworks, including CAPS, and
  catalog and framework statistics reflect CAPS.
- `AC-012`: In a real STDIO MCP session, a client can retrieve CAPS
  frameworks, standards, and Learning Components, search them, and get their
  context through the existing tools, resources, and prompts.
- `AC-013`: In a real STDIO MCP session, a client can look up, search, and
  traverse CAPS Learning Progressions. Responses carry the same Learning
  Progression disclosures as the existing frameworks.
- `AC-014`: The MCPB stage built from the repository includes CAPS, and the
  STDIO smoke test passes against that bundle.
- `AC-015`: The Docker build context includes the CAPS package and profile
  without any per-framework list.

**Depends on:** 2, 3.

### 5. No regression to the existing server

**Intent:** Adding CAPS must not change what already ships.

**Done when:**

- `AC-022`: The six existing packages and their profiles are byte-identical to
  the cycle baseline and keep their snapshot IDs. They serve the same results,
  with one exception: a path-search request that previously came back
  truncated may now return complete paths.
- `AC-017`: The public MCP surface is unchanged: 19 tools, 1 fixed resource, 14
  resource templates, and 9 prompts.
- `AC-018`: Generic runtime, build, and validation code contains no
  CAPS-specific branching, and no validation rule is relaxed.
- `AC-019`: The full offline test suite passes with the seven-package corpus,
  including progression baselines and rights assertions that cover CAPS.

**Depends on:** 2, 3, 4, 7.

### 6. Project documentation

**Intent:** Hand-maintained documentation should describe the seven-framework
corpus accurately.

**Done when:**

- `AC-020`: Documentation that lists frameworks or states corpus counts,
  totals, sizes, or input sets reflects the seven-framework corpus with CAPS,
  with no stale six-framework statements left.
- `AC-021`: The framework catalog documentation describes CAPS: identity,
  grades including the Grade R labelling, missing statement codes, rights
  posture with the "Unknown" source license, and Learning Progression
  disclosures.
- `AC-027`: The path-search reference documentation states the new maximum
  path depth of 16 and describes target-aware path search.

**Depends on:** 2, 3, 4, 7.

### 7. Target-aware path search for long connections

**Intent:** Clients can find CAPS's long Learning Progression connections
(up to 13 hops) through the existing path tool, within the existing fixed work
budgets, without changing results the tool already returns completely.

**Done when:**

- `AC-023`: `get_learning_progression_paths` accepts a `max_depth` of up to 16
  and rejects larger values the same way it rejects out-of-range values today.
  The default path depth stays 6.
- `AC-024`: For every request that the cycle-baseline path search answers
  without truncation, on any of the seven packages, the target-aware search
  returns the same paths in the same order.
- `AC-025`: Every connected CAPS `buildsTowards` source–target pair (43,145
  pairs, with shortest paths of up to 13 hops) returns its complete shortest
  path, without truncation, when requested with a `max_depth` from that
  pair's shortest-path length up to 16. The existing queue and work budgets
  stay fixed.
- `AC-026`: Path search never returns a wrong, partial, or wrong-length path.
  Any result that is incomplete reports non-empty truncation reasons.

**Depends on:** 2, 3.

## Retired Acceptance Identifiers

- `AC-016`: Retired on 2026-10-14 because the target-aware path-search change
  makes "serve the same results" too strict. Replaced by `AC-022`.

## Assumptions

- The CAPS export is complete and final. Its validation reports pass with no
  errors and no needs-review claims, and its pending-completions file is empty,
  so the empty `.lp_generation.lock` left from 2026-10-10 is treated as
  leftover.
- The framework ID, version token, input-set name, and source publication date
  are design decisions. The attribution's © 2011 is a candidate date, not an
  established one.
- The untracked `data/graph_packages/.claude/` directory is outside this
  cycle's deliverable. Local verification runs in a checkout without it, or
  after the user removes it.
- Grade-R labelling is a presentation requirement. Which normalized value
  represents it is a design decision, as long as AC-008 holds.
