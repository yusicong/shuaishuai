import os
from typing import Optional
from chromadb import Client as ChromaClient
from chromadb.config import Settings
from chromadb.api.types import Documents, EmbeddingFunction, Embeddings
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma as LangChainChroma
from langchain_core.vectorstores import VectorStore


class ChromaService:
    """
    ChromaDB 服务类，负责初始化和提供向量数据库实例。
    支持持久化存储和内存模式。
    """
    
    def __init__(self, persist_directory: str = "./data/vector_db", embedding_model_name: str = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"):
        self.persist_directory = persist_directory
        self.embedding_model_name = embedding_model_name
        self._client: Optional[ChromaClient] = None
        self._embedding_function: Optional[EmbeddingFunction] = None
        self._vector_store: Optional[VectorStore] = None
        
    def initialize(self) -> ChromaClient:
        """
        初始化 ChromaDB 客户端。
        如果 persist_directory 存在，则使用持久化模式；否则使用内存模式。
        """
        if not os.path.exists(self.persist_directory):
            os.makedirs(self.persist_directory, exist_ok=True)
        
        # 初始化嵌入模型
        self._embedding_function = HuggingFaceEmbeddings(model_name=self.embedding_model_name)
        
        # 配置 Chroma 设置
        settings = Settings(
            persist_directory=self.persist_directory,
            is_persistent=True,
        )
        
        # 创建客户端
        self._client = ChromaClient(settings=settings)
        print(f"ChromaDB initialized with persistence at: {self.persist_directory}")
        
        return self._client
    
    def get_vector_store(self, collection_name: str = "default_collection") -> VectorStore:
        """
        获取 LangChain 兼容的向量存储实例。
        """
        if self._vector_store is None:
            if self._embedding_function is None:
                raise RuntimeError("ChromaService not initialized. Call initialize() first.")
            
            # 创建 LangChain Chroma 实例
            self._vector_store = LangChainChroma(
                client=self._client,
                collection_name=collection_name,
                embedding_function=self._embedding_function
            )
        
        return self._vector_store
    
    @property
    def client(self) -> ChromaClient:
        if self._client is None:
            raise RuntimeError("ChromaService not initialized. Call initialize() first.")
        return self._client
    
    @property
    def embedding_function(self) -> EmbeddingFunction:
        if self._embedding_function is None:
            raise RuntimeError("ChromaService not initialized. Call initialize() first.")
        return self._embedding_function


# 全局实例，便于在整个应用中共享
chroma_service = ChromaService()


def get_chroma_client() -> ChromaClient:
    """
    获取全局的 ChromaDB 客户端实例。
    """
    return chroma_service.client


def get_vector_store(collection_name: str = "default_collection") -> VectorStore:
    """
    获取 LangChain 兼容的向量存储实例。
    """
    return chroma_service.get_vector_store(collection_name=collection_name)


def init_chroma_service(persist_directory: str = "./data/vector_db", embedding_model_name: str = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"):
    """
    初始化 Chroma 服务。
    这个函数应该在应用启动时调用一次。
    """
    chroma_service.initialize()