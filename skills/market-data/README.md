# FinMeta Market Data

Read-only market data (symbols / quotes / kline) for **A-Share**, **US Stock**, **HK Stock**, **Crypto**. Usage and API examples live in `SKILL.md`; this README documents market-specific coverage details.

## HK Stock coverage

HK Stock covers **142 competition symbols only** (from the hk.ai competition list) — **not** the full Hong Kong market. Get the complete, always-current list via the symbols endpoint:

```bash
curl -H "Authorization: Bearer $FINMETA_ACCESS_TOKEN" \
  "https://fin-meta.net/api/v1/public/markets/hkstock/symbols"
```

### Most-traded symbols (a subset, for reference)

| Symbol | Name |
|--------|------|
| 00700.HK | Tencent Holdings |
| 09988.HK | Alibaba Group |
| 03690.HK | Meituan |
| 01810.HK | Xiaomi |
| 00388.HK | Hong Kong Exchanges and Clearing |
| 00005.HK | HSBC Holdings |
| 01299.HK | AIA Group |
| 00939.HK | China Construction Bank |
| 01398.HK | Industrial and Commercial Bank of China |
| 00941.HK | China Mobile |
| 02318.HK | Ping An Insurance |
| 01211.HK | BYD Company |
| 09618.HK | JD.com |
| 09999.HK | NetEase |
| 09888.HK | Baidu |
| 01024.HK | Kuaishou Technology |
| 00981.HK | SMIC |
| 03968.HK | China Merchants Bank |
| 09961.HK | Trip.com Group |
| 09992.HK | Pop Mart |

### Kline refresh

HK Stock kline updates **every 5 minutes** during HK trading hours (09:30–16:00 HKT). `1m` is native; `5m`/`1h`/`1d` are server-aggregated from 1m.
