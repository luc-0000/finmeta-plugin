---
name: finmeta-simulation-skill
description: Unified simulation trading skill. Supports A-Share, US Stock, HK Stock, and Crypto markets — market data, account queries, trading (buy/sell), and order history. Use when the user wants to check prices, analyze charts, manage simulation accounts, or place trades in any of these markets.
---

# FinMeta Simulation Trading

Covers **A-Share** (`ashare/`), **Crypto** (`crypto/`), **US Stock** (`usstock/`), and **HK Stock** (`hkstock/`). Each sub-module has its own `api.py` and `api_reference.md`.

## Quick Start

```bash
# Token: auto-loaded from ~/.finmeta/config.json by api.py (no export needed)
# A-Share account_id is read from ~/.finmeta/config.json — see Setup to save it

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
# A-Share only — save account ID to ~/.finmeta/config.json (accounts.ashare)
python ashare/api.py --account-id 123
```

- **Account ID** (A-Share only): My Simulation → click ID chip to copy
- Crypto, US Stock, and HK Stock auto-resolve accounts — no account_id needed
- Saved account IDs live in `~/.finmeta/config.json` under `accounts.<market>`; every trade reads from there at runtime

## Tools

### A-Share (`ashare/api.py`)

| Action | Command |
|--------|---------|
| Stock list | `--action list_stocks` |
| Quote | `--action get_quote --symbols "600519.SH"` |
| K-line | `--action kline --symbol 600519.SH` |
| Account | `--action account` |
| Positions | `--action positions` |
| Buy | `--action buy --symbol 600519.SH --quantity 100` |
| Sell | `--action sell --symbol 600519.SH --quantity 100` |
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
| Positions | `--action positions` |
| Buy | `--action buy --symbol BTC/USDT --quantity 0.01` |
| Sell | `--action sell --symbol BTC/USDT --quantity 0.01` |
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
| Positions | `--action positions` |
| Buy | `--action buy --symbol AAPL --quantity 10` |
| Sell | `--action sell --symbol AAPL --quantity 10` |
| Orders | `--action orders` |
| Balance log | `--action balance_log` |
| Rules | `--action rules` |

**US Stock notes**: T+0, lot_size=1 (integer shares), zero commission, no daily limit. Quantity negative = USD amount (resolves to floor(USD/price) shares). Universe = S&P 500.

### HK Stock (`hkstock/api.py`)

| Action | Command |
|--------|---------|
| Stock list | `--action list_stocks` |
| Quotes | `--action get_quotes --symbols "00700.HK"` |
| K-line | `--action kline --symbol 00700.HK --period 1d` |
| Account | `--action account` |
| Positions | `--action positions` |
| Buy | `--action buy --symbol 00700.HK --quantity 10` |
| Sell | `--action sell --symbol 00700.HK --quantity 10` |
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
2. For A-Share: read account_id from `~/.finmeta/config.json` (`accounts.ashare`).
3. If A-Share account_id is missing (but token is set):
   - List accounts: `curl -H "Authorization: Bearer $FINMETA_ACCESS_TOKEN" https://fin-meta.net/api/v1/simulation/accounts?lightweight=true&market=ashare`
   - Present the list: *"Here are your accounts: (1) Account #123 — A-Share. Which one?"*
   - Save with: `python ashare/api.py --account-id <id>` (writes to `~/.finmeta/config.json`)
4. Crypto and US Stock do not need account_id — they auto-resolve from your user.

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
from finmeta_simulation_skill.crypto import buy as crypto_buy, get_account as crypto_account
from finmeta_simulation_skill.usstock import buy as usstock_buy, get_account as usstock_account
from finmeta_simulation_skill.hkstock import buy as hkstock_buy, get_account as hkstock_account

# A-Share — account_id optional (reads from env var / config.json)
result = ashare_buy("600519.SH", 100, account_id=123)

# Crypto — no account_id needed
result = crypto_buy("BTC/USDT", 0.01)

# US Stock — account_id optional (auto-creates personal account)
result = usstock_buy("AAPL", 10)

# HK Stock — no account_id needed (auto-creates personal account)
result = hkstock_buy("00700.HK", 10)
```
