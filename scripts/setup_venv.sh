#!/usr/bin/env bash
# 创建并初始化项目虚拟环境（macOS/Linux）
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$PROJECT_ROOT"

VENV_DIR=".venv"

echo "[1/3] 创建虚拟环境：$VENV_DIR"
python3 -m venv "$VENV_DIR"

echo "[2/3] 激活虚拟环境并升级 pip"
source "$VENV_DIR/bin/activate"
python -m pip install --upgrade pip

echo "[3/3] 安装依赖 requirements.txt"
pip install -r requirements.txt

echo "✅ 虚拟环境就绪。使用方式：\n  source .venv/bin/activate"

