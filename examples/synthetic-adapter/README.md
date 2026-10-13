# Synthetic customer-runner adapter demonstration

**Status: contract illustration only — no native engine, AAR, XCFramework, credential, entitlement, or supported release.**

This runnable, dependency-free fixture demonstrates three parts of Envuscator's intended **customer-runner-local** build integration: accepting a file-based configuration, producing different deterministic *synthetic* output for different build identities, and returning bounded manifest/result evidence while failing closed for malformed inputs.

It is not the real GitHub Action, GitLab Component, native generator, release resolver, obfuscation engine, or the canonical production manifest/result schema. The `android`/`ios` and `Debug`/`Release` switches are labels in this example; they **do not** compile or qualify either mobile platform.

## Run locally (Python 3.10+; standard library only)

Run from a clean clone of this **public** repository:

```sh
work=$(mktemp -d)
cp examples/synthetic-adapter/fixtures/sample.env "$work/config.env"
chmod 600 "$work/config.env"
python3 examples/synthetic-adapter/demo.py \
  --config "$work/config.env" \
  --output "$work/build-a" \
  --build-id fixture-build-A \
  --platform android \
  --build-type Debug
python3 examples/synthetic-adapter/demo.py \
  --config "$work/config.env" \
  --output "$work/build-b" \
  --build-id fixture-build-B \
  --platform android \
  --build-type Debug
# The output directories contain synthetic-artifact.json,
# synthetic-manifest.json and synthetic-result.json.
# Inspect only these benign synthetic outputs; delete the scratch directory afterward.
rm -rf "$work"
```

The checked-in example contains only `https://example.invalid` and a dummy display label. **Never** use real customer configuration or secrets with this illustrative program. No network calls, hosted customer build service, engine archive, signing key, OAuth bearer, or entitlement exchange are used.

## What the test proves and does not prove

- **Deterministic fixture:** identical non-secret input, build ID, platform and build type yield byte-identical sample output and a matching SHA-256 manifest. Different build IDs yield different sample output. This is test data, not cryptographic unpredictability.
- **Fail-closed illustration:** rejects symlinks, world/group-readable configuration, wrong ownership, unsafe key/value framing, duplicate keys, UTF-8/control-character violations, oversized inputs, invalid selectors, and existing output directories. It writes a fresh, private scratch directory and synthetic JSON files; failure text does not print configuration values.
- **Public-output bound:** the demonstration tests reject plaintext synthetic canaries in its generated output and ensure only allowlisted example source files are published. CI exercises the fixture on a fresh checkout without uploading generated payloads.
- **Security claim:** `demonstrative_transform()` deliberately uses a reversible XOR byte stream derived from a **public build ID and public source code**. It is **not encryption** or secret storage. It can be reversed by anyone who has the shipped data and build ID, just as sufficiently capable attackers can inspect client binaries and runtime values. Real layered obfuscation aims to increase extraction cost, **not** to provide confidentiality, identity verification, or backend authorization.
- **Release boundary:** this example cannot establish that the actual Envuscator native engine/adapter conforms, that released binaries are reproducible, or that Android/iOS builds pass. Those remain subject to private engine and adapter conformance, signed immutable release verification, native iOS qualification, production entitlement custody, and activation gates.

## Tests

```sh
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover \
  -s examples/synthetic-adapter/tests -p 'test_*.py' -v
```

The suite checks deterministic reproduction, build-ID variation, output digest/size, denial/failure cases, output permissions, non-disclosure of synthetic canary values, and a closed allowlist of public example files. CI runs it under `.github/workflows/static-site.yml` using only the public repository checkout.

See [local-runner guidance](../../docs/local-runner.md), [compatibility matrix](../../docs/compatibility.md), and [security reporting and scope](../../SECURITY.md). Production/public-adapter promotion is separate work; this fixture must not be advertised as generally available Envuscator execution.
