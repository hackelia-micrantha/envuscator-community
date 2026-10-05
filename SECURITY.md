# Security Policy

Envuscator is an incubating security-focused project. This policy covers the public community surface and provides a private reporting path for vulnerabilities that may affect the wider Envuscator system.

## Supported versions

Envuscator does not yet publish a production-supported release line.

Security fixes are applied to the active development line and to promoted releases when such releases exist. Historical concept/demo deployments, unpublished adapters, experimental interfaces, and unreleased artifacts should not be treated as supported production versions unless their documentation explicitly says otherwise.

## Reporting a vulnerability

**Do not report suspected vulnerabilities through public issues, pull requests, discussions, or social channels.**

1. **Prefer GitHub private vulnerability reporting** for this repository when that option is available.
2. If private vulnerability reporting is unavailable, email **contact@envuscator.com** with a subject that clearly identifies the message as a security report.
3. Include the affected repository, component, version or commit when known; a concise description; safe reproduction steps; likely impact; and any mitigation you have already identified.

Do not send live credentials, private signing material, customer source/configuration, production data, or unrelated personal information. Share only the minimum sensitive material needed to establish the issue, and coordinate before sending larger exploit artifacts or private logs.

## Scope

Security reports may cover:

- the public website, Cloudflare deployment configuration, and publication boundary;
- signed release metadata, checksums, provenance, authenticity, or downgrade/substitution concerns;
- workload identity, entitlement, authorization, replay, or private-engine delivery boundaries;
- runner-local handling of protected configuration, temporary plaintext, generated artifacts, and cleanup;
- provider adapters or verification flows that could weaken the documented trust model;
- accidental publication of private implementation material, credentials, keys, or security-sensitive evidence;
- security guidance or public claims that could materially mislead users about the protection Envuscator provides.

Reports about private implementation repositories are accepted through this path and may be routed internally to the owning repository.

## Security model boundary

Envuscator is defense in depth. It is not encryption, secret storage, runtime authorization, or a guarantee that data shipped in a client application cannot be recovered by a sufficiently capable attacker.

A report is still security-relevant when it demonstrates a bypass, substitution, trust-boundary failure, authorization defect, sensitive-data exposure, or misleading security guarantee within the documented architecture. Demonstrating that arbitrary client-side values can eventually be observed at runtime, by itself, is not a vulnerability in the stated model.

## Disclosure

Please allow a reasonable opportunity to investigate, coordinate remediation, and notify affected downstream users before public disclosure. No fixed acknowledgment or remediation SLA is promised while Envuscator remains incubating.

Where appropriate, maintainers will coordinate affected-version information, mitigations, disclosure timing, and credit with the reporter.
