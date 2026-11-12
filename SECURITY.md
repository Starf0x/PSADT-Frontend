# Security Policy

## Reporting a vulnerability

Please **do not** open a public issue for security problems. Use GitHub's
[private vulnerability reporting](../../security/advisories/new) instead.
We aim to respond within 7 days.

## Design notes

- Sessions are server-side; the browser only holds an `HttpOnly`, `Secure`, `SameSite=Strict` cookie. Only a SHA-256 hash of the token is stored.
- All state-changing requests require an `X-CSRF-Token` header that matches the session.
- Passwords are hashed with argon2; accounts lock after repeated failed logins.
- Generated PowerShell is built from a whitelist of step types. User input is emitted as single-quoted literals; file names are validated. The server **never executes** generated scripts; PowerShell is only used to *parse* them for syntax errors.
- The official PSADT template is downloaded at build time and verified against a pinned SHA-256.
- Run behind a TLS-terminating reverse proxy (Caddy, Traefik, nginx) when exposed to a network.
