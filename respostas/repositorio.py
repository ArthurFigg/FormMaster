import uuid
from typing import Any

from sqlalchemy.orm import Session

from respostas.orm import Resposta


def buscar_por_form_email(db: Session, form_id: uuid.UUID, email: str) -> Resposta | None:
    return (
        db.query(Resposta)
        .filter(Resposta.form_id == form_id, Resposta.respondent_email == email)
        .first()
    )


def criar_resposta(
    db: Session,
    form_id: uuid.UUID,
    user_id: uuid.UUID | None,
    respondent_name: str | None,
    respondent_email: str | None,
    respondent_phone: str | None,
    assigned_group_id: uuid.UUID | None,
    variable_scores: dict[str, int],
    answers: dict[str, Any],
) -> Resposta:
    resposta = Resposta(
        form_id=form_id,
        user_id=user_id,
        respondent_name=respondent_name,
        respondent_email=respondent_email,
        respondent_phone=respondent_phone,
        assigned_group_id=assigned_group_id,
        variable_scores=variable_scores,
        answers=answers,
    )
    db.add(resposta)
    db.commit()
    db.refresh(resposta)
    return resposta


def buscar_por_id(db: Session, response_id: uuid.UUID) -> Resposta | None:
    return db.get(Resposta, response_id)


def vincular_respostas_ao_usuario(db: Session, email: str, user_id: uuid.UUID) -> None:
    db.query(Resposta).filter(
        Resposta.respondent_email == email,
        Resposta.user_id.is_(None),
    ).update({"user_id": user_id})
    db.commit()
