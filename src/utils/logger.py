"""
日志配置模块。

使用 loguru 提供统一的日志管理。
"""

import sys
from loguru import logger
from src.config import load_config

# 移除默认的 handler
logger.remove()

# 加载配置
cfg = load_config()
log_level = cfg.log_level.upper()

# 添加控制台输出
logger.add(
    sys.stderr,
    level=log_level,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"
)

# 可选：添加文件输出（按天轮转）
# logger.add("logs/app_{time}.log", rotation="1 day", level=log_level)

__all__ = ["logger"]