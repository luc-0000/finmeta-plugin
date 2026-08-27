# A-Share Simulation API Reference (v3 — per-account routing)

Base: `https://fin-meta.net/api/v1/ashare`

## Market Data (no auth)

| Action | HTTP | Path |
|--------|------|------|
| list_stocks | GET | /stocks |
| get_quote | GET | /stocks/quotes?symbols= |
| kline | GET | /stocks/{code}/kline?period=1d&limit=60 |
| rules | GET | /rules |

## Account (Bearer Token required)

account_id is auto-resolved (config id ownership-checked → personal account →
auto-create on trade). Pass one explicitly only to override.
No account yet? `--action create_account` creates one and saves it to config.

| Action | HTTP | Path |
|--------|------|------|
| account | GET | /accounts/{account_id} |
| create_account | POST | /simulation/accounts body {market: ashare, name?} — new id saved to config |
| delete_account | DELETE | /simulation/accounts/{id} — 204; explicit id required, config pin cleared if it pointed there |
| positions | GET | /accounts/{account_id}/positions |
| list_my_accounts | GET | /accounts?lightweight=true |

## Trading (Bearer Token required)

| Action | HTTP | Path | Body |
|--------|------|------|------|
| buy | POST | /accounts/{account_id}/orders/buy | {stock_code, quantity} |
| sell | POST | /accounts/{account_id}/orders/sell | {stock_code, quantity} |

## Conditional Orders (Bearer Token required)

Trigger engine reads 5-minute bars from the platform database (no external quote API) and
ticks every 30s during auction hours. Fills happen at the triggering bar's closing price,
so a cross may take up to ~5 minutes to fire. If the latest bar has already crossed at
placement time, the order fires immediately — the response status may be `filled`/`rejected` right away.

| Action | HTTP | Path | Body / Query |
|--------|------|------|--------------|
| conditional_buy / conditional_sell | POST | /simulation/ashare/accounts/{account_id}/orders/conditional | {stock_code, side: buy\|sell, quantity, trigger_dir: le\|ge, trigger_price, expiry: day\|gtc, client_order_id?} |
| conditional_orders | GET | /simulation/accounts/{account_id}/orders/conditional | ?status=pending\|filled\|rejected\|expired\|cancelled&limit= |
| conditional_cancel | DELETE | /simulation/accounts/{account_id}/orders/conditional/{order_id} | 204 ok; 409 non-pending; 404 missing |

- `trigger_dir`: `le` = fire when the bar's low ≤ trigger_price; `ge` = fire when the bar's high ≥ trigger_price (fill = bar close)
- `expiry`: `day` (void after 15:00 same day, rejected off-hours) | `gtc` (good till cancelled)
- `client_order_id`: idempotency key — same key returns the original order, never duplicates (recommended for agents)

## History (Bearer Token required)

| Action | HTTP | Path |
|--------|------|------|
| orders | GET | /accounts/{account_id}/orders |
| buy_orders | GET | /accounts/{account_id}/orders?side=buy |
| sell_orders | GET | /accounts/{account_id}/orders?side=sell |
| balance_log | GET | /accounts/{account_id}/balance-log |
| fee_log | GET | /accounts/{account_id}/balance-log |
