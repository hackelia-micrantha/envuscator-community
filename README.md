# Envuscator Community

Public product, documentation, and release surface for Envuscator.

Envuscator is building a runner-local mobile security layer that adds randomized, environment-bound obfuscation to Android and iOS build pipelines. Native generation exists today; the provider-neutral engine contract, GitHub/GitLab adapters, signed distribution, entitlement service, and Rust orchestration migration are being delivered incrementally.

## Public website

The static site lives in [`web/`](./web):

- `web/index.html`
- `web/styles.css`

It separates current foundations, work in progress, and target-v1 architecture so planned security properties are not presented as deployed guarantees.

## Deployment contract

This repository is the intended authoritative public documentation and product surface.

- Source directory: `web/`
- Build step: none
- Output directory: `web/`
- Deployment target: static hosting such as Cloudflare Pages or GitHub Pages
- Production hostname: to be finalized as part of the duplicate-site retirement tracked in issue #2
- `https://envuscator.micrantha.com`: currently a separate concept/demo application and not evidence that the complete runner-local v1 architecture is deployed

Until the production hostname and hosting integration are finalized, merging website changes updates the authoritative source but may not update the currently linked demo application.

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
- The orchestration boundary migrates incrementally to Rust behind conformance tests.

## Project boundaries

| Repository | Current role | Target role |
| --- | --- | --- |
| `mobuild-envuscator` | Private implementation and native generation | Engine, provider adapters, and release producer |
| `envuscator-community` | Public static content | Authoritative website, documentation, examples, verification material, and release surface |
| `envuscator-web` | Existing demo/application code | Minimal licensing and entitlement service with no hosted customer builds or configuration storage |

## Validation

The repository includes a dependency-free validation script and GitHub Actions workflow.

```sh
python3 scripts/verify_site.py
```

The validation checks:

- HTML parses successfully
- internal fragment links resolve
- required metadata and headings exist
- the architecture is represented as an ordered list
- stylesheet references resolve
- CSS braces are balanced
- current-state and target-state labels remain present

## Local preview

```sh
python3 -m http.server 8080 --directory web
```

Then open `http://localhost:8080`.

## Contact

- Waitlist: `waitlist@envuscator.com`
- Integration and demo requests: `contact@envuscator.com`
