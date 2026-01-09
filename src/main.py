"""
LangChain 使用示例（中文注释）：

功能说明：
- 读取配置（OPENAI_API_KEY、模型名等）
- 构建一个最简单的对话链：Prompt -> LLM -> 输出解析
- 运行后在终端打印回复结果
"""

import os
from typing import Dict
from src.config import load_config, validate_config

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_openai import ChatOpenAI
from langfuse.langchain import CallbackHandler


def build_chain(cfg) -> "StrOutputParser":
    """构建一个最小可用的 LangChain 链。"""
    # 定义对话模板：系统角色给出指令，用户角色提出问题
    prompt = ChatPromptTemplate.from_messages([
        ("system", "你是一个乐于助人的中文 AI 助手，回答要简洁明了。"),
        ("user", "{question}")
    ])

    # 根据 provider 初始化 LLM
    provider = (cfg.provider or "dashscope").lower()
    if provider == "dashscope":
        # 使用 OpenAI 兼容接口调用 Qwen（DashScope）
        llm = ChatOpenAI(
            api_key=cfg.dashscope.api_key,
            base_url=cfg.dashscope.base_url,
            model=cfg.dashscope.model,
            temperature=cfg.dashscope.temperature,
        )
    else:
        # 默认使用 OpenAI
        llm = ChatOpenAI(
            api_key=cfg.openai.api_key,
            model=cfg.openai.model,
            temperature=cfg.openai.temperature,
        )

    # 组合为链：Prompt -> LLM -> 字符串输出解析器
    chain = prompt | llm | StrOutputParser()
    return chain


def run_once(inputs: Dict[str, str]) -> str:
    """执行一次推理，返回字符串结果。"""
    cfg = load_config()
    errors = validate_config(cfg)
    if errors:
        # 友好提示用户填写配置
        print("配置缺失：")
        for e in errors:
            print(f"- {e}")
        print("\n请在 .env 或 config/config.yaml 中补齐后再运行。")
        raise SystemExit(1)
  
    # 初始化 Langfuse Handler
    langfuse_handler = None
    if cfg.langfuse.secret_key and cfg.langfuse.public_key:
        os.environ["LANGFUSE_SECRET_KEY"] = cfg.langfuse.secret_key
        os.environ["LANGFUSE_PUBLIC_KEY"] = cfg.langfuse.public_key
        os.environ["LANGFUSE_HOST"] = cfg.langfuse.host
        langfuse_handler = CallbackHandler()

    chain = build_chain(cfg)
    
    # 执行推理时传入 callbacks
    return chain.invoke(inputs, config={"callbacks": [langfuse_handler]} if langfuse_handler else {})


if __name__ == "__main__":
    # 简单示例：询问一个问题
    question = "用一句话介绍 LangChain 的用途"
    print("正在调用模型，请稍候...\n")
    answer = run_once({"question": question})
    print("模型回复：")
    print(answer)
