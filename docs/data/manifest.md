# Manifest contract

`package_manifest.json` is the package-level contract that binds identity, artifacts,
checksums, profile semantics, capabilities, rights, counts, and validation state.

The runtime accepts manifest/delivery pairs `1.0/1.1` for existing packages and
`1.1/1.2` for new packages. Mixed pairs are rejected; stored LPs require manifest
`1.1`. Source schema and supported package revision remain `1.0` and `1`.
All frameworks except CBSE Science use the `1.1/1.2` pair. CBSE Science
retains the legacy `1.0/1.1` pair during the staged rollout.

## Top-level fields

| Field                   | Purpose                                                           |
|-------------------------|-------------------------------------------------------------------|
| `manifestVersion`       | Manifest schema version                                           |
| `frameworkId`           | Framework-family identity                                         |
| `snapshotId`            | Immutable snapshot identity, namespaced by `frameworkId`          |
| `graphPackageId`        | Immutable package identity                                        |
| `graphType`             | Primary graph domain                                              |
| `includedGraphTypes`    | Graph domains included in the package                             |
| `packageRevision`       | Package-format revision, currently `1`                            |
| `deliverySchemaVersion` | Delivery schema `1.1` or `1.2`, paired as above     |
| `sourceSchemaVersion`   | Detailed-source schema version                                    |
| `createdAt`             | Timezone-aware package creation timestamp                         |
| `framework`             | Source-faithful and normalized framework metadata                 |
| `profile`               | Exact interpretation-profile ID, version, and SHA-256             |
| `artifacts`             | Logical artifact names mapped to package-relative paths           |
| `checksums`             | SHA-256 for every and only declared artifact path                 |
| `counts`                | Declared graph and additional counts                              |
| `capabilities`          | Snapshot/package search and provenance capabilities               |
| `rights`                | Accepted package rights/exposure metadata                         |
| `validation`            | Package validation status and terminal timestamp                  |
| `snapshotRelations`     | Optional operator-supplied relations to other immutable snapshots |

All public/config schemas serialize with lower-camel-case aliases even though the Python
models use snake_case internally.

## Identity rules

A valid manifest must satisfy several identity invariants:

1. `snapshotId` begins with the exact `frameworkId` namespace.
2. `graphType` appears in `includedGraphTypes`.
3. `includedGraphTypes` contains no duplicates.
4. For an initial package whose `graphPackageId` equals the `snapshotId`,
   `packageRevision` must be `1` and only the primary `graphType` may be included.
5. Otherwise `graphPackageId` must equal the deterministic graph-type/package-revision
   form accepted by the identifier contract.
6. A snapshot relation may not target the same snapshot or duplicate the same
   `(relationType, targetSnapshotId)` pair.

Packages migrated to include learning components and progressions declare
`includedGraphTypes: [academic_standards, learning_components, learning_progressions]`. Because an initial
`graphPackageId` may declare only its primary graph type, such a package uses the
deterministic graph-type/package-revision form instead, and its `graphPackageId` is
therefore longer than its `snapshotId`. Adding LP artifacts changes the artifact-set snapshot hash and package directory;
it does not create a new curriculum edition or change standard/component identifiers.

## Framework metadata

The `framework` object records source-facing and normalized metadata such as:

- `name`;
- `jurisdiction` and optional `jurisdictionType`;
- `issuingAuthority` and `provider`;
- `languages`;
- `localSubject` and `normalizedSubjects`;
- `localGradesOrStages` and `normalizedGrades`;
- `adoptionStatus`;
- `isCurrent`;
- `sourceVersion`, optional publication date, and optional source-document SHA-256; and
- subject-mapping status/note.

Normalized subject and grade metadata supports discovery. It does not overwrite local
curriculum terminology or establish equivalence.

## Profile reference

The profile binding is deliberately small and exact. This example is for a migrated profile; legacy packages retain version `1.0` and their original checksum:

```json
{
  "profile": {
    "profileId": "ghana-nacca-primary-english-language-basic-1-3",
    "profileVersion": "2.0",
    "sha256": "sha256:fe2b269f7e76d0abf89d00799857602e17c8e76b6d1b4055797c662629ce7212"
  }
}
```

The loader computes SHA-256 over the exact resolved `profile.json` bytes and rejects a
mismatch.

## Artifact declarations

The `artifacts` object always requires:

| Logical name    | Role                        |
|-----------------|-----------------------------|
| `nodes`         | Delivery node JSONL         |
| `relationships` | Delivery relationship JSONL |

It can also declare these built-in artifacts:

| Logical name                   | Typical retained artifact                  |
|--------------------------------|--------------------------------------------|
| `academicStandardsBundle`      | Detailed Academic Standards bundle JSON    |
| `entityProvenance`             | Detailed provenance JSON                   |
| `relationshipsHasChild`        | Detailed hierarchy relationship JSONL      |
| `standardsFramework`           | Detailed framework JSON                    |
| `standardsFrameworkItems`      | Detailed item JSONL                        |
| `unresolvedItems`              | Unresolved-evidence report JSON            |
| `validationReport`             | Detailed validation report JSON            |
| `learningComponentsBundle`     | Detailed learning-component bundle JSON    |
| `learningComponentSummary`     | Learning-component generation summary JSON |
| `learningComponentProvenance`  | Learning-component provenance JSON         |
| `learningComponentDedupGroups` | Learning-component dedup groups JSON       |

LP adds nine dedicated artifacts: `learningProgressionBuildsTowards`, `learningProgressionRelatesTo`, `learningProgressionProvenance`, `learningProgressionValidation`, `learningProgressionUnresolved`, `learningProgressionSummary`, `learningProgressionFinalClaims`, `learningProgressionProvenanceIndex`, `learningProgressionNormalization`. All 64 provenance partitions are explicitly declared additional artifacts. See the [preparation/update contract](../development/framework-package.md#learning-progression-inputs-and-updates).

`additionalArtifacts` can represent other logical artifacts, but names reserved by the
built-in fields are forbidden. Every declared artifact path must be unique.

A manifest declaration does not automatically make an artifact readable over MCP. See
[Rights and provenance](rights-and-provenance.md) and
[Resources reference](../reference/resources.md).

## Checksum closure

`checksums` must cover **exactly** the declared artifact paths:

```text
set(checksums.keys()) == set(artifacts.declared_artifacts().paths)
```

A missing checksum or checksum for an undeclared path invalidates the manifest. During
loading, each declared file is read and checked against its expected SHA-256 and size
observation.

## Counts

The version-1 count contract contains:

```json
{
  "counts": {
    "frameworkNodes": 1,
    "itemNodes": 430,
    "learningComponentNodes": 0,
    "relationships": 430,
    "supportsRelationships": 0,
    "buildsTowardsRelationships": 0,
    "relatesToRelationships": 0,
    "additionalCounts": {
      "codedItems": 319,
      "multiParentTargets": 0,
      "unresolvedRelationships": 2
    }
  }
}
```

`itemNodes` counts standards framework items only and `learningComponentNodes` counts
generated learning components; the two are never combined. `relationships` counts every
relationship in the package, of which `supportsRelationships` are learning-component
edges. `buildsTowardsRelationships` and `relatesToRelationships` separately count LP
edges. Those four component/LP counts default to zero for packages without the declared
domains; all packages must still use current supported schemas. Counts are checked
against decoded content. Hierarchy/unresolved counts retain their original meaning.

`frameworkNodes` is exactly `1`. Version 1 requires `additionalCounts` to contain
exactly these three names:

- `codedItems`;
- `multiParentTargets`; and
- `unresolvedRelationships`.

The validator independently derives graph facts and compares them with the manifest and
detailed validation report.

## Capabilities

The `capabilities` object declares package-level behavior:

| Field                           | Meaning                                                 |
|---------------------------------|---------------------------------------------------------|
| `textSearch`                    | Lexical text search is supported                        |
| `codeSearch`                    | Code availability: `complete`, `partial`, or `none`     |
| `multiParent`                   | Accepted hierarchy can contain multi-parent targets     |
| `hasDetailedProvenance`         | Detailed provenance is retained                         |
| `hasUnresolvedRelationships`    | Package retains unresolved relationship evidence        |
| `hasOfficialActivities`         | Official activity-role nodes are represented            |
| `hasOfficialAssessmentGuidance` | Official assessment-guidance role nodes are represented |

`hasLearningProgressions` and `hasLearningProgressionProvenance` report accepted
declarations/evidence, including a valid zero-edge LP package. They do not follow
from a global enum or a nonzero count alone.

Capabilities must agree with independently observed graph/profile facts. They are not
free-form feature flags.

## Rights

The manifest retains the accepted package rights object independently of artifact
presence. It includes source license/attribution plus operator exposure decisions such
as `allowFullText`, `allowStandardResources`, and `allowBulkResource`.

See [Rights and provenance](rights-and-provenance.md).

## Validation state

`validation` is:

```json
{
  "status": "passed",
  "validatedAt": "2026-07-23T00:45:49Z"
}
```

Supported states are `pending`, `passed`, `failed`, and `quarantined`.

A terminal state requires a timezone-aware `validatedAt`. A `pending` state must not
have one. The controlled validation transition changes only the validation object; it
must not alter package-defining manifest fields or `createdAt`.

## Snapshot relations

`snapshotRelations` can record operator-supplied relations using:

```text
derived_from
replaces
revises
supersedes
```

Each relation identifies a target snapshot and can include evidence. The supplied six
packages currently declare no snapshot relations.

---

**Next:** [Validation and lifecycle](validation.md)
