# Envuscator

**A mobile build-time obfuscation layer for Android and iOS delivery pipelines.**

Envuscator is an incubating Micrantha Solution that protects selected mobile configuration values by transforming them during CI/CD into generated native artifacts with per-use runtime decoding.

It is an additional defense layer, not a substitute for secure backend design, platform attestation, secret rotation, or the assumption that application binaries and shipped configuration can eventually be inspected.

## Product role

Envuscator is designed to make mobile configuration extraction less predictable and more expensive while fitting into existing customer-controlled build pipelines.

The product boundary consists of:

- a provider-neutral native engine;
- Android and iOS artifact generation;
- a local command-line interface;
- a GitHub Action adapter;
- a GitLab CI/CD Component adapter;
- licensing and entitlement verification;
- normalized manifests, checksums, SBOM metadata, and provenance where available.

## Delivery and commercial model

The v1 commercial surface is being designed around **licensed CI adapters** rather than hosted customer builds:

| Surface | Delivery model |
| --- | --- |
| GitHub | Versioned GitHub Action using workload identity for entitlement exchange |
| GitLab | Versioned GitLab CI/CD Component using GitLab job identity |
| Local | CLI using the same provider-neutral execution contract |
| Web | Licensing, entitlement, account, and product information only |

Customer source code, mobile configuration, and generated build content remain on customer-controlled runners. The adapters resolve and verify an immutable signed engine and must not require a consumer personal access token to check out mutable private engine source.

The GitHub and GitLab integrations are intended to provide consistent product semantics while supporting subscriptions, organization entitlements, trials, and future offline licenses. Implementation remains in progress; this repository does not claim that every commercial surface is generally available today.

## Security boundary

Envuscator accepts a local configuration file materialized by the CI platform's protected secret mechanism. Plaintext or base64 configuration values are not intended to be ordinary workflow, component, JSON, or command-line inputs.

A canonical execution handles exactly one platform and one build type:

```text
GitHub Action / GitLab Component / local CLI
                    |
                    v
          entitlement verification
                    |
                    v
        immutable engine verification
                    |
                    v
       configuration source generation
                    |
                    v
        Android AAR or iOS XCFramework
                    |
                    v
 manifest + checksums + provenance metadata
```

Expected controls include:

- immutable version and digest verification;
- workload-identity-based entitlement exchange;
- restrictive temporary-file permissions;
- explicit Android or iOS execution boundaries;
- secret and canary-value leak scanning;
- cleanup verification;
- provider-neutral error categories and manifests;
- no hosted build orchestration in the v1 trust boundary.

## Relationship to other Micrantha projects

Envuscator complements other mobile security layers rather than replacing them:

- **Digitalis** addresses device attestation and secure runtime configuration delivery.
- **Veil** explores privacy-preserving image concealment.
- **Bluebell** provides reusable Kotlin Multiplatform build and SDK patterns.
- **Mobuild** provides the wider modular mobile-build architecture in which Envuscator originated.

## Current platform scope

- Android
- iOS
- ARM, ARM64, x86, and x86_64 where supported by the selected platform toolchain

## Status

Envuscator is **Incubating**. Its provider-neutral adapter contract, customer-runner trust boundary, GitHub/GitLab parity, immutable engine model, and licensing direction are accepted architectural decisions under active implementation.

## Contact

- Waitlist: `waitlist@envuscator.com`
- Contact or demo: `contact@envuscator.com`
