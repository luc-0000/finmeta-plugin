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
CONFIG_FILE = SKILL_DIR / "config.json"  # legacy: token field only
TOKEN_FILE = Path.home() / ".finmeta" / "access_token"  # SSOT for access token
ACCOUNTS_FILE = Path.home() / ".finmeta" / "config.json"  # SSOT for account_ids
MARKET = "usstock"  # this module's key under accounts.*
API_BASE = os.getenv("FINTOOLS_API_BASE", "https://fin-meta.net")
MARKET_DATA_PREFIX = "/api/v1/usstock"  # 行情（市场 router，与模拟盘无关）
SIM_PREFIX = "/api/v1/simulation"      # 模拟盘 canonical（2026-08-21 路由统一）


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
    if ACCOUNTS_FILE.exists():  # SSOT: ~/.finmeta/config.json
        try:
            t = json.loads(ACCOUNTS_FILE.read_text()).get("access_token")
            if t:
                return t
        except json.JSONDecodeError:
            pass
    if TOKEN_FILE.exists():  # legacy fallback: ~/.finmeta/access_token
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
    """Read account_id from env/config, fall back to None (usstock auto-creates)."""
    return _load_account_id()


def _headers():
    return {"Authorization": f"Bearer {_load_token()}", "Content-Type": "application/json"}


def _url(path: str) -> str:
    return f"{API_BASE}{MARKET_DATA_PREFIX}{path}"


def _sim_url(path: str) -> str:
    """模拟盘 canonical 路径：/api/v1/simulation/*。"""
    return f"{API_BASE}{SIM_PREFIX}{path}"


def _get(path, params=None, sim: bool = False):
    try:
        r = requests.get(_sim_url(path) if sim else _url(path),
                         headers=_headers(), params=params, timeout=60)
        r.raise_for_status()
        return {"success": True, "data": r.json()}
    except requests.exceptions.RequestException as e:
        return _handle_error(e)


def _post(path, body=None):
    """POST（模拟盘专用，path 为 /api/v1/simulation 下的完整段）。"""
    try:
        r = requests.post(_sim_url(path), headers=_headers(), json=body or {}, timeout=60)
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


def get_kline(symbol: str, limit: int = 100, period: str = "5m"):
    """Query kline (OHLCV) for a symbol.

    Args:
        symbol: ticker, e.g. AAPL
        limit: number of klines to return, max 500
        period: 5m | 1h | 1d (default 5m; 1h/1d aggregated from 5m)
    """
    return _get("/kline", {"symbol": symbol, "limit": min(limit, 500), "period": period})


# === Account (requires account_id) ===

def _pick_account_id():
    """Resolve account_id: env/config override → personal account from GET /simulation/accounts."""
    aid = _require_account_id()
    if aid:
        return aid
    resp = _get("/accounts", {"market": MARKET}, sim=True)
    if not resp.get("success"):
        return None
    accounts = resp.get("data", {}).get("data", {}).get("accounts", [])
    personal = next((a for a in accounts if a.get("competition_id") is None), None)
    acc = personal or (accounts[0] if accounts else None)
    return acc.get("id") if acc else None


def _ensure_account_id():
    """下单用：env/config → 名下盘 → 都没有则新建一个（对齐旧自动建盘行为）。"""
    aid = _pick_account_id()
    if aid:
        return aid
    resp = _post("/accounts", {"market": MARKET})
    if resp.get("success"):
        return resp["data"]["data"]["id"]
    return None


def get_account(account_id: int = None):
    """Get account overview (balance, market value, P/L).

    Args:
        account_id: optional — with it returns single-account detail;
            without it returns all your accounts with aggregate stats.
    """
    _require_token()
    aid = account_id if account_id is not None else _require_account_id()
    if aid:
        return _get(f"/accounts/{aid}", sim=True)
    return _get("/accounts", {"market": MARKET}, sim=True)


# === Trading (requires account_id) ===

def buy(symbol: str, quantity: float, account_id: int = None):
    """Buy US stock.

    Args:
        symbol: ticker, e.g. AAPL
        quantity: shares (positive integer) OR USD amount (negative number, resolves to floor(USD/price) shares)
        account_id: optional — reads from FINTOOLS_SIMULATION_ACCOUNT_ID env var if omitted;
            名下没有盘时自动新建一个（对齐旧行为）。
    """
    _require_token()
    aid = account_id if account_id is not None else _ensure_account_id()
    if not aid:
        return {"success": False, "error": "No accounts available and auto-create failed"}
    return _post(f"/{MARKET}/accounts/{aid}/orders/buy",
                 {"stock_code": symbol, "quantity": quantity})


def sell(symbol: str, quantity: float, account_id: int = None):
    """Sell US stock.

    Args:
        symbol: ticker, e.g. AAPL
        quantity: shares (positive integer) OR USD amount (negative number)
        account_id: optional — reads from FINTOOLS_SIMULATION_ACCOUNT_ID env var if omitted;
            名下没有盘时自动新建一个（对齐旧行为）。
    """
    _require_token()
    aid = account_id if account_id is not None else _ensure_account_id()
    if not aid:
        return {"success": False, "error": "No accounts available and auto-create failed"}
    return _post(f"/{MARKET}/accounts/{aid}/orders/sell",
                 {"stock_code": symbol, "quantity": quantity})


# === Rules (no auth) ===

def get_rules():
    """Get US stock trading rules (lot size, commission, T+0, etc.)."""
    return _get(f"/rules/{MARKET}", sim=True)


# === History (requires account_id) ===

def get_positions(account_id: int = None):
    """Get current holdings with unrealized P/L.

    Args:
        account_id: optional — auto-resolves your personal account if omitted.
    """
    _require_token()
    aid = account_id if account_id is not None else _pick_account_id()
    if not aid:
        return {"success": False, "error": "No accounts found — place a trade first (auto-creates one)"}
    return _get(f"/accounts/{aid}/positions", sim=True)


def get_orders(limit: int = 20, account_id: int = None):
    """Query trade history.

    Args:
        limit: max results (default 20, max 200).
        account_id: optional — auto-resolves your personal account if omitted.
    """
    _require_token()
    aid = account_id if account_id is not None else _pick_account_id()
    if not aid:
        return {"success": False, "error": "No accounts found — place a trade first (auto-creates one)"}
    return _get(f"/accounts/{aid}/orders", {"limit": min(limit, 200)}, sim=True)


def get_balance_log(page: int = 1, limit: int = 50, account_id: int = None):
    """Get balance change log (paginated).

    Args:
        page: page number (1-indexed).
        limit: max results per page (default 50, max 200).
        account_id: optional — auto-resolves your personal account if omitted.
    """
    _require_token()
    aid = account_id if account_id is not None else _pick_account_id()
    if not aid:
        return {"success": False, "error": "No accounts found — place a trade first (auto-creates one)"}
    return _get(f"/accounts/{aid}/balance-log", {"page": page, "limit": min(limit, 200)}, sim=True)


# ═══════════ CLI ═══════════

def main():
    parser = argparse.ArgumentParser(description="US Stock simulation trading CLI")
    parser.add_argument("--action", required=False, default="")
    parser.add_argument("--symbol")
    parser.add_argument("--symbols")
    parser.add_argument("--quantity", type=float)
    parser.add_argument("--limit", type=int, default=100)
    parser.add_argument("--period", default="5m")
    parser.add_argument("--token", help="Save API token to config.json")
    parser.add_argument("--account-id", type=int, help="Save simulation account_id to config.json")
    args = parser.parse_args()

    if args.token:
        _save_token(args.token)
        print("Token saved to", CONFIG_FILE)
    if args.account_id:
        _save_account_id(args.account_id)
        print(f"Account ID saved to {ACCOUNTS_FILE} (accounts.{MARKET})")
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
        result = get_kline(args.symbol, args.limit, args.period) if args.symbol else {"success": False, "error": "missing --symbol"}
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
