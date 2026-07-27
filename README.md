# Envuscator Community

Public product, documentation, and release surface for Envuscator.

Envuscator adds randomized, environment-bound obfuscation to Android and iOS build pipelines. The v1 architecture is action/component-first: the engine executes inside customer-controlled GitHub Actions or GitLab CI/CD runners, while Envuscator infrastructure is limited to licensing, workload identity verification, and short-lived access to immutable engine releases.

## Public website

The static site lives in [`web/`](./web):

- `web/index.html`
- `web/styles.css`

It presents the current goals, expected outcomes, trust boundaries, architecture, delivery roadmap, and security limitations.

## Architecture principles

- Customer configuration, source, artifacts, and build logs remain in the customer runner.
- GitHub and GitLab adapters consume the same provider-neutral engine contract.
- Engine releases are immutable, checksummed, signed, and independently verifiable.
- Generated artifacts include deterministic manifests without configuration values.
- Obfuscation is defense in depth, not secret storage or runtime authorization.
- The orchestration boundary will migrate incrementally to Rust behind conformance tests.

## Project boundaries

| Repository | Responsibility |
| --- | --- |
| `mobuild-envuscator` | Private engine, native generation, provider adapters, and release production |
| `envuscator-community` | Public website, documentation, examples, verification material, and release surface |
| `envuscator-web` | Minimal licensing and entitlement service; no hosted customer builds or configuration storage |

## Contact

- Waitlist: `waitlist@envuscator.com`
- Integration and demo requests: `contact@envuscator.com`
