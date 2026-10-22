# Documentation maintenance contract

**Adoption:** Micrantha's shared `documentation-sync` default, unchanged.

Follow the [shared documentation-sync skill](https://github.com/hackelia-micrantha/.github/blob/main/skills/documentation-sync/SKILL.md) for the review/decision process. This file records only Envuscator-specific ownership, public claim limits, validation commands, and deployment boundaries; it is not a second copy of the shared contract.

## Authority and maintained surfaces

- The private `mobuild-envuscator` project owns the native engine, source behavior, and immutable engine release/signing contracts; provider adapters own their own provider integration and runner execution contracts.
- Private `envuscator-web` owns licensing, entitlement exchange, and entitlement-authorized **private** immutable-engine delivery, not the public product website or customer build execution.
- This `envuscator-community` repository owns the **public** website under `web/`, public documentation and examples, compatibility and security guidance, and the **public signed release-metadata plane** under `web/releases/`. Do not promote private implementation or entitlement material here.
- [Issue #2](https://github.com/hackelia-micrantha/envuscator-community/issues/2) tracks public-site consolidation and remaining external private-entitlement ingress verification. Documentation review does not complete that infrastructure gate.

The public source of truth for site content is `web/index.html` and its adjacent assets, not generated output in another repository. The [root README](../README.md), [compatibility matrix](compatibility.md), [customer-runner guide](local-runner.md), [release-metadata rules](../web/releases/README.md), [security policy](../SECURITY.md), and [synthetic adapter example](../examples/synthetic-adapter/README.md) must remain consistent with the site.

## Capability, security, and availability claims

Preserve the separate states **implemented**, **executable-qualified**, **publicly released/activated**, and **planned**.

- Build-time obfuscation adds a bounded defense-in-depth layer; it is not encryption, secret storage, runtime authorization, or an assertion that client-shipped values cannot be recovered.
- Linux/Android executable qualification is not native iOS qualification, general provider-adapter activation, or a production release.
- Customer-controlled runner/non-custody is the accepted v1 execution boundary; do not imply that the public Worker or private entitlement service runs customer builds.
- Public signed release metadata and entitlement-gated private engine archives are separate planes. Public hosting is **distribution, not trust**; signed statements, descriptors, and archive identity must be verified independently.
- Do not claim production signing, a published supported engine version, active paid licensing, operational completeness, or a specific private ingress restriction from source or CI alone.

## Source and preview validation

Use the smallest applicable existing validation at the exact candidate SHA:

```sh
# Requires Python 3.11+ for tomllib-based public routing checks.
python3 scripts/verify_site.py
python3 scripts/test_validate_release_metadata.py
python3 scripts/validate_release_metadata.py
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s examples/synthetic-adapter/tests -p 'test_*.py'
```

The repository's [Static site workflow](../.github/workflows/static-site.yml) also executes a synthetic demo and serves `web/` for a local HTTP smoke test. These checks establish source and local behavior only; the demo has **no** production-engine or adapter authority.

For local visual inspection, serve `web/` with `python3 -m http.server 8080 --directory web`. Inspect the local page, link targets, status labels, and accessibility when changing presentation. Do not claim an external browser/rendered-production check from a source validator alone.

## Live deployment and release boundaries

[`wrangler.toml`](../wrangler.toml) declares the `envuscator-community` Worker, static asset root `./web`, Custom Domains `envuscator.com` and `envuscator.micrantha.com`, and the distinct `www.envuscator.com/*` Worker Route. An accepted source diff does **not** authorize Cloudflare deployment, DNS/routing changes, signing, a public release, or engine distribution.

After an explicitly authorized deployment, independently compare the live Cloudflare Worker/route inventory and deployed revision with that reviewed source, then verify the public page and `/.well-known/security.txt` on each configured hostname. An inaccessible fetch client is **indeterminate**, not evidence of an outage or a successful deployment.

For release-metadata work, enforce the [public release-tree contract](../web/releases/README.md), validate exact version/target paths, reject archive/key/private-customer material, and separately verify signing trust and immutable private archive acquisition before claiming a release active. A green public source check does not grant publication authority.

## Recurrence and decisions

Run documentation-sync after engine or adapter capability changes, compatibility decisions, signed-metadata/release transitions, security-claim changes, public/private repository changes, or Cloudflare routing/deployment changes. Prefer event-driven, project-owned updates; do not mirror private status reports or duplicate the shared skill.

Raise material unresolved public security, release, commercial, or routing claims through the shared `DOC-Q*` human-decision queue. No additional skill specialization is currently required.
