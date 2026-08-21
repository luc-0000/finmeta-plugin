---
name: market-data
description: Query FinMeta market data — symbols, quotes, kline for A-Share, US Stock, HK Stock, Crypto. Read-only, does not charge credits. Use when the user wants to look up tickers, latest prices, or candlestick/kline data without trading.
---

# FinMeta Market Data

Read-only market data (symbols / quotes / kline) for **A-Share**, **US Stock**, **HK Stock**, **Crypto**. **Does not charge credits.**

> **Token**: load from persistent storage first:
> ```bash
> export FINMETA_ACCESS_TOKEN=$(cat ~/.finmeta/access_token 2>/dev/null)
> ```
> If the file doesn't exist or is empty, stop and ask the user to run `finmeta-plugin` setup skill first.

Base URL: `https://fin-meta.net/api/v1`. `{market}` = `ashare` | `usstock` | `hkstock` | `crypto`.

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
```

## Kline (candles)

`period`: A-Share `5m|1h|1d`, US Stock `5m|1h|1d`, HK Stock `1m|5m|1h|1d`, Crypto `1m|5m|1h|1d`. `limit`: 1–500 (default 100).

> **US Stock**: native bar is 5m; `1h` and `1d` are server-aggregated from 5m. Use `period=1d` for daily candles — do NOT pull 5m and aggregate client-side.

```bash
# Crypto — BTC 1-hour candles, last 50
curl -H "Authorization: Bearer $FINMETA_ACCESS_TOKEN" \
  "https://fin-meta.net/api/v1/public/markets/crypto/kline?symbol=BTC/USDT&period=1h&limit=50"

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
```

## Notes

- A-Share symbols returns the full active list; use `keyword` + `limit` to filter. HK Stock symbols covers 142 competition symbols only — see `README.md`.
- Crypto kline data is 1-minute native; larger periods are server-aggregated.
- HK Stock kline updates every 5 minutes during HK trading hours (09:30–16:00 HKT); `1m` is native, `5m`/`1h`/`1d` are server-aggregated from 1m.
- No account needed; no credits charged.
- For trading / account / orders, use `finmeta-simulation-skill` instead.
