# finmeta-plugin

A Claude Code **plugin** that bundles FinMeta client skills.

## What it does

| Skill | Purpose | Credits |
|-------|---------|---------|
| `finmeta-plugin` (root) | Token setup — SSOT for `FINMETA_ACCESS_TOKEN` | — |
| `market-data` | Read-only market data: symbols / quotes / kline (A-Share, US Stock, Crypto) | Free |
| `finmeta-simulation-skill` | Simulation trading: accounts / positions / orders (A-Share, US Stock, Crypto) | Free |
| `invoke-api-agent` | Call API agents (`type=api`) via synchronous HTTP POST | Per-call |

What each skill lets you do:

- **market-data** — Look up tickers, get latest quotes, pull kline/candlestick bars for A-Share, US Stock, and Crypto. Read-only, free.
- **finmeta-simulation-skill** — Check account balance and positions, view order history, place buy/sell orders with simulated money across all three markets. Free.
- **invoke-api-agent** — Call a marketplace API agent (e.g. data / factor agent) and get a structured result back in one request. Charges credits per call.

All skills share one `FINMETA_ACCESS_TOKEN`, set up by the root skill.

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
