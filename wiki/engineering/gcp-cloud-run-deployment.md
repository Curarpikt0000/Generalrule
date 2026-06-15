---
title: GCP Cloud Run 部署规范
domain: engineering
type: concept
keywords: [gcp, cloud-run, 部署, dockerfile, fastapi, source模式, 镜像库]
tags: [gcp, cloud-run, deployment, dockerfile]
source: L-2026-04-30-002（原 general rule §4.15）
sources: [L-2026-04-30-002, L-2026-06-15-001]
created: 2026-05-24
updated: 2026-06-15
last_updated: 2026-06-15
---

# GCP Cloud Run 部署规范

> 在 GCP Cloud Run 上部署服务时遵守。涉及 Cloud Run 部署的任务先读本页。

---

## 核心规则

- **云原生部署优先使用 `--source` 模式**，绕过镜像库域名迁移带来的权限死锁。
- **Dockerfile 的 `CMD` 必须精准对齐**包含 FastAPI `app` 实例的启动模块。

---

## 为什么

**关于 `--source` 模式**：直接用预构建镜像部署时，会遇到镜像库域名迁移（如 gcr.io → Artifact Registry）导致的权限死锁——服务账号对新旧域名权限不一致，部署卡死。`gcloud run deploy --source .` 让 Cloud Build 在 GCP 侧完成构建与推送，绕开这个死锁。

**关于 CMD 对齐**：Cloud Run 期望容器监听 `$PORT`。如果 Dockerfile 的 `CMD` 启动的模块不是真正包含 FastAPI `app` 实例的那个，容器会起不来或健康检查失败。CMD 必须精准指向 `app` 所在模块。

---

## 正确做法

```bash
# 用 --source 模式部署，让 GCP 侧构建
gcloud run deploy <service-name> \
  --source . \
  --region <region> \
  --project <project-id>
```

```dockerfile
# CMD 精准对齐含 app 实例的模块
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
```

---

---

## 部署同步陷阱：改了持久化层枚举/schema 却忘了重部署读取方（L-2026-06-15-001）

### 症状

下游进程健康轮询，却长期「读到 0 条待处理」、没有产出——表面像「没有新数据」，实则**上游写入方（Cloud Run）每次执行都崩溃 500**，新数据进不了队列。最隐蔽，因为没人报错，只是「没数据」。

```
ValueError: 'skipped' is not a valid ProcessStatus
  at /app/storage.py  return ProcessStatus(doc.get("status"))
HTTP "POST /scan HTTP/1.1" 500 -
```

### 根因

一个进程往持久化层（Firestore / DB / 消息队列）写入了**新增的枚举值 / schema 字段**，但负责读取该层的**另一个服务用的是不认得这个值的旧镜像**。两者代码版本漂移：本地源码已加 `ProcessStatus.SKIPPED`，但 Cloud Run 部署的镜像比该改动早了半个月，旧枚举解析新值即 `ValueError`，整个请求 500。

### 规则

- **改了任何被多进程共享的持久化层的枚举/schema，必须同步重部署所有读取该层的服务**，否则旧读取方一遇新值就崩——造成**静默停摆**。
- **「本地源码是对的」≠「线上是对的」**。尤其非 git 管理的项目，要靠**文件 mtime 与部署 revision 时间戳比对**确认改动是否真上线（`gcloud run revisions list --format="table(metadata.name,metadata.creationTimestamp)"`）。
- 排查「下游空转」先回溯**上游写入方是否在产出**，别只盯健康的下游。
- 验证部署用真实触发路径（如 `gcloud scheduler jobs run <job>`），别用个人身份令牌手动 curl——通常缺 `run.invoker` 会 401，是假阴性。

### 通用化

这条不限 Cloud Run：任何「写入方加了新状态值、读取方未同步升级」的**多版本共存**场景（微服务、跨语言客户端、灰度发布）都会复现。枚举/schema 演进时遵循「先让所有读取方认得新值，再让写入方开始写新值」的顺序。

---

## 来源

- L-2026-04-30-002（原 general rule §4.15）—— `--source` 部署 + CMD 对齐
- L-2026-06-15-001（magazine-podcast：枚举漂移致扫描器静默停摆半月）

## 相关页面

- [[gcp-iam-runtime-permissions]] —— 部署成功后还需补运行时权限
- general-global-rule.md §7 安全与禁区
