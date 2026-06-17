#!/usr/bin/env python3
"""
collect_topic_conversation.py — Hermes 项目上下文采集脚本

用法（预留给 cron 调用，当前用 Hermes cron job prompt 替代）：
    python3 collect_topic_conversation.py --project-dir /path/to/project

功能：
  从 Hermes state.db 拉取最近 N 天与该项目相关的 telegram 对话，
  提取新的决策/纠正/配置变化，蒸馏写入 docs/context-log.md，
  并刷新 AGENTS.md 的项目简介行。

注意：
  Hermes state.db 对 telegram 会话只记 source='telegram'，不持久化
  topic/thread_id。本脚本用「时间窗 + telegram 来源 + 含项目关键词过滤
  + 排除 delegation 子任务噪音」做近似。单 topic 活跃时效果好。

采集策略：
  1. 从 state.db 读取最近 3 天所有 source='telegram' 的会话
  2. 按 project_keywords 列表过滤：session title 含任一关键词即入选
  3. 排除 parent_session_id IS NOT NULL 的 delegation 子任务
  4. 提取 messages 中 role='user' 和 role='assistant' 的对话
  5. 合并输出成纯文本内容，供 cron agent 蒸馏

输出：
  JSON 到 stdout，含 sessions JSON 和 messages JSON（每条带 role + content 截断）
"""

import sqlite3
import json
import os
import sys
from datetime import datetime, timezone, timedelta

STATE_DB = os.path.expanduser("~/.hermes/state.db")
DAYS_BACK = 3   # 拉取最近 N 天

def get_recent_sessions(project_keywords, days=DAYS_BACK):
    """获取符合项目关键词的近期 telegram 会话"""
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    cutoff_ts = cutoff.timestamp()

    conn = sqlite3.connect(STATE_DB)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    # 查近期 telegram 会话（排除 delegation 子任务）
    cur.execute("""
        SELECT id, source, user_id, started_at, ended_at, title,
               message_count, parent_session_id
        FROM sessions
        WHERE source = 'telegram'
          AND started_at >= ?
          AND parent_session_id IS NULL
        ORDER BY started_at DESC
    """, (cutoff_ts,))

    rows = cur.fetchall()
    conn.close()

    results = []
    for r in rows:
        title = r['title'] or ''
        # 用项目关键词过滤
        if not any(kw.lower() in title.lower() for kw in project_keywords):
            continue

        results.append({
            'id': r['id'],
            'title': title,
            'started_at': r['started_at'],
            'started_at_str': datetime.fromtimestamp(r['started_at'], tz=timezone.utc).strftime('%Y-%m-%d %H:%M UTC'),
            'message_count': r['message_count'],
            'user_id': r['user_id'],
        })

    return results


def get_session_messages(session_id, max_messages=100):
    """获取指定 session 的对话消息"""
    conn = sqlite3.connect(STATE_DB)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    cur.execute("""
        SELECT id, role, content, timestamp, tool_name
        FROM messages
        WHERE session_id = ?
          AND role IN ('user', 'assistant')
          AND active = 1
        ORDER BY timestamp ASC
        LIMIT ?
    """, (session_id, max_messages))

    rows = cur.fetchall()
    conn.close()

    messages = []
    for r in rows:
        content = r['content'] or ''
        # 截断过长内容（保留前 2000 字符）
        if len(content) > 2000:
            content = content[:2000] + f"\n[...截断，原长 {len(content)} 字符]"

        messages.append({
            'role': r['role'],
            'content': content,
            'timestamp': r['timestamp'],
        })

    return messages


def collect(project_dir, project_keywords):
    """主采集函数——收集对话文本，输出到 stdout"""
    project_dir = os.path.abspath(project_dir)
    project_name = os.path.basename(project_dir)

    if not project_keywords:
        # 默认用目录名做关键词
        project_keywords = [project_name.replace('-', ' ').replace('_', ' ')]

    print(f"# 项目上下文采集: {project_name}", file=sys.stderr)
    print(f"# 项目目录: {project_dir}", file=sys.stderr)
    print(f"# 关键词: {project_keywords}", file=sys.stderr)
    print(f"# 时间窗: 最近 {DAYS_BACK} 天", file=sys.stderr)

    sessions = get_recent_sessions(project_keywords)

    print(f"# 找到 {len(sessions)} 个相关会话", file=sys.stderr)

    output = {
        'project': project_name,
        'project_dir': project_dir,
        'keywords': project_keywords,
        'days_back': DAYS_BACK,
        'collected_at': datetime.now(timezone.utc).isoformat(),
        'sessions': [],
    }

    for s in sessions:
        session_data = {
            'id': s['id'],
            'title': s['title'],
            'started_at': s['started_at_str'],
            'messages': get_session_messages(s['id']),
        }
        output['sessions'].append(session_data)
        print(f"#  - {s['title']} ({s['started_at_str']}, {s['message_count']} 条消息)",
              file=sys.stderr)

    print(json.dumps(output, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='Hermes 项目上下文采集')
    parser.add_argument('--project-dir', required=True, help='项目目录绝对路径')
    parser.add_argument('--keywords', nargs='+', help='项目关键词列表，用于过滤相关会话')
    args = parser.parse_args()

    collect(args.project_dir, args.keywords or [])
