# Nomos Challenge Scenarios

Source of truth inspected: `https://github.com/nomos-energy/voice-agent` (`README.md`, `CHEATSHEET.md`, `fixtures.json`, and `recordings/*.md`). Use this as a compact operational reference for the `nomos-clearing-calls` skill.

## Challenge objective

Build an English-speaking AI voice agent that clears stuck electricity signup cases. The agent receives structured case data, places or simulates the call, talks to an English-speaking market back-office clerk, captures the real diagnosis and next step, then writes a clean structured result and back-office note.

The agent must be pleasant enough that a clerk is willing to talk to it, but winning means moving the case forward.

## Non-negotiable rules

- First words to a **human** must disclose the agent is AI.
- Calls are in English.
- Use only synthetic challenge data. Do not use real customer details.
- In challenge mode, dial/use only provided clerk-agent/test targets, not real grid-operator or customer phone numbers.
- Phone menus/IVRs are not humans. Use DTMF only when a recorded menu explicitly asks for keypad input.
- Long identifiers must be read back digit-by-digit or in short chunks.
- No passwords or security questions are expected.

## Three signup stages

### 1. MaLo-Ident: find the market-location number

Nomos needs the official delivery-point identifier, the MaLo. Automated lookup may fail because the address is ambiguous, the meter number points elsewhere, no MaLo exists yet, or the operator never replied.

Call objective:

- identify the correct MaLo if one exists;
- use meter number and address to disambiguate;
- read the corrected MaLo back digit-by-digit;
- learn the next step if no MaLo can be found.

Example fixture:

- `CASE-C`: automated identification returned no clear match; building has multiple delivery points; the meter number disambiguates the correct MaLo.

Messy real-call pattern:

- Example 4 shows no clean MaLo answer. The clerk finds no MaLo for the meter, sees a meter removal and internal Zuarbeit/escalation, gives a Vorgangsnummer, and promises an update. Correct behavior is to log/wait/follow up, not invent a MaLo.

### 2. Kündigung: cancel the old contract

Nomos may need the customer's previous supplier to terminate the old contract before Nomos can supply. If that cancellation is ignored or rejected, the case stalls.

Call objective:

- confirm whether the old supplier received/processed/rejected the cancellation;
- learn why it is stuck;
- determine who owns the next action: Nomos, customer, previous supplier, or email agent;
- get a reference number if available.

This case type is explicitly described by the challenge even if the public `fixtures.json` currently focuses on CASE-A/B/C. The broad skill must support it.

### 3. Netzanmeldung: register Nomos with the grid operator

Nomos registers the connection with the grid operator. The operator confirms, rejects, sends only a receipt/APERAK, or says another process is already in progress.

Call objectives vary:

- if the registration **bounced**, find the real rejection reason and next step;
- if the registration is **silent/stuck**, confirm receipt/processing and whether resubmission is needed;
- if another registration/process blocks it, identify the blocker and owner.

Example fixtures:

- `CASE-A`: registration rejected with `Marktlokation nimmt nicht teil`; expected win is discovering the real reason and next step, e.g. the meter was a Baustromzähler and the old MaLo/connection cannot be used.
- `CASE-B`: APERAK/receipt received but no confirmation; expected win is confirmation it is being processed, a Vorgangsnummer, and no resubmission.

## Fixture summary

| Case | Scenario | Symptom | Goal | Expected style of outcome |
| --- | --- | --- | --- | --- |
| `CASE-A` | Bounced Netzanmeldung | MaLo exists but registration rejected as `Marktlokation nimmt nicht teil`. | Find real reason and next step. | Meter/connection issue such as removed Baustromzähler; customer/new Anlage next step; no ticket required. |
| `CASE-B` | Silent/stuck Netzanmeldung | APERAK/receipt but no confirmation after deadline. | Confirm received/in process, why stalled, get reference, confirm no resubmission. | Registration valid and taken into processing; Vorgangsnummer; wait/follow-up. |
| `CASE-C` | MaLo-Ident / wrong MaLo | Address ambiguous; current MaLo does not match. | Get correct MaLo using meter number; read back digit-by-digit. | Correct MaLo stored; resubmit registration with corrected identifier. |

## Call quality patterns from recordings

- Begin with concise AI disclosure to a human: "Hello, this is an AI assistant calling from Nomos...".
- State the case in one or two sentences and offer the relevant identifiers immediately.
- Use the clerk's vocabulary: supplier switching, grid registration, MaLo identification, cancellation, market communication, and reference number. Recognize process terms such as Lieferantenwechsel, Netzanmeldung, MaLo-Ident, Kündigung, Marktkommunikation, and Vorgangsnummer if they appear.
- Let the clerk search. Pauses and hold music are normal.
- Confirm IDs carefully:
  - MaLo: digit-by-digit.
  - Meter numbers: alphanumeric chunks.
  - Vorgangsnummer: chunks or digit-by-digit.
- Summarize the diagnosis and next step before closing.
- End once the case is actually cleared or the next action is known.

## What counts as a win

A win is a structured result with enough information for Nomos to act:

- `scenario_type`
- `diagnosis`
- `corrected_identifier` if any
- `reference_number` if any
- `resubmission_needed`
- `next_action_owner`
- `next_action`
- `backoffice_note_de` with English prose for this English-focused skill
- `confidence`
- supporting transcript evidence

A call is incomplete if it only has:

- a friendly exchange but no reason/next step;
- a ticket number but no diagnosis;
- a corrected identifier not read back/confirmed;
- an assumed backend update with no MCP/tool success;
- a clean-looking result when the transcript was actually inconclusive.
