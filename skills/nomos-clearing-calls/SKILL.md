---
name: nomos-clearing-calls
description: Use when the user asks Hermes to resolve Nomos hackathon clearing-call cases by reading structured case data, configuring or instructing the Vapi voice agent, placing/simulating the German clearing call, extracting the real diagnosis and next action, and writing the result back through Nomos MCP tools.
version: 1.1.0
author: Bruno + Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [nomos, vapi, mcp, voice-agent, clearing-calls, energy-market, case-resolution]
    related_skills: [voice-agent-orchestration, voice-agent-platforms, native-mcp]
---

# Nomos Clearing Calls

## Overview

This skill is for the Nomos voice-agent challenge workflow. It is **not only a MaLo correction skill**. A future Hermes agent should use it whenever Bruno asks to clear, resolve, call about, simulate, or update a stuck Nomos signup case.

Hermes is the workflow orchestrator: it reads case context, chooses the scenario objective, prepares the Vapi assistant/call, validates the returned transcript or structured report, and writes the outcome back through Nomos MCP tools when they exist.

Vapi is the real-time German voice agent: it handles spoken conversation, interruption behavior, DTMF/keypad handling, and the actual call/simulation session.

Default challenge shape: a structured case file describes a stuck electricity signup. The voice agent calls a German market participant, explains the case, gets the real reason and next step, and Hermes stores a clean back-office result. The win is **case movement**, not just a corrected MaLo or a pleasant transcript.

## When to Use

Use this skill when the user asks things like:

- "resolve CASE-A"
- "call about CASE-B"
- "get the correct MaLo for CASE-C"
- "clear this Nomos case"
- "have the Vapi agent call the grid operator / supplier / back office"
- "run the Nomos clearing-call simulation"
- "write the call outcome back into Nomos"
- "trigger the next action after the call"
- "make the skill cover all challenge scenarios, not just MaLo"

Do **not** use this for generic Vapi architecture advice unless the user is specifically working on Nomos clearing calls. For broad voice-platform design, load/use `voice-agent-orchestration` or `voice-agent-platforms` instead.

## Source-of-Truth Hierarchy

When executing this workflow, prefer sources in this order:

1. **Live Nomos MCP tools** in the active Hermes session.
   - Tool names may be prefixed like `mcp_nomos_*`, `mcp_fake_system_*`, or the server name Bruno configured.
   - Current fake-system tools may be customer-oriented (`list_customers`, `get_customer`, `update_customer`) until case-specific tools are added.
2. **Explicit case context provided by Bruno** in the current conversation.
3. **Challenge fixtures and docs** from `https://github.com/nomos-energy/voice-agent` when needed for scenario semantics.
   - `README.md` defines the challenge and the three signup stages.
   - `fixtures.json` defines practice cases CASE-A, CASE-B, CASE-C.
   - `CHEATSHEET.md` defines German terms and non-negotiable rules.
   - `recordings/*.md` shows good/messy clearing-call transcripts.
4. **This skill's references**:
   - `references/nomos-challenge-scenarios.md`
   - `references/nomos-mcp-expectations.md`
5. **Never invent missing case facts, phone numbers, call results, reference numbers, corrected identifiers, or backend updates.**

## Scenario Taxonomy: Classify Before Calling

Before preparing the Vapi prompt, classify the case. Do not assume every case wants a corrected MaLo.

| Scenario | Typical symptom | Call objective | A cleared result looks like | Likely next action |
| --- | --- | --- | --- | --- |
| **MaLo-Ident / market-location identification** | Automated identification found no/equivocal/wrong MaLo; address ambiguous; meter number disambiguates. | Get the correct market-location number or learn why none exists. | Correct MaLo read back digit-by-digit, or a documented reason no MaLo exists. | Store corrected MaLo and trigger/resubmit registration; or contact customer / wait for operator if unresolved. |
| **Netzanmeldung bounced** | Registration rejected, e.g. `Marktlokation nimmt nicht teil`. | Find the real reason behind the rejection and the actionable next step. | Diagnosis such as removed temporary meter / dead MaLo / new Anlage required; not necessarily a ticket number. | Contact customer, create new installation flow, resubmit only if appropriate. |
| **Silent/stuck registration** | APERAK or receipt received, but no confirmation and deadline passed. | Confirm receipt, processing state, whether resubmission is needed, and tracking reference. | Operator confirms it is in process, gives Vorgangsnummer, confirms no resubmission. | Wait/track with reference; maybe follow up by email/date. |
| **Kündigung / previous supplier cancellation** | Old supplier did not answer or rejected cancellation. | Learn whether the old supplier received/processed the cancellation and who must act. | Reason for stall, whether Nomos/customer/old supplier must do anything, reference if available. | Reminder to old supplier, customer cancellation request, email-agent handoff, or retry process. |
| **Another process already in progress** | Registration rejected because another supplier/process is already active. | Find which process blocks Nomos and what must happen before Nomos can continue. | Clear blocker and owner; not a fake registration success. | Wait, contact customer, coordinate with previous supplier, or schedule retry. |
| **Inconclusive / escalated clearing case** | Clerk cannot resolve immediately, puts caller on hold, escalates internally, promises callback. | Capture reference, owning department, promised next update, and exact unresolved question. | Vorgangsnummer + promised follow-up window + current facts. | Log and wait/follow-up; do not bluff a resolved MaLo/status. |

For the current public fixtures:

- `CASE-A` = Netzanmeldung bounced: `Marktlokation nimmt nicht teil`; expected win is real reason and next step, e.g. meter was a Baustromzähler and the connection needs a new Anlage.
- `CASE-B` = silent/stuck registration: APERAK/receipt but no confirmation; expected win is confirmation in process, Vorgangsnummer, and no resubmission.
- `CASE-C` = MaLo-Ident / wrong market-location: building has several delivery points; expected win is corrected MaLo read back digit-by-digit and registration with that identifier.

## Operational Workflow

### 1. Discover available tools and case data

1. Look for Nomos MCP tools in the active tool list.
2. If a case key is given, retrieve that case through MCP if possible.
3. If tools are only customer-oriented, search/list customers and inspect `notes`/`status`/fields for the case key or structured case JSON.
4. If no MCP tools are available, state that the Nomos MCP server/config is not connected. Continue only if Bruno explicitly provided enough synthetic case context and a safe challenge/test call target.
5. If a case lookup fails, stop and report the failure; do not fabricate a fixture.
6. Verify the case has enough information to call/simulate:
   - case id/key
   - process step (`malo_ident`, `kuendigung`, `netzanmeldung`, or unknown)
   - symptom/status text
   - relevant identifiers: MaLo if present, meter number if present, reference numbers if present
   - address/delivery location
   - date sent/requested supply start when relevant
   - call target: grid operator, metering operator, previous supplier, market back office, or provided clerk-agent/simulation endpoint
   - target phone/simulation route if a real call or platform call is requested

### 2. Classify the case and define the exact call goal

Use the taxonomy above. The Vapi agent's objective must be scenario-specific.

Examples:

- For a bounced registration, ask for the true rejection reason and next step; do not over-focus on obtaining a new MaLo unless the clerk says the MaLo is wrong.
- For a silent registration, ask whether the registration was received/processed, whether resubmission is needed, and get a Vorgangsnummer.
- For MaLo-Ident, use the address and meter number to obtain/confirm the correct MaLo, then read it back digit-by-digit.
- For Kündigung, target the old supplier/cancellation context and capture whether Nomos, the customer, or the previous supplier owns the next action.
- For an inconclusive escalation, capture the reference number, owner, promised update timing, and the exact unresolved question.

### 3. Build the Vapi assistant prompt

Use the bundled base prompt:

```text
templates/vapi-clearing-call-assistant-prompt.md
```

Append a `# Case context for this call` section. Include only real facts from MCP/user/fixtures. Unknown fields should be omitted or explicitly marked `unknown`.

Recommended appended context shape:

```markdown
# Case context for this call
Case key: CASE-B
Scenario type: silent_registration
Supplier: Nomos GmbH
Call target: Rheinland Netz AG / market communication back office
Safe test target: <provided challenge clerk/simulation target or phone number>
Process step: Netzanmeldung
Symptom/status: APERAK received but no confirmation; deadline passed.
Known MaLo-ID: 48820037615
Meter number: 1EMH9000020002
Delivery address: Musterstraße 211, Köln-Ehrenfeld
Registration sent: 02.06.2026
Requested supply start: 01.08.2026
Previous communication: Email follow-up sent, no reply.

Information to obtain:
- whether the registration was received and is valid
- why processing stalled
- whether Nomos must resubmit
- Vorgangsnummer/reference number, if one exists
- next action owner and expected timing

Do not tell the clerk the expected answer. Ask naturally and verify.
```

For scenario/evaluation harnesses, keep expected answers/oracles out of the Vapi assistant prompt. The prompt may include case facts and goals, but not hidden expected outputs such as the corrected MaLo for CASE-C or the expected CASE-A diagnosis.

### 4. Choose call/simulation path

Use the Vapi integration available in the current environment. In Bruno's Vapi/Hermes setup, useful entrypoints may include:

- `hermes-vapi-iterate` for Vapi Simulations prompt iteration.
  - `hermes-vapi-iterate run-all --dry-run` previews scenarios without calling Vapi.
  - `hermes-vapi-iterate run-all --limit 1` smoke-tests the suite runner.
  - `hermes-vapi-iterate run-all` runs all scenario JSON files through Vapi simulation and does **not** place PSTN calls.
- `hermes-vapi-smoke` for no-call auth/chat/phone-number checks.
- `hermes-vapi-phone` for profile-scoped telephony/real-call workflows.
- `~/.local/bin/vapi` or the Vapi REST API for direct assistant updates if needed.

For a real external phone call, ensure the user has explicitly asked for that call and that the target is safe/authorized. Challenge rules say to use synthetic fixture data and provided clerk-agent/test targets only; never dial real customer/grid-operator numbers unless Bruno explicitly confirms a non-hackathon real-call context and compliance constraints.

### 5. Place or run the call, then retrieve real output

1. Update/create the Vapi assistant with the base prompt plus appended case context.
2. Ensure Vapi has the required tools (at minimum DTMF/keypad and end-call behavior when supported).
3. Start the simulation or call.
4. Retrieve the real transcript, structured report, call ID, run ID, status, and any tool-call logs.
5. If the call failed, timed out, reached voicemail, got stuck in an IVR, or did not produce an answer, report that honestly and do not update the case as if it succeeded.

### 6. Interpret the call result by scenario

Extract only facts supported by the call transcript/report.

Always extract:

- call/simulation status and ID
- scenario type
- real diagnosis/reason
- next action owner
- next action verb
- confidence and supporting quote/summary
- reference/Vorgangsnummer if provided
- whether a follow-up date/window was promised
- whether a resubmission/retry is needed

Extract scenario-specific fields:

- MaLo-Ident: corrected MaLo-ID if provided; whether read back/confirmed digit-by-digit.
- Bounced registration: rejection reason, whether old MaLo is dead/valid, whether new Anlage/customer action is required.
- Silent registration: whether registration was received/valid/in processing, whether no resubmission is needed, reference number.
- Kündigung: old supplier status, whether customer must cancel, cancellation reference, retry/reminder owner.
- Inconclusive escalation: escalated department, unresolved question, promised callback/update timing, reference.

If a long identifier is obtained, verify that the transcript shows the agent read it back or confirmed it in chunks/digit-by-digit. If not, mark confidence lower and avoid irreversible updates without confirmation.

### 7. Update Nomos through MCP

When MCP update tools are available:

1. Write a short back-office note in plain language.
2. Store structured fields supported by the tool/schema.
3. Trigger the scenario-specific next action only if the tool exists and the call result supports it.
4. Read the case back through MCP after updating if possible.
5. Report the update result and any verification readback.

Suggested next-action mapping:

| Scenario result | Update/action |
| --- | --- |
| Corrected MaLo confirmed | Store corrected MaLo; trigger/resubmit registration. |
| Current MaLo dead due to removed/construction meter | Mark case as customer follow-up/new Anlage needed; trigger email agent/customer contact. |
| Registration received and pending | Store reference; mark waiting/in processing; schedule follow-up if promised. |
| No resubmission required | Do not resend; note operator confirmation. |
| Resubmission required | Mark for Nomos resubmission with reason. |
| Old supplier cancellation blocker | Assign action to previous supplier/customer/Nomos as stated; trigger customer email if needed. |
| Escalated/inconclusive | Store reference and promised update window; mark waiting for operator; schedule follow-up. |

If update tools are not available, provide a structured pending update payload. Do not claim Nomos was updated.

### 8. Final response format

Use this structure for user-facing completion:

```markdown
## Nomos clearing-call result: <CASE-ID>

- Scenario: <malo_ident | bounced_registration | silent_registration | kuendigung | competing_registration | escalation | unknown>
- Call/simulation status: <completed/failed/etc.>
- Vapi call/run ID: <id if available>
- Diagnosis: <short factual summary>
- Corrected MaLo-ID: <value or not applicable/unknown>
- Reference/Vorgangsnummer: <value or none provided>
- Resubmission needed: <yes/no/unknown/not applicable>
- Next action owner: <Nomos/customer/grid operator/previous supplier/email agent/unknown>
- Next action: <specific action>
- Nomos update: <succeeded/failed/not available>

Back-office note:
<plain-language note suitable for the Nomos case record>

Evidence:
<brief transcript-supported quote/summary>
```

## Guardrails

- Do not reduce every task to "correct MaLo". Identify the scenario first.
- Do not invent case data, call targets, call outcomes, reference numbers, corrected IDs, dates, or next steps.
- Do not claim a backend/Nomos update unless a real MCP tool reports success.
- Do not place a call if the case lookup failed and the user has not provided enough synthetic case context manually.
- Do not place a real external call if the target phone number is absent, ambiguous, unauthorized, or outside the challenge/test constraints.
- Do not use real customer data for challenge runs. The public fixtures are synthetic.
- Do not ask the clerk for passwords or security credentials; clearing calls do not require them.
- Do not use DTMF/keypad in response to a human saying a department name. DTMF is only for recorded automated menus that explicitly ask for keypad input.
- The Vapi agent must disclose AI status as its first words to a human, not to an IVR.
- A reference number is useful but not always the win. The real reason and next step matter most.
- Do not turn the workflow into Hermes-as-Vapi-Custom-LLM unless Bruno explicitly asks; default to Vapi handling real-time voice and Hermes orchestrating workflow/post-call actions.

## Common Pitfalls

1. **MaLo tunnel vision.** CASE-A is not solved by merely asking for a corrected MaLo; it may be solved by discovering the old meter/MaLo is dead and the customer/new Anlage path is required.
2. **Treating a ticket number as success.** A Vorgangsnummer without diagnosis/next step is incomplete.
3. **Leaking expected answers into prompts.** In simulations, expected values belong in evaluator/oracle files, not the Vapi assistant prompt.
4. **Skipping digit readback.** Long identifiers must be confirmed digit-by-digit or in chunks before storing.
5. **Ignoring inconclusive outcomes.** Real calls may end with an internal escalation and promised callback. Log and follow up; do not fabricate resolution.
6. **Updating unsupported fields.** If the MCP tool only supports generic `notes`/`status`, write a note/status only; do not pretend case-specific fields were stored.
7. **Dialing real parties during challenge work.** Use provided synthetic/test targets unless Bruno explicitly moves to real-call testing.

## Verification Checklist

- [ ] Case context came from MCP, explicit user input, or challenge fixture docs.
- [ ] Scenario was classified before calling.
- [ ] Vapi prompt used `templates/vapi-clearing-call-assistant-prompt.md` plus appended case context.
- [ ] Expected answers/oracles were not included in the Vapi assistant prompt.
- [ ] Call/simulation was actually run, or the blocker was reported honestly.
- [ ] Transcript/structured output was inspected before extracting facts.
- [ ] Long identifiers were read back/confirmed before being treated as high-confidence.
- [ ] Nomos update was performed through MCP, or the lack of MCP update capability was reported with a pending payload.
- [ ] Final response includes call/run ID, diagnosis, next action, update status, and evidence.
