---
name: watchlist
description: Manage the user's FinMeta watchlist (stock pool) — read, add, remove symbols per market (A-Share / US Stock / HK Stock / Crypto). Use when the user asks to add a stock to their watchlist, remove one, show their watchlist, or when a trading agent needs the user's preferred stock universe before picking stocks. Soft guidance only — the pool never restricts trading.
---

# FinMeta Watchlist (Stock Pool)

Per-user, per-market watchlist. It is the user's **preferred stock universe** —
soft guidance for agents, never a trading restriction. An empty pool means
"no preference" (agent may consider the full market).

> **Token**: load from persistent storage first:
> ```bash
> export FINMETA_ACCESS_TOKEN=$(python3 -c "import json,os;print(json.load(open(os.path.expanduser('~/.finmeta/config.json'))).get('access_token',''))")
> ```
> If the file doesn't exist or is empty, stop and ask the user to run `finmeta-plugin` setup skill first.

Base URL: `https://fin-meta.net/api/v1`. `{market}` = `ashare` | `usstock` | `hkstock` | `crypto`.

## Read the watchlist

Returns `[{"symbol", "name", "added_at"}, ...]`, oldest first. Empty array = no preference.

```bash
curl -H "Authorization: Bearer $FINMETA_ACCESS_TOKEN" \
  "https://fin-meta.net/api/v1/watchlist/ashare"
```

## Add symbols (incremental — never clears the pool)

**Use this when the user says "add XXX to my watchlist".** Appends new symbols
at the end; symbols already in the pool are skipped. It does NOT replace the
existing pool.

```bash
# Add Kweichow Moutai + Wuliangye to the A-Share watchlist
curl -X POST -H "Authorization: Bearer $FINMETA_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"symbols": ["600519.SH", "000858.SZ"]}' \
  "https://fin-meta.net/api/v1/watchlist/ashare/add"

# Add Apple to the US Stock watchlist
curl -X POST -H "Authorization: Bearer $FINMETA_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"symbols": ["AAPL"]}' \
  "https://fin-meta.net/api/v1/watchlist/usstock/add"
```

Symbol format per market: A-Share `600519.SH` / `000858.SZ`, US `AAPL`,
HK `00700.HK`, Crypto `BTC/USDT`. If unsure of the code, look it up with the
`market-data` skill's symbols endpoint first.

## Remove symbols (incremental)

Removes the given symbols; unknown ones are ignored, the rest keep their order.

```bash
curl -X POST -H "Authorization: Bearer $FINMETA_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"symbols": ["600519.SH"]}' \
  "https://fin-meta.net/api/v1/watchlist/ashare/remove"
```

## Replace the whole watchlist (bulk edit)

**Full replacement — only for "set my watchlist to exactly these".** Requires
sending the complete symbol list; anything omitted is dropped.

```bash
curl -X PUT -H "Authorization: Bearer $FINMETA_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"symbols": ["600519.SH", "000858.SZ"]}' \
  "https://fin-meta.net/api/v1/watchlist/ashare"
```

For adding or removing, prefer the `/add` and `/remove` endpoints — a bare PUT
with only the new symbols would wipe the user's existing pool.

## How agents should use the pool

- Before picking stocks to analyze or trade, GET the watchlist of that market.
  Non-empty → prefer those symbols as the candidate universe.
  Empty → no preference, proceed as usual.
- The pool is advisory: it never blocks a trade outside the pool, and no
  endpoint enforces it. Do not treat it as a constraint.
- Watchlists are per-market and independent of simulation accounts.
