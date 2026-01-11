"""
SSE（Server-Sent Events）工具函数。

说明：
SSE 本质是一个“按行/分帧”的文本协议，浏览器端可以用：
- fetch + ReadableStream 手动解析（推荐，支持 POST + 自定义 header）
- EventSource（仅 GET，且 header/鉴权能力受限）

为方便学习和后续扩展，这里把“协议拼帧”抽成独立模块。
"""

from __future__ import annotations

import json
from typing import Any, Dict, Optional


def sse_encode(data: Dict[str, Any], *, event: Optional[str] = None) -> str:
    """
    把一个 JSON 对象编码为 SSE frame 文本。

    返回值示例：
    event: message
    data: {"type":"delta","content":"你好"}

    （以空行结尾表示一帧结束）
    """

    payload = json.dumps(data, ensure_ascii=False)
    lines: list[str] = []
    if event:
        lines.append(f"event: {event}")
    lines.append(f"data: {payload}")
    return "\n".join(lines) + "\n\n"

