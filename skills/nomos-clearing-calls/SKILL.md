---
name: nomos-clearing-calls
description: Use when the user mentions Nomos case numbers, MaLo IDs, meter numbers, electricity grid-operator/supplier signup issues, asks what to do with a Nomos case, or requests a Nomos clearing call. Defines case context, SSML-only English call conduct, MCP update rules, and the standard Vapi call/simulation procedure.
version: 1.4.1
author: Bruno + Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [nomos, malo, case-management, energy-market, mcp, vapi, english]
    related_skills: [voice-agent-orchestration, voice-agent-platforms, native-mcp, telephony]
---

# Nomos Clearing Calls

## Purpose

Use this skill to understand references to Nomos cases, MaLo numbers, meter numbers, suppliers, grid operators, electricity market-communication terms, or stuck electricity signup cases, and to run the standard Nomos clearing-call workflow when the user authorizes a call or simulation.

This skill is deliberately broader than “correct the MaLo”. A Nomos clearing case may involve MaLo-Ident, a bounced Netzanmeldung, a silent registration after APERAK, a Kündigung/old-supplier blocker, another registration already in progress, or an inconclusive operator escalation. The job is to identify the case type, get the real diagnosis and next action, and update Nomos with only confirmed facts.

Hermes is the workflow orchestrator: read case context, classify the scenario, prepare the prompt/call, inspect the returned transcript or structured report, and update Nomos through MCP tools. Vapi/telephony is the real-time voice layer: spoken English conversation, interruptions, DTMF/keypad, and call lifecycle.

For phone calls, use the Nomos-specific Vapi/`telephony.py ai-call` procedure documented below together with the `telephony` skill. Do not bypass the helper with ad-hoc Vapi API calls unless the helper is broken or stale.

## When to Use

Load this skill when the user says things like:

- `case NM26-L811`
- `case number CASE-A`
- `wrong MaLo number`
- `confirm the MaLo`
- `meter number`
- `grid operator`
- `supplier switch`
- `registration is stuck/rejected/silent`
- `Kündigung`, `Netzanmeldung`, `MaLo-Ident`, `Lieferantenwechsel`, `Vorgangsnummer`, or `APERAK`
- `update the Nomos case`
- `run a Nomos clearing call`
- `have the Vapi agent call the operator/back office`

For generic Vapi/provider setup, raw Vapi API schemas, simulations unrelated to Nomos, or provider status quirks, use `voice-agent-orchestration`, `voice-agent-platforms`, and/or `telephony`. For live Nomos case data, use MCP tools.

## Domain Shorthand

| Term the user may use | Meaning |
| --- | --- |
| `case`, `case number`, `case ID` | A Nomos case record, usually retrievable through `mcp_nomos_get_case` or `mcp_nomos_get_case_summary`. |
| `MaLo`, `MaLo-ID`, `Malo`, `market-location ID`, `Marktlokation` | The electricity market-location identifier, usually an 11-digit number. |
| `wrong MaLo` | The stored market-location ID may not match the meter/address/delivery point. Confirm before changing it. |
| `meter number`, `Zählernummer` | The physical/electronic meter identifier. Often disambiguates buildings with multiple delivery points. |
| `grid operator`, `Netzbetreiber`, `VNB` | The network/grid company that may identify or confirm the market location and registration status. |
| `supplier`, `Lieferant` | Usually Nomos GmbH unless the case says otherwise. |
| `Lieferantenwechsel` | Supplier switch. Often the correct IVR/menu category for a Nomos signup issue. |
| `MaLo-Ident` | Market-location identification step before registration. |
| `Netzanmeldung` | Grid registration of Nomos as supplier for the delivery point. |
| `Kündigung` | Cancellation/termination of the old supplier contract, which can block the switch. |
| `APERAK` | Automated receipt/rejection message; an APERAK without confirmation can still mean a stuck case. |
| `Vorgangsnummer` | Ticket/reference number. Useful evidence, but not the whole win. |
| `Baustromzähler`, `Zähler ausgebaut`, `neue Anlage` | Temporary construction meter, meter removed, new installation/connection needed. Often indicates the old MaLo cannot be used. |

## Source of Truth

When a case number is mentioned:

1. Retrieve the case through Nomos MCP if tools are available.
   - Prefer `mcp_nomos_get_case_summary(case_id)` when you need both current case details and latest call log.
   - Use `mcp_nomos_get_case(case_id)` when only the structured case is needed.
   - Use `mcp_nomos_list_cases` only to find/confirm candidate case IDs.
2. Treat explicit details from the user as authoritative if they override or clarify the case record.
3. Use challenge fixtures/docs only for scenario semantics or synthetic test cases, not as a substitute for live MCP data when the user names a live case.
4. Do not invent missing case facts, phone numbers, MaLo IDs, reference numbers, call outcomes, or backend updates.
5. If case lookup fails, say so and ask for the missing context rather than guessing.

## What to Extract From a Case

For any Nomos case, identify these fields if present:

- case ID
- supplier / Lieferant
- grid operator / market participant / back-office target
- current MaLo ID
- meter number / Zählernummer
- delivery address / Lieferstelle
- registration date and requested supply start
- status text / symptom / current rejection
- goal
- latest call result, if any
- current next action

Then classify the scenario before prompting or calling.

## Interpreting Common Case Types

| Situation | What it usually means | What a useful resolution contains | English call focus |
| --- | --- | --- | --- |
| Wrong or uncertain MaLo / MaLo-Ident | Stored market-location ID may not match meter/address, or automated ID failed. | Correct MaLo, or a documented reason no MaLo is available yet, plus next action. | Use address + meter number/Zählernummer; read MaLo digit-by-digit; ask whether to submit with the corrected market location. |
| Registration rejected/bounced / Netzanmeldung | A submitted registration failed, e.g. `Marktlokation nimmt nicht teil`. | Actual rejection reason and whether resubmission, customer action, or grid-operator action is needed. | Ask whether MaLo is invalid/dead, whether the meter was removed, whether a temporary construction meter or new installation is involved, or whether another registration blocks it. |
| Silent/stuck registration | Receipt/APERAK may exist but no confirmation arrived. | Whether it was received, current processing status, reference number if any, and whether resubmission is needed. | Ask if the registration is received and valid, why it stalled, whether Nomos must resend, and expected processing date. |
| Previous-supplier cancellation / Kündigung | Old supplier cancellation may be blocking the switch. | Whether cancellation was received/accepted/rejected and who owns the next step. | Ask whether old supplier, customer, or Nomos must act; capture reference and follow-up channel. |
| Competing registration/process | Another supplier or market process is already active. | Which process blocks Nomos and what must happen before Nomos can continue. | Ask what process is active, who owns it, whether waiting/customer clarification is required, and when retry makes sense. |
| Escalated/inconclusive | The other party cannot resolve immediately. | Reference number, owning department/person, promised follow-up window, and exact unresolved question. | Stay patient through hold music; capture internal support department/owner, reference number, and promised update. |

Do not force every case into “get corrected MaLo.” A corrected MaLo matters only when the case actually concerns market-location identification or a wrong market-location ID.

## If the User Asks for a Call

Nomos outbound calls should use the local `telephony` skill helper with Vapi. Load/use the `telephony` skill for provider setup and safety rules. Do not inspect or grep the helper implementation just to learn how to place the call unless the documented command fails or the skill appears stale.

### Authorization and single-call discipline

One explicit user authorization covers exactly **one** outbound call attempt to **one** target number for **one** case.

- After starting a real call, record the Vapi call ID before doing anything else.
- Poll/fetch status for that same call ID until the provider reports a terminal state such as `ended`, `completed`, `failed`, `busy`, `no-answer`, `voicemail`, `silence-timed-out`, or an explicit provider error.
- Do **not** place a second call just because the status is `queued`, `ringing`, `in-progress`, missing a transcript, missing a summary, ended by customer, or because the provider UI/API lags.
- If the call fails, is missed, is silent, reaches voicemail, is ended by the customer, or produces no usable transcript, stop and ask the user for fresh explicit authorization before retrying.
- Before any retry, state the previous call ID and final status so duplicate-call risk is visible.

### Standard reusable Vapi assistant

Use the installed helper script, normally:

```bash
SCRIPT="/home/bruno/.hermes/profiles/vapihermes/skills/productivity/telephony/scripts/telephony.py"
HERMES_AGENT_DIR="${HERMES_AGENT_DIR:-/home/bruno/projects/hermes-agent}"
NOMOS_SKILL_DIR="${NOMOS_SKILL_DIR:-/home/bruno/projects/nomos-agent/skills/nomos-clearing-calls}"
export VAPI_ENABLE_SSML_PARSING="${VAPI_ENABLE_SSML_PARSING:-true}"
export VAPI_VOICE_SPEED="${VAPI_VOICE_SPEED:-0.85}"
export VAPI_11LABS_MODEL="${VAPI_11LABS_MODEL:-eleven_flash_v2_5}"
export VAPI_11LABS_LANGUAGE="${VAPI_11LABS_LANGUAGE:-en}"
```

If the path changes, locate it with:

```bash
SCRIPT="$(find ~/.hermes/profiles/vapihermes/skills ~/.hermes/skills -path '*/telephony/scripts/telephony.py' -print -quit 2>/dev/null)"
```

Create or update the durable Nomos Vapi assistant before repeated calls, and rerun this command whenever `templates/vapi-clearing-call-assistant-prompt.md` changes:

```bash
(cd "$HERMES_AGENT_DIR" && uv run python "$SCRIPT" vapi-assistant ensure \
  --key nomos-clearing-calls \
  --name "Nomos clearing caller" \
  --prompt-file "$NOMOS_SKILL_DIR/templates/vapi-clearing-call-assistant-prompt.md" \
  --task-variable case_context \
  --max-duration 5)
```

The assistant is stable behavior: English call conduct, SSML-only output, AI disclosure, DTMF rules, identifier pacing, and Nomos clearing-call policy. Do not put live case facts into the reusable assistant prompt. Live case facts belong in the per-call task file passed to `ai-call`.

Preview assistant creation/update without touching Vapi when needed:

```bash
(cd "$HERMES_AGENT_DIR" && uv run python "$SCRIPT" vapi-assistant ensure \
  --key nomos-clearing-calls \
  --name "Nomos clearing caller" \
  --prompt-file "$NOMOS_SKILL_DIR/templates/vapi-clearing-call-assistant-prompt.md" \
  --task-variable case_context \
  --max-duration 5 \
  --dry-run)
```

### Standard call command

Write the per-case context to a file. Use facts from MCP, user-provided synthetic context, or fixture docs only:

```bash
cat > /tmp/nomos-call-task.md <<'EOF'
# Case context for this call

Case ID: <case_id>
Supplier: <supplier>
Grid/operator/target: <grid_operator or call target>
Current MaLo ID: <malo_id if any>
Meter number / Zählernummer: <meter_number if any>
Delivery address / Lieferstelle: <address if any>
Registration date / Anmeldung: <registration_date if any>
Requested supply start / Lieferbeginn: <supply_start if any>
Status/symptom: <status_text/symptom>
Scenario type: <MaLo-Ident | Netzanmeldung | Kündigung | Lieferantenwechsel | Marktkommunikation | other>
Goal: <what must be confirmed or obtained>
Information to obtain: <specific unknowns>
EOF
```

Run the exact call as a dry-run first. This validates the task file and confirms the provider request will reuse the saved `nomos-clearing-calls` assistant:

```bash
(cd "$HERMES_AGENT_DIR" && uv run python "$SCRIPT" ai-call '<E164 phone number>' \
  --provider vapi \
  --assistant-key nomos-clearing-calls \
  --task-file /tmp/nomos-call-task.md \
  --first-sentence '<short English greeting mentioning Nomos and the case ID>' \
  --max-duration 5 \
  --dry-run)
```

Only after explicit user authorization for this one call, run the same command without `--dry-run`:

```bash
(cd "$HERMES_AGENT_DIR" && uv run python "$SCRIPT" ai-call '<E164 phone number>' \
  --provider vapi \
  --assistant-key nomos-clearing-calls \
  --task-file /tmp/nomos-call-task.md \
  --first-sentence '<short English greeting mentioning Nomos and the case ID>' \
  --max-duration 5)
```

The call command returns a Vapi `call_id`. Record it immediately and poll that exact call:

```bash
(cd "$HERMES_AGENT_DIR" && uv run python "$SCRIPT" ai-status '<call_id>' --provider vapi)
```

### Vapi voice settings for identifier pacing

Before a call that will read MaLo IDs, meter numbers, phone numbers, or reference numbers, verify the Vapi voice settings:

```bash
(cd "$HERMES_AGENT_DIR" && uv run python "$SCRIPT" diagnose)
```

For the standard `telephony.py` helper with ElevenLabs (`voice_provider: 11labs`), prefer these settings in `~/.hermes/.env` or the Hermes config:

```env
VAPI_ENABLE_SSML_PARSING=true
VAPI_VOICE_SPEED=0.85
VAPI_11LABS_MODEL=eleven_flash_v2_5
VAPI_11LABS_LANGUAGE=en
```

Do not rely on the LLM prompt alone for number pacing. The prompt must spell or chunk identifiers, and the voice layer must be configured to honor SSML pauses.

For Nomos calls, the assistant must use **SSML-only output**:

- Every spoken assistant response must be exactly one valid `<speak>...</speak>` document.
- No plain text, Markdown, code fences, XML declarations, comments, or explanations outside `<speak>`.
- Use only the tested SSML subset in the reusable template: `<speak>` plus `<break time="300ms" />`, `<break time="400ms" />`, or `<break time="500ms" />`.
- Do not use `<prosody>`, `<say-as>`, `<emphasis>`, `<phoneme>`, `<sub>`, `<spell>`, `<p>`, or `<s>` in this Vapi/ElevenLabs loop.
- Do not rely on raw digits for MaLo IDs, meter numbers, phone numbers, dates, or reference numbers. Write English spoken words and insert short `<break>` tags between groups.

### English first sentence

Use exactly one concise English first sentence path. For Vapi outbound calls, prefer `--first-sentence` as the provider-level `firstMessage`, and ensure the assistant prompt says not to repeat an introduction that has already been spoken. The first sentence should disclose AI status to the first human and identify Nomos/case context. Example:

```text
Hello, I am an artificial intelligence from Nomos GmbH calling about electricity signup case <case_id>. Could you help me clarify it?
```

Do not disclose AI status to an IVR/recorded menu. For IVR, choose DTMF only when the recorded menu explicitly asks for keypad input. Read recorded menu options literally and choose the option label that matches the case; do not default to option 1. MaLo-Ident, wrong-MaLo, corrected-MaLo, and market-communication cases should choose Marktkommunikation when that option is offered.

### IVR and DTMF handling

DTMF/keypad actions are for recorded menus, not for human department words.

- For recorded IVR menus, choose the menu option that matches the case. Do not default to option 1; if Marktkommunikation is option 2 for a MaLo-Ident case, choose option 2.
- In chat/mock evals where no DTMF tool is attached, answer an explicit recorded menu with only the keypad choice, such as `[DTMF:1]`, `<DTMF:1>`, or `1`. Do not wrap keypad choices in SSML.
- Do not press a key just because a human says department words such as Lieferantenwechsel, Netzanmeldung, MaLo-Ident, Kündigung, Marktkommunikation, or Abteilung.
- If the assistant uses a DTMF/keypad or endCall tool, it should call the tool silently. If it speaks afterward, it must output a fresh `<speak>...</speak>` document.

### Per-call task file shape

For a call about a Nomos case, provide the reusable Vapi assistant with concise case context only. Use English back-office wording in case goals and questions, preserving necessary energy-market terms where they are the actual process names, but do not repeat the full stable assistant behavior from `templates/vapi-clearing-call-assistant-prompt.md` in every task file:

```markdown
# Case context for this call

Case ID: <case_id>
Supplier: <supplier>
Grid/operator/target: <grid_operator or call target>
Current MaLo ID: <malo_id if any>
Meter number / Zählernummer: <meter_number if any>
Delivery address / Lieferstelle: <address if any>
Registration date / Anmeldung: <registration_date if any>
Requested supply start / Lieferbeginn: <supply_start if any>
Status/symptom: <status_text/symptom>
Scenario type: <MaLo-Ident | Netzanmeldung | Kündigung | Lieferantenwechsel | Marktkommunikation | other>
Goal: <what must be confirmed or obtained>
Information to obtain: <specific unknowns>

Case-specific questions:
- <question 1>
- <question 2>
- <question 3 if needed>

Important identifier pacing:
- <identifier that must be read back slowly, if any>

Success criteria:
- <what answer/reference/follow-up is enough to resolve or advance this case>
```

Do not include hidden expected answers or invented outcomes in call instructions. For simulations/evals, expected answers belong in evaluator/oracle files, not the target assistant prompt.

## Building a Vapi Assistant or Simulation Prompt

For Vapi Simulations or assistant-prompt iteration, use the bundled base prompt:

```text
templates/vapi-clearing-call-assistant-prompt.md
```

Append a `# Case context for this call` section with only facts from MCP, user-provided synthetic context, or fixture docs. Unknown fields should be omitted or explicitly marked `unknown`.

The base prompt is English-call focused: it requires SSML-only assistant output, English speech inside SSML, AI disclosure to the first human, literal IVR menu selection, DTMF only for recorded menus, slow one-identifier-at-a-time pacing, `<break>` pauses, digit-by-digit readback, scenario-specific goals, and English back-office note intent.

## After the Call or Simulation

Inspect the real call output/transcript/structured summary before extracting facts. Extract only facts supported by the transcript/report:

- call/simulation status and ID
- scenario type
- real diagnosis/reason
- next action owner
- next action verb
- confidence and supporting quote/summary
- reference/Vorgangsnummer if provided
- follow-up date/window if promised
- whether resubmission/retry is needed
- corrected MaLo-ID or other corrected identifier if confirmed

If a long identifier was obtained, verify that the transcript shows readback/confirmation. If not, mark confidence lower and avoid irreversible updates without confirmation.

## Updating Nomos

Use MCP update tools only for facts actually known from the case record, the user, or a completed call/result.

Preferred tools:

1. `mcp_nomos_save_call_result` — record the call outcome/summary/confidence.
2. `mcp_nomos_update_case_details` — update audited case fields such as `malo_id`, `grid_operator`, `address`, `meter_number`, `registration_date`, `supply_start`, `status_text`, `symptom`, or `goal` when a confirmed detail changes. Dates must be `YYYY-MM-DD`; MaLo IDs must contain exactly 11 digits.
3. `mcp_nomos_update_case_status` — update `case_status` and `next_action` after the outcome supports it.
4. `mcp_nomos_get_case_summary` — read back the final visible state.

Rules:

- If a corrected MaLo is confirmed, use `mcp_nomos_update_case_details` with `malo_id=<confirmed 11-digit ID>` and then set a resubmission/registration next action if appropriate.
- If no corrected MaLo was obtained, do **not** overwrite the MaLo field.
- If a call was inconclusive, save the call result as inconclusive and keep the case open with a clear next action.
- If a reference number or promised follow-up was provided, include it in the call result summary and/or next-action text if the MCP schema supports it.
- If the current MaLo is dead due to removed/construction meter, update status/next action toward customer follow-up/new Anlage; do not store a fake replacement MaLo.
- If only generic status/next-action update is appropriate, avoid changing case-detail fields.
- Read the case summary back after updates when possible.

### Suggested next-action mapping

| Scenario result | Update/action |
| --- | --- |
| Corrected MaLo confirmed | Store corrected MaLo; trigger/resubmit registration. |
| Current MaLo dead due to removed/construction meter | Mark customer follow-up/new Anlage needed; no resubmission on old MaLo. |
| Registration received and pending | Store reference; mark waiting/in processing; schedule follow-up if promised. |
| No resubmission required | Do not resend; note operator confirmation. |
| Resubmission required | Mark for Nomos resubmission with reason. |
| Old supplier cancellation blocker | Assign action to previous supplier/customer/Nomos; trigger customer email if needed. |
| Escalated/inconclusive | Store reference and promised update window; mark waiting for operator; schedule follow-up. |

## Reverting Dev/Test Case Changes

If the user asks to reset a Nomos fake-system case for another test run, use MCP first and last for readback. Direct database edits may be appropriate only when the user explicitly asks to revert local/dev database state or says the dev services are running and wants a DB-level reset.

Safe revert pattern:

1. Read the case through `mcp_nomos_get_case_summary`.
2. Inspect only rows for the specific `case_id` in `cases`, `call_logs`, and `audit_logs`.
3. Revert only the rows/fields created by the unwanted action, using exact IDs/predicates.
4. Preserve original case fields unless the user explicitly requests a full reset.
5. Read back through MCP again.

## Final Answer Pattern

When reporting a Nomos case action, keep it short and factual:

```markdown
## Nomos case result: <CASE-ID>

- Status: <resolved/open/inconclusive>
- Scenario: <malo_ident | bounced_registration | silent_registration | kuendigung | competing_registration | escalation | unknown>
- Call/simulation status: <completed/failed/etc.>
- Vapi call/run ID: <id if available>
- MaLo: <confirmed/corrected/unchanged/unknown/not applicable>
- Corrected MaLo: <value or none>
- Diagnosis: <what is known>
- Reference/Vorgangsnummer: <value or none provided>
- Resubmission needed: <yes/no/unknown/not applicable>
- Next action: <who should do what>
- Nomos update: <succeeded/failed/not available>
- Evidence: <brief source: MCP, call transcript, or user-provided context>

Back-office note:
<short English note suitable for the Nomos case record>
```

## Guardrails

- Do not assume every case is a MaLo correction case.
- Do not overwrite a MaLo unless the corrected ID is confirmed.
- Do not invent case data, phone numbers, reference numbers, corrected IDs, diagnoses, dates, or call outcomes.
- Do not claim Nomos was updated unless an MCP update tool succeeded.
- Do not place a call if the case lookup failed and the user has not provided enough synthetic case context manually.
- Do not place a real external call if the target phone number is absent, ambiguous, unauthorized, or outside the challenge/test constraints.
- Do not place more than one outbound real phone call per explicit authorization.
- Do not start a second call as a way to test, recover, cancel, or debug the first call. Work from the original call ID and ask before any retry.
- Do not use DTMF/keypad in response to a human saying a department name. DTMF is only for recorded automated menus that explicitly ask for keypad input.
- Do not ask the clerk for passwords or security credentials; clearing calls do not require them.
- The Vapi agent must disclose AI status as its first words to a human, not to an IVR.
- A reference number is useful but not always the win. The real reason and next step matter most.
- Do not turn the workflow into Hermes-as-Vapi-Custom-LLM unless the user explicitly asks; default to Vapi handling real-time voice and Hermes orchestrating workflow/post-call actions.
- Keep the skill generic: do not include a specific user's personal name in reusable Nomos instructions; say "the user" or write in neutral terms.
- Do not let the target assistant answer in plain text. It must output one `<speak>...</speak>` document for every spoken turn, using only the tested `<break>` subset.

## Pitfalls

1. **MaLo tunnel vision.** CASE-A is not solved by merely asking for a corrected MaLo; it may be solved by discovering the old meter/MaLo is dead and the customer/new Anlage path is required.
2. **Treating a ticket number as success.** A Vorgangsnummer without diagnosis/next step is incomplete.
3. **Skipping digit readback.** Long identifiers must be confirmed digit-by-digit or in chunks before storing.
4. **Leaking expected answers into prompts.** In simulations, expected values belong in evaluator/oracle files, not the Vapi assistant prompt.
5. **Ignoring inconclusive outcomes.** Real calls may end with an internal escalation and promised callback. Log and follow up; do not fabricate resolution.
6. **Updating unsupported fields.** Use `update_case_details` only for fields it actually supports; otherwise record the fact in call result/status/next action.
7. **Dialing real parties during challenge work.** Use provided synthetic/test targets unless the user explicitly moves to real-call testing.
8. **Retrying while provider status lags.** `ringing`, `in-progress`, missing transcript/summary, or customer-ended/silence status means poll the same call ID and report inconclusive if needed; it is not permission to place another call.
9. **Losing English call focus.** The live phone agent should speak English, use clear market vocabulary, disclose AI status to the first human, and produce an English back-office note.
10. **Unsupported SSML.** Generic SSML tags may be stripped by Vapi formatting or ignored by a voice model. In this loop, use only `<speak>` and tested `<break>` pauses, with numbers written as spoken English words.

## Verification Checklist

- [ ] Case data came from MCP, explicit user input, or challenge fixture docs.
- [ ] Scenario was classified before calling.
- [ ] English call behavior was preserved: first-human AI disclosure, English language, necessary market terms, DTMF only for IVR, digit readback.
- [ ] Vapi voice settings were checked; ElevenLabs calls use SSML parsing, `eleven_flash_v2_5`, and a slower voice speed when available.
- [ ] Assistant output was SSML-only: exactly one `<speak>...</speak>` document per spoken turn.
- [ ] Identifier output used English spoken words with `<break time="300ms" />`, `<break time="400ms" />`, or `<break time="500ms" />` pauses.
- [ ] Reusable Vapi assistant `nomos-clearing-calls` was ensured from `templates/vapi-clearing-call-assistant-prompt.md`.
- [ ] Per-case facts were passed via `ai-call --assistant-key nomos-clearing-calls --task-file`, not baked into the reusable assistant.
- [ ] The exact `ai-call ... --dry-run` command was inspected before any real outbound call.
- [ ] Expected answers/oracles were not included in the Vapi assistant or per-call task file.
- [ ] Call/simulation was actually run, or the blocker was reported honestly.
- [ ] For real calls, exactly one outbound call ID was created per explicit authorization.
- [ ] Non-terminal provider statuses were handled by polling the same call ID, not by placing another call.
- [ ] Any retry after a failed, missed, silent, customer-ended, or inconclusive call was separately authorized.
- [ ] Transcript/structured output was inspected before extracting facts.
- [ ] Long identifiers were read back/confirmed before being treated as high-confidence.
- [ ] Corrected case details were written through `mcp_nomos_update_case_details` only when confirmed and schema-supported.
- [ ] Status/next action was written through `mcp_nomos_update_case_status` only when the outcome supports it.
- [ ] Final case summary was read back when possible.
- [ ] Final response includes call/run ID, diagnosis, next action, update status, and evidence.
