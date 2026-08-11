# Envuscator signed release metadata

This directory is the **public metadata plane** for entitlement-gated Envuscator engine releases. It is deliberately separate from private engine archive storage.

## Layout

Production-signed release metadata is published only at exact version and target paths:

```text
/releases/v1/<engine-version>/<target>/release.statement.json
/releases/v1/<engine-version>/<target>/release.statement.sig
/releases/v1/<engine-version>/<target>/release.json
```

Supported targets are:

- `darwin-arm64`
- `darwin-x86_64`
- `linux-arm64`
- `linux-x86_64`

The execution path selects an exact semantic version and target. It does **not** trust a mutable `latest` pointer or catalog entry to select executable code.

## Trust model

Public hosting provides distribution, not trust.

Consumers must independently verify the canonical release statement signature and signing-key lifecycle using a reviewed, pinned trust bundle. They must then verify the canonical descriptor size, SHA-256 digest, and release identity against that signed statement before using its engine version, archive digest, or archive size.

The descriptor field `archive_url` is not authoritative for the commercial entitlement-gated path. Engine archive retrieval remains confined to the separately reviewed fixed Envuscator service origin after workload entitlement exchange.

## Never publish here

Do not publish any of the following under `web/releases/v1`:

- engine archives or checksum files;
- private signing keys or signing credentials;
- release-store credentials;
- workload identity tokens or entitlements;
- customer configuration, source code, generated code, artifacts, or logs;
- mutable trust bundles supplied alongside a release;
- arbitrary redirect or download metadata intended to select an archive origin.

Only the three signed metadata files for an exact version/target belong in each release directory.

## Publication state

The release tree intentionally remains empty until production signing authority and a production release are provisioned. Repository validation permits an absent/empty `web/releases/v1` tree, but once a release directory exists it must be complete and internally consistent.

See `scripts/validate_release_metadata.py` for repository-level structural checks. Cryptographic signature verification remains a consumer responsibility and is enforced in the adapter contract rather than by trusting this repository alone.
