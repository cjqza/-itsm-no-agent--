"""AI / RAG 模块

提供智能客服 RAG（检索增强生成）能力。
所有重型依赖（sentence_transformers、chromadb、ctransformers）均为惰性导入，
不安装时不影响其他功能。
"""
from app.ai.rag import get_rag_pipeline

__all__ = ["get_rag_pipeline"]
