#!/usr/bin/env python3
"""给 KOL List 的 page 正文写入丰富的结构化背景+历史言论汇总。
用 Notion blocks: callout/heading/bulleted_list/quote/divider 分层, 非纯 text。
CLI: python3 write_kol_profile.py <json_file>
json 格式:
{
  "page_id": "...",          # KOL List 的 page id
  "display_name": "Luke Gromen",
  "one_liner": "FFTT创始人, 石油美元体系瓦解论旗手",   # callout 一句话定位
  "identity": ["机构/头衔", "履历亮点", ...],          # 身份背景 bullets
  "framework": ["核心分析框架点1", ...],               # 分析框架 bullets
  "core_views": ["长期核心立场1(中文)", ...],          # 长期立场 bullets
  "recent_summary": "近期(过去半年)观点演变汇总段落",   # 段落
  "stance": "持仓派/交易派 + 一句话",                  # 派别
  "key_assets": "🟢 黄金 GLD BTC | 🔴 美元 TLT"        # 常提标的
}
幂等: 写入前先清空该 page 现有 children(避免重复追加)。
"""
import json, sys, urllib.request, urllib.error, time

def lk(n):
    p=n+"="
    for l in open("config/.env"):
        if l.startswith(p): return l[len(p):].strip()
TOK=lk("NOTION_"+"TOKEN")
H={"Authorization":f"Bearer {TOK}","Notion-Version":"2022-06-28","Content-Type":"application/json"}

def api(method,url,body=None):
    data=json.dumps(body).encode() if body is not None else None
    req=urllib.request.Request(url,data=data,headers=H,method=method)
    for a in range(3):
        try: return json.load(urllib.request.urlopen(req,timeout=45))
        except urllib.error.HTTPError as e:
            m=e.read().decode()[:200]
            if e.code==429 and a<2: time.sleep(2*(a+1)); continue
            raise RuntimeError(f"HTTP {e.code}: {m}")

def rt(text):
    return [{"type":"text","text":{"content":text[:2000]}}]

def clear_children(pid):
    r=api("GET",f"https://api.notion.com/v1/blocks/{pid}/children?page_size=100")
    for b in r.get("results",[]):
        try: api("DELETE",f"https://api.notion.com/v1/blocks/{b['id']}")
        except: pass

def build_blocks(d):
    B=[]
    # 顶部 callout: 一句话定位
    B.append({"object":"block","type":"callout","callout":{
        "rich_text":rt(d["one_liner"]),"icon":{"emoji":"🎯"},"color":"blue_background"}})
    # 派别 + 常提标的 callout
    if d.get("stance") or d.get("key_assets"):
        line=[]
        if d.get("stance"): line.append("【派别】"+d["stance"])
        if d.get("key_assets"): line.append("【常提标的】"+d["key_assets"])
        B.append({"object":"block","type":"callout","callout":{
            "rich_text":rt("  ".join(line)),"icon":{"emoji":"⚖️"},"color":"gray_background"}})
    # 身份背景
    if d.get("identity"):
        B.append({"object":"block","type":"heading_3","heading_3":{"rich_text":rt("👤 身份与背景")}})
        for x in d["identity"]:
            B.append({"object":"block","type":"bulleted_list_item","bulleted_list_item":{"rich_text":rt(x)}})
    # 分析框架
    if d.get("framework"):
        B.append({"object":"block","type":"heading_3","heading_3":{"rich_text":rt("🧭 核心分析框架")}})
        for x in d["framework"]:
            B.append({"object":"block","type":"bulleted_list_item","bulleted_list_item":{"rich_text":rt(x)}})
    # 长期核心立场
    if d.get("core_views"):
        B.append({"object":"block","type":"heading_3","heading_3":{"rich_text":rt("📌 长期核心立场")}})
        for x in d["core_views"]:
            B.append({"object":"block","type":"bulleted_list_item","bulleted_list_item":{"rich_text":rt(x)}})
    # 近期观点演变
    if d.get("recent_summary"):
        B.append({"object":"block","type":"heading_3","heading_3":{"rich_text":rt("📈 近期观点演变(过去半年)")}})
        B.append({"object":"block","type":"quote","quote":{"rich_text":rt(d["recent_summary"])}})
    return B

def write_profile(d):
    pid=d["page_id"]
    clear_children(pid)
    blocks=build_blocks(d)
    # Notion 一次最多 100 blocks
    for i in range(0,len(blocks),50):
        api("PATCH",f"https://api.notion.com/v1/blocks/{pid}/children",{"children":blocks[i:i+50]})
    return {"status":"OK","blocks":len(blocks),"page_id":pid}

if __name__=="__main__":
    d=json.load(open(sys.argv[1]))
    print(json.dumps(write_profile(d),ensure_ascii=False))
