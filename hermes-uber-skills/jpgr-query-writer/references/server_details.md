# MCP Server Reference

### usearch-backend
uSearch / Glean search + document retrieval over Uber's internal knowledge
(EngWiki/Confluence, Google Drive, Databook, Jira, StackOverflow, etc.). Returns
raw search results and document content — no AI answer layer.

Typical use in this skill:
- Re-fetch the JPGR Query Repo sheet or KPI dashboard sheet when the baked-in
  `query_repo.md` catalog may be stale (`getdocuments` with the sheet URL and
  `includeFields: ["DOCUMENT_CONTENT"]`).
- Confirm a Hive table's existence/columns via Databook or find a documented
  QueryBuilder / Query Copilot pattern before returning SQL (`searchv2`).

Access pattern (through omni-mcp):
1. `discover_tools` with `{"server_name": "usearch-backend"}` if tool names are unknown.
2. `get_tool_schema` for the selected tool (e.g. `usearchbackend_getdocuments`, `usearchbackend_searchv2`).
3. `invoke_tool` with `{"server": "usearch-backend", "tool": "<tool>", "arguments": {...}}`.

Notes:
- `getdocuments` honors only the FIRST document spec per call; send one call per URL.
- Large sheet exports may be truncated/persisted to a file path in the tool
  result — read that path to get full content.
