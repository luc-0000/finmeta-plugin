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

## Install in Hermes

This repo is a Claude-Code-format bundle (`.claude-plugin/` + `skills/`, no
`plugin.yaml`), so it is **not** a native Hermes plugin. Do **not** use
`hermes skills install luc-0000/finmeta-plugin/skills/<name>` — Hermes' GitHub
fetcher only downloads files referenced from `SKILL.md` that live under its
allowlisted support dirs (`references/`, `templates/`, `scripts/`, `assets/`,
`examples/`). This plugin's code lives in custom dirs (`ashare/`, `crypto/`,
`hkstock/`, `usstock/`), so that command would install a hollow `SKILL.md` with
no `api.py` and the skill would fail at runtime.

Clone the repo and **copy** (never symlink) each skill directory into Hermes'
discovery path:

```bash
git clone https://github.com/luc-0000/finmeta-plugin.git ~/.hermes/plugins/finmeta-plugin

# root credentials skill
mkdir -p ~/.hermes/skills/finmeta-plugin
cp ~/.hermes/plugins/finmeta-plugin/SKILL.md ~/.hermes/skills/finmeta-plugin/

# bundled skills
for s in ~/.hermes/plugins/finmeta-plugin/skills/*/; do
  cp -R "$s" ~/.hermes/skills/"$(basename "$s")"
done
```

- **Copy, don't symlink.** Keep installed skills independent of the clone.
- **To update**: `git -c http.version=HTTP/1.1 -C ~/.hermes/plugins/finmeta-plugin pull origin main`, then re-run the copy steps above (the copies don't follow the clone).
- If `git` fails with `Error in the HTTP2 framing layer`, retry with the `-c http.version=HTTP/1.1` flag.
