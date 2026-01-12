"""
搜索结果评估器（中文注释）

功能：
- 评估搜索结果的质量，包括相关性、新鲜度、可信度等维度
- 为每个搜索结果生成综合评分，供 LLM 参考

设计思路：
1. 规则评估：基于关键词匹配、域名权威性、时效性等规则
2. 可扩展：后续可以接入机器学习模型进行更精确的评估
3. 透明化：每个维度的评分清晰可见，便于调试

对于 Java 开发者：这个类式的设计应该很熟悉，类似于 Java 中的 Service 层
"""

import re
from datetime import datetime
from typing import Dict, List, Optional, Any
from urllib.parse import urlparse

from src.utils.logger import logger


class SearchResultEvaluator:
    """
    搜索结果评估器。
    
    示例：
    ```python
    evaluator = SearchResultEvaluator()
    results = evaluator.evaluate("Python 教程", [...])
    ```
    """
    
    def __init__(self, weights: Optional[Dict[str, float]] = None):
        """
        初始化评估器。
        
        Args:
            weights: 各维度权重配置，默认值：
                relevance: 0.5 (相关性)
                freshness: 0.2 (新鲜度)
                credibility: 0.3 (可信度)
        """
        self.weights = weights or {
            "relevance": 0.5,
            "freshness": 0.2,
            "credibility": 0.3
        }
        
        # 可信域名列表（示例）
        self.credible_domains = {
            "github.com": 0.9,
            "stackoverflow.com": 0.8,
            "wikipedia.org": 0.9,
            "medium.com": 0.6,
            "towardsdatascience.com": 0.7,
            "arxiv.org": 0.9,
            "docs.python.org": 0.9,
            "realpython.com": 0.8,
        }
        
        # 时效性关键词
        self.recency_keywords = {
            "2025": 1.0, "2024": 0.8, "2023": 0.6, "2022": 0.4, "2021": 0.2,
            "今年": 1.0, "最近": 0.8, "最新": 0.9, "近期": 0.7,
            "today": 1.0, "yesterday": 0.9, "this week": 0.8, "this month": 0.7
        }
    
    def evaluate_relevance(self, query: str, title: str, snippet: str) -> float:
        """
        评估结果与查询的相关性。
        
        策略：
        1. 关键词在标题中出现（权重更高）
        2. 关键词在摘要中出现
        3. 完全匹配 vs 部分匹配
        """
        query_words = set(re.findall(r'\b\w+\b', query.lower()))
        title_lower = title.lower()
        snippet_lower = snippet.lower()
        
        score = 0.0
        
        # 标题匹配（权重更高）
        title_match_count = 0
        for word in query_words:
            if word in title_lower:
                title_match_count += 1
        
        # 摘要匹配
        snippet_match_count = 0
        for word in query_words:
            if word in snippet_lower:
                snippet_match_count += 1
        
        # 计算分数（标题权重 0.7，摘要权重 0.3）
        if query_words:
            title_score = title_match_count / len(query_words) * 0.7
            snippet_score = snippet_match_count / len(query_words) * 0.3
            score = title_score + snippet_score
        
        return min(score, 1.0)
    
    def evaluate_freshness(self, title: str, snippet: str) -> float:
        """
        评估结果的新鲜度（时效性）。
        
        策略：
        1. 检查年份关键词
        2. 检查时效性描述词
        """
        text = f"{title} {snippet}".lower()
        
        # 检查年份
        for year_keyword, year_score in self.recency_keywords.items():
            if year_keyword in text:
                return year_score
        
        # 没有明确时间信息，默认中等分数
        return 0.5
    
    def evaluate_credibility(self, link: str) -> float:
        """
        评估来源的可信度。
        
        策略：
        1. 检查域名是否在可信列表中
        2. 检查顶级域名（.edu, .gov, .org 通常更可信）
        3. 默认分数
        """
        try:
            parsed = urlparse(link)
            domain = parsed.netloc.lower()
            
            # 去除 www 前缀
            if domain.startswith("www."):
                domain = domain[4:]
            
            # 检查可信域名列表
            if domain in self.credible_domains:
                return self.credible_domains[domain]
            
            # 根据顶级域名判断
            tld = domain.split('.')[-1] if '.' in domain else ''
            if tld in ['edu', 'gov', 'org']:
                return 0.7
            elif tld in ['com', 'net']:
                return 0.5
            else:
                return 0.4
                
        except Exception:
            return 0.4  # 解析失败时默认分数
    
    def evaluate_single_result(self, query: str, result: Dict[str, Any]) -> Dict[str, Any]:
        """
        评估单个搜索结果。
        
        Returns:
            包含评估分数的结果字典
        """
        title = result.get("title", "")
        link = result.get("link", "")
        snippet = result.get("snippet", "")
        
        # 计算各维度分数
        relevance_score = self.evaluate_relevance(query, title, snippet)
        freshness_score = self.evaluate_freshness(title, snippet)
        credibility_score = self.evaluate_credibility(link)
        
        # 加权综合分数
        overall_score = (
            relevance_score * self.weights["relevance"] +
            freshness_score * self.weights["freshness"] +
            credibility_score * self.weights["credibility"]
        )
        
        # 构建评估结果
        evaluated_result = result.copy()
        evaluated_result.update({
            "relevance_score": round(relevance_score, 3),
            "freshness_score": round(freshness_score, 3),
            "credibility_score": round(credibility_score, 3),
            "overall_score": round(overall_score, 3),
            "evaluation_notes": self._generate_evaluation_notes(
                relevance_score, freshness_score, credibility_score
            )
        })
        
        return evaluated_result
    
    def _generate_evaluation_notes(self, relevance: float, freshness: float, credibility: float) -> str:
        """生成评估说明文本。"""
        notes = []
        
        if relevance >= 0.8:
            notes.append("相关性很高")
        elif relevance >= 0.5:
            notes.append("相关性中等")
        else:
            notes.append("相关性较低")
        
        if freshness >= 0.8:
            notes.append("内容较新")
        elif freshness >= 0.5:
            notes.append("内容时效性一般")
        else:
            notes.append("内容可能较旧")
        
        if credibility >= 0.8:
            notes.append("来源可信")
        elif credibility >= 0.5:
            notes.append("来源可信度一般")
        else:
            notes.append("来源可信度较低")
        
        return "；".join(notes)
    
    def evaluate(self, query: str, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        评估搜索结果列表。
        
        Args:
            query: 搜索查询
            results: 原始结果列表
            
        Returns:
            包含评估分数的结果列表（按综合分数降序排序）
        """
        evaluated_results = []
        
        for result in results:
            try:
                evaluated = self.evaluate_single_result(query, result)
                evaluated_results.append(evaluated)
            except Exception as e:
                logger.error(f"评估单个结果失败: {e}")
                # 保留原始结果，但不添加评估分数
                result_without_eval = result.copy()
                result_without_eval.update({
                    "relevance_score": 0.0,
                    "freshness_score": 0.0,
                    "credibility_score": 0.0,
                    "overall_score": 0.0,
                    "evaluation_notes": "评估失败"
                })
                evaluated_results.append(result_without_eval)
        
        # 按综合分数降序排序
        evaluated_results.sort(key=lambda x: x["overall_score"], reverse=True)
        
        logger.debug(f"评估完成: 查询='{query}', 结果数={len(evaluated_results)}, "
                   f"最高分={evaluated_results[0]['overall_score'] if evaluated_results else 0:.2f}")
        
        return evaluated_results


# 便捷函数（保持与现有工具链兼容）
def evaluate_search_results(query: str, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    便捷函数：评估搜索结果。
    
    这是为了在 serper_search.py 中直接调用。
    """
    evaluator = SearchResultEvaluator()
    return evaluator.evaluate(query, results)


# 导出
__all__ = ["SearchResultEvaluator", "evaluate_search_results"]
