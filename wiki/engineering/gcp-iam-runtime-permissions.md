---
title: GCP 运行时权限补全
domain: engineering
type: concept
keywords: [gcp, iam, 权限, service-account, 运行时, aiplatform, 部署]
tags: [gcp, iam, permissions, service-account]
source: L-2026-04-30-001（原 general rule §4.16）
sources: [L-2026-04-30-001]
created: 2026-05-24
updated: 2026-05-24
last_updated: 2026-05-24
---

# GCP 运行时权限补全

> 在 GCP 部署服务（尤其调用其他 GCP API 的服务）后遵守。涉及 GCP 部署的任务先读本页。

---

## 核心规则

- **部署成功不代表业务可用。** 必须补全 Service Account 的运行时权限（如 `roles/aiplatform.user`）。

---

## 为什么

部署成功只意味着"容器跑起来了"，不意味着"业务能正常工作"。服务在运行时调用其他 GCP API（如 Vertex AI、Storage、Pub/Sub）时，用的是它绑定的 Service Account。如果这个 SA 没有相应的运行时角色，调用会在运行时报 403 权限错误——而部署阶段一切正常，问题只在真正调用时才暴露。

这是个隐蔽的坑：日志显示部署成功、服务在线，但一调用核心功能就挂。

---

## 正确做法

部署后，给服务的 Service Account 补全运行时所需角色。例：

```bash
# 例：补全 Vertex AI 调用权限
gcloud projects add-iam-policy-binding <project-id> \
  --member="serviceAccount:<sa-email>" \
  --role="roles/aiplatform.user"
```

按服务实际调用的 API 补对应角色（Storage → `roles/storage.objectUser`，Pub/Sub → `roles/pubsub.editor` 等）。

---

## 检查清单

部署后自问：
- 服务运行时会调用哪些 GCP API？
- 它的 Service Account 有这些 API 的角色吗？
- 验证：实际触发一次核心业务流程，确认不报 403。

---

## 来源

L-2026-04-30-001（原 general rule §4.16）

## 相关页面

- [[gcp-cloud-run-deployment]] —— 先部署，再补权限
- general-global-rule.md §2.4 目标驱动执行（"部署成功"不是验收标准，"业务跑通"才是）
