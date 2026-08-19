# VerilayJobHistory — attribute vocabulary

Human-readable definitions for the terms used by the `VerilayJobHistory` credential type. The JSON-LD
context maps each subject field to an anchor in this file via the `verilay-vocab` prefix, so
`verilay-vocab:companyId` resolves to `#companyid` below.

This document is descriptive. The normative type of every field is the `@type` in
[`VerilayJobHistory-v1.json-ld`](../VerilayJobHistory-v1.json-ld); the normative validation rules are
in [`VerilayJobHistory-v1.json`](../VerilayJobHistory-v1.json).

A candidate holds **one of these per employer**, so several at once. Nothing in this credential is
keyed on the subject's DID and type alone — `companyId` is what distinguishes one instance from
another, and any store holding them must qualify its key by it.

## companyId

`xsd:string` — **required**

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

## role

`xsd:string` — **required**

Job title the company attested to, as free text, e.g. `"Senior Backend Engineer"`.

Carried because a review template has to show the role and the reviewer must not be the one asserting
it. Free text, so equality and set-membership queries only — a policy asking about seniority cannot
match reliably on this and should not try.

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
