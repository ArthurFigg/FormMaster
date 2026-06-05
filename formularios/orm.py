import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy import JSON, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base


class Formulario(Base):
    __tablename__ = "forms"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    owner_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("users.id"), nullable=False)
    title: Mapped[str] = mapped_column(String, nullable=False, default="Novo formulário")
    status: Mapped[str] = mapped_column(String, nullable=False, default="draft")
    block_resubmit: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    collect_name: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    collect_email: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    collect_phone: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    name_required: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    email_required: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    phone_required: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    finish_mode: Mapped[str] = mapped_column(String, nullable=False, default="generic")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    perguntas: Mapped[list["Pergunta"]] = relationship(
        "Pergunta", back_populates="formulario", cascade="all, delete-orphan"
    )
    grupos: Mapped[list["Grupo"]] = relationship(
        "Grupo", back_populates="formulario", cascade="all, delete-orphan"
    )
    variaveis: Mapped[list["Variavel"]] = relationship(
        "Variavel", back_populates="formulario", cascade="all, delete-orphan"
    )
    regras: Mapped[list["Regra"]] = relationship(
        "Regra", back_populates="formulario", cascade="all, delete-orphan"
    )


class Pergunta(Base):
    __tablename__ = "questions"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    form_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("forms.id"), nullable=False)
    order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    text: Mapped[str] = mapped_column(String, nullable=False)
    type: Mapped[str] = mapped_column(String, nullable=False)
    options: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    required: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    formulario: Mapped["Formulario"] = relationship("Formulario", back_populates="perguntas")


class Grupo(Base):
    __tablename__ = "groups"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    form_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("forms.id"), nullable=False)
    name: Mapped[str] = mapped_column(String, nullable=False)
    finish_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    formulario: Mapped["Formulario"] = relationship("Formulario", back_populates="grupos")
    thresholds: Mapped[list["GrupoThreshold"]] = relationship(
        "GrupoThreshold", back_populates="grupo", cascade="all, delete-orphan"
    )


class Variavel(Base):
    __tablename__ = "variables"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    form_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("forms.id"), nullable=False)
    name: Mapped[str] = mapped_column(String, nullable=False)
    initial_value: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    formulario: Mapped["Formulario"] = relationship("Formulario", back_populates="variaveis")


class Regra(Base):
    __tablename__ = "rules"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    form_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("forms.id"), nullable=False)
    order: Mapped[int] = mapped_column(Integer, nullable=False)
    conditions: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    logical_operator: Mapped[str] = mapped_column(String, nullable=False, default="AND")
    action_type: Mapped[str] = mapped_column(String, nullable=False)
    action_target: Mapped[str] = mapped_column(String, nullable=False)
    action_value: Mapped[int | None] = mapped_column(Integer, nullable=True)

    formulario: Mapped["Formulario"] = relationship("Formulario", back_populates="regras")


class GrupoThreshold(Base):
    __tablename__ = "group_thresholds"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    group_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("groups.id", ondelete="CASCADE"), nullable=False
    )
    variable_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("variables.id"), nullable=False
    )
    operator: Mapped[str] = mapped_column(String, nullable=False)
    value: Mapped[int] = mapped_column(Integer, nullable=False)
    order: Mapped[int] = mapped_column(Integer, nullable=False)

    grupo: Mapped["Grupo"] = relationship("Grupo", back_populates="thresholds")
