# finmeta-plugin

A Claude Code **plugin** that bundles FinMeta client skills.

## Skills

| Skill | What it does | Credits |
|-------|-------------|---------|
| `finmeta-plugin` (root) | **Token setup** — SSOT for `FINMETA_ACCESS_TOKEN` | — |
| `market-data` | Symbols / quotes / kline (A-Share, US Stock, Crypto) | Free |
| `finmeta-simulation-skill` | Simulation trading — accounts, positions, orders | Free |
| `invoke-api-agent` | Call API agents (`type=api`) | Per-call |
| `finmeta-task-agent` | Call Task agents via A2A | Per-call |

> All 4 functional skills share the same `FINMETA_ACCESS_TOKEN` — managed centrally by the root `finmeta-plugin` setup skill.

## Structure

```
finmeta-plugin/
├── SKILL.md                ← plugin-level token setup (SSOT)
├── README.md
├── .claude-plugin/
│   ├── plugin.json          ← plugin 清单（name/version/description）
│   └── marketplace.json     ← marketplace 目录（GitHub 安装用）
└── skills/
    └── finmeta-simulation-skill/
        ├── SKILL.md          ← skill 定义（frontmatter name+description + 指令）
        ├── README.md         ← skill 详细用法
        ├── ashare/  crypto/  usstock/   ← 三市 api.py + api_reference.md
        └── ...
```

**关键点：**
- `.claude-plugin/plugin.json` 是 plugin 的**身份标识**（有它这个目录才算 plugin）。`name` 决定命名空间。
- `skills/` 下每个**子目录**是一个 skill（靠 `SKILL.md` 定义）。plugin 装 5 个 skill（1 个 plugin 级 token setup + 4 个功能 skill）。
- Skill 调用名带命名空间 `/finmeta-plugin:skill-name`。
- 组件都在**插件根**（不在 `.claude-plugin/` 里）。

## 安装

### 本地开发（临时试）
```bash
claude --plugin-dir /Users/lu/development/fintools_all/skills/finmeta-plugin
```
只对本次会话生效，原地读、不复制。改了文件 `/reload-plugins` 或重启。

### 从 GitHub 安装（给最终用户）
repo 需 `.claude-plugin/` 下**两个**文件（本 plugin 都备好）：`plugin.json` + `marketplace.json`。把 repo 推 GitHub 后，用户在 Claude Code 会话里：
```bash
/plugin marketplace add <owner>/finmeta-plugin       # 一次性注册 marketplace
/plugin install finmeta-plugin@finmeta-plugins       # 装（插件名@marketplace名）
/reload-plugins                                       # 当场生效，不用重启
```
然后：
```
/finmeta-plugin:finmeta-simulation-skill             # 用 skill（命名空间前缀）
```
public repo 用户无需 token；更新走 `/plugin marketplace update finmeta-plugins`。

## 怎么用（装上后）
**先设 token**：触发 `finmeta-plugin` setup skill 设置 `FINMETA_ACCESS_TOKEN`。

然后触发目标 skill，按对应 SKILL.md 的指引调用。简例：
```bash
curl -H "Authorization: Bearer $FINMETA_ACCESS_TOKEN" \
  "https://fin-meta.net/api/v1/public/markets/ashare/quotes?symbols=600519.SH"
```

## plugin 机制速记
- **plugin = 打包/分发/命名空间**这一层；skill 才是能力单元。
- 装上后 plugin 里所有 skill 的 `name`+`description` 进 context（正文懒加载），靠 description 匹配任务。
- skill 调用名带命名空间 `/插件名:skill名`，避免多 plugin 同名冲突。
- 想让某 skill 不被自动触发：frontmatter 加 `disable-model-invocation: true`。

## 扩展
- 新功能 → 独立 skill 的判据：**触发词 / auth / 受众 / 生命周期**不同就拆。在 `skills/` 下加个子目录即可。
- 例如行情只读（免 auth，走 `/public/markets`）可做成另一个 skill，跟 auth 的交易 skill 分开。
