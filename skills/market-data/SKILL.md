---
name: market-data
description: Query FinMeta market data — symbols, quotes, kline for A-Share, US Stock, HK Stock, Crypto, ETF. Read-only, does not charge credits. Use when the user wants to look up tickers, latest prices, or candlestick/kline data without trading.
---

# FinMeta Market Data

Read-only market data (symbols / quotes / kline) for **A-Share**, **US Stock**, **HK Stock**, **Crypto**, **ETF**. **Does not charge credits.**

> **Token**: load from persistent storage first:
> ```bash
> export FINMETA_ACCESS_TOKEN=$(python3 -c "import json,os;print(json.load(open(os.path.expanduser('~/.finmeta/config.json'))).get('access_token',''))")
> ```
> If the file doesn't exist or is empty, stop and ask the user to run `finmeta-plugin` setup skill first.

Base URL: `https://fin-meta.net/api/v1`. `{market}` = `ashare` | `usstock` | `hkstock` | `crypto` | `etf`.

## Symbols (list / search)

Returns up to `limit` stocks (default 100, max 10000); supports optional `keyword` filter.

```bash
# A-Share
curl -H "Authorization: Bearer $FINMETA_ACCESS_TOKEN" \
  "https://fin-meta.net/api/v1/public/markets/ashare/symbols"

# US Stock
curl -H "Authorization: Bearer $FINMETA_ACCESS_TOKEN" \
  "https://fin-meta.net/api/v1/public/markets/usstock/symbols"

# HK Stock
curl -H "Authorization: Bearer $FINMETA_ACCESS_TOKEN" \
  "https://fin-meta.net/api/v1/public/markets/hkstock/symbols"

# Crypto
curl -H "Authorization: Bearer $FINMETA_ACCESS_TOKEN" \
  "https://fin-meta.net/api/v1/public/markets/crypto/symbols"
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

# Crypto — Bitcoin + Ethereum
curl -H "Authorization: Bearer $FINMETA_ACCESS_TOKEN" \
  "https://fin-meta.net/api/v1/public/markets/crypto/quotes?symbols=BTC/USDT,ETH/USDT"

# ETF — 有色金属ETF南方 + 沪深300ETF
curl -H "Authorization: Bearer $FINMETA_ACCESS_TOKEN" \
  "https://fin-meta.net/api/v1/public/markets/etf/quotes?symbols=512400.SH,510300.SH"
```

## Kline (candles)

`period`: A-Share `1m|5m|1h|1d`, US Stock `5m|1h|1d`, HK Stock `1m|5m|1h|1d`, Crypto `1m|5m|1h|1d`, ETF `1m|5m|1h|1d`. `limit`: 1–500 (default 100).

> **US Stock**: native bar is 5m; `1h` and `1d` are server-aggregated from 5m. Use `period=1d` for daily candles — do NOT pull 5m and aggregate client-side.
> **A-Share**: native data is 1-minute snapshots; `5m`/`1h`/`1d` are server-aggregated from 1m snapshots (~30 days of history). Use `period=1d` for daily candles.
> **ETF**: same as A-Share — native 1-minute snapshots, larger periods server-aggregated, ~30 days of history (coverage starts 2026-09-22).

```bash
# Crypto — BTC 1-hour candles, last 50
curl -H "Authorization: Bearer $FINMETA_ACCESS_TOKEN" \
  "https://fin-meta.net/api/v1/public/markets/crypto/kline?symbol=BTC/USDT&period=1h&limit=50"

# A-Share — Moutai 1-minute candles, last 30 (during/after trading hours)
curl -H "Authorization: Bearer $FINMETA_ACCESS_TOKEN" \
  "https://fin-meta.net/api/v1/public/markets/ashare/kline?symbol=600519.SH&period=1m&limit=30"

# A-Share — Moutai daily, last 30
curl -H "Authorization: Bearer $FINMETA_ACCESS_TOKEN" \
  "https://fin-meta.net/api/v1/public/markets/ashare/kline?symbol=600519.SH&period=1d&limit=30"

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
```

## Notes

- A-Share symbols returns the full active list; use `keyword` + `limit` to filter. HK Stock symbols covers 142 competition symbols only — see `README.md`.
- A-Share kline: the 1-minute snapshot table is the **sole source** — `1m` derives per-minute bars from snapshots, `5m`/`1h` are bucketed from 1m, `1d` is day-level (open = first snapshot's open; volume/amount = final cumulative). Coverage starts 2026-08-29 with ~30 days retention; earlier ranges return empty. Per-minute volume/amount are exact; high/low are exact only when the minute sets a new day extreme, otherwise bounded by that minute's open/close.
- ETF kline: identical snapshot semantics to A-Share (above); ETF symbols list covers ~1674 funds, updates every minute during CN trading hours, coverage starts 2026-09-22 with ~30 days retention.
- Crypto kline data is 1-minute native; larger periods are server-aggregated.
- HK Stock kline updates every 5 minutes during HK trading hours (09:30–16:00 HKT); `1m` is native, `5m`/`1h`/`1d` are server-aggregated from 1m.
- No account needed; no credits charged.
- For trading / account / orders, use `finmeta-simulation-skill` instead (ETF trading not yet supported).
