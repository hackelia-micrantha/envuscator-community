# Envuscator Community

**Public product, documentation, and release surface for Envuscator.**

Envuscator is an incubating Micrantha Solution that adds a mobile build-time obfuscation layer to Android and iOS delivery pipelines. Native generation exists today; the provider-neutral engine contract, GitHub and GitLab adapters, signed distribution, entitlement service, deterministic evidence, and Rust orchestration migration are being delivered incrementally.

It is an additional defense layer, not a substitute for secure backend design, platform attestation, secret rotation, or the assumption that application binaries and shipped configuration can eventually be inspected.

## Product role

Envuscator is designed to make selected mobile configuration extraction less predictable and more expensive while fitting into customer-controlled build pipelines.

The target product boundary includes:

- a provider-neutral native engine;
- Android and iOS artifact generation;
- a local command-line interface;
- a GitHub Action adapter;
- a GitLab CI/CD Component adapter;
- licensing and entitlement verification;
- normalized manifests, checksums, SBOM metadata, and provenance where available.

Implementation remains in progress; this repository does not claim that every commercial surface or target security property is generally available today.

## Public website

The authoritative static site lives in [`web/`](./web):

- `web/index.html`
- `web/styles.css`

It separates current foundations, work in progress, and target-v1 architecture so planned security properties are not presented as deployed guarantees.

## Deployment contract

- Source directory: `web/`
- Build step: none
- Output directory: `web/`
- Cloudflare configuration: [`wrangler.toml`](./wrangler.toml)
- Production hostname: to be finalized as part of the duplicate-site retirement tracked in issue #2
- `https://envuscator.micrantha.com`: currently a separate concept/demo application and not evidence that the complete runner-local v1 architecture is deployed

The Cloudflare Workers integration serves `web/` as static assets. This repository is the intended authoritative public documentation and product surface.

## Delivery and commercial model

The v1 commercial surface is being designed around **licensed CI adapters** rather than hosted customer builds:

| Surface | Target delivery model |
| --- | --- |
| GitHub | Versioned GitHub Action using workload identity for entitlement exchange |
| GitLab | Versioned GitLab CI/CD Component using GitLab job identity |
| Local | CLI using the same provider-neutral execution contract |
| Web | Licensing, entitlement, account, and product information only |

Customer source code, protected mobile configuration, generated artifacts, and build logs remain on customer-controlled runners in the target v1 trust boundary. Adapters resolve and verify immutable engine releases and must not require consumer personal access tokens to check out mutable private engine source.

## Architecture principles

### Current foundations

- Native Android and iOS generation paths exist.
- Build-time configuration and obfuscation concepts are implemented in the existing engine.
- Obfuscation is treated as defense in depth, not secret storage or runtime authorization.

### Target v1 contract

- Customer configuration, source, artifacts, and build logs remain in the customer runner.
- GitHub and GitLab adapters consume the same provider-neutral engine contract.
- Engine releases are immutable, checksummed, signed, and independently verifiable.
- Generated artifacts include deterministic manifests without configuration values.
- Plaintext temporary material is permission-restricted, leak-scanned, and cleanup-verified.
- The orchestration boundary migrates incrementally to Rust behind conformance tests.
- Hosted customer build orchestration remains outside the v1 trust boundary.

## Project boundaries

| Repository | Current role | Target role |
| --- | --- | --- |
| `mobuild-envuscator` | Private implementation and native generation | Engine, provider adapters, and release producer |
| `envuscator-community` | Public static content | Authoritative website, documentation, examples, verification material, and release surface |
| `envuscator-web` | Existing demo/application code | Minimal licensing and entitlement service with no hosted customer builds or configuration storage |

## Relationship to other Micrantha projects

- **Digitalis** addresses device attestation and secure runtime configuration delivery.
- **Veil** explores privacy-preserving image concealment.
- **Bluebell** provides reusable Kotlin Multiplatform build and SDK patterns.
- **Mobuild** provides the wider modular mobile-build architecture in which Envuscator originated.

## Validation

The repository includes a dependency-free validation script and GitHub Actions workflow.

```sh
python3 scripts/verify_site.py
```

Validation checks include HTML parsing, internal fragment links, metadata, heading structure, semantic architecture markup, stylesheet resolution, balanced CSS, Micrantha brand tokens, and current-versus-target state labels.

## Local preview

```sh
python3 -m http.server 8080 --directory web
```

Then open `http://localhost:8080`.

## Status

Envuscator is **Incubating**. Its provider-neutral adapter contract, customer-runner trust boundary, GitHub/GitLab parity, immutable engine model, and licensing direction are accepted architectural decisions under active implementation.

## Contact

- Waitlist: `waitlist@envuscator.com`
- Integration and demo requests: `contact@envuscator.com`
