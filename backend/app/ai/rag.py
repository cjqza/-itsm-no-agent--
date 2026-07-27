"""AI / RAG 管道

协调 Embedding、VectorStore、LLM 完成检索增强生成。
全局单例通过 get_rag_pipeline() 获取，惰性初始化，线程安全。
"""
import asyncio
import json
import logging
import threading
from typing import AsyncGenerator, Optional

from app.config import get_settings

logger = logging.getLogger(__name__)

# 全局单例
_rag_pipeline = None
_rag_lock = threading.Lock()


class RAGPipeline:
    """RAG 管道：retrieve -> build_messages -> llm.generate/stream"""

    def __init__(self, embedding, vectorstore, llm, config=None):
        """
        Args:
            embedding: BaseEmbedding 实例
            vectorstore: VectorStoreManager 实例
            llm: BaseLLM 实例
            config: Settings 实例
        """
        self._embedding = embedding
        self._vectorstore = vectorstore
        self._llm = llm
        self._config = config or get_settings()

    async def _retrieve(self, query: str) -> list[dict]:
        """向量检索 + 过滤低分结果

        Args:
            query: 用户查询

        Returns:
            过滤后的检索结果列表
        """
        top_k = self._config.AI_RAG_TOP_K
        threshold = self._config.AI_RAG_SCORE_THRESHOLD

        try:
            results = await self._vectorstore.search(query, top_k=top_k)
            # 过滤低于阈值的结果
            filtered = [r for r in results if r.get("score", 0) >= threshold]
            logger.info(
                f"RAG 检索: 返回 {len(results)} 条，过滤后 {len(filtered)} 条 "
                f"(阈值={threshold})"
            )
            return filtered
        except Exception as e:
            logger.error(f"RAG 检索异常: {e}")
            return []

    def _build_messages(
        self, question: str, docs: list[dict], history: list[dict]
    ) -> list[dict]:
        """构建 LLM messages

        Args:
            question: 用户问题
            docs: 检索到的文档
            history: 格式化后的历史消息

        Returns:
            LLM messages 列表
        """
        from app.ai.prompts import (
            SYSTEM_PROMPT, RAG_PROMPT_TEMPLATE, FALLBACK_PROMPT, build_context,
        )

        messages = [{"role": "system", "content": SYSTEM_PROMPT}]

        # 添加历史消息
        if history:
            messages.extend(history)

        # 构建用户问题（含 RAG 上下文或兜底提示）
        if docs:
            context = build_context(docs)
            user_content = RAG_PROMPT_TEMPLATE.format(
                context=context, question=question
            )
        else:
            user_content = FALLBACK_PROMPT.format(question=question)

        messages.append({"role": "user", "content": user_content})
        return messages

    async def query(self, question: str, history: list[dict] = None) -> dict:
        """同步查询：retrieve -> build_messages -> llm.generate

        Args:
            question: 用户问题
            history: 历史消息列表（已格式化为 LLM messages 格式）

        Returns:
            {answer, sources, has_relevant_docs, llm_provider}
        """
        from app.ai.prompts import format_history

        history = history or []
        formatted_history = format_history(
            history, max_turns=self._config.AI_RAG_MAX_HISTORY_TURNS
        )

        # 检索
        docs = await self._retrieve(question)

        # 构建消息
        messages = self._build_messages(question, docs, formatted_history)

        # 生成（返回 {"answer": str, "thinking": Optional[str]}）
        result = await self._llm.generate(messages)
        answer = result["answer"]
        thinking = result.get("thinking")

        # 构建来源信息
        sources = []
        for doc in docs:
            sources.append({
                "content": doc["content"][:200],  # 截断
                "metadata": doc.get("metadata", {}),
                "score": round(doc.get("score", 0), 3),
            })

        return {
            "answer": answer,
            "thinking": thinking,
            "sources": sources,
            "has_relevant_docs": len(docs) > 0,
            "llm_provider": self._llm.provider_name,
        }

    async def stream_query(
        self, question: str, history: list[dict] = None
    ) -> AsyncGenerator[str, None]:
        """流式查询：返回 SSE 格式的 async generator

        Args:
            question: 用户问题
            history: 历史消息列表

        Yields:
            SSE 格式字符串: "data: {...}\n\n"
        """
        from app.ai.prompts import format_history

        history = history or []
        formatted_history = format_history(
            history, max_turns=self._config.AI_RAG_MAX_HISTORY_TURNS
        )

        # 检索
        docs = await self._retrieve(question)

        # 构建消息
        messages = self._build_messages(question, docs, formatted_history)

        # 构建来源信息（先发送）
        sources = []
        for doc in docs:
            sources.append({
                "content": doc["content"][:200],
                "metadata": doc.get("metadata", {}),
                "score": round(doc.get("score", 0), 3),
            })

        # 先发送来源事件
        meta_event = {
            "type": "sources",
            "sources": sources,
            "has_relevant_docs": len(docs) > 0,
            "llm_provider": self._llm.provider_name,
        }
        yield f"data: {json.dumps(meta_event, ensure_ascii=False)}\n\n"

        # 流式生成（llm.stream 现在 yield dict 事件）
        try:
            async for event in self._llm.stream(messages):
                yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"
        except Exception as e:
            logger.error(f"RAG 流式生成异常: {e}")
            error_event = {
                "type": "error",
                "content": "AI 生成出现错误，请稍后重试",
            }
            yield f"data: {json.dumps(error_event, ensure_ascii=False)}\n\n"

        # 结束事件
        done_event = {
            "type": "done",
            "has_relevant_docs": len(docs) > 0,
        }
        yield f"data: {json.dumps(done_event, ensure_ascii=False)}\n\n"


def get_rag_pipeline() -> Optional[RAGPipeline]:
    """获取 RAG 管道全局单例（惰性初始化，线程安全）

    Returns:
        RAGPipeline 实例，初始化失败时返回 None
    """
    global _rag_pipeline

    if _rag_pipeline is not None:
        return _rag_pipeline

    with _rag_lock:
        # 双重检查
        if _rag_pipeline is not None:
            return _rag_pipeline

        try:
            from app.ai.embeddings import create_embedding
            from app.ai.vectorstore import VectorStoreManager
            from app.ai.llm import create_llm

            config = get_settings()
            logger.info("正在初始化 RAG 管道...")

            embedding = create_embedding(config)
            vectorstore = VectorStoreManager(embedding, config)
            llm = create_llm(config)

            _rag_pipeline = RAGPipeline(embedding, vectorstore, llm, config)
            logger.info("RAG 管道初始化完成")
            return _rag_pipeline

        except ImportError as e:
            logger.warning(f"RAG 管道初始化失败（缺少依赖）: {e}")
            return None
        except Exception as e:
            logger.error(f"RAG 管道初始化异常: {e}", exc_info=True)
            return None
