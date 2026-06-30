import json, urllib.request, time
import urllib.error
def lk(n):
    p=n+"="
    for l in open("config/.env"):
        if l.startswith(p): return l[len(p):].strip()
tok=lk("NOTION_"+"TOKEN")
H={"Authorization":f"Bearer {tok}","Notion-Version":"2022-06-28","Content-Type":"application/json"}
DB="32347eb5fd3c8087b9c0f409f95f664e"

# 查每个 registry KOL 在 2025-11-01~2026-03-13 空白期是否有记录(证明已回溯)
reg=json.load(open("data/kol_registry.json"))
done=[]; todo=[]
for k in reg["kols"]:
    name=k["notion_select_name"]
    body={"filter":{"and":[
        {"property":"Name of KOL","select":{"equals":name}},
        {"property":"Date","date":{"on_or_before":"2026-03-13"}},
    ]},"page_size":1}
    try:
        r=json.load(urllib.request.urlopen(urllib.request.Request(
            f"https://api.notion.com/v1/databases/{DB}/query",
            data=json.dumps(body).encode(),headers=H,method="POST"),timeout=30))
        if r["results"]:
            done.append(k["id"])
        else:
            todo.append(k["id"])
    except urllib.error.HTTPError:
        # select option 不存在 = 从没写过 = 待回溯
        todo.append(k["id"])
    time.sleep(0.15)

print(f"已有空白期回溯数据: {len(done)} 个")
print(f"待回溯(空白期无数据): {len(todo)} 个")
print("\n待回溯 id:")
for i in range(0,len(todo),4):
    print("  ", todo[i:i+4])
json.dump(todo, open("data/still_todo.json","w"))
