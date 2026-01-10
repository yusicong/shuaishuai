"""
向量数据库工具类，提供便捷的向量操作接口。
设计为工具类，方便直接调用。
"""
from typing import List, Optional
from langchain_core.documents import Document
from langchain_core.vectorstores import VectorStore
from src.core.vector_store import get_vector_store


class VectorDBUtil:
    """
    向量数据库工具类，封装了常用的操作方法。
    """
    
    def __init__(self, collection_name: str = "default_collection"):
        self.collection_name = collection_name
        self._vector_store: Optional[VectorStore] = None
    
    @property
    def vector_store(self) -> VectorStore:
        if self._vector_store is None:
            self._vector_store = get_vector_store(collection_name=self.collection_name)
        return self._vector_store

    def add_texts(self, texts: List[str], metadatas: Optional[List[dict]] = None) -> List[str]:
        """
        添加文本到向量数据库。
        
        Args:
            texts: 要添加的文本列表
            metadatas: 对应的元数据列表
            
        Returns:
            生成的文档ID列表
        """
        return self.vector_store.add_texts(texts=texts, metadatas=metadatas)

    def add_documents(self, documents: List[Document]) -> List[str]:
        """
        添加文档到向量数据库。
        
        Args:
            documents: 要添加的文档列表
            
        Returns:
            生成的文档ID列表
        """
        return self.vector_store.add_documents(documents)

    def similarity_search(self, query: str, k: int = 4, filter: Optional[dict] = None) -> List[Document]:
        """
        相似性搜索。
        
        Args:
            query: 查询文本
            k: 返回结果数量
            filter: 过滤条件
            
        Returns:
            相似文档列表
        """
        return self.vector_store.similarity_search(query, k=k, filter=filter)

    def similarity_search_with_score(self, query: str, k: int = 4, filter: Optional[dict] = None):
        """
        相似性搜索，返回相似度分数。
        
        Args:
            query: 查询文本
            k: 返回结果数量
            filter: 过滤条件
            
        Returns:
            包含文档和相似度分数的元组列表
        """
        return self.vector_store.similarity_search_with_score(query, k=k, filter=filter)

    def max_marginal_relevance_search(self, query: str, k: int = 4, fetch_k: int = 20, lambda_mult: float = 0.5, filter: Optional[dict] = None):
        """
        最大边际相关性搜索，用于返回多样化的结果。
        
        Args:
            query: 查询文本
            k: 返回结果数量
            fetch_k: 初始获取的候选数量
            lambda_mult: MMR 的平衡参数
            filter: 过滤条件
            
        Returns:
            相关文档列表
        """
        return self.vector_store.max_marginal_relevance_search(
            query, k=k, fetch_k=fetch_k, lambda_mult=lambda_mult, filter=filter
        )

    def delete_collection(self):
        """
        删除当前集合中的所有数据。
        注意：这将删除集合中的所有文档。
        """
        # ChromaDB 通常通过重新创建集合来"清空"，这里我们重新获取一个空的实例
        self._vector_store = None
        # 重新初始化向量存储以清空内容
        from src.core.vector_store import chroma_service
        chroma_service.get_vector_store(collection_name=self.collection_name)


# 便捷的全局实例
vector_db_util = VectorDBUtil()


def add_texts(texts: List[str], metadatas: Optional[List[dict]] = None, collection_name: str = "default_collection") -> List[str]:
    """
    便捷函数：添加文本到向量数据库。
    """
    util = VectorDBUtil(collection_name=collection_name)
    return util.add_texts(texts, metadatas)


def add_documents(documents: List[Document], collection_name: str = "default_collection") -> List[str]:
    """
    便捷函数：添加文档到向量数据库。
    """
    util = VectorDBUtil(collection_name=collection_name)
    return util.add_documents(documents)


def similarity_search(query: str, k: int = 4, filter: Optional[dict] = None, collection_name: str = "default_collection") -> List[Document]:
    """
    便捷函数：执行相似性搜索。
    """
    util = VectorDBUtil(collection_name=collection_name)
    return util.similarity_search(query, k, filter)


def similarity_search_with_score(query: str, k: int = 4, filter: Optional[dict] = None, collection_name: str = "default_collection"):
    """
    便捷函数：执行相似性搜索并返回分数。
    """
    util = VectorDBUtil(collection_name=collection_name)
    return util.similarity_search_with_score(query, k, filter)