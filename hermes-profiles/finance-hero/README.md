# Finance Hero · Profile 部署蓝图

> **本目录不是项目，是蓝图。** 是 Hermes `finance` profile（`~/.hermes/profiles/finance/`）的版本受控源。
> 更多见顶层文档：`../ARCHITECTURE.md`（架构）、`../MECHANISM-DESIGN.md`（机制）、`../DISTILLATION-PROCESS.md`（蒸馏）、`../COPY-GUIDE.md`（复刻指南）。

## 文件分工

| 蓝图文件 | 部署后位置 | 作用 |
|---|---|---|
| `SOUL.md` | `~/.hermes/profiles/finance/SOUL.md` | 行为核心，每条消息重载 |
| `skills/<大师>/` | `~/.hermes/profiles/finance/skills/<大师>/` | 11 位投资大师的思维定义 |
| `references/synthesis.md` | `~/.hermes/profiles/finance/references/synthesis.md` | 综合裁决四问规则 |
| `references/depth-modes.md` | `~/.hermes/profiles/finance/references/depth-modes.md` | 快答 vs 全议会档位 |
| `references/moomoo-setup.md` | `~/.hermes/profiles/finance/references/moomoo-setup.md` | 行情数据接入说明 |
| `tools/gfinance_research.py` | `~/.hermes/profiles/finance/tools/gfinance_research.py` | Google Finance 二次验证脚本 |
| `deploy.md` | （部署说明） | 首次部署清单 |
| `sync.sh` | （部署脚本） | 蓝图→profile 一键同步 |
| `AGENTS.md` | （废弃） | 旧架构遗物 |

## 11 位大师阵容

| 大师 | 分类 | 核心镜片 |
|---|---|---|
| 巴菲特 | 价值 | 护城河、安全边际、集中投资 |
| 格雷厄姆 | 价值 | 内在价值、市场先生、安全边际 |
| 彼得·林奇 | 价值 | 身边股主义、十倍股、耐心 |
| 段永平 | 价值 | 商业逻辑、买股票=买公司 |
| 利弗莫尔 | 趋势 | 最小阻力、关键点、领头羊 |
| 索罗斯 | 宏观 | 反身性、宏观机会 |
| 西蒙斯 | 量化 | 数据驱动、统计套利 |
| 德曼 | 量化 | 模型不是真的、还原论 |
| 塔勒布 | 风险 | 反脆弱、尾部风险、非对称 |
| 芒格 | 反向 | 反向思考、多元思维、偏误清单 |
| 霍华德·马克斯 | 周期 | 钟摆位置、情绪温度 |

## 部署

```bash
# 首次部署（需要先创建 profile，配 bot token）
# 详见 deploy.md

# 后续更新（改蓝图后）
cd ~/hermesagent/Distill/蒸馏Hermes/finance-hero
./sync.sh
```

详情见 `deploy.md`、`../COPY-GUIDE.md`。
