#!/usr/bin/env bash
# 启动 HTTP API（含 SSE 流式对话）
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$PROJECT_ROOT"

VENV_DIR=".venv"
if [ ! -d "$VENV_DIR" ]; then
  echo "未找到虚拟环境 .venv，请先执行：scripts/setup_venv.sh"
  exit 1
fi

echo "激活虚拟环境并启动 API Server"
source "$VENV_DIR/bin/activate"
uvicorn src.api.app:app --host 0.0.0.0 --port 8000 --reload

