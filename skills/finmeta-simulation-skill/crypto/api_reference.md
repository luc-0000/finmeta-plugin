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
| account | GET | /account?account_id= | — |
| positions | GET | /positions?account_id= | — |
| buy | POST | /orders/buy | {symbol, quantity, account_id?} |
| sell | POST | /orders/sell | {symbol, quantity, account_id?} |

## History (Bearer Token required)

| Action | HTTP | Path |
|--------|------|------|
| orders | GET | /orders?limit=&account_id= |
| balance_log | GET | /balance-log?page=&limit=&account_id= |
