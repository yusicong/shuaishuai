"""
Serper 网络搜索工具（中文注释）

功能：
- 使用 serper.dev 的 Google 搜索 API 进行网络查询
- 返回结构化搜索结果（摘要、链接等）
- 集成到 LangChain 工具系统中，供 LLM 调用

API 密钥配置：
- 优先使用环境变量 SERPER_API_KEY
- 若无环境变量，则使用项目默认密钥（仅限学习用途）
- 生产环境务必使用自己的密钥

参考：https://serper.dev/
"""

import json
import os
from typing import Any, Dict, Optional, Type

import requests
from langchain.tools import BaseTool
from pydantic import BaseModel, Field
from src.utils.logger import logger


class SerperSearchInput(BaseModel):
    """
    搜索工具的输入参数模型。

    Attributes:
        query (str): 搜索查询关键词或问题
        num_results (int): 返回结果数量，默认 10
    """

    query: str = Field(description="搜索查询关键词或问题")
    num_results: Optional[int] = Field(
        default=10, description="返回结果数量，默认 10", ge=1, le=20
    )


class SerperSearchTool(BaseTool):
    """
    Serper 网络搜索工具。

    使用示例：
    ```python
    tool = SerperSearchTool()
    result = tool.run("苹果公司最新财报")
    ```

    返回格式：
    {
        "searchParameters": {...},
        "knowledgeGraph": {...},
        "organic": [...],
        "answerBox": {...}
    }
    """

    name: str = "serper_search"
    description: str = (
        "使用 Google 搜索 API 获取最新的网络信息。"
        "适用于查询实时新闻、公司信息、技术文档等。"
        "输入应为具体的搜索查询关键词。"
    )
    args_schema: Type[BaseModel] = SerperSearchInput
    return_direct: bool = False

    # API 配置
    _api_url: str = "https://google.serper.dev/search"
    _api_key: Optional[str] = None
    _gl: str = "us"
    _hl: str = "en"
    _location: str = "United States"

    def __init__(self, gl: str = "us", hl: str = "en", location: str = "United States", **kwargs: Any):
        super().__init__(**kwargs)
        # 优先从环境变量读取 API 密钥
        self._api_key = os.getenv("SERPER_API_KEY")
        if not self._api_key:
            # 学习项目默认密钥（生产环境务必使用自己的密钥）
            self._api_key = "819e2982d8a6367ab58594c0d4c54ec88a147e18"
            print("⚠️  使用默认 Serper API 密钥，建议设置 SERPER_API_KEY 环境变量")
        
        # 存储配置参数
        self._gl = gl
        self._hl = hl
        self._location = location

    def _run(self, query: str, num_results: int = 10) -> Dict[str, Any]:
        """
        执行搜索并返回结构化结果。

        Args:
            query: 搜索查询字符串
            num_results: 返回结果数量

        Returns:
            包含搜索结果的结构化字典
        """
        logger.debug(f"Executing Serper search. Query: {query}, GL: {self._gl}, HL: {self._hl}")
        if logger.level("DEBUG"):
             logger.debug(f"Serper API payload: {json.dumps({'q': query, 'num': num_results, 'gl': self._gl, 'hl': self._hl, 'location': self._location}, ensure_ascii=False)}")
        try:
            payload = json.dumps({
                "q": query,
                "num": num_results,
                "gl": self._gl,
                "hl": self._hl,
                "location": self._location
            })
            headers = {
                "X-API-KEY": self._api_key,
                "Content-Type": "application/json",
            }

            response = requests.request(
                "POST", self._api_url, headers=headers, data=payload, timeout=30
            )
            response.raise_for_status()

            result = response.json()
            logger.debug(f"Serper API response status: {response.status_code}")
            
            # 详细记录 API 响应内容
            if logger.level("DEBUG"):
                logger.debug(f"Serper API raw response: {json.dumps(result, ensure_ascii=False)[:500]}..." if len(json.dumps(result)) > 500 else f"Serper API raw response: {json.dumps(result, ensure_ascii=False)}")

            # 简化结果，便于 LLM 理解
            simplified = self._simplify_result(result)
            logger.debug(f"Simplified results count: {len(simplified.get('organic_results', []))}")
            return simplified

        except requests.exceptions.Timeout:
            logger.error("Serper API timeout")
            return {"error": "搜索请求超时，请稍后重试"}
        except requests.exceptions.RequestException as e:
            logger.error(f"Serper API error: {e}")
            if hasattr(e, 'response') and e.response is not None:
                 logger.error(f"API Response: {e.response.text}")
            return {"error": f"网络请求失败: {str(e)}"}
        except json.JSONDecodeError:
            logger.error("Serper API returned invalid JSON")
            return {"error": "搜索结果解析失败"}

    def _simplify_result(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """
        简化搜索结果，提取关键信息供 LLM 使用。

        Args:
            result: 原始 API 响应

        Returns:
            简化的搜索结果
        """
        simplified = {
            "query": result.get("searchParameters", {}).get("q", ""),
            "total_results": result.get("searchInformation", {}).get("totalResults", 0),
        }

        # 提取知识图谱信息
        if "knowledgeGraph" in result:
            kg = result["knowledgeGraph"]
            simplified["knowledge_graph"] = {
                "title": kg.get("title"),
                "description": kg.get("description"),
                "attributes": kg.get("attributes", []),
            }

        # 提取有机搜索结果
        organic_results = []
        for item in result.get("organic", [])[:5]:  # 取前5条
            organic_results.append({
                "title": item.get("title", ""),
                "link": item.get("link"),
                "snippet": item.get("snippet"),
            })
        if organic_results:
            simplified["organic_results"] = organic_results

        # 提取答案框（如果有）
        if "answerBox" in result:
            answer_box = result["answerBox"]
            simplified["answer_box"] = {
                "answer": answer_box.get("answer"),
                "snippet": answer_box.get("snippet"),
                "title": answer_box.get("title"),
            }

        # 提取相关搜索建议
        if "relatedSearches" in result:
            simplified["related_searches"] = [
                q.get("query") for q in result["relatedSearches"][:3]
            ]

        return simplified

    async def _arun(self, query: str, num_results: int = 10) -> Dict[str, Any]:
        """
        异步执行搜索（暂不支持，仅提供同步版本）。
        """
        raise NotImplementedError("异步搜索暂不支持")


def create_serper_search_tool(**kwargs) -> SerperSearchTool:
    """
    便捷函数：创建 Serper 搜索工具实例。

    Returns:
        SerperSearchTool 实例
    """
    return SerperSearchTool(**kwargs)