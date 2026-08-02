---
name: market-data
description: Query FinMeta market data — symbols, quotes, kline for A-Share, US Stock, Crypto. Read-only, does not charge credits. Use when the user wants to look up tickers, latest prices, or candlestick/kline data without trading.
---

# FinMeta Market Data

Read-only market data (symbols / quotes / kline) for **A-Share**, **US Stock**, **Crypto**. **Does not charge credits.**

> **Token**: load from persistent storage first:
> ```bash
> export FINMETA_ACCESS_TOKEN=$(cat ~/.finmeta/access_token 2>/dev/null)
> ```
> If the file doesn't exist or is empty, stop and ask the user to run `finmeta-plugin` setup skill first.

Base URL: `https://fin-meta.net/api/v1`. `{market}` = `ashare` | `usstock` | `crypto`.

## Symbols (list / search)

Returns all stocks; supports optional `keyword` filter and `limit` (max 10000).

```bash
# A-Share
curl -H "Authorization: Bearer $FINMETA_ACCESS_TOKEN" \
  "https://fin-meta.net/api/v1/public/markets/ashare/symbols"

# US Stock
curl -H "Authorization: Bearer $FINMETA_ACCESS_TOKEN" \
  "https://fin-meta.net/api/v1/public/markets/usstock/symbols"

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

# Crypto — Bitcoin + Ethereum
curl -H "Authorization: Bearer $FINMETA_ACCESS_TOKEN" \
  "https://fin-meta.net/api/v1/public/markets/crypto/quotes?symbols=BTC/USDT,ETH/USDT"
```

## Kline (candles)

`period`: A-Share `1d|5m`, US Stock `5Min`, Crypto `1m|5m|15m|1h|4h|1d`. `limit`: 1–500 (default 100).

```bash
# Crypto — BTC 1-hour candles, last 50
curl -H "Authorization: Bearer $FINMETA_ACCESS_TOKEN" \
  "https://fin-meta.net/api/v1/public/markets/crypto/kline?symbol=BTC/USDT&period=1h&limit=50"

# A-Share — Moutai daily, last 30
curl -H "Authorization: Bearer $FINMETA_ACCESS_TOKEN" \
  "https://fin-meta.net/api/v1/public/markets/ashare/kline?symbol=600519.SH&period=1d&limit=30"

# US Stock — Apple 5-min candles, last 30
curl -H "Authorization: Bearer $FINMETA_ACCESS_TOKEN" \
  "https://fin-meta.net/api/v1/public/markets/usstock/kline?symbol=AAPL&period=5Min&limit=30"
```

## Notes

- A-Share symbols returns the full active list; use `keyword` + `limit` to filter.
- Crypto kline data is 1-minute native; larger periods are server-aggregated.
- No account needed; no credits charged.
- For trading / account / orders, use `finmeta-simulation-skill` instead.
