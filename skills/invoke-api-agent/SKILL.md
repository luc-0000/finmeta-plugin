---
name: invoke-api-agent
description: Invoke a published FinMeta API Agent (type=api) via its fc_invoke_url — synchronous HTTP POST. Use when the user wants to call a marketplace API agent (data / text-factor) and pay credits per call.
---

# Invoke FinMeta API Agent

Call a FinMeta **API Agent** (any agent with a non-null `fc_invoke_url`) published to the marketplace. Synchronous HTTP POST. **Charges `call_credits` per call** after `free_call_quota`; the owner calls free.

> **Token**: load from persistent storage first:
> ```bash
> export FINMETA_ACCESS_TOKEN=$(cat ~/.finmeta/access_token 2>/dev/null)
> ```
> If the file doesn't exist or is empty, stop and ask the user to run `finmeta-plugin` setup skill first.

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
curl -X POST "$FC_INVOKE_URL" \
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
