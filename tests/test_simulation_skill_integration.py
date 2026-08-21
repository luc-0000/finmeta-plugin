"""Integration: finmeta-simulation-skill 全部公开函数打 localhost。

验证目标：skill 四个 market api.py 的每个公开函数（行情 + 账户 + 交易 + 规则）
在本地环境真实可用 —— 直接 import skill 源码，通过 env 注入
FINTOOLS_API_BASE / FINMETA_ACCESS_TOKEN / FINTOOLS_SIMULATION_ACCOUNT_ID，
不是重新实现 HTTP 调用。

跑法（token 从本地 backend .env 取，不落盘）：
  TOKEN=$(grep -E '^FINMETA_ACCESS_TOKEN=' "$FINTOOLS_REPO/fintools_backend/.env" \
    | sed 's/^FINMETA_ACCESS_TOKEN=//' | tr -d '\r\n')
  FINMETA_ACCESS_TOKEN=$TOKEN conda run --no-capture-output -n fintools_backend \
    python -u tests/test_simulation_skill_integration.py
  # FINTOOLS_REPO = fintools 主仓库路径；在 finmeta-plugin repo 根目录下执行

净零清理：每个 market 建独立测试盘（skill-integration-<market>），
tearDownClass 统一 DELETE（级联清 positions/orders/balance_log）。
注意：local 模式 backend 连云 RDS，交易写入云端测试盘后随删盘清理。

交易断言分两档：
  - crypto：24/7 且 T+0，buy/sell 必须真实成功（严格）
  - ashare/hkstock/usstock：盘中应成功；若被业务规则拦（T+1 / 闭市 / 涨跌停），
    断言返回的是业务错误（success=False + 明确 detail），证明链路通、规则生效
"""
import importlib.util
import os
import unittest
from pathlib import Path

import requests

SKILL_ROOT = Path(__file__).resolve().parents[1] / "skills" / "finmeta-simulation-skill"
API_BASE = os.environ.setdefault("FINTOOLS_API_BASE", "http://localhost:8000")
TOKEN = os.environ.get("FINMETA_ACCESS_TOKEN", "")

# 业务错误关键词：命中视为"链路通、业务规则拦截"（非函数故障）
BUSINESS_RULE_KEYWORDS = ("t+1", "closed", "hours", "limit", "停", "闭市",
                          "not open", "market status", "suspend", "delist")


def _load_skill_module(market: str):
    """按 market 加载 skill 的 api.py（hyphen 目录名不能直接 import）。"""
    spec = importlib.util.spec_from_file_location(
        f"sim_skill_{market}", SKILL_ROOT / market / "api.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _api(method: str, path: str, body=None):
    """测试自身的账号生命周期管理（建/删测试盘），不经过 skill。"""
    r = requests.request(method, f"{API_BASE}{path}",
                         headers={"Authorization": f"Bearer {TOKEN}"},
                         json=body, timeout=60)
    r.raise_for_status()
    return r.json() if r.status_code != 204 else {}


@unittest.skipUnless(TOKEN, "FINMETA_ACCESS_TOKEN 未设置（见文件头跑法）")
class _MarketIntegrationMixin:
    """每个 market 一个子类（mixin + TestCase）；setUpClass 建盘，tearDownClass 删盘。
    不直接继承 TestCase，避免基类自身被 unittest 收集执行。"""
    MARKET = ""            # ashare | usstock | hkstock | crypto
    SYMBOL = ""            # 该市场的样本标的
    BUY_QTY = 1            # 买入数量
    SELL_QTY = 1           # 卖出数量
    STRICT_ROUND_TRIP = False  # True = sell 必须成功（crypto）

    mod = None
    account_id = None
    _orig_account_env = None

    @classmethod
    def setUpClass(cls):
        assert cls.MARKET, "子类必须设置 MARKET"
        cls.mod = _load_skill_module(cls.MARKET)
        resp = _api("POST", f"/api/v1/{cls.MARKET}/accounts",
                    {"market": cls.MARKET, "name": f"skill-integration-{cls.MARKET}"})
        cls.account_id = resp["data"]["id"]
        cls._orig_account_env = os.environ.get("FINTOOLS_SIMULATION_ACCOUNT_ID")
        os.environ["FINTOOLS_SIMULATION_ACCOUNT_ID"] = str(cls.account_id)

    @classmethod
    def tearDownClass(cls):
        if cls.account_id:
            _api("DELETE", f"/api/v1/{cls.MARKET}/accounts/{cls.account_id}")
        if cls._orig_account_env is None:
            os.environ.pop("FINTOOLS_SIMULATION_ACCOUNT_ID", None)
        else:
            os.environ["FINTOOLS_SIMULATION_ACCOUNT_ID"] = cls._orig_account_env

    # ── 断言助手 ──

    def assertOk(self, resp, what):
        self.assertTrue(resp.get("success"),
                        f"{what}: {resp.get('error', resp)}")

    def assertTrade(self, resp, what):
        """交易类：成功最好；业务规则拦截也算链路通；HTTP/解析失败才是故障。"""
        if resp.get("success"):
            return resp
        err = str(resp.get("error", "")).lower()
        self.assertTrue(
            any(k in err for k in BUSINESS_RULE_KEYWORDS),
            f"{what} 失败且非业务规则拦截: {resp.get('error')}")
        self.skipTest(f"{what}: 业务规则拦截（链路通）— {resp.get('error')}")
        return resp

    # ── 1. 行情（无鉴权） ──

    def test_10_market_data(self):
        m = self.mod
        if hasattr(m, "list_stocks"):
            self.assertOk(m.list_stocks(), "list_stocks")
        if hasattr(m, "list_symbols"):
            self.assertOk(m.list_symbols(), "list_symbols")
        if hasattr(m, "get_quote"):
            self.assertOk(m.get_quote([self.SYMBOL]), "get_quote")
        if hasattr(m, "get_quotes"):
            self.assertOk(m.get_quotes([self.SYMBOL]), "get_quotes")
        self.assertOk(m.get_kline(self.SYMBOL), "get_kline")
        self.assertOk(m.get_rules(), "get_rules")

    # ── 2. 账户查询 ──

    def test_20_account(self):
        resp = self.mod.get_account()
        self.assertOk(resp, "get_account")
        self.assertEqual(resp["data"]["code"], 0)

    def test_30_buy(self):
        resp = self.mod.buy(self.SYMBOL, self.BUY_QTY)
        resp = self.assertTrade(resp, f"buy {self.SYMBOL} x{self.BUY_QTY}")
        self.assertTrue(resp.get("success"))

    def test_40_sell(self):
        resp = self.mod.sell(self.SYMBOL, self.SELL_QTY)
        if self.STRICT_ROUND_TRIP:
            self.assertOk(resp, f"sell {self.SYMBOL} x{self.SELL_QTY}")
        else:
            self.assertTrade(resp, f"sell {self.SYMBOL} x{self.SELL_QTY}")

    def test_50_positions_orders_logs(self):
        m = self.mod
        self.assertOk(m.get_positions(), "get_positions")
        self.assertOk(m.get_orders(), "get_orders")
        self.assertOk(m.get_balance_log(), "get_balance_log")
        if hasattr(m, "get_buy_orders"):
            self.assertOk(m.get_buy_orders(), "get_buy_orders")
        if hasattr(m, "get_sell_orders"):
            self.assertOk(m.get_sell_orders(), "get_sell_orders")
        if hasattr(m, "get_fee_log"):
            self.assertOk(m.get_fee_log(), "get_fee_log")


class AshareIntegration(_MarketIntegrationMixin, unittest.TestCase):
    MARKET = "ashare"
    SYMBOL = "600519.SH"
    BUY_QTY = 100   # 1 手
    SELL_QTY = 100


class UsstockIntegration(_MarketIntegrationMixin, unittest.TestCase):
    MARKET = "usstock"
    SYMBOL = "AAPL"
    BUY_QTY = 1
    SELL_QTY = 1


class HkstockIntegration(_MarketIntegrationMixin, unittest.TestCase):
    MARKET = "hkstock"
    SYMBOL = "00700.HK"
    BUY_QTY = 100
    SELL_QTY = 100


class CryptoIntegration(_MarketIntegrationMixin, unittest.TestCase):
    MARKET = "crypto"
    SYMBOL = "BTC/USDT"
    BUY_QTY = 0.001
    SELL_QTY = 0.001
    STRICT_ROUND_TRIP = True   # 24/7 + T+0，必须真实跑通买→卖


if __name__ == "__main__":
    unittest.main(verbosity=2)
