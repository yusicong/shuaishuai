"""
会话记忆管理模块。

功能：
- 提供基于内存的会话历史存储（InMemoryChatMessageHistory）
- 按 Session ID 隔离不同的对话上下文
- 未来可扩展为 Redis 或数据库存储
"""

from langchain_core.chat_history import BaseChatMessageHistory, InMemoryChatMessageHistory
from langchain_core.messages import BaseMessage
from typing import Dict

# 全局内存存储
# 结构: {session_id: InMemoryChatMessageHistory}
_store: Dict[str, InMemoryChatMessageHistory] = {}


def get_session_history(session_id: str) -> BaseChatMessageHistory:
    """
    获取指定 Session ID 的聊天历史对象。
    如果不存在，则创建一个新的。
    """
    if session_id not in _store:
        _store[session_id] = InMemoryChatMessageHistory()
    return _store[session_id]


def clear_session_history(session_id: str):
    """
    清空指定 Session 的历史（可选功能）。
    """
    if session_id in _store:
        del _store[session_id]
