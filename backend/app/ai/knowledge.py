"""AI / RAG 知识库构建

从已解决工单和 FAQ 文档中提取知识，构建向量索引。
数据库查询用同步 SQLAlchemy（在线程中执行），向量存储操作用异步接口。
"""
import asyncio
import hashlib
import logging
import os
import re
from datetime import datetime, timezone
from typing import Optional

from app.config import get_settings

logger = logging.getLogger(__name__)


def _make_doc_id(source_type: str, source_id: str) -> str:
    """生成确定性文档 ID"""
    raw = f"{source_type}:{source_id}"
    return hashlib.md5(raw.encode()).hexdigest()


class KnowledgeBuilder:
    """知识库构建器

    从已解决工单和 FAQ Markdown 文档中提取知识，写入 ChromaDB。
    数据库查询在线程中用同步 SQLAlchemy 执行，向量存储用异步接口。
    """

    def __init__(self, vectorstore, config=None):
        """
        Args:
            vectorstore: VectorStoreManager 实例
            config: Settings 实例，为空时自动获取
        """
        self._vectorstore = vectorstore
        self._config = config or get_settings()
        self._last_sync: Optional[datetime] = None

    def _get_sync_session(self):
        """创建同步 SQLAlchemy session"""
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker

        db_url = self._config.SYNC_DATABASE_URL
        engine = create_engine(db_url, echo=False)
        Session = sessionmaker(bind=engine)
        return Session()

    def _query_resolved_tickets(self, since: Optional[datetime] = None) -> list[dict]:
        """同步查询已解决工单，返回文档数据列表（在线程中运行）

        Args:
            since: 增量同步起始时间

        Returns:
            文档数据列表，每项包含 content, metadata, doc_id
        """
        from app.models.ticket import Ticket, TicketStatus

        session = self._get_sync_session()
        try:
            query = session.query(Ticket).filter(
                Ticket.status == TicketStatus.RESOLVED
            )
            if since:
                query = query.filter(Ticket.updated_at >= since)

            tickets = query.all()
            if not tickets:
                logger.info("没有需要同步的已解决工单")
                return []

            results = []
            for t in tickets:
                parts = []
                if t.title:
                    parts.append(f"问题：{t.title}")
                if t.description:
                    parts.append(f"描述：{t.description}")
                if t.solution_text:
                    parts.append(f"解决方法：{t.solution_text}")
                if t.remark:
                    parts.append(f"备注：{t.remark}")

                if not parts:
                    continue

                content = "\n".join(parts)
                doc_id = _make_doc_id("ticket", str(t.id))

                results.append({
                    "content": content,
                    "metadata": {
                        "source_type": "ticket",
                        "source_id": str(t.id),
                        "ticket_no": t.ticket_no or "",
                        "title": t.title or "",
                        "priority": str(t.priority.value) if t.priority else "",
                        "created_at": t.created_at.isoformat() if t.created_at else "",
                        "resolved_at": t.resolved_at.isoformat() if t.resolved_at else "",
                    },
                    "doc_id": doc_id,
                })

            return results
        finally:
            session.close()

    def _parse_faq_docs(self, faq_dir: str) -> list[dict]:
        """解析 FAQ Markdown 文档，返回文档数据列表（在线程中运行）

        Args:
            faq_dir: FAQ 文档目录

        Returns:
            文档数据列表
        """
        if not os.path.isdir(faq_dir):
            logger.info(f"FAQ 目录不存在: {faq_dir}，跳过 FAQ 同步")
            return []

        results = []
        for filename in os.listdir(faq_dir):
            if not filename.endswith(".md"):
                continue

            filepath = os.path.join(faq_dir, filename)
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()

            # 按 heading 拆分段落
            sections = re.split(r"\n(?=#{1,3}\s)", content)

            for section in sections:
                section = section.strip()
                if not section or len(section) < 10:
                    continue

                title_match = re.match(r"^#{1,3}\s+(.+)", section)
                title = title_match.group(1).strip() if title_match else ""

                doc_id = _make_doc_id("faq", f"{filename}:{title}")

                results.append({
                    "content": section,
                    "metadata": {
                        "source_type": "faq",
                        "source_id": f"{filename}:{title}",
                        "filename": filename,
                        "title": title,
                    },
                    "doc_id": doc_id,
                })

        return results

    async def sync_tickets(self, since: Optional[datetime] = None) -> int:
        """从已解决工单同步知识。

        Args:
            since: 增量同步起始时间

        Returns:
            同步的文档数量
        """
        # 在线程中查询数据库
        records = await asyncio.to_thread(self._query_resolved_tickets, since)
        if not records:
            return 0

        # 异步写入向量存储（分批）
        batch_size = 100
        total = 0
        for i in range(0, len(records), batch_size):
            batch = records[i:i + batch_size]
            await self._vectorstore.add_documents(
                docs=[r["content"] for r in batch],
                metadatas=[r["metadata"] for r in batch],
                ids=[r["doc_id"] for r in batch],
            )
            total += len(batch)

        logger.info(f"已同步 {total} 条工单知识")
        return total

    async def sync_faq_docs(self, faq_dir: Optional[str] = None) -> int:
        """从 Markdown FAQ 文档同步知识。

        Args:
            faq_dir: FAQ 文档目录，默认 backend/faq_docs/

        Returns:
            同步的文档数量
        """
        if faq_dir is None:
            faq_dir = os.path.join(
                os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
                "faq_docs",
            )

        # 在线程中解析文件
        records = await asyncio.to_thread(self._parse_faq_docs, faq_dir)
        if not records:
            return 0

        # 异步写入向量存储（分批）
        batch_size = 100
        total = 0
        for i in range(0, len(records), batch_size):
            batch = records[i:i + batch_size]
            await self._vectorstore.add_documents(
                docs=[r["content"] for r in batch],
                metadatas=[r["metadata"] for r in batch],
                ids=[r["doc_id"] for r in batch],
            )
            total += len(batch)

        logger.info(f"已同步 {total} 条 FAQ 知识")
        return total

    async def sync_all(self, force: bool = False, since: Optional[datetime] = None) -> dict:
        """全量/增量同步知识库。

        Args:
            force: 是否强制全量重建（先清空旧数据）
            since: 增量同步起始时间

        Returns:
            同步统计信息
        """
        stats = {"tickets": 0, "faq": 0, "total": 0}

        if force:
            logger.info("强制模式：清空旧数据后全量重建")
            await self._vectorstore.clear()

        ticket_count = await self.sync_tickets(since=since)
        faq_count = await self.sync_faq_docs()

        stats["tickets"] = ticket_count
        stats["faq"] = faq_count
        stats["total"] = ticket_count + faq_count
        stats["sync_time"] = datetime.now(timezone.utc).isoformat()

        self._last_sync = datetime.now(timezone.utc)
        logger.info(f"知识库同步完成: {stats}")
        return stats

    @property
    def last_sync(self) -> Optional[datetime]:
        """最近同步时间"""
        return self._last_sync
