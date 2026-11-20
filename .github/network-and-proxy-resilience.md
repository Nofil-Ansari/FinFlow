# Network & Proxy Resilience (HTTP 502 / Upstream Errors)

## Context
When interacting with external APIs, cloud CLI hooks, or remote model gateways, transient network or proxy failures (e.g. `HTTP 502 Bad Gateway`, `Upstream proxy error`, `context deadline exceeded` in MCP telemetry hooks) may occur.

## Behavioral Guidelines
1. **Recognize Transient Infrastructure Failures**:
   - HTTP 502 / 504 status codes are symptoms whose underlying cause may be an intermediary proxy/gateway or an upstream application failure, not conclusive proof of a transient proxy issue alone.
   - Do not immediately attempt to modify working local application code for transient gateway drops, but require investigating persistent or reproducible 502/504 failures to verify whether upstream application errors are the root cause.

2. **State Preservation**:
   - Ensure current plan, progress, and file state in `.gsd/STATE.md` remain accurate and are not discarded.

3. **Actionable User Communication**:
   - Clearly state that the failure was a transient upstream proxy/network drop.
   - Check whether the operation already completed, or use an idempotency key when available, before retrying.
   - Inform the user that a retry after a short pause or switching model tier (e.g. Flash to Pro/Low to Medium) typically resolves transient issues.
   - Provide direct local execution paths (e.g., local bat files, terminal commands) if remote tool execution or MCP hooks are blocked.

