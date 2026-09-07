# verilay-schemas

Public, canonical credential schemas for the [Verilay](https://github.com/Verilay-Labs) protocol.

Verilay issues W3C Verifiable Credentials in the iden3 format. Each credential type is described by
**two** documents that must both be resolvable by anyone:

| Document | What it is | Who reads it |
|----------|------------|--------------|
| `<Type>-vN.json-ld` | JSON-LD **context** — maps subject field names to IRIs and XSD types | The issuer, to merklize the credential; the wallet/browser, to build a query proof; the on-chain policy, whose schema hash is derived from the type IRI in this file |
| `<Type>-vN.json` | JSON **Schema** — validates the shape of an issued credential | Anything validating a credential; carries `$metadata.uris` pointing back at the context |

These are two different documents with two different jobs. `credentialSchema.id` on an issued
credential points at the **JSON Schema** (`.json`); the credential's `@context` array points at the
**JSON-LD context** (`.json-ld`).

## Why this repo is public

Everything here is field-name vocabulary and types — `kycApproved`, `birthday`, `companyId`,
`degreeLevel`. No keys, no endpoints, no personal data. It has to be public because:

- the issuer resolves the context server-side to merklize a credential;
- a holder's browser may fetch the context while producing a proof;
- `credentialSchema.id` is embedded in every issued credential and must resolve for anyone holding
  one;
- the on-chain policy's schema hash is derived from the type IRI in the context, so a third party
  cannot verify what a policy actually asserts without reading it.

Same posture as [`iden3/claim-schema-vocab`](https://github.com/iden3/claim-schema-vocab).

## These files are immutable once referenced

**Never edit a published document in place.** A credential's schema hash is derived from the type
IRI in its context, and both the issuer and the on-chain policy pin that hash. Changing a published
file silently invalidates every credential and policy that referenced it.

Adding, removing, renaming or retyping a field means **a new version file** landed alongside the old
ones, which stay where they are forever. `VerilayKYC-v3` is exactly that: v2 plus one field, published
as a new pair, with v2 untouched and still pinned by everything that was registered against it.

Typo fixes in prose (this README, the `vocab/` notes) are fine. Anything inside a `.json-ld` or
`.json` is not.

The rule is blanket on purpose, but the two files are not equally dangerous, and it is worth knowing
which is which before someone talks themselves into an exception:

- The **JSON-LD context** is the load-bearing one. Adding, renaming or reordering terms changes the
  `claimPathKey`s, which breaks every credential already issued *and* the policy already registered
  on-chain. There is no safe edit here.
- The **JSON Schema**'s `title`/`description` prose is not part of any hash — the schema hash derives
  only from the type IRI string. Editing prose is technically harmless. It is still forbidden,
  because "harmless edit to a published schema" is not a judgement worth relitigating per commit.

## Schemas

Every type here is **merklized** — no context carries an `iden3_serialization` directive, so every
subject field is addressable through the merklization root rather than being packed into fixed claim
slots.

Dates are integers in `YYYYMMDD` form throughout (`birthday`, `employedFrom`, `employedTo`,
`awardedAt`). That is not cosmetic: an integer can be range-queried on chain, and a hashed string can
only be tested for equality and set membership. Any field a policy needs to compare with `<` or `>`
has to be an integer here, and choosing wrong is unfixable without a new schema version.

### VerilayJobHistory v1

- Context: <https://raw.githubusercontent.com/Verilay-Labs/verilay-schemas/main/VerilayJobHistory-v1.json-ld>
- JSON Schema: <https://raw.githubusercontent.com/Verilay-Labs/verilay-schemas/main/VerilayJobHistory-v1.json>
- Type IRI: `https://raw.githubusercontent.com/Verilay-Labs/verilay-schemas/main/VerilayJobHistory-v1.json-ld#VerilayJobHistory`
- Vocabulary: [`vocab/VerilayJobHistory.md`](vocab/VerilayJobHistory.md)

A company registered in Verilay attests that the subject worked there, in what role, over which
dates. This is the credential that gates review submission.

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `companyId` | `xsd:string` | yes | The company's Verilay account `user_uuid`, canonical lowercase hyphenated form |
| `role` | `xsd:string` | yes | Job title as attested, free text |
| `employedFrom` | `xsd:integer` | yes | `YYYYMMDD`; integer ⇒ range queries |
| `employedTo` | `xsd:integer` | no | `YYYYMMDD`; **absent means employment had not ended at attestation** |

`companyId` is the load-bearing field: it is the same identifier `verilay-user-service` exposes on
the public business record and the same one the reviews registry keys on, which is what lets a review
be gated on "this reviewer worked at *this* company". It is the account UUID and not a company name
or domain because names change, domains are shared and re-registered, and neither is a stable join
key — the display name is resolved from the registry instead of frozen into the credential.

A candidate holds **one of these per employer**, so several at once. Nothing here is keyed on
`(subject DID, type)` alone; `companyId` is what distinguishes instances, and any store holding them
must qualify its key by it.

⚠️ A policy meaning "employment has ended" must handle `employedTo` being absent rather than assuming
it is there — `claimPathNotExists` is part of the `queryHash` for exactly this case. A range query
over `employedTo` alone silently excludes every ongoing employment.

### VerilayDiploma v1

- Context: <https://raw.githubusercontent.com/Verilay-Labs/verilay-schemas/main/VerilayDiploma-v1.json-ld>
- JSON Schema: <https://raw.githubusercontent.com/Verilay-Labs/verilay-schemas/main/VerilayDiploma-v1.json>
- Type IRI: `https://raw.githubusercontent.com/Verilay-Labs/verilay-schemas/main/VerilayDiploma-v1.json-ld#VerilayDiploma`
- Vocabulary: [`vocab/VerilayDiploma.md`](vocab/VerilayDiploma.md)

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `institution` | `xsd:string` | yes | Awarding institution name; display string, not a resolvable id |
| `degree` | `xsd:string` | yes | Human-readable title, e.g. `Master of Science` — **display only, do not query** |
| `degreeLevel` | `xsd:integer` | yes | ISCED 2011 level: 3 upper secondary, 6 bachelor's, 7 master's, 8 doctoral |
| `fieldOfStudy` | `xsd:string` | no | Subject area as awarded |
| `awardedAt` | `xsd:integer` | yes | `YYYYMMDD`; integer ⇒ range queries |

`degreeLevel` is the queryable form of `degree`, and the reason it is an integer. "At least a
bachelor's" is `degreeLevel >= 6`, a range query the on-chain verifier can evaluate; no free-text
title could express that, because hashed string values support only equality and set membership and
the same policy would have to enumerate every title in every country meaning "bachelor's".

### VerilayKYC v3

- Context: <https://raw.githubusercontent.com/Verilay-Labs/verilay-schemas/main/VerilayKYC-v3.json-ld>
- JSON Schema: <https://raw.githubusercontent.com/Verilay-Labs/verilay-schemas/main/VerilayKYC-v3.json>
- Type IRI: `https://raw.githubusercontent.com/Verilay-Labs/verilay-schemas/main/VerilayKYC-v3.json-ld#VerilayKYC`
- Vocabulary: [`vocab/VerilayKYC.md`](vocab/VerilayKYC.md)

**This is the version new KYC issuance uses.** v3 is v2 plus `fullName`, so the person can see in
their vault exactly what an issuer-attested disclosure statement would share with an employer, and so
selective disclosure of the name later has a field to disclose.

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `kycApproved` | `xsd:boolean` | yes | KYC provider returned an approved decision |
| `birthday` | `xsd:integer` | yes | `YYYYMMDD`, e.g. `19970517`; integer ⇒ range queries, which is what makes an on-chain age check possible |
| `documentCountry` | `xsd:string` | no | ISO 3166-1 alpha-3, e.g. `DEU`; string ⇒ equality/set queries only |
| `fullName` | `xsd:string` | yes | Full legal name as verified from the identity document, one display string, e.g. `Jane Doe`; **display and disclosure only, no policy queries it** |

`fullName` is required because the version exists to carry it — a v3 credential without a name is a
v2 credential and should be issued as one. `documentCountry` stays optional for the same reason it
was in v2.

#### Which version does what

A new context is a new type IRI, and therefore a **new `schemaHash` and new `claimPathKey`s** — the
same field name under v2 and v3 merklizes to different keys. That is what makes the versions
independent, and it is why the split below is not optional:

| Use | Version | Why |
|-----|---------|-----|
| New `VerilayKYC` issuance by the Sumsub issuer | **v3** | Carries `fullName` |
| Every existing on-chain KYC request (`setRequests` age/KYC policies), the verification catalog, the contracts golden vectors | **v2** | Registered against the v2 `schemaHash` / `claimPathKey`s; `setRequests` is irreversible, so those pins do not move |

A holder proving against a registered v2 request needs a v2 credential in their vault; a holder whose
vault only holds v3 cannot satisfy a v2 request, because the schema hash in the proof will not match.
Consumers that re-sync a holder onto v3 must keep that in mind until requests are re-registered on
v3 — which is a separate decision, not implied by this file existing.

### VerilayKYC v2

- Context: <https://raw.githubusercontent.com/Verilay-Labs/verilay-schemas/main/VerilayKYC-v2.json-ld>
- JSON Schema: <https://raw.githubusercontent.com/Verilay-Labs/verilay-schemas/main/VerilayKYC-v2.json>
- Type IRI: `https://raw.githubusercontent.com/Verilay-Labs/verilay-schemas/main/VerilayKYC-v2.json-ld#VerilayKYC`
- Vocabulary: [`vocab/VerilayKYC.md`](vocab/VerilayKYC.md)

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `kycApproved` | `xsd:boolean` | yes | KYC provider returned an approved decision |
| `birthday` | `xsd:integer` | yes | `YYYYMMDD`, e.g. `19970517`; integer ⇒ range queries, which is what makes an on-chain age check possible |
| `documentCountry` | `xsd:string` | no | ISO 3166-1 alpha-3, e.g. `DEU`; string ⇒ equality/set queries only |

`documentCountry` is optional because the KYC provider does not always return a country and no
policy queries it. Omitting it is safe: `claimPathKey` derives from the JSON-LD context path, not
from the JSON Schema's `required` list, so an absent field is simply not in the merklization tree.

v2 is **the version every registered on-chain KYC request refers to**, and it stays published and
byte-identical for as long as any of those requests exist. New issuance moved to [v3](#verilaykyc-v3).

### There is no VerilayKYC v1

`VerilayKYC-v1.json-ld` was referenced by the issuer and the frontend before this repo existed, so
that URL always returned 404 and **nothing valid was ever issued against it**. There is no
back-compat to preserve and no v1 file will be published. Any credential still carrying a v1
`credentialSchema.id` is to be reissued against the current issuance version.

## Vendored copies must be byte-identical

Several repos keep a local copy of a context rather than fetching it at runtime — an issuer embeds
it, a deploy script loads it to derive query parameters, a frontend serves it to avoid a network
fetch while proving. **Every one of those copies must be byte-identical to the published file.**

This is not a style rule. The `schemaHash` and the `claimPathKey`s are derived from the document
bytes and are committed inside the on-chain `queryHash`. `setRequests` is irreversible and a
requestId can never be re-registered, so a single whitespace difference in a single copy is an
unrecoverable mismatch: proving fails, and the registered request cannot be corrected.

[`SHA256SUMS`](SHA256SUMS) exists so that no repo has to assert this by eye. It is the published
digest of every document here, and CI fails if it is stale or does not cover them all.

```sh
# in a repo that vendors a context — fetch the manifest, check the local copy against it
curl -fsSL https://raw.githubusercontent.com/Verilay-Labs/verilay-schemas/main/SHA256SUMS -o SHA256SUMS
sha256sum -c --ignore-missing SHA256SUMS      # shasum -a 256 -c on macOS
```

Assert against **this** manifest, not against a value your own code recomputes — a test that checks a
derivation against your re-derivation of it passes just as happily when both sides are wrong
together.

## Checks

Nothing at runtime reports a context and its JSON Schema drifting apart — the symptom is an issuer
that merklizes a field the verifier cannot see, or a proof that stops matching. Both are checked in
CI on every pull request:

```sh
python3 scripts/validate.py    # context ↔ JSON Schema agree on fields, types and URIs;
                               # SHA256SUMS covers every document and is current

npm install --no-save jsonld@8 ajv@8 ajv-formats@3
node scripts/roundtrip.mjs     # a sample credential validates, then expands with every field intact
```

`fixtures/` holds sample credentials shaped the way the issuers emit them — including one per type
with its optional fields absent, which is the case that is easy to get wrong and expensive to
discover late. They are test inputs, not published documents.

After changing or adding a document, regenerate the manifest:

```sh
shasum -a 256 *.json *.json-ld > SHA256SUMS
```

## Licence

[MIT](LICENSE).
