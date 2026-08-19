# VerilayDiploma — attribute vocabulary

Human-readable definitions for the terms used by the `VerilayDiploma` credential type. The JSON-LD
context maps each subject field to an anchor in this file via the `verilay-vocab` prefix, so
`verilay-vocab:degreeLevel` resolves to `#degreelevel` below.

This document is descriptive. The normative type of every field is the `@type` in
[`VerilayDiploma-v1.json-ld`](../VerilayDiploma-v1.json-ld); the normative validation rules are in
[`VerilayDiploma-v1.json`](../VerilayDiploma-v1.json).

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
| `5` | Short-cycle tertiary |
| `6` | Bachelor's or equivalent |
| `7` | Master's or equivalent |
| `8` | Doctoral or equivalent |

Lower ISCED levels (`0`–`4`, early childhood through post-secondary non-tertiary) are permitted by
the schema but are not what this credential is normally issued for.

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
