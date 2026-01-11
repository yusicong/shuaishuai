"""
HTTP API 请求/响应结构（Pydantic）。

设计目标：
1. 结构尽量接近前端常用的 OpenAI Chat 格式（messages），降低学习与迁移成本；
2. 保持字段最小化：学习项目先跑通流式，再逐步扩展（例如 tools、RAG、用户态会话等）。
"""

from __future__ import annotations

from typing import List, Literal, Optional

from pydantic import BaseModel, Field


Role = Literal["system", "user", "assistant", "tool"]


class ChatMessage(BaseModel):
    role: Role
    content: str = Field(default="", description="消息内容（纯文本）")
    name: Optional[str] = Field(default=None, description="工具名称（当 role=tool 时必填）")
    tool_call_id: Optional[str] = Field(default=None, description="工具调用ID（当 role=tool 时必填）")
    tool_calls: Optional[List[dict]] = Field(default=None, description="助手生成的工具调用列表")


class ChatRequest(BaseModel):
    messages: List[ChatMessage] = Field(default_factory=list, description="对话消息列表（含历史）")
    system_prompt: Optional[str] = Field(default=None, description="可选：覆盖默认 system prompt")
    max_history_messages: int = Field(default=20, description="最大历史消息数量（保留最新的 N 条）")
    use_tools: bool = Field(default=True, description="是否启用工具调用（如网络搜索），默认开启")


class ChatResponse(BaseModel):
    reply: str

