"""
LangChain 使用示例（中文注释）：

功能说明：
- 读取配置（OPENAI_API_KEY、模型名等）
- 构建一个最简单的对话链：Prompt -> LLM -> 输出解析
- 运行后在终端打印回复结果
"""

from typing import Dict
from src.config import load_config, validate_config
from src.core.vector_store import init_chroma_service
from src.utils.vector_utils import VectorDBUtil, add_texts, similarity_search

from src.chains.basic_chat import build_callbacks, build_chat_chain, to_langchain_messages


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
  
    chain = build_chat_chain(cfg)
    callbacks = build_callbacks(cfg)

    question = inputs.get("question") or ""
    lc_messages = to_langchain_messages([{"role": "user", "content": question}])
    return chain.invoke({"messages": lc_messages}, config={"callbacks": callbacks} if callbacks else {})


def test_vector_database():
    """
    测试向量数据库的启动、存储和读取功能。
    """
    print("\n" + "="*50)
    print("开始测试向量数据库...")
    print("="*50)
    
    try:
        # 1. 启动/初始化向量数据库
        print("\n1. 初始化向量数据库服务...")
        init_chroma_service()
        print("   ✅ 向量数据库初始化成功")
        
        # 2. 存储测试数据
        print("\n2. 存储测试数据...")
        test_texts = [
            "LangChain 是一个用于开发语言模型应用的框架",
            "向量数据库用于存储和检索文本的向量表示",
            "ChromaDB 是一个开源的向量数据库",
            "检索增强生成 (RAG) 结合了检索和生成模型"
        ]
        test_metadatas = [
            {"source": "doc1", "type": "framework"},
            {"source": "doc2", "type": "database"},
            {"source": "doc3", "type": "database"},
            {"source": "doc4", "type": "technique"}
        ]
        
        # 使用工具类添加文本
        doc_ids = add_texts(test_texts, test_metadatas, collection_name="test_collection")
        print(f"   ✅ 成功存储 {len(doc_ids)} 个文档")
        print(f"   文档ID: {doc_ids}")
        
        # 3. 读取数据（相似性搜索）
        print("\n3. 执行相似性搜索...")
        query = "什么是向量数据库？"
        results = similarity_search(query, k=2, collection_name="test_collection")
        
        print(f"   查询: '{query}'")
        print(f"   返回 {len(results)} 个最相关文档:")
        for i, doc in enumerate(results, 1):
            print(f"   {i}. {doc.page_content[:80]}...")
            print(f"      元数据: {doc.metadata}")
        
        print("\n✅ 向量数据库测试通过！")
        
    except Exception as e:
        print(f"❌ 向量数据库测试失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    # 简单示例：询问一个问题
    question = "用一句话介绍 LangChain 的用途"
    print("正在调用模型，请稍候...\n")
    answer = run_once({"question": question})
    print("模型回复：")
    print(answer)
    
    # 运行向量数据库测试
    test_vector_database()
