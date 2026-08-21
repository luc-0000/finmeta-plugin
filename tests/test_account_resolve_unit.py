"""Unit: finmeta-simulation-skill 账户解析（_pick/_ensure/_no_account_error）。

2026-08-21 修复的回归守卫（四个市场统一行为）：
- config 残留旧 token 用户的 account_id → 名单校验归属 + 清残留自愈（换 token 后
  首次调用即恢复，不再 404 死锁）
- auto-create 建盘成功后写回 config（此前 hkstock 建了 4056 但没存，每次都重新解析）
- ashare _require_account_id 硬退出 sys.exit(1) → 软化：读操作无盘时返回
  success=False + 提示传入最新模拟盘号，不杀进程

纯 mock（_get/_post/临时 config 文件），不发网络请求。
"""
import importlib.util
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

SKILL_ROOT = Path(__file__).resolve().parents[1] / "skills" / "finmeta-simulation-skill"
MARKETS = ["ashare", "hkstock", "usstock", "crypto"]


def _load(market):
    spec = importlib.util.spec_from_file_location(
        f"resolve_{market}", SKILL_ROOT / market / "api.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _list_resp(accounts):
    return {"success": True, "data": {"data": {"accounts": accounts}}}


class AccountResolveUnitTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.cfg_path = Path(self._tmp.name) / "config.json"

    def tearDown(self):
        self._tmp.cleanup()

    def _mod(self, market, accounts_cfg=None):
        """加载 market 模块，ACCOUNTS_FILE 指向临时 config（含假 token）。"""
        mod = _load(market)
        mod.ACCOUNTS_FILE = self.cfg_path
        cfg = {"access_token": "unit-test-token"}
        if accounts_cfg is not None:
            cfg["accounts"] = accounts_cfg
        self.cfg_path.write_text(json.dumps(cfg))
        return mod

    def _no_env(self):
        # _load_account_id 优先读环境变量 — 测试里清掉，保证走 config 分支
        return patch.dict(os.environ)

    def test_stale_config_id_cleared_and_falls_back(self):
        """config id 不在名下（旧 token 残留）→ 清除 + 改用名下个人盘。"""
        for market in MARKETS:
            with self.subTest(market=market):
                mod = self._mod(market, {market: 26})
                with patch.object(mod, "_get",
                                  return_value=_list_resp([{"id": 4056, "competition_id": None}])), \
                     self._no_env():
                    os.environ.pop("FINTOOLS_SIMULATION_ACCOUNT_ID", None)
                    self.assertEqual(mod._pick_account_id(), 4056, market)
                cfg = json.loads(self.cfg_path.read_text())
                self.assertNotIn(market, cfg.get("accounts", {}),
                                 f"{market}: stale id 必须从 config 清除")

    def test_owned_config_id_returned_as_is(self):
        """config id 在名下 → 原样返回，不动 config。"""
        for market in MARKETS:
            with self.subTest(market=market):
                mod = self._mod(market, {market: 4056})
                with patch.object(mod, "_get",
                                  return_value=_list_resp([{"id": 4056, "competition_id": None}])), \
                     self._no_env():
                    os.environ.pop("FINTOOLS_SIMULATION_ACCOUNT_ID", None)
                    self.assertEqual(mod._pick_account_id(), 4056, market)
                cfg = json.loads(self.cfg_path.read_text())
                self.assertEqual(cfg.get("accounts", {}).get(market), 4056)

    def test_list_failure_keeps_config_id(self):
        """名单接口挂了 → 不误清 config（网络问题 ≠ 残留）。"""
        for market in MARKETS:
            with self.subTest(market=market):
                mod = self._mod(market, {market: 26})
                with patch.object(mod, "_get",
                                  return_value={"success": False, "error": "boom"}), \
                     self._no_env():
                    os.environ.pop("FINTOOLS_SIMULATION_ACCOUNT_ID", None)
                    self.assertEqual(mod._pick_account_id(), 26, market)
                cfg = json.loads(self.cfg_path.read_text())
                self.assertEqual(cfg.get("accounts", {}).get(market), 26)

    def test_ensure_autocreates_and_saves_to_config(self):
        """名下无盘 → 下单路径 auto-create，且新盘号写回 config。"""
        for market in MARKETS:
            with self.subTest(market=market):
                mod = self._mod(market)  # 无 accounts
                with patch.object(mod, "_get", return_value=_list_resp([])), \
                     patch.object(mod, "_post",
                                  return_value={"success": True,
                                                "data": {"data": {"id": 4242}}}), \
                     self._no_env():
                    os.environ.pop("FINTOOLS_SIMULATION_ACCOUNT_ID", None)
                    self.assertEqual(mod._ensure_account_id(), 4242, market)
                cfg = json.loads(self.cfg_path.read_text())
                self.assertEqual(cfg.get("accounts", {}).get(market), 4242,
                                 f"{market}: auto-create 的盘号必须写回 config")

    def test_personal_account_preferred_over_competition(self):
        """优先个人盘（competition_id=None），无个人盘才落到比赛盘。"""
        for market in MARKETS:
            with self.subTest(market=market):
                mod = self._mod(market)
                with patch.object(mod, "_get", return_value=_list_resp(
                        [{"id": 7, "competition_id": 3}, {"id": 9, "competition_id": None}])), \
                     self._no_env():
                    os.environ.pop("FINTOOLS_SIMULATION_ACCOUNT_ID", None)
                    self.assertEqual(mod._pick_account_id(), 9, market)

    def test_read_without_account_returns_hint_not_exit(self):
        """无盘可解析时读操作返回 success=False + 提示最新盘号（ashare 不得 sys.exit）。"""
        for market in MARKETS:
            with self.subTest(market=market):
                mod = self._mod(market)  # 无 accounts
                with patch.object(mod, "_get",
                                  return_value={"success": False, "error": "boom"}), \
                     self._no_env():
                    os.environ.pop("FINTOOLS_SIMULATION_ACCOUNT_ID", None)
                    result = mod.get_positions()
                self.assertFalse(result.get("success"), market)
                self.assertIn("--account-id", result.get("error", ""), market)


if __name__ == "__main__":
    unittest.main(verbosity=2)
