"""cria tabelas formularios

Revision ID: fa413121fefe
Revises: 0d3b1e5ff18f
Create Date: 2026-06-04 17:51:47.897557

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = 'fa413121fefe'
down_revision: Union[str, Sequence[str], None] = '0d3b1e5ff18f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "forms",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("owner_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("title", sa.String(), nullable=False, server_default="Novo formulário"),
        sa.Column("status", sa.String(), nullable=False, server_default="draft"),
        sa.Column("block_resubmit", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("collect_name", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("collect_email", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("collect_phone", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("name_required", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("email_required", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("phone_required", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("finish_mode", sa.String(), nullable=False, server_default="generic"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["owner_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "questions",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("form_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("text", sa.String(), nullable=False),
        sa.Column("type", sa.String(), nullable=False),
        sa.Column("options", postgresql.JSONB(), nullable=True),
        sa.Column("required", sa.Boolean(), nullable=False, server_default="false"),
        sa.ForeignKeyConstraint(["form_id"], ["forms.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "groups",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("form_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("finish_message", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["form_id"], ["forms.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "variables",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("form_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("initial_value", sa.Integer(), nullable=False, server_default="0"),
        sa.ForeignKeyConstraint(["form_id"], ["forms.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "rules",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("form_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("order", sa.Integer(), nullable=False),
        sa.Column("conditions", postgresql.JSONB(), nullable=False),
        sa.Column("logical_operator", sa.String(), nullable=False, server_default="AND"),
        sa.Column("action_type", sa.String(), nullable=False),
        sa.Column("action_target", sa.String(), nullable=False),
        sa.Column("action_value", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(["form_id"], ["forms.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "group_thresholds",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("group_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("variable_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("operator", sa.String(), nullable=False),
        sa.Column("value", sa.Integer(), nullable=False),
        sa.Column("order", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["group_id"], ["groups.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["variable_id"], ["variables.id"]),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("group_thresholds")
    op.drop_table("rules")
    op.drop_table("variables")
    op.drop_table("groups")
    op.drop_table("questions")
    op.drop_table("forms")
