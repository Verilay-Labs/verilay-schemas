#!/usr/bin/env python3
"""Check that every published schema pair is internally consistent.

The files in this repo are consumed by an issuer, a browser prover and an on-chain policy that
never see each other. Nothing at runtime will tell us a context and its JSON Schema drifted apart —
the symptom is a proof that silently stops matching. So the invariants are checked here instead.

Run: python3 scripts/validate.py
"""

import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
RAW_BASE = "https://raw.githubusercontent.com/Verilay-Labs/verilay-schemas/main/"

errors = []


def check(condition, message):
    if not condition:
        errors.append(message)


def raw_url_to_path(url):
    """Map a published raw URL back to the file it must be served from."""
    if not url.startswith(RAW_BASE):
        return None
    return REPO / url[len(RAW_BASE):].split("#")[0]


for schema_path in sorted(REPO.glob("*.json")):
    name = schema_path.name
    schema = json.loads(schema_path.read_text())

    meta = schema.get("$metadata", {})
    uris = meta.get("uris", {})
    check("uris" in meta, f"{name}: missing $metadata.uris")

    ctx_url = uris.get("jsonLdContext")
    check(bool(ctx_url), f"{name}: missing $metadata.uris.jsonLdContext")
    if not ctx_url:
        continue

    ctx_path = raw_url_to_path(ctx_url)
    check(
        ctx_path is not None and ctx_path.is_file(),
        f"{name}: $metadata.uris.jsonLdContext does not resolve to a file in this repo: {ctx_url}",
    )
    if ctx_path is None or not ctx_path.is_file():
        continue

    self_url = uris.get("jsonSchema")
    check(
        raw_url_to_path(self_url or "") == schema_path,
        f"{name}: $metadata.uris.jsonSchema must point at this file, got {self_url!r}",
    )

    # The context is a list holding a single term-definition object.
    context = json.loads(ctx_path.read_text())["@context"][0]

    cred_type = meta.get("type")
    check(bool(cred_type), f"{name}: missing $metadata.type")
    check(
        cred_type in context,
        f"{name}: $metadata.type {cred_type!r} is not defined in {ctx_path.name}",
    )
    if cred_type not in context:
        continue

    type_def = context[cred_type]
    type_iri = type_def["@id"]
    check(
        type_iri == f"{ctx_url}#{cred_type}",
        f"{ctx_path.name}: {cred_type}.@id must be '{ctx_url}#{cred_type}', got {type_iri!r}. "
        "The on-chain schema hash is derived from this IRI.",
    )
    check(
        uris.get("jsonLdType") == type_iri,
        f"{name}: $metadata.uris.jsonLdType must equal the context type IRI {type_iri!r}, "
        f"got {uris.get('jsonLdType')!r}",
    )

    terms = type_def["@context"]
    check(
        "iden3_serialization" not in terms,
        f"{ctx_path.name}: {cred_type} carries an iden3_serialization directive, which turns off "
        "merklization. Verilay credentials must stay merklized.",
    )

    # Every subject field the JSON Schema declares must have a term in the context, and vice versa —
    # a field defined in only one of the two is invisible to half the stack.
    subject = schema["properties"]["credentialSubject"]
    declared = set(subject["properties"]) - {"id"}
    defined = {k for k, v in terms.items() if isinstance(v, dict) and k not in ("id", "type")}
    check(
        declared == defined,
        f"{name}: credentialSubject fields {sorted(declared)} do not match the terms defined in "
        f"{ctx_path.name} {sorted(defined)}",
    )

    # Fields may legitimately be optional — the KYC provider does not always return every attribute,
    # and an absent field is simply not in the merklization tree. What must not happen is `required`
    # naming something the schema does not declare: that is a typo no validator would ever fire on,
    # because the field can never be present to be checked.
    required = set(subject.get("required", []))
    check(
        "id" in required,
        f"{name}: credentialSubject.required must include id",
    )
    check(
        required <= declared | {"id"},
        f"{name}: credentialSubject.required names undeclared fields "
        f"{sorted(required - declared - {'id'})}",
    )

    # A term's XSD type and its JSON Schema type describe the same value; if they disagree the
    # issuer merklizes something other than what validation accepted.
    xsd_to_json = {
        "xsd:boolean": "boolean",
        "xsd:string": "string",
        "xsd:integer": "integer",
        "xsd:positiveInteger": "integer",
        "xsd:dateTime": "string",
        "xsd:double": "number",
    }
    for field in sorted(declared & defined):
        xsd = terms[field]["@type"]
        check(
            xsd in xsd_to_json,
            f"{ctx_path.name}: {field} has unmapped @type {xsd!r}",
        )
        if xsd in xsd_to_json:
            check(
                subject["properties"][field].get("type") == xsd_to_json[xsd],
                f"{name}: {field} is {subject['properties'][field].get('type')!r} but "
                f"{ctx_path.name} types it {xsd!r}",
            )

        vocab_iri = terms[field]["@id"]
        check(
            vocab_iri.endswith(f":{field}"),
            f"{ctx_path.name}: {field} maps to {vocab_iri!r}, expected a term ending in ':{field}'",
        )

    # The vocab prefix must resolve to a file we actually publish, or the IRIs are 404s again —
    # which is the exact failure this repo exists to fix.
    for prefix, target in terms.items():
        if isinstance(target, str) and target.startswith("https://github.com/Verilay-Labs/"):
            rel = re.sub(r"^.*/blob/main/", "", target).split("#")[0]
            check(
                (REPO / rel).is_file(),
                f"{ctx_path.name}: prefix {prefix!r} points at {target!r}, which is not a file in "
                "this repo",
            )

if errors:
    for error in errors:
        print(f"FAIL {error}", file=sys.stderr)
    sys.exit(1)

print("ok")
