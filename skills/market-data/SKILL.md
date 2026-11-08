---
name: market-data
description: Query FinMeta market data — symbols, quotes, kline for A-Share, US Stock, HK Stock, Crypto, ETF, Convertible Bonds (可转债), plus the A-Share call-auction process feed (per-second indicative price/volume). Read-only, does not charge credits. Use when the user wants to look up tickers, latest prices, candlestick/kline data, or auction-phase price discovery without trading.
---

# FinMeta Market Data

Read-only market data (symbols / quotes / kline) for **A-Share**, **US Stock**, **HK Stock**, **Crypto**, **ETF**, **Convertible Bonds (可转债)**, plus the **A-Share call-auction process feed** (集合竞价过程，per-second indicative price/volume). **Does not charge credits. Requires a FINMETA_ACCESS_TOKEN (register a FinTools account → profile page).**

> **Token**: load from persistent storage first:
> ```bash
> export FINMETA_ACCESS_TOKEN=$(python3 -c "import json,os;print(json.load(open(os.path.expanduser('~/.finmeta/config.json'))).get('access_token',''))")
> ```
> If the file doesn't exist or is empty, stop and give the user the setup steps: get a token
> at https://fin-meta.net/profile → **Access Token**, save it into `~/.finmeta/config.json`
> — full steps in the plugin root `SKILL.md` (**Setup** section).

Base URL: `https://fin-meta.net/api/v1`. `{market}` = `ashare` | `usstock` | `hkstock` | `crypto` | `etf` | `cb`.

## Symbols (list / search)

Optional `keyword` filter. `limit` = top-N (max 10000). Omitting `limit` returns
the FULL list on backend ≥ 2026-10-08; older backend silently truncated to a
top-100 by volume — for universe/membership use, always pass an explicit large
`limit` (e.g. `limit=10000`).

```bash
# A-Share (~5700 active)
curl -H "Authorization: Bearer $FINMETA_ACCESS_TOKEN" \
  "https://fin-meta.net/api/v1/public/markets/ashare/symbols?limit=10000"

# US Stock
curl -H "Authorization: Bearer $FINMETA_ACCESS_TOKEN" \
  "https://fin-meta.net/api/v1/public/markets/usstock/symbols?limit=10000"

# HK Stock
curl -H "Authorization: Bearer $FINMETA_ACCESS_TOKEN" \
  "https://fin-meta.net/api/v1/public/markets/hkstock/symbols?limit=10000"

# Crypto (spot, ~500 pairs)
curl -H "Authorization: Bearer $FINMETA_ACCESS_TOKEN" \
  "https://fin-meta.net/api/v1/public/markets/crypto/symbols?limit=10000"

# Crypto perpetuals (~730 USDT-M contracts, "BTC/USDT:USDT" format)
curl -H "Authorization: Bearer $FINMETA_ACCESS_TOKEN" \
  "https://fin-meta.net/api/v1/public/markets/crypto/symbols?type=perp&limit=1000"

# Convertible Bonds (~320 SH/SZ, codes like 110081.SH)
curl -H "Authorization: Bearer $FINMETA_ACCESS_TOKEN" \
  "https://fin-meta.net/api/v1/public/markets/cb/symbols?limit=1000"
```

## Quotes (latest price)

```bash
# A-Share — Kweichow Moutai + Wuliangye
curl -H "Authorization: Bearer $FINMETA_ACCESS_TOKEN" \
  "https://fin-meta.net/api/v1/public/markets/ashare/quotes?symbols=600519.SH,000858.SZ"

# US Stock — Apple
curl -H "Authorization: Bearer $FINMETA_ACCESS_TOKEN" \
  "https://fin-meta.net/api/v1/public/markets/usstock/quotes?symbols=AAPL"

# HK Stock — Tencent + HSBC
curl -H "Authorization: Bearer $FINMETA_ACCESS_TOKEN" \
  "https://fin-meta.net/api/v1/public/markets/hkstock/quotes?symbols=00700.HK,00005.HK"

# Crypto — Bitcoin + Ethereum (perp symbols "BTC/USDT:USDT" also supported;
# perp quotes carry funding_rate — the latest settled 8h rate; spot returns null)
curl -H "Authorization: Bearer $FINMETA_ACCESS_TOKEN" \
  "https://fin-meta.net/api/v1/public/markets/crypto/quotes?symbols=BTC/USDT,ETH/USDT"

# ETF — 有色金属ETF南方 + 沪深300ETF
curl -H "Authorization: Bearer $FINMETA_ACCESS_TOKEN" \
  "https://fin-meta.net/api/v1/public/markets/etf/quotes?symbols=512400.SH,510300.SH"

# Convertible Bonds — 闻泰转债 + 强力转债
curl -H "Authorization: Bearer $FINMETA_ACCESS_TOKEN" \
  "https://fin-meta.net/api/v1/public/markets/cb/quotes?symbols=110081.SH,123076.SZ"
```

## Kline (candles)

`period`: A-Share `1m|5m|1h|1d`, US Stock `5m|1h|1d`, HK Stock `1m|5m|1h|1d`, Crypto `1m|5m|1h|1d`, ETF `1m|5m|1h|1d`, Convertible Bonds `1m|5m|1h|1d`. `limit`: 1–500 (default 100).

> **US Stock**: native bar is 5m; `1h` and `1d` are server-aggregated from 5m. Use `period=1d` for daily candles — do NOT pull 5m and aggregate client-side.
> **A-Share**: `1m` native snapshots; `5m`/`1h` server-aggregated from 1m (~30 days of history); `1d` reads the permanent daily table — **~2 years of history** (backfilled from 2024-11-06). Use `period=1d` for daily candles.
> **ETF**: same as A-Share — intraday from 1-minute snapshots (~30 days, coverage starts 2026-09-22); `1d` reads the daily table, ~2 years (from 2024-11-06).
> **Convertible Bonds**: same as A-Share — intraday from 1-minute snapshots (~30 days, coverage starts 2026-10-14); `1d` reads the daily table, ~2 years (from 2024-11-06).

```bash
# Crypto — BTC 1-hour candles, last 50
curl -H "Authorization: Bearer $FINMETA_ACCESS_TOKEN" \
  "https://fin-meta.net/api/v1/public/markets/crypto/kline?symbol=BTC/USDT&period=1h&limit=50"

# A-Share — Moutai 1-minute candles, last 30 (during/after trading hours)
curl -H "Authorization: Bearer $FINMETA_ACCESS_TOKEN" \
  "https://fin-meta.net/api/v1/public/markets/ashare/kline?symbol=600519.SH&period=1m&limit=30"

# A-Share — Moutai daily, last 500 (≈ 2 full years)
curl -H "Authorization: Bearer $FINMETA_ACCESS_TOKEN" \
  "https://fin-meta.net/api/v1/public/markets/ashare/kline?symbol=600519.SH&period=1d&limit=500"

# US Stock — Apple daily candles, last 5 trading days
curl -H "Authorization: Bearer $FINMETA_ACCESS_TOKEN" \
  "https://fin-meta.net/api/v1/public/markets/usstock/kline?symbol=AAPL&period=1d&limit=5"

# US Stock — Apple 5-min candles, last 30
curl -H "Authorization: Bearer $FINMETA_ACCESS_TOKEN" \
  "https://fin-meta.net/api/v1/public/markets/usstock/kline?symbol=AAPL&period=5m&limit=30"

# HK Stock — Tencent daily candles, last 30
curl -H "Authorization: Bearer $FINMETA_ACCESS_TOKEN" \
  "https://fin-meta.net/api/v1/public/markets/hkstock/kline?symbol=00700.HK&period=1d&limit=30"

# ETF — 有色金属ETF南方 5-min candles, last 30 (server-aggregated from 1m)
curl -H "Authorization: Bearer $FINMETA_ACCESS_TOKEN" \
  "https://fin-meta.net/api/v1/public/markets/etf/kline?symbol=512400.SH&period=5m&limit=30"

# Convertible Bonds — 闻泰转债 5-min candles, last 30 (server-aggregated from 1m)
curl -H "Authorization: Bearer $FINMETA_ACCESS_TOKEN" \
  "https://fin-meta.net/api/v1/public/markets/cb/kline?symbol=110081.SH&period=5m&limit=30"
```

## A-Share Call Auction process (集合竞价过程, ashare only)

Per-second indicative points from the two A-Share call-auction sessions: **open auction 09:15–09:25** and **close auction 14:57–15:00**. During these windows the exchange publishes an indicative match price/volume that evolves as orders arrive and cancel — the raw material for bull/bear-trap (诱多/诱空) analysis.

```bash
# Ping An Bank — latest day with data (omit date)
curl -H "Authorization: Bearer $FINMETA_ACCESS_TOKEN" \
  "https://fin-meta.net/api/v1/public/markets/ashare/auction?symbol=000001.SZ"

# Explicit trading day
curl -H "Authorization: Bearer $FINMETA_ACCESS_TOKEN" \
  "https://fin-meta.net/api/v1/public/markets/ashare/auction?symbol=000001.SZ&date=2026-10-27"
```

Response: list of points, ascending in time; `point_index` is a continuous ordinal across the whole day (open segment starts at 0, close segment continues).

| Field | Meaning |
|-------|---------|
| `time` | Point timestamp `YYYY-MM-DD HH:MM:SS` (3–9 s cadence, event-driven — denser = more order activity) |
| `price` | Indicative matched price (虚拟匹配价) |
| `matched_volume` | Cumulative indicative matched volume, in 手. Converges to the official match volume; the last point may sit slightly below it (orders still arriving in the final seconds) |
| `unmatched_volume` | Residual size of the un-matched side |
| `unmatched_direction` | `+1` = buy side un-matched, `-1` = sell side un-matched |
| `point_index` | Day-global point ordinal |

- The official match result (09:26 / 15:00 bar) is **not** part of this feed — it lands in quotes/kline like any other bar.
- Coverage starts **2026-09-01**; collected once daily after close. A known symbol with no auction data that day (e.g. suspended) returns an empty list; an unknown symbol returns **404** — use symbols from the `ashare/symbols` endpoint.
- Typical day: open segment ~40–65 points per stock, close segment ~19; point counts vary with activity.

## Notes

- A-Share symbols returns the full active list; use `keyword` to filter. HK Stock symbols covers 142 competition symbols only — see `README.md`.
- A-Share kline: `1m`/`5m`/`1h` derive from the 1-minute snapshot table (coverage starts 2026-08-29, ~30 days retention; earlier ranges return empty); `1d` reads the permanent daily table — **~2 years of history** (backfilled to 2024-11-06), one bar per trading day, volume in 股, and the latest day is live-filled from snapshots until it lands in the table (~15:35). Per-minute volume/amount are exact; high/low are exact only when the minute sets a new day extreme, otherwise bounded by that minute's open/close.
- ETF kline: identical snapshot semantics to A-Share (above, including the two-year `1d` daily table); ETF symbols list covers ~1674 funds, updates every minute during CN trading hours; intraday coverage starts 2026-09-22 with ~30 days retention.
- Convertible Bond (cb) kline: identical snapshot semantics to A-Share (above, including the two-year `1d` daily table); covers ~320 SH/SZ convertible bonds (SH `11xxxx` / SZ `12xxxx`, e.g. `110081.SH`), updates every minute during CN trading hours; intraday coverage starts 2026-10-14 with ~30 days retention. `volume` unit is 张 (bonds, face value 100 CNY each), same unit for `1d`; real-world CBs trade T+0 with ±20% limits, but market data here is read-only (no simulation trading yet).
- Crypto kline data is 1-minute native; larger periods are server-aggregated. The kline endpoint works for both spot (`BTC/USDT`) and perp (`BTC/USDT:USDT`) symbols; rolling ~60 days of 1m history.
- Crypto perp symbols (`?type=perp`) are tradable in the simulation via the `finmeta-simulation-skill` Crypto Perp section (`contract_open` / `contract_close`).
- HK Stock kline updates every 5 minutes during HK trading hours (09:30–16:00 HKT); `1m` is native, `5m`/`1h`/`1d` are server-aggregated from 1m.
- All calls require a `FINMETA_ACCESS_TOKEN` (account registration is required to obtain one); no credits are charged for market data.
- For trading / account / orders, use `finmeta-simulation-skill` instead (ETF trading not yet supported).
