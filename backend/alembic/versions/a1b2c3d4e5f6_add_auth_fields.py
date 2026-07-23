"""add auth fields: login_id, password_hash, unique phone, pending status

Revision ID: a1b2c3d4e5f6
Revises:
Create Date: 2026-07-23

新增认证体系相关字段：
- users.login_id  专属ID号（唯一索引，可空）
- users.password_hash  密码哈希（可空）
- users.phone 改为唯一索引（登录键）
- UserStatus 新增 pending（SQLite 枚举无强约束，无需 DDL 变更）

SQLite 不支持直接 ALTER 加约束，使用 batch 模式。
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 新增列（批处理模式，兼容 SQLite）
    with op.batch_alter_table("users") as batch_op:
        batch_op.add_column(sa.Column("login_id", sa.String(length=32), nullable=True))
        batch_op.add_column(sa.Column("password_hash", sa.String(length=256), nullable=True))

    # 唯一索引：login_id、phone
    op.create_index("ix_users_login_id", "users", ["login_id"], unique=True)
    op.create_index("ix_users_phone", "users", ["phone"], unique=True)

    # 注：UserStatus 新增 pending 值。SQLite 将枚举存为 VARCHAR，无 CHECK 约束，
    # 无需变更表结构；MySQL 若使用原生 ENUM 需 ALTER，此处按 SQLite 部署默认处理。


def downgrade() -> None:
    op.drop_index("ix_users_phone", table_name="users")
    op.drop_index("ix_users_login_id", table_name="users")
    with op.batch_alter_table("users") as batch_op:
        batch_op.drop_column("password_hash")
        batch_op.drop_column("login_id")
