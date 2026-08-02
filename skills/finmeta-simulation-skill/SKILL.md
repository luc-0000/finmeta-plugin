---
name: finmeta-simulation-skill
description: Unified simulation trading skill. Supports A-Share, US Stock, and Crypto markets — market data, account queries, trading (buy/sell), and order history. Use when the user wants to check prices, analyze charts, manage simulation accounts, or place trades in any of these markets.
---

# FinMeta Simulation Trading

Covers **A-Share** (`ashare/`), **Crypto** (`crypto/`), and **US Stock** (`usstock/`). Each sub-module has its own `api.py` and `api_reference.md`.

## Quick Start

```bash
# Token: load from ~/.finmeta/access_token (set up by finmeta-plugin)
export FINMETA_ACCESS_TOKEN=$(cat ~/.finmeta/access_token 2>/dev/null)
export FINTOOLS_SIMULATION_ACCOUNT_ID=123   # A-Share only

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
```

## Setup

> **Token**: load from persistent storage first:
> ```bash
> export FINMETA_ACCESS_TOKEN=$(cat ~/.finmeta/access_token 2>/dev/null)
> ```
> If the file doesn't exist or is empty, stop and ask the user to run `finmeta-plugin` setup skill first.

```bash
# A-Share only — save account ID (token is managed by plugin)
python ashare/api.py --account-id 123
```

- **Account ID** (A-Share only): My Simulation → click ID chip to copy
- Crypto and US Stock auto-resolve accounts — no account_id needed

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

## Agent Notes

### First Run — Token & Account Setup

1. Token: load from `~/.finmeta/access_token`. If missing, invoke `finmeta-plugin` setup skill.
2. For A-Share: check `FINTOOLS_SIMULATION_ACCOUNT_ID` env var or `config.json` `account_id`
3. If A-Share account_id is missing (but token is set):
   - List accounts: `curl -H "Authorization: Bearer $FINMETA_ACCESS_TOKEN" https://fin-meta.net/api/v1/ashare/accounts?lightweight=true`
   - Present the list: *"Here are your accounts: (1) Account #123 — A-Share. Which one?"*
   - Save with: `python ashare/api.py --account-id <id>`
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

# A-Share — account_id optional (reads from env var / config.json)
result = ashare_buy("600519.SH", 100, account_id=123)

# Crypto — no account_id needed
result = crypto_buy("BTC/USDT", 0.01)

# US Stock — account_id optional (auto-creates personal account)
result = usstock_buy("AAPL", 10)
```
