"""
工具调用对话链（中文注释）。

功能：
- 集成 Serper 网络搜索工具，让 LLM 在需要时调用
- 支持流式输出（增量 token）
- 保持与基础对话链相同的接口（messages 输入）

设计思路：
1. 创建工具实例并绑定到 LLM
2. 使用 MessagesPlaceholder 接收历史消息
3. 处理工具调用：如果 LLM 返回工具调用，则执行工具并将结果添加为 ToolMessage
4. 继续生成最终回复

参考：https://python.langchain.com/docs/how_to/tool_calling/
"""

from __future__ import annotations

import json
from typing import Iterable, List, Optional, Union

from langchain_core.messages import (
    AIMessage,
    BaseMessage,
    HumanMessage,
    SystemMessage,
    ToolMessage,
)
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables import Runnable, RunnableConfig
from langchain_openai import ChatOpenAI
from langfuse.langchain import CallbackHandler

from src.config import AppConfig
from src.tools import create_serper_search_tool, create_current_time_tool
from src.utils.logger import logger


def build_callbacks(cfg: AppConfig) -> list:
    """
    构造 LangChain callbacks（当前仅接入 Langfuse）。

    说明：
    - 这里用"按需开启"的方式：只有配置了 Langfuse key 才创建 handler；
    - 后续你要接入更多观测/日志/指标，只要在这里追加即可，入口代码无需改动。
    """
    from src.chains.basic_chat import build_callbacks as basic_build_callbacks
    return basic_build_callbacks(cfg)


def build_llm(cfg: AppConfig) -> ChatOpenAI:
    """
    根据配置创建 LLM（复用基础链的逻辑）。
    """
    from src.chains.basic_chat import build_llm as basic_build_llm
    return basic_build_llm(cfg)


def create_tool_calling_chain(cfg: AppConfig, system_prompt: Optional[str] = None) -> Runnable:
    """
    创建支持工具调用的对话链。

    返回的链接受输入：{"messages": List[BaseMessage]}
    输出：AIMessage（可能包含工具调用或最终回复）

    工作流程：
    1. LLM 接收消息历史
    2. LLM 决定是否调用工具
    3. 如果调用工具，执行工具并将结果作为 ToolMessage 添加
    4. 再次调用 LLM 生成最终回复
    """
    # 创建工具实例（使用配置参数）
    search_tool = create_serper_search_tool(
        gl=cfg.serper.gl,
        hl=cfg.serper.hl,
        location=cfg.serper.location
    )
    time_tool = create_current_time_tool()
    
    # 创建 LLM 并绑定工具
    llm = build_llm(cfg)
    llm_with_tools = llm.bind_tools([search_tool, time_tool])
    
    # 系统提示
    base_system_prompt = (
        "你是一个乐于助人的中文 AI 助手，可以调用网络搜索工具获取最新信息。\n"
        "当用户询问需要实时数据、新闻、公司信息等问题时，你应该调用搜索工具。\n"
        "如果搜索查询中包含相对时间（如'今年'、'最近'），请先调用 current_time 工具获取准确的当前时间，再构造包含具体年份的搜索查询。\n"
        "使用工具后，根据搜索结果给出准确、简洁的回答。\n"
        "如果搜索结果不充分或没有找到相关信息，请如实告知用户。"
    )
    
    # 如果用户提供了 system_prompt，我们将其与工具说明合并
    # 这样既保留了用户的个性化设定，又确保了工具调用的引导
    if system_prompt:
        system_prompt = f"{system_prompt}\n\n【工具使用说明】\n{base_system_prompt}"
    else:
        system_prompt = base_system_prompt
    
    logger.debug(f"Tool calling chain system prompt: {system_prompt[:100]}...")

    # 构建提示模板
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        MessagesPlaceholder("messages"),
    ])
    
    # 创建链：提示 -> LLM（带工具）-> 输出解析
    chain = prompt | llm_with_tools
    
    return chain


def process_tool_calls(
    chain: Runnable,
    messages: List[BaseMessage],
    callbacks: list = None,
    max_iterations: int = 3
) -> Iterable[str]:
    """
    处理工具调用迭代，生成最终回复的流式输出。

    算法：
    1. 将当前消息传入链，得到 AIMessage
    2. 检查是否有 tool_calls
    3. 如果有，执行每个工具调用，将结果添加为 ToolMessage
    4. 将新的 ToolMessage 添加到消息列表，重复步骤1
    5. 如果没有 tool_calls，则返回 AIMessage 的内容

    参数：
        chain: 调用工具链
        messages: 当前消息历史
        callbacks: 回调函数列表
        max_iterations: 最大迭代次数，防止无限循环

    返回：
        生成器，逐段产出最终回复文本
    """
    config = {"callbacks": callbacks} if callbacks else {}
    
    # 提前加载配置，避免循环中重复加载
    from src.config import load_config
    cfg = load_config()
    # 预创建工具实例
    search_tool = create_serper_search_tool(
        gl=cfg.serper.gl,
        hl=cfg.serper.hl,
        location=cfg.serper.location
    )
    time_tool = create_current_time_tool()
    
    for iteration in range(max_iterations):
        # 调用链获取响应
        logger.debug(f"Iteration {iteration + 1}: Invoking LLM (streaming)...")
        
        # 详细记录输入消息
        if logger.level("DEBUG"):
            for i, msg in enumerate(messages):
                content_preview = str(msg.content)[:100] + "..." if len(str(msg.content)) > 100 else str(msg.content)
                logger.debug(f"Chain Input Msg[{i}] ({type(msg).__name__}): {content_preview}")

        # 使用 chain.stream 替代 chain.invoke
        final_chunk = None
        for chunk in chain.stream(
            {"messages": messages},
            config=config
        ):
            if final_chunk is None:
                final_chunk = chunk
            else:
                final_chunk += chunk
            
            # 如果有文本内容，实时 yield
            if chunk.content:
                yield chunk.content
        
        # 流结束，final_chunk 是完整的 AIMessage (Chunk)
        response = final_chunk
        
        # 详细记录 LLM 原始响应
        if logger.level("DEBUG"):
            logger.debug(f"LLM Response Content: {response.content}")
            if response.tool_calls:
                logger.debug(f"LLM Response Tool Calls: {response.tool_calls}")
        
        # 检查是否有工具调用
        if response.tool_calls:
            logger.info(f"Tool calls detected: {len(response.tool_calls)}")
            # 执行每个工具调用
            for tool_call in response.tool_calls:
                tool_name = tool_call["name"]
                tool_args = tool_call["args"]
                
                logger.info(f"Executing tool: {tool_name} with args: {tool_args}")
                
                # 查找工具实例
                if tool_name == "serper_search":
                    tool_result = search_tool._run(**tool_args)
                elif tool_name == "current_time":
                    tool_result = time_tool._run(**tool_args)
                else:
                    tool_result = {"error": f"未知工具: {tool_name}"}
                
                # 详细记录工具执行结果
                if logger.level("DEBUG"):
                    logger.debug(f"Tool result (full): {json.dumps(tool_result, ensure_ascii=False)}")
                else:
                    logger.debug(f"Tool result: {str(tool_result)[:200]}...")
                
                # 创建 ToolMessage
                tool_message = ToolMessage(
                    content=json.dumps(tool_result, ensure_ascii=False),
                    tool_call_id=tool_call["id"],
                    name=tool_name,
                )
                messages.append(response)  # 添加包含工具调用的 AIMessage
                messages.append(tool_message)  # 添加工具执行结果
        
        else:
            logger.debug("No tool calls, response already streamed.")
            # 没有工具调用，且内容已经在流式循环中 yield 过了，无需再次 yield
            break
        
        # 安全检查：防止无限循环
        if iteration >= max_iterations - 1:
            logger.warning("Max iterations reached, stopping.")
            yield "⚠️ 达到最大工具调用次数，停止迭代。"
            break


def to_langchain_messages(messages: Iterable[dict]) -> List[BaseMessage]:
    """
    把前端常见的 {role, content} 消息结构转换为 LangChain 的 Message 对象。

    支持角色：
    - system / user / assistant / tool
    """
    from src.chains.basic_chat import to_langchain_messages as basic_to_langchain_messages
    return basic_to_langchain_messages(messages)


def stream_tool_calling_text(
    chain: Runnable,
    messages: List[BaseMessage],
    callbacks: list = None,
    max_iterations: int = 3
) -> Iterable[str]:
    """
    流式输出工具调用链的最终回复。

    这是为了与基础链的 stream_text 函数保持接口一致。
    """
    yield from process_tool_calls(chain, messages, callbacks, max_iterations)