# Nomos MCP Expectations

This project is expected to expose Nomos case data and update actions to Hermes through an MCP server. Use MCP as the source of truth whenever it is configured.

## Current repo state

The local `nomos-agent` repo currently includes `packages/fake-system`, which ships:

- a FastAPI dashboard;
- a streamable HTTP MCP server documented at `http://localhost:8765/mcp`;
- current fake-system tools that may be customer-oriented rather than case-oriented:
  - `list_customers`
  - `get_customer(customer_id)`
  - `update_customer(customer_id, name, email, company, plan, status, notes)`
  - resource `customers://all`

Until the fake system grows first-class case models, future Hermes agents may need to store structured clearing-call outcomes in generic `notes` and/or `status` fields. Do not pretend unsupported fields were updated.

## Expected future case tools

A mature Nomos MCP server may expose equivalents of:

- `list_cases()` / `search_cases(query)`
- `get_case(case_id)`
- `update_case(case_id, fields)`
- `record_call_outcome(case_id, outcome)`
- `set_corrected_malo(case_id, malo_id)`
- `set_reference_number(case_id, reference_number)`
- `set_next_action(case_id, owner, action, due_date)`
- `trigger_resubmission(case_id)`
- `trigger_email_agent(case_id, template, context)`
- `schedule_followup(case_id, due_date, reason)`

Tool names may be prefixed by Hermes' MCP naming convention, e.g. `mcp_nomos_get_case`, `mcp_fake_system_list_customers`, or another server-specific prefix.

## Fields a case read should provide if available

- `case_id` / external case key such as `CASE-A`
- `customer_name` if safe/synthetic and relevant
- `lieferant` / supplier, usually Nomos GmbH
- `process_step`: `malo_ident`, `kuendigung`, `netzanmeldung`, or equivalent
- `case_title` / `status_text` / rejection or symptom
- `malo_id` if known
- `zaehlernummer` / meter number if relevant
- `lieferstelle` / delivery address
- `anmeldung_datum` / sent date
- `lieferbeginn` / requested supply start
- `vnb_name` / grid operator or relevant market partner
- previous supplier if cancellation case
- previous communication or reference numbers
- allowed call/simulation target
- any notes from prior attempts

## Structured call outcome to store

When a call/simulation completes, normalize the result before updating:

```json
{
  "case_id": "CASE-A",
  "scenario_type": "bounced_registration",
  "call_status": "completed",
  "call_id": "vapi-call-or-run-id",
  "cleared": true,
  "diagnosis": "The meter behind the old MaLo was removed; a new Anlage is required.",
  "corrected_malo_id": null,
  "reference_number": null,
  "resubmission_needed": false,
  "next_action_owner": "customer",
  "next_action": "Contact customer / start new Anlage process",
  "followup_due": null,
  "backoffice_note_de": "...",
  "confidence": "high",
  "evidence": "Transcript-supported summary or quote"
}
```

Adapt values by scenario:

- `malo_ident`: often `corrected_malo_id` + `next_action = resubmit_registration`.
- `bounced_registration`: often diagnosis + customer/new Anlage/resubmission decision.
- `silent_registration`: often reference number + `next_action = wait_for_processing`.
- `kuendigung`: often previous supplier/customer/Nomos owner + reminder/customer email action.
- `escalation`: often reference + follow-up date/window + `next_action = wait_or_follow_up`.

## Back-office note style

Keep notes short, factual, and action-oriented. Write the note prose in English while preserving necessary energy-market terms when they are the actual process names. Keep the existing `backoffice_note_de` field name when that is the current schema key, but fill it with English text for this English-focused skill. Example templates:

### Corrected MaLo

```text
Clearing call with <partner> on <date>: case for <address>/<meter>. Correct MaLo according to the back-office clerk: <malo>, read back digit by digit and confirmed during the call. Next step: resend grid registration with the corrected MaLo.
```

### Bounced registration / removed meter

```text
Clearing call with <partner> on <date>: checked grid registration status "Marktlokation nimmt nicht teil". According to the back-office clerk, the related meter/connection is no longer active (<reason/date if given>); the old MaLo cannot be used. Next step: contact the customer / clarify the new installation. Do not resubmit on the old MaLo.
```

### Silent registration

```text
Clearing call with <partner> on <date>: registration from <sent_date> has been received and is technically valid, but has not been processed further yet. No resubmission is required. Reference: <reference>. Expected processing/update: <timing>.
```

### Kündigung / previous supplier blocker

```text
Clearing call about cancellation/previous supplier on <date>: status according to the back-office clerk: <diagnosis>. Next step: <owner> should <action>. Reference: <reference or none>. Follow-up action: <email/customer/reminder/follow-up>.
```

### Escalation / inconclusive

```text
Clearing call with <partner> on <date>: the case could not be fully clarified. The back office escalated it to <department/owner>. Reference: <reference>. Open question: <question>. Expected update: <timing>. Next step: wait/follow up.
```

## Behavior while MCP surface is incomplete

- Do not invent unavailable tools.
- If no MCP tools are available in the active session, say that the Nomos MCP server/config still needs to be added before Hermes can read or update case details.
- If the user explicitly provided enough synthetic case context and an authorized test target, Hermes may still set up/place/simulate the Vapi call.
- If only a generic `update_customer(..., notes/status=...)` tool exists, write the normalized outcome into `notes` and set a conservative status if appropriate.
- If no update tool exists, provide the exact pending update payload and back-office note for Bruno to apply later.
- After an update, read the record back if a read tool exists and report what was verified.
