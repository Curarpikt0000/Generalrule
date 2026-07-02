#!/usr/bin/env python3
"""
SHFE 库存周报抓取脚本
使用 Playwright (stealth) 绕过 WAF，抓取 SHFE 指定日期的库存周报数据
输出：JSON 格式的 Au + Ag 库存数据
"""

import asyncio
import json
import sys
import re
from datetime import datetime, timedelta

from playwright.async_api import async_playwright
from playwright_stealth import Stealth
from bs4 import BeautifulSoup


async def get_weekly_stock(date_str: str) -> dict:
    """
    抓取指定日期的 SHFE 库存周报
    date_str: YYYYMMDD 格式的日期（必须是周五/交易日）
    返回: { "gold": {"品种":"黄金","单位":"千克","上周库存":X,"本周库存":X,"增减":X}, 
             "silver": {"品种":"白银","单位":"千克","上周库存":X,"本周库存":X,"增减":X} }
    """
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=['--no-sandbox', '--disable-blink-features=AutomationControlled']
        )
        context = await browser.new_context(
            user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            viewport={'width': 1920, 'height': 1080},
            locale='zh-CN'
        )
        page = await context.new_page()
        stealth = Stealth()
        await stealth.apply_stealth_async(page)

        try:
            # 访问页面
            await page.goto('https://www.shfe.com.cn/reports/tradedata/dailyandweeklydata/',
                            wait_until='networkidle', timeout=30000)
            await asyncio.sleep(3)

            # 检查是否被 WAF 拦截
            content = await page.content()
            if 'WEB 应用防火墙' in content:
                # 等待 JS 挑战
                await asyncio.sleep(8)
                content = await page.content()
                if 'WEB 应用防火墙' in content:
                    raise Exception("WAF 拦截，无法获取数据")

            # 设置目标日期（可能需要翻月历）
            target_year = date_str[:4]
            target_month = str(int(date_str[4:6]))
            
            # 读取当前月历
            cal_title = await page.evaluate('() => document.querySelector(".el-calendar__title")?.textContent || ""')
            
            # 如果需要切换月份，点击上个月/下个月
            max_clicks = 12  # 最多翻12个月
            for _ in range(max_clicks):
                cal_title = await page.evaluate('() => document.querySelector(".el-calendar__title")?.textContent || ""')
                if f'{target_year} 年 {target_month} 月' in cal_title:
                    break
                # 如果目标月份比当前早，点"上个月"
                if int(date_str) < int(datetime.now().strftime('%Y%m%d')):
                    try:
                        await page.click('text=上个月')
                        await asyncio.sleep(0.5)
                    except:
                        break
                else:
                    try:
                        await page.click('text=下个月')
                        await asyncio.sleep(0.5)
                    except:
                        break

            # 设置 Vue 的 currentDate
            await page.evaluate(f'''() => {{
                const app = document.querySelector("#js_page")?.__vue__;
                if (app) app.currentDate = "{date_str}";
            }}''')

            # 点击"库存周报" tab
            await page.click('#weeklystock')
            await asyncio.sleep(5)

            # 获取数据 HTML
            full_html = await page.evaluate('''() => {
                const el = document.querySelector('#daily_stock_html');
                return el ? el.innerHTML : '';
            }''')

            if not full_html:
                raise Exception("无法获取库存周报数据 HTML")

        except Exception as e:
            raise e
        finally:
            await browser.close()

    # 解析 HTML 提取黄金和白银数据
    return parse_weekly_stock_html(full_html, date_str)


def parse_weekly_stock_html(html: str, date_str: str) -> dict:
    """解析库存周报 HTML，提取黄金和白银数据"""
    soup = BeautifulSoup(html, 'html.parser')
    tables = soup.find_all('table')
    
    result = {
        "日期": date_str,
        "来源": "SHFE 上海期货交易所",
        "gold": None,
        "silver": None
    }

    # 遍历所有 table，找黄金和白银
    for i, table in enumerate(tables):
        text = table.get_text()
        
        # 黄金 - 汇总表（3列：上周库存、本周库存、库存增减）
        if ('黄金' in text and '单位' in text and '千克' in text and 
            '上周库存' in text and '本周库存' in text):
            rows = table.find_all('tr')
            for row in rows:
                cells = [c.get_text(strip=True) for c in row.find_all(['td', 'th'])]
                if len(cells) >= 3 and cells[0] == '黄金':
                    # 下一行是数据行
                    continue
                if len(cells) >= 3 and all(c.replace('.','',1).replace('-','',1).isdigit() for c in cells[:3]):
                    result["gold"] = {
                        "品种": "黄金",
                        "单位": "千克",
                        "上周库存": int(cells[0].replace(',', '')),
                        "本周库存": int(cells[1].replace(',', '')),
                        "增减": int(cells[2].replace(',', '')),
                        "日期": date_str
                    }
                    # 添加吨位换算
                    result["gold"]["上周库存_吨"] = round(result["gold"]["上周库存"] / 1000, 3)
                    result["gold"]["本周库存_吨"] = round(result["gold"]["本周库存"] / 1000, 3)
                    result["gold"]["增减_吨"] = round(result["gold"]["增减"] / 1000, 3)
                    break

        # 白银 - 明细表（有总计行）
        if ('白银' in text and '单位' in text and '千克' in text and '总计' in text):
            rows = table.find_all('tr')
            for row in rows:
                cells = [c.get_text(strip=True) for c in row.find_all(['td', 'th'])]
                # 总计行: ['总计', last_week, this_week, change, ...]
                if len(cells) >= 4 and cells[0] == '总计':
                    last_week = int(cells[1].replace(',', ''))
                    this_week = int(cells[2].replace(',', ''))
                    change = int(cells[3].replace(',', ''))
                    result["silver"] = {
                        "品种": "白银",
                        "单位": "千克",
                        "上周库存": last_week,
                        "本周库存": this_week,
                        "增减": change,
                        "日期": date_str
                    }
                    result["silver"]["上周库存_吨"] = round(last_week / 1000, 3)
                    result["silver"]["本周库存_吨"] = round(this_week / 1000, 3)
                    result["silver"]["增减_吨"] = round(change / 1000, 3)
                    break
        
        if result["gold"] and result["silver"]:
            break

    return result


async def main():
    # 从命令行参数获取日期，默认最新周五
    if len(sys.argv) > 1:
        date_str = sys.argv[1]
    else:
        # 默认取最近的周五
        today = datetime.now()
        # 找最近的周五
        days_to_friday = (today.weekday() - 4) % 7
        last_friday = today - timedelta(days=days_to_friday)
        # 如果今天就是周五，用今天
        if today.weekday() == 4:
            last_friday = today
        date_str = last_friday.strftime('%Y%m%d')
    
    print(f"正在抓取 {date_str} 的 SHFE 库存周报...", file=sys.stderr)
    
    try:
        result = await get_weekly_stock(date_str)
        print(json.dumps(result, ensure_ascii=False, indent=2))
    except Exception as e:
        print(json.dumps({"error": str(e), "date": date_str}, ensure_ascii=False))
        sys.exit(1)


if __name__ == '__main__':
    asyncio.run(main())
