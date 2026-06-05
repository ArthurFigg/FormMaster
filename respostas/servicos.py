import uuid
from typing import Any

from fastapi import HTTPException
from sqlalchemy.orm import Session

import respostas.repositorio as repo
from formularios.orm import Formulario, GrupoThreshold, Regra, Variavel
from respostas.motor import avaliar
from respostas.orm import Resposta


def _desserializar_answers(raw: dict[str, Any], formulario: Formulario) -> dict[str, Any]:
    """Converte os valores do form POST para os tipos corretos antes de chamar o motor."""
    tipo_por_id = {str(p.id): p.type for p in formulario.perguntas}
    resultado: dict[str, Any] = {}
    for qid, valor in raw.items():
        tipo = tipo_por_id.get(qid)
        if tipo in ('scale', 'number'):
            try:
                resultado[qid] = int(valor)
            except (ValueError, TypeError):
                resultado[qid] = valor
        elif tipo == 'checkbox':
            resultado[qid] = valor if isinstance(valor, list) else [valor]
        else:
            resultado[qid] = valor
    return resultado


def processar_submissao(
    db: Session,
    formulario: Formulario,
    respondent_name: str | None,
    respondent_email: str | None,
    respondent_phone: str | None,
    answers_raw: dict[str, Any],
    user_id: uuid.UUID | None,
) -> Resposta:
    if formulario.status == 'draft':
        raise HTTPException(status_code=404)
    if formulario.status == 'closed':
        raise HTTPException(status_code=403, detail="Formulário encerrado.")

    if formulario.block_resubmit:
        if not respondent_email:
            raise HTTPException(status_code=422, detail="Email obrigatório para este formulário.")
        if repo.buscar_por_form_email(db, formulario.id, respondent_email):
            raise HTTPException(status_code=409, detail="Você já respondeu este formulário.")

    answers = _desserializar_answers(answers_raw, formulario)

    regras = [
        {
            'id': r.id, 'order': r.order,
            'conditions': r.conditions,
            'logical_operator': r.logical_operator,
            'action_type': r.action_type,
            'action_target': r.action_target,
            'action_value': r.action_value,
        }
        for r in sorted(formulario.regras, key=lambda x: x.order)
    ]

    thresholds_db = (
        db.query(GrupoThreshold)
        .join(GrupoThreshold.grupo)
        .filter(GrupoThreshold.grupo.has(form_id=formulario.id))
        .all()
    )
    thresholds = [
        {
            'id': t.id, 'group_id': t.group_id,
            'variable_id': t.variable_id,
            'operator': t.operator, 'value': t.value, 'order': t.order,
        }
        for t in thresholds_db
    ]

    variaveis = [
        {'id': v.id, 'name': v.name, 'initial_value': v.initial_value}
        for v in formulario.variaveis
    ]

    grupo_id, scores = avaliar(regras, thresholds, variaveis, answers)

    return repo.criar_resposta(
        db=db,
        form_id=formulario.id,
        user_id=user_id,
        respondent_name=respondent_name,
        respondent_email=respondent_email,
        respondent_phone=respondent_phone,
        assigned_group_id=grupo_id,
        variable_scores=scores,
        answers=answers,
    )
