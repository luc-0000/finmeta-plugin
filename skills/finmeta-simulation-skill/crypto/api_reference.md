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

## Perp Contract (Bearer Token required)

Wallet `market=crypto_contract` — a **separate USDT wallet** from spot crypto (config key
`accounts.crypto_contract`; auto-created on first trade). Account / positions / orders /
balance-log reuse the unified routes below — they return contract data when the account is
a perp wallet; only open/close are contract-specific.

| Action | HTTP | Path | Body / Query |
|--------|------|------|------|
| contract_rules | GET | /simulation/rules/crypto_contract | — (max leverage, MMR, fees, min notional) |
| contract_open | POST | /simulation/crypto_contract/accounts/{id}/orders/open | {symbol: "BTC/USDT:USDT", side: long\|short, leverage: 1–20, margin_usdt \| quantity (base size; margin_usdt wins if both)} |
| contract_close | POST | /simulation/crypto_contract/accounts/{id}/orders/close | {position_id, quantity?} — quantity omitted = full close; larger-than-held clamps to full close |
| positions | GET | /accounts/{id}/positions | — contract wallet returns mark price, unrealized P/L, ROE, est. liquidation price, cumulative funding, margin, leverage |
| account | GET | /accounts/{id} | — contract summary: balance, margin in use, total assets incl. position equity |
| orders | GET | /accounts/{id}/orders?limit= | — open / close / liquidation records with realized P/L (net of fee) |

Rule recap: isolated margin per position (max loss = margin); taker fee 0.05% of notional;
liquidation when `margin + funding + uPnL ≤ 0.5% × notional` (liquidation fee 0.5% of
notional, payout floored at 0); Binance funding events (8h) settle against the wallet
during bar replay, rate > 0 = longs pay; min notional 5 USDT per order; margin per order
≤ 50% of initial balance; fills at the latest 1m bar close; 24/7. Settlement is lazy —
bars since the last visit are replayed on the next query, so funding/liquidation apply
even after inactivity. Opposite-side position on the same symbol must be closed first;
same-side adds merge into one position (entry weighted-averages, leverage = latest).

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
