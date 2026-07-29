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

Everything here is field-name vocabulary and types — `kycApproved`, `documentCountry`, `birthday`.
No keys, no endpoints, no personal data. It has to be public because:

- the issuer resolves the context server-side to merklize a credential;
- a holder's browser may fetch the context while producing a proof;
- `credentialSchema.id` is embedded in every issued credential and must resolve for anyone holding
  one;
- the on-chain policy's schema hash is derived from the type IRI in the context, so a third party
  cannot verify what an age query actually asserts without reading it.

Same posture as [`iden3/claim-schema-vocab`](https://github.com/iden3/claim-schema-vocab).

## These files are immutable once referenced

**Never edit a published document in place.** A credential's schema hash is derived from the type
IRI in its context, and both the issuer and the on-chain policy pin that hash. Changing a published
file silently invalidates every credential and policy that referenced it.

Adding, removing, renaming or retyping a field means **a new version file** — `VerilayKYC-v3.json-ld`
and `VerilayKYC-v3.json` — landed alongside the old ones, which stay where they are forever.

Typo fixes in prose (this README, the `vocab/` notes) are fine. Anything inside a `.json-ld` or
`.json` is not.

## Schemas

### VerilayKYC v2

- Context: <https://raw.githubusercontent.com/Verilay-Labs/verilay-schemas/main/VerilayKYC-v2.json-ld>
- JSON Schema: <https://raw.githubusercontent.com/Verilay-Labs/verilay-schemas/main/VerilayKYC-v2.json>
- Type IRI: `https://raw.githubusercontent.com/Verilay-Labs/verilay-schemas/main/VerilayKYC-v2.json-ld#VerilayKYC`
- Vocabulary: [`vocab/VerilayKYC.md`](vocab/VerilayKYC.md)

Merklized — the context carries no `iden3_serialization` directive, so every subject field is
addressable through the merklization root rather than being packed into fixed claim slots.

| Field | Type | Notes |
|-------|------|-------|
| `kycApproved` | `xsd:boolean` | KYC provider returned an approved decision |
| `documentCountry` | `xsd:string` | ISO 3166-1 alpha-3, e.g. `DEU`; string ⇒ equality/set queries only |
| `birthday` | `xsd:integer` | `YYYYMMDD`, e.g. `19970517`; integer ⇒ range queries, which is what makes an on-chain age check possible |

### There is no v1

`VerilayKYC-v1.json-ld` was referenced by the issuer and the frontend before this repo existed, so
that URL always returned 404 and **nothing valid was ever issued against it**. There is no
back-compat to preserve and no v1 file will be published. Any credential still carrying a v1
`credentialSchema.id` is to be reissued against v2.

## Consumers

Any local copy of a context — for example a frontend bundling it to avoid a network fetch during
proving — must be **byte-identical** to the published file. The schema hash is derived from the
document; a stray whitespace difference produces a different hash and the on-chain query stops
matching.

## Checks

Nothing at runtime reports a context and its JSON Schema drifting apart — the symptom is an issuer
that merklizes a field the verifier cannot see, or a proof that stops matching. Both are checked in
CI on every pull request:

```sh
python3 scripts/validate.py    # context ↔ JSON Schema agree on fields, types and URIs

npm install --no-save jsonld@8 ajv@8 ajv-formats@3
node scripts/roundtrip.mjs     # a sample credential validates, then expands with every field intact
```

`fixtures/` holds one sample credential per schema version, shaped the way the issuer emits them.
They are test inputs, not published documents.

## Licence

[MIT](LICENSE).
