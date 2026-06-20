# Nomos MCP Expectations

This project is expected to expose Nomos case data to Hermes through an MCP server.

Current repo notes:

- `packages/fake-system` already ships a FastAPI dashboard and an MCP server.
- The README currently documents the streamable HTTP MCP endpoint as `http://localhost:8765/mcp`.
- Existing fake-system tools may be customer-oriented until the case workflow is expanded.

Expected future case workflow tools may include equivalents of:

- list/search cases by case key, e.g. `CASE-A`
- get full case details for one case
- update case notes/status
- store corrected MaLo-ID / MaLo identifier
- store call outcome, diagnosis, next action owner, and resubmission flag

Hermes behavior while the MCP surface is incomplete:

- Do not invent unavailable tools.
- If MCP tools are not available in the active session, say that the Nomos MCP server/config still needs to be added before Hermes can read or update case details.
- If the user has explicitly provided enough case context and a phone number, Hermes may still set up/place the Vapi call, but must not claim the Nomos system was updated.
- Once MCP tools exist, prefer them over scraping files or the dashboard for case reads/updates.
