"""add performance indexes on high-frequency query columns

Revision ID: f7a8b9c0d1e2
Revises: a1b2c3d4e5f6
Create Date: 2026-07-23

为高频查询字段添加数据库索引，提升查询性能：
- tickets: status, created_at, assignee_id, creator_id, category_id
- ticket_logs: ticket_id
- chat_messages: room_id
- chat_message_reads: message_id, user_id
"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "f7a8b9c0d1e2"
down_revision: Union[str, None] = "a1b2c3d4e5f6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # tickets 表索引
    op.create_index("ix_tickets_status", "tickets", ["status"])
    op.create_index("ix_tickets_created_at", "tickets", ["created_at"])
    op.create_index("ix_tickets_assignee_id", "tickets", ["assignee_id"])
    op.create_index("ix_tickets_creator_id", "tickets", ["creator_id"])
    op.create_index("ix_tickets_category_id", "tickets", ["category_id"])

    # ticket_logs 表索引
    op.create_index("ix_ticket_logs_ticket_id", "ticket_logs", ["ticket_id"])

    # chat_messages 表索引
    op.create_index("ix_chat_messages_room_id", "chat_messages", ["room_id"])

    # chat_message_reads 表索引
    op.create_index("ix_chat_message_reads_message_id", "chat_message_reads", ["message_id"])
    op.create_index("ix_chat_message_reads_user_id", "chat_message_reads", ["user_id"])


def downgrade() -> None:
    op.drop_index("ix_chat_message_reads_user_id", table_name="chat_message_reads")
    op.drop_index("ix_chat_message_reads_message_id", table_name="chat_message_reads")
    op.drop_index("ix_chat_messages_room_id", table_name="chat_messages")
    op.drop_index("ix_ticket_logs_ticket_id", table_name="ticket_logs")
    op.drop_index("ix_tickets_category_id", table_name="tickets")
    op.drop_index("ix_tickets_creator_id", table_name="tickets")
    op.drop_index("ix_tickets_assignee_id", table_name="tickets")
    op.drop_index("ix_tickets_created_at", table_name="tickets")
    op.drop_index("ix_tickets_status", table_name="tickets")
