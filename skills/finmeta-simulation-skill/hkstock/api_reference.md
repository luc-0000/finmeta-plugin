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
| create_account | POST | /simulation/accounts | {market: hkstock, name?} — new id saved to config |
| delete_account | DELETE | /simulation/accounts/{id} | 204; explicit id required, config pin cleared if it pointed there |
| account (list) | GET | /accounts | — |
| account (detail) | GET | /accounts/{id} | — |
| positions | GET | /accounts/{id}/positions | — |
| buy | POST | /orders/buy | {symbol, quantity, account_id?} |
| sell | POST | /orders/sell | {symbol, quantity, account_id?} |

## Conditional Orders (Bearer Token required)

One engine for all four markets; HK fills at the triggering 1Min bar's close, ticks every 30s during HKT trading hours.

| Action | HTTP | Path | Body / Query |
|--------|------|------|------|
| conditional_buy / conditional_sell | POST | /simulation/hkstock/accounts/{id}/orders/conditional | {stock_code, side, quantity (board lot 10), trigger_dir: le\|ge, trigger_price, expiry: day\|gtc, client_order_id?, source?} |
| conditional_orders | GET | /simulation/accounts/{id}/orders/conditional | ?status=pending|filled|rejected|expired|cancelled&limit= |
| conditional_cancel | DELETE | /simulation/accounts/{id}/orders/conditional/{order_id} | 204; non-pending → 409 |

`expiry: "day"` voids at 16:00 HKT same day (only accepted during trading hours). `client_order_id` is the idempotency key — retries return the original order. If the latest bar already crossed at placement (during trading hours), the order fires immediately (response may be `filled`/`rejected`).

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
- Account auto-creates on first trade if no account_id passed; explicit `--action create_account` also available.
