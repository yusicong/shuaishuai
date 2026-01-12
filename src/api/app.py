"""
最小 HTTP API（含 SSE 流式对话）。

为什么选择 SSE：
- 前端接入简单，浏览器原生支持；
- 适合“模型逐 token 输出”的场景；
- 相比 WebSocket 更轻量，学习成本更低。

路由说明：
- GET  /healthz           健康检查
- POST /api/chat          非流式：一次性返回 reply
- POST /api/chat/stream   流式：以 text/event-stream 返回增量 token
"""

from __future__ import annotations

import os
import time
from typing import Iterable, Optional

from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse

from src.api.schemas import ChatRequest, ChatResponse
from src.api.sse import sse_encode
from src.chains.basic_chat import (
    build_callbacks,
    build_chat_chain,
    stream_text,
    to_langchain_messages,
)
from src.chains.tool_calling_chat import (
    create_tool_calling_chain,
    stream_tool_calling_text,
)
from src.config import load_config, validate_config
from src.utils.logger import logger


def _parse_cors_origins(value: Optional[str]) -> list[str]:
    """
    解析 CORS_ORIGINS 环境变量。 （允许任意源）
    """

    if not value:
        return ["*"]
    value = value.strip()
    if value == "*":
        return ["*"]
    return [x.strip() for x in value.split(",") if x.strip()]


def create_app() -> FastAPI:
    app = FastAPI(title="lang-all API", version="0.1.0")

    allow_origins = _parse_cors_origins(os.getenv("CORS_ORIGINS"))
    app.add_middleware(
        CORSMiddleware,
        allow_origins=allow_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/healthz")
    def healthz():
        return {"ok": True}

    @app.post("/api/chat/stream")
    def chat_stream(
        req: ChatRequest,
        use_tools_query: bool = Query(None, alias="use_tools", description="是否启用工具调用（网络搜索），优先级高于 Body"),
    ):
        """
        SSE 流式输出协议（每帧为 JSON）：
        - {"type":"delta","content":"..."}：增量文本
        - {"type":"tool_start", ...}：工具调用开始
        - {"type":"tool_result", ...}：工具调用结果
        - {"type":"done"}：完成
        - {"type":"error","message":"..."}：错误
        
        参数：
        - session_id: 会话ID
        - query: 用户问题
        - use_tools: 是否启用工具
        """

        cfg = load_config()
        errors = validate_config(cfg)
        if errors:
            return JSONResponse(status_code=400, content={"errors": errors})

        # 确定 use_tools 的值：Query 参数优先，其次是 Body 参数
        final_use_tools = use_tools_query if use_tools_query is not None else req.use_tools
        
        logger.info(f"Received chat_stream request. session_id={req.session_id}, query={req.query[:50]}..., use_tools={final_use_tools}")
        
        if final_use_tools:
            logger.debug("Creating tool calling chain")
            chain = create_tool_calling_chain(cfg, system_prompt=req.system_prompt)
            stream_func = stream_tool_calling_text
        else:
            logger.debug("Creating basic chat chain")
            chain = build_chat_chain(cfg, system_prompt=req.system_prompt)
            stream_func = stream_text
        
        callbacks = build_callbacks(cfg)

        def gen() -> Iterable[str]:
            request_id = f"req_{int(time.time() * 1000)}"
            logger.debug(f"Starting stream for {request_id}")
            yield sse_encode({"type": "meta", "request_id": request_id}, event="message")
            try:
                # 调用流式函数，传入 session_id 和 query
                for chunk in stream_func(chain, session_id=req.session_id, query=req.query, callbacks=callbacks):
                    if isinstance(chunk, str):
                        yield sse_encode({"type": "delta", "content": chunk}, event="message")
                    elif isinstance(chunk, dict):
                        # 直接透传工具事件 (tool_start, tool_result)
                        yield sse_encode(chunk, event="message")
                
                yield sse_encode({"type": "done"}, event="message")
                logger.info(f"Stream finished for {request_id}")
            except Exception as e:
                logger.error(f"Stream error for {request_id}: {e}")
                yield sse_encode({"type": "error", "message": str(e)}, event="message")

        return StreamingResponse(gen(), media_type="text/event-stream")

    return app


app = create_app()

