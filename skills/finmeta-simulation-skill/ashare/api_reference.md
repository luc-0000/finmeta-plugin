# A-Share Simulation API Reference (v3 — per-account routing)

Base: `https://fin-meta.net/api/v1/ashare`

## Market Data (no auth)

| Action | HTTP | Path |
|--------|------|------|
| list_stocks | GET | /stocks |
| get_quote | GET | /stocks/quotes?symbols= |
| kline | GET | /stocks/{code}/kline?period=1d&limit=60 |
| rules | GET | /rules |

## Account (Bearer Token + Account ID required)

| Action | HTTP | Path |
|--------|------|------|
| account | GET | /accounts/{account_id} |
| positions | GET | /accounts/{account_id}/positions |
| list_my_accounts | GET | /accounts?lightweight=true |

## Trading (Bearer Token + Account ID required)

| Action | HTTP | Path | Body |
|--------|------|------|------|
| buy | POST | /accounts/{account_id}/orders/buy | {stock_code, quantity} |
| sell | POST | /accounts/{account_id}/orders/sell | {stock_code, quantity} |

## History (Bearer Token + Account ID required)

| Action | HTTP | Path |
|--------|------|------|
| orders | GET | /accounts/{account_id}/orders |
| buy_orders | GET | /accounts/{account_id}/orders?side=buy |
| sell_orders | GET | /accounts/{account_id}/orders?side=sell |
| balance_log | GET | /accounts/{account_id}/balance-log |
| fee_log | GET | /accounts/{account_id}/balance-log |
