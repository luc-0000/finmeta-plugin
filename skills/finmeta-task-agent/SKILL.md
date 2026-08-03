---
name: finmeta-task-agent
description: Call a FinMeta Task Agent (trading / deep-research / strategy / data-agent / ...) via A2A. Async — the agent runs as a K8s Job for 1–10 min, then returns a decision or report. Use when the user wants a long-running agent's output (not a one-shot data call — that's invoke-api-agent).
---

# FinMeta Task Agent Client (A2A)

Call a FinMeta **Task Agent** (`type=agent`: trading / deep-research / strategy / data-agent / hk-ai / test). The agent runs as an **async K8s Job** — the call returns immediately with a `run_id`; the result (a trading decision or report) is produced 1–10 minutes later. **Charges `call_credits` per call** after `free_call_quota`.

> **Token**: auto-loaded from `~/.finmeta/config.json` (`access_token` field) — no `export` needed. Run `finmeta-plugin` setup first if missing. (Env var `FINMETA_ACCESS_TOKEN` overrides; `~/.finmeta/access_token` is a legacy fallback.)

## Quick Start

```bash
# 1. List task agents + their input_schema (so you know which keys to pass)
python a2a_client.py --list

# 2. Submit a call (returns immediately with run_id)
python a2a_client.py --agent 1 --args '{"stock_code":"600519.SH"}'

# 3. Submit + poll + download report, print the decision (blocks several min)
python a2a_client.py --agent 1 --args '{"stock_code":"600519.SH"}' --wait
```

The `--args` keys **must match the agent's `input_schema`** (shown by `--list`). Examples:
- `trading_agent_tauric` → `{"stock_code":"600519.SH"}`
- `8k-item-code` (API agent) → not this skill, use `invoke-api-agent`

## How it works

1. `POST /api/v1/agents/{id}/a2a/` with the A2A JSON-RPC body. The backend extracts `params.message.parts[0].metadata.agent_args` and injects it into the Pod as the `AGENT_ARGS` env var.
2. Backend starts a K8s Job and returns `{"run_id","job_name","status":"job_started"}` immediately.
3. The agent runs (multi-round debate / research) for 1–10 min, writes its result, and calls back the backend.
4. Poll `GET /api/v1/agents/{id}/runs?limit=1` until `status=completed`. The decision (`buy`/`sell`/`hold`) is in `result` and in `artifacts.report_url` (a `report.zip` containing `reports/output.json`, `reports/run.log`, and a full analysis JSON).

`--wait` does steps 1+4 for you: polls every 30s up to 15 min (`--timeout`), then **downloads + extracts `report.zip`** and prints the decision from `reports/output.json`. Use `--out-dir` to choose the extract location (default: current dir).

> **Timeout ≠ failure.** Some agents run >10 min. If `--wait` times out (exit 124), the agent may still be running — the client prints the `run_id` + a `curl` command to re-check later. It never silently mistakes timeout for failure.

## Manual call (curl)

```bash
curl -X POST "https://fin-meta.net/api/v1/agents/{agent_id}/a2a/" \
  -H "Authorization: Bearer $FINMETA_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"params":{"message":{"parts":[{"metadata":{"agent_args":{"stock_code":"600519.SH"}}}]}}}'
```

The `agent_args` object MUST be nested at `params.message.parts[0].metadata.agent_args` — a flat `{"stock_code":...}` body will NOT reach the Pod (`AGENT_ARGS` stays unset, agent exits empty).

## Notes

- Job-mode only (trading / deep-research / strategy / data-agent / hk-ai / test). For `type=api` agents, use `invoke-api-agent`.
- Insufficient credits → HTTP 402.
- HTTP uses curl, not urllib — fin-meta.net is behind Cloudflare bot-fight, which blocks default Python clients.
