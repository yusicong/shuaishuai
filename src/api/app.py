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

from fastapi import FastAPI
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
from src.config import load_config, validate_config


def _parse_cors_origins(value: Optional[str]) -> list[str]:
    """
    解析 CORS_ORIGINS 环境变量。

    允许写法：
    - "*"（允许任意源，学习阶段最省事；正式环境建议收紧）
    - "https://a.com,https://b.com"
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

    @app.post("/api/chat", response_model=ChatResponse)
    def chat(req: ChatRequest):
        cfg = load_config()
        errors = validate_config(cfg)
        if errors:
            return JSONResponse(status_code=400, content={"errors": errors})

        chain = build_chat_chain(cfg, system_prompt=req.system_prompt)
        callbacks = build_callbacks(cfg)
        lc_messages = to_langchain_messages([m.model_dump() for m in req.messages])
        reply = chain.invoke({"messages": lc_messages}, config={"callbacks": callbacks} if callbacks else {})
        return ChatResponse(reply=str(reply))

    @app.post("/api/chat/stream")
    def chat_stream(req: ChatRequest):
        """
        SSE 流式输出协议（每帧为 JSON）：
        - {"type":"delta","content":"..."}：增量文本
        - {"type":"done"}：完成
        - {"type":"error","message":"..."}：错误
        """

        cfg = load_config()
        errors = validate_config(cfg)
        if errors:
            return JSONResponse(status_code=400, content={"errors": errors})

        chain = build_chat_chain(cfg, system_prompt=req.system_prompt)
        callbacks = build_callbacks(cfg)
        lc_messages = to_langchain_messages([m.model_dump() for m in req.messages])

        def gen() -> Iterable[str]:
            request_id = f"req_{int(time.time() * 1000)}"
            yield sse_encode({"type": "meta", "request_id": request_id}, event="message")
            try:
                for delta in stream_text(chain, messages=lc_messages, callbacks=callbacks):
                    yield sse_encode({"type": "delta", "content": delta}, event="message")
                yield sse_encode({"type": "done"}, event="message")
            except Exception as e:
                yield sse_encode({"type": "error", "message": str(e)}, event="message")

        return StreamingResponse(gen(), media_type="text/event-stream")

    return app


app = create_app()

