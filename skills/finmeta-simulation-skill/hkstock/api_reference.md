# HK Stock Simulation API Reference

Base: `https://fin-meta.net/api/v1/hkstock`

## Market Data (no auth)

| Action | HTTP | Path |
|--------|------|------|
| list_stocks | GET | /stocks |
| get_quotes | GET | /quotes?symbols= |
| kline | GET | /kline?symbol=&limit=&period= |
| rules | GET | /rules |

## Account / Trading (Bearer Token required)

| Action | HTTP | Path | Body |
|--------|------|------|------|
| account (list) | GET | /accounts | — |
| account (detail) | GET | /accounts/{id} | — |
| positions | GET | /accounts/{id}/positions | — |
| buy | POST | /orders/buy | {symbol, quantity, account_id?} |
| sell | POST | /orders/sell | {symbol, quantity, account_id?} |

## History (Bearer Token required)

| Action | HTTP | Path |
|--------|------|------|
| orders | GET | /accounts/{id}/orders?limit= |
| balance_log | GET | /accounts/{id}/balance-log?page=&limit= |

## Notes

- Symbol format: 5-digit code with `.HK` suffix, e.g. `00700.HK`, `09988.HK` (keep leading zeros).
- Kline `period`: `1m` (native) · `5m` · `1h` · `1d` (aggregated from 1m). Refreshed every 5 min during HK trading hours (09:30–16:00 HKT).
- Lot size 10 shares; T+0 settlement; no daily price limit.
- Commission 0.1% (min HK$5); stamp tax 0.1% (sell only).
- Symbol universe: 142 competition symbols (HK.AI list), not the full HK market.
- Account auto-creates on first trade if no account_id passed.
