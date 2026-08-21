---
name: invoke-api-agent
description: Invoke a published FinMeta API Agent (type=api) via its fc_invoke_url — synchronous HTTP POST. Use when the user wants to call a marketplace API agent (data / text-factor) and pay credits per call.
---

# Invoke FinMeta API Agent

Call a FinMeta **API Agent** (any agent with a non-null `fc_invoke_url`) published to the marketplace. Synchronous HTTP POST. **Charges `call_credits` per call** after `free_call_quota`; the owner calls free.

> **Token**: load the `access_token` field from `~/.finmeta/config.json`:
> ```bash
> export FINMETA_ACCESS_TOKEN=$(python3 -c "import json,os;print(json.load(open(os.path.expanduser('~/.finmeta/config.json'))).get('access_token',''))")
> ```
> If the file or field is missing, stop and ask the user to run `finmeta-plugin` setup skill first.

## Step 1: List API agents

```bash
curl -s 'https://fin-meta.net/api/v1/public/agents?type=api_agent' | python3 -m json.tool
```

Each result includes:
- `fc_invoke_url` — the POST endpoint to call
- `input_schema` — required JSON body fields
- `call_credits` / `free_call_quota` — cost

Pick the agent you want, then call it.

## Step 2: Call

```bash
curl --max-time 600 -X POST "$FC_INVOKE_URL" \
  -H "Authorization: Bearer $FINMETA_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '<JSON matching the agent input_schema>'
```

- `$FC_INVOKE_URL` = the agent's `fc_invoke_url` (from Step 1), e.g. `https://fin-meta.net/api/v1/repos/{repo_id}/fc/invoke`.
- Request body: JSON matching the agent's `input_schema` (from Step 1).
- Response: the JSON the agent returns.

## Notes

- Insufficient credits → HTTP 402.
- For Task Agents (trading / deep-research / strategy / ...), use `finmeta-task-agent` (A2A), not this.
- All discovery and invoke calls target **cloud** (`https://fin-meta.net`), not localhost.

## Timeouts

The invoke is a **synchronous LLM call — taking several minutes is normal**. A cut-off call almost always means some timeout layer fired, not that the agent is broken. Two layers can cut it, with different fixes:

1. **The shell/tool running curl (most common).** Many agent Bash tools default to ~120s and kill curl long before its own 600s limit. Symptom: the command is killed with no curl exit code and no JSON output. Fix: re-run with the tool timeout raised to ≥ 600s, or run the curl in the background and read the output file when it finishes.
2. **curl itself (`--max-time 600`).** curl exits with **code 28** — the agent genuinely ran past 10 minutes. The server may still finish that call (and bill it), so check with the user before blindly retrying — a retry may charge twice.

Step 1 (list agents) is a quick metadata call — a short timeout there is fine.
