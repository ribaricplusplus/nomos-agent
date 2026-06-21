# Nomos Agent

Nomos Agent is the hackathon project repo for a Hermes-orchestrated clearing-call workflow:

- **Nomos fake system**: a PostgreSQL-backed case system with a web dashboard and MCP server.
- **Hermes Agent**: the workflow orchestrator that reads/updates Nomos cases through MCP and prepares call tasks.
- **Vapi + Twilio**: the realtime voice layer that places outbound AI phone calls from an owned Twilio number.

This repo is the **main project repo**. The working Hermes fork lives separately at:

- Main repo: <https://github.com/ribaricplusplus/nomos-agent>
- Hermes fork: <https://github.com/ribaricplusplus/hermes-agent/tree/hackathon>

The fork's `hackathon` branch contains the Vapi/Twilio telephony helper changes and the Vapi eval/smoke harnesses used by this project.

## Architecture

```text
Hermes profile: vapihermes
  |
  | loads Nomos skill from this repo
  | ~/.hermes/profiles/vapihermes/config.yaml
  |   skills.external_dirs -> ~/projects/nomos-agent/skills
  |
  | connects to Nomos MCP
  v
Nomos fake-system MCP server  <---->  Postgres
  |
  | shared data layer
  v
Nomos dashboard

For calls:
Hermes telephony helper -> Vapi assistant/call -> Twilio-owned phone number -> phone network
```

Hermes should stay the workflow orchestrator. Vapi is the realtime voice agent. Do **not** make Hermes the Vapi Custom LLM unless you are intentionally changing the architecture.

## Prerequisites

Install these locally:

- Git + GitHub CLI (`gh`) if you want to push changes.
- Docker + Docker Compose.
- Node.js 20+ and pnpm 9+.
- Python 3.11, 3.12, or 3.13.
- [`uv`](https://docs.astral.sh/uv/) for Python environments.
- A Hermes model provider credential, configured through `hermes setup` or `hermes model`.
- A Vapi account/API key.
- A Twilio account SID + auth token, plus a Twilio phone number.
- Optional but recommended: ElevenLabs voice configured in Vapi for better call quality.

Secrets belong in `~/.hermes/profiles/vapihermes/.env`, not in this git repo.

## 1. Clone both repos

Use the Nomos repo as the project root and the Hermes fork as the runtime:

```bash
mkdir -p ~/projects
cd ~/projects

git clone https://github.com/ribaricplusplus/nomos-agent.git

git clone https://github.com/ribaricplusplus/hermes-agent.git
cd hermes-agent
git switch hackathon
uv sync
```

The fork currently has `hackathon` as its default branch, but the explicit `git switch hackathon` keeps the setup unambiguous.

## 2. Start the Nomos fake system

From the Nomos repo:

```bash
cd ~/projects/nomos-agent
pnpm install
pnpm fake-system install:py
cp .env.example .env
```

By default the dashboard is exposed on `8000` and MCP on `8765`:

```bash
docker compose up -d --build
```

Open/check:

```text
Dashboard:  http://localhost:8000
MCP:        http://127.0.0.1:8765/mcp
```

If port `8765` is already occupied, edit `~/projects/nomos-agent/.env` before starting Compose:

```env
MCP_PORT=8766
```

Then your Hermes MCP URL must also use `http://127.0.0.1:8766/mcp`.

Useful service commands:

```bash
pnpm up                 # docker compose up -d
pnpm logs               # docker compose logs -f
pnpm down               # docker compose down
pnpm fake-system smoke  # end-to-end fake-system smoke test, when services are up
```

## 3. Create the isolated Hermes profile

The project uses a separate Hermes profile named `vapihermes` so credentials, skills, memories, sessions, MCP servers, and gateway state stay isolated from your normal Hermes profile.

```bash
export HERMES_AGENT_DIR="$HOME/projects/hermes-agent"
export NOMOS_AGENT_DIR="$HOME/projects/nomos-agent"
export HERMES_PROFILE_HOME="$HOME/.hermes/profiles/vapihermes"

if [ ! -d "$HERMES_PROFILE_HOME" ]; then
  "$HERMES_AGENT_DIR/.venv/bin/hermes" profile create vapihermes --no-alias
fi
```

Create a wrapper that always runs the forked Hermes with the `vapihermes` profile:

```bash
mkdir -p ~/.local/bin
cat > ~/.local/bin/hermes-vapi <<'EOF'
#!/usr/bin/env bash
set -euo pipefail
HERMES_AGENT_DIR="${HERMES_AGENT_DIR:-$HOME/projects/hermes-agent}"
exec "$HERMES_AGENT_DIR/.venv/bin/hermes" --profile vapihermes "$@"
EOF
chmod +x ~/.local/bin/hermes-vapi
```

Make sure `~/.local/bin` is on your `PATH`, then configure the model/provider for Hermes:

```bash
hermes-vapi setup
# or later:
hermes-vapi model
hermes-vapi doctor
```

The hackathon profile used `openai-codex` with `gpt-5.5`, but any capable Hermes provider/model can work as the orchestrator.

## 4. Install the local telephony skill and wrappers

The telephony skill version needed here is in the Hermes fork's `hackathon` branch. Copy that local skill into the isolated profile:

```bash
mkdir -p "$HERMES_PROFILE_HOME/skills/productivity"
cp -a "$HERMES_AGENT_DIR/optional-skills/productivity/telephony" \
  "$HERMES_PROFILE_HOME/skills/productivity/"
```

Create helper wrappers:

```bash
cat > ~/.local/bin/hermes-vapi-phone <<'EOF'
#!/usr/bin/env bash
set -euo pipefail
HERMES_AGENT_DIR="${HERMES_AGENT_DIR:-$HOME/projects/hermes-agent}"
export HERMES_HOME="${HERMES_HOME:-$HOME/.hermes/profiles/vapihermes}"
SCRIPT="$(find "$HERMES_HOME/skills" -path '*/telephony/scripts/telephony.py' -print -quit)"
if [[ -z "$SCRIPT" ]]; then
  echo "telephony.py not found under $HERMES_HOME/skills" >&2
  exit 1
fi
exec "$HERMES_AGENT_DIR/.venv/bin/python3" "$SCRIPT" "$@"
EOF
chmod +x ~/.local/bin/hermes-vapi-phone

cat > ~/.local/bin/hermes-vapi-smoke <<'EOF'
#!/usr/bin/env bash
set -euo pipefail
HERMES_AGENT_DIR="${HERMES_AGENT_DIR:-$HOME/projects/hermes-agent}"
export HERMES_HOME="${HERMES_HOME:-$HOME/.hermes/profiles/vapihermes}"
cd "$HERMES_AGENT_DIR/hackathon/vapi-no-call-smoke"
exec "$HERMES_AGENT_DIR/.venv/bin/python3" vapi_no_call_smoke.py "$@"
EOF
chmod +x ~/.local/bin/hermes-vapi-smoke

cat > ~/.local/bin/hermes-vapi-iterate <<'EOF'
#!/usr/bin/env bash
set -euo pipefail
HERMES_AGENT_DIR="${HERMES_AGENT_DIR:-$HOME/projects/hermes-agent}"
export HERMES_HOME="${HERMES_HOME:-$HOME/.hermes/profiles/vapihermes}"
cd "$HERMES_AGENT_DIR/hackathon/vapi-iteration"
exec "$HERMES_AGENT_DIR/.venv/bin/python3" vapi_iterate.py "$@"
EOF
chmod +x ~/.local/bin/hermes-vapi-iterate
```

## 5. Attach Nomos skills and MCP to the profile

The Nomos clearing-call skill lives in this repo and should be loaded by Hermes as an external skill directory. The Nomos fake system exposes MCP over HTTP.

Set the MCP URL to match your Compose port:

```bash
export NOMOS_MCP_URL="http://127.0.0.1:8765/mcp"
# If you used MCP_PORT=8766 in .env, use this instead:
# export NOMOS_MCP_URL="http://127.0.0.1:8766/mcp"
```

Patch the profile config idempotently:

```bash
HERMES_HOME="$HERMES_PROFILE_HOME" \
NOMOS_AGENT_DIR="$NOMOS_AGENT_DIR" \
NOMOS_MCP_URL="$NOMOS_MCP_URL" \
"$HERMES_AGENT_DIR/.venv/bin/python3" - <<'PY'
import os
from pathlib import Path
import yaml

home = Path(os.environ["HERMES_HOME"])
config_path = home / "config.yaml"
config_path.parent.mkdir(parents=True, exist_ok=True)
config = yaml.safe_load(config_path.read_text()) if config_path.exists() else {}
if not isinstance(config, dict):
    config = {}

nomos_skills = str(Path(os.environ["NOMOS_AGENT_DIR"]) / "skills")
config.setdefault("skills", {})["external_dirs"] = [nomos_skills]
config.setdefault("mcp_servers", {})["nomos"] = {
    "url": os.environ["NOMOS_MCP_URL"],
    "enabled": True,
}

config_path.write_text(yaml.safe_dump(config, sort_keys=False), encoding="utf-8")
print(f"updated {config_path}")
PY
```

Verify Hermes sees the MCP server:

```bash
hermes-vapi mcp list
hermes-vapi skills list | grep nomos || true
```

Expected MCP entry:

```text
nomos  http://127.0.0.1:<port>/mcp  enabled
```

## 6. Configure Vapi, Twilio, and voice settings

Save provider secrets into the isolated profile. Use real values here; do not commit them.

```bash
export HERMES_HOME="$HOME/.hermes/profiles/vapihermes"

hermes-vapi-phone save-vapi "$VAPI_API_KEY"
hermes-vapi-phone save-twilio "$TWILIO_ACCOUNT_SID" "$TWILIO_AUTH_TOKEN"
```

If you do not already have a Twilio number, search and buy one:

```bash
hermes-vapi-phone twilio-search --country US --limit 10
hermes-vapi-phone twilio-buy "+15551234567" --save-env
```

If you already have a number in Twilio, persist it as the default:

```bash
hermes-vapi-phone twilio-owned
hermes-vapi-phone twilio-set-default "+15551234567" --save-env
```

Import the Twilio number into Vapi and persist the returned Vapi phone-number ID:

```bash
hermes-vapi-phone vapi-import-twilio --save-env
```

Recommended voice/model defaults for the Nomos demo:

```bash
cat >> "$HERMES_HOME/.env" <<'EOF'
PHONE_PROVIDER=vapi
VAPI_VOICE_PROVIDER=11labs
VAPI_VOICE_ID=cjVigY5qzO86Huf0OWal
VAPI_MODEL=gpt-5.4-mini
VAPI_ENABLE_SSML_PARSING=true
VAPI_VOICE_SPEED=0.85
VAPI_OPTIMIZE_STREAMING_LATENCY=1
VAPI_11LABS_MODEL=eleven_flash_v2_5
VAPI_11LABS_LANGUAGE=en
EOF
```

Notes:

- `VAPI_VOICE_ID=cjVigY5qzO86Huf0OWal` is ElevenLabs **Eric - Smooth, Trustworthy**.
- Use a Vapi model available to your Vapi org. The hackathon setup used `gpt-5.4-mini`.
- If your Vapi org does not have an ElevenLabs key/provider configured, add it in the Vapi dashboard first.
- For German or stricter identifier pronunciation, try `VAPI_11LABS_MODEL=eleven_multilingual_v2` and/or `VAPI_11LABS_LANGUAGE=de`.

Check the profile state:

```bash
hermes-vapi-phone diagnose
hermes-vapi-smoke check-auth
hermes-vapi-smoke list-phone-numbers
```

`hermes-vapi-smoke` is intentionally no-call: it can list Vapi resources and use `/chat`, but it refuses Vapi `/call` endpoints.

## 7. Create/update the reusable Nomos Vapi assistant

The reusable assistant contains stable call behavior. Per-case facts are passed later as a task file.

```bash
export HERMES_AGENT_DIR="$HOME/projects/hermes-agent"
export NOMOS_SKILL_DIR="$HOME/projects/nomos-agent/skills/nomos-clearing-calls"
export SCRIPT="$HOME/.hermes/profiles/vapihermes/skills/productivity/telephony/scripts/telephony.py"

hermes-vapi-phone vapi-assistant ensure \
  --key nomos-clearing-calls \
  --name "Nomos clearing caller" \
  --prompt-file "$NOMOS_SKILL_DIR/templates/vapi-clearing-call-assistant-prompt.md" \
  --task-variable case_context \
  --max-duration 5 \
  --dry-run
```

If the dry run looks right, create/update the assistant in Vapi:

```bash
hermes-vapi-phone vapi-assistant ensure \
  --key nomos-clearing-calls \
  --name "Nomos clearing caller" \
  --prompt-file "$NOMOS_SKILL_DIR/templates/vapi-clearing-call-assistant-prompt.md" \
  --task-variable case_context \
  --max-duration 5
```

Re-run this command whenever `skills/nomos-clearing-calls/templates/vapi-clearing-call-assistant-prompt.md` changes.

## 8. Smoke-test the full local stack

Run these checks before placing any real call:

```bash
# Fake system containers and HTTP ports
docker compose ps

# Vapi/Twilio/Hermes profile readiness
hermes-vapi-phone diagnose
hermes-vapi-smoke check-auth
hermes-vapi-smoke list-phone-numbers

# MCP registration
hermes-vapi mcp list

# Hermes should be able to load Nomos skill + reach MCP.
hermes-vapi chat -q "Load the nomos-clearing-calls skill. List the available Nomos cases through MCP. Do not place a call."
```

For prompt/eval iteration without PSTN calls:

```bash
hermes-vapi-iterate diagnose
hermes-vapi-iterate list-scenarios
hermes-vapi-iterate pacing-check
hermes-vapi-iterate quick --scenario scenarios/case_h_identifier_pacing_ssml.json
```

The iteration harness uses Vapi eval/chat APIs. It does **not** place Twilio/PSTN calls.

## 9. Place a Nomos clearing call

Only place a real call after explicit authorization for one call to one target number.

1. Have Hermes retrieve or accept the case facts.
2. Write a short per-case task file.
3. Dry-run the exact call command.
4. Run the same command without `--dry-run` only after authorization.
5. Poll that same call ID until terminal status.
6. Save supported facts back to Nomos via MCP.

Example task file:

```bash
cat > /tmp/nomos-call-task.md <<'EOF'
# Case context for this call

Case ID: CASE-C
Supplier: Nomos GmbH
Grid/operator/target: <operator name>
Current MaLo ID: <if known>
Meter number / Zählernummer: <if known>
Delivery address / Lieferstelle: <address>
Status/symptom: MaLo identification failed; Nomos needs the correct market-location ID.
Scenario type: MaLo-Ident
Goal: Confirm the correct MaLo for the meter/address and whether Nomos should resubmit registration.
Information to obtain:
- Correct 11-digit MaLo ID, if available.
- Whether the current registration can be resubmitted.
- Reference/Vorgangsnummer, if the clerk creates one.
EOF
```

Dry-run:

```bash
hermes-vapi-phone ai-call "+15551234567" \
  --provider vapi \
  --assistant-key nomos-clearing-calls \
  --task-file /tmp/nomos-call-task.md \
  --first-sentence "Hello, I am an artificial intelligence from Nomos GmbH calling about electricity signup case CASE-C. Could you help me clarify it?" \
  --max-duration 5 \
  --dry-run
```

Real call, only after explicit approval:

```bash
hermes-vapi-phone ai-call "+15551234567" \
  --provider vapi \
  --assistant-key nomos-clearing-calls \
  --task-file /tmp/nomos-call-task.md \
  --first-sentence "Hello, I am an artificial intelligence from Nomos GmbH calling about electricity signup case CASE-C. Could you help me clarify it?" \
  --max-duration 5
```

Then poll the returned call ID:

```bash
hermes-vapi-phone ai-status "<call_id>" --provider vapi
```

## Repository layout

```text
.
├── compose.yml                         # Postgres + fake-system web + MCP
├── packages/fake-system                # FastAPI dashboard, SQLAlchemy, Alembic, MCP server
└── skills/nomos-clearing-calls         # Hermes Nomos workflow skill and Vapi prompt template
```

Important Nomos skill files:

- `skills/nomos-clearing-calls/SKILL.md` — workflow rules for Hermes.
- `skills/nomos-clearing-calls/templates/vapi-clearing-call-assistant-prompt.md` — stable Vapi assistant behavior.
- `skills/nomos-clearing-calls/references/nomos-challenge-scenarios.md` — synthetic challenge scenarios.
- `skills/nomos-clearing-calls/references/nomos-mcp-expectations.md` — expected MCP usage/update behavior.

Important Hermes fork files:

- `optional-skills/productivity/telephony/SKILL.md`
- `optional-skills/productivity/telephony/scripts/telephony.py`
- `hackathon/vapi-no-call-smoke/`
- `hackathon/vapi-iteration/`

## Troubleshooting

### Hermes cannot see Nomos MCP tools

Check the fake-system MCP port and the profile config agree:

```bash
cd ~/projects/nomos-agent
docker compose ps
hermes-vapi mcp list
```

If Compose uses `MCP_PORT=8766`, Hermes must use `http://127.0.0.1:8766/mcp`.

### Telephony helper cannot find credentials

Make sure you are using the isolated profile:

```bash
export HERMES_HOME="$HOME/.hermes/profiles/vapihermes"
hermes-vapi-phone diagnose
```

The secrets should be in:

```text
~/.hermes/profiles/vapihermes/.env
```

### Vapi auth works but calls fail

Check:

- `VAPI_API_KEY` is valid.
- `VAPI_PHONE_NUMBER_ID` exists after `vapi-import-twilio --save-env`.
- The Twilio number is imported into the same Vapi org.
- The chosen `VAPI_MODEL` is available to the Vapi org.
- ElevenLabs/provider credentials are configured in Vapi if using `VAPI_VOICE_PROVIDER=11labs`.

### Calls are too fast or identifiers sound wrong

Try slower or multilingual settings in the profile `.env`:

```env
VAPI_VOICE_SPEED=0.75
VAPI_ENABLE_SSML_PARSING=true
VAPI_OPTIMIZE_STREAMING_LATENCY=1
VAPI_11LABS_MODEL=eleven_multilingual_v2
```

Then re-run:

```bash
hermes-vapi-phone diagnose
hermes-vapi-phone vapi-assistant ensure \
  --key nomos-clearing-calls \
  --name "Nomos clearing caller" \
  --prompt-file "$HOME/projects/nomos-agent/skills/nomos-clearing-calls/templates/vapi-clearing-call-assistant-prompt.md" \
  --task-variable case_context \
  --max-duration 5
```

### Do not accidentally place duplicate calls

For real calls, one explicit authorization covers exactly one outbound call attempt. If a call status is delayed, missing transcript, `ringing`, `in-progress`, `customer-ended`, or otherwise inconclusive, keep polling/reporting that same call ID. Do not start a second call without fresh authorization.
