# Notion DB/DS 参考大全

> 所有 Notion 数据库和 Data Source 的 ID 速查表。
> 注意：data_sources API 使用 `Notion-Version: 2026-03-11`，databases API 使用 `Notion-Version: 2022-06-28`

---

## 4 张西方源表 (Data Source → DB 回退)

| # | 表名 | DS ID (API 优先) | DB ID (回退) | 查询版本 | 回退版本 | 说明 |
|---|---|---|---|---|---|---|
| 1 | CME 库存 | `2e047eb5-fd3c-8034-a672-000be7162cff` | `2e047eb5-fd3c-80d8-9d56-e2c1ad066138` | 2026-03-11 | 2022-06-28 | 过滤 Metal Type=Gold/Silver/Platinum |
| 2 | OI | `2fc47eb5-fd3c-8023-85ec-000b59408356` | `2fc47eb5-fd3c-8035-ab22-cabf3e6e41bb` | 2026-03-11 | 2022-06-28 | OI Futures/Options 含 JSON 需反转义 |
| 3 | CFTC | `2c747eb5-fd3c-808e-ab46-000bfe7673c5` | `2c747eb5-fd3c-8081-86dd-d0aeb45d5046` | 2026-03-11 | 2022-06-28 | COT JSON 可能只含日期无 concentration |
| 4 | SLV iShares | `2ba47eb5-fd3c-8026-b549-000b2a02c5c8` | `2ba47eb5-fd3c-80c6-a0c1-ce9f47ec5d25` | 2026-03-11 | 2022-06-28 | 字段名 `Ounces In trus`(拼写错误!) |

## 2 张东方源表 (普通 Database)

| # | 表名 | DB ID | 版本 | 排序字段 | 说明 |
|---|---|---|---|---|---|
| 5 | SHFE Au 周库存 | `2bc47eb5-fd3c-8083-966e-ecfd9f396b44` | 2022-06-28 | `Gold日期` | 筛选 `市场=SHFE`, `库存频率=每周` |
| 6 | SHFE/SGE Ag 周库存 | `2bc47eb5-fd3c-80f3-a71a-d8de149a4943` | 2022-06-28 | `Silver日期` | 筛选 `市场=SHFE` or `SGE`, `库存频率=每周` |

## 写入库

| 库名 | DB ID | 版本 | Page Name 格式 | Hermes Analysis 列名 |
|---|---|---|---|---|
| Delivery Notice & AI Analysis | `2be47eb5-fd3c-80ba-b065-f188139834b9` | 2022-06-28 | `日报 YYYY-MM-DD` | `Hermes Analysis ` (注意尾随空格!) |

## Token

| 用途 | Token | 所属集成 |
|---|---|---|
| Notion API | `YOUR_NOTION_TOKEN` | Hermes Analysis Issue Report |
| FRED DGS3MO | `YOUR_FRED_API_KEY` | FRED API Key |

## API 版本规则

| 场景 | HTTP Header | 备注 |
|---|---|---|
| data_sources 查询/读取 | `Notion-Version: 2026-03-11` | 最新版，旧版本返回 400 |
| databases 查询 | `Notion-Version: 2022-06-28` | 最新版返回 400 |
| 创建/更新 page | `Notion-Version: 2022-06-28` | 写入时用这个 |
| PATCH blocks | `Notion-Version: 2022-06-28` | 同上 |

## 数据库连接状态

| 库 | 状态 | 备注 |
|---|---|---|
| CME 库存 | ✅ 可连接 | DS 2026-06-15起返回0行，需回退DB |
| OI | ✅ 可连接 | 同上故障 |
| CFTC | ✅ 可连接 | 同上故障 |
| SLV | ✅ 可连接 | 同上故障 |
| SHFE Au | 🔴 未授权 | 需在 Notion 手动 Share 给 Hermes Analysis 集成 |
| SHFE/SGE Ag | 🔴 未授权 | 同上 |
