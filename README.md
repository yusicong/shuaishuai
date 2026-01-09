# LangChain + LangGraph 学习项目

本项目用于学习 Python、LangChain 和 LangGraph。

## 目录结构规划

为了保持代码的整洁和可维护性，本项目采用以下目录结构：

```text
lang-all/
├── config/                 # 存放配置文件
│   └── settings.yaml       # (可选) 项目配置，如模型名称、API参数等
├── data/                   # 存放数据文件
│   ├── raw/                # 原始数据
│   └── processed/          # 处理后的数据
├── docs/                   # 项目文档
├── notebooks/              # Jupyter Notebooks，用于实验和演示
│   ├── 01_langchain_basics.ipynb
│   └── 02_langgraph_intro.ipynb
├── src/                    # 源代码目录
│   ├── __init__.py
│   ├── core/               # 核心逻辑
│   │   └── config.py       # 配置加载逻辑
│   ├── chains/             # LangChain 链的定义
│   │   └── __init__.py
│   ├── graphs/             # LangGraph 图的定义
│   │   └── __init__.py
│   ├── tools/              # 自定义工具 (Tools)
│   │   └── __init__.py
│   └── utils/              # 通用工具函数
│       └── __init__.py
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
