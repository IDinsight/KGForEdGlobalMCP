# Interpretation profiles

Interpretation profiles keep curriculum-specific semantics in versioned configuration
rather than in framework-specific Python branches.

Every accepted graph package references one exact profile by ID, version, and SHA-256.
The package loader resolves that profile from the configured profile root and rejects a
checksum mismatch.

## Location and identity

Profiles use this directory convention:

```text
config/profiles/<profile-id>/<profile-version>/profile.json
```

For example:

```text
config/profiles/
└── ghana-nacca-primary-english-language-basic-1-3/
    └── 1.0/
        └── profile.json
```

The document must declare the same `profileId` and `profileVersion` selected by its
path. The supported `profileSchemaVersion` is currently `1.0`.

## What a profile defines

| Contract area           | Principal fields                                                                                        | Purpose                                                                                                        |
|-------------------------|---------------------------------------------------------------------------------------------------------|----------------------------------------------------------------------------------------------------------------|
| Identity                | `profileId`, `profileVersion`, `frameworkIds`                                                           | Binds the profile to exact framework families                                                                  |
| Subject mapping         | `localSubject`, `normalizedSubjects`, `subjectMappingStatus`, `subjectMappingNote`, `subjectVocabulary` | Preserves local subject naming while supplying reviewed discovery facets                                       |
| Grade/stage mapping     | `gradeMappings`, `educationStageMappings`, `gradeLevelStatementTypes`                                   | Maps local labels and aliases to normalized retrieval facets                                                   |
| Statement semantics     | `statementTypes`                                                                                        | Defines source statement types, normalized type, aliases, parent rules, identity scope, and optional code type |
| Hierarchy               | `hierarchy`                                                                                             | Declares root types, relationship type, optional type order, and multi-parent policy                           |
| Code search             | `codeSearchPolicy`                                                                                      | Declares code availability, code types, matching/canonicalization rules, and optional prefix behavior          |
| Language                | `languagePolicy`                                                                                        | Preserves source terminology and declares supported source languages                                           |
| Source roles            | `sourceRoleCapabilities`                                                                                | Reports whether official activities, assessment guidance, or resources are represented                         |
| Rights                  | `rights`                                                                                                | Carries the framework-local rights policy used when validating package agreement                               |
| Interpretation guidance | `comparisonDimensions`, `progressionHeuristics`                                                         | Supplies configuration-level dimensions/heuristics without asserting derived relationships                     |
| Caveats                 | `knownSourceAnomalies`, `requiredDisclosures`                                                           | Preserves known source issues and mandatory interpretation warnings                                            |

## Grade mappings are retrieval facets

A grade mapping connects a canonical local label and optional aliases to one or more
normalized grade strings. For Ghana English, for example, `BASIC 1` maps to normalized
`1` while aliases include `Basic 1`, `B1`, `Primary 1`, `Grade 1`, and `Class 1`.

!!! warning "Normalized grades are not grade equivalence"
    A normalized grade is a discovery facet. It does not establish international grade
    equivalence, curriculum equivalence, learner readiness, or instructional sequence.

The runtime preserves the local label alongside the normalized value so clients can
filter consistently without replacing source terminology.

## Statement types and hierarchy

Each `statementTypes` entry can define:

- the source-facing statement type;
- a normalized classification of `Standard` or `Standard Grouping`;
- aliases and controlled values;
- whether it is a graph node;
- identity-scope dimensions;
- an optional code type; and
- permitted direct-parent statement types with minimum/maximum cardinality.

The profile-level `hierarchy` then declares the structural relationship type and root
behavior.

For Ghana English and Mathematics, the declared ordered hierarchy is:

```text
Grade
└── Strand
    └── Sub-Strand
        └── Content Standard
            └── Indicator
```

For CBSE Science, `allowMultiParent` is `true` and no single global
`statementTypeOrder` is declared. A Content Domain Specific Learning Outcome can be
linked to a Chapter and one or more NCERT Learning Outcomes, so the accepted structure
is a DAG rather than a simple tree.

!!! important "Hierarchy is structural evidence"
    The configured `hasChild` structure does not by itself assert prerequisite,
    instructional order, mastery, or learning progression.

## Code-search policy

`codeSearchPolicy` controls whether code search is available and how authored code
surfaces are handled.

Important fields include:

- `availability`: `complete`, `partial`, or `none`;
- `codeTypes`: regex patterns and statement-type scope for known code families;
- `caseSensitive`;
- `whitespaceNormalization` and `punctuationNormalization`;
- `allowPrefixSearch` and `prefixDelimiters`;
- `codeParentRules`: configured deterministic transformations where explicitly allowed;
- `codesAreUniqueIdentifiers`; and
- `canonicalizationNotes`.

The supplied profiles intentionally demonstrate different behavior:

| Profile                            | Code availability | Prefix search |
|------------------------------------|-------------------|---------------|
| Ghana English Basic 1–3            | Partial           | Yes           |
| Ghana Mathematics Basic 4–6        | Partial           | Yes           |
| CBSE Science Classes IX–X          | Partial           | No            |
| Tamil Nadu Mathematics Classes 1–5 | Partial           | Yes           |
| Nigeria Mathematics Primary 1–3    | None              | No            |
| Rwanda Mathematics P1–P3           | None              | No            |

Code equality must not be treated as global identity unless a future profile explicitly
provides that guarantee. The current coded profiles set `codesAreUniqueIdentifiers` to
`false`.

## Known anomalies and disclosures

Profiles make source caveats machine-readable rather than hiding them in prose. Current
examples include:

- Ghana English: printed code anomalies and explicitly unresolved parent relationships;
- Ghana Mathematics: reused codes and editorial duplicates;
- CBSE Science: scoped code interpretation and multi-parent relationships;
- Tamil Nadu Mathematics: Class is a scope dimension rather than a hierarchy node;
- Nigeria Mathematics: no stable statement codes and repeated local labels; and
- Rwanda Mathematics: a configured identity-scope repair for a source-visible P3 Unit 5 anomaly without synthesizing the absent source node.

Every current profile also requires disclosure that normalized grades do not establish
international equivalence, `hasChild` is not automatically a progression, a standard
does not establish mastery, and retrieval matches do not establish official
equivalence.

## Rights in profiles and manifests

Profiles include a `rights` object so interpretation configuration carries the expected
rights policy. The package manifest separately carries its accepted package rights. The
validator checks framework/profile/package semantics for consistency instead of
allowing rights policy to drift silently.

See [Rights and provenance](rights-and-provenance.md) for the exposure model.

## Profile validation

The Pydantic profile contract performs cross-field checks such as:

- exact supported schema version;
- unique framework IDs, aliases, mappings, code types, and hierarchy declarations;
- valid code-search regular expressions;
- code types referencing declared statement types;
- statement types referencing declared code types;
- parent policies referencing valid graph-node types;
- root types and grade-level types referencing declared statement types;
- multi-parent/cardinality rules agreeing with the hierarchy policy; and
- normalized subjects agreeing with the declared subject vocabulary.

The profile loader also:

1. resolves the configured profile root as a trust boundary;
2. rejects symlinked profile components;
3. requires a real `<profile-id>/<version>/profile.json` file;
4. verifies the declared identity; and
5. computes the exact-byte SHA-256 later compared with the package manifest.

## Versioning rule

Treat a referenced profile version as immutable. A semantic change to grade mapping,
hierarchy policy, code handling, rights, or required disclosures should be published as
a new profile version and graph packages should bind explicitly to the intended version
and checksum.

---

**Next:** [Prompt configurations](prompt-configs.md)
