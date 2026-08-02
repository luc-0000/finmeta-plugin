"""FinMeta Simulation Trading Skill — A-Share + Crypto + US Stock.

Usage:
    from finmeta_simulation_skill.ashare import buy, get_account
    from finmeta_simulation_skill.crypto import buy as crypto_buy, get_account as crypto_account
    from finmeta_simulation_skill.usstock import buy as usstock_buy, get_account as usstock_account

Or from the top-level:
    from finmeta_simulation_skill import ashare, crypto, usstock
    ashare.buy("600519.SH", 100)
    crypto.buy("BTC/USDT", 0.01)
    usstock.buy("AAPL", 10)
"""

from . import ashare
from . import crypto
from . import usstock

__all__ = ["ashare", "crypto", "usstock"]
