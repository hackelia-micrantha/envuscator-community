# Envuscator compatibility matrix

Status: **Incubating / pre-activation**  
Last reviewed: **2026-10-05**

This document is the public compatibility projection of the current Envuscator engine and provider-adapter contracts. It separates **contracted** targets, **qualified** execution evidence, and **publicly available** releases. A contracted target is not automatically qualified or publicly available.

## Mobile platform outputs

| Mobile platform | Output | Application/runtime architectures | Build types | Toolchain boundary | Current status |
| --- | --- | --- | --- | --- | --- |
| Android | AAR | `armeabi-v7a`, `arm64-v8a`, `x86`, `x86_64` | `Debug`, `Release` | CMake 3.10+; Android NDK required. Current CI pins NDK `27.1.12297006` and Android platform 29, but that pin is evidence rather than a published supported-version range. | Native generation exists. Linux/Android engine execution is qualified on the repository-scoped rootless JIT path. Public provider wrappers remain activation-gated. |
| iOS | XCFramework | `arm64`, `x86_64` | `Debug`, `Release` | CMake 3.10+; Xcode/`xcodebuild` required. No public supported Xcode-version range is declared yet. | Native generation exists. Native iOS qualification remains an explicit release gate. Public provider wrappers remain activation-gated. |

The mobile architectures above describe the generated application artifact. They are distinct from the host architecture of the immutable Envuscator engine archive.

## Engine host targets

The release-descriptor v1 contract accepts exactly these immutable engine archive targets:

| Engine host target | Contracted | Current public-release status |
| --- | --- | --- |
| `linux-x86_64` | Yes | Contract-valid; exact production availability will be established by signed release metadata after signing/publication gates pass. |
| `linux-arm64` | Yes | Contract-valid; exact production availability will be established by signed release metadata after signing/publication gates pass. |
| `darwin-x86_64` | Yes | Contract-valid; exact production availability will be established by signed release metadata after signing/publication gates pass. |
| `darwin-arm64` | Yes | Contract-valid; exact production availability will be established by signed release metadata after signing/publication gates pass. |

There is no Windows engine-host target in release-descriptor v1. When public releases are activated, exact signed release metadata is authoritative for whether a particular engine version/target archive actually exists.

## Provider adapters

| Provider | Host mapping | Mobile selectors | Identity boundary | Activation status |
| --- | --- | --- | --- | --- |
| GitHub Actions | Linux/macOS × x86_64/arm64 map to the four engine targets above | Android, iOS; Debug, Release | GitHub OIDC; the authorized online path requires caller `id-token: write` | Authorized orchestration is implemented internally, but is not yet wired as the public production Action path. |
| GitLab CI/CD | Linux/Darwin × x86_64/arm64 map to the four engine targets above | Android, iOS; Debug, Release | Explicit modern GitLab `id_tokens:` JWT | Authorized orchestration is implemented internally, but is not yet wired as the public production Component path. |

Provider support therefore describes the implemented adapter contract, not current public availability.

## Artifact and evidence contract

A successful platform build produces:

- the platform artifact: AAR for Android or XCFramework for iOS;
- a deterministic build manifest containing artifact kind/path/SHA-256, platform, build type, engine version, source revision, and schema versions;
- normalized resolver, execution, and adapter results through the provider-neutral adapter boundary.

The immutable engine release descriptor binds one engine version/source revision to one exact host target, a `tar.gz` archive identity/digest/size, required entrypoints, schema versions, adapter contract version 1, and entitlement trust metadata.

## Configuration-file boundary

The public CI adapter contract consumes a local configuration file path on the customer-controlled runner. The current v1 parser boundary includes a regular file owned by the current user or root, no group/world permission bits (`0600` recommended), no symlinks/special files, maximum size 1 MiB, maximum 1024 entries, keys up to 128 bytes matching `[A-Za-z_][A-Za-z0-9_]*`, and values up to 16 KiB.

This is an input-compatibility boundary, not a claim that shipped client configuration becomes unrecoverable.

## Not yet a public compatibility promise

The following are intentionally not claimed as supported public ranges yet:

- a general Android SDK/NDK version range beyond current executable CI evidence;
- a supported Xcode/macOS version range;
- production availability of every contract-valid engine host target;
- a stable public Action or GitLab Component release line;
- native iOS qualification;
- long-term upgrade/deprecation guarantees before the first supported immutable release line.

## Maintenance rule

This matrix must be updated from authoritative contracts/evidence, not inferred from marketing copy. Current canonical sources are the private engine release descriptor/build-manifest/toolchain contracts, the GitHub/GitLab authorized-adapter host mappings, and the public Envuscator qualification/activation status. If those sources disagree, the public matrix must fail conservative and document the narrower supported state until the owning contract is reconciled.
