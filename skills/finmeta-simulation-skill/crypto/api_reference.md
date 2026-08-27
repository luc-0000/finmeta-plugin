# Crypto Simulation API Reference

Base: `https://fin-meta.net/api/v1/crypto`

## Market Data (no auth)

| Action | HTTP | Path |
|--------|------|------|
| list_symbols | GET | /symbols |
| get_quotes | GET | /quotes?symbols= |
| kline | GET | /kline?symbol=&limit= |
| rules | GET | /rules |

## Account / Trading (Bearer Token required)

| Action | HTTP | Path | Body |
|--------|------|------|------|
| create_account | POST | /simulation/accounts | {market: crypto, name?} — new id saved to config |
| delete_account | DELETE | /simulation/accounts/{id} | 204; explicit id required, config pin cleared if it pointed there |
| account (list) | GET | /accounts | — |
| account (detail) | GET | /accounts/{id} | — |
| positions | GET | /accounts/{id}/positions | — |
| buy | POST | /orders/buy | {symbol, quantity, account_id?} |
| sell | POST | /orders/sell | {symbol, quantity, account_id?} |

## Conditional Orders (Bearer Token required)

One engine for all four markets; crypto fills at the triggering 1m bar's close, ticks every 30s around the clock.

| Action | HTTP | Path | Body / Query |
|--------|------|------|------|
| conditional_buy / conditional_sell | POST | /simulation/crypto/accounts/{id}/orders/conditional | {stock_code, side, quantity (lot 0.0001, e.g. 0.5), trigger_dir: le\|ge, trigger_price, expiry: day\|gtc, client_order_id?, source?} |
| conditional_orders | GET | /simulation/accounts/{id}/orders/conditional | ?status=pending|filled|rejected|expired|cancelled&limit= |
| conditional_cancel | DELETE | /simulation/accounts/{id}/orders/conditional/{order_id} | 204; non-pending → 409 |

Crypto trades 24/7 with no daily close, so `expiry: "day"` is auto-converted to `gtc` (response `data.expiry_coerced: "gtc"`). `client_order_id` is the idempotency key — retries return the original order. If the latest bar already crossed at placement, the order fires immediately (response may be `filled`/`rejected`).

## History (Bearer Token required)

| Action | HTTP | Path |
|--------|------|------|
| orders | GET | /accounts/{id}/orders?limit= |
| balance_log | GET | /accounts/{id}/balance-log?page=&limit= |
