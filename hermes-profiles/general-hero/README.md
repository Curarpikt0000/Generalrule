# General Hero · Profile 部署蓝图

> **本目录不是项目，是蓝图。** 是 Hermes `general` profile（`~/.hermes/profiles/general/`）的版本受控源。
> 改动这里 → 跑 `sync.sh` 同步到 profile → 自动重启 launchd 服务生效。

## 文件分工

| 蓝图文件 | 部署后位置 | 作用 |
|---|---|---|
| `SOUL.md` | `~/.hermes/profiles/general/SOUL.md` | profile 的"行为核心"，每条消息重载 |
| `skills/<大师>/SKILL.md` + `references/` | `~/.hermes/profiles/general/skills/<大师>/` | 9 位伟人的思维定义 |
| `references/scaffold-feynman.md` | 同上 | 费曼翻译层细则 |
| `references/scaffold-falsification.md` | 同上 | 证伪自检细则 |
| `references/scaffold-saussure.md` | 同上 | 索绪尔历时/共时横纵细则 |
| `references/scaffold-evolution-peer.md` | 同上 | 演化/同类强制辅维细则 |
| `references/synthesis.md` | 同上 | 综合裁决四问规则 |
| `references/depth-modes.md` | 同上 | 快答 vs 全议会档位 + 9 位召唤映射 |
| `sync.sh` | （不部署，本地脚本）| 蓝图→profile 一键同步 |
| `deploy.md` | （不部署，本地说明）| 首次部署清单 |

## 10 位大师阵容

| 大师 | 来源 | 招牌镜片 |
|---|---|---|
| 毛泽东 | [wwwaapplleecu-source/mao-skill](https://github.com/wwwaapplleecu-source/mao-skill) | 博弈 / 主要矛盾 / 动力 / 实践论 |
| 费曼 | [nuwa-skill/examples/feynman-perspective](https://github.com/alchaincyf/nuwa-skill) | 第一性 / 翻译 / 直觉物理 |
| 芒格 | 复用 finance + [alchaincyf/munger-skill](https://github.com/alchaincyf/munger-skill) | 反向思考 / 多元思维 / 认知偏误 |
| 塔勒布 | 复用 finance + [alchaincyf/taleb-skill](https://github.com/alchaincyf/taleb-skill) | 风险 / 反脆弱 / 不对称 |
| 库恩 | Cowork 手蒸馏（2026-05-28）| 范式 / 演化阶段 / 不可通约 |
| 老子 | Cowork 手蒸馏（2026-05-28）| 反者道之动 / 无为 / 上善若水 |
| 福柯 | Cowork 手蒸馏（2026-05-28）| 权力/知识 / 话语 / 规训 |
| 波特 | Cowork 手蒸馏（2026-05-28）| 五力 / 通用战略 / 定位 |
| 阿克洛夫 | Cowork 手蒸馏（2026-05-28）| 信息不对称 / 柠檬市场 / 信号 |
| 乔布斯 | [nuwa-skill/examples/steve-jobs-perspective](https://github.com/alchaincyf/nuwa-skill) | 极简取舍 / 产品哲学 / 用户体验直觉 / "Connect the dots" |

## 四件套脚手架（general hero 灵魂，每次回答强制走完）

1. **费曼翻译层** —— 讲给 5 岁小孩 + 6 步讲述训练
2. **证伪自检** —— "我可能错在哪 + 一个具体反例"
3. **索绪尔历时/共时横纵** —— 时间位 + 系统位双扫
4. **演化 / 同类强制辅维** —— 借库恩 + 波特镜片，定时间位 + 空间位

## 它和 finance / worker profile 的关系

```
~/.hermes/profiles/worker/    ← 工程师纪律 + "建工程项目结构"
~/.hermes/profiles/finance/   ← 投资大师议会（11 位）
~/.hermes/profiles/general/   ← 通识/人生议会（9 位 + 四件套）← 本蓝图部署目标
```

每个 profile 完全独立：自己的 SOUL / bot / 记忆 / skills，互不污染。

## 设计要点（继承 finance + 新增）

继承 finance：
- 议会模式（大师=声部，主持人=综合）
- 综合裁决层（共识 / 冲突 / 根源 / 我倾向哪条路径）
- 深度档位（快答 vs 全议会）
- 蓝图↔profile SSOT 同步纪律

新增（general 专属）：
- **四件套脚手架**：每次回答强制走完费曼 + 证伪 + 横纵 + 演化-同类
- **快答档篇幅 ≤700 字**（finance 是 500，因为脚手架占空间）
- **澄清困境再答**：若用户没说处境，先反问 1-2 句再分析
- **东方哲学声部**（老子）—— 议会的反向 / 顺势维度

## 上游

服从 General Global Rule（认知纪律、§2.10 显式失败、研究先行）。
方法论继承自 finance hero —— 详见 wiki `agent-rules/finance-hero-distillation.md`。
