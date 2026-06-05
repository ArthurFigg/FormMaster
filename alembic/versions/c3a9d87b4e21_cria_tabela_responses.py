"""cria tabela responses

Revision ID: c3a9d87b4e21
Revises: fa413121fefe
Create Date: 2026-06-05 00:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = 'c3a9d87b4e21'
down_revision: Union[str, Sequence[str], None] = 'fa413121fefe'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "responses",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("form_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("respondent_name", sa.String(), nullable=True),
        sa.Column("respondent_email", sa.String(), nullable=True),
        sa.Column("respondent_phone", sa.String(), nullable=True),
        sa.Column("assigned_group_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("variable_scores", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column("answers", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column("submitted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["form_id"], ["forms.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["assigned_group_id"], ["groups.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_responses_form_email", "responses", ["form_id", "respondent_email"])


def downgrade() -> None:
    op.drop_index("ix_responses_form_email", table_name="responses")
    op.drop_table("responses")
