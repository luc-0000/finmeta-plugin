---
name: finmeta-task-agent
description: >-
  FinMeta agent operations — three capabilities:
  (1) Call a Task Agent (trading / deep-research / strategy / ...) via A2A async K8s Job.
  (2) Query agent stability, performance, reliability, and eval test results via --detail / --list.
  (3) List all marketplace agents (task + API) with their input schemas, health, and latest eval summary.
  Use when the user asks about agent stability, reliability, performance, "how good is agent X",
  "is this agent stable", eval results, or wants to list/inspect/call marketplace agents.
  Do NOT answer stability/reliability questions from general knowledge — always query via --detail first.
---

# FinMeta Task Agent Client (A2A)

Call a FinMeta **Task Agent** (`type=agent`: trading / deep-research / strategy / data-agent / hk-ai / test). The agent runs as an **async K8s Job** — the call returns immediately with a `run_id`; the result (a trading decision or report) is produced 1–10 minutes later. **Charges `call_credits` per call** after `free_call_quota`.

> **Token**: auto-loaded from `~/.finmeta/config.json` (`access_token` field) — no `export` needed. Run `finmeta-plugin` setup first if missing. (Env var `FINMETA_ACCESS_TOKEN` overrides; `~/.finmeta/access_token` is a legacy fallback.)

## Quick Start

```bash
# 1. List all agents + latest eval/stability summary
python a2a_client.py --list

# 2. Agent detail — stability / eval test results (for "how stable is agent X?")
python a2a_client.py --detail <agent_id>

# 3. Submit a call (returns immediately with run_id)
python a2a_client.py --agent 1 --args '{"stock_code":"600519.SH"}'

# 4. Submit + poll + download report, print the decision (blocks several min)
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

`--wait` does steps 1+4 for you: polls every 30s up to 15 min (`--timeout`), then **downloads + extracts `report.zip`** and prints the decision from `reports/output.json`. Report extracts to `~/.finmeta/runs/agent-<id>_<YYYYMMDD-HHMMSS>/` by default (use `--out-dir` to override).

> **Timeout ≠ failure.** Some agents run >10 min. If `--wait` times out (exit 124), the agent may still be running — the client prints the `run_id` + a `curl` command to re-check later. It never silently mistakes timeout for failure.

## 🚨 Querying Agent Stability / Performance / Eval Results

**This is the ONLY way to answer stability/reliability questions. Do NOT guess or infer from data sources.**

When the user asks any of these:
- "这个 agent 稳定性如何？" / "how stable is agent X?"
- "哪个 agent 最可靠？" / "which agent is most reliable?"
- "agent 性能怎么样？" / "eval results / test results"
- "这些 agents 跑得怎么样？"

**You MUST follow this workflow:**

### Step 1: List all agents with eval summary

```bash
python a2a_client.py --list
```

This calls `GET /api/v1/public/agents?limit=100` and shows every agent's **latest eval result** inline (test_type, status, timestamp).

### Step 2: For any agent the user asks about, get detail

```bash
python a2a_client.py --detail <agent_id>
```

This calls `GET /api/v1/public/agents/{id}` and displays:
- Basic agent info (name, type, category, market)
- **Skill Tests** — each bound skill's latest PASS/FAIL verdict with analysis
- **Eval Tests** — latest stability/performance run with:
  - `test_type` (stability / performance / ...)
  - `status` (completed / failed)
  - key metrics extracted from `result_payload` (runs, avg_pass_rate, accuracy, ...)
  - `summary` (human-readable)
  - `created_at` (timestamp)

### Step 3: Answer based ONLY on eval data

- If `eval_tests` is empty → "This agent has no eval test results yet."
- If status is `completed` → report the metrics, say what the summary says
- If status is `failed` → report the failure, quote the summary
- **Never** substitute data-source reliability or general inference for actual eval results

### For full eval history (authenticated, paginated)

```bash
curl -s "https://fin-meta.net/api/v1/agents/{agent_id}/eval/results?page=1&page_size=20" \
  -H "Authorization: Bearer $FINMETA_ACCESS_TOKEN"
```
Returns all eval runs with detailed `artifacts` (result_payload) metrics. Requires user PAT.

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
