---
name: invoke-api-agent
description: >-
  Answer finance/data questions by routing to the right FinMeta marketplace API agent and
  invoking it, or call an agent the user names. Use when the user asks ANY question that a
  marketplace agent could answer — 盘前隔夜、新闻快讯、公告/监管动态、资金流、涨停池、
  研报/管理层纪要、宏观/期货/CFTC、加密动态、国家队 ETF 动向、板块热度 — even when they
  never mention "agent"; or when they explicitly want to call a marketplace API agent
  (type=api), their own private strategy agent, or fetch the latest output of a scheduled
  agent.
---

# Invoke FinMeta API Agent

Call a FinMeta **API Agent** (any agent with a non-null `fc_invoke_url`) — either published to the marketplace, or your own private strategy agent. Synchronous HTTP POST. **Charges `call_credits` per call** after `free_call_quota`; the owner calls free.

> **Token**: load the `access_token` field from `~/.finmeta/config.json`:
> ```bash
> export FINMETA_ACCESS_TOKEN=$(python3 -c "import json,os;print(json.load(open(os.path.expanduser('~/.finmeta/config.json'))).get('access_token',''))")
> ```
> If the file or field is missing (or a call returns 401), stop and give the user the setup
> steps: get a token at https://fin-meta.net/profile → **Access Token**, save it into
> `~/.finmeta/config.json` — full steps in the plugin root `SKILL.md` (**Setup** section).

## Step 0: Route a question to the right agent

When the user asked a **question**（「美股盘前如何」「有什么新闻」「国家队加仓了吗」）rather than naming an agent, pick the agent yourself from the live catalog — never from a memorized list:

1. **Load the catalog**: `GET https://fin-meta.net/api/v1/public/agents?type=api_agent&page_size=100` with Bearer token (also returns your private strategy agents). ⚠️ The param is `page_size` (default 20, max 100) — `limit` is **silently ignored** and truncates the catalog to 20 with no error; if response `total` > returned count, walk `page=2,3,...`. Cache the parsed list to `~/.finmeta/agent-catalog.json` (with fetch timestamp) and reuse it for **24 h**. On a cache hit where nothing matches, delete the file and re-fetch once before concluding "no match" — the marketplace may have added an agent since.
2. **Match**: read each agent's `name` and `description` and pick the best **semantic** match for the question — you are the router; descriptions are owner-written summaries of what each agent does and when to use it. When the question names a market or instrument type, pre-filter with the structured fields (`asset_market`, `asset_instrument`).
3. **Ambiguous** (2+ plausible candidates): show each candidate's name + one-line description + cost and ask the user to pick — don't guess, invocations charge credits.
4. **No match**: say so plainly and offer the closest alternative. Plain price/kline questions belong to the `market-data` skill (free). Never invoke an unrelated agent.
5. **First invoke of an agent** in a conversation: tell the user it charges `call_credits` per call (owner invokes are free) and get a go-ahead.
6. **Boundary**: deep trading decisions / multi-minute research（「值不值得买」「深度研究 X」）→ use `finmeta-task-agent` instead. API agents are synchronous data / scan / news agents.

The live catalog is the single source of routing truth: newly listed agents become routable without any plugin update.

## Step 1: List API agents

```bash
curl -s 'https://fin-meta.net/api/v1/public/agents?type=api_agent&page_size=100' \
  -H "Authorization: Bearer $FINMETA_ACCESS_TOKEN" | python3 -m json.tool
```

⚠️ `page_size` (default 20, max 100) is the real param — `limit` is silently ignored (catalog would truncate to 20, no error). If `total` > returned items, walk `page=2,3,...`.

With the token the list also includes **your own private strategy agents** (`agent_category: "strategy_api_agent"`, `market_status` not `listed`) — they never appear on the public marketplace and are invisible to other users. Without a token you only see public marketplace agents; an invalid/expired token returns 401 (re-run the plugin setup to refresh it).

Each result includes:
- `fc_invoke_url` — the POST endpoint to call
- `input_schema` — required JSON body fields
- `call_credits` / `free_call_quota` — cost

Pick the agent you want, then call it. **If `agent_category` is `scheduled_api_agent`, STOP — use GET, not POST (see Step 3).** This is the same catalog Step 0 caches — reuse a fresh `~/.finmeta/agent-catalog.json` instead of re-fetching.

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

## Step 3: Scheduled API agents — GET the latest result (never POST)

A `scheduled_api_agent` runs on the **owner's schedule** (e.g. once a day pre-market) and serves one shared result to everyone. For these agents the `fc_invoke_url` field already points to the **query** endpoint `GET /repos/{repo_id}/fc/latest` — read it with GET:

```bash
curl -s "$FC_INVOKE_URL" -H "Authorization: Bearer $FINMETA_ACCESS_TOKEN"
```

- The response is the **latest scheduled run's shared result** — idempotent, executes nothing, same for every caller. Access/billing follow the same per-category rules as invoke (owner free).
- **404 "No scheduled result yet"** = the schedule hasn't completed a run since deploy. Retry after the next scheduled fire — do not fall back to POST.
- **Freshness**: `run_at` = when that run executed (lag = now − `run_at`); `as_of` = when its data was collected. Judge staleness from these two, never from when you made the request.
- **Failures are shared too**: if the latest scheduled round failed, what you read IS its `error` envelope (HTTP stays 200 — that is the platform convention). Judge failure solely by the presence of an `error` key.
- **There is nothing to pass**: `input_schema` on a scheduled agent describes the **owner's schedule parameters**, not a request body.
- Owner-only debug channel: `POST /repos/{repo_id}/fc/invoke` (the `/invoke` URL, not the `fc_invoke_url` field) runs one round now; non-owners get 403 with a hint to use the GET above. Run-now results do **not** enter the shared pool — consumers only ever see scheduled output.

## Notes

- Insufficient credits → HTTP 402.
- Your own `strategy_api_agent` entries: owner invokes are free; other users cannot see or invoke them at all.
- Run history for any agent you called: `GET /api/v1/public/agents/{repo_id}/runs` with the same Bearer token. Paginate with `?limit=100&offset=N` (newest first; `offset` = rows already fetched) or `?page=N&limit=100` — do not pass `page` and `offset>0` together (422).
- Fetching a run's report: prefer `GET /api/v1/agents/{repo_id}/report?run_id={run_id}` (backend proxy, works for any historical run). The `report_url` field in run history is a short-lived signed link — after it expires, use the proxy endpoint instead.
- For Task Agents (trading / deep-research / strategy / ...), use `finmeta-task-agent` (A2A), not this.
- All discovery and invoke calls target **cloud** (`https://fin-meta.net`).

## Timeouts

The invoke is a **synchronous LLM call — taking several minutes is normal**. A cut-off call almost always means some timeout layer fired, not that the agent is broken. Two layers can cut it, with different fixes:

1. **The shell/tool running curl (most common).** Many agent Bash tools default to ~120s and kill curl long before its own 600s limit. Symptom: the command is killed with no curl exit code and no JSON output. Fix: re-run with the tool timeout raised to ≥ 600s, or run the curl in the background and read the output file when it finishes.
2. **curl itself (`--max-time 600`).** curl exits with **code 28** — the agent genuinely ran past 10 minutes. The server may still finish that call (and bill it), so check with the user before blindly retrying — a retry may charge twice.

Step 1 (list agents) is a quick metadata call — a short timeout there is fine.
