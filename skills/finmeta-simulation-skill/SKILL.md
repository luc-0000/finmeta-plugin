---
name: finmeta-simulation-skill
description: Unified simulation trading skill. Supports A-Share, US Stock, HK Stock, and Crypto markets — market data, account queries, trading (buy/sell), and order history. Use when the user wants to check prices, analyze charts, manage simulation accounts, or place trades in any of these markets.
---

# FinMeta Simulation Trading

Covers **A-Share** (`ashare/`), **Crypto** (`crypto/`), **US Stock** (`usstock/`), and **HK Stock** (`hkstock/`). Each sub-module has its own `api.py` and `api_reference.md`.

## Quick Start

```bash
# Token: auto-loaded from ~/.finmeta/config.json by api.py (no export needed)
# account_id optional in all four markets — auto-resolved (see Setup)

# A-Share
python ashare/api.py --action get_quote --symbols "600519.SH"
python ashare/api.py --action account
python ashare/api.py --action buy --symbol 600519.SH --quantity 100

# Crypto
python crypto/api.py --action get_quotes --symbols "BTC/USDT,ETH/USDT"
python crypto/api.py --action account
python crypto/api.py --action buy --symbol BTC/USDT --quantity 0.01

# US Stock
python usstock/api.py --action get_quotes --symbols "AAPL,MSFT"
python usstock/api.py --action account
python usstock/api.py --action buy --symbol AAPL --quantity 10

# HK Stock
python hkstock/api.py --action get_quotes --symbols "00700.HK,00005.HK"
python hkstock/api.py --action account
python hkstock/api.py --action buy --symbol 00700.HK --quantity 10
```

## Setup

> **Token**: auto-loaded from `~/.finmeta/config.json` by `api.py` — no export needed.
> If the file doesn't exist, stop and ask the user to run `finmeta-plugin` setup skill first.

```bash
# Optional — pin a specific account (writes accounts.<market> to ~/.finmeta/config.json)
python ashare/api.py --account-id 123
```

- All four markets **auto-resolve** your personal account — no account_id needed
- Placing a trade with no account under this token **auto-creates** one and saves it to config
- No account yet and want one? Create explicitly: `python <market>/api.py --action create_account` (id saved to config automatically; optional `--name "..."`)
- Delete a sim: `python <market>/api.py --action delete_account --account-id <id>` — explicit id required, never auto-picks; clears the config pin if it pointed at the deleted id
- A saved account_id is **ownership-checked** per call: if it belongs to another token's user
  (leftover after switching tokens), it is cleared automatically and your own account is used —
  switching tokens never deadlocks a market
- Find an ID: My Simulation → click ID chip to copy

## Tools

### A-Share (`ashare/api.py`)

| Action | Command |
|--------|---------|
| Stock list | `--action list_stocks` |
| Quote | `--action get_quote --symbols "600519.SH"` |
| K-line | `--action kline --symbol 600519.SH` |
| Account | `--action account` |
| Create account | `--action create_account` (optional `--name "..."`) |
| Delete account | `--action delete_account --account-id <id>` (clears the config pin if it pointed there) |
| Positions | `--action positions` |
| Buy | `--action buy --symbol 600519.SH --quantity 100` |
| Sell | `--action sell --symbol 600519.SH --quantity 100` |
| Conditional buy | `--action conditional_buy --symbol 600519.SH --quantity 100 --trigger-dir le --trigger-price 1500 --expiry gtc` |
| Conditional sell | `--action conditional_sell --symbol 600519.SH --quantity 100 --trigger-dir ge --trigger-price 1700` |
| Conditional orders | `--action conditional_orders --status pending` |
| Cancel conditional | `--action conditional_cancel --order-id 6` |
| Orders | `--action orders` |
| Balance log | `--action balance_log` |
| Fee log | `--action fee_log` |
| Rules | `--action rules` |

### Crypto (`crypto/api.py`)

| Action | Command |
|--------|---------|
| Symbol list | `--action list_symbols` |
| Quotes | `--action get_quotes --symbols "BTC/USDT"` |
| K-line | `--action kline --symbol BTC/USDT` |
| Account | `--action account` |
| Create account | `--action create_account` (optional `--name "..."`) |
| Delete account | `--action delete_account --account-id <id>` (clears the config pin if it pointed there) |
| Positions | `--action positions` |
| Buy | `--action buy --symbol BTC/USDT --quantity 0.01` |
| Sell | `--action sell --symbol BTC/USDT --quantity 0.01` |
| Conditional buy | `--action conditional_buy --symbol BTC/USDT --quantity 0.5 --trigger-dir le --trigger-price 49000` |
| Conditional sell | `--action conditional_sell --symbol BTC/USDT --quantity 0.5 --trigger-dir ge --trigger-price 52000` |
| Conditional orders | `--action conditional_orders --status pending` |
| Cancel conditional | `--action conditional_cancel --order-id 6` |
| Orders | `--action orders` |
| Balance log | `--action balance_log` |
| Rules | `--action rules` |

### US Stock (`usstock/api.py`)

| Action | Command |
|--------|---------|
| Symbol list | `--action list_symbols` |
| Quotes | `--action get_quotes --symbols "AAPL"` |
| K-line | `--action kline --symbol AAPL` |
| Account | `--action account` |
| Create account | `--action create_account` (optional `--name "..."`) |
| Delete account | `--action delete_account --account-id <id>` (clears the config pin if it pointed there) |
| Positions | `--action positions` |
| Buy | `--action buy --symbol AAPL --quantity 10` |
| Sell | `--action sell --symbol AAPL --quantity 10` |
| Conditional buy | `--action conditional_buy --symbol AAPL --quantity 10 --trigger-dir le --trigger-price 185` |
| Conditional sell | `--action conditional_sell --symbol AAPL --quantity 10 --trigger-dir ge --trigger-price 210` |
| Conditional orders | `--action conditional_orders --status pending` |
| Cancel conditional | `--action conditional_cancel --order-id 6` |
| Orders | `--action orders` |
| Balance log | `--action balance_log` |
| Rules | `--action rules` |

**US Stock notes**: T+0, lot_size=1 (integer shares), zero commission, no daily limit. Quantity negative = USD amount (resolves to floor(USD/price) shares). Universe = S&P 500.

### Conditional Orders (all four markets, one engine)

Same conditional-order engine for all markets; market differences are data (bar cadence, trading hours, day-close time). Trigger engine reads each market's bars from the platform database (no external quote API) and ticks every 30s. Fills happen at the triggering bar's closing price — how long a cross takes to fire depends on the market's bar cadence (~5 min for A-Share 5m bars, ~1-2 min for HK 1Min / crypto 1m bars).
`--trigger-dir le` = fire when the bar's low ≤ trigger (typical for buy-the-dip); `ge` = fire when the bar's high ≥ trigger (typical for take-profit sell). `--expiry day` voids at the market's close (A-Share 15:00 / US 16:00 ET / HK 16:00 HKT; rejected off-hours) and is auto-converted to `gtc` on crypto (24/7, no daily close); `gtc` stays until cancelled/filled.
If the latest bar has already crossed when you place (during trading hours), the order fires immediately (response may come back `filled`/`rejected`).
Pass `--client-order-id <key>` for idempotency — retries with the same key return the original order, never duplicate.

### HK Stock (`hkstock/api.py`)

| Action | Command |
|--------|---------|
| Stock list | `--action list_stocks` |
| Quotes | `--action get_quotes --symbols "00700.HK"` |
| K-line | `--action kline --symbol 00700.HK --period 1d` |
| Account | `--action account` |
| Create account | `--action create_account` (optional `--name "..."`) |
| Delete account | `--action delete_account --account-id <id>` (clears the config pin if it pointed there) |
| Positions | `--action positions` |
| Buy | `--action buy --symbol 00700.HK --quantity 10` |
| Sell | `--action sell --symbol 00700.HK --quantity 10` |
| Conditional buy | `--action conditional_buy --symbol 00700.HK --quantity 100 --trigger-dir le --trigger-price 290` |
| Conditional sell | `--action conditional_sell --symbol 00700.HK --quantity 100 --trigger-dir ge --trigger-price 330` |
| Conditional orders | `--action conditional_orders --status pending` |
| Cancel conditional | `--action conditional_cancel --order-id 6` |
| Orders | `--action orders` |
| Balance log | `--action balance_log` |
| Rules | `--action rules` |

**HK Stock notes**: T+0, lot_size=10, commission 0.1% (min HK$5), stamp tax 0.1% (sell only), no daily limit. Symbol = 5-digit code with `.HK` suffix (`00700.HK`, keep leading zeros). Kline `--period`: `1m` `5m` `1h` `1d`, refreshed every 5 min during HK trading hours (09:30–16:00 HKT). Universe = 142 competition symbols, not the full HK market.

## Agent Notes

> ⚠️ **Account ID source of truth = `~/.finmeta/config.json`** (key `accounts.<market>`).
> Every trade/account query reads account_id from this file at runtime — `api.py` does it for you; **never** hardcode an id in a command.
> **NEVER** store account_id in agent memory, and **never** copy a value from conversation history into a call. If the user mentions an account id, persist it first with `python <market>/api.py --account-id <id>`, then let the skill read it back from the file.

### First Run — Token & Account Setup

1. Token: load from `~/.finmeta/config.json` (`access_token`). If missing, invoke `finmeta-plugin` setup skill.
2. account_id: nothing to do — every market auto-resolves your personal account
   (ownership-checks any id saved in config, auto-creates an account when you trade with none).
   User has no account and wants one? `python <market>/api.py --action create_account`
   creates it and pins the id in config.
3. If a call reports no account under this token and the user names one, persist it first:
   `python <market>/api.py --account-id <id>` (writes to `~/.finmeta/config.json`).

### Typical Flow

```bash
# A-Share
python ashare/api.py --action get_quote --symbols "600519.SH"
python ashare/api.py --action account
python ashare/api.py --action buy --symbol 600519.SH --quantity 100

# Crypto
python crypto/api.py --action get_quotes --symbols "BTC/USDT"
python crypto/api.py --action account
python crypto/api.py --action buy --symbol BTC/USDT --quantity 0.01
```

### Python Import (Agent Code)

```python
from finmeta_simulation_skill.ashare import buy as ashare_buy, get_account as ashare_account
from finmeta_simulation_skill.ashare import place_conditional as ashare_place_conditional
from finmeta_simulation_skill.crypto import buy as crypto_buy, get_account as crypto_account
from finmeta_simulation_skill.usstock import buy as usstock_buy, get_account as usstock_account
from finmeta_simulation_skill.hkstock import buy as hkstock_buy, get_account as hkstock_account

# A-Share — account_id optional (auto-resolves / auto-creates)
result = ashare_buy("600519.SH", 100)

# A-Share conditional order (trigger_dir: "le" price<=trigger | "ge" price>=trigger)
result = ashare_place_conditional("600519.SH", "buy", 100,
                                  trigger_dir="le", trigger_price=1500, expiry="gtc",
                                  client_order_id="my-task-001")

# Crypto conditional order (day is auto-converted to gtc — 24/7 market)
from finmeta_simulation_skill.crypto import place_conditional as crypto_place_conditional
result = crypto_place_conditional("BTC/USDT", "buy", 0.5,
                                  trigger_dir="le", trigger_price=49000,
                                  client_order_id="my-task-002")

# Crypto
result = crypto_buy("BTC/USDT", 0.01)

# US Stock
result = usstock_buy("AAPL", 10)

# HK Stock
result = hkstock_buy("00700.HK", 10)
```
