# Notion 位置坐标 — Economy-KOL-to-Notion

> 新 agent 用这些 database_id 连接真实 Notion（需你自己的 NOTION_TOKEN，见 config.env.example）。
> DB id 是坐标不是凭证——光有 id 无 token 访问不了。

## 三层 Notion DB

| DB | database_id | 粒度 | 作用 |
|---|---|---|---|
| **KOL List**（registry 权威源 SSOT） | `35947eb5fd3c800db852cef31f9de6a5` | 每 KOL 一行 | 唯一权威 KOL 名单；`Name of KOL` 是 **select** 类型；机构不算 KOL |
| **KOL By Day** | `32347eb5fd3c8087b9c0f409f95f664e` | 每 KOL 每天一行 | 核心分析表（含方向明细 JSON + 期限） |
| **KOL By Week** | `36b47eb5fd3c80d08d39e30f9e526c45` | 每周一行 | 全市场综合周报 |

## By Day data_source_id（改 select options 用）
- `32347eb5-fd3c-80d6-b948-000b45caae34`（注意 80d6，≠ database_id 的 8087）
- **建 page** 用 database_id（8087）；**读/更新 select options** 用 data_source_id（80d6）

## Dashboard（对外展示层）
- 线上 URL：https://curarpikt0000.github.io/kol-dashboard/
- 独立 git repo：`curarpikt0000/kol-dashboard`（GitHub Pages）
- 数据源 data.json 由 `dashboard/kol-dashboard/generate_dashboard_data.py` 从 By Day 生成

## By Day 关键属性
- `Name of KOL`（**select**）｜`Comments`（rich_text）｜`方向明细`/`direction_detail`（rich_text 存 JSON 数组，每 leg 含 标的/板块/方向/期限）｜`主导方向`（select 6 档）｜`Sector`｜`Detail Sector`
- 方向明细 JSON 示例：
  `[{"标的":"黄金","板块":"Precious Metals","方向":"看多","期限":"长期"},{"标的":"长久期美债","板块":"Macro","方向":"强烈看空","期限":"短期"}]`
