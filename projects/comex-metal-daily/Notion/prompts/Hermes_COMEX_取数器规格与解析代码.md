# Hermes COMEX 日报 — 取数器规格 & 解析代码

版本 2026-05-28 · 目标:让现有 GitHub job 在写文件的同时写入"结构化解析数据",Hermes 只读结构化数据做分析并回写分析库。

---

## 0. 核心架构:单写入者原则(回应"双写冲突"担心)

```
                ┌─────────────────────────────────────────┐
   CME 源站 ──► │  GitHub Action(唯一写入者,Linux,有外网)  │
                │  下载文件 → 解析 → 同一行写: 文件 + 结构化字段 │
                └─────────────────────────────────────────┘
                                  │ 写
                                  ▼
        ┌──────────────┬──────────────┬──────────────┬──────────────┐
        │ CME 库存 DB   │   OI DB       │  CFTC DB      │  SLV DB       │  ← 4 张源表
        └──────────────┴──────────────┴──────────────┴──────────────┘
                                  │ 读(Hermes 只读)
                                  ▼
                ┌─────────────────────────────────────────┐
   Hermes ────► │  读结构化数据 → 生成分析 → 写分析库        │
   (每日定时)    │  Delivery Notice & AI Analysis(唯一写入者) │
                └─────────────────────────────────────────┘
```

**规则:**
1. 解析代码**合并进现有 GitHub job**,不另起本地进程。每张源表只有 GitHub 写。
2. Hermes 不写任何源表;只写分析库。任何一张表都不会被两个进程同时写,无竞态、无重复行、无覆盖。
3. 写入按 `Date` 去重/更新已有行(沿用你现有 job 的查重逻辑),解析字段填进同一行。

---

## 1. 各源表要新增/填充的字段

### 1.1 CME 库存 DB(`Daily auto tracking`,每金属每天一行)
现有数字列目前是空的,改为由解析器填:

| Notion 字段 | 类型 | 来源(解析 `<Metal>_stocks.xls`) |
|---|---|---|
| Total Registered | number | 合计行 TOTAL REGISTERED 的 TOTAL TODAY |
| Total Eligible | number | 合计行 TOTAL ELIGIBLE 的 TOTAL TODAY |
| Net Change | number | COMBINED TOTAL 行的 NET CHANGE |
| Reg/Total Ratio | number(%) | Registered /(Registered+Eligible) |
| Activity Note | text | 逐金库当日有变动的活动摘要(见解析器输出) |
| JPM/Asahi etc Stock change | text | 仅 JPM/Asahi 等关键金库的变动(可选) |
| (新增)Parse Status | text | `OK` 或 `PARSE_FAILED:<原因>`,供 Hermes 判断是否可信 |

### 1.2 OI DB(`OI`,每天一行,含期货+期权)
现有只有 File / Option File 两个附件列。新增:

| 新增字段 | 类型 | 来源 |
|---|---|---|
| OI Futures (JSON) | text | Section62 解析出的"按品种×合约月:OI 及变化"紧凑 JSON |
| OI Options (JSON) | text | Section64 解析出的期权 OI 摘要 |
| Parse Status | text | OK / PARSE_FAILED |

### 1.3 CFTC DB(`CFTC Con H`,每周一行)
| 新增字段 | 类型 | 来源 |
|---|---|---|
| COT (JSON) | text | 各品种 生产商/掉期商/管理基金/其他 多空+占比+交易商数+周变化 |
| Parse Status | text | OK / PARSE_FAILED |

### 1.4 SLV DB(`SLV`,iShares,每天一行)
重建坏掉的抓取(原 slv_updater.py 因 iShares 改 JS 渲染失效)。填 `Ounces In trus` / `Shares Outstanding` /(可选 `Price`)。抓取方式见 §4。

---

## 2. 解析器(已用 2026-05-26 真实文件验证)

> 依赖:`pip install xlrd openpyxl pdfplumber`。`.xls` 必须用 `xlrd`(旧二进制),不要用 openpyxl。

### 2.1 库存 xls 解析(✅ 已验证:合计与文件自带 TOTAL 分毫不差)

```python
import xlrd

def parse_stock_xls(path):
    """返回 dict: registered/eligible/combined/net_change/reg_ratio/activity/status"""
    wb = xlrd.open_workbook(path)
    sh = wb.sheet_by_index(0)
    def num(r, c):
        v = sh.cell_value(r, c)
        return v if isinstance(v, (int, float)) else None
    COLS = {'prev':2,'recv':3,'wd':4,'net':5,'adj':6,'today':7}
    data, cur = {}, None
    file_reg = file_elig = file_comb = file_net = None
    for r in range(sh.nrows):
        label = str(sh.cell_value(r,0)).strip()
        if not label:
            continue
        low = label.lower()
        if low in ('registered','eligible','total'):
            data.setdefault(cur, {})[low] = {k: num(r,i) for k,i in COLS.items()}
        elif label.upper().startswith('TOTAL REGISTERED'):
            file_reg = num(r, COLS['today'])
        elif label.upper().startswith('TOTAL ELIGIBLE'):
            file_elig = num(r, COLS['today'])
        elif label.upper().startswith('COMBINED TOTAL'):
            file_comb = num(r, COLS['today']); file_net = num(r, COLS['net'])
        elif label.isupper():           # 金库名(全大写),排除标题行
            if not any(h in low for h in ['commodity','metal depository','troy','silver','gold','copper','platinum','palladium','aluminum','zinc','lead']):
                cur = label
    # 自校验:逐金库累加 == 文件合计行
    sum_reg  = sum((data[d]['registered']['today'] or 0) for d in data if 'registered' in data[d])
    sum_elig = sum((data[d]['eligible']['today']  or 0) for d in data if 'eligible'  in data[d])
    status = 'OK'
    if file_reg and abs(sum_reg - file_reg) > 1:
        status = f'PARSE_FAILED: registered {sum_reg} != file {file_reg}'
    if file_elig and abs(sum_elig - file_elig) > 1:
        status = f'PARSE_FAILED: eligible {sum_elig} != file {file_elig}'
    # 活动摘要:列出当日有 RECEIVED/WITHDRAWN 的金库
    acts = []
    for d in data:
        t = data[d].get('total', {})
        recv, wd = t.get('recv') or 0, t.get('wd') or 0
        if recv or wd:
            net = (t.get('net') or 0)
            acts.append(f"{d}: {'+' if net>=0 else ''}{net:,.0f}(收{recv:,.0f}/提{wd:,.0f})")
    return {
        'registered': file_reg, 'eligible': file_elig, 'combined': file_comb,
        'net_change': file_net,
        'reg_ratio': (file_reg/(file_reg+file_elig)) if (file_reg and file_elig) else None,
        'activity': ' | '.join(acts), 'status': status,
    }
```

### 2.2 交割 Issue & Stop PDF 解析(✅ 已验证:4 合约全部对账成功)

```python
import pdfplumber, re

def parse_issue_stop(path):
    """返回 [{contract, business_date, settlement, mtd, firms:[(code,acct,name,issued,stopped)], status}]"""
    contracts, cur, bdate = [], None, None
    with pdfplumber.open(path) as pdf:
        for p in pdf.pages:
            words = p.extract_words()
            issued_x = stopped_x = None
            for w in words:
                if w['text'] == 'ISSUED':  issued_x  = (w['x0']+w['x1'])/2
                if w['text'] == 'STOPPED': stopped_x = (w['x0']+w['x1'])/2
            lines = {}
            for w in words:
                lines.setdefault(round(w['top']), []).append(w)
            for top in sorted(lines):
                lw = sorted(lines[top], key=lambda x: x['x0'])
                txt = " ".join(w['text'] for w in lw)
                bd = re.search(r'BUSINESS DATE:\s*([\d/]+)', txt)
                if bd: bdate = bd.group(1)
                m = re.match(r'CONTRACT:\s*(.+)', txt)
                if m:
                    cur = {'contract': m.group(1).strip(), 'business_date': bdate,
                           'settlement': None, 'mtd': None, 'firms': [], 'tot': None}
                    contracts.append(cur); continue
                sm = re.match(r'SETTLEMENT:\s*([\d,.]+)', txt)
                if sm and cur: cur['settlement'] = sm.group(1)
                mt = re.match(r'MONTH TO DATE:\s*([\d,]+)', txt)
                if mt and cur: cur['mtd'] = int(mt.group(1).replace(',',''))
                tm = re.match(r'TOTAL:\s*([\d,]+)\s+([\d,]+)', txt)
                if tm and cur:
                    cur['tot'] = (int(tm.group(1).replace(',','')), int(tm.group(2).replace(',','')))
                    continue
                # 席位行: 3位代码 + H/C + 名称 + 数字(按 x 坐标分到 ISSUED/STOPPED)
                if len(lw) >= 3 and re.match(r'^\d{3}$', lw[0]['text']) and lw[1]['text'] in ('H','C') and cur is not None:
                    issued = stopped = 0; namep = []
                    for w in lw[2:]:
                        if re.match(r'^[\d,]+$', w['text']):
                            iv = int(w['text'].replace(',','')); xc = (w['x0']+w['x1'])/2
                            if abs(xc-issued_x) <= abs(xc-stopped_x): issued = iv
                            else: stopped = iv
                        else:
                            namep.append(w['text'])
                    cur['firms'].append((lw[0]['text'], lw[1]['text'], " ".join(namep), issued, stopped))
    # 自校验:逐合约 Issued/Stopped 之和 == 打印 TOTAL
    for c in contracts:
        si = sum(f[3] for f in c['firms']); ss = sum(f[4] for f in c['firms'])
        c['status'] = 'OK' if (c['tot'] and si==c['tot'][0] and ss==c['tot'][1]) else \
                      f'PARSE_FAILED: {si}/{ss} != {c["tot"]}'
    return contracts
```

### 2.3 OI Section62 期货 解析(✅ 已验证:31/32 商品对账成功,UX 铀为非项目品种)

```python
import pdfplumber, re

INT_RE = re.compile(r'^[\d,]+$')

def _tail_oi_chg(toks):
    """从行尾抽 (OI, OI_chg)。支持 UNCH、+/- 独立符号、'<num>+' 粘连符号、单数字TOTAL。"""
    if not toks: return None, None
    if toks[-1] == 'UNCH':
        for t in reversed(toks[:-1]):
            if INT_RE.match(t): return int(t.replace(',','')), 0
        return None, 0
    sm = re.match(r'^([+-])?([\d,]+)$', toks[-1])
    if not sm: return None, None
    chg = int(sm.group(2).replace(',',''))
    if sm.group(1) == '-': chg = -chg
    head = toks[:-1]
    if head:
        gm = re.match(r'^([\d,]+)([+-])$', head[-1])
        if gm: return int(gm.group(1).replace(',','')), chg
    if head and head[-1] in ('+','-'):
        chg = int(toks[-1].replace(',','')) * (1 if head[-1]=='+' else -1)
        head = head[:-1]
    for t in reversed(head):
        if INT_RE.match(t): return int(t.replace(',','')), chg
    return None, chg

def parse_section62(path):
    """返回 {code: {name, months:[{month,oi,oi_chg}], total_oi, total_oi_chg, status}}"""
    with pdfplumber.open(path) as pdf:
        text = "\n".join((p.extract_text() or "") for p in pdf.pages)
    out = {}
    cur = None
    HEAD_RE  = re.compile(r'^([A-Z0-9][A-Z0-9]*)\s+FUT\s+(.+)$')
    TOTAL_RE = re.compile(r'^TOTAL\s+([A-Z0-9][A-Z0-9]*)\s+FUT\b(.*)$')
    MONTH_RE = re.compile(r'^([A-Z]{3}\d{2})\b')
    LTD_TAIL = re.compile(r'^\d{2}/\d{2}')  # LTD 日历行
    for raw in text.split("\n"):
        ln = raw.strip()
        if not ln: continue
        m = TOTAL_RE.match(ln)
        if m:
            code = m.group(1)
            oi, chg = _tail_oi_chg(m.group(2).strip().split())
            if code in out:
                out[code]['total_oi'] = oi; out[code]['total_oi_chg'] = chg
            continue
        m = HEAD_RE.match(ln)
        if m and not ln.startswith('TOTAL'):
            name = m.group(2).strip()
            if LTD_TAIL.match(name):     # LTD 日历,忽略
                continue
            cur = m.group(1)
            entry = out.setdefault(cur, {'name': name, 'months': [], 'total_oi': None, 'total_oi_chg': None, 'status': None})
            entry['name'] = name
            continue
        if cur and MONTH_RE.match(ln):
            toks = ln.split()
            oi, chg = _tail_oi_chg(toks[1:])
            if oi is not None:
                out[cur]['months'].append({'month': toks[0], 'oi': oi, 'oi_chg': chg or 0})
    # 自校验:逐月 OI 之和 == TOTAL OI;逐月 OI变化之和 == TOTAL OI变化
    for code, d in out.items():
        sum_oi  = sum(m['oi']     for m in d['months'])
        sum_chg = sum(m['oi_chg'] for m in d['months'])
        if d['total_oi'] is None:
            d['status'] = f'NO_TOTAL parsed={sum_oi}'
        elif sum_oi == d['total_oi'] and sum_chg == d['total_oi_chg']:
            d['status'] = 'OK'
        else:
            d['status'] = f'PARSE_FAILED parsed={sum_oi}/{sum_chg:+} vs TOTAL={d["total_oi"]}/{d["total_oi_chg"]:+}'
    return out
```

### 2.4 OI Section64 期权 解析(✅ 已验证:28 个有 OI 商品全部抽出,贵金属命名正确)

期权文件无文件级合计,做"按 `<CODE>_<CALL|PUT|OPT>` 聚合 OI/变化"的紧凑摘要。

```python
def parse_section64(path):
    """返回 {f'{code}_{side}': {code, side, name, oi, oi_chg, n_total_rows}}"""
    with pdfplumber.open(path) as pdf:
        text = "\n".join((p.extract_text() or "") for p in pdf.pages)
    out = {}
    cur_key = None
    HEAD_RE = re.compile(r'^([A-Z0-9][A-Z0-9]+)\s+(CALL|PUT|OPT)\s+(.+)$')
    LTD_TAIL = re.compile(r'^\d{2}/\d{2}')
    for raw in text.split("\n"):
        ln = raw.strip()
        if not ln: continue
        m = HEAD_RE.match(ln)
        if m:
            name = m.group(3).strip()
            if LTD_TAIL.match(name): continue
            cur_key = f"{m.group(1)}_{m.group(2)}"
            entry = out.setdefault(cur_key, {'code': m.group(1), 'side': m.group(2),
                                              'name': name, 'oi': 0, 'oi_chg': 0, 'n_total_rows': 0})
            entry['name'] = name
            continue
        if ln.startswith('TOTAL') and cur_key:
            oi, chg = _tail_oi_chg(ln.split()[1:])
            if oi is not None:
                out[cur_key]['oi'] += oi
                out[cur_key]['oi_chg'] += (chg or 0)
                out[cur_key]['n_total_rows'] += 1
    return out
```

### 2.5 CFTC Long Report 解析(✅ 已验证:贵金属+铜 6 商品集中度 100% 正确)

```python
def parse_cftc_long(path):
    """返回 {commodity_name: {exchange, date, oi, positions[11], oi_change, changes[11],
                             percent[11], traders_total, traders[11], concentration[8], status}}
       11 列含义: producer_long, producer_short, swap_long, swap_short, swap_spr,
                  mm_long, mm_short, mm_spr, other_long, other_short, other_spr
       8 列含义:   G4L, G4S, G8L, G8S, N4L, N4S, N8L, N8S  (Gross/Net × 4/8 largest × Long/Short)
    """
    _INT = lambda s: int(s.replace(',','')) if s and re.match(r'^-?[\d,]+$', s) else None
    _FLT = lambda s: float(s)
    with pdfplumber.open(path) as pdf:
        text = "\n".join((p.extract_text() or "") for p in pdf.pages)
    lines = text.split("\n")
    out = {}
    for i, ln in enumerate(lines):
        if 'Disaggregated Commitments of Traders' not in ln or i == 0: continue
        title = lines[i-1].strip()
        tm = re.match(r'^(.+?)\s*-\s*(.+)$', title)
        if not tm: continue
        name = tm.group(1).strip(); exch = tm.group(2).strip()
        date_m = re.search(r'(\w+ \d+, \d{4})', ln)
        e = {'name': name, 'exchange': exch, 'date': date_m.group(1) if date_m else None,
             'oi': None, 'positions': None, 'oi_change': None, 'changes': None,
             'percent': None, 'traders_total': None, 'traders': None, 'concentration': None,
             'status': 'OK'}
        section = None
        for j in range(i+1, min(i+60, len(lines))):
            t = lines[j]
            if 'Disaggregated Commitments of Traders' in t: break
            if 'Positions' in t and section is None: section = 'positions'
            elif 'Changes in Commitments' in t: section = 'changes'
            elif 'Percent of Open Interest Represented by Each' in t: section = 'percent'
            elif 'Number of Traders' in t: section = 'traders'
            elif 'Largest Traders' in t: section = 'concentration'
            m = re.match(r'^\s*All\s*:\s*(.+)$', t)
            if m and section:
                body = m.group(1)
                if section == 'concentration':
                    nums = re.findall(r'-?[\d,]+\.[\d]+|-?[\d,]+', body)
                    e['concentration'] = [_FLT(x) for x in nums]
                else:
                    if ':' in body:
                        pfx, _, dat = body.partition(':'); pfx = pfx.strip(); dat = dat.strip()
                    else: pfx, dat = None, body
                    nums = re.findall(r'-?[\d,]+\.[\d]+|-?[\d,]+', dat)
                    if section == 'positions':
                        e['oi'] = _INT(pfx); e['positions'] = [_INT(x) for x in nums]
                    elif section == 'percent':
                        e['percent'] = [_FLT(x) for x in nums]
                    elif section == 'traders':
                        e['traders_total'] = _INT(pfx); e['traders'] = [_INT(x) for x in nums]
            if section == 'changes' and e['changes'] is None:
                cm = re.match(r'^\s*:\s*(-?[\d,]+)\s*:\s*(.+)$', t)
                if cm:
                    e['oi_change'] = _INT(cm.group(1))
                    nums = re.findall(r'-?[\d,]+', cm.group(2))
                    e['changes'] = [_INT(x) for x in nums[:11]]
        # 关键字段校验(positions=11, changes=11, concentration=8 必须齐);traders 列数不齐只是 warning
        errs = []
        if e['positions'] is None or len(e['positions']) != 11: errs.append(f'pos={len(e["positions"] or [])}')
        if e['changes']    is None or len(e['changes'])    != 11: errs.append(f'chg={len(e["changes"] or [])}')
        if e['concentration'] is None or len(e['concentration']) != 8: errs.append(f'conc={len(e["concentration"] or [])}')
        if errs: e['status'] = 'PARSE_FAILED: ' + ' '.join(errs)
        out[name] = e
    return out
```

**验证结果汇总(2026-05-26/27 真实文件):**

| 解析器 | 商品数 | 关键字段 OK | 备注 |
|---|---|---|---|
| `parse_stock_xls` | — | ✅ 合计行对账精确 | Silver 已验证;Gold/Platinum/Palladium 等同格式可直接用 |
| `parse_issue_stop` | 4 合约 | ✅ 全部 Issued/Stopped 对账 | Gold/Silver/Copper/Palladium |
| `parse_section62` | 31/32 | ✅ 贵金属+铜 100% OK | UX(铀)非本项目品种 |
| `parse_section64` | 28 | ✅ 贵金属+铜命名+OI 正确 | 期权无文件级合计,逐商品聚合 |
| `parse_cftc_long` | 47 | ✅ 贵金属+铜 6 商品集中度 100% | 部分小品种 traders 列数不齐(非关键) |

---

## 3. 失败处理(回应"格式变化"担心)

1. 每支解析器都返回 `status`;只要 `!= OK`,GitHub job **不要写入数字字段**(避免脏数据污染),只把 `Parse Status` 写成 `PARSE_FAILED:<原因>`,并保留原始文件附件不变。
2. Hermes 每日读到 `PARSE_FAILED` 时,在分析里明确标注"某数据当日解析失败、未采用",绝不臆造数字。
3. 修复闭环:你把当天那份新格式文件丢进 Hermes 对话 → Hermes 诊断并改写对应解析函数 → 回灌进 GitHub job。CME 公报格式稳定,触发概率低;iShares 抓取最易变。

---

## 4. iShares SLV 重建

原脚本用 `requests+BeautifulSoup` 抓 `ishares.com/.../239855` 页面里的 "Ounces in Trust"/"Shares Outstanding",因页面改 JS 渲染而失效。重建二选一:
- **首选**:调用 iShares 的结构化数据接口(产品页背后的 AJAX/JSON 下载端点)直接拿 Ounces/Shares,稳定不依赖 DOM 文案。
- 兜底:用无头浏览器渲染后再取。
写入 SLV DB 时沿用按 `Date` 去重。注意原脚本只做 SLV(白银),若要 GLD 需另确认具体黄金 ETF。

---

## 5. Hermes 侧(读 + 写,无需改动源表写入)

每日定时:读 4 张源表当日(CFTC 当周)结构化字段 → 生成分析(Issue&Stop 席位穿透、OI 异动、库存 Eligible/Registered 失血、SIFO 温差等)→ 写入 `Delivery Notice & AI Analysis`:
- 短评写进 `Hermes Analysis ` 列(**注意列名带尾随空格**)。
- 完整分析写进该行的 detail page。
- 按 `Date` 去重。
```
