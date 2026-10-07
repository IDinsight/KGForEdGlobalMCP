# Available frameworks

The repository snapshot reviewed for this documentation contains six terminal `passed`
Academic Standards graph packages. All six are marked `isCurrent: true` within their
framework families.

This page summarizes the accepted package/profile metadata included in the repository.
For runtime discovery, use `list_frameworks` and `get_framework`.

## Catalog summary

| Framework              | Jurisdiction      | Local scope       | Subject          | Adoption       | Code search         | Hierarchy        |    Items | hasChild |      LCs | supports | buildsTowards | relatesTo | All relationships |
|------------------------|-------------------|-------------------|------------------|----------------|---------------------|------------------|---------:|---------:|---------:|---------:|--------------:|----------:|------------------:|
| Ghana English Language | Ghana             | BASIC 1–3         | English Language | Adopted        | Partial + prefix    | Tree             |      430 |      430 |      272 |      307 | 0 | 0 | 737 |
| Ghana Mathematics      | Ghana             | BASIC 4–6         | Mathematics      | Adopted        | Partial + prefix    | Tree             |      302 |      302 |      230 |      273 | 299 | 300 | 1174 |
| CBSE Science           | India             | Class IX–X        | Science          | Unknown        | Partial, exact only | Multi-parent DAG |      874 |     1109 |      853 |      858 | 0 | 0 | 1967 |
| Tamil Nadu Mathematics | Tamil Nadu, India | Class-1–5         | Mathematics      | Proposed Draft | Partial + prefix    | Tree             |      255 |      255 |      399 |      419 | 472 | 435 | 1581 |
| Nigeria Mathematics    | Nigeria           | PRIMARY ONE–THREE | Mathematics      | Adopted        | None                | Tree             |      242 |      242 |      186 |      204 | 189 | 297 | 932 |
| Rwanda Mathematics     | Rwanda            | P1–P3             | Mathematics      | Adopted        | None                | Tree             |      626 |      626 |      716 |      797 | 0 | 0 | 1423 |
| **Total**              |                   |                   |                  |                |                     |                  | **2729** | **2964** | **2656** | **2858** | **960** | **1032** | **7814** |

Across the six manifests there are **1,439 coded items**, **15 unresolved
relationships**, and **235 multi-parent targets**. The multi-parent targets are all in
the CBSE Science package; the unresolved relationships are in the two Ghana packages.

!!! warning "Normalized grade numbers are discovery facets"
    Similar normalized numbers across frameworks do not establish official grade
    equivalence, curricular alignment, or instructional interchangeability.

Nigeria, Ghana and Tamil Nadu Mathematics are migrated, with a combined
**960 buildsTowards** and **1,032 relatesTo** edges. The other three packages await migration. The complete rollout targets
**3,039 buildsTowards** and **5,041 relatesTo** edges. Update this catalog with each migration;
`get_capabilities` and `get_framework` remain authoritative at runtime.
See [rollout and acceptance](../development/lp-migration.md).

## Ghana — English Language, Basic 1–3

**Framework ID**

```text
ghana-nacca-primary-english-language-basic-1-3
```

**Current snapshot**

```text
ghana-nacca-primary-english-language-basic-1-3@2019+c33ab5a379fb
```

| Property                 | Value                                                                         |
|--------------------------|-------------------------------------------------------------------------------|
| Official title           | English Language Curriculum for Primary Schools (Basic 1 - 3)                 |
| Issuing authority        | National Council for Curriculum and Assessment (NaCCA), Ministry of Education |
| Local subject            | English Language                                                              |
| Normalized subject       | English Language Arts                                                         |
| Local grades             | BASIC 1, BASIC 2, BASIC 3                                                     |
| Code search              | Partial; exact and prefix                                                     |
| Detailed provenance      | Yes                                                                           |
| Unresolved relationships | 2                                                                             |
| Coded items              | 319                                                                           |

Hierarchy:

```text
Grade > Strand > Sub-Strand > Content Standard > Indicator
```

Important profile caveat: the accepted source preserves printed code anomalies and
explicit unresolved-root fallback relationships. Code/hierarchy matches can require
source-path review.

## Ghana — Mathematics, Basic 4–6

**Framework ID**

```text
ghana-nacca-primary-mathematics-basic-4-6
```

**Current snapshot**

```text
ghana-nacca-primary-mathematics-basic-4-6@2019+0b768f7cfaf9
```

| Property                 | Value                                                    |
|--------------------------|----------------------------------------------------------|
| Official title           | Mathematics Curriculum for Primary Schools (Basic 4 - 6) |
| Issuing authority        | NaCCA, Ministry of Education                             |
| Local subject            | Mathematics                                              |
| Local grades             | BASIC 4, BASIC 5, BASIC 6                                |
| Code search              | Partial; exact and prefix                                |
| Detailed provenance      | Yes                                                      |
| Unresolved relationships | 13                                                       |
| Coded items              | 254                                                      |

Hierarchy:

```text
Grade > Strand > Sub-Strand > Content Standard > Indicator
```

Important profile caveat: reused codes, same-code/different-content records, and
editorial duplicates mean code equality is retrieval evidence rather than guaranteed
identity.

## India — CBSE Science, Classes IX–X

**Framework ID**

```text
india-cbse-science-learning-framework-classes-9-10
```

**Current snapshot**

```text
india-cbse-science-learning-framework-classes-9-10@undated+e8361376ae1e
```

| Property             | Value                                                                  |
|----------------------|------------------------------------------------------------------------|
| Official title       | Learning Framework - Science                                           |
| Issuing authority    | Central Board of Secondary Education (CBSE) and Azim Premji University |
| Local subject        | Science                                                                |
| Local grades         | Class IX, Class X                                                      |
| Adoption status      | Unknown                                                                |
| Code search          | Partial; exact only                                                    |
| Detailed provenance  | Yes                                                                    |
| Multi-parent targets | 235                                                                    |
| Coded items          | 831                                                                    |

This framework is the repository's explicit multi-parent example. Source statement types
include Class, Content Domain, Chapter, NCERT Learning Outcome, Content Domain Specific
Learning Outcome, and Indicator. A CLO can have a Chapter parent and one or more NCERT
Learning Outcome parents.

Code families include `LO`, `CLO`, and indicator-style codes, scoped by Class. Numeric
code ranges must not be used to infer hierarchy.

## India — Tamil Nadu Mathematics, Classes 1–5

**Framework ID**

```text
india-tamil-nadu-tnscert-mathematics-classes-1-5
```

**Current snapshot**

```text
india-tamil-nadu-tnscert-mathematics-classes-1-5@2025-proposed-draft+aa0dd9310a0f
```

| Property            | Value                                                           |
|---------------------|-----------------------------------------------------------------|
| Official title      | Tamil Nadu Curriculum Framework 2025: Mathematics - Classes 1-5 |
| Issuing authority   | TNSCERT                                                         |
| Local grades/stages | Class-1 through Class-5                                         |
| Adoption status     | Proposed Draft                                                  |
| Code search         | Partial; exact and prefix                                       |
| Detailed provenance | Yes                                                             |
| Coded items         | 35                                                              |

Graph hierarchy:

```text
Curricular Goal > Competency > Content
```

Class applicability is a scope dimension on content rather than an additional graph
hierarchy level. The profile preserves authored code surfaces while allowing configured
canonicalization for deterministic lookup.

## Nigeria — Mathematics, Primary 1–3

**Framework ID**

```text
nigeria-nerdc-mathematics-primary-1-3
```

**Current snapshot**

```text
nigeria-nerdc-mathematics-primary-1-3@undated+bc5e769ed26f
```

| Property            | Value                                                         |
|---------------------|---------------------------------------------------------------|
| Official title      | 9-Year Basic Education Mathematics Curriculum for Primary 1-3 |
| Issuing authority   | Nigerian Educational Research and Development Council (NERDC) |
| Local grades        | PRIMARY ONE, PRIMARY TWO, PRIMARY THREE                       |
| Adoption status     | Adopted                                                       |
| Code search         | None                                                          |
| Detailed provenance | Yes                                                           |
| Coded items         | 0                                                             |

Hierarchy:

```text
Grade > Theme > Sub-Theme > Topic > Performance Objective
```

The profile explicitly records that there are no stable statement codes. Repeated local
labels and visible topic ordinals must remain scoped to their source context rather than
being treated as global IDs.

## Rwanda — Mathematics, P1–P3

**Framework ID**

```text
rwanda-reb-mathematics-lower-primary-1-3
```

**Current snapshot**

```text
rwanda-reb-mathematics-lower-primary-1-3@2025+98426787aa9f
```

| Property            | Value                                                   |
|---------------------|---------------------------------------------------------|
| Official title      | Mathematics Syllabus for Lower Primary \| Primary 1 - 3 |
| Issuing authority   | Rwanda Basic Education Board (REB)                      |
| Local grades        | P1, P2, P3                                              |
| Adoption status     | Adopted                                                 |
| Code search         | None                                                    |
| Detailed provenance | Yes                                                     |
| Coded items         | 0                                                       |

Primary grouping hierarchy:

```text
Grade > Topic Area > Sub-Topic Area > Unit > Key Unit Competence
```

The profile also models Grade Key Competence plus Knowledge, Skills, and Attitudes and
Values objectives under their configured parents.

Important caveat: the accepted upstream configuration contains a scoped repair for a
visible P3 Unit 5 Sub-Topic Area whose Topic Area heading is absent from the source. The
MCP layer must not synthesize the missing source node; configured scope repair remains a
deterministic derivation rather than a source-visible statement.

## Shared package properties

The installed packages use these formats during the staged rollout:

| Packages | Manifest / delivery schema | Profile version / schema | Included domains |
| --- | --- | --- | --- |
| Nigeria, Ghana and Tamil Nadu Mathematics | 1.1 / 1.2 | 2.0 / 1.1 | Academic standards, learning components, learning progressions |
| Other three frameworks | 1.0 / 1.1 | 1.0 / 1.0 | Academic standards, learning components |

All six supplied packages currently share these properties:

- graph type: `academic_standards`;
- package revision: `1`;
- source schema: `1.0`;
- prompt-config version: `2.0.0`;
- terminal validation state: `passed`;
- text search: enabled;
- detailed provenance: present;
- official activity capability: false;
- official assessment-guidance capability: false;
- rights review: `provisional_operator_approved`;
- full-text permission: true;
- standard-resource permission: true;
- bulk-resource permission: false; and
- generated derivatives policy: `allowed`.

For exact runtime metadata, use [Discover frameworks](../guides/framework-discovery.md)
and [Framework and capability tools](../reference/framework-tools.md).

---

**Next:** [Environment variables](../operations/configuration.md)
