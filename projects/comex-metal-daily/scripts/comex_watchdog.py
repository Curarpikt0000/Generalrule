#!/usr/bin/env python3
"""
COMEX Daily Report Watchdog — 独立看门狗
每天22:30 JST运行,检查当天是否有新报告写入Notion Delivery Notice & AI Analysis库。
如果没有(说明Hermes cron没触发),通过Telegram Bot API发送⚠️报警。
与Hermes gateway完全独立(不同进程树),gateway挂了也不影响它。

部署: launchd plist (com.chaojin.comex-watchdog.plist)
"""
import os
import sys
import json
import urllib.request
from datetime import datetime, timezone, timedelta

JST = timezone(timedelta(hours=9))

NOTION_TOKEN = os.environ["NOTION_TOKEN"]  # 从 plist EnvironmentVariables 读,不进代码
DB_ID = "2be47eb5-fd3c-80ba-b065-f188139834b9"

# --- Telegram Bot 告警 ---
TELEGRAM_BOT_TOKEN = os.environ.get("HERMES_TELEGRAM_TOKEN", "")
TELEGRAM_CHAT_ID = os.environ.get("WATCHDOG_ALERT_CHAT_ID", "-1003946549077")  # Hermes工程师Group
TELEGRAM_THREAD_ID = "7535"  # 当前对话thread

def send_telegram_alert(message: str):
    """通过Telegram Bot API发消息"""
    if not TELEGRAM_BOT_TOKEN:
        print("⚠️ TELEGRAM_BOT_TOKEN not set, cannot send alert")
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = json.dumps({
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "Markdown",
        "message_thread_id": TELEGRAM_THREAD_ID
    }).encode("utf-8")
    req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
    try:
        resp = urllib.request.urlopen(req, timeout=15)
        print(f"Telegram alert sent: {resp.status}")
    except Exception as e:
        print(f"Telegram send failed: {e}")

def query_notion_today():
    """查询Notion分析库,看今天有没有新写入"""
    today = datetime.now(JST).strftime("%Y-%m-%d")
    yesterday = (datetime.now(JST) - timedelta(days=1)).strftime("%Y-%m-%d")

    # 先搜今天
    payload = json.dumps({
        "filter": {
            "and": [
                {"property": "Date", "date": {"on_or_after": today}},
                {"property": "Date", "date": {"on_or_before": today}}
            ]
        },
        "sorts": [{"property": "Date", "direction": "descending"}],
        "page_size": 5
    }).encode("utf-8")

    req = urllib.request.Request(
        f"https://api.notion.com/v1/databases/{DB_ID}/query",
        data=payload,
        headers={
            "Authorization": f"Bearer {NOTION_TOKEN}",
            "Notion-Version": "2022-06-28",
            "Content-Type": "application/json"
        }
    )

    try:
        resp = urllib.request.urlopen(req, timeout=15)
        data = json.loads(resp.read())
        results = data.get("results", [])

        if results:
            # 如果有Hermes Analysis内容则算成功
            for page in results:
                props = page.get("properties", {})
                hermes_analysis = props.get("Hermes Analysis ", {}).get("rich_text", [])
                if hermes_analysis and hermes_analysis[0].get("text", {}).get("content", "").strip():
                    print(f"✅ {today}: Found report with analysis text")
                    return "found_today"

        print(f"⚠️ {today}: No reports found. Trying {yesterday}...")
    except Exception as e:
        print(f"Error querying today: {e}")

    # 搜昨天(可能是因为时区差异,22:00 JST = 13:00 UTC, 可能前一天)
    payload2 = json.dumps({
        "filter": {
            "and": [
                {"property": "Date", "date": {"on_or_after": yesterday}},
                {"property": "Date", "date": {"on_or_before": yesterday}}
            ]
        },
        "sorts": [{"property": "Date", "direction": "descending"}],
        "page_size": 5
    }).encode("utf-8")

    req2 = urllib.request.Request(
        f"https://api.notion.com/v1/databases/{DB_ID}/query",
        data=payload2,
        headers={
            "Authorization": f"Bearer {NOTION_TOKEN}",
            "Notion-Version": "2022-06-28",
            "Content-Type": "application/json"
        }
    )

    try:
        resp2 = urllib.request.urlopen(req2, timeout=15)
        data2 = json.loads(resp2.read())
        results2 = data2.get("results", [])

        if results2:
            for page in results2:
                props = page.get("properties", {})
                hermes_analysis = props.get("Hermes Analysis ", {}).get("rich_text", [])
                if hermes_analysis and hermes_analysis[0].get("text", {}).get("content", "").strip():
                    print(f"✅ {yesterday}: Found yesterday's report with analysis text")
                    return "found_yesterday"

        print(f"❌ {today} AND {yesterday}: No reports found!")
        return "missing"
    except Exception as e:
        print(f"Error querying yesterday: {e}")
        return "error"

def main():
    # 周末不检查
    today_weekday = datetime.now(JST).weekday()
    if today_weekday in (5, 6):  # Sat/Sun
        print("Weekend, skipping check")
        return

    status = query_notion_today()

    if status == "missing":
        today_str = datetime.now(JST).strftime("%Y-%m-%d")
        msg = (
            f"⚠️ **COMEX日报看门狗告警**\n"
            f"检测时间: {datetime.now(JST).strftime('%Y-%m-%d %H:%M JST')}\n"
            f"状态: 当日({today_str})及前一工作日均未发现有效报告\n\n"
            f"可能原因: Hermes cron未触发 / gateway宕机 / Notion连接失败\n"
            f"请检查: `hermes cron list` 或 gateway日志"
        )
        send_telegram_alert(msg)
        print("Alert sent!")
    elif status == "error":
        print("Query error, no alert sent (avoid false positives from transient issues)")
    else:
        print("All good, no alert needed")

if __name__ == "__main__":
    main()
