# Manifest contract

`package_manifest.json` is the package-level contract that binds identity, artifacts,
checksums, profile semantics, capabilities, rights, counts, and validation state.

The manifest version is `1.2`, delivery schema is `1.2`, and source schema is `1.0`. The
supported package revision is `1`. The loader rejects any other manifest version with
`manifest_version_unsupported`.

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
| `deliverySchemaVersion` | Delivery JSONL schema version. The supported version is `1.2`     |
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

The current packages including learning components and progressions declare
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

The profile binding is deliberately small and exact:

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

| Logical name                   | Package path in the current packages       | Content                                    |
|--------------------------------|--------------------------------------------|--------------------------------------------|
| `entityProvenance`             | `slim/as_entity_provenance.json`           | Slim standards provenance                  |
| `standardsFramework`           | `detailed/as_standards_framework.json`     | Framework JSON                             |
| `unresolvedItems`              | `detailed/as_unresolved_items.json`        | Unresolved-evidence report JSON            |
| `validationReport`             | `detailed/as_lc_validation_report.json`    | Validation report JSON                     |
| `learningComponentSummary`     | `detailed/lc_generation_summary.json`      | Learning-component generation summary JSON |
| `learningComponentProvenance`  | `slim/lc_entity_provenance.json`           | Slim learning-component provenance         |
| `learningComponentDedupGroups` | `detailed/lc_dedup_groups.json`            | Learning-component dedup groups JSON       |

A package that includes learning progressions must declare these five LP artifacts:

| Logical name                         | Package path                                 |
|--------------------------------------|----------------------------------------------|
| `learningProgressionNormalization`   | `detailed/lp_normalization_receipt.json`     |
| `learningProgressionProvenanceIndex` | `slim/lp_relationship_provenance_index.json` |
| `learningProgressionSummary`         | `detailed/lp_generation_summary.json`        |
| `learningProgressionUnresolved`      | `detailed/lp_unresolved_items.json`          |
| `learningProgressionValidation`      | `detailed/lp_validation_report.json`         |

It must also declare the 64 slim shards as additional artifacts,
`learningProgressionProvenanceShard00` to `learningProgressionProvenanceShard63`, at
`slim/lp_relationship_provenance_shard_NN.json`.

Every manifest must declare `evidenceArchiveRecord` as an additional artifact at
`evidence/evidence_archive_record.json`. See
[Runtime files and archived evidence](graph-packages.md#runtime-files-and-archived-evidence).

A manifest cannot declare archive-only evidence. These names are reserved and rejected,
both as built-in fields and as additional artifacts, even with a `null` value:

```text
academicStandardsBundle
learningComponentsBundle
relationshipsHasChild
standardsFrameworkItems
learningProgressionFinalClaims
learningProgressionProvenance
learningProgressionBuildsTowards
learningProgressionRelatesTo
```

Their files are bound by hash in the evidence archive record instead.

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
| `hasDetailedProvenance`         | `entityProvenance` (slim standards provenance) is declared |
| `hasUnresolvedRelationships`    | Package retains unresolved relationship evidence        |
| `hasOfficialActivities`         | Official activity-role nodes are represented            |
| `hasOfficialAssessmentGuidance` | Official assessment-guidance role nodes are represented |

`hasLearningProgressions` and `hasLearningProgressionProvenance` must both equal
whether `learning_progressions` is in `includedGraphTypes`. When it is, the five LP
artifacts and 64 slim shards above must all be declared. A valid zero-edge LP package
also sets both flags. They do not follow from a global enum or a nonzero count alone.

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
