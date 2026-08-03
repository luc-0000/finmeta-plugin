#!/usr/bin/env python3
"""
Crypto simulation trading.

Used via the unified skill:
    from finmeta_simulation_skill.crypto import buy, get_account

Or CLI (from skill root):
    python crypto/api.py --action account
    python crypto/api.py --action buy --symbol BTC/USDT --quantity 0.01

Env vars: FINMETA_ACCESS_TOKEN
"""

import argparse, json, os, sys
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent.parent
CONFIG_FILE = SKILL_DIR / "config.json"  # legacy: token field only
TOKEN_FILE = Path.home() / ".finmeta" / "access_token"  # SSOT for access token
ACCOUNTS_FILE = Path.home() / ".finmeta" / "config.json"  # SSOT for account_ids
MARKET = "crypto"  # this module's key under accounts.*
API_BASE = os.getenv("FINTOOLS_API_BASE", "https://fin-meta.net")
API_PREFIX = "/api/v1/crypto"


def _ensure_requests():
    try:
        import requests  # noqa: F811
        return requests
    except ImportError:
        import subprocess
        print("Installing requests...", file=sys.stderr)
        subprocess.check_call(
            [sys.executable, "-m", "pip", "install", "requests", "-q"],
            stdout=sys.stderr, stderr=sys.stderr,
        )
        import requests  # noqa: F811
        return requests


requests = _ensure_requests()


# ═══════════ Config ═══════════

def _load_config():
    if CONFIG_FILE.exists():
        try:
            return json.loads(CONFIG_FILE.read_text())
        except (json.JSONDecodeError, KeyError):
            return {}
    return {}


def _save_config(cfg: dict):
    CONFIG_FILE.write_text(json.dumps(cfg))


def _load_token():
    token = os.getenv("FINMETA_ACCESS_TOKEN") or os.getenv("FINTOOLS_API_TOKEN")
    if token:
        return token
    if TOKEN_FILE.exists():
        return TOKEN_FILE.read_text().strip()
    return _load_config().get("token", "")


def _save_token(token):
    cfg = _load_config()
    cfg["token"] = token
    _save_config(cfg)


def _load_account_id():
    """Read account_id from env var (override) or ~/.finmeta/config.json (SSOT)."""
    val = os.getenv("FINTOOLS_SIMULATION_ACCOUNT_ID")
    if val:
        try:
            return int(val)
        except ValueError:
            pass
    if ACCOUNTS_FILE.exists():
        try:
            return json.loads(ACCOUNTS_FILE.read_text()).get("accounts", {}).get(MARKET)
        except json.JSONDecodeError:
            return None
    return None


def _save_account_id(account_id: int):
    ACCOUNTS_FILE.parent.mkdir(parents=True, exist_ok=True)
    cfg = {}
    if ACCOUNTS_FILE.exists():
        try:
            cfg = json.loads(ACCOUNTS_FILE.read_text())
        except json.JSONDecodeError:
            cfg = {}
    cfg.setdefault("accounts", {})[MARKET] = account_id
    ACCOUNTS_FILE.write_text(json.dumps(cfg, indent=2))


def _require_account_id():
    """Read account_id from env/config, fall back to None (crypto auto-creates)."""
    return _load_account_id()


def _headers():
    return {"Authorization": f"Bearer {_load_token()}", "Content-Type": "application/json"}


def _url(path: str) -> str:
    return f"{API_BASE}{API_PREFIX}{path}"


def _get(path, params=None):
    try:
        r = requests.get(_url(path), headers=_headers(), params=params, timeout=60)
        r.raise_for_status()
        return {"success": True, "data": r.json()}
    except requests.exceptions.RequestException as e:
        return _handle_error(e)


def _post(path, body=None):
    try:
        r = requests.post(_url(path), headers=_headers(), json=body or {}, timeout=60)
        r.raise_for_status()
        return {"success": True, "data": r.json()}
    except requests.exceptions.RequestException as e:
        return _handle_error(e)


def _handle_error(e):
    resp = getattr(e, "response", None)
    if resp is not None:
        try:
            detail = resp.json().get("detail", "")
            if detail:
                return {"success": False, "error": detail}
        except Exception:
            pass
        return {"success": False, "error": f"HTTP {resp.status_code}"}
    return {"success": False, "error": type(e).__name__}


def _require_token():
    token = _load_token()
    if not token:
        print(
            "Missing API token. Get yours from https://fin-meta.net/profile, then:\n"
            "  python crypto/api.py --token YOUR_TOKEN",
            file=sys.stderr,
        )
        sys.exit(1)
    return token


# === Market Data (no auth) ===

def list_symbols():
    """List all supported crypto trading pairs."""
    return _get("/symbols")


def get_quotes(symbols):
    """Batch query quotes for given symbols.

    Args:
        symbols: comma-separated string or list, e.g. "BTC/USDT,ETH/USDT"
    """
    if isinstance(symbols, str):
        symbols = [s.strip() for s in symbols.split(",")]
    return _get("/quotes", {"symbols": ",".join(symbols)})


def get_kline(symbol: str, limit: int = 100):
    """Query kline (OHLCV) for a symbol.

    Args:
        symbol: trading pair, e.g. BTC/USDT
        limit: number of klines to return, max 500
    """
    return _get("/kline", {"symbol": symbol, "limit": min(limit, 500)})


# === Account (requires account_id) ===

def get_account(account_id: int = None):
    """Get account overview (balance, market value, P/L).

    Args:
        account_id: optional — reads from FINTOOLS_SIMULATION_ACCOUNT_ID env var if omitted.
    """
    _require_token()
    aid = account_id if account_id is not None else _require_account_id()
    return _get(f"/account?account_id={aid}" if aid else "/account")


# === Trading (requires account_id) ===

def buy(symbol: str, quantity: float, account_id: int = None):
    """Buy crypto.

    Args:
        symbol: trading pair, e.g. BTC/USDT
        quantity: amount in base currency, e.g. 0.01 BTC
        account_id: optional — reads from FINTOOLS_SIMULATION_ACCOUNT_ID env var if omitted.
    """
    _require_token()
    aid = account_id if account_id is not None else _require_account_id()
    body = {"symbol": symbol, "quantity": quantity}
    if aid:
        body["account_id"] = aid
    return _post("/orders/buy", body)


def sell(symbol: str, quantity: float, account_id: int = None):
    """Sell crypto.

    Args:
        symbol: trading pair, e.g. BTC/USDT
        quantity: amount in base currency, e.g. 0.01 BTC
        account_id: optional — reads from FINTOOLS_SIMULATION_ACCOUNT_ID env var if omitted.
    """
    _require_token()
    aid = account_id if account_id is not None else _require_account_id()
    body = {"symbol": symbol, "quantity": quantity}
    if aid:
        body["account_id"] = aid
    return _post("/orders/sell", body)


# === Rules (no auth) ===

def get_rules():
    """Get crypto trading rules (min order size, commission, etc.)."""
    return _get("/rules")


# === History (requires account_id) ===

def get_positions(account_id: int = None):
    """Get current holdings with unrealized P/L.

    Args:
        account_id: optional — reads from FINTOOLS_SIMULATION_ACCOUNT_ID env var if omitted.
    """
    _require_token()
    aid = account_id if account_id is not None else _require_account_id()
    params = {}
    if aid:
        params["account_id"] = aid
    return _get("/positions", params)


def get_orders(limit: int = 20, account_id: int = None):
    """Query trade history.

    Args:
        limit: max results (default 20, max 100).
        account_id: optional — reads from FINTOOLS_SIMULATION_ACCOUNT_ID env var if omitted.
    """
    _require_token()
    aid = account_id if account_id is not None else _require_account_id()
    params = {"limit": min(limit, 100)}
    if aid:
        params["account_id"] = aid
    return _get("/orders", params)


def get_balance_log(page: int = 1, limit: int = 50, account_id: int = None):
    """Get balance change log (paginated).

    Args:
        page: page number (1-indexed).
        limit: max results per page (default 50, max 200).
        account_id: optional — reads from FINTOOLS_SIMULATION_ACCOUNT_ID env var if omitted.
    """
    _require_token()
    aid = account_id if account_id is not None else _require_account_id()
    params = {"page": page, "limit": min(limit, 200)}
    if aid:
        params["account_id"] = aid
    return _get("/balance-log", params)


# ═══════════ CLI ═══════════

def main():
    parser = argparse.ArgumentParser(description="Crypto simulation trading CLI")
    parser.add_argument("--action", required=False, default="")
    parser.add_argument("--symbol")
    parser.add_argument("--symbols")
    parser.add_argument("--quantity", type=float)
    parser.add_argument("--limit", type=int, default=100)
    parser.add_argument("--token", help="Save API token to config.json")
    args = parser.parse_args()

    if args.token:
        _save_token(args.token)
        print("Token saved to", CONFIG_FILE)
        if not args.action:
            return

    if not args.action:
        parser.print_help()
        sys.exit(0)

    AUTH_ACTIONS = {"account", "buy", "sell", "orders", "positions", "balance_log"}

    if args.action in AUTH_ACTIONS:
        _require_token()

    if args.action == "list_symbols":
        result = list_symbols()
    elif args.action == "get_quotes":
        result = get_quotes(args.symbols) if args.symbols else {"success": False, "error": "missing --symbols"}
    elif args.action == "kline":
        result = get_kline(args.symbol, args.limit) if args.symbol else {"success": False, "error": "missing --symbol"}
    elif args.action == "account":
        result = get_account()
    elif args.action == "positions":
        result = get_positions()
    elif args.action == "buy":
        result = buy(args.symbol, args.quantity) if args.symbol and args.quantity else {"success": False, "error": "missing --symbol or --quantity"}
    elif args.action == "sell":
        result = sell(args.symbol, args.quantity) if args.symbol and args.quantity else {"success": False, "error": "missing --symbol or --quantity"}
    elif args.action == "orders":
        result = get_orders(args.limit)
    elif args.action == "balance_log":
        result = get_balance_log()
    elif args.action == "rules":
        result = get_rules()
    else:
        result = {"success": False, "error": f"unknown action: {args.action}"}

    print(json.dumps(result, ensure_ascii=False, indent=2))
    sys.exit(0 if result and result.get("success") else 1)


if __name__ == "__main__":
    main()
