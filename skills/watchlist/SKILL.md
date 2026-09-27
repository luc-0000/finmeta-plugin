---
name: watchlist
description: Manage the user's FinMeta watchlists (stock pools) — read, add, remove symbols per market (A-Share / US Stock / HK Stock / Crypto), for the default pool or any list by its id. Use when the user asks to add a stock to their watchlist, remove one, show their watchlist, references a watchlist by id or name, or when a trading agent needs the user's preferred stock universe before picking stocks. Soft guidance only — the pool never restricts trading.
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

## Multiple named lists — addressing by id

A user may own **several named lists per market**. Each has a numeric `id` and a
`name`; exactly one is the `is_default` list (marked with a dot in the web UI,
which also shows the id as `#N` next to every list name).

All list endpoints return the envelope `{"code": 0, "msg": "ok", "data": ...}` —
the payloads below are the `data` field.

```bash
# List all lists of a market: data = [{"id", "name", "is_default", "count"}, ...]
curl -H "Authorization: Bearer $FINMETA_ACCESS_TOKEN" \
  "https://fin-meta.net/api/v1/watchlist/ashare/lists"
```

The endpoints without an id (documented below) always operate on the **default**
list. To operate on a specific list instead, use its id:

```bash
# Read one list by id (same payload shape as the default-pool read)
curl -H "Authorization: Bearer $FINMETA_ACCESS_TOKEN" \
  "https://fin-meta.net/api/v1/watchlist/ashare/lists/14"

# Add / remove symbols in list 14 (same bodies as /add and /remove)
curl -X POST -H "Authorization: Bearer $FINMETA_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"symbols": ["600519.SH"]}' \
  "https://fin-meta.net/api/v1/watchlist/ashare/lists/14/add"
```

Also available by id: `PUT /watchlist/{market}/lists/{id}` (full replacement),
`POST /watchlist/{market}/lists` (create), `PATCH .../lists/{id}` (rename),
`DELETE .../lists/{id}` (delete; the default list cannot be deleted).

## Read the watchlist

Returns `[{"symbol", "name", "added_at"}, ...]` in the order symbols were added/saved (add
appends at the end). `added_at` is when the symbol was **first** added — later
add/remove/replace operations keep it. Empty array = no preference.

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

- **Which list to use**: if the user references a specific watchlist by id
  ("use watchlist 14") → use `/{market}/lists/14` endpoints directly. If they
  reference one by name → `GET /{market}/lists` and match `name`. Otherwise →
  the default list (the id-less endpoints below).
- Before picking stocks to analyze or trade, GET the watchlist of that market.
  Non-empty → prefer those symbols as the candidate universe.
  Empty → no preference, proceed as usual.
- The pool is advisory: it never blocks a trade outside the pool, and no
  endpoint enforces it. Do not treat it as a constraint.
- Watchlists are per-market and independent of simulation accounts.
