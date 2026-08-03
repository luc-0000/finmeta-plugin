# finmeta-plugin

A Claude Code **plugin** that bundles FinMeta client skills.

## What it does

| Skill | Purpose | Credits |
|-------|---------|---------|
| `finmeta-plugin` (root) | Credentials setup — SSOT `~/.finmeta/config.json` (token + account_id) | — |
| `market-data` | Read-only market data: symbols / quotes / kline (A-Share, US Stock, Crypto) | Free |
| `finmeta-simulation-skill` | Simulation trading: accounts / positions / orders (A-Share, US Stock, Crypto) | Free |
| `invoke-api-agent` | Call API agents (`type=api`) via synchronous HTTP POST | Per-call |
| `finmeta-task-agent` | Call Task agents (`type=agent`) via A2A — async K8s Job | Per-call |

What each skill lets you do:

- **market-data** — Look up tickers, get latest quotes, pull kline/candlestick bars for A-Share, US Stock, and Crypto. Read-only, free.
- **finmeta-simulation-skill** — Check account balance and positions, view order history, place buy/sell orders with simulated money across all three markets. Free.
- **invoke-api-agent** — Call a marketplace API agent (e.g. data / factor agent) and get a structured result back in one request. Charges credits per call.
- **finmeta-task-agent** — Run a Task agent (trading / deep-research / strategy / ...) via A2A. Async — runs as a K8s Job (1–10 min), returns a decision or report. Charges credits per call.

All skills read credentials from `~/.finmeta/config.json` (token + account_id), set up by the root skill — no `export` needed.

## Install

### From GitHub (end users)

```bash
/plugin marketplace add luc-0000/finmeta-plugin
/plugin install finmeta-plugin@finmeta-plugins
/reload-plugins
```

Updates: `/plugin marketplace update finmeta-plugins`.

### Local dev

```bash
claude --plugin-dir /Users/lu/development/fintools_all/skills/finmeta-plugin
```

Reload after edits: `/reload-plugins`.
