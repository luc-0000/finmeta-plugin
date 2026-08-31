# A-Share Simulation API Reference (v3 — per-account routing)

Base: `https://fin-meta.net/api/v1/ashare`

## Response Envelope & Field Names (verified 2026-08-29)

Every CLI action prints one JSON blob — the real payload is one level deeper than you'd guess:

```json
{"success": true, "data": {"code": 0, "msg": "ok", "data": <payload>}}
```

**Trade responses have NO `status` field.** Success = `success: true` plus
`order_id` / `price` / `fee` in the payload. Failure = `success: false` with a
structured `error`, e.g. the T+1 gate:
`Insufficient sellable position (T+1): 000001.SZ 0.000 sellable, 100 requested`.

Actual payload field names (these are the contract — don't infer from other APIs):

| Action | Payload fields |
|---|---|
| account | `id`, `name`, `market`, `current_balance`, `total_market_value`, `total_assets`, `total_profit`, `total_profit_pct`, `initial_balance`, `settlement_date` |
| buy / sell | `order_id`, `stock_code`, `price`, `quantity`, `total`, `fee`, `trade_time` — no `status` |
| get_quote | `stock_code`, `stock_name`, `latest_price`, `change_pct`, `volume`, `price_source` (`kline_1m` = 1m snapshot primary), `kline_date` |
| orders / buy_orders / sell_orders | `id`, `side`, `price`, `quantity`, `fee`, `source`, `trade_time`, `error` — no `status`/`created_at`; `error: null` means filled |
| positions | `holding_quantity` (not `quantity`), `available_quantity` (0 while T+1-locked), `avg_cost`, `latest_price`, `profit_pct`, `profit_amt`, `last_buy_time` |
| conditional orders | `id`, `side`, `trigger_price`, `client_order_id`, `status` (`pending`/`filled`/`rejected`/`expired`/`cancelled`), `created_at` |

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

Trigger engine reads 1-minute snapshots from the platform database (sole data source for
A-Share; no external quote API) and ticks every 30s around the clock
(per-market session gate skips off-hours). Fills happen at the triggering bar's closing price,
so a cross typically fires within ~1 minute. If the latest bar has already crossed at
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
