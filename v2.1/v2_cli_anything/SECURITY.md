# Security Policy (Open Slap!)

Open Slap! is a local-first application. Treat any connectors, skills, or tool execution capabilities as privileged, and avoid exposing the app to untrusted networks.

## Supported Versions

Security fixes apply to:

- The latest published release, and
- The `main` branch

## Threat Model (High Level)

- **Prompt injection risk:** untrusted inputs can manipulate the agent into unsafe actions if powerful tools are available.
- **Supply chain risk:** third-party dependencies, skills, and plugins can introduce malicious behavior.
- **Exposure risk:** binding HTTP services to `0.0.0.0` or opening ports can enable remote abuse.
- **Secret leakage:** committing `.env` files, API keys, or tokens leads to account compromise.

## Hardening Checklist (Open Slap!)

- Run locally (loopback) whenever possible; avoid exposing ports publicly.
- Keep secrets out of the repository; use environment variables and local secret stores.
- Treat skills/plugins as code execution: only install from trusted sources and review changes.
- Limit filesystem and network permissions to what your workflow requires.
- Enable memory redaction for persisted content:
  - `SLAP_MEMORY_REDACTION_ENABLED=true` (default) redacts common secrets (tokens/keys) before persistence.

## Reporting Security Issues

If you discover a vulnerability:

- Do not open a public issue with exploit details.
- Prefer GitHub’s private vulnerability reporting for this repository (Security Advisories), when available.
- If private reporting is not enabled, open a minimal issue requesting a private disclosure channel.
