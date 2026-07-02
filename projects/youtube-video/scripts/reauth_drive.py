#!/usr/bin/env python3
"""
reauth_drive.py — 重新授权 Google Drive 上传 OAuth token

当 ~/.drive-upload-token.json 过期或被撤销时运行本脚本：
  python3 ~/hermesagent/Youtube\ video/reauth_drive.py

浏览器会自动打开授权页面，授权后 token 写入 ~/.drive-upload-token.json
"""

import os
import sys
import glob

# ── 找到 client_secret 文件 ────────────────────────────────────────────────
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
TOKEN_PATH  = os.path.expanduser("~/.drive-upload-token.json")
SCOPES      = ["https://www.googleapis.com/auth/drive.file"]

# 优先使用 910102927961 项目的 client_secret（与 YouTube 同项目）
client_secrets = sorted(glob.glob(os.path.join(SCRIPT_DIR, "client_secret_910102927961*.json")))
if not client_secrets:
    client_secrets = sorted(glob.glob(os.path.join(SCRIPT_DIR, "client_secret*.json")))

if not client_secrets:
    print("❌ 找不到 client_secret_*.json 文件！")
    print(f"   请把 client_secret.json 放到: {SCRIPT_DIR}")
    sys.exit(1)

# 优先用 -q4sjml 那个（Drive 专用，范围更小）
chosen = client_secrets[0]
for cs in client_secrets:
    if "q4sjml" in cs:
        chosen = cs
        break

print(f"使用 client_secret: {os.path.basename(chosen)}")
print(f"Token 将保存到: {TOKEN_PATH}")
print()

try:
    from google_auth_oauthlib.flow import InstalledAppFlow
except ImportError:
    print("❌ 缺少 google-auth-oauthlib，请运行：")
    print("   pip3 install google-auth-oauthlib --break-system-packages")
    sys.exit(1)

print("🌐 正在打开浏览器授权页面...")
print("   请在浏览器中登录你的 Google 账号并点击「允许」")
print()

flow = InstalledAppFlow.from_client_secrets_file(chosen, scopes=SCOPES)
creds = flow.run_local_server(port=0, prompt="consent")

with open(TOKEN_PATH, "w") as f:
    f.write(creds.to_json())

print()
print(f"✅ 授权成功！Token 已保存到 {TOKEN_PATH}")
print()
print("现在可以重新运行 backfill：")
print('  python3 "/Users/chaojin/hermesagent/Youtube video/backfill_drive_assets.py" --max 20')
