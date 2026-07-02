# US Debt & Fed Liquidity — Cron Job Configuration
# Generated from Hermes cronjob list

# --- Cron Job Summary ---

## Job 1: US Debt 项目上下文快照压缩
#   job_id: 23bf49d38e04
#   name: US Debt 项目上下文快照压缩 - 每晚
#   schedule: 45 2 * * * (every night at 02:45 JST)
#   last_status: ok (2026-07-02)
#   deliver: local (writes to docs/context-log.md)
#   workdir: "/Users/chaojin/hermesagent/US Debt and Fed Liquidity/美债收益率和Fed中美日流动性日报"
#   prompt: Search recent (3-day) sessions related to US Debt project, extract key context, update docs/context-log.md
#   model: system default (no override)

# Deployment notes:
# - This is a context-compression job that runs nightly
# - All 7 workflow prompts live in hermes_workflows/ (01-07)
# - All 2 AI analysis role prompts live in hermes_analysis_prompts/
# - Primary data pipeline: scrapers/ → notion_writer/ → hermes analysis prompts
# - The context-log.md in docs/ is updated nightly by the cron job
