#!/usr/bin/env python3
"""
A-Share simulation trading (v3 — per-account routing).

Used via the unified skill:
    from finmeta_simulation_skill.ashare import buy_stock, get_account_snapshot

Or CLI (from skill root):
    python ashare/api.py --action account
    python ashare/api.py --action buy --symbol 600519.SH --quantity 100

Env vars: FINMETA_ACCESS_TOKEN, FINTOOLS_SIMULATION_ACCOUNT_ID
"""

import argparse, json, os, sys
from pathlib import Path

ACCOUNTS_FILE = Path.home() / ".finmeta" / "config.json"  # SSOT: access_token + accounts.*
MARKET = "ashare"  # this module's key under accounts.*
API_BASE = os.getenv("FINTOOLS_API_BASE", "https://fin-meta.net")
MARKET_DATA_PREFIX = "/api/v1/ashare"  # 行情（市场 router，与模拟盘无关）
SIM_PREFIX = "/api/v1/simulation"     # 模拟盘 canonical（2026-08-21 路由统一）


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
    return ""


def _save_token(token):
    ACCOUNTS_FILE.parent.mkdir(parents=True, exist_ok=True)
    cfg = {}
    if ACCOUNTS_FILE.exists():
        try:
            cfg = json.loads(ACCOUNTS_FILE.read_text())
        except json.JSONDecodeError:
            cfg = {}
    cfg["access_token"] = token
    ACCOUNTS_FILE.write_text(json.dumps(cfg, indent=2))


def _load_account_id():
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


def _require_account_id():
    """Read account_id from env/config, fall back to None (auto-resolve/auto-create downstream)."""
    return _load_account_id()


def _clear_account_id():
    """Remove this market's account_id from config (stale residue from another token's user)."""
    if not ACCOUNTS_FILE.exists():
        return
    try:
        cfg = json.loads(ACCOUNTS_FILE.read_text())
    except json.JSONDecodeError:
        return
    if MARKET in cfg.get("accounts", {}):
        del cfg["accounts"][MARKET]
        ACCOUNTS_FILE.write_text(json.dumps(cfg, indent=2))


def _pick_account_id():
    """Resolve account_id: env/config (ownership-validated) → personal account from GET /simulation/accounts.

    config 存的 id 不在当前 token 名下 = 旧 token 残留：从 config 清除并改用名下盘，
    换 token 后首次调用即自愈（不再 404 死锁）。列表接口失败时不拦已配置的 id。
    """
    aid = _require_account_id()
    resp = _get("/accounts", {"market": MARKET}, sim=True)
    if not resp.get("success"):
        return aid
    accounts = resp.get("data", {}).get("data", {}).get("accounts", [])
    owned = {a.get("id") for a in accounts}
    if aid and aid in owned:
        return aid
    if aid:
        _clear_account_id()
        print(f"stale account id {aid} (accounts.{MARKET}) cleared — not owned by current token",
              file=sys.stderr)
    personal = next((a for a in accounts if a.get("competition_id") is None), None)
    acc = personal or (accounts[0] if accounts else None)
    return acc.get("id") if acc else None


def _ensure_account_id():
    """下单用：env/config → 名下盘 → 都没有则新建一个并写回 config（对齐旧自动建盘行为）。"""
    aid = _pick_account_id()
    if aid:
        return aid
    resp = _post("/accounts", {"market": MARKET})
    if resp.get("success"):
        new_id = resp["data"]["data"]["id"]
        _save_account_id(new_id)
        return new_id
    return None


def _no_account_error(trade: bool = False):
    """名下无盘（或建盘失败）时的报错 — 提示用户传入最新模拟盘号。"""
    hint = ("provide the latest simulation account_id: pass account_id / set "
            f"FINTOOLS_SIMULATION_ACCOUNT_ID / python {MARKET}/api.py --account-id <id>")
    if trade:
        return {"success": False,
                "error": f"No {MARKET} account and auto-create failed — {hint}"}
    return {"success": False,
            "error": f"No {MARKET} accounts found under this token — {hint}, "
                     f"or place a trade first (a new account will be created)"}


def _require_token():
    token = _load_token()
    if not token:
        print(
            "Missing API token. Get yours from https://fin-meta.net/profile, then:\n"
            "  python ashare/api.py --token YOUR_TOKEN",
            file=sys.stderr,
        )
        sys.exit(1)
    return token


# === Market Data (no auth) ===

def list_stocks():
    return _get("/stocks")


def get_quote(symbols):
    if isinstance(symbols, str):
        symbols = [s.strip() for s in symbols.split(",")]
    return _get("/stocks/quotes", {"symbols": ",".join(symbols)})


_PERIOD_ALIASES = {"day": "1d", "daily": "1d", "1d": "1d", "5m": "5m"}


def get_kline(stock_code: str, period: str = "1d", limit: int = 60):
    period = _PERIOD_ALIASES.get(period, period)
    return _get(f"/stocks/{stock_code}/kline", {"period": period, "limit": limit})


# === Account (requires account_id) ===

def get_account(account_id: int = None):
    """Get account overview (balance, market value, P/L).

    Args:
        account_id: optional — reads from FINTOOLS_SIMULATION_ACCOUNT_ID env var if omitted.
    """
    aid = account_id if account_id is not None else _pick_account_id()
    if aid:
        return _get(f"/accounts/{aid}", sim=True)
    return _get("/accounts", {"market": MARKET}, sim=True)


def get_positions(account_id: int = None):
    """Get current positions with unrealized P/L.

    Args:
        account_id: optional — auto-resolves your personal account if omitted.
    """
    aid = account_id if account_id is not None else _pick_account_id()
    if not aid:
        return _no_account_error()
    return _get(f"/accounts/{aid}/positions", sim=True)


# === Trading (requires account_id) ===

def buy(stock_code: str, quantity: int, account_id: int = None):
    """Buy shares (quantity must be multiple of 100).

    Args:
        stock_code: e.g. 600519.SH
        quantity: number of shares, must be multiple of 100 (1 lot).
        account_id: optional — auto-resolves if omitted; auto-creates an account when you have none.
    """
    aid = account_id if account_id is not None else _ensure_account_id()
    if not aid:
        return _no_account_error(trade=True)
    return _post(f"/{MARKET}/accounts/{aid}/orders/buy",
                 {"stock_code": stock_code, "quantity": quantity})


def sell(stock_code: str, quantity: int, account_id: int = None):
    """Sell shares (quantity must be multiple of 100).

    Args:
        stock_code: e.g. 600519.SH
        quantity: number of shares, must be multiple of 100 (1 lot).
        account_id: optional — auto-resolves if omitted; auto-creates an account when you have none.
    """
    aid = account_id if account_id is not None else _ensure_account_id()
    if not aid:
        return _no_account_error(trade=True)
    return _post(f"/{MARKET}/accounts/{aid}/orders/sell",
                 {"stock_code": stock_code, "quantity": quantity})


# === History (requires account_id) ===

def get_orders(limit: int = 50, account_id: int = None):
    """Get recent trade orders.

    Args:
        limit: max results (default 50, max 200).
        account_id: optional — auto-resolves your personal account if omitted.
    """
    aid = account_id if account_id is not None else _pick_account_id()
    if not aid:
        return _no_account_error()
    return _get(f"/accounts/{aid}/orders", {"limit": min(limit, 200)}, sim=True)


def get_buy_orders(page: int = 1, limit: int = 50, account_id: int = None):
    """Get buy orders (paginated). account_id is optional."""
    aid = account_id if account_id is not None else _pick_account_id()
    if not aid:
        return _no_account_error()
    return _get(f"/accounts/{aid}/orders", {"page": page, "limit": min(limit, 200), "side": "buy"}, sim=True)


def get_sell_orders(page: int = 1, limit: int = 50, account_id: int = None):
    """Get sell orders (paginated). account_id is optional."""
    aid = account_id if account_id is not None else _pick_account_id()
    if not aid:
        return _no_account_error()
    return _get(f"/accounts/{aid}/orders", {"page": page, "limit": min(limit, 200), "side": "sell"}, sim=True)


def get_balance_log(page: int = 1, limit: int = 50, account_id: int = None):
    """Get balance change log (paginated). account_id is optional."""
    aid = account_id if account_id is not None else _pick_account_id()
    if not aid:
        return _no_account_error()
    return _get(f"/accounts/{aid}/balance-log", {"page": page, "limit": min(limit, 200)}, sim=True)


def get_fee_log(page: int = 1, limit: int = 50, account_id: int = None):
    """Get fee log — only buy/sell entries (paginated). account_id is optional."""
    aid = account_id if account_id is not None else _pick_account_id()
    if not aid:
        return _no_account_error()
    raw = _get(f"/accounts/{aid}/balance-log", {"page": page, "limit": min(limit, 200)}, sim=True)
    if raw.get("success") and raw["data"].get("data"):
        items = raw["data"]["data"].get("items", [])
        raw["data"]["items"] = [x for x in items if x.get("reason") in ("buy", "sell")]
    return raw


def get_rules():
    return _get(f"/rules/{MARKET}", sim=True)


# ═══════════ CLI ═══════════

def main():
    parser = argparse.ArgumentParser(description="A-Share simulation trading CLI (v3)")
    parser.add_argument("--action", required=False, default="")
    parser.add_argument("--symbols")
    parser.add_argument("--symbol", dest="stock_code")  # unified --symbol alias
    parser.add_argument("--stock-code")
    parser.add_argument("--quantity", type=int)
    parser.add_argument("--period", default="1d")
    parser.add_argument("--limit", type=int, default=60)
    parser.add_argument("--page", type=int, default=1)
    parser.add_argument("--token", help="Save API token to ~/.finmeta/config.json")
    parser.add_argument("--account-id", type=int, help="Save simulation account ID to config.json")
    args = parser.parse_args()

    if args.token or args.account_id:
        if args.token:
            _save_token(args.token)
            print("Token saved to", ACCOUNTS_FILE)
        if args.account_id:
            _save_account_id(args.account_id)
            print(f"Account ID {args.account_id} saved to {ACCOUNTS_FILE} (accounts.{MARKET})")
        if not args.action:
            return

    if not args.action:
        parser.print_help()
        sys.exit(0)

    AUTH_ACTIONS = {"account", "positions", "buy", "sell", "orders",
                    "buy_orders", "sell_orders", "balance_log", "fee_log"}

    if args.action in AUTH_ACTIONS:
        _require_token()

    code = args.stock_code

    if args.action == "list_stocks":
        result = list_stocks()
    elif args.action == "get_quote":
        result = get_quote(args.symbols) if args.symbols else {"success": False, "error": "missing --symbols"}
    elif args.action == "kline":
        result = get_kline(code, args.period, args.limit) if code else {"success": False, "error": "missing --symbol"}
    elif args.action == "account":
        result = get_account()
    elif args.action == "positions":
        result = get_positions()
    elif args.action == "buy":
        result = buy(code, args.quantity) if code and args.quantity else {"success": False, "error": "missing --symbol or --quantity"}
    elif args.action == "sell":
        result = sell(code, args.quantity) if code and args.quantity else {"success": False, "error": "missing --symbol or --quantity"}
    elif args.action == "orders":
        result = get_orders(args.limit)
    elif args.action == "buy_orders":
        result = get_buy_orders(args.page, args.limit)
    elif args.action == "sell_orders":
        result = get_sell_orders(args.page, args.limit)
    elif args.action == "balance_log":
        result = get_balance_log(args.page, args.limit)
    elif args.action == "fee_log":
        result = get_fee_log(args.page, args.limit)
    elif args.action == "rules":
        result = get_rules()
    else:
        result = {"success": False, "error": f"unknown action: {args.action}"}

    print(json.dumps(result, ensure_ascii=False, indent=2))
    sys.exit(0 if result and result.get("success") else 1)


if __name__ == "__main__":
    main()
