# Vercel 前端对接：流式对话（SSE）

本文档面向学习项目，目标是**最小成本跑通“流式输出”**，并保留清晰的扩展点。

## 1. 后端启动

### 1.1 安装依赖

```bash
pip install -r requirements.txt
```

### 1.2 配置模型 Key

把 `.env.example` 复制为 `.env`，按你的供应商填写：

- DashScope/Qwen（OpenAI 兼容）：`DASHSCOPE_API_KEY`、`DASHSCOPE_BASE_URL`
- OpenAI：`OPENAI_API_KEY`

模型名在 `config/config.yaml` 里配置（例如 `qwen-plus`）。

### 1.3 启动 API

```bash
uvicorn src.api.app:app --host 0.0.0.0 --port 8000 --reload
```

健康检查：

```bash
curl http://localhost:8000/healthz
```

## 2. 接口说明

### 2.1 非流式：POST /api/chat

请求：

```json
{
  "messages": [
    {"role": "user", "content": "用一句话介绍 LangChain"}
  ]
}
```

响应：

```json
{
  "reply": "..."
}
```

### 2.2 流式：POST /api/chat/stream

请求 JSON 与 `/api/chat` 相同。

响应类型：`text/event-stream`，每帧为一条 JSON（使用 SSE 协议封装）：

- 增量：`{"type":"delta","content":"..."}`
- 完成：`{"type":"done"}`
- 错误：`{"type":"error","message":"..."}`

用 curl 体验流式（重要：加 `-N` 禁用缓冲）：

```bash
curl -N http://localhost:8000/api/chat/stream \
  -H 'Content-Type: application/json' \
  -d '{"messages":[{"role":"user","content":"写一首四句小诗"}]}'
```

## 3. Vercel / Next.js 前端接入（推荐：fetch 读取流）

SSE 在浏览器里有两种常见接法：

- `EventSource`：只支持 GET，且不方便携带 header（不适合 POST/鉴权扩展）
- `fetch` + `ReadableStream`：更通用，**推荐**

下面示例使用 `fetch` 读取 SSE 数据帧。

### 3.1 环境变量

在 Vercel 项目里新增环境变量：

- `NEXT_PUBLIC_BACKEND_URL`：例如 `https://your-backend.example.com`

本地开发可以在 `.env.local` 写：

```bash
NEXT_PUBLIC_BACKEND_URL=http://localhost:8000
```

### 3.2 前端工具函数（可直接复制）

创建 `lib/chatStream.ts`：

```ts
export type StreamEvent =
  | { type: "meta"; request_id: string }
  | { type: "delta"; content: string }
  | { type: "done" }
  | { type: "error"; message: string };

function parseSseFrames(buffer: string): { events: StreamEvent[]; rest: string } {
  const parts = buffer.split("\n\n");
  const rest = parts.pop() ?? "";
  const events: StreamEvent[] = [];

  for (const part of parts) {
    const lines = part.split("\n");
    for (const line of lines) {
      if (!line.startsWith("data: ")) continue;
      const json = line.slice("data: ".length);
      try {
        events.push(JSON.parse(json));
      } catch {
        // 学习项目：忽略解析失败的帧
      }
    }
  }

  return { events, rest };
}

export async function chatStream(params: {
  messages: { role: "system" | "user" | "assistant"; content: string }[];
  onDelta: (text: string) => void;
  onDone?: () => void;
}): Promise<void> {
  const baseUrl = process.env.NEXT_PUBLIC_BACKEND_URL;
  if (!baseUrl) throw new Error("Missing NEXT_PUBLIC_BACKEND_URL");

  const res = await fetch(`${baseUrl}/api/chat/stream`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ messages: params.messages }),
  });

  if (!res.ok || !res.body) {
    const text = await res.text().catch(() => "");
    throw new Error(`HTTP ${res.status} ${text}`);
  }

  const reader = res.body.getReader();
  const decoder = new TextDecoder("utf-8");
  let buf = "";

  while (true) {
    const { value, done } = await reader.read();
    if (done) break;
    buf += decoder.decode(value, { stream: true });
    const { events, rest } = parseSseFrames(buf);
    buf = rest;

    for (const ev of events) {
      if (ev.type === "delta") params.onDelta(ev.content);
      if (ev.type === "done") params.onDone?.();
      if (ev.type === "error") throw new Error(ev.message);
    }
  }
}
```

### 3.3 React 组件示例

```tsx
import { useState } from "react";
import { chatStream } from "@/lib/chatStream";

export default function ChatDemo() {
  const [input, setInput] = useState("");
  const [answer, setAnswer] = useState("");
  const [loading, setLoading] = useState(false);

  async function onSend() {
    setAnswer("");
    setLoading(true);
    try {
      await chatStream({
        messages: [{ role: "user", content: input }],
        onDelta: (t) => setAnswer((prev) => prev + t),
        onDone: () => setLoading(false),
      });
    } catch (e: any) {
      setLoading(false);
      setAnswer(`错误：${e?.message ?? String(e)}`);
    }
  }

  return (
    <div style={{ maxWidth: 720, margin: "40px auto" }}>
      <h1>流式对话 Demo</h1>
      <textarea value={input} onChange={(e) => setInput(e.target.value)} rows={4} style={{ width: "100%" }} />
      <button onClick={onSend} disabled={loading || !input.trim()}>
        {loading ? "生成中..." : "发送"}
      </button>
      <pre style={{ whiteSpace: "pre-wrap" }}>{answer}</pre>
    </div>
  );
}
```

## 4. CORS（跨域）说明

后端默认 `CORS_ORIGINS="*"`（学习阶段方便调试）。

如果你想收紧到你的 Vercel 域名（推荐后续再做），设置：

```bash
CORS_ORIGINS=https://your-app.vercel.app
```

## 5. 常见问题

### 5.1 为什么不把模型 API Key 放前端？

因为前端代码会暴露给用户。**正确做法是 Key 只放后端**，前端只调用你自己的 `/api/chat/*`。

### 5.2 Vercel Serverless 能不能直接跑 SSE 后端？

很多 Serverless 环境会对响应做缓冲或有连接时长限制，流式体验不稳定。学习项目建议：

- 前端部署在 Vercel
- 后端用可长连接的服务部署（本地、云主机、Fly.io、Render 等）

