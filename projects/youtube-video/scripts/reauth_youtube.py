#!/usr/bin/env python3
"""
reauth_youtube.py — 重新授权 YouTube OAuth Token

当 ~/.youtube-mcp/token.json 出现 invalid_grant 时运行此脚本。
会打开浏览器让你重新登录 Google，授权后自动保存新 token。

用法：
    python3 reauth_youtube.py
"""

import json, os, sys

# ── 路径 ──────────────────────────────────────────────────────────────────────
CLIENT_SECRET = os.path.expanduser(
    "~/hermesagent/Youtube video/"
    "client_secret_825033890920-1h4sd9fgomqo80s05uoepelvl8ab5g44.apps.googleusercontent.com.json"
)
TOKEN_OUT = os.path.expanduser("~/.youtube-mcp/token.json")

SCOPES = [
    "https://www.googleapis.com/auth/youtube",
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube.force-ssl",
]

# ── 安装检查 ──────────────────────────────────────────────────────────────────
try:
    from google_auth_oauthlib.flow import InstalledAppFlow
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
except ImportError:
    print("❌ 缺少依赖，请先运行：")
    print("   pip3 install google-auth google-auth-oauthlib google-api-python-client")
    sys.exit(1)

# ── 主流程 ─────────────────────────────────────────────────────────────────────
def main():
    if not os.path.exists(CLIENT_SECRET):
        print(f"❌ 找不到 client_secret 文件：{CLIENT_SECRET}")
        sys.exit(1)

    print("🔑 启动 YouTube OAuth 授权流程...")
    print("   浏览器将自动打开，请用你的 Google 账号登录并授权。")
    print()

    flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRET, scopes=SCOPES)
    creds = flow.run_local_server(port=0, open_browser=True)

    # 保存 token
    os.makedirs(os.path.dirname(TOKEN_OUT), exist_ok=True)
    token_data = {
        "token":         creds.token,
        "refresh_token": creds.refresh_token,
        "token_uri":     creds.token_uri,
        "client_id":     creds.client_id,
        "client_secret": creds.client_secret,
        "scopes":        list(creds.scopes) if creds.scopes else SCOPES,
        "expiry":        creds.expiry.isoformat() if creds.expiry else None,
    }
    with open(TOKEN_OUT, "w") as f:
        json.dump(token_data, f, indent=2)

    print(f"✅ 新 token 已保存到：{TOKEN_OUT}")
    print(f"   refresh_token: {'✓ 存在' if creds.refresh_token else '❌ 缺失！'}")
    print()
    print("现在可以重新运行 QC 脚本：")
    print("   python3 youtubevideoQC.py --reupload-video --max 30")

if __name__ == "__main__":
    main()
