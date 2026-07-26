"""AI / RAG 提示词模板"""
from typing import Optional


SYSTEM_PROMPT = """你是一个专业的公司IT服务台智能客服助手。你的职责是帮助用户解决日常IT问题，包括但不限于：
- 电脑、打印机、网络等硬件故障
- 操作系统、办公软件、邮件等软件问题
- 账号密码、权限申请等账户相关问题
- 其他IT相关的咨询

回答要求：
1. 使用简洁、专业的中文回答
2. 如果知识库中有相关信息，优先基于知识库内容回答
3. 如果知识库中没有相关信息，基于通用IT知识回答，但要明确告知用户这是通用建议
4. 对于复杂问题或无法确定的问题，建议用户提交工单由IT工程师处理
5. 回答要友好、耐心，避免过于技术化的术语"""


RAG_PROMPT_TEMPLATE = """基于以下参考资料回答用户的问题。如果参考资料中包含相关信息，请优先引用。如果参考资料不包含相关信息，请基于你的通用知识回答，并说明这是通用建议。

参考资料：
{context}

用户问题：{question}"""


FALLBACK_PROMPT = """用户的问题没有找到直接匹配的知识库文档。请基于你的通用IT知识回答以下问题，并建议用户如需进一步帮助可提交工单：

用户问题：{question}"""


def format_history(messages: list[dict], max_turns: int = 5) -> list[dict]:
    """将前端传来的历史消息格式化为 LLM messages 格式。

    Args:
        messages: 前端传来的历史消息列表，每条包含 role 和 content
        max_turns: 最大保留轮数（一问一答算一轮）

    Returns:
        格式化后的 LLM messages 列表
    """
    if not messages:
        return []

    formatted = []
    for msg in messages:
        role = msg.get("role", "")
        content = msg.get("content", "")
        if not content:
            continue
        # 只保留 user 和 assistant 角色
        if role in ("user", "assistant"):
            formatted.append({"role": role, "content": content})

    # 只保留最近 max_turns 轮（每轮 2 条消息）
    max_messages = max_turns * 2
    if len(formatted) > max_messages:
        formatted = formatted[-max_messages:]

    return formatted


def build_context(docs: list[dict]) -> str:
    """将检索到的文档列表构建为上下文字符串。

    Args:
        docs: 检索结果列表，每项包含 content 和 metadata

    Returns:
        格式化的上下文字符串
    """
    if not docs:
        return "（无相关参考资料）"

    parts = []
    for i, doc in enumerate(docs, 1):
        source = doc.get("metadata", {}).get("source_type", "未知来源")
        source_id = doc.get("metadata", {}).get("source_id", "")
        prefix = f"[来源{i}: {source}"
        if source_id:
            prefix += f" #{source_id}"
        prefix += "]"
        parts.append(f"{prefix}\n{doc['content']}")

    return "\n\n".join(parts)
