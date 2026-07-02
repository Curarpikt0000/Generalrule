# US Debt & Fed Liquidity Daily Report
# 美债收益率和Fed中美日流动性日报

## Project Overview

Automated daily report pipeline: scrapes US Treasury yield, Fed liquidity, BoJ/PBoC/MoF data → writes to 13 Notion databases → AI analysis via Hermes (DeepSeek backend).

## Notion Databases (13 DBs, 2 Pages)

### Page A — 美债收益率和Fed流动性 (US Treasury & Fed Liquidity)
| ID | Name | Description |
|----|------|-------------|
| A1 | 美债收益率曲线 | US Treasury yield curve data |
| A2 | Fed 资产负债表规模 | Fed balance sheet size (rebuilt V7) |
| A3 | 美联储缩表进度 | Fed QT progress tracker |
| A4 | Fed 流动性工具使用 | Fed liquidity facility usage (rebuilt V7) |
| A5 | SOFR / EFFR | Overnight rates |
| A6 | ⚠️ **DEPRECATED — in Recycle Bin** | Replaced by B7 |
| A7 | AI 综合分析 | AI-generated daily commentary + analysis |

### Page B — 中日流动性 (China & Japan Liquidity)
| ID | Name | Description |
|----|------|-------------|
| B1 | 中国央行 OMO | PBoC open market operations |
| B2 | 中国10年国债收益率 | China 10Y bond yield |
| B3 | BoJ 利率决议 | BoJ policy rate decisions |
| B4 | 日本10年国债收益率 | Japan 10Y JGB yield |
| B5 | 资产负债表快照 — PBoC | PBoC balance sheet snapshot (monthly) |
| B6 | 资产负债表快照 — Fed | Fed H.4.1 balance sheet snapshot (weekly) |
| B7 | 资产负债表快照 — BoJ | BoJ balance sheet snapshot (10-day) — *also replaces A6* |

## Workflows (7 Hermes Cron Jobs)

| # | Name | Schedule (JST) | Description |
|---|------|----------------|-------------|
| 01 | Morning US Data | 07:30 | FRED yield + Fed balance sheet scrape |
| 02 | Morning JGB Data | 07:45 | MoF Japan + BoJ scrape |
| 03 | Morning AI Analysis | 08:00 | Hermes writes A7 morning analysis |
| 04 | Noon China+Japan | ~12:00 | PBoC OMO + China yield scrape |
| 05 | Noon AI Analysis | ~12:30 | Hermes writes B-side analysis |
| 06 | Weekly Fed H.4.1 | Thursday | Fed balance sheet weekly refresh |
| 07 | Monthly CB Balance | Month-end | Central bank monthly snapshot |

## External Services

| Service | Usage | Notes |
|---------|-------|-------|
| FRED API | US Treasury yields, balance sheet, SOFR | Free API key; rate limit: `sleep(2)` between calls |
| MoF Japan | JGB yield CSV (`jgbcme.csv`) | English site; **not** `jgbcm.csv` |
| BoJ | Policy rate, JGB purchases, TONAR, FX | Official website scraping |
| PBoC | OMO operations | GBK-encoded static HTML |
| Investing.com | Anti-scrape fallback | Aggressive WAF; MoF preferred |

## Key Lessons Learned

1. **A6 in Recycle Bin**: Original A6 DB cannot be recovered from trash. Replaced by B7 (BoJ balance sheet), which now serves double duty.
2. **A2/A4 Rebuilt (V7)**: Both DBs were accidentally lost in trash. Rebuilt with schema upgrades (added scale/status light fields).
3. **DS API vs DB API Version Differences**: Notion MCP date field format requires explicit `"date:Date:start"` + `"date:Date:is_datetime": 0`. Rich text body has specific `type` nesting rules.
4. **Status Light Enums**: Must match exact emoji + text (e.g. `🟢正常` ≠ `🟢` ≠ `正常`). Not select fields case-sensitive.
5. **FRED 429 Rate Limit**: Concurrent series fetch causes 429 errors. Fixed by sequential calls with `sleep(2)`.
6. **PBoC GBK Encoding**: Must set `r.encoding = 'gbk'` before BeautifulSoup parsing.
7. **Hermes Non-JSON Output**: Must try/catch + retry with lower temperature; if still fails, write `❌失败` to A7.

## Configuration

See `config.env.example` for API key templates (no real tokens included):

```bash
FRED_API_KEY=         # Fred API key (required)
DEEPSEEK_API_KEY=     # DeepSeek platform key (required)
NOTION_TOKEN=         # Notion Integration token
DEEPSEEK_MODEL=deepseek-chat
LOG_LEVEL=INFO
TIMEZONE=Asia/Tokyo
```

## Directory Structure

```
/tmp/us-debt-docker/
├── README.md                    # This file
├── context-log.md               # Project context snapshot
├── AGENTS.md                    # Project rules (constraints)
├── PROPOSAL.md                  # Design document
├── DEPLOYMENT.md                # Deployment instructions
├── HERMES_WORKER_BOOTSTRAP.md   # Hermes worker setup
├── notion_db_ids.json            # 13 Notion DB ID index
├── config.py                    # Loads env vars
├── config.env.example           # API key template (no real tokens)
├── scrapers/                    # 7 Python scrapers
├── scripts/                     # 3 helper scripts
├── notion_writer/               # Notion MCP call wrapper
├── hermes_workflows/            # 7 Hermes workflow prompts (.md)
├── hermes_analysis_prompts/     # 2 AI role prompts (.md)
├── tasks/                       # Project tasks + lessons
├── cron/                        # Cron job configurations
└── docs/                        # Additional docs
```
