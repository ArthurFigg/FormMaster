import uuid

from sqlalchemy.orm import Session

from formularios.modelos import (
    GrupoSchema,
    PerguntaSchema,
    RegraSchema,
    ThresholdSchema,
    VariavelSchema,
)
from formularios.orm import Formulario, Grupo, GrupoThreshold, Pergunta, Regra, Variavel


def buscar_por_id(db: Session, form_id: uuid.UUID) -> Formulario | None:
    return db.get(Formulario, form_id)


def listar_por_dono(db: Session, owner_id: uuid.UUID) -> list[Formulario]:
    return (
        db.query(Formulario)
        .filter(Formulario.owner_id == owner_id)
        .order_by(Formulario.created_at.desc())
        .all()
    )


def formulario_para_dict(f: Formulario) -> dict:
    """Serializa um Formulario com todas as entidades para uso nos templates."""
    return {
        "id": str(f.id),
        "title": f.title,
        "status": f.status,
        "collect_name": f.collect_name,
        "collect_email": f.collect_email,
        "collect_phone": f.collect_phone,
        "name_required": f.name_required,
        "email_required": f.email_required,
        "phone_required": f.phone_required,
        "block_resubmit": f.block_resubmit,
        "finish_mode": f.finish_mode,
        "questions": [
            {
                "id": str(p.id),
                "order": p.order,
                "text": p.text,
                "type": p.type,
                "options": p.options,
                "required": p.required,
            }
            for p in sorted(f.perguntas, key=lambda x: x.order)
        ],
        "groups": [
            {"id": str(g.id), "name": g.name, "finish_message": g.finish_message}
            for g in f.grupos
        ],
        "variables": [
            {"id": str(v.id), "name": v.name, "initial_value": v.initial_value}
            for v in f.variaveis
        ],
        "rules": [
            {
                "id": str(r.id),
                "order": r.order,
                "conditions": r.conditions,
                "logical_operator": r.logical_operator,
                "action_type": r.action_type,
                "action_target": r.action_target,
                "action_value": r.action_value,
            }
            for r in sorted(f.regras, key=lambda x: x.order)
        ],
        "thresholds": [
            {
                "id": str(t.id),
                "group_id": str(t.group_id),
                "variable_id": str(t.variable_id),
                "operator": t.operator,
                "value": t.value,
                "order": t.order,
            }
            for g in f.grupos
            for t in g.thresholds
        ],
    }


def reconciliar_perguntas(db: Session, form_id: uuid.UUID, perguntas: list[PerguntaSchema]) -> None:
    existentes = {p.id: p for p in db.query(Pergunta).filter(Pergunta.form_id == form_id).all()}
    ids_payload = {p.id for p in perguntas if p.id is not None}

    for pid, obj in existentes.items():
        if pid not in ids_payload:
            db.delete(obj)

    for i, p in enumerate(perguntas):
        if p.id is None:
            db.add(Pergunta(form_id=form_id, order=i, text=p.text, type=p.type, options=p.options, required=p.required))
        elif p.id in existentes:
            obj = existentes[p.id]
            obj.order = i
            obj.text = p.text
            obj.type = p.type
            obj.options = p.options
            obj.required = p.required


def reconciliar_grupos(db: Session, form_id: uuid.UUID, grupos: list[GrupoSchema]) -> None:
    existentes = {g.id: g for g in db.query(Grupo).filter(Grupo.form_id == form_id).all()}
    ids_payload = {g.id for g in grupos if g.id is not None}

    for gid, obj in existentes.items():
        if gid not in ids_payload:
            db.delete(obj)

    for g in grupos:
        if g.id is None:
            db.add(Grupo(form_id=form_id, name=g.name, finish_message=g.finish_message))
        elif g.id in existentes:
            obj = existentes[g.id]
            obj.name = g.name
            obj.finish_message = g.finish_message


def reconciliar_variaveis(db: Session, form_id: uuid.UUID, variaveis: list[VariavelSchema]) -> None:
    existentes = {v.id: v for v in db.query(Variavel).filter(Variavel.form_id == form_id).all()}
    ids_payload = {v.id for v in variaveis if v.id is not None}

    for vid, obj in existentes.items():
        if vid not in ids_payload:
            db.delete(obj)

    for v in variaveis:
        if v.id is None:
            db.add(Variavel(form_id=form_id, name=v.name, initial_value=v.initial_value))
        elif v.id in existentes:
            obj = existentes[v.id]
            obj.name = v.name
            obj.initial_value = v.initial_value


def reconciliar_regras(db: Session, form_id: uuid.UUID, regras: list[RegraSchema]) -> None:
    existentes = {r.id: r for r in db.query(Regra).filter(Regra.form_id == form_id).all()}
    ids_payload = {r.id for r in regras if r.id is not None}

    for rid, obj in existentes.items():
        if rid not in ids_payload:
            db.delete(obj)

    for r in regras:
        conds = [c.model_dump() for c in r.conditions]
        if r.id is None:
            db.add(Regra(
                form_id=form_id,
                order=r.order,
                conditions=conds,
                logical_operator=r.logical_operator,
                action_type=r.action_type,
                action_target=r.action_target,
                action_value=r.action_value,
            ))
        elif r.id in existentes:
            obj = existentes[r.id]
            obj.order = r.order
            obj.conditions = conds
            obj.logical_operator = r.logical_operator
            obj.action_type = r.action_type
            obj.action_target = r.action_target
            obj.action_value = r.action_value


def reconciliar_thresholds(db: Session, form_id: uuid.UUID, thresholds: list[ThresholdSchema]) -> None:
    existentes = {
        t.id: t
        for t in (
            db.query(GrupoThreshold)
            .join(Grupo, GrupoThreshold.group_id == Grupo.id)
            .filter(Grupo.form_id == form_id)
            .all()
        )
    }
    ids_payload = {t.id for t in thresholds if t.id is not None}

    for tid, obj in existentes.items():
        if tid not in ids_payload:
            db.delete(obj)

    for t in thresholds:
        if t.id is None:
            db.add(GrupoThreshold(
                group_id=t.group_id,
                variable_id=t.variable_id,
                operator=t.operator,
                value=t.value,
                order=t.order,
            ))
        elif t.id in existentes:
            obj = existentes[t.id]
            obj.group_id = t.group_id
            obj.variable_id = t.variable_id
            obj.operator = t.operator
            obj.value = t.value
            obj.order = t.order
