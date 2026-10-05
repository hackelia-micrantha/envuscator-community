# Local customer-runner guidance

Status: **Incubating / pre-activation**  
Last reviewed: **2026-10-05**

Envuscator v1 is customer-runner-first. The build and protected configuration stay on infrastructure controlled by the customer; Envuscator's service boundary is for licensing/entitlement and immutable engine delivery, not hosted customer builds.

This document describes the local execution boundary that exists today. It is **not** a public installation quickstart and does not claim that a paid offline/local licensing product is available.

## What “local” means

A local/customer-runner execution keeps the sensitive build path on a machine or runner you control:

1. materialize the configuration file locally;
2. obtain and verify the exact immutable engine release through the applicable release/authorization path;
3. run the engine locally for Android or iOS;
4. retain the generated artifact, build manifest, normalized execution evidence, and logs under your own retention policy;
5. clean up temporary plaintext/configuration material locally.

Customer source, protected configuration, generated artifacts, and build logs are not sent to Envuscator for hosted compilation in the v1 trust model.

## Configuration file boundary

The public adapter contract uses a local configuration file path rather than inline workflow strings, JSON, or base64 configuration payloads.

Current v1 constraints include:

- regular file owned by the current user or root;
- no group/world permission bits (`0600` recommended);
- symlinks and special files rejected;
- maximum file size 1 MiB;
- maximum 1024 entries;
- one non-empty `KEY=value` record per line;
- keys matching `[A-Za-z_][A-Za-z0-9_]*`, at most 128 bytes;
- values at most 16 KiB, valid UTF-8, with ASCII control bytes rejected.

Do not place protected configuration in command-line arguments, public CI variables, logs, issue comments, or durable diagnostic output.

## Platform prerequisites

See [`compatibility.md`](./compatibility.md) for the current matrix. In summary:

- Android produces an AAR and requires the Android NDK/CMake toolchain;
- iOS produces an XCFramework and requires Xcode/`xcodebuild` plus CMake;
- exact supported public toolchain ranges are not yet declared;
- native iOS qualification remains a release gate.

## Verification remains mandatory

Local execution does not weaken release verification. When public immutable releases are activated, a consumer must still verify the exact signed release metadata, expected engine target, archive identity/digest/size, and required entrypoints before execution.

Public hosting is distribution, not the trust root, and a locally cached archive is not trusted merely because it was downloaded previously.

## Licensing boundary

CI workload identity and paid local/offline licensing are separate problems.

- GitHub authorization is bound to GitHub workload identity.
- GitLab authorization is bound to GitLab job identity.
- A future paid local/offline mode must define its own auditable identity, renewal, revocation, recovery, and authorization semantics.
- It must not fabricate a `local` CI provider or reuse provider identity claims when no provider workload exists.

Until that separate contract is reviewed and activated, local development/execution capability must not be presented as a generally available paid offline license.

## What is not available yet

This documentation does not provide a public install command because no supported immutable public engine release line has been promoted yet. Android/GitLab/iOS quickstarts remain gated on their corresponding public adapter, signing, release-publication, and qualification work.

Once those gates pass, this guide can become an executable quickstart by adding only the reviewed acquisition/version commands; the runner-local trust and data-custody boundaries above should remain unchanged.
