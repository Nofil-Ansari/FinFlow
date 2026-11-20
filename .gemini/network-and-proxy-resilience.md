# Network & Proxy Resilience (HTTP 502 / Upstream Errors)

## Context
When interacting with external APIs, cloud CLI hooks, or remote model gateways, transient network or proxy failures (e.g. `HTTP 502 Bad Gateway`, `Upstream proxy error`, `context deadline exceeded` in MCP telemetry hooks) may occur.

## Behavioral Guidelines
1. **Recognize Transient Infrastructure Failures**:
   - HTTP 502 / 504 errors originate from intermediate proxies/gateways, not code bugs or user errors.
   - Do not attempt to fix working local application code in response to a 502 gateway error.

2. **State Preservation**:
   - Ensure current plan, progress, and file state in `.gsd/STATE.md` remain accurate and are not discarded.

3. **Actionable User Communication**:
   - Clearly state that the failure was a transient upstream proxy/network drop.
   - Inform the user that a retry after a short pause or switching model tier (e.g. Flash to Pro/Low to Medium) typically resolves the issue.
   - Provide direct local execution paths (e.g., local bat files, terminal commands) if remote tool execution or MCP hooks are blocked.

