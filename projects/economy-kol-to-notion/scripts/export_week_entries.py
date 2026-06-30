#!/usr/bin/env python3
"""导出指定缺口周的 By Day 原始观点，供周报生成（子agent）读取。
用法: python3 export_week_entries.py  -> 生成 data/week_backfill/<year>-W<wk>.json
覆盖所有缺口周（By Day 有数据但 By Week 没有的周）。
"""
import json, urllib.request, datetime, os
from collections import defaultdict

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
env = {}
for l in open(os.path.join(BASE, 'config/.env')):
    if '=' in l and not l.strip().startswith('#'):
        k, v = l.strip().split('=', 1); env[k] = v
ids = json.load(open(os.path.join(BASE, 'config/notion_ids.json')))
TOK = env['NOTION_TOKEN']; DAY = ids['kol_by_day_database_id']; WK = ids['kol_by_week_database_id']
H = {'Authorization': 'Bearer ' + TOK, 'Notion-Version': '2022-06-28', 'Content-Type': 'application/json'}

def txt(p):
    t = p.get('type')
    if t == 'title': return ''.join(x['plain_text'] for x in p['title'])
    if t == 'rich_text': return ''.join(x['plain_text'] for x in p['rich_text'])
    if t == 'select': return (p['select'] or {}).get('name', '')
    if t == 'number': return p['number']
    if t == 'date': return (p['date'] or {}).get('start', '')
    return ''

def query_all(db):
    cursor = None; out = []
    while True:
        body = {'page_size': 100}
        if cursor: body['start_cursor'] = cursor
        req = urllib.request.Request('https://api.notion.com/v1/databases/' + db + '/query',
                                     data=json.dumps(body).encode(), headers=H, method='POST')
        res = json.load(urllib.request.urlopen(req))
        out += res['results']
        if not res['has_more']: break
        cursor = res['next_cursor']
    return out

# 1. existing By Week weeks
wk_rows = query_all(WK)
existing_weeks = set()
for r in wk_rows:
    n = txt(r['properties'].get('Week Number', {}))
    d = txt(r['properties'].get('Date', {}))
    if d:
        y, m, dd = map(int, d[:10].split('-'))
        iso = datetime.date(y, m, dd).isocalendar()
        existing_weeks.add((iso[0], iso[1]))
print('Existing By Week weeks:', sorted(existing_weeks))

# 2. all By Day entries grouped by ISO week
day_rows = query_all(DAY)
weeks = defaultdict(list)
for r in day_rows:
    pr = r['properties']
    d = txt(pr.get('Date', {}))
    if not d: continue
    try:
        y, m, dd = map(int, d[:10].split('-'))
        iso = datetime.date(y, m, dd).isocalendar()
    except Exception:
        continue
    # collect KOL name property (title is likely Key Insight; KOL name is a select 'Name of KOL')
    kol = ''
    for cand in ['Name of KOL', 'KOL', 'Name']:
        if cand in pr and txt(pr[cand]): kol = txt(pr[cand]); break
    weeks[(iso[0], iso[1])].append({
        'date': d[:10],
        'kol': kol,
        'sector': txt(pr.get('Sector', {})),
        'detail_sector': txt(pr.get('Detail Sector', {})),
        'kol_or_ib': txt(pr.get('KOL or IB View', {})),
        'key_insight': txt(pr.get('Key Insight', {})),
        'comments': txt(pr.get('Comments', {})),
        'targets': txt(pr.get('多空标的', {})),
        'suggestion': txt(pr.get('Suggestion', {})),
    })

# 3. gap weeks = has By Day but not in By Week
gap_weeks = sorted([w for w in weeks if w not in existing_weeks])
outdir = os.path.join(BASE, 'data/week_backfill')
os.makedirs(outdir, exist_ok=True)
summary = []
for w in gap_weeks:
    y, wn = w
    entries = sorted(weeks[w], key=lambda e: e['date'])
    # week start (Monday) date for the Date field
    monday = datetime.date.fromisocalendar(y, wn, 1)
    fn = os.path.join(outdir, f'{y}-W{wn:02d}.json')
    json.dump({'year': y, 'week': wn, 'week_start': monday.isoformat(),
               'entry_count': len(entries), 'entries': entries},
              open(fn, 'w'), ensure_ascii=False, indent=2)
    summary.append((f'{y}-W{wn:02d}', monday.isoformat(), len(entries)))

print(f'\n=== Gap weeks exported: {len(gap_weeks)} ===')
for s in summary:
    print(f'  {s[0]} (start {s[1]}): {s[2]} entries -> {s[0]}.json')
json.dump({'gap_weeks': [f'{y}-W{wn:02d}' for (y, wn) in gap_weeks],
           'existing_weeks': sorted([f'{y}-W{wn:02d}' for (y, wn) in existing_weeks])},
          open(os.path.join(outdir, '_index.json'), 'w'), ensure_ascii=False, indent=2)
print('\nIndex written to data/week_backfill/_index.json')
