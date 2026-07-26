"""AI / RAG ChromaDB 向量存储管理

惰性导入 chromadb，不安装时不影响其他功能。
"""
import asyncio
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class VectorStoreManager:
    """ChromaDB 向量存储管理器

    封装 ChromaDB PersistentClient，提供文档的增删查操作。
    所有 ChromaDB 同步操作通过 asyncio.to_thread() 异步化。
    """

    def __init__(self, embedding, config):
        """
        Args:
            embedding: BaseEmbedding 实例，用于生成向量
            config: Settings 实例
        """
        self._embedding = embedding
        self._config = config
        self._client = None
        self._collection = None
        self._persist_directory = config.AI_VECTORSTORE_PATH

    def _ensure_client(self):
        """惰性初始化 ChromaDB 客户端"""
        if self._client is not None:
            return
        try:
            import chromadb
        except ImportError:
            raise ImportError(
                "chromadb 未安装。请执行: pip install chromadb"
            )
        logger.info(f"正在初始化 ChromaDB，存储路径: {self._persist_directory}")
        self._client = chromadb.PersistentClient(path=self._persist_directory)

        # 使用自定义 embedding function，避免 ChromaDB 下载 onnx 模型
        from chromadb import EmbeddingFunction
        class NullEmbeddingFunction(EmbeddingFunction):
            def __call__(self, input):
                return [[0.0] * 512 for _ in input]  # BGE-small-zh 输出 512 维

        self._collection = self._client.get_or_create_collection(
            name="knowledge",
            metadata={"hnsw:space": "cosine"},
            embedding_function=NullEmbeddingFunction(),
        )
        logger.info(f"ChromaDB 初始化完成，当前文档数: {self._collection.count()}")

    def _add_documents_sync(
        self, docs: list[str], metadatas: list[dict], ids: list[str]
    ) -> None:
        """同步添加/更新文档（upsert 语义）"""
        self._ensure_client()
        self._collection.upsert(
            documents=docs,
            metadatas=metadatas,
            ids=ids,
        )
        logger.info(f"已 upsert {len(docs)} 条文档到 ChromaDB")

    async def add_documents(
        self, docs: list[str], metadatas: list[dict], ids: list[str]
    ) -> None:
        """异步添加/更新文档（upsert 语义）

        Args:
            docs: 文档文本列表
            metadatas: 元数据列表
            ids: 文档 ID 列表
        """
        if not docs:
            return
        await asyncio.to_thread(self._add_documents_sync, docs, metadatas, ids)

    def _search_sync(self, query: str, top_k: int) -> list[dict]:
        """同步向量检索"""
        self._ensure_client()
        if self._collection.count() == 0:
            return []

        # 查询时需要 embedding function，ChromaDB 内部会调用
        # 但我们用自己的 embedding，所以直接传 query_embeddings
        # 注意：这里不能调用 async embed_query，所以用同步方式
        # 实际上 ChromaDB 会使用其默认 embedding function
        # 我们在 search 方法中手动处理 embedding
        raise NotImplementedError("应使用异步 search 方法")

    async def search(self, query: str, top_k: int = 10) -> list[dict]:
        """异步向量检索

        Args:
            query: 查询文本
            top_k: 返回结果数量

        Returns:
            检索结果列表，每项包含 content、metadata、score
        """
        self._ensure_client()

        if self._collection.count() == 0:
            return []

        # 用 embedding 模型生成查询向量
        query_embedding = await self._embedding.embed_query(query)

        def _do_query():
            results = self._collection.query(
                query_embeddings=[query_embedding],
                n_results=min(top_k, self._collection.count()),
                include=["documents", "metadatas", "distances"],
            )
            items = []
            if results and results["documents"]:
                for i, doc in enumerate(results["documents"][0]):
                    items.append({
                        "content": doc,
                        "metadata": results["metadatas"][0][i] if results["metadatas"] else {},
                        "score": 1.0 - results["distances"][0][i] if results["distances"] else 0.0,
                    })
            return items

        return await asyncio.to_thread(_do_query)

    def _delete_by_source_sync(self, source_type: str, source_id: str) -> int:
        """按来源同步删除"""
        self._ensure_client()
        try:
            # ChromaDB where filter
            where = {
                "$and": [
                    {"source_type": source_type},
                    {"source_id": source_id},
                ]
            }
            # 先查出要删除的 ID
            results = self._collection.get(where=where, include=[])
            if results and results["ids"]:
                self._collection.delete(ids=results["ids"])
                return len(results["ids"])
            return 0
        except Exception as e:
            logger.warning(f"ChromaDB 按来源删除失败: {e}")
            return 0

    async def delete_by_source(self, source_type: str, source_id: str) -> int:
        """按来源删除文档

        Args:
            source_type: 来源类型（如 "ticket", "faq"）
            source_id: 来源 ID

        Returns:
            删除的文档数量
        """
        return await asyncio.to_thread(
            self._delete_by_source_sync, source_type, source_id
        )

    def _get_stats_sync(self) -> dict:
        """同步获取统计信息"""
        self._ensure_client()
        total = self._collection.count()
        collections = [c.name for c in self._client.list_collections()]
        return {
            "total_documents": total,
            "collections": collections,
            "persist_directory": self._persist_directory,
        }

    async def get_stats(self) -> dict:
        """获取向量存储统计信息"""
        return await asyncio.to_thread(self._get_stats_sync)

    def _clear_sync(self) -> None:
        """清空集合"""
        self._ensure_client()
        # 删除并重建集合
        try:
            self._client.delete_collection("knowledge")
        except Exception:
            pass
        from chromadb import EmbeddingFunction
        class NullEmbeddingFunction(EmbeddingFunction):
            def __call__(self, input):
                return [[0.0] * 512 for _ in input]

        self._collection = self._client.get_or_create_collection(
            name="knowledge",
            metadata={"hnsw:space": "cosine"},
            embedding_function=NullEmbeddingFunction(),
        )
        logger.info("ChromaDB knowledge 集合已清空")

    async def clear(self) -> None:
        """清空所有文档"""
        await asyncio.to_thread(self._clear_sync)
