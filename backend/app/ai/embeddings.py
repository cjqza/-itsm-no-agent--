"""AI / RAG Embedding 抽象层

惰性导入重型依赖（sentence_transformers、httpx），不安装时不影响其他功能。
"""
import asyncio
import logging
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


class BaseEmbedding(ABC):
    """Embedding 抽象基类"""

    @abstractmethod
    async def embed_documents(self, texts: list[str]) -> list[list[float]]:
        """批量嵌入文档"""
        ...

    @abstractmethod
    async def embed_query(self, text: str) -> list[float]:
        """嵌入单条查询"""
        ...

    @property
    @abstractmethod
    def dimension(self) -> int:
        """Embedding 向量维度"""
        ...


class BGEEmbedding(BaseEmbedding):
    """本地 bge-small-zh-v1.5 Embedding

    使用 sentence_transformers.SentenceTransformer，通过 asyncio.to_thread()
    将同步推理包装为异步调用。
    """

    def __init__(self, model_name: str = "BAAI/bge-small-zh-v1.5"):
        self._model_name = model_name
        self._model = None
        self._dimension: int = 512

    def _load_model(self):
        """惰性加载模型"""
        if self._model is not None:
            return
        try:
            from sentence_transformers import SentenceTransformer
        except ImportError:
            raise ImportError(
                "sentence_transformers 未安装。请执行: pip install sentence-transformers"
            )
        logger.info(f"正在加载 BGE 模型: {self._model_name}")
        self._model = SentenceTransformer(self._model_name)
        # 获取实际维度
        test_vec = self._model.encode(["test"])
        self._dimension = len(test_vec[0])
        logger.info(f"BGE 模型加载完成，维度: {self._dimension}")

    def _encode_sync(self, texts: list[str]) -> list[list[float]]:
        """同步编码（在线程中运行）"""
        self._load_model()
        embeddings = self._model.encode(texts, normalize_embeddings=True)
        return [vec.tolist() for vec in embeddings]

    async def embed_documents(self, texts: list[str]) -> list[list[float]]:
        """批量嵌入文档"""
        if not texts:
            return []
        return await asyncio.to_thread(self._encode_sync, texts)

    async def embed_query(self, text: str) -> list[float]:
        """嵌入单条查询"""
        results = await asyncio.to_thread(self._encode_sync, [text])
        return results[0]

    @property
    def dimension(self) -> int:
        return self._dimension


class OpenAIEmbedding(BaseEmbedding):
    """OpenAI API Compatible Embedding（含 DeepSeek）

    使用 httpx.AsyncClient 调用远程 API，支持自定义 base_url。
    """

    def __init__(
        self,
        model: str = "bge-small-zh-v1.5",
        api_key: str = "",
        base_url: str = "https://api.openai.com/v1",
        dimension: int = 512,
    ):
        self._model = model
        self._api_key = api_key
        self._base_url = base_url.rstrip("/")
        self._dimension = dimension

    async def _call_api(self, texts: list[str]) -> list[list[float]]:
        """调用 Embedding API"""
        try:
            import httpx
        except ImportError:
            raise ImportError("httpx 未安装。请执行: pip install httpx")

        url = f"{self._base_url}/embeddings"
        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self._model,
            "input": texts,
        }

        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(url, json=payload, headers=headers)
            resp.raise_for_status()
            data = resp.json()

        # 按 index 排序
        sorted_data = sorted(data["data"], key=lambda x: x["index"])
        return [item["embedding"] for item in sorted_data]

    async def embed_documents(self, texts: list[str]) -> list[list[float]]:
        """批量嵌入文档（分批，每批最多 16 条）"""
        if not texts:
            return []
        batch_size = 16
        all_embeddings = []
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            result = await self._call_api(batch)
            all_embeddings.extend(result)
        return all_embeddings

    async def embed_query(self, text: str) -> list[float]:
        """嵌入单条查询"""
        results = await self._call_api([text])
        return results[0]

    @property
    def dimension(self) -> int:
        return self._dimension


def create_embedding(config) -> BaseEmbedding:
    """Embedding 工厂函数，根据配置选择实现。

    Args:
        config: Settings 实例，需包含 AI_EMBEDDING_PROVIDER 等字段

    Returns:
        BaseEmbedding 实例
    """
    provider = config.AI_EMBEDDING_PROVIDER.lower()

    if provider == "bge":
        return BGEEmbedding(model_name=config.AI_EMBEDDING_MODEL)
    elif provider == "openai":
        return OpenAIEmbedding(
            model=config.AI_EMBEDDING_MODEL,
            api_key=config.AI_EMBEDDING_API_KEY,
            base_url=config.AI_EMBEDDING_BASE_URL,
            dimension=config.AI_EMBEDDING_DIMENSION,
        )
    else:
        raise ValueError(f"不支持的 Embedding 提供商: {provider}，可选: bge, openai")
