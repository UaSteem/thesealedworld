"""Frozen site schema before 0002 (raw refresh tokens, no referrals/email verification).

Revision ID: 0001_site_schema_baseline
Revises:
Create Date: 2026-05-19 00:00:00.000000

Do not import application metadata here: later revisions own later fields.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0001_site_schema_baseline"
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(sa.text("CREATE SCHEMA IF NOT EXISTS site"))
    op.create_table(
        "articles",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("slug", sa.String(length=200), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("preview", sa.String(length=400), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("cover_image", sa.String(length=500), nullable=True),
        sa.Column("is_published", sa.Boolean(), nullable=False),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_articles")),
        schema="site",
    )
    op.create_index(op.f("ix_site_articles_slug"), "articles", ["slug"], unique=True, schema="site")
    op.create_table(
        "auth_users",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("email", sa.String(length=320), nullable=False),
        sa.Column("hashed_password", sa.String(length=512), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("is_superuser", sa.Boolean(), nullable=False),
        sa.Column("tester_status", sa.String(length=20), nullable=False),
        sa.Column("tester_approved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_auth_users")),
        schema="site",
    )
    op.create_index(op.f("ix_site_auth_users_email"), "auth_users", ["email"], unique=True, schema="site")
    op.create_table(
        "player_daily_activity",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("player_id", sa.Uuid(), nullable=False),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("first_seen", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_seen", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_player_daily_activity")),
        sa.UniqueConstraint("player_id", "date", name="uq_player_daily_activity"),
        schema="site",
    )
    op.create_index(
        op.f("ix_site_player_daily_activity_date"), "player_daily_activity", ["date"], unique=False, schema="site"
    )
    op.create_table(
        "surveys",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_surveys")),
        schema="site",
    )
    op.create_table(
        "auth_refresh_tokens",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("token", sa.String(length=128), nullable=False),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["site.auth_users.id"],
            name=op.f("fk_auth_refresh_tokens_user_id_auth_users"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_auth_refresh_tokens")),
        schema="site",
    )
    op.create_index("ix_site_auth_refresh_tokens_token", "auth_refresh_tokens", ["token"], unique=True, schema="site")
    op.create_table(
        "feedback",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("type", sa.String(length=20), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("priority", sa.String(length=20), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["site.auth_users.id"], name=op.f("fk_feedback_user_id_auth_users")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_feedback")),
        schema="site",
    )
    op.create_table(
        "survey_questions",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("survey_id", sa.Integer(), nullable=False),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("question_type", sa.String(length=20), nullable=False),
        sa.Column("choices_json", sa.Text(), nullable=True),
        sa.Column("order", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["survey_id"], ["site.surveys.id"], name=op.f("fk_survey_questions_survey_id_surveys")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_survey_questions")),
        schema="site",
    )
    op.create_table(
        "survey_sends",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("survey_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("token", sa.String(length=64), nullable=False),
        sa.Column("sent_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["survey_id"], ["site.surveys.id"], name=op.f("fk_survey_sends_survey_id_surveys")),
        sa.ForeignKeyConstraint(["user_id"], ["site.auth_users.id"], name=op.f("fk_survey_sends_user_id_auth_users")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_survey_sends")),
        schema="site",
    )
    op.create_index(op.f("ix_site_survey_sends_token"), "survey_sends", ["token"], unique=True, schema="site")
    op.create_table(
        "survey_responses",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("send_id", sa.Integer(), nullable=False),
        sa.Column("answers_json", sa.Text(), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(
            ["send_id"], ["site.survey_sends.id"], name=op.f("fk_survey_responses_send_id_survey_sends")
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_survey_responses")),
        sa.UniqueConstraint("send_id", name=op.f("uq_survey_responses_send_id")),
        schema="site",
    )


def downgrade() -> None:
    op.drop_table("survey_responses", schema="site")
    op.drop_table("survey_sends", schema="site")
    op.drop_table("survey_questions", schema="site")
    op.drop_table("feedback", schema="site")
    op.drop_table("auth_refresh_tokens", schema="site")
    op.drop_table("surveys", schema="site")
    op.drop_table("player_daily_activity", schema="site")
    op.drop_table("auth_users", schema="site")
    op.drop_table("articles", schema="site")
    # Refuse to destroy unrelated objects; PostgreSQL rolls back this migration.
    op.execute(sa.text("DROP SCHEMA site"))
