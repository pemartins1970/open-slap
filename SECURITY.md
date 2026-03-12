# Security Information (Open Slap!)

Open Slap! is an agentic engine intended to run locally. When it is connected to an execution plane (e.g., Slap! GO), treat that execution plane as privileged and isolate it.

## Threat Model (High Level)

- **Local agent gateway risk:** prompt injection can trigger unsafe actions if the execution plane has OS/network/filesystem access.
- **Supply chain risk:** importing external “skills” or plugins can introduce malicious behavior.
- **Exposure risk:** running a local agent on `0.0.0.0` without authentication can lead to remote abuse.
- **Secret leakage:** committing `.env` / API keys to public repos leads to account compromise.

## Recommended Architecture (Family-wide Pattern)

- **Control Plane (Open Slap UI/Engine):** orchestration, configuration, memory/metadata, UX.
- **Execution Plane (e.g., Slap! GO):** tool execution only, behind authentication, running inside a sandbox/controlled environment.
- **All external clients connect to Control Plane** (or an API gateway) and are routed to the Execution Plane inside the sandbox.

## Execution Plane Hardening (Slap! GO)

Slap! GO supports a defensive layer with authentication and an IP defender:

- **Authentication:** set `SLAPGO_API_KEY` to require `X-API-Key` (or `Authorization: Bearer`) for all `/api/*` endpoints (except `/api/status`).
- **Local-only mode:** set `SLAPGO_LOCAL_ONLY=true` to only accept `127.0.0.1` / `::1`.
- **IP defender (ban):**
  - Enabled by default. Disable with `SLAPGO_DEFENDER_ENABLED=false`.
  - Threshold and window:
    - `SLAPGO_MAX_UNAUTHORIZED` (default 10)
    - `SLAPGO_UNAUTHORIZED_WINDOW_MS` (default 300000)
    - `SLAPGO_BAN_MINUTES` (default 60)
  - When the threshold is exceeded, the IP is banned and a security event is recorded.

### Visibility for Users (Alerts + Logs)

- **Security logs:** `GET /api/security/logs` returns the latest events, including:
  - `unauthorized` (first unauthorized attempt in a window)
  - `ip_banned` (ban event)
  - Events include IP and are stored with a DB timestamp.
- **Active bans:** `GET /api/security/bans` returns current banned IPs and ban expiry (`until`).
- The UI should surface these events to users as visible alerts (e.g., a “Security” panel/badge).

## Sandbox Guidance

To reduce impact of a successful prompt injection:

- Run the execution plane in an isolated environment (recommended): **WSL2/Docker/VM** or a dedicated low-privilege OS user.
- Restrict filesystem access to a dedicated workspace directory.
- Restrict outbound network access unless explicitly required.
- Do not expose agent ports publicly. Prefer localhost + reverse proxy with auth if remote access is required.

## Secret Management

- Never commit API keys, tokens, or JWT secrets.
- Keep local secrets in `.env` and ensure it is ignored by Git (use `.gitignore`).

## Reporting Security Issues

If you discover a vulnerability, do not open a public issue with exploit details. Prefer a private disclosure channel in the project’s distribution repository.
