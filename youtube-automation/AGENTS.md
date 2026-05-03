# YouTube Automation — 项目规则 (AGENTS.md)

## 项目目标
将 Globalmagzineyoutube Google Drive 里的音频文件自动化生成 YouTube 视频。
支持杂志：Economist, Bloomberg, NewYorker, WSJ, Science

## Drive 结构（已验证真实 ID）
Root:             1tOVhkClasjoGUxtKIzyskFoGi3Zs1zy4
Economist/2026:   1uU2FXsUQFDfbp9JtuA5o4oICC6_jXuvy
Economist/audio:  1-bI__-1nRmWRGqTPHBMbNZtUSLluERac
Bloomberg/2026:   1FU1tDXCdMlEy0a-G8B1LY0pymNOPR_Zd
Bloomberg/audio:  1OdqqxLr1kufTfw0Z-yZdWnYSaNssVISs
NewYorker/2026:   1S4AE2FdyCHZRY66_-rAID7F8tXvtBRXi
NewYorker/audio:  1giVn8gmIpyb2Q14azKe7zYj4ynu0Y-3v
WSJ/2026:         1dh-eJb5a9u7ndlTlsaObcEgSXtnHPPsb
WSJ/audio:        11wI7h6Q-k6wV0k1pGZNc99qmjeEJC4et
Science/2026:     1h-rU6kVDZ0r1KnP-dtch8S5NmfVEaDFM
Science/audio:    18NRU8lblZ_mx1jLTHmFsQbSFtzjWlrBO

## Drive 工具调用规范
PYTHON=/home/curarpikt00/hermes_venv/bin/python3
TOOL=/home/curarpikt00/.hermes/skills/google_drive/drive_tool.py

所有 Drive 操作必须通过 terminal 工具执行上述脚本。
每次调用必须等待真实 JSON 返回，JSON 里的 id 才是真实 ID。
返回 error 字段时立刻停止，不得继续。

## 执行规约（最高优先级）
1. 任何文件操作必须通过真实工具调用完成，严禁在文本里描述"已执行"
2. 每步完成后必须用 list_folder 验证结果，验证失败立刻停止汇报
3. 工具不可用时直接说"工具 X 不可用"，不得绕过或模拟
4. 不确定时说"无法验证"，严禁猜测

## 流水线阶段
P1 监控    → list_audio 发现新文件
P2 建文件夹 → create_folder 在年份目录下建项目文件夹
P3 下载    → download 音频到 /tmp/
P4 转录    → Whisper STT（待配置）
P5 分析    → Claude 结构化提取逻辑块
P6 生图    → 图像生成 API（待配置）
P7 合成    → 视频渲染（待配置）
P8 上传    → YouTube Data API（待配置）

## Run-One-Check 规则
完成第一个视频全流程后必须停止，等待"确认继续"指令。
在获得确认前，禁止处理其他音频文件。

## 经验记录
所有经验按 general-global-rule.md 的 promote-lessons workflow 升级到 wiki/。
新增领域：~/.hermes/generalrule/wiki/ 下创建 media/ 或 podcast/ 目录。

## 标准目录结构（已验证）
[Magazine] / [Year] / video / [Magazine_YYYYMMDD] /   ← 项目文件夹
[Magazine] / [Year] / audio /                          ← 音频源文件（只读）

示例（Bloomberg）：
Bloomberg / 2026 / video / Bloomberg_20260401 /   ID: 1xLyjHrton78dYHY7YqLTCCIUsEb_w5oS
Bloomberg / 2026 / video /                        ID: 1ZodD0YCsfH2KhN6OJi6qTvle1SK_U9q-

P2 建文件夹顺序：
1. 检查 [Year] 下是否已有 video 文件夹（list_folder）
2. 没有则创建 video 文件夹
3. 在 video 下创建 [Magazine_YYYYMMDD] 项目文件夹

## OAuth 上传规范（2026-05-02 新增）
所有产物（文本、JSON、图片、视频）必须上传到 Drive 的项目文件夹做归档。
使用命令：
$PYTHON $TOOL oauth_upload <local_path> <project_folder_id>

OAuth token: /home/curarpikt00/.hermes/google_token.json
身份：curarpikt00@gmail.com（用户 OAuth，无配额限制）

每个 P 阶段完成后立刻上传产物到 Drive，不等用户要求。
