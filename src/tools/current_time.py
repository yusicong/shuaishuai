"""
当前时间工具（中文注释）。

功能：
- 获取系统当前的日期和时间
- 帮助 LLM 在生成搜索查询时使用正确的时间上下文（例如“今年”是哪一年）
"""

from datetime import datetime
from typing import Any, Dict, Type

from langchain.tools import BaseTool
from pydantic import BaseModel, Field
from src.utils.logger import logger


class CurrentTimeInput(BaseModel):
    """
    当前时间工具的输入参数模型。
    实际上不需要任何参数，但为了符合 Tool 接口规范保留。
    """
    pass


class CurrentTimeTool(BaseTool):
    """
    获取当前系统时间的工具。
    
    返回格式：
    "2026-01-11 16:35:00 (Saturday)"
    """

    name: str = "current_time"
    description: str = (
        "获取当前的日期和时间。"
        "当你需要知道'今天'、'今年'是具体什么时间，或者需要基于当前时间构造搜索查询时，请使用此工具。"
    )
    args_schema: Type[BaseModel] = CurrentTimeInput
    return_direct: bool = False

    def _run(self, **kwargs: Any) -> str:
        """
        执行工具。

        Returns:
            格式化的当前时间字符串
        """
        logger.debug("Executing CurrentTimeTool")
        now = datetime.now()
        # 格式：YYYY-MM-DD HH:MM:SS (Weekday)
        formatted_time = now.strftime("%Y-%m-%d %H:%M:%S (%A)")
        logger.debug(f"Current time: {formatted_time}")
        return formatted_time


def create_current_time_tool(**kwargs) -> CurrentTimeTool:
    """
    创建 CurrentTimeTool 实例。
    """
    return CurrentTimeTool(**kwargs)
