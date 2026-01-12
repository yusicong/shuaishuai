
## 实现了什么

### 1. 流式对话 API (SSE)
为了方便对接类似 ChatGPT 的前端体验，我实现了一个基于 Server-Sent Events (SSE) 的接口。相比 WebSocket，它更轻量，也更适合 LLM 这种“逐字吐出”的场景。

- **普通对话**: `/api/chat` (一次性返回)
- **流式对话**: `/api/chat/stream` (实时推送 Token)

如果你需要对接前端（比如 Vercel AI SDK），可以参考我写的这篇笔记：[docs/vercel_流式对话对接.md](docs/vercel_流式对话对接.md)

### 2. 向量数据库集成
为了使用 RAG，接入了 **ChromaDB**。
- 代码在 `src/core/vector_store.py` 和 `src/utils/vector_utils.py`。
- 目前支持简单的文本存入和相似度搜索，数据会持久化保存在 `data/vector_db` 下。

## 怎么跑起来

环境配置比较简单，我尽量保持了依赖的精简。

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 启动服务 (默认 8000 端口)
uvicorn src.api.app:app --host 0.0.0.0 --port 8000 --reload
```

## 项目结构

为了避免代码写着写着就乱了（毕竟 Python 比较灵活），我参考了一些工程化规范，整理了目前的目录结构：

```text
lang-all/
├── config/                 # 配置相关
├── data/                   # 数据存储 (向量库数据在这里)
├── docs/                   # 学习过程中的文档记录
├── notebooks/              # 用于快速实验的 Jupyter Notebooks
├── src/                    # 核心代码
│   ├── api/                # FastAPI 接口层
│   ├── chains/             # LangChain 的 Chain 定义
│   ├── core/               # 核心组件 (配置、数据库连接)
│   ├── graphs/             # LangGraph 图定义 (正在研究中)
│   └── utils/              # 工具类
├── tests/                  # 测试代码
└── .env                    # 环境变量 (API Key 放这里)
```


