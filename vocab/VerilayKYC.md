# VerilayKYC — attribute vocabulary

Human-readable definitions for the terms used by the `VerilayKYC` credential type. The JSON-LD
context maps each subject field to an anchor in this file via the `verilay-vocab` prefix, so
`verilay-vocab:birthday` resolves to `#birthday` below.

This document is descriptive. The normative type of every field is the `@type` in
[`VerilayKYC-v2.json-ld`](../VerilayKYC-v2.json-ld); the normative validation rules are in
[`VerilayKYC-v2.json`](../VerilayKYC-v2.json).

## kycApproved

`xsd:boolean`

True when Verilay's KYC provider returned an approved decision for the subject. A `VerilayKYC`
credential is only issued after an approved decision, so in practice this field is always `true` on
a live credential — it exists so a policy can assert approval explicitly rather than inferring it
from the mere existence of the credential.

## documentCountry

`xsd:string` — **optional**

ISO 3166-1 alpha-3 country code of the identity document the subject passed KYC with, e.g. `"DEU"`.
This is the country that *issued the document*, not the subject's country of residence.

Optional because the KYC provider does not always return one — thin applicant data is normal,
particularly in sandbox — and no policy queries this field. A credential without it is valid, and
the field is then simply absent from the merklization tree rather than present-and-empty.

Because the field is a string, it is merklized as a hashed value: equality and set-membership
queries (`$eq`, `$in`, `$nin`) work against it, ordering comparisons do not.

## birthday

`xsd:integer`

The subject's date of birth encoded as the integer `YYYYMMDD` — `1997-05-17` becomes `19970517`.
This follows iden3's `KYCAgeCredential` convention.

The integer encoding is deliberate and load-bearing: it is what lets an age check be expressed as a
single range query over the field (`birthday <= <cutoff YYYYMMDD>`), which is a form the on-chain
verifier can evaluate. A date string would have to be hashed and could only be tested for equality.

Callers must zero-pad — `19970517`, never `1997517`.
