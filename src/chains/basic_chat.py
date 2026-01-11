"""
最小对话链（可扩展版）：

设计目标（学习项目，避免过度设计）：
1. 把“模型初始化 / Prompt / 回调”等与入口（CLI、HTTP、测试）解耦；
2. 统一消息结构：输入使用 messages（role/content），便于后续做多轮、工具调用、RAG 等扩展；
3. 同时支持一次性返回（invoke）与流式输出（stream）。
"""

from __future__ import annotations

import os
from typing import Iterable, List, Optional

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import ChatOpenAI
from langfuse.langchain import CallbackHandler

from src.config import AppConfig


def build_callbacks(cfg: AppConfig) -> list:
    """
    构造 LangChain callbacks（当前仅接入 Langfuse）。

    说明：
    - 这里用“按需开启”的方式：只有配置了 Langfuse key 才创建 handler；
    - 后续你要接入更多观测/日志/指标，只要在这里追加即可，入口代码无需改动。
    """

    if not (cfg.langfuse.secret_key and cfg.langfuse.public_key):
        return []

    os.environ["LANGFUSE_SECRET_KEY"] = cfg.langfuse.secret_key
    os.environ["LANGFUSE_PUBLIC_KEY"] = cfg.langfuse.public_key
    os.environ["LANGFUSE_HOST"] = cfg.langfuse.host
    return [CallbackHandler()]


def build_llm(cfg: AppConfig) -> ChatOpenAI:
    """
    根据配置创建 LLM（当前使用 langchain-openai 的 ChatOpenAI）。

    说明：
    - DashScope/Qwen：通过 OpenAI 兼容接口调用，需要 base_url + api_key + model；
    - OpenAI：使用 api_key + model；
    - 后续扩展其他供应商时，建议把“创建 LLM”的分支逻辑集中维护在这里。
    """

    provider = (cfg.provider or "dashscope").lower()
    if provider == "dashscope":
        return ChatOpenAI(
            api_key=cfg.dashscope.api_key,
            base_url=cfg.dashscope.base_url,
            model=cfg.dashscope.model,
            temperature=cfg.dashscope.temperature,
        )

    return ChatOpenAI(
        api_key=cfg.openai.api_key,
        model=cfg.openai.model,
        temperature=cfg.openai.temperature,
    )


def build_chat_chain(cfg: AppConfig, system_prompt: Optional[str] = None):
    """
    构建一个面向“消息列表 messages”的对话链。

    输入：
    - {"messages": [BaseMessage, ...]}

    输出：
    - str（模型最终输出的文本）

    为什么用 MessagesPlaceholder：
    - 你可以直接把“历史对话消息”作为列表传进来；
    - 后续加 Memory / RAG / 工具调用时，接口形态依旧稳定。
    """

    system_prompt = system_prompt or "你是一个乐于助人的中文 AI 助手，回答要简洁明了。"

    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", system_prompt),
            MessagesPlaceholder("messages"),
        ]
    )
    llm = build_llm(cfg)
    return prompt | llm | StrOutputParser()


def to_langchain_messages(messages: Iterable[dict]) -> List[BaseMessage]:
    """
    把前端常见的 {role, content} 消息结构转换为 LangChain 的 Message 对象。

    支持角色：
    - system / user / assistant
    """

    result: List[BaseMessage] = []
    for m in messages or []:
        role = (m.get("role") or "").strip().lower()
        content = m.get("content") or ""
        if role == "system":
            result.append(SystemMessage(content=content))
        elif role == "assistant":
            result.append(AIMessage(content=content))
        else:
            result.append(HumanMessage(content=content))
    return result


def stream_text(chain, *, messages: List[BaseMessage], callbacks: Optional[list] = None) -> Iterable[str]:
    """
    同步流式输出：逐段 yield 文本增量。

    说明：
    - 这里保持“纯文本增量”的抽象，HTTP 层可以自由选择封装成 SSE、WebSocket 等；
    - 后续若要切换到 async（支持 astream），可以新增 async 版本而不破坏现有接口。
    """

    config = {"callbacks": callbacks} if callbacks else {}
    for chunk in chain.stream({"messages": messages}, config=config):
        if chunk:
            yield str(chunk)

