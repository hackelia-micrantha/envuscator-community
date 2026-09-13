# Envuscator Community

**Public product, documentation, and release surface for Envuscator.**

Envuscator is an incubating Micrantha Solution that adds an extra build-specific security layer to Android and iOS delivery pipelines through layered configuration obfuscation and per-build transformation.

It is defense in depth, not a substitute for secure backend design, platform attestation, secret rotation, authorization, or the assumption that application binaries and shipped client-side configuration can eventually be inspected by a sufficiently capable attacker.

## Current project state

The core architecture has moved beyond the initial concept/demo stage:

- native Android and iOS generation paths exist;
- the provider-neutral immutable-engine and entitlement contracts are implemented;
- customer-runner execution and non-custody are accepted v1 boundaries;
- signed public release-metadata and private immutable-engine delivery are separate trust/distribution planes;
- the private entitlement service has executable-qualified workload identity, normalized licensing, short-lived entitlement issuance, private-engine authorization, replay-safe persistence, and durable commercial reconciliation foundations;
- Linux/Android engine CI has executed successfully on the rootless JIT runner path;
- production signing identities, external entitlement-service deployment, public adapter activation, production release publication, and native iOS qualification remain activation gates.

This repository does **not** claim that the commercial service, production signing chain, public adapters, or every target platform path are generally available today.

## Product role

Envuscator is designed to make selected mobile configuration extraction less predictable and more expensive while fitting into customer-controlled build pipelines.

The v1 product boundary includes:

- a provider-neutral native engine;
- Android and iOS artifact generation;
- customer-runner/local execution;
- GitHub and GitLab CI adapters;
- workload-identity-based licensing and entitlement verification;
- immutable signed release metadata with entitlement-gated engine archives;
- normalized manifests, checksums, SBOM metadata, and provenance where available.

The intended effect is friction against accidental disclosure and opportunistic static extraction. It is not encryption or secret storage, and it does not make values used by client code unrecoverable at runtime.

## Public website and release metadata

The authoritative static surface lives in [`web/`](./web):

- `web/index.html`
- `web/styles.css`
- [`web/releases/`](./web/releases/) for signed release metadata only

The site separates current foundations, work in progress, and target-v1 architecture so planned security properties are not presented as deployed guarantees.

The release metadata plane is intentionally separate from private engine archive storage. Exact-version metadata uses the reserved layout:

```text
/releases/v1/<engine-version>/<target>/release.statement.json
/releases/v1/<engine-version>/<target>/release.statement.sig
/releases/v1/<engine-version>/<target>/release.json
```

Public hosting is distribution, not trust. Consumers independently verify the signed release statement and descriptor before using version, digest, or size. The entitlement-gated commercial path does not trust descriptor `archive_url` for private engine retrieval. See [`web/releases/README.md`](./web/releases/README.md).

Production metadata is published only after the production release-signing identity and trust path are provisioned and reviewed.

## Deployment contract

- Source directory: `web/`
- Build step: none
- Output directory: `web/`
- Cloudflare configuration: [`wrangler.toml`](./wrangler.toml)
- Production hostname: to be finalized as part of duplicate-site retirement
- `https://envuscator.micrantha.com`: a separate historical concept/demo surface and not evidence that the complete runner-local v1 architecture is deployed

The Cloudflare Workers integration serves `web/` as static assets. This repository is the intended authoritative public documentation, signed metadata, and product surface.

The private entitlement service uses a separate origin and must not serve this public product UI.

## Delivery and commercial model

Envuscator v1 is customer-runner-first rather than a hosted customer-build service:

| Surface | Delivery model / state |
| --- | --- |
| GitHub | Versioned Action using workload identity for entitlement exchange; public activation remains gated |
| GitLab | Versioned CI/CD Component using GitLab job identity; public activation remains gated |
| Local | Customer-runner/local engine path; paid local/offline licensing is a separate later contract and does not reuse CI identity fiction |
| Web | Private licensing, entitlement, private-engine delivery, account, and product information only |

Customer source code, protected mobile configuration, generated artifacts, and build logs remain on customer-controlled runners in the v1 trust boundary. Adapters resolve and verify immutable engine releases and must not require consumer personal access tokens to check out mutable private engine source.

Commercial authorization is normalized before it reaches the engine/adapter contract. Payment-provider identifiers are not part of signed workload entitlements.

## Architecture principles

### Implemented foundations

- Native Android and iOS generation paths exist.
- Build-time configuration and layered obfuscation are implemented in the engine.
- Obfuscation is treated as defense in depth, not secret storage or runtime authorization.
- Configuration-file input is bounded and designed to remain runner-local.
- The entitlement service has fail-closed GitHub/GitLab workload identity, normalized license policy, durable replay-safe authority state, canonical short-lived entitlement issuance, and entitlement-authorized private-engine delivery.
- Commercial reconciliation has durable event-ledger, source-binding, generation/fencing, revision, and crash-recoverable fan-out foundations without making webhook arrival order authoritative.
- Linux/Android rootless JIT executable qualification exists for the engine; native iOS qualification is still a separate gate.

### V1 invariants

- Customer configuration, source, artifacts, and build logs remain in the customer runner.
- GitHub and GitLab adapters consume the same provider-neutral engine and entitlement contracts.
- Engine releases are immutable, checksummed, signed, and independently verifiable.
- Signed release metadata can be distributed publicly while engine archives remain entitlement-gated.
- Public hosting is never the signing or authorization trust root.
- Generated artifacts include deterministic manifests without configuration values.
- Plaintext temporary material is permission-restricted, leak-scanned, and cleanup-verified.
- Hosted customer build orchestration remains outside the v1 trust boundary.
- Production route activation remains fail closed until deployment, signing, release trust, and executable qualification gates are satisfied.

### Later evolution

- Rust orchestration remains an incremental migration behind existing contracts and conformance tests rather than a prerequisite for the first supported v1 release.
- Paid local/offline licensing requires its own auditable identity, renewal, revocation, and recovery model rather than fabricating a `local` CI provider.

## Project boundaries

| Repository | Current authoritative role |
| --- | --- |
| `mobuild-envuscator` | Private provider-neutral engine, native generation/runtime, immutable release and signing contracts |
| `actions` | Provider adapters, workload identity acquisition, public metadata verification, entitlement exchange, private-engine acquisition, and runner-side sequencing |
| `envuscator-web` | Private licensing/entitlement authority and entitlement-authorized immutable-engine delivery service; no hosted customer builds/configuration custody |
| `envuscator-community` | Authoritative public website, documentation, examples, verification guidance, signed release metadata, and public product surface |

These are explicit trust and ownership boundaries. A public site does not create product truth, the entitlement service does not become a build plane, and provider adapters do not weaken engine verification semantics.

## Relationship to other Micrantha projects

- **Digitalis** addresses device attestation and secure runtime configuration delivery.
- **Veil** explores privacy-preserving image concealment.
- **Bluebell** provides reusable Kotlin Multiplatform build and SDK patterns.
- **Mobuild** provides wider modular mobile-build architecture and coordination; Envuscator repositories retain authority over their own implementation and security contracts.

## Validation

The repository includes dependency-free validation scripts and GitHub Actions coverage.

```sh
python3 scripts/verify_site.py
python3 scripts/test_validate_release_metadata.py
python3 scripts/validate_release_metadata.py
```

Site validation checks HTML parsing, internal fragment links, metadata, heading structure, semantic architecture markup, stylesheet resolution, balanced CSS, Micrantha brand tokens, and current-versus-target state labels.

Release metadata validation rejects unexpected release payloads, archive/key publication, unsafe paths, non-canonical metadata, version/target path mismatches, and statement/descriptor identity disagreement. Cryptographic signature verification remains mandatory in consumers; repository validation does not substitute for it.

## Local preview

```sh
python3 -m http.server 8080 --directory web
```

Then open `http://localhost:8080`.

## Status

Envuscator is **Incubating**. The engine/non-custody/entitlement architecture is substantially implemented, while public activation remains gated on production signing and release trust, entitlement-service deployment, provider-adapter promotion, remaining operational qualification, and supported native iOS qualification.

## Contact

- Waitlist: `waitlist@envuscator.com`
- Integration and demo requests: `contact@envuscator.com`
