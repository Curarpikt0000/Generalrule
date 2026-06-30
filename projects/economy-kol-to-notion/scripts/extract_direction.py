#!/usr/bin/env python3
"""方向提取处理库 — 供方向回填子agent使用。
功能:
  list_batch(offset,limit)  -> 导出一批 By Day 记录的待判断数据(id/date/kol/sector/comments/多空标的/key_insight)
  write_direction(page_id, detail_list, dominant, targets_str, std_sector) -> 回填:
      方向明细(JSON) + 主导方向(select) + 多空标的(补全,可选) + Sector(标准化)
detail_list 格式: [{"标的":"美债","板块":"Government Debt","方向":"看空"}, ...]
  板块必须是7标准之一; 方向必须是: 强烈看多/看多/中性/看空/强烈看空/分歧
dominant: 整条记录主导方向(6档之一), 取该KOL本条最强/最主要的方向
命令行:
  python3 extract_direction.py list <offset> <limit>      # 打印一批待判断JSON
  python3 extract_direction.py count                      # 总记录数 + 已处理数(有方向明细的)
"""
import json, urllib.request, os, sys, time

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
env = {}
for l in open(os.path.join(BASE, 'config/.env')):
    if '=' in l and not l.strip().startswith('#'):
        k, v = l.strip().split('=', 1); env[k] = v
ids = json.load(open(os.path.join(BASE, 'config/notion_ids.json')))
TOK = env['NOTION_TOKEN']; DAY = ids['kol_by_day_database_id']
H = {'Authorization': 'Bearer ' + TOK, 'Notion-Version': '2022-06-28', 'Content-Type': 'application/json'}
SECMAP = json.load(open(os.path.join(BASE, 'config/sector_standard_map.json')))
STD_SECTORS = set(SECMAP['standard_sectors'])
VALID_DIR = {'强烈看多', '看多', '中性', '看空', '强烈看空', '分歧'}

def _txt(p):
    t = p.get('type')
    if t == 'select': return (p['select'] or {}).get('name', '')
    if t == 'rich_text': return ''.join(x['plain_text'] for x in p['rich_text'])
    if t == 'title': return ''.join(x['plain_text'] for x in p['title'])
    if t == 'date': return (p['date'] or {}).get('start', '')
    return ''

def _query_all():
    cur = None; out = []
    while True:
        b = {'page_size': 100}
        if cur: b['start_cursor'] = cur
        req = urllib.request.Request('https://api.notion.com/v1/databases/' + DAY + '/query',
                                     data=json.dumps(b).encode(), headers=H, method='POST')
        r = json.load(urllib.request.urlopen(req)); out += r['results']
        if not r['has_more']: break
        cur = r['next_cursor']
    return out

def list_batch(offset, limit):
    rows = _query_all()
    rows.sort(key=lambda r: (_txt(r['properties'].get('Date', {})), r['id']))
    batch = rows[offset:offset+limit]
    out = []
    for r in batch:
        pr = r['properties']
        out.append({
            'id': r['id'],
            'date': _txt(pr.get('Date', {})),
            'kol': _txt(pr.get('Name of KOL', {})),
            'raw_sector': _txt(pr.get('Sector', {})),
            'key_insight': _txt(pr.get('Key Insight', {})),
            'comments': _txt(pr.get('Comments', {})),
            '多空标的_now': _txt(pr.get('多空标的', {})),
            'has_direction': bool(_txt(pr.get('方向明细', {})).strip()),
        })
    return out

def count():
    rows = _query_all()
    done = sum(1 for r in rows if _txt(r['properties'].get('方向明细', {})).strip())
    return {'total': len(rows), 'with_direction': done, 'remaining': len(rows) - done}

def write_direction(page_id, detail_list, dominant, targets_str=None, std_sector=None):
    # validate
    for d in detail_list:
        if d.get('板块') not in STD_SECTORS:
            raise ValueError('bad 板块: %r (must be one of %s)' % (d.get('板块'), STD_SECTORS))
        if d.get('方向') not in VALID_DIR:
            raise ValueError('bad 方向: %r' % d.get('方向'))
    if dominant not in VALID_DIR:
        raise ValueError('bad dominant: %r' % dominant)
    detail_json = json.dumps(detail_list, ensure_ascii=False)
    props = {
        '方向明细': {'rich_text': [{'type': 'text', 'text': {'content': detail_json[:1990]}}]},
        '主导方向': {'select': {'name': dominant}},
    }
    if targets_str is not None and targets_str.strip():
        props['多空标的'] = {'rich_text': [{'type': 'text', 'text': {'content': targets_str[:1990]}}]}
    if std_sector:
        if std_sector not in STD_SECTORS:
            raise ValueError('bad std_sector: %r' % std_sector)
        props['Sector'] = {'select': {'name': std_sector}}
    body = {'properties': props}
    req = urllib.request.Request('https://api.notion.com/v1/pages/' + page_id,
                                 data=json.dumps(body).encode(), headers=H, method='PATCH')
    json.load(urllib.request.urlopen(req))
    return {'ok': True, 'page_id': page_id, 'n_targets': len(detail_list), 'dominant': dominant}

def next_unfilled(limit):
    """返回下一批【未回填方向明细】的记录(按日期排序)。供cron滚动处理。"""
    rows = _query_all()
    rows.sort(key=lambda r: (_txt(r['properties'].get('Date', {})), r['id']))
    out = []
    for r in rows:
        if _txt(r['properties'].get('方向明细', {})).strip():
            continue
        pr = r['properties']
        out.append({
            'id': r['id'], 'date': _txt(pr.get('Date', {})),
            'kol': _txt(pr.get('Name of KOL', {})), 'raw_sector': _txt(pr.get('Sector', {})),
            'key_insight': _txt(pr.get('Key Insight', {})), 'comments': _txt(pr.get('Comments', {})),
            '多空标的_now': _txt(pr.get('多空标的', {})),
        })
        if len(out) >= limit:
            break
    return out

if __name__ == '__main__':
    cmd = sys.argv[1] if len(sys.argv) > 1 else 'count'
    if cmd == 'count':
        print(json.dumps(count(), ensure_ascii=False))
    elif cmd == 'list':
        off = int(sys.argv[2]); lim = int(sys.argv[3])
        print(json.dumps(list_batch(off, lim), ensure_ascii=False, indent=2))
    elif cmd == 'next':
        lim = int(sys.argv[2]) if len(sys.argv) > 2 else 60
        print(json.dumps(next_unfilled(lim), ensure_ascii=False, indent=2))
