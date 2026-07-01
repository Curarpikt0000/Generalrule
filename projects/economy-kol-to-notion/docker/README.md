# Docker 知识包镜像 — Economy-KOL-to-Notion

> **目的**：未来 agent `docker run` 即拿到本项目**全部知识**（逻辑/历史/未来工作/Notion 坐标/运维机制/skill/脚本）。
> **知识包镜像**：不含真实数据（KOL 言论/Notion 快照）和密钥——agent 用自己的 `.env` 连真实 Notion。
> 已脱敏（无 Uber 内部专有名），脱离原环境也成立。

## 镜像里有什么

`docker run --rm economy-kol-to-notion-knowledge` → 打印 `AGENT_START_HERE.md` 引导。
镜像内 `/knowledge/`：
- `AGENT_START_HERE.md` — 引导入口（先读这个）
- `README.md` — 项目逻辑/架构/铁律/进展
- `ops/RUNBOOK.md` + `ops/cron-jobs.json` + `ops/*.sh` — 运维机制（时序/更新顺序/重建）
- `notion-locations.md` — Notion 三层 DB 坐标（database_id / data_source_id / dashboard URL）
- `lessons.md` / `todo.md` — 踩坑教训 / 待办
- `skill/` — E2E 操作手册 skill + references
- `scripts/` — 23 个核心脚本
- `config/.env.example` — 密钥模板（自己填）

## 如何构建（构建上下文需要 knowledge/ 目录）

Dockerfile 用 `COPY knowledge/ /knowledge/`，所以构建前要把知识包组装进同目录的 `knowledge/`。
知识包内容 = 本 repo `projects/economy-kol-to-notion/` 的**已脱敏**副本 + 本 docker/ 目录的引导文件。

```bash
# 在本 docker/ 目录旁组装构建上下文
mkdir -p build/knowledge
# 1. 项目知识包(代码+文档+RUNBOOK+ops+skill), 从本 repo 拷(已脱敏)
cp -r ../*  build/knowledge/                 # projects/economy-kol-to-notion/ 全部
cp -r ../../../self-skill/economics-kol-daily-update build/knowledge/skill
# 2. 镜像专属引导文件(本目录)
cp AGENT_START_HERE.md notion-locations.md config.env.example build/knowledge/
# 3. 构建
cp Dockerfile build.sh build/
cd build && bash build.sh
```

> 或直接把本 repo 已脱敏的 `projects/economy-kol-to-notion/` + `self-skill/economics-kol-daily-update/` 拷成 `knowledge/`，加本目录 3 个引导文件，然后 `docker build`。

## 使用

```bash
docker load < economy-kol-to-notion-knowledge-latest.tar.gz   # 若有离线 tar
docker run --rm economy-kol-to-notion-knowledge               # 看引导
docker run --rm economy-kol-to-notion-knowledge cat /knowledge/README.md
docker run --rm economy-kol-to-notion-knowledge cat /knowledge/ops/RUNBOOK.md
docker run --rm -it economy-kol-to-notion-knowledge sh        # 进容器浏览
```

## 为什么 tar.gz 不进 git

导出的镜像 tar.gz（~49MB）是二进制，不适合 git。需要离线镜像时用 `build.sh` 现构建，或从约定的分发位置获取。本 repo 只放**可复现构建的源**（Dockerfile + build.sh + 引导文件）。
