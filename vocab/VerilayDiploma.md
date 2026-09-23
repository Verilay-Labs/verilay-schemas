# VerilayDiploma — attribute vocabulary

Human-readable definitions for the terms used by the `VerilayDiploma` credential type. The JSON-LD
context maps each subject field to an anchor in this file via the `verilay-vocab` prefix, so
`verilay-vocab:degreeLevel` resolves to `#degreelevel` below.

This document is descriptive. The normative type of every field is the `@type` in the context of the
version being used — [`VerilayDiploma-v2.json-ld`](../VerilayDiploma-v2.json-ld) for new issuance
(MS3 issues v2 only), [`VerilayDiploma-v1.json-ld`](../VerilayDiploma-v1.json-ld) for the frozen v1
— and the normative validation rules are in the matching JSON Schema
([`VerilayDiploma-v2.json`](../VerilayDiploma-v2.json),
[`VerilayDiploma-v1.json`](../VerilayDiploma-v1.json)). A term marked **(v2)** exists only in v2.

## institution

`xsd:string` — **required**

Name of the awarding institution as it appears on the diploma, e.g.
`"Technical University of Munich"`.

Institutions are **not** Verilay accounts and there is no institution registry, so unlike
`companyId` on [`VerilayJobHistory`](VerilayJobHistory.md) this is a display string rather than a
resolvable identifier. Equality and set-membership queries only, and a policy naming specific
institutions has to enumerate the exact strings it accepts.

## degree

`xsd:string` — **required**

Human-readable title of the qualification, e.g. `"Master of Science"`.

This exists so a reader can see what was actually awarded. **Do not query it** — free-text degree
titles vary by country and by institution, so a policy matching on the string will miss
qualifications it meant to accept. Query `degreeLevel` instead.

## degreeLevel

`xsd:integer` — **required**

ISCED 2011 level of the qualification:

| Value | Level |
|-------|-------|
| `3` | Upper secondary — a school-leaving diploma |
| `4` | Post-secondary non-tertiary |
| `5` | Short-cycle tertiary |
| `6` | Bachelor's or equivalent |
| `7` | Master's or equivalent |
| `8` | Doctoral or equivalent |

**The full `0`–`8` range is allowed deliberately, not by oversight.** A school-leaving diploma is a
diploma, and a company asking "has completed secondary education" is a real policy. Restricting the
schema to tertiary levels would make that unaskable — and the range cannot be widened afterwards,
because widening it is a new schema version, new context URL, new requestIds and every credential
reissued. Permissive costs nothing here: the ordering that makes `>= 6` mean "at least a bachelor's"
holds across the whole range.

This is the **queryable** form of `degree`, and the reason the type is an integer rather than a
string. "At least a bachelor's" is `degreeLevel >= 6` — a range query the on-chain verifier can
evaluate. No free-text title could express that: hashed string values support only equality and set
membership, so the same policy would have to enumerate every title in every country that happens to
mean "bachelor's". Same reasoning as `birthday` on [`VerilayKYC`](VerilayKYC.md).

## fieldOfStudy

`xsd:string` — **optional**

Subject area of the qualification as awarded, e.g. `"Computer Science"`.

Optional because not every qualification names one. Free text, so equality and set-membership queries
only — a policy relying on it must enumerate the spellings it accepts, and should expect to miss
some.

## awardedAt

`xsd:integer` — **required**

Date the qualification was awarded, encoded as the integer `YYYYMMDD` — `2019-07-15` becomes
`20190715`. Same convention as `birthday` on [`VerilayKYC`](VerilayKYC.md) and `employedFrom` on
[`VerilayJobHistory`](VerilayJobHistory.md).

Integer encoding makes "graduated after X" a range query rather than an impossible string comparison.

Callers must zero-pad — `20190715`, never `2019715`.

## grade

`xsd:integer` — **required** (v2)

How strongly the source proved the credential, as an ordinal on the education scale:

| Value | Grade |
|-------|-------|
| `4` | CRYPTO |
| `3` | REGISTRY |
| `2` | ISSUER |
| `1` | APOSTILLE_ONLY |
| `0` | UNVERIFIABLE |

Higher is stronger, so "at least REGISTRY"-style requirements are range queries (`grade >= N`) that
the on-chain verifier can evaluate, the same trick as `degreeLevel`. The scale is frozen with the
schema version: adding, removing or reordering a grade is a new version.

`UNVERIFIABLE` (`0`) completes the ordering but **no credential is ever issued at 0** — a request
that cannot be verified ends without a credential. A `grade >= 0` policy would accept anything, which
is a self-declaration and needs no issuer.

## source

`xsd:string` — **required** (v2)

Identifier of the verification source that produced the grade — the issuer's source-adapter id, e.g.
`br.diploma_digital`, `registry.pe.sunedu`, or a finer source name where one adapter covers several. Equality and set-membership
queries only.

## verifiedAt

`xsd:integer` — **required** (v2)

Date the verification concluded, as `YYYYMMDD`. Integer, so "verified since" is a range query.
Callers must zero-pad.

## documentHash

`xsd:string` — **optional** (v2)

SHA-256 of the evidence document's bytes exactly as submitted to the issuer, as 64 lowercase hex
characters. It binds the credential to the document that was verified without disclosing the
document.

**Absent when the source had no document to hash — never the empty string.** The iden3 merklizer
cannot merklize an empty string value, so a credential carrying `documentHash: ""` could never be
issued or proven; the JSON Schema rejects it. Lowercase only, so that equality is byte equality.

## evidenceMethod

`xsd:string` — **required** (v2)

How the evidence was checked, e.g. `XADES_ICP_BRASIL_OFFLINE`, `PORTAL_CODE_RECHECK`,
`OPERATOR_PORTAL_CHECK`, `EMPLOYER_ATTESTATION_SIGNED`. It distinguishes an automated check from an
operator-resolved one at the same grade. Equality and set-membership queries only.

## institutionCode

`xsd:string` — **optional** (v2)

The awarding institution's identifier in the source's own registry — the e-MEC IES code for a
Brazilian diploma, or the registry's institution id. Only sources with an institution registry
provide one. Meaningful only together with `source`: two registries' codes are not comparable.

## courseCode

`xsd:string` — **optional** (v2)

The course or programme's identifier in the source's own registry, e.g. the e-MEC course code. Only
sources with a course registry provide one. Meaningful only together with `source`.

## accreditationSnapshotAt

`xsd:integer` — **optional** (v2)

Date of the accreditation snapshot the institution and course were checked against (e.g. the e-MEC
sync), as `YYYYMMDD`. Present only when the source checks accreditation. Integer, so range queries.
