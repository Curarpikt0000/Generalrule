#!/bin/bash
# 构建 + 导出 Economy-KOL-to-Notion 知识包镜像
# 用法: bash build.sh
set -e
cd "$(dirname "$0")"

IMAGE="economy-kol-to-notion-knowledge"
TAG="${1:-latest}"

echo "=== 构建镜像 $IMAGE:$TAG ==="
docker build -t "$IMAGE:$TAG" .

echo "=== 镜像信息 ==="
docker images "$IMAGE:$TAG"

echo "=== 导出为 tar (便于分发/离线加载) ==="
docker save "$IMAGE:$TAG" | gzip > "$IMAGE-$TAG.tar.gz"
ls -lh "$IMAGE-$TAG.tar.gz"

echo ""
echo "✅ 完成。使用方式:"
echo "  docker load < $IMAGE-$TAG.tar.gz          # 加载镜像"
echo "  docker run --rm $IMAGE:$TAG                # 看引导 AGENT_START_HERE"
echo "  docker run --rm $IMAGE:$TAG cat /knowledge/README.md      # 读项目逻辑"
echo "  docker run --rm $IMAGE:$TAG cat /knowledge/ops/RUNBOOK.md # 读运维机制"
echo "  docker run --rm -it $IMAGE:$TAG sh        # 进容器浏览全部 /knowledge"
