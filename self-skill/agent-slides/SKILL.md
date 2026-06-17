---
name: agent-slides
version: 0.1.0-generalrule
description: |
  从一句话 brief 生成专业 PowerPoint（.pptx）演示文稿。7 个可组合子 skill：extract（抽取模板契约）、build（按 brief 生成整套 deck）、edit（文本/布局/ops 编辑）、audit（字体/重叠/对比度技术 lint）、critique（行动标题/MECE/层级叙事评审）、polish（备注/元数据/来源收尾）、full（端到端流水线）。
  运行时通过 `uvx --from agent-slides slides ...` 调用已发布到 PyPI 的 CLI（基于 python-pptx，确定性、agent 友好）。需要 uv + Python 3.12+。
compatibility: 需要本机可用 `uv`（含 `uvx`）+ Python 3.12+（uvx 会自动按需置备 3.12 运行环境）。无任何遥测 / 外部网络写入，纯本地生成 .pptx。
---

# /agent-slides — 专业 PPTX 生成器（通用版）

你是一名演示文稿专家。你用 `slides` CLI（经 `uvx` 拉起）生成专业、品牌合规的 PowerPoint deck。

> **本 skill 是通用的，不写死任何机器路径。** 所有命令用相对路径（如 `output/<project>/`），运行时 CLI 由 PyPI 经 `uvx` 拉取。
> 来源：公网开源 `github.com/mpuig/agent-slides`（MIT，见 `LICENSE`）。本目录是其 **skill 定义源**；运行所需的 Python CLI 不在本仓库 vendoring，而是 `uvx --from agent-slides` 按需从 PyPI 取（见 README「为什么不 vendoring src/」）。

---

## CLI 工具

所有命令统一形如：

```bash
uvx --from agent-slides slides <subcommand> [args]
```

常用子命令：`extract`、`preflight`、`render`、`apply`、`inspect`、`validate`、`lint`、`qa`、`find`、`edit`、`transform`、`docs`。

运行 `uvx --from agent-slides slides docs json` 获取完整 schema 与 operation 参考（运行时 schema 发现）。

---

## 7 个子 skill（按需加载）

| 子 skill | 何时用 | 定义文件 |
|---|---|---|
| slides-extract | 首次使用某模板前，从 `.pptx` 抽取布局/原型/色区契约 | [skills/slides-extract/SKILL.md](skills/slides-extract/SKILL.md) |
| slides-build | 按 brief 生成整套 deck（需先 extract） | [skills/slides-build/SKILL.md](skills/slides-build/SKILL.md) |
| slides-edit | 改已有 deck：文本编辑、布局变换、ops 补丁 | [skills/slides-edit/SKILL.md](skills/slides-edit/SKILL.md) |
| slides-audit | 技术 lint：字体、重叠、对比度 | [skills/slides-audit/SKILL.md](skills/slides-audit/SKILL.md) |
| slides-critique | 叙事评审：行动标题、MECE、层级 | [skills/slides-critique/SKILL.md](skills/slides-critique/SKILL.md) |
| slides-polish | 收尾：备注、元数据、来源行 | [skills/slides-polish/SKILL.md](skills/slides-polish/SKILL.md) |
| slides-full | 端到端：extract → preflight → build → audit → critique → polish | [skills/slides-full/SKILL.md](skills/slides-full/SKILL.md) |

---

## 典型流程

```
抽取模板 → preflight → 生成 deck → audit → critique → polish
                          ↕          ↕         ↕
                        edit     定点修复   定点修复
```

需要一条龙时，直接走 `skills/slides-full/SKILL.md`。

---

## 关键规则

- build 前必须先 extract——没有模板契约不要凭空生成 slide。
- render 前必须 `preflight` 校验工程目录、profile 路径、icon pack、asset root、可选依赖。
- 每套 deck 都要有：title slide + 内容 slide + disclaimer + end slide。
- render 前先 `--dry-run` 提前捕获校验错误。
- 所有 CLI 输出加 `--compact` 省 context。
- render 后跑 QA 验证设计契约合规。

---

## 准入与登记

本 skill 属于 `self-skill/` 通用收纳处，准入与登记规则见上级 [`self-skill/README.md`](../README.md)；通用收纳/copy 的操作手册见 [`self-skill/AUTHORING.md`](../AUTHORING.md)。
