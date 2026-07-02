#!/usr/bin/env python3
"""
Query Notion data_sources for CME inventory.
Usage:
  python3 query_cme_inventory.py [metal] [days_back]
  python3 query_cme_inventory.py Silver 30
  python3 query_cme_inventory.py Gold 7
  python3 query_cme_inventory.py Platinum 14

Metal options: Gold, Silver, Platinum, Palladium (default: Silver)
Days back from today (default: 30)
"""

import requests, json, sys, datetime

NOTION_TOKEN = os.environ.get('NOTION_TOKEN', '')  # 从 .hermes/.env 获取

# DS ID for CME inventory Daily auto tracking
CME_DS_ID = '2e047eb5-fd3c-8034-a672-000be7162cff'

metal = sys.argv[1] if len(sys.argv) > 1 else 'Silver'
days = int(sys.argv[2]) if len(sys.argv) > 2 else 30

start_date = (datetime.date.today() - datetime.timedelta(days=days)).isoformat()

headers = {
    'Authorization': f'Bearer {NOTION_TOKEN}',
    'Notion-Version': '2025-09-03',
    'Content-Type': 'application/json'
}

payload = {
    'filter': {
        'and': [
            {'property': 'Metal Type', 'select': {'equals': metal}},
            {'property': 'Date', 'date': {'on_or_after': start_date}}
        ]
    },
    'sorts': [{'property': 'Date', 'direction': 'ascending'}],
    'page_size': 100
}

resp = requests.post(f'https://api.notion.com/v1/data_sources/{CME_DS_ID}/query', headers=headers, json=payload)
data = resp.json()
results = data.get('results', [])

print(f'{metal} inventory: {len(results)} rows from {start_date}')
print()

for r in results:
    props = r.get('properties', {})
    date = props.get('Date', {}).get('date', {}).get('start', '?')
    reg = props.get('Total Registered', {}).get('number', '')
    elig = props.get('Total Eligible', {}).get('number', '')
    net = props.get('Net Change', {}).get('number', '')
    ratio = props.get('Reg/Total Ratio', {}).get('number', '')
    combined = props.get('Combined Total', {}).get('number', '')

    reg_str = f'{reg:,.0f}' if isinstance(reg, (int, float)) else ''
    elig_str = f'{elig:,.0f}' if isinstance(elig, (int, float)) else ''
    net_str = f'{net:+,.0f}' if isinstance(net, (int, float)) else ''
    ratio_str = f'{ratio*100:.1f}%' if isinstance(ratio, (int, float)) else ''
    comb_str = f'{combined:,.0f}' if isinstance(combined, (int, float)) else ''

    print(f'{date:<14s} Reg={reg_str:<20s} Elig={elig_str:<20s} Net={net_str:<15s} Ratio={ratio_str:<8s} Comb={comb_str}')
