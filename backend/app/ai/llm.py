"""AI / RAG LLM 抽象层

惰性导入重型依赖（ctransformers、transformers、httpx），不安装时不影响其他功能。
ctransformers 用于加载本地 GGUF 模型，替代 llama-cpp-python（Windows 编译问题）。
transformers 用于加载完整 HuggingFace 模型（如 Qwen2.5-1.5B-Instruct）。
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
    """本地 ctransformers GGUF 模型

    通过 asyncio.to_thread() 将同步推理包装为异步调用。
    使用 ctransformers 替代 llama-cpp-python（Windows 上编译更简单）。
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
            from ctransformers import AutoModelForCausalLM
        except ImportError:
            raise ImportError(
                "ctransformers 未安装。请执行: pip install ctransformers"
            )
        if not self._model_path:
            raise ValueError("AI_LLM_MODEL_PATH 未配置，请在 .env 中设置 GGUF 模型路径")
        logger.info(f"正在加载 GGUF 模型: {self._model_path}")
        self._llm = AutoModelForCausalLM.from_pretrained(
            self._model_path,
            model_type="qwen2",
            max_new_tokens=self._max_tokens,
            temperature=self._temperature,
        )
        logger.info("GGUF 模型加载完成")

    def _messages_to_prompt(self, messages: list[dict]) -> str:
        """将 OpenAI 格式的 messages 转为 ctransformers 可用的 prompt 字符串"""
        parts = []
        for m in messages:
            if m["role"] == "system":
                parts.append(f"<|system|>\n{m['content']}")
            elif m["role"] == "user":
                parts.append(f"<|user|>\n{m['content']}")
            elif m["role"] == "assistant":
                parts.append(f"<|assistant|>\n{m['content']}")
        parts.append("<|assistant|>")
        return "\n".join(parts)

    def _generate_sync(self, messages: list[dict]) -> str:
        """同步生成"""
        self._load_model()
        prompt = self._messages_to_prompt(messages)
        return self._llm(prompt)

    async def generate(self, messages: list[dict]) -> str:
        """异步生成回答"""
        return await asyncio.to_thread(self._generate_sync, messages)

    async def stream(self, messages: list[dict]) -> AsyncGenerator[str, None]:
        """流式生成回答

        ctransformers 的 __call__ 支持 stream=True 返回同步迭代器，
        使用队列桥接同步流和异步生成器。
        """
        self._load_model()
        prompt = self._messages_to_prompt(messages)
        queue: asyncio.Queue = asyncio.Queue()
        sentinel = object()
        loop = asyncio.get_running_loop()

        def _stream_sync():
            try:
                for token in self._llm(prompt, stream=True):
                    if token:
                        asyncio.run_coroutine_threadsafe(
                            queue.put(token), loop
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


class TransformersLLM(BaseLLM):
    """transformers 库加载本地模型（CPU 推理）

    使用 transformers.AutoModelForCausalLM + AutoTokenizer。
    模型在首次调用时惰性加载。
    通过 asyncio.to_thread() 包装为异步。
    """

    def __init__(self, model_path: str, max_tokens: int = 512, temperature: float = 0.7):
        self._model_path = model_path
        self._max_tokens = max_tokens
        self._temperature = temperature
        self._model = None
        self._tokenizer = None

    def _load_model(self):
        """惰性加载模型"""
        if self._model is not None:
            return
        try:
            from transformers import AutoModelForCausalLM, AutoTokenizer
            import torch
        except ImportError:
            raise ImportError(
                "transformers 或 torch 未安装。请执行: pip install transformers torch"
            )
        if not self._model_path:
            raise ValueError("AI_LLM_MODEL_PATH 未配置，请在 .env 中设置模型路径")
        logger.info(f"正在加载 transformers 模型: {self._model_path}")
        self._tokenizer = AutoTokenizer.from_pretrained(
            self._model_path, trust_remote_code=True
        )
        self._model = AutoModelForCausalLM.from_pretrained(
            self._model_path,
            dtype=torch.float32,  # CPU 用 float32
            device_map="cpu",
            trust_remote_code=True,
        )
        logger.info("transformers 模型加载完成")

    def _messages_to_prompt(self, messages: list[dict]) -> str:
        """将 OpenAI 格式 messages 转为 prompt 字符串"""
        parts = []
        for m in messages:
            role = m.get("role", "user")
            content = m.get("content", "")
            if role == "system":
                parts.append(f"<|system|>\n{content}")
            elif role == "user":
                parts.append(f"<|user|>\n{content}")
            elif role == "assistant":
                parts.append(f"<|assistant|>\n{content}")
        parts.append("<|assistant|>")
        return "\n".join(parts)

    def _generate_sync(self, messages: list[dict]) -> str:
        """同步生成"""
        self._load_model()
        import torch
        prompt = self._messages_to_prompt(messages)
        inputs = self._tokenizer(prompt, return_tensors="pt").to(self._model.device)
        with torch.no_grad():
            outputs = self._model.generate(
                **inputs,
                max_new_tokens=self._max_tokens,
                temperature=self._temperature,
                do_sample=True,
                pad_token_id=self._tokenizer.eos_token_id,
            )
        # 只取新生成的 token
        new_tokens = outputs[0][inputs["input_ids"].shape[1]:]
        return self._tokenizer.decode(new_tokens, skip_special_tokens=True)

    async def generate(self, messages: list[dict]) -> str:
        """异步生成回答"""
        return await asyncio.to_thread(self._generate_sync, messages)

    async def stream(self, messages: list[dict]) -> AsyncGenerator[str, None]:
        """流式生成回答

        transformers 没有原生流式 generate，用同步方式返回完整结果。
        """
        result = await self.generate(messages)
        yield result

    @property
    def provider_name(self) -> str:
        return "transformers"


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
    elif provider == "transformers":
        return TransformersLLM(
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
        raise ValueError(f"不支持的 LLM 提供商: {provider}，可选: gguf, transformers, deepseek")
