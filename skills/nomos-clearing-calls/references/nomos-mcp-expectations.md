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

Keep notes short, factual, and action-oriented. Example templates:

### Corrected MaLo

```text
Kläranruf mit <partner> am <date>: Fall zu <address>/<meter>. Korrekte MaLo laut Sachbearbeitung: <malo>, im Gespräch ziffernweise zurückgelesen und bestätigt. Nächster Schritt: Netzanmeldung mit korrigierter MaLo erneut senden.
```

### Bounced registration / removed meter

```text
Kläranruf mit <partner> am <date>: Netzanmeldung mit Status "Marktlokation nimmt nicht teil" geprüft. Laut Sachbearbeitung ist der zugehörige Zähler/Anschluss nicht mehr aktiv (<reason/date if given>); alte MaLo kann nicht verwendet werden. Nächster Schritt: Kunde kontaktieren / neue Anlage klären. Keine erneute Anmeldung auf alter MaLo.
```

### Silent registration

```text
Kläranruf mit <partner> am <date>: Anmeldung vom <sent_date> liegt vor und ist fachlich korrekt, wurde aber noch nicht weiterbearbeitet. Keine erneute Einreichung erforderlich. Vorgangsnummer: <reference>. Erwartete Bearbeitung/Rückmeldung: <timing>.
```

### Kündigung / previous supplier blocker

```text
Kläranruf zu Kündigung/Altlieferant am <date>: Status laut Sachbearbeitung: <diagnosis>. Nächster Schritt: <owner> soll <action>. Referenz: <reference or none>. Folgeaktion: <email/customer/reminder/follow-up>.
```

### Escalation / inconclusive

```text
Kläranruf mit <partner> am <date>: Fall konnte nicht abschließend geklärt werden. Sachbearbeitung hat an <department/owner> eskaliert. Vorgangsnummer: <reference>. Offene Frage: <question>. Erwartete Rückmeldung: <timing>. Nächster Schritt: warten/nachfassen.
```

## Behavior while MCP surface is incomplete

- Do not invent unavailable tools.
- If no MCP tools are available in the active session, say that the Nomos MCP server/config still needs to be added before Hermes can read or update case details.
- If the user explicitly provided enough synthetic case context and an authorized test target, Hermes may still set up/place/simulate the Vapi call.
- If only a generic `update_customer(..., notes/status=...)` tool exists, write the normalized outcome into `notes` and set a conservative status if appropriate.
- If no update tool exists, provide the exact pending update payload and back-office note for Bruno to apply later.
- After an update, read the record back if a read tool exists and report what was verified.
