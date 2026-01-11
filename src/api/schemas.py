"""
HTTP API 请求/响应结构（Pydantic）。

设计目标：
1. 结构尽量接近前端常用的 OpenAI Chat 格式（messages），降低学习与迁移成本；
2. 保持字段最小化：学习项目先跑通流式，再逐步扩展（例如 tools、RAG、用户态会话等）。
"""

from __future__ import annotations

from typing import List, Literal, Optional

from pydantic import BaseModel, Field


Role = Literal["system", "user", "assistant"]


class ChatMessage(BaseModel):
    role: Role
    content: str = Field(default="", description="消息内容（纯文本）")


class ChatRequest(BaseModel):
    messages: List[ChatMessage] = Field(default_factory=list, description="对话消息列表（含历史）")
    system_prompt: Optional[str] = Field(default=None, description="可选：覆盖默认 system prompt")


class ChatResponse(BaseModel):
    reply: str

