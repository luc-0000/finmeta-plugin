---
name: finmeta-task-agent
description: Call a FinMeta Task Agent (trading / deep-research / strategy / data-agent / ...) via the A2A protocol. Use when the user wants to run a task-type agent and get its decision or report.
---

# FinMeta Task Agent Client (A2A)

Call a FinMeta **Task Agent** (`type=agent`: trading / deep-research / strategy / data-agent / hk-ai / test) via **A2A**. **Charges `call_credits` per call** after `free_call_quota`.

> **Token**: load from persistent storage first:
> ```bash
> export FINMETA_ACCESS_TOKEN=$(cat ~/.finmeta/access_token 2>/dev/null)
> ```
> If the file doesn't exist or is empty, stop and ask the user to run `finmeta-plugin` setup skill first.

## Quick Start (Python)

```bash
# Discover task agents
python a2a_client.py --list

# Call a task agent
python a2a_client.py --agent 1 --args '{"input":"600519.SH"}'

# Call + poll for result (blocks until completed)
python a2a_client.py --agent 1 --args '{"input":"600519.SH"}' --wait
```

The script handles:
- Token loading (env var → `~/.finmeta/access_token`)
- Proper A2A JSON-RPC body formatting (agent_args nested under `params.message.parts[0].metadata`)
- Job-mode response: returns immediately with `run_id`, then optionally polls for result
- For non-job-mode agents (streaming): streams raw SSE response

## Manual Call (curl)

A2A request body MUST follow the JSON-RPC message structure — agent args go in `params.message.parts[].metadata.agent_args`:

```bash
curl -X POST "https://fin-meta.net/api/v1/agents/{agent_id}/a2a/" \
  -H "Authorization: Bearer $FINMETA_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "params": {
      "message": {
        "parts": [{
          "metadata": {
            "agent_args": {"input": "600519.SH"}
          }
        }]
      }
    }
  }'
```

- `{agent_id}` — find via `python a2a_client.py --list` or `GET /api/v1/public/agents`.
- Job-mode agents (trading / deep-research / strategy / data-agent / hk-ai / test) return immediately with `{"run_id","job_name","status":"job_started"}`. Poll:
  ```bash
  curl -s "https://fin-meta.net/api/v1/agents/{agent_id}/runs?limit=1" \
    -H "Authorization: Bearer $FINMETA_ACCESS_TOKEN"
  ```
- Non-job-mode agents stream SSE (the backend acts as a reverse proxy).

## Notes

- For API Agents (`type=api`), use `invoke-api-agent` (plain HTTP), not this.
- Insufficient credits → HTTP 402.
