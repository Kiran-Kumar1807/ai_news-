"""Initial schema: users, niches, user_preferences, articles.

Revision ID: 0001_initial
Revises:
Create Date: 2026-07-20
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0001_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("email", sa.String(length=320), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("full_name", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)
    op.create_index("ix_users_id", "users", ["id"])

    op.create_table(
        "niches",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("niche_name", sa.String(length=100), nullable=False),
        sa.UniqueConstraint("niche_name", name="uq_niches_name"),
    )
    op.create_index("ix_niches_id", "niches", ["id"])

    op.create_table(
        "user_preferences",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("niche_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["niche_id"], ["niches.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("user_id", "niche_id", name="uq_user_niche"),
    )
    op.create_index("ix_user_preferences_id", "user_preferences", ["id"])
    op.create_index("ix_user_preferences_user_id", "user_preferences", ["user_id"])
    op.create_index("ix_user_preferences_niche_id", "user_preferences", ["niche_id"])

    op.create_table(
        "articles",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("title", sa.String(length=512), nullable=False),
        sa.Column("source", sa.String(length=128), nullable=False),
        sa.Column("article_url", sa.String(length=1024), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("category", sa.String(length=64), nullable=False),
        sa.Column("article_hash", sa.String(length=64), nullable=False),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_articles_id", "articles", ["id"])
    op.create_index("ix_articles_source", "articles", ["source"])
    op.create_index("ix_articles_category", "articles", ["category"])
    op.create_index("ix_articles_hash", "articles", ["article_hash"], unique=True)
    op.create_index("ix_articles_published_at", "articles", ["published_at"])
    op.create_index("ix_articles_created_at", "articles", ["created_at"])


def downgrade() -> None:
    op.drop_table("articles")
    op.drop_table("user_preferences")
    op.drop_table("niches")
    op.drop_table("users")
