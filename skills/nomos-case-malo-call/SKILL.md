---
name: nomos-case-malo-call
description: Use when the user asks Hermes to resolve a Nomos case's correct MaLo identifier, especially CASE-A, by reading case data from the Nomos MCP tools, placing a Vapi clearing call, and writing the outcome back to Nomos.
version: 1.0.0
author: Bruno + Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [nomos, vapi, malo, mcp, voice-agent, case-resolution]
    related_skills: [voice-agent-platforms, native-mcp]
---

# Nomos Case MaLo Call

## Intent

This skill is narrow on purpose. It tells Hermes what to do for the Nomos hackathon workflow where the user asks for the correct MaLo for a case, especially:

> get the correct case MaLo for CASE-A

Default interpretation of that request:

1. Get the case details from the Nomos system through MCP tools.
2. Set up a Vapi call using the assistant prompt in `templates/vapi-case-malo-assistant-prompt.md`.
3. Append the specific case context for the run to that prompt before placing the call.
4. Place the call to the correct grid-operator / market back-office number from the case data.
5. Extract the corrected MaLo-ID, diagnosis, reference number, and next action from the call result.
6. Update the Nomos case through MCP tools.
7. Report exactly what happened, including call ID/status and whether the Nomos update succeeded.

Hermes is the workflow orchestrator. Vapi is the real-time voice agent. Do not redesign this as Hermes being the Vapi Custom LLM unless Bruno explicitly asks for that architecture.

## Trigger Phrases

Use this skill when the user says things like:

- "get the correct case MaLo for CASE-A"
- "call about CASE-A and fix the MaLo"
- "resolve the MaLo for this Nomos case"
- "have the Vapi agent call the network operator for CASE-A"
- "update the case with the corrected MaLo after the call"

If the user names another case key, use the same workflow for that case.

## Required Source of Truth

### Case data

The Nomos MCP tools are the source of truth for case details once they are configured. Expected details include:

- case key, e.g. `CASE-A`
- customer name if relevant
- address / metering location context
- current MaLo-ID if any
- meter number if relevant
- process step / rejection / current status
- requested supply start date
- grid operator / market partner / back-office phone number
- any previous communication or reference numbers

MCP setup is not guaranteed to exist yet. See `references/nomos-mcp-expectations.md`.

### Vapi assistant prompt

Use `templates/vapi-case-malo-assistant-prompt.md` as the base assistant prompt. That file is copied from the existing `vapi-iteration/assistant_prompt.md` prompt and is the canonical voice-agent behavior for this workflow.

Append a `# Case context for this call` section containing the MCP case details for the specific run. Do not replace the base prompt with generic call instructions.

## Procedure

### 1. Resolve the case

When the user asks for a case by key, e.g. `CASE-A`:

1. Look for Nomos MCP tools in the active tool list. Tool names may be prefixed like `mcp_nomos_*`, `mcp_fake_system_*`, or whatever server name Bruno configured.
2. Use the available MCP case lookup/search tool to retrieve the case.
3. If no MCP tools are available, explain that the Nomos MCP server/config is not connected yet. Do not fake case data.
4. If the case cannot be found, stop and report that the case lookup failed.
5. If the case is found but lacks a phone number or enough details to identify the operator/back-office, ask Bruno for only the missing detail.

### 2. Build the Vapi prompt

Read or use the bundled template at:

```text
templates/vapi-case-malo-assistant-prompt.md
```

Then append the live case context, for example:

```markdown
# Case context for this call
Case key: CASE-A
Goal: Find and confirm the correct MaLo-ID / MaLo identifier.
Current known MaLo-ID: <value or "unknown">
Meter number: <value if present>
Address: <value if present>
Grid operator / back office: <value if present>
Phone number: <value>
Process step: <value>
Current rejection/status: <value>
Requested supply start: <value if present>
Previous reference numbers: <value if present>

Information to obtain:
- corrected MaLo-ID, if the current one is wrong or missing
- exact diagnosis/reason the case is stuck
- Vorgangsnummer/reference number, if one exists
- whether Nomos must resubmit
- next action owner
```

Never append invented placeholders as if they were facts. Unknown fields should be explicitly marked `unknown` or omitted.

### 3. Set up and place the Vapi call

Use the Vapi integration available in the current environment. In Bruno's Vapi/Hermes hackathon environment, useful entrypoints may include:

- `hermes-vapi-phone` for profile-scoped telephony workflows
- `hermes-vapi-smoke` for auth/chat checks that do not place calls
- `hermes-vapi-iterate` for Vapi Simulations prompt iteration
- the authenticated `vapi` CLI at `~/.local/bin/vapi`
- the Vapi REST API using the locally configured Vapi API key

For an explicit request like "get the correct case MaLo for CASE-A", placing the call is part of the requested workflow once case details and phone number are available. Do not ask a second broad confirmation just to proceed, but do stop if the target phone number is missing or ambiguous.

When creating/updating the Vapi assistant for the call:

- use the exact base prompt from `templates/vapi-case-malo-assistant-prompt.md`
- append the case context
- keep the Vapi agent as the real-time voice caller
- ensure the agent can use DTMF only for automated menus as specified in the prompt
- make sure the call result/transcript/summary can be retrieved after the call

### 4. Interpret the call result

After the call, inspect the real call output/transcript/structured summary. Extract only facts supported by the call result:

- corrected MaLo-ID / MaLo identifier
- whether the current MaLo was wrong, missing, or already correct
- diagnosis / why the case was stuck
- Vorgangsnummer/reference number, if provided
- resubmission requirement
- next action owner
- any follow-up channel, e.g. email required

If the call failed, timed out, reached voicemail, or did not produce an answer, report that directly and do not update the case as if it succeeded.

### 5. Update Nomos through MCP

Once the call produces an outcome and Nomos MCP update tools are available:

1. Update the case with the corrected MaLo-ID if one was confirmed.
2. Add a back-office note summarizing call outcome, diagnosis, reference number, resubmission flag, and next action owner.
3. Update case status only if the call result supports the change.
4. Read back the case through MCP after updating, if a read tool is available, to verify the stored values.

If the MCP update tool is not available yet, report the call outcome and provide the exact note/update payload Bruno should apply later. Do not claim that Nomos was updated.

## Output Format

When finished, respond with:

```markdown
## CASE-A MaLo call result

- Call status: <completed/failed/etc.>
- Vapi call ID: <id if available>
- Corrected MaLo-ID: <value or unknown/not obtained>
- Diagnosis: <short factual summary>
- Reference/Vorgangsnummer: <value or none provided>
- Resubmission needed: <yes/no/unknown>
- Next action owner: <Nomos/customer/grid operator/previous supplier/email follow-up/unknown>
- Nomos update: <succeeded/failed/not available>

Notes:
<short note suitable for the Nomos case record>
```

## Guardrails

- Do not invent case data, phone numbers, call results, reference numbers, or corrected MaLo-IDs.
- Do not claim a backend/Nomos update unless a real MCP tool reports success.
- Do not place a call if the case lookup failed and the user has not provided enough case context manually.
- Do not place a call if the target phone number is absent or ambiguous.
- Do not ask for passwords or security information during these calls.
- Do not use DTMF in response to a human saying a department name; DTMF is only for recorded automated menus.
- Do not turn the workflow into a general Vapi architecture discussion unless Bruno asks.

## Verification Checklist

- [ ] Case data came from Nomos MCP tools or explicit user-provided context.
- [ ] Vapi prompt used `templates/vapi-case-malo-assistant-prompt.md` plus appended case context.
- [ ] Call was actually placed or the blocker was reported honestly.
- [ ] Call output/transcript was inspected before extracting a corrected MaLo-ID.
- [ ] Nomos case update was performed through MCP, or the lack of MCP update capability was reported.
- [ ] Final response includes call ID/status and update status.
