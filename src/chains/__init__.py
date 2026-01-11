"""
对话链模块（中文注释）。

导出的链与工具：
1. 基础对话链（无工具调用）：
   - build_chat_chain: 创建基础对话链
   - stream_text: 流式输出文本
   - to_langchain_messages: 消息格式转换

2. 工具调用对话链（支持网络搜索）：
   - create_tool_calling_chain: 创建支持工具调用的链
   - stream_tool_calling_text: 工具调用链的流式输出
   - process_tool_calls: 处理工具调用迭代

3. 工具：
   - SerperSearchTool: 网络搜索工具
   - create_serper_search_tool: 创建搜索工具实例
"""

from src.chains.basic_chat import (
    build_chat_chain,
    stream_text,
    to_langchain_messages,
)
from src.chains.tool_calling_chat import (
    create_tool_calling_chain,
    stream_tool_calling_text,
    process_tool_calls,
)
from src.tools import SerperSearchTool, create_serper_search_tool

__all__ = [
    # 基础链
    "build_chat_chain",
    "stream_text",
    "to_langchain_messages",
    # 工具调用链
    "create_tool_calling_chain",
    "stream_tool_calling_text",
    "process_tool_calls",
    # 工具
    "SerperSearchTool",
    "create_serper_search_tool",
]