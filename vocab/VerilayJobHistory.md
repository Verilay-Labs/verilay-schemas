# VerilayJobHistory — attribute vocabulary

Human-readable definitions for the terms used by the `VerilayJobHistory` credential type. The JSON-LD
context maps each subject field to an anchor in this file via the `verilay-vocab` prefix, so
`verilay-vocab:companyId` resolves to `#companyid` below.

This document is descriptive. The normative type of every field is the `@type` in the context of the
version being used — [`VerilayJobHistory-v2.json-ld`](../VerilayJobHistory-v2.json-ld) for new
issuance (MS3 issues v2 only), [`VerilayJobHistory-v1.json-ld`](../VerilayJobHistory-v1.json-ld) for
the frozen v1 — and the normative validation rules are in the matching JSON Schema
([`VerilayJobHistory-v2.json`](../VerilayJobHistory-v2.json),
[`VerilayJobHistory-v1.json`](../VerilayJobHistory-v1.json)). A term marked **(v2)** exists only in
v2.

A candidate holds **one of these per employer**, so several at once. Nothing in this credential is
keyed on the subject's DID and type alone — `companyId` is what distinguishes one instance from
another, and any store holding them must qualify its key by it. In v2, where `companyId` may be
absent, the credential id is the only key that is always unique.

## companyId

`xsd:string` — **required** (v1) · **optional** (v2)

The attesting company's Verilay account `user_uuid`, in canonical lowercase 8-4-4-4-12 hyphenated
form.

This is the load-bearing field of the whole credential. It is the same identifier
`verilay-user-service` exposes on the public business record and the same one the reviews registry
keys on, which is what lets a review be gated on "this reviewer worked at *this* company". It is
deliberately the account UUID and not a company name, domain or display label: names change, domains
are shared and re-registered, and neither is a stable join key. A human-readable company name is
resolved from the registry at display time rather than frozen into the credential.

Because the field is a string, it is merklized as a hashed value: equality and set-membership
queries (`$eq`, `$in`, `$nin`) work against it, ordering comparisons do not. That is all a
"worked at company X" gate needs.

**v2:** optional. Present when a company registered in Verilay attested the employment; absent on a
credential from a state employment record, which names an employer but not a Verilay account.
**Only a credential carrying `companyId` can gate a review** — the reviews registry keys on it.

## role

`xsd:string` — **required** (v1) · **optional** (v2)

Job title the company attested to, as free text, e.g. `"Senior Backend Engineer"`.

Carried because a review template has to show the role and the reviewer must not be the one asserting
it. Free text, so equality and set-membership queries only — a policy asking about seniority cannot
match reliably on this and should not try.

**v2:** optional — state employment records do not assert a role.

## employedFrom

`xsd:integer` — **required**

First day of the employment period, encoded as the integer `YYYYMMDD` — `2021-03-01` becomes
`20210301`. Same convention as `birthday` in [`VerilayKYC`](VerilayKYC.md).

The integer encoding is deliberate: it is what lets tenure and date-window checks be expressed as
range queries the on-chain verifier can evaluate. A date string could only be tested for equality.

Callers must zero-pad — `20210301`, never `202131`.

## employedTo

`xsd:integer` — **optional**

Last day of the employment period, encoded as `YYYYMMDD`.

**Absent means the employment had not ended when the company attested.** It is optional for the same
reason `documentCountry` is optional on the KYC credential: a required field that the issuer cannot
always fill produces credentials that fail their own published schema. An employer attesting to a
current employee has no end date to give.

⚠️ A policy that means "employment has ended" must handle absence explicitly rather than assuming the
field is there — `claimPathNotExists` is part of the `queryHash` for exactly this case. A range query
over `employedTo` alone silently excludes every ongoing employment.

## employerName

`xsd:string` — **required** (v2)

The employer as the source names it: the attesting company's name in Verilay, or the employer named
on a state employment record, e.g. `"Acme Iberia S.L."`. It is required because it is the one
employer field every source gives. A display string, not a join key — `companyId` is the join key
where present.

## employerTaxId

`xsd:string` — **optional** (v2)

The employer's tax identifier as the source record states it, e.g. a Spanish NIF/CIF or a Portuguese
NIPC. Sources that do not state one omit it. Equality and set-membership queries only.

## contributionDays

`xsd:integer` — **optional** (v2)

Number of social-insurance contribution days the source record attributes to this employment. Only
sources that state it provide it. Integer, so range queries.

## sourceCaveat

`xsd:string` — **optional** (v2)

A limitation the source itself places on what its verification proves — e.g. that a verification
code confirms the authenticity of the document but not the validity of the data in it. Display only.

## grade

`xsd:integer` — **required** (v2)

How strongly the source proved the credential, as an ordinal on the employment scale:

| Value | Grade |
|-------|-------|
| `6` | CRYPTO |
| `5` | SOCIAL_INSURANCE |
| `4` | PAYROLL |
| `3` | EMPLOYER_ATTESTED |
| `2` | GIG_PLATFORM |
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
`es.vida_laboral`, `pt.ss_direta`, `verilay.employer_attestation`, or a finer source name where one adapter covers several. Equality and set-membership
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
