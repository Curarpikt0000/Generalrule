# Economy-KOL-to-Notion — 知识包镜像
# 未来 agent: docker run 即看引导, 镜像内 /knowledge 是全部内容(代码/文档/运维/skill/Notion坐标)
# 不含真实数据(KOL言论/Notion快照)和密钥 — 用你自己的 .env 连真实 Notion
FROM python:3.11-slim

LABEL org.opencontainers.image.title="economy-kol-to-notion-knowledge"
LABEL org.opencontainers.image.description="Economy-KOL-to-Notion 项目知识包: 逻辑/历史/未来工作/Notion坐标/运维机制/skill/脚本. 无数据无密钥."
LABEL org.opencontainers.image.source="https://github.com/Curarpikt0000/Generalrule"
LABEL maintainer="Curarpikt0000"

# 项目脚本依赖(可选, 让脚本能直接跑)
RUN pip install --no-cache-dir requests 2>/dev/null || true

WORKDIR /knowledge
COPY knowledge/ /knowledge/

# 把 env 模板放进 config/ 目录, 提示 agent 复制填写
RUN mkdir -p /knowledge/config && \
    cp /knowledge/config.env.example /knowledge/config/.env.example && \
    echo "复制 config/.env.example -> config/.env 并填入你自己的密钥(NOTION_TOKEN/EXA_API_KEY 等)" > /knowledge/config/README.txt

# 默认: 打印引导, 告诉 agent 从哪读起
CMD ["sh", "-c", "cat /knowledge/AGENT_START_HERE.md"]
