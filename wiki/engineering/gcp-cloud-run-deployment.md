---
title: GCP Cloud Run 部署规范
domain: engineering
type: concept
keywords: [gcp, cloud-run, 部署, dockerfile, fastapi, source模式, 镜像库]
tags: [gcp, cloud-run, deployment, dockerfile]
source: L-2026-04-30-002（原 general rule §4.15）
sources: [L-2026-04-30-002]
created: 2026-05-24
updated: 2026-05-24
last_updated: 2026-05-24
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

## 来源

L-2026-04-30-002（原 general rule §4.15）

## 相关页面

- [[gcp-iam-runtime-permissions]] —— 部署成功后还需补运行时权限
- general-global-rule.md §7 安全与禁区
