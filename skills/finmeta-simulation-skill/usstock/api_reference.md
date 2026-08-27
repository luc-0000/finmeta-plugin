# US Stock Simulation API Reference

Base: `https://fin-meta.net/api/v1/usstock`

## Market Data (no auth)

| Action | HTTP | Path |
|--------|------|------|
| list_symbols | GET | /symbols |
| get_quotes | GET | /quotes?symbols= |
| kline | GET | /kline?symbol=&limit=&period= |
| rules | GET | /rules |

## Account / Trading (Bearer Token required)

| Action | HTTP | Path | Body |
|--------|------|------|------|
| create_account | POST | /simulation/accounts | {market: usstock, name?} — new id saved to config |
| delete_account | DELETE | /simulation/accounts/{id} | 204; explicit id required, config pin cleared if it pointed there |
| account (list) | GET | /accounts | — |
| account (detail) | GET | /accounts/{id} | — |
| positions | GET | /accounts/{id}/positions | — |
| buy | POST | /orders/buy | {symbol, quantity, account_id?} |
| sell | POST | /orders/sell | {symbol, quantity, account_id?} |

## Conditional Orders (Bearer Token required)

One engine for all four markets; US fills at the triggering 5Min bar's close, ticks every 30s during ET trading hours.

| Action | HTTP | Path | Body / Query |
|--------|------|------|------|
| conditional_buy / conditional_sell | POST | /simulation/usstock/accounts/{id}/orders/conditional | {stock_code, side, quantity (lot 1), trigger_dir: le\|ge, trigger_price, expiry: day\|gtc, client_order_id?, source?} |
| conditional_orders | GET | /simulation/accounts/{id}/orders/conditional | ?status=pending|filled|rejected|expired|cancelled&limit= |
| conditional_cancel | DELETE | /simulation/accounts/{id}/orders/conditional/{order_id} | 204; non-pending → 409 |

`expiry: "day"` voids at 16:00 ET same day (only accepted during trading hours). `client_order_id` is the idempotency key — retries return the original order. If the latest bar already crossed at placement (during trading hours), the order fires immediately (response may be `filled`/`rejected`).

## History (Bearer Token required)

| Action | HTTP | Path |
|--------|------|------|
| orders | GET | /accounts/{id}/orders?limit= |
| balance_log | GET | /accounts/{id}/balance-log?page=&limit= |

## Notes

- Symbol format: plain ticker, e.g. `AAPL`, `MSFT`, `GOOGL` (no exchange suffix).
- Quantity: integer shares (lot_size = 1). Negative quantity = USD amount, resolves to floor(USD/price) shares.
- Price source: `us_stock_symbols.price`, refreshed every 5 min via Alpaca IEX snapshots (15-min delayed).
- T+0 settlement, no daily price limit, zero commission.
- Symbol universe: S&P 500 only.
- Kline `period`: `5m` (native) · `1h` · `1d` (aggregated from 5m).
