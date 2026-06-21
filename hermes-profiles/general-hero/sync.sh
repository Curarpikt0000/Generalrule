#!/bin/bash
# 把蓝图（本目录）同步到 general profile，并重启网关让改动生效。
#
# 用法：
#   cd ~/hermesagent/Distill/蒸馏Hermes/general-hero && ./sync.sh
#
# 纪律：永远改蓝图 → 跑这个脚本，不要直接改 ~/.hermes/profiles/general/
# 上游：General Global Rule §2.5（显式暴露冲突，拒绝折中调和）

set -euo pipefail

BLUEPRINT="$(cd "$(dirname "$0")" && pwd)"
TARGET="$HOME/.hermes/profiles/general"

if [ ! -d "$TARGET" ]; then
  echo "❌ profile 目录不存在：$TARGET"
  echo "   先跑：hermes profile create general"
  exit 1
fi

echo "==> 蓝图：$BLUEPRINT"
echo "==> 目标：$TARGET"
echo ""

# 同步三块：SOUL / skills / references
# rsync --exclude 跳过毛泽东 repo 的 Python 工具 / 开发文档 / 测试数据（噪音，部署到 profile 里没必要）

echo "[1/4] 同步 SOUL.md"
cp "$BLUEPRINT/SOUL.md" "$TARGET/SOUL.md"

echo "[2/4] 同步 skills/（9 位大师；bundled skills 不受影响）"
rsync -a \
  --exclude='.git' --exclude='.github' \
  --exclude='internal/' --exclude='tools/' \
  --exclude='docs/' --exclude='prompts/' --exclude='data/' \
  --exclude='*.py' --exclude='requirements.txt' \
  --exclude='*.pyc' --exclude='__pycache__/' \
  --exclude='CHANGELOG.md' --exclude='CONTRIBUTING.md' \
  --exclude='README.de.md' --exclude='README.es.md' --exclude='README.ja.md' --exclude='README.ko.md' --exclude='README.en.md' \
  "$BLUEPRINT/skills/" "$TARGET/skills/"

echo "[3/4] 同步 references/"
mkdir -p "$TARGET/references"
rsync -a --delete "$BLUEPRINT/references/" "$TARGET/references/"

echo "[4/4] 重启 general gateway"
# Hermes 自带 launchd 集成；kickstart 让 launchd 重启 gateway 进程但保留服务定义
launchctl kickstart -k "gui/$(id -u)/ai.hermes.gateway-general" 2>/dev/null || {
  # 如果 launchd 服务未加载，回退到 manual start
  general gateway stop 2>/dev/null || true
  sleep 1
  general gateway start
}

echo ""
echo "✅ 同步完成。Telegram 里 @ GeneralHeroBot 测一句话验证。"
