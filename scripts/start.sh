#!/usr/bin/env bash
# 启动示例程序（需先创建并激活虚拟环境）
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$PROJECT_ROOT"

VENV_DIR=".venv"
if [ ! -d "$VENV_DIR" ]; then
  echo "未找到虚拟环境 .venv，请先执行：scripts/setup_venv.sh"
  exit 1
fi

echo "激活虚拟环境并运行示例"
source "$VENV_DIR/bin/activate"
python -m src.main
