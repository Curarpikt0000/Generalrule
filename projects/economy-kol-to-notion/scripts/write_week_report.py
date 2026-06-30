#!/usr/bin/env python3
"""By Week 周报写入库。供子agent调用，或命令行单测。
用法(命令行测试): python3 write_week_report.py <path-to-report-json>
report-json 格式:
{
  "year":2025,"week":44,"week_start":"2025-10-27",
  "sector":"Multi-Asset",            # 主导sector(select)
  "key_insight":"W44 ...（2025-10-27）",
  "comments":"【贵金属】... 【宏观】...",
  "targets":"🟢 GLD(...)... | 🔴 TLT(...)...",
  "suggestion":"建议增配..."
}
幂等: 若该 Week Number 已存在则跳过(不重复写)。select 字段写入前合并现有 options。
"""
import json, urllib.request, os, sys

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
env = {}
for l in open(os.path.join(BASE, 'config/.env')):
    if '=' in l and not l.strip().startswith('#'):
        k, v = l.strip().split('=', 1); env[k] = v
ids = json.load(open(os.path.join(BASE, 'config/notion_ids.json')))
TOK = env['NOTION_TOKEN']; WK = ids['kol_by_week_database_id']
H = {'Authorization': 'Bearer ' + TOK, 'Notion-Version': '2022-06-28', 'Content-Type': 'application/json'}

def _txt(p):
    t = p.get('type')
    if t == 'number': return p['number']
    if t == 'date': return (p['date'] or {}).get('start', '')
    return ''

def existing_week_numbers():
    cursor = None; nums = set()
    while True:
        body = {'page_size': 100}
        if cursor: body['start_cursor'] = cursor
        req = urllib.request.Request('https://api.notion.com/v1/databases/' + WK + '/query',
                                     data=json.dumps(body).encode(), headers=H, method='POST')
        res = json.load(urllib.request.urlopen(req))
        for r in res['results']:
            n = _txt(r['properties'].get('Week Number', {}))
            if n is not None: nums.add(int(n))
        if not res['has_more']: break
        cursor = res['next_cursor']
    return nums

def rt(s):
    """rich_text payload, split into <=2000 char chunks (Notion limit)."""
    s = s or ''
    chunks = [s[i:i+1900] for i in range(0, len(s), 1900)] or ['']
    return [{'type': 'text', 'text': {'content': c}} for c in chunks]

def write_report(rep, week_number_override=None):
    wn = int(week_number_override if week_number_override is not None else rep['week'])
    existing = existing_week_numbers()
    if wn in existing:
        return {'skipped': True, 'reason': f'Week Number {wn} already exists', 'week': wn}
    props = {
        'Key Insight': {'title': rt(rep['key_insight'])},
        'Week Number': {'number': wn},
        'Date': {'date': {'start': rep['week_start']}},
        'Comments': {'rich_text': rt(rep.get('comments', ''))},
        '多空标的': {'rich_text': rt(rep.get('targets', ''))},
        'Suggestion': {'rich_text': rt(rep.get('suggestion', ''))},
    }
    if rep.get('sector'):
        props['Sector'] = {'select': {'name': rep['sector']}}
    if rep.get('detail_sector'):
        props['Detail Sector'] = {'select': {'name': rep['detail_sector']}}
    body = {'parent': {'database_id': WK}, 'properties': props}
    req = urllib.request.Request('https://api.notion.com/v1/pages',
                                 data=json.dumps(body).encode(), headers=H, method='POST')
    res = json.load(urllib.request.urlopen(req))
    return {'skipped': False, 'page_id': res['id'], 'week': wn}

if __name__ == '__main__':
    rep = json.load(open(sys.argv[1]))
    wno = int(sys.argv[2]) if len(sys.argv) > 2 else None
    print(json.dumps(write_report(rep, wno), ensure_ascii=False, indent=2))
