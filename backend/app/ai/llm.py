"""AI / RAG LLM 抽象层

惰性导入重型依赖（llama_cpp、httpx），不安装时不影响其他功能。
llama-cpp-python 需要用户手动安装（编译复杂），代码中用 try/except 给出友好提示。
"""
import asyncio
import json
import logging
from abc import ABC, abstractmethod
from typing import AsyncGenerator

logger = logging.getLogger(__name__)


class BaseLLM(ABC):
    """LLM 抽象基类"""

    @abstractmethod
    async def generate(self, messages: list[dict]) -> str:
        """同步生成回答"""
        ...

    @abstractmethod
    async def stream(self, messages: list[dict]) -> AsyncGenerator[str, None]:
        """流式生成回答，逐 token yield"""
        ...

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """提供商名称"""
        ...


class GGUFLLM(BaseLLM):
    """本地 llama-cpp-python GGUF 模型

    通过 asyncio.to_thread() 将同步推理包装为异步调用。
    注意：llama-cpp-python 需要用户手动安装（编译复杂）。
    """

    def __init__(self, model_path: str, max_tokens: int = 1024, temperature: float = 0.7):
        self._model_path = model_path
        self._max_tokens = max_tokens
        self._temperature = temperature
        self._llm = None

    def _load_model(self):
        """惰性加载模型"""
        if self._llm is not None:
            return
        try:
            from llama_cpp import Llama
        except ImportError:
            raise ImportError(
                "llama-cpp-python 未安装。请参考 https://github.com/abetlen/llama-cpp-python "
                "手动安装（需要 C++ 编译环境）。"
            )
        if not self._model_path:
            raise ValueError("AI_LLM_MODEL_PATH 未配置，请在 .env 中设置 GGUF 模型路径")
        logger.info(f"正在加载 GGUF 模型: {self._model_path}")
        self._llm = Llama(model_path=self._model_path, n_ctx=4096, verbose=False)
        logger.info("GGUF 模型加载完成")

    def _generate_sync(self, messages: list[dict]) -> str:
        """同步生成"""
        self._load_model()
        response = self._llm.create_chat_completion(
            messages=messages,
            max_tokens=self._max_tokens,
            temperature=self._temperature,
        )
        return response["choices"][0]["message"]["content"]

    async def generate(self, messages: list[dict]) -> str:
        """异步生成回答"""
        return await asyncio.to_thread(self._generate_sync, messages)

    async def stream(self, messages: list[dict]) -> AsyncGenerator[str, None]:
        """流式生成回答

        注意：llama-cpp-python 的流式是同步迭代器，需要在线程中运行。
        这里使用一个队列桥接同步流和异步生成器。
        """
        self._load_model()
        queue: asyncio.Queue = asyncio.Queue()
        sentinel = object()
        loop = asyncio.get_running_loop()

        def _stream_sync():
            try:
                stream = self._llm.create_chat_completion(
                    messages=messages,
                    max_tokens=self._max_tokens,
                    temperature=self._temperature,
                    stream=True,
                )
                for chunk in stream:
                    delta = chunk["choices"][0].get("delta", {})
                    content = delta.get("content", "")
                    if content:
                        # 使用 run_coroutine_threadsafe 将数据放入队列
                        asyncio.run_coroutine_threadsafe(
                            queue.put(content), loop
                        )
            except Exception as e:
                logger.error(f"GGUF 流式生成异常: {e}")
            finally:
                asyncio.run_coroutine_threadsafe(
                    queue.put(sentinel), loop
                )

        # 在线程中启动同步流
        loop.run_in_executor(None, _stream_sync)

        # 从队列中读取数据
        while True:
            item = await queue.get()
            if item is sentinel:
                break
            yield item

    @property
    def provider_name(self) -> str:
        return "gguf"


class DeepSeekLLM(BaseLLM):
    """DeepSeek API（OpenAI 兼容）

    使用 httpx.AsyncClient 调用远程 API，支持流式。
    """

    def __init__(
        self,
        api_key: str = "",
        base_url: str = "https://api.deepseek.com",
        model_name: str = "deepseek-chat",
        max_tokens: int = 1024,
        temperature: float = 0.7,
    ):
        self._api_key = api_key
        self._base_url = base_url.rstrip("/")
        self._model_name = model_name
        self._max_tokens = max_tokens
        self._temperature = temperature

    async def _call_api(self, messages: list[dict], stream: bool = False):
        """调用 DeepSeek API"""
        try:
            import httpx
        except ImportError:
            raise ImportError("httpx 未安装。请执行: pip install httpx")

        url = f"{self._base_url}/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self._model_name,
            "messages": messages,
            "max_tokens": self._max_tokens,
            "temperature": self._temperature,
            "stream": stream,
        }

        if stream:
            client = httpx.AsyncClient(timeout=120.0)
            req = client.build_request("POST", url, json=payload, headers=headers)
            resp = await client.send(req, stream=True)
            return resp, client
        else:
            async with httpx.AsyncClient(timeout=120.0) as client:
                resp = await client.post(url, json=payload, headers=headers)
                resp.raise_for_status()
                return resp.json()

    async def generate(self, messages: list[dict]) -> str:
        """同步生成回答"""
        data = await self._call_api(messages, stream=False)
        return data["choices"][0]["message"]["content"]

    async def stream(self, messages: list[dict]) -> AsyncGenerator[str, None]:
        """流式生成回答（SSE 格式解析）"""
        resp, client = await self._call_api(messages, stream=True)
        try:
            async for line in resp.aiter_lines():
                if not line:
                    continue
                if not line.startswith("data: "):
                    continue
                data_str = line[6:]
                if data_str.strip() == "[DONE]":
                    break
                try:
                    data = json.loads(data_str)
                    delta = data["choices"][0].get("delta", {})
                    content = delta.get("content", "")
                    if content:
                        yield content
                except (json.JSONDecodeError, KeyError, IndexError):
                    continue
        finally:
            await resp.aclose()
            await client.aclose()

    @property
    def provider_name(self) -> str:
        return "deepseek"


def create_llm(config) -> BaseLLM:
    """LLM 工厂函数，根据配置选择实现。

    Args:
        config: Settings 实例

    Returns:
        BaseLLM 实例
    """
    provider = config.AI_LLM_PROVIDER.lower()

    if provider == "gguf":
        return GGUFLLM(
            model_path=config.AI_LLM_MODEL_PATH,
            max_tokens=config.AI_LLM_MAX_TOKENS,
            temperature=config.AI_LLM_TEMPERATURE,
        )
    elif provider == "deepseek":
        return DeepSeekLLM(
            api_key=config.AI_LLM_API_KEY,
            base_url=config.AI_LLM_BASE_URL,
            model_name=config.AI_LLM_MODEL_NAME,
            max_tokens=config.AI_LLM_MAX_TOKENS,
            temperature=config.AI_LLM_TEMPERATURE,
        )
    else:
        raise ValueError(f"不支持的 LLM 提供商: {provider}，可选: deepseek, gguf")
