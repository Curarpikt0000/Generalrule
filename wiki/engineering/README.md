# Engineering 领域知识

这里存放软件工程、系统架构、云部署和第三方 API 集成等通用工程实践的经验与教训。

## 页面列表

* [[github-actions-rate-limit-mitigation]] - GitHub Actions 定时任务中 GitHub API 限流防护
* [[notion-dedup-fail-loud]] - Notion API 去重校验防静默失败与 Fail Loud 协议
* [[notion-pagination-validation]] - Notion 数据验证必须循环翻页
* [[agent-dedup-double-insurance]] - Agent 去重双保险：音视频转换流水线必读规则
* [[google-antigravity]] - Google Antigravity SDK 开发指南与最佳实践
* [[gcp-cloud-run-deployment]] - GCP Cloud Run 部署与超时管理
* [[gcp-iam-runtime-permissions]] - GCP IAM 运行时服务账号最小权限控制
* [[pathlib-vs-ospath]] - Python 路径处理推荐使用 pathlib 避免斜杠混用
* [[url-fidelity]] - 爬虫与 API 数据管道中的 URL 保真度协议
* [[skill-check-before-coding]] - 动手编写代码前强制检索 Skill 机制
* [[youtube-pipeline-genimages-template-issue]] - YouTube 音频转换管道与图片生成模版常见问题
* [[container-reboot-service-persistence]] - 容器重启后服务恢复与开机持久化（临时 /etc 陷阱、幂等 boot 脚本、setsid、watchdog 循环依赖、自愈的认证升级边界、端口漂移、调用链排障）
* [[polling-bidirectional-bot-and-source-timeout-isolation]] - 轮询式双向消息机器人（无事件回调时用读 API+游标）+ 多源管道单源硬超时隔离（ThreadPoolExecutor 硬超时陷阱、shutdown(wait=False)、僵线程拖住退出、os._exit）
* [[uber-hermes-web-search-stack]] - 公网搜索工具栈与兜底层级（**SearXNG 主力**；usearch CLI 逐级 backup 封装；Cerberus idle 保活根治）。🔴 GenAI Gateway grounded **只是项目级可选辅助兜底、非标准搜索步骤**——AI-Guard 对人名做 PII 匿名化，搜人名不可靠，默认走 SearXNG。
