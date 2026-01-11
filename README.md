# LangChain + LangGraph 学习项目

本项目用于学习 Python、LangChain 和 LangGraph。

## 快速开始：流式对话 API（SSE）

本项目提供一个最小的 HTTP API，支持：
- 非流式对话：一次性返回
- 流式对话：SSE（服务端逐段推送模型输出）

### 启动

```bash
pip install -r requirements.txt
uvicorn src.api.app:app --host 0.0.0.0 --port 8000 --reload
```

### 文档

- 前端 Vercel/Next.js 对接流式输出：[docs/vercel_流式对话对接.md](docs/vercel_%E6%B5%81%E5%BC%8F%E5%AF%B9%E8%AF%9D%E5%AF%B9%E6%8E%A5.md)

## 目录结构规划

为了保持代码的整洁和可维护性，本项目采用以下目录结构：

```text
lang-all/
├── config/                 # 存放配置文件
│   └── settings.yaml       # (可选) 项目配置，如模型名称、API参数等
├── data/                   # 存放数据文件
│   ├── raw/                # 原始数据
│   ├── processed/          # 处理后的数据
│   └── vector_db/          # 向量数据库持久化目录
├── docs/                   # 项目文档
├── notebooks/              # Jupyter Notebooks，用于实验和演示
│   ├── 01_langchain_basics.ipynb
│   └── 02_langgraph_intro.ipynb
├── src/                    # 源代码目录
│   ├── __init__.py
│   ├── core/               # 核心逻辑
│   │   ├── config.py       # 配置加载逻辑
│   │   └── vector_store.py # 向量数据库服务
│   ├── chains/             # LangChain 链的定义
│   │   └── __init__.py
│   ├── api/                # HTTP API（含 SSE 流式对话）
│   │   └── app.py
│   ├── graphs/             # LangGraph 图的定义
│   │   └── __init__.py
│   ├── tools/              # 自定义工具 (Tools)
│   │   └── __init__.py
│   └── utils/              # 通用工具函数
│       ├── __init__.py
│       └── vector_utils.py # 向量数据库工具类
├── tests/                  # 测试代码
│   ├── __init__.py
│   └── test_main.py
├── .env                    # 环境变量 (包含 API Keys，不要提交到 Git)
├── .env.example            # 环境变量示例 (用于分享)
├── .gitignore              # Git 忽略文件配置
├── README.md               # 项目说明文档
└── requirements.txt        # 项目依赖包列表
```

## 目录说明

- **config/**: 用于存放项目的配置文件，将配置与代码分离。
- **data/**: 存放项目运行所需的数据文件。
- **docs/**: 存放更详细的项目文档或笔记。
- **notebooks/**: 这是一个非常重要的目录，用于存放 Jupyter Notebook (`.ipynb`) 文件。作为初学者，可以在这里进行代码实验、调试和快速验证想法。
- **src/**: 所有的源代码都应该放在这里。
    - **core/**: 存放核心配置和基础类。
    - **chains/**: 如果你使用 LangChain 构建特定的链（Chains），将它们定义在这里。
    - **graphs/**: LangGraph 的核心是图（Graph），将你的状态图定义放在这里。
    - **tools/**: 如果你自定义了供 Agent 使用的工具，放在这里。
    - **utils/**: 存放一些通用的辅助函数。
- **tests/**: 编写测试用例，确保代码的正确性。
- **.env**: 存放敏感信息，如 `OPENAI_API_KEY`。
- **requirements.txt**: 记录项目安装的 Python 包。

## 向量数据库 (ChromaDB)

本项目集成了 ChromaDB 作为向量数据库，用于检索增强生成 (RAG) 等场景。

### 初始化

在应用启动时，需要调用 `init_chroma_service()` 来初始化向量数据库服务：

```python
from src.core.vector_store import init_chroma_service

# 初始化向量数据库服务
init_chroma_service(persist_directory="./data/vector_db", embedding_model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")
```

### 使用工具类

项目提供了便捷的工具类 `VectorDBUtil` 来操作向量数据库：

```python
from src.utils.vector_utils import VectorDBUtil, add_texts, similarity_search

# 方法一：使用工具类实例
util = VectorDBUtil(collection_name="my_docs")
doc_ids = util.add_texts(["文档1内容", "文档2内容"], [{"source": "file1"}, {"source": "file2"}])
results = util.similarity_search("查询文本", k=2)

# 方法二：使用便捷函数
doc_ids = add_texts(["文档1内容", "文档2内容"], [{"source": "file1"}, {"source": "file2"}], collection_name="my_docs")
results = similarity_search("查询文本", k=2, collection_name="my_docs")
```

向量数据库会自动在 `./data/vector_db` 目录下进行持久化存储。
