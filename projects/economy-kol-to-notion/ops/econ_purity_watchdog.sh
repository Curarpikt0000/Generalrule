#!/bin/bash
# Economy-KOL 数据脱敏污染每日体检 watchdog
# 干净则静默(无输出, cron 不投递); 有污染才输出告警
cd /home/user/Projects/Economy-KOL-to-Notion || exit 1
/usr/bin/python3 scripts/purity_watchdog.py 2>&1
