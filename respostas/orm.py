import uuid
from datetime import datetime, timezone

from sqlalchemy import JSON, DateTime, ForeignKey, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from database import Base


class Resposta(Base):
    __tablename__ = "responses"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    form_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("forms.id"), nullable=False)
    user_id: Mapped[uuid.UUID | None] = mapped_column(Uuid(as_uuid=True), ForeignKey("users.id"), nullable=True)
    respondent_name: Mapped[str | None] = mapped_column(String, nullable=True)
    respondent_email: Mapped[str | None] = mapped_column(String, nullable=True)
    respondent_phone: Mapped[str | None] = mapped_column(String, nullable=True)
    assigned_group_id: Mapped[uuid.UUID | None] = mapped_column(Uuid(as_uuid=True), ForeignKey("groups.id"), nullable=True)
    variable_scores: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    answers: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    submitted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
