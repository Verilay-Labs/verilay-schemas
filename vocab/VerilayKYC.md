# VerilayKYC — attribute vocabulary

Human-readable definitions for the terms used by the `VerilayKYC` credential type. The JSON-LD
context maps each subject field to an anchor in this file via the `verilay-vocab` prefix, so
`verilay-vocab:birthday` resolves to `#birthday` below.

This document is descriptive. The normative type of every field is the `@type` in the context of
the version being used — [`VerilayKYC-v3.json-ld`](../VerilayKYC-v3.json-ld) for new issuance,
[`VerilayKYC-v2.json-ld`](../VerilayKYC-v2.json-ld) for the credentials the on-chain KYC requests
were registered against — and the normative validation rules are in the matching JSON Schema
([`VerilayKYC-v3.json`](../VerilayKYC-v3.json), [`VerilayKYC-v2.json`](../VerilayKYC-v2.json)).

Both versions share this vocabulary: v3 is v2 plus [`fullName`](#fullname). A term means the same
thing in every version that carries it.

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

## fullName

`xsd:string` — **v3 and later**

The subject's full legal name as verified by the KYC provider from the identity document, as a single
display string — `"Jane Doe"`, not separate given/family fields. Required in v3: the version exists to
carry it.

It is here so the person can see, in their own vault, exactly what an issuer-attested disclosure
statement would share with an employer before they ask for one to be issued, and so that selective
disclosure of the name has a field to disclose. The name is never queried on chain: no policy
compares it, and it is not part of any registered request. As a string it is merklized as a hashed
value, so only equality and set-membership queries could ever be expressed against it.

Personal data lives in the holder's vault. Nothing in Verilay stores this value server-side by
default; an employer only ever receives it through a statement the person explicitly requests.
