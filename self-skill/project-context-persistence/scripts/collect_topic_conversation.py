#!/usr/bin/env python3
"""
collect_topic_conversation.py

Deterministically pull the most recent Telegram conversation text from Hermes's
state.db so a cron job can compress it into a project's context log.

WHY a script (not session_search): session_search is FTS5 keyword-based and the
DB does NOT persist Telegram topic/thread_id in a queryable column. To
approximate "this topic's recent discussion" we pull the most recently-active
telegram session(s) within a lookback window and dump user+assistant turns as
plain text. The cron agent then compresses that.

Output: raw conversation text to stdout (consumed by the cron prompt). Prints a
NO_NEW_CONTENT marker line if nothing in the window, so the cron agent stays
quiet.

Usage:
  python3 collect_topic_conversation.py [--hours 26] [--db PATH] [--max-chars 40000]
"""
import argparse
import os
import sqlite3
import time

DEFAULT_DB = os.path.expanduser("~/.hermes/state.db")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--hours", type=float, default=26.0,
                    help="Lookback window in hours (default 26 = 1 day + buffer).")
    ap.add_argument("--db", default=DEFAULT_DB)
    ap.add_argument("--max-chars", type=int, default=40000,
                    help="Cap on total dumped characters (keeps cron context sane).")
    args = ap.parse_args()

    if not os.path.exists(args.db):
        print(f"NO_NEW_CONTENT (db not found: {args.db})")
        return

    cutoff = time.time() - args.hours * 3600
    con = sqlite3.connect(args.db)
    cur = con.cursor()

    cur.execute(
        """
        SELECT DISTINCT s.id, s.title, s.started_at
        FROM sessions s
        JOIN messages m ON m.session_id = s.id
        WHERE s.source = 'telegram' AND m.timestamp >= ?
        ORDER BY s.started_at DESC
        """,
        (cutoff,),
    )
    sessions = cur.fetchall()
    if not sessions:
        print("NO_NEW_CONTENT (no telegram messages in window)")
        return

    chunks = []
    total = 0
    for sid, title, started in sessions:
        # Skip delegation/subagent sessions: their first user message is a long
        # machine-generated task goal (not a real human turn). Real Telegram
        # turns from the user are short and often prefixed with "[Name]".
        cur.execute(
            """
            SELECT content FROM messages
            WHERE session_id = ? AND role = 'user'
              AND content IS NOT NULL AND content != ''
            ORDER BY id ASC LIMIT 1
            """,
            (sid,),
        )
        first = cur.fetchone()
        if first:
            fc = first[0]
            if len(fc) > 500 and not fc.lstrip().startswith("["):
                continue
        cur.execute(
            """
            SELECT role, content, timestamp
            FROM messages
            WHERE session_id = ?
              AND role IN ('user', 'assistant')
              AND timestamp >= ?
              AND content IS NOT NULL AND content != ''
            ORDER BY id ASC
            """,
            (sid, cutoff),
        )
        rows = cur.fetchall()
        if not rows:
            continue
        header = f"\n===== SESSION: {title or sid} =====\n"
        chunks.append(header)
        total += len(header)
        for role, content, ts in rows:
            line = f"[{role}] {content}\n"
            if total + len(line) > args.max_chars:
                chunks.append("\n...[truncated: window exceeded max-chars]...\n")
                total = args.max_chars
                break
            chunks.append(line)
            total += len(line)
        if total >= args.max_chars:
            break

    out = "".join(chunks).strip()
    if not out:
        print("NO_NEW_CONTENT (sessions had no usable text)")
        return
    print(out)


if __name__ == "__main__":
    main()
