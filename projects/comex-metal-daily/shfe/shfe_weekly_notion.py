#!/usr/bin/env python3
"""
SHFE 库存周报 → Notion 写入器
被 cron 调用：抓取数据 → 写入 Notion Gold DB / Silver DB
"""

import asyncio
import json
import sys
import os
from datetime import datetime, timedelta

# 添加项目路径
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SCRIPT_DIR)

from shfe_weekly_stock import get_weekly_stock


def notion_upsert(notion_api_key: str, db_id: str, properties: dict, name_filter: str) -> dict:
    """Notion upsert: 按 name 查询 → 存在则 PATCH，不存在则 POST"""
    import requests
    
    headers = {
        "Authorization": f"Bearer {notion_api_key}",
        "Content-Type": "application/json",
        "Notion-Version": "2022-06-28"
    }
    
    # 查询
    query_url = f"https://api.notion.com/v1/databases/{db_id}/query"
    query_data = {
        "filter": {"property": "Name", "title": {"equals": name_filter}}
    }
    resp = requests.post(query_url, headers=headers, json=query_data)
    resp.raise_for_status()
    existing = resp.json().get("results", [])
    
    if existing:
        # 更新
        page_id = existing[0]["id"]
        update_url = f"https://api.notion.com/v1/pages/{page_id}"
        resp = requests.patch(update_url, headers=headers, json={"properties": properties})
        resp.raise_for_status()
        return {"action": "updated", "page_id": page_id}
    else:
        # 创建
        create_url = "https://api.notion.com/v1/pages"
        create_data = {
            "parent": {"database_id": db_id},
            "properties": properties
        }
        resp = requests.post(create_url, headers=headers, json=create_data)
        resp.raise_for_status()
        return {"action": "created", "page_id": resp.json()["id"]}


def write_to_notion(data: dict, date_str: str, notion_key: str):
    """
    将抓取的数据写入 Notion DB
    Gold DB: 2bc47eb5-fd3c-8083-966e-ecfd9f396b44
    Silver DB: 2bc47eb5-fd3c-80f3-a71a-d8de149a4943
    """
    results = []
    
    if data.get("gold"):
        gold = data["gold"]
        name = f"Gold SHFE {date_str[:4]}-{date_str[4:6]}-{date_str[6:]}"
        props = {
            "Name": {"title": [{"text": {"content": name}}]},
            "Gold日期": {"date": {"start": f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:]}"}},
            "市场": {"select": {"name": "SHFE"}},
            "库存频率": {"select": {"name": "每周"}},
            "SH库存吨": {"number": gold["本周库存_吨"]},
            "URL": {"url": "https://www.shfe.com.cn/reports/tradedata/dailyandweeklydata/"},
            "说明": {"rich_text": [{"text": {"content": f"SHFE 沪金周库存(Hermes自动抓取),增减 {gold['增减_吨']} 吨"}}]}
        }
        r = notion_upsert(notion_key, "2bc47eb5-fd3c-8083-966e-ecfd9f396b44", props, name)
        results.append({"db": "Gold", **r})
    
    if data.get("silver"):
        silver = data["silver"]
        name = f"Silver SHFE {date_str[:4]}-{date_str[4:6]}-{date_str[6:]}"
        props = {
            "Name": {"title": [{"text": {"content": name}}]},
            "Silver日期": {"date": {"start": f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:]}"}},
            "市场": {"select": {"name": "SHFE"}},
            "库存频率": {"select": {"name": "每周"}},
            "SH库存吨": {"number": silver["本周库存_吨"]},
            "URL": {"url": "https://www.shfe.com.cn/reports/tradedata/dailyandweeklydata/"},
            "说明": {"rich_text": [{"text": {"content": f"SHFE 沪银周库存(Hermes自动抓取),增减 {silver['增减_吨']} 吨"}}]}
        }
        r = notion_upsert(notion_key, "2bc47eb5-fd3c-80f3-a71a-d8de149a4943", props, name)
        results.append({"db": "Silver", **r})
    
    return results


async def main():
    # 获取日期参数
    if len(sys.argv) > 1:
        date_str = sys.argv[1]
    else:
        today = datetime.now()
        days_to_friday = (today.weekday() - 4) % 7
        last_friday = today - timedelta(days=days_to_friday)
        if today.weekday() == 4:
            last_friday = today
        date_str = last_friday.strftime('%Y%m%d')
    
    # 获取 Notion API Key
    notion_key = os.environ.get("NOTION_API_KEY") or os.environ.get("NOTION_TOKEN")
    if not notion_key:
        print(json.dumps({"error": "NOTION_API_KEY 或 NOTION_TOKEN 环境变量未设置"}))
        sys.exit(1)
    
    print(f"抓取 {date_str} SHFE 库存周报...", file=sys.stderr)
    data = await get_weekly_stock(date_str)
    
    if "error" in data:
        print(json.dumps(data))
        sys.exit(1)
    
    print(f"黄金: {data['gold']['本周库存_吨']} 吨" if data.get("gold") else "黄金: 无数据", file=sys.stderr)
    print(f"白银: {data['silver']['本周库存_吨']} 吨" if data.get("silver") else "白银: 无数据", file=sys.stderr)
    
    # 写入 Notion
    results = write_to_notion(data, date_str, notion_key)
    
    output = {
        "date": date_str,
        "data": data,
        "notion_results": results
    }
    print(json.dumps(output, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    asyncio.run(main())
