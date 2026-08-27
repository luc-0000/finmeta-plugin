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

- Symbol format: plain ticker, e.g. `AAPL`, `MSFT`, `GOOGL` (no exchange suffix).
- Quantity: integer shares (lot_size = 1). Negative quantity = USD amount, resolves to floor(USD/price) shares.
- Price source: `us_stock_symbols.price`, refreshed every 5 min via Alpaca IEX snapshots (15-min delayed).
- T+0 settlement, no daily price limit, zero commission.
- Symbol universe: S&P 500 only.
- Kline `period`: `5m` (native) · `1h` · `1d` (aggregated from 5m).
