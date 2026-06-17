# Memory-Bank Cron Recipe (verified working)

Worked, end-to-end-verified recipe for daily per-topic context distillation into a project folder. Built and run successfully on a Hermes deployment serving multiple Telegram topics (one topic per project).

## 0. Prereqs / install the collector
Copy this skill's `scripts/collect_topic_conversation.py` into `~/.hermes/scripts/` (cron `script` requires the file there, referenced by bare filename).

```
cp <skill_dir>/scripts/collect_topic_conversation.py ~/.hermes/scripts/
python3 ~/.hermes/scripts/collect_topic_conversation.py --hours 26 --max-chars 2000 | head   # smoke test
```
Expect either real `===== SESSION: ... =====` blocks of `[user]/[assistant]` turns, or `NO_NEW_CONTENT`.

## 1. Scaffold (structure-first)
Confirm with the user FIRST: the project parent directory (whatever convention the user uses, e.g. `~/Projects/` — the exact path is the user's call, never assume one from a template) and the EXACT channel-name list (don't trust `channel_directory.json` — it's often stale; the user is authoritative). Then per channel:

```
mkdir -p ~/Projects/<Slug>/{src,tasks,tests,docs,scratch,agents,hooks,commands,.claude/rules}
# .gitkeep in each empty dir so structure survives git
cd ~/Projects/<Slug> && ln -sf AGENTS.md CLAUDE.md && git init -q
```
Write `AGENTS.md` (project entry template), `tasks/todo.md`, `tasks/lessons.md`, `.gitignore` via `write_file` (avoids the CJK/homoglyph shell-scan interruption that hits `printf`/heredoc).

## 2. Create the cron job
Via the `cronjob` tool, action=create:
- `name`: `<slug>-context-distill`
- `schedule`: `0 2 * * *` (or `every 6h` for incremental)
- `script`: `collect_topic_conversation.py`   ← bare filename only
- `workdir`: `<absolute path to the project dir>`  ← absolute; auto-loads its AGENTS.md
- `deliver`: `local`                            ← silent archive, doesn't ping the user
- `enabled_toolsets`: `["file", "terminal"]`

### Cron prompt (CJK example that worked)
```
你是 <项目> 的上下文归档器。上方注入的是过去约一天里 Telegram 上的真实人机对话原文（已过滤掉子任务噪音）。

如果对话内容是 "NO_NEW_CONTENT" 开头，说明今天没有新对话，直接什么都不做，安静退出（不写文件、不输出）。

否则（工作目录已是项目根）：
1. 压缩成简洁上下文快照，只保留对未来有用的信息：决策/共识、事实/配置（路径、命名、表、参数）、准备工作进展、待办/未决。丢弃寒暄、纠错往返、过程废话。
2. 追加写入 docs/context-log.md（不存在则创建，首行 "# <项目> 上下文日志"）。格式：
   ## YYYY-MM-DD
   ### 决策 / ### 事实/配置 / ### 准备工作进展 / ### 待办
   用 read_file 读出原内容再 write_file 追加，或 shell 追加；不要覆盖。
3. 若 AGENTS.md 的 "## 项目简介" 仍是占位符，用一句准确的话替换，只动这一段。
4. 一句话报告写了哪些文件。

保持原文语言（中文为主），不要翻译。不要把密钥/token 写进文件。
```

## 3. VERIFY (mandatory — do not skip)
```
cronjob action=run job_id=<id>        # queues for next tick
# wait ~60-120s for the tick + agent run
ls -la ~/Projects/<Slug>/docs/        # context-log.md should appear
read_file ~/Projects/<Slug>/docs/context-log.md
```
Check `~/.hermes/cron/jobs.json` for `last_status: ok`. Then read the file and confirm quality. Only then tell the user it's done.

## Observed bonus behaviour
With a capable model, the distiller doesn't just summarize today — it can pull prior prep work from earlier sessions in the window and seed the context-log richly (tables, segments, TODOs). That's the point: future sessions in that workdir start warm.

## Tradeoffs / when to escalate
- Time-window approximation is fine while only one topic is active. If several topics are simultaneously busy, the window mixes them → switch that project to its own Hermes **profile** for true session/memory isolation (heavier: separate startup/service).
