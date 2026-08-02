#!/usr/bin/env python3
"""
US Stock simulation trading.

Used via the unified skill:
    from finmeta_simulation_skill.usstock import buy, get_account

Or CLI (from skill root):
    python usstock/api.py --action account
    python usstock/api.py --action buy --symbol AAPL --quantity 10

Env vars: FINMETA_ACCESS_TOKEN, FINTOOLS_SIMULATION_ACCOUNT_ID (optional)
"""

import argparse, json, os, sys
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent.parent
CONFIG_FILE = SKILL_DIR / "config.json"
API_BASE = os.getenv("FINTOOLS_API_BASE", "https://fin-meta.net")
API_PREFIX = "/api/v1/usstock"


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
    return _load_config().get("token", "")


def _save_token(token):
    cfg = _load_config()
    cfg["token"] = token
    _save_config(cfg)


def _load_account_id():
    """Read simulation_account_id from env var or config.json."""
    val = os.getenv("FINTOOLS_SIMULATION_ACCOUNT_ID")
    if val:
        try:
            return int(val)
        except ValueError:
            pass
    return _load_config().get("account_id")


def _save_account_id(account_id: int):
    cfg = _load_config()
    cfg["account_id"] = account_id
    _save_config(cfg)


def _require_account_id():
    """Read account_id from env/config, fall back to None (usstock auto-creates)."""
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
            "  python usstock/api.py --token YOUR_TOKEN",
            file=sys.stderr,
        )
        sys.exit(1)
    return token


# === Market Data (no auth) ===

def list_symbols():
    """List all supported US stock symbols (S&P 500)."""
    return _get("/symbols")


def get_quotes(symbols):
    """Batch query quotes for given symbols.

    Args:
        symbols: comma-separated string or list, e.g. "AAPL,MSFT"
    """
    if isinstance(symbols, str):
        symbols = [s.strip() for s in symbols.split(",")]
    return _get("/quotes", {"symbols": ",".join(symbols)})


def get_kline(symbol: str, limit: int = 100, timeframe: str = "5Min"):
    """Query kline (OHLCV) for a symbol.

    Args:
        symbol: ticker, e.g. AAPL
        limit: number of klines to return, max 500
        timeframe: 1Min | 5Min | 15Min | 1Hour | 1Day (default 5Min)
    """
    return _get("/kline", {"symbol": symbol, "limit": min(limit, 500), "timeframe": timeframe})


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
    """Buy US stock.

    Args:
        symbol: ticker, e.g. AAPL
        quantity: shares (positive integer) OR USD amount (negative number, resolves to floor(USD/price) shares)
        account_id: optional — reads from FINTOOLS_SIMULATION_ACCOUNT_ID env var if omitted.
    """
    _require_token()
    aid = account_id if account_id is not None else _require_account_id()
    body = {"symbol": symbol, "quantity": quantity}
    if aid:
        body["account_id"] = aid
    return _post("/orders/buy", body)


def sell(symbol: str, quantity: float, account_id: int = None):
    """Sell US stock.

    Args:
        symbol: ticker, e.g. AAPL
        quantity: shares (positive integer) OR USD amount (negative number)
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
    """Get US stock trading rules (lot size, commission, T+0, etc.)."""
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
    parser = argparse.ArgumentParser(description="US Stock simulation trading CLI")
    parser.add_argument("--action", required=False, default="")
    parser.add_argument("--symbol")
    parser.add_argument("--symbols")
    parser.add_argument("--quantity", type=float)
    parser.add_argument("--limit", type=int, default=100)
    parser.add_argument("--timeframe", default="5Min")
    parser.add_argument("--token", help="Save API token to config.json")
    parser.add_argument("--account-id", type=int, help="Save simulation account_id to config.json")
    args = parser.parse_args()

    if args.token:
        _save_token(args.token)
        print("Token saved to", CONFIG_FILE)
    if args.account_id:
        _save_account_id(args.account_id)
        print("Account ID saved to", CONFIG_FILE)
    if args.token or args.account_id:
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
        result = get_kline(args.symbol, args.limit, args.timeframe) if args.symbol else {"success": False, "error": "missing --symbol"}
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
