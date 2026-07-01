#!/bin/bash
# 每小时重生 KOL dashboard 雷达图数据并推线上 (期限回填进行中)
# no_agent cron: stdout 有内容才发, 无变化静默
cd /home/user/Projects/Economy-KOL-to-Notion/dashboard/kol-dashboard || exit 1
export TZ='Asia/Tokyo'

# 1. 重生 data.json (从 Notion 拉最新含期限数据)
timeout 300 python3 generate_dashboard_data.py > /tmp/kol_radar_gen.log 2>&1
if [ $? -ne 0 ]; then
    echo "⚠️ generate_dashboard_data.py 失败, 见 /tmp/kol_radar_gen.log"
    tail -5 /tmp/kol_radar_gen.log
    exit 1
fi

# 2. 无变化则静默退出
if git diff --quiet data.json 2>/dev/null; then
    exit 0
fi

# 3. 有变化: commit + push (忽略 git wrapper 的 proto 噪音)
COV=$(cd /home/user/Projects/Economy-KOL-to-Notion && timeout 90 python3 scripts/add_term.py count 2>/dev/null | tail -1)
git add data.json 2>/dev/null
git commit -m "dashboard hourly: 雷达图刷新 ($(date '+%Y-%m-%d %H:%M JST'))" -q 2>/dev/null
PUSH=$(git push origin main 2>&1)
if echo "$PUSH" | grep -qE "rejected|error:|fatal:"; then
    echo "⚠️ git push 失败: $(echo "$PUSH" | grep -E 'rejected|error|fatal' | head -2)"
    exit 1
fi

echo "✅ Dashboard 雷达图已更新 $(date '+%H:%M JST')"
echo "期限覆盖: $COV"
