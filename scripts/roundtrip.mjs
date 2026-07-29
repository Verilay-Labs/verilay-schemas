// Check each schema pair against a real credential shaped the way the issuer emits them.
//
// scripts/validate.py compares the two documents to each other. This goes one step further and runs
// an actual credential through both: JSON Schema validation, then JSON-LD expansion using the local
// context. Expansion is the interesting half — a term that silently fails to expand is dropped from
// the merklization tree, and the only downstream symptom is a proof that never matches.
//
// Run: npm install --no-save jsonld ajv ajv-formats && node scripts/roundtrip.mjs

import { readFileSync, readdirSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

import Ajv from "ajv";
import addFormats from "ajv-formats";
import jsonld from "jsonld";

const REPO = join(dirname(fileURLToPath(import.meta.url)), "..");
const RAW_BASE =
  "https://raw.githubusercontent.com/Verilay-Labs/verilay-schemas/main/";

const read = (p) => JSON.parse(readFileSync(join(REPO, p), "utf8"));

const failures = [];
const check = (ok, message) => {
  if (!ok) failures.push(message);
};

// Serve any URL under this repo's raw base from disk, so the check passes before the branch is
// merged and does not depend on the network for our own documents.
const documentLoader = async (url) => {
  if (url.startsWith(RAW_BASE)) {
    return {
      contextUrl: null,
      documentUrl: url,
      document: read(url.slice(RAW_BASE.length).split("#")[0]),
    };
  }
  const response = await fetch(url, {
    headers: { accept: "application/ld+json, application/json" },
  });
  if (!response.ok) throw new Error(`${url} -> HTTP ${response.status}`);
  return { contextUrl: null, documentUrl: url, document: await response.json() };
};

const ajv = new Ajv({ strict: false, allErrors: true });
addFormats(ajv);

for (const file of readdirSync(join(REPO, "fixtures")).sort()) {
  const fixture = read(join("fixtures", file));
  const { credential } = fixture;
  const type = credential.type.at(-1);
  const schemaFile = `${type}-v${fixture.version}.json`;
  const schema = read(schemaFile);

  const validate = ajv.compile(schema);
  check(
    validate(credential),
    `${file}: fails ${schemaFile}: ${ajv.errorsText(validate.errors)}`,
  );

  let expanded;
  try {
    [expanded] = await jsonld.expand(credential, { documentLoader });
  } catch (error) {
    check(false, `${file}: JSON-LD expansion failed: ${error.message}`);
    continue;
  }
  const subject =
    expanded["https://www.w3.org/2018/credentials#credentialSubject"][0];

  // Anything that failed to expand is simply absent from the result — compare against the fields
  // the JSON Schema declares rather than trusting whatever came back.
  const declared = Object.keys(schema.properties.credentialSubject.properties)
    .filter((f) => f !== "id")
    .sort();
  const typeIri = schema.$metadata.uris.jsonLdType;
  const vocabBase = `${typeIri.split("#")[0].replace(RAW_BASE, "")}`;

  for (const field of declared) {
    const iri = Object.keys(subject).find((k) => k.endsWith(`#${field}`));
    check(
      iri !== undefined,
      `${file}: '${field}' did not expand to an absolute IRI — it will be missing from the ` +
        `merklization tree. Check its term definition in the context for ${vocabBase}.`,
    );
    if (iri === undefined) continue;
    check(
      subject[iri][0]["@value"] === credential.credentialSubject[field],
      `${file}: '${field}' expanded to ${JSON.stringify(subject[iri][0]["@value"])}, ` +
        `expected ${JSON.stringify(credential.credentialSubject[field])}`,
    );
  }

  check(
    expanded["@type"].includes(typeIri),
    `${file}: credential type did not expand to ${typeIri}. The on-chain schema hash is derived ` +
      `from this IRI, so a mismatch here means no policy will ever match the credential.`,
  );
  check(
    credential.credentialSchema.id === `${RAW_BASE}${schemaFile}`,
    `${file}: credentialSchema.id must point at the JSON Schema (${RAW_BASE}${schemaFile}), ` +
      `got ${credential.credentialSchema.id}`,
  );
}

if (failures.length > 0) {
  for (const failure of failures) console.error(`FAIL ${failure}`);
  process.exit(1);
}

console.log("ok");
