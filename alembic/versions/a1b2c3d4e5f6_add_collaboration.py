"""add collaborative project management

Revision ID: a1b2c3d4e5f6
Revises: 37a8f5c4eb70
Create Date: 2026-10-24 20:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, Sequence[str], None] = "37a8f5c4eb70"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _table_exists(name: str) -> bool:
    bind = op.get_bind()
    return name in inspect(bind).get_table_names()


def _column_exists(table: str, column: str) -> bool:
    bind = op.get_bind()
    cols = [c["name"] for c in inspect(bind).get_columns(table)]
    return column in cols


def upgrade() -> None:
    if not _table_exists("project_members"):
        op.create_table(
            "project_members",
            sa.Column("project_id", sa.String(length=36), nullable=False),
            sa.Column("user_id", sa.String(length=36), nullable=False),
            sa.Column("role", sa.String(length=20), nullable=False),
            sa.Column("status", sa.String(length=20), nullable=False),
            sa.Column("invited_by_id", sa.String(length=36), nullable=True),
            sa.Column("invited_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("joined_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("id", sa.String(length=36), nullable=False),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                server_default=sa.text("(CURRENT_TIMESTAMP)"),
                nullable=False,
            ),
            sa.Column(
                "updated_at",
                sa.DateTime(timezone=True),
                server_default=sa.text("(CURRENT_TIMESTAMP)"),
                nullable=False,
            ),
            sa.ForeignKeyConstraint(["invited_by_id"], ["users.id"], ondelete="SET NULL"),
            sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("project_id", "user_id", name="uq_project_member_project_user"),
        )
        op.create_index(op.f("ix_project_members_project_id"), "project_members", ["project_id"], unique=False)
        op.create_index(op.f("ix_project_members_user_id"), "project_members", ["user_id"], unique=False)
        op.create_index(op.f("ix_project_members_role"), "project_members", ["role"], unique=False)
        op.create_index(op.f("ix_project_members_status"), "project_members", ["status"], unique=False)
        op.create_index(op.f("ix_project_members_invited_by_id"), "project_members", ["invited_by_id"], unique=False)

    if not _table_exists("notifications"):
        op.create_table(
            "notifications",
            sa.Column("user_id", sa.String(length=36), nullable=False),
            sa.Column("type", sa.String(length=50), nullable=False),
            sa.Column("title", sa.String(length=200), nullable=False),
            sa.Column("message", sa.Text(), nullable=False),
            sa.Column("data", sa.JSON(), nullable=True),
            sa.Column("is_read", sa.Boolean(), nullable=False),
            sa.Column("project_id", sa.String(length=36), nullable=True),
            sa.Column("id", sa.String(length=36), nullable=False),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                server_default=sa.text("(CURRENT_TIMESTAMP)"),
                nullable=False,
            ),
            sa.Column(
                "updated_at",
                sa.DateTime(timezone=True),
                server_default=sa.text("(CURRENT_TIMESTAMP)"),
                nullable=False,
            ),
            sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="SET NULL"),
            sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index(op.f("ix_notifications_user_id"), "notifications", ["user_id"], unique=False)
        op.create_index(op.f("ix_notifications_type"), "notifications", ["type"], unique=False)
        op.create_index(op.f("ix_notifications_is_read"), "notifications", ["is_read"], unique=False)
        op.create_index(op.f("ix_notifications_project_id"), "notifications", ["project_id"], unique=False)

    # Only add missing task columns (partial previous runs may already have them)
    need_created_by = not _column_exists("tasks", "created_by_id")
    need_assignee = not _column_exists("tasks", "assignee_id")
    if need_created_by or need_assignee:
        with op.batch_alter_table("tasks", schema=None) as batch_op:
            if need_created_by:
                batch_op.add_column(sa.Column("created_by_id", sa.String(length=36), nullable=True))
                batch_op.create_index(op.f("ix_tasks_created_by_id"), ["created_by_id"], unique=False)
            if need_assignee:
                batch_op.add_column(sa.Column("assignee_id", sa.String(length=36), nullable=True))
                batch_op.create_index(op.f("ix_tasks_assignee_id"), ["assignee_id"], unique=False)


def downgrade() -> None:
    if _column_exists("tasks", "assignee_id") or _column_exists("tasks", "created_by_id"):
        with op.batch_alter_table("tasks", schema=None) as batch_op:
            if _column_exists("tasks", "assignee_id"):
                try:
                    batch_op.drop_index(op.f("ix_tasks_assignee_id"))
                except Exception:
                    pass
                batch_op.drop_column("assignee_id")
            if _column_exists("tasks", "created_by_id"):
                try:
                    batch_op.drop_index(op.f("ix_tasks_created_by_id"))
                except Exception:
                    pass
                batch_op.drop_column("created_by_id")

    if _table_exists("notifications"):
        op.drop_index(op.f("ix_notifications_project_id"), table_name="notifications")
        op.drop_index(op.f("ix_notifications_is_read"), table_name="notifications")
        op.drop_index(op.f("ix_notifications_type"), table_name="notifications")
        op.drop_index(op.f("ix_notifications_user_id"), table_name="notifications")
        op.drop_table("notifications")

    if _table_exists("project_members"):
        op.drop_index(op.f("ix_project_members_invited_by_id"), table_name="project_members")
        op.drop_index(op.f("ix_project_members_status"), table_name="project_members")
        op.drop_index(op.f("ix_project_members_role"), table_name="project_members")
        op.drop_index(op.f("ix_project_members_user_id"), table_name="project_members")
        op.drop_index(op.f("ix_project_members_project_id"), table_name="project_members")
        op.drop_table("project_members")
