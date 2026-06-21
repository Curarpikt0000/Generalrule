#!/bin/bash
# 把蓝图（本目录）同步到 finance profile，并重启网关让改动生效。
#
# 用法：
#   cd ~/hermesagent/Distill/蒸馏Hermes/finance-hero && ./sync.sh
#
# 纪律：永远改蓝图 → 跑这个脚本，不要直接改 ~/.hermes/profiles/finance/
# 上游：General Global Rule §2.5（显式暴露冲突，拒绝折中调和）

set -euo pipefail

BLUEPRINT="$(cd "$(dirname "$0")" && pwd)"
TARGET="$HOME/.hermes/profiles/finance"

if [ ! -d "$TARGET" ]; then
  echo "❌ profile 目录不存在：$TARGET"
  echo "   先跑：hermes profile create finance"
  exit 1
fi

echo "==> 蓝图：$BLUEPRINT"
echo "==> 目标：$TARGET"
echo ""

# 同步几块，不删除 profile 里 Hermes 自己生成的东西（如 87 个 bundled skills、config.yaml、.env）
echo "[1/5] 同步 SOUL.md"
cp "$BLUEPRINT/SOUL.md" "$TARGET/SOUL.md"

echo "[2/5] 同步 skills/（7 位大师；bundled skills 不受影响）"
rsync -a "$BLUEPRINT/skills/" "$TARGET/skills/"

echo "[3/5] 同步 references/"
mkdir -p "$TARGET/references"
rsync -a --delete "$BLUEPRINT/references/" "$TARGET/references/"

echo "[4/5] 同步 tools/（按需工具：moomoo helper / Google Finance 二次验证脚本）"
mkdir -p "$TARGET/tools"
rsync -a --delete --exclude='.placeholder' "$BLUEPRINT/tools/" "$TARGET/tools/"
# 保留执行权限
find "$TARGET/tools" -name '*.py' -exec chmod +x {} \;

echo "[5/5] 重启 finance gateway"
launchctl kickstart -k "gui/$(id -u)/ai.hermes.gateway-finance" 2>/dev/null || {
  finance gateway stop 2>/dev/null || true
  sleep 1
  finance gateway start &
}
sleep 2

echo ""
echo "✅ 同步完成。Telegram 里 @ FiHeroBot 测一句话验证。"
