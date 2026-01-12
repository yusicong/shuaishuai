# `/api/chat/stream` 完整对接文档（SSE 流式对话）

本文档**只包含**一个接口：`POST /api/chat/stream`。用于在浏览器/前端以流式方式接收模型输出（边生成边显示）。

## 1. 接口概览

- **Method**：`POST`
- **Path**：`/api/chat/stream`
- **Content-Type（请求）**：`application/json`
- **Content-Type（响应）**：`text/event-stream`
- **协议**：SSE（Server-Sent Events），每一帧携带一段 JSON 数据

适用场景：
- Chat UI 逐字/逐段输出
- 前端希望拿到“增量 token”并实时渲染

不适用/不推荐：
- 需要双向实时通信（那更适合 WebSocket）

## 2. 请求（Request）

### 2.1 Headers

必须：
- `Content-Type: application/json`

可选（取决于你是否加了鉴权；当前学习项目默认不需要）：
- `Authorization: Bearer <token>`

### 2.2 Body（JSON）

```json
{
  "messages": [
    { "role": "user", "content": "写一首四句小诗" }
  ],
  "system_prompt": "（可选）覆盖默认 system prompt"
}
```

字段说明：
- `messages`：消息数组，包含历史对话（如有）
  - `role`：`system | user | assistant`
  - `content`：纯文本内容
- `system_prompt`：可选。若传入，会覆盖后端默认的 system prompt

学习项目建议的最小用法：
- 只传一个 `user` 消息即可跑通流式输出

## 3. 响应（Response）

### 3.1 响应格式：SSE 帧

响应以 **SSE** 方式持续输出，直到完成。每一帧格式如下：

```text
event: message
data: {"type":"delta","content":"..."}

```

说明：
- 每一帧以空行（`\n\n`）结束
- `data:` 后面是一个 JSON 字符串（UTF-8）
- 当前后端固定使用 `event: message`，你只需要解析 `data:` 即可

### 3.2 `data` JSON 结构

后端会输出以下几类事件（`type` 字段区分）：

1) 元信息（可用于 debug/链路追踪）

```json
{ "type": "meta", "request_id": "req_..." }
```

2) 增量输出（最重要）

```json
{ "type": "delta", "content": "本次新增的一小段文本" }
```

3) 结束

```json
{ "type": "done" }
```

4) 错误（通常是模型调用失败、配置缺失等）

```json
{ "type": "error", "message": "错误信息" }
```

前端处理建议：
- 收到 `delta`：把 `content` 追加到 UI 上
- 收到 `done`：停止 loading 状态
- 收到 `error`：显示错误并停止

## 4. cURL 调试（最小可复现）

重要参数：
- `-N`：禁用 curl 缓冲，才能实时看到流式输出

```bash
curl -N http://localhost:8000/api/chat/stream \
  -H 'Content-Type: application/json' \
  -d '{"messages":[{"role":"user","content":"写一首四句小诗"}]}'
```

你会看到多行类似输出：

```text
event: message
data: {"type":"meta","request_id":"req_..."}

event: message
data: {"type":"delta","content":"..."}

event: message
data: {"type":"done"}

```

## 5. 前端对接（Vercel / Next.js）：推荐 fetch + ReadableStream

为什么不推荐 `EventSource`：
- `EventSource` 只能 GET，请求体不方便携带 `messages`
- 很难带自定义 header（例如后续做鉴权）

因此这里推荐用 `fetch` 读取响应流，并手动解析 SSE 帧。

### 5.1 环境变量

在 Vercel 配置：
- `NEXT_PUBLIC_BACKEND_URL`：后端地址，如 `https://your-backend.example.com`

本地开发可写 `.env.local`：

```bash
NEXT_PUBLIC_BACKEND_URL=http://localhost:8000
```

### 5.2 解析 SSE 的工具函数（TypeScript）

创建 `lib/sseChatStream.ts`：

```ts
export type ChatRole = "system" | "user" | "assistant";
export type ChatMessage = { role: ChatRole; content: string };

export type StreamEvent =
  | { type: "meta"; request_id: string }
  | { type: "delta"; content: string }
  | { type: "done" }
  | { type: "error"; message: string };

/**
 * 将“可能被分片”的文本缓冲区解析为 SSE 事件。
 *
 * 注意：
 * - SSE 帧以空行（\n\n）分隔
 * - 我们只解析以 "data: " 开头的行
 * - 解析后留下“半帧残留”给下一轮继续拼接
 */
function parseSse(buffer: string): { events: StreamEvent[]; rest: string } {
  const frames = buffer.split("\n\n");
  const rest = frames.pop() ?? "";
  const events: StreamEvent[] = [];

  for (const frame of frames) {
    for (const line of frame.split("\n")) {
      if (!line.startsWith("data: ")) continue;
      const jsonText = line.slice("data: ".length);
      try {
        events.push(JSON.parse(jsonText));
      } catch {
        // 学习项目：解析失败就跳过，避免中断（你也可以选择抛错）
      }
    }
  }

  return { events, rest };
}

/**
 * 调用 /api/chat/stream 并以回调方式接收增量输出。
 */
export async function chatStream(params: {
  messages: ChatMessage[];
  onDelta: (deltaText: string) => void;
  onMeta?: (meta: { request_id: string }) => void;
  onDone?: () => void;
}): Promise<void> {
  const baseUrl = process.env.NEXT_PUBLIC_BACKEND_URL;
  if (!baseUrl) throw new Error("缺少 NEXT_PUBLIC_BACKEND_URL");

  const res = await fetch(`${baseUrl}/api/chat/stream`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      // 预留：后续你做鉴权时可以加 Authorization
      // Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify({ messages: params.messages }),
  });

  // HTTP 层错误：直接读取文本，方便你调试后端返回的 errors
  if (!res.ok) {
    const text = await res.text().catch(() => "");
    throw new Error(`HTTP ${res.status}: ${text}`);
  }

  if (!res.body) {
    throw new Error("响应体为空：ReadableStream 不可用");
  }

  const reader = res.body.getReader();
  const decoder = new TextDecoder("utf-8");
  let buffer = "";

  while (true) {
    const { value, done } = await reader.read();
    if (done) break;

    // 将本次二进制分片解码成字符串，并拼接进缓冲区
    buffer += decoder.decode(value, { stream: true });

    // 从缓冲区里尽可能解析出完整 SSE 帧
    const { events, rest } = parseSse(buffer);
    buffer = rest;

    for (const ev of events) {
      if (ev.type === "meta") params.onMeta?.({ request_id: ev.request_id });
      if (ev.type === "delta") params.onDelta(ev.content);
      if (ev.type === "done") params.onDone?.();
      if (ev.type === "error") throw new Error(ev.message);
    }
  }
}
```

### 5.3 React 组件最小示例（逐段追加文本）

```tsx
import { useState } from "react";
import { chatStream } from "@/lib/sseChatStream";

export default function ChatStreamDemo() {
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
      <h1>/api/chat/stream 流式对话</h1>
      <textarea
        rows={4}
        style={{ width: "100%" }}
        value={input}
        onChange={(e) => setInput(e.target.value)}
      />
      <button disabled={loading || !input.trim()} onClick={onSend}>
        {loading ? "生成中..." : "发送"}
      </button>
      <pre style={{ whiteSpace: "pre-wrap" }}>{answer}</pre>
    </div>
  );
}
```

## 6. 线上部署与常见坑（Vercel 相关）

### 6.1 不要把模型 Key 放前端

前端代码会被用户看到。模型 Key 必须只在后端环境中保存，前端只调用你的 `/api/chat/stream`。

### 6.2 Serverless 对 SSE 支持可能不稳定

很多 Serverless 平台会对响应做缓冲，导致“流式变成一次性返回”。学习项目建议：
- 前端部署在 Vercel
- 后端部署在支持长连接/流式的环境（本地、云主机、Fly.io、Render 等）

### 6.3 CORS

如果你在浏览器直接请求后端域名，需要后端允许跨域。

当前后端支持通过环境变量设置：

```bash
CORS_ORIGINS=*
```

想收紧到指定域名：

```bash
CORS_ORIGINS=https://your-app.vercel.app
```

