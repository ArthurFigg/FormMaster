import uuid

from fastapi import HTTPException
from sqlalchemy.orm import Session

import formularios.repositorio as repo
from formularios.modelos import PatchFormulario
from formularios.orm import Formulario, Grupo, GrupoThreshold, Pergunta, Regra, Variavel


def criar_formulario_de_ia(db: Session, dados_ia: "RespostaIA", owner_id: uuid.UUID, objetivo: str) -> Formulario:
    formulario = Formulario(owner_id=owner_id, title=objetivo[:100])
    db.add(formulario)
    db.flush()

    for i, q in enumerate(dados_ia.questions):
        db.add(Pergunta(
            form_id=formulario.id,
            order=i,
            text=q.text,
            type=q.type,
            options=q.options,
            required=q.required,
        ))

    mapa_grupos: dict[str, uuid.UUID] = {}
    for g in dados_ia.groups:
        grupo = Grupo(form_id=formulario.id, name=g.name)
        db.add(grupo)
        db.flush()
        mapa_grupos[g.name] = grupo.id

    mapa_variaveis: dict[str, uuid.UUID] = {}
    for v in dados_ia.variables:
        variavel = Variavel(form_id=formulario.id, name=v.name, initial_value=v.initial_value)
        db.add(variavel)
        db.flush()
        mapa_variaveis[v.name] = variavel.id

    for r in dados_ia.rules:
        db.add(Regra(
            form_id=formulario.id,
            order=r.order,
            conditions=[c.model_dump() for c in r.conditions],
            logical_operator=r.logical_operator,
            action_type=r.action_type,
            action_target=r.action_target,  # nome conceitual — mapeado para UUID pelo mestre no editor
            action_value=r.action_value,
        ))

    # order = posição sequencial da primeira ocorrência de cada grupo no array
    ordem_grupos: dict[str, int] = {}
    proximo_order = 1
    for t in dados_ia.group_thresholds:
        if t.group not in ordem_grupos:
            ordem_grupos[t.group] = proximo_order
            proximo_order += 1
        group_id = mapa_grupos.get(t.group)
        variable_id = mapa_variaveis.get(t.variable)
        if group_id and variable_id:
            db.add(GrupoThreshold(
                group_id=group_id,
                variable_id=variable_id,
                operator=t.operator,
                value=t.value,
                order=ordem_grupos[t.group],
            ))

    db.commit()
    db.refresh(formulario)
    return formulario


def criar_formulario(db: Session, owner_id: uuid.UUID) -> Formulario:
    formulario = Formulario(owner_id=owner_id)
    db.add(formulario)
    db.commit()
    db.refresh(formulario)
    return formulario


def patch_atomico(db: Session, form_id: uuid.UUID, owner_id: uuid.UUID, payload: PatchFormulario) -> Formulario:
    formulario = repo.buscar_por_id(db, form_id)
    if not formulario:
        raise HTTPException(status_code=404, detail="Formulário não encontrado.")
    if formulario.owner_id != owner_id:
        raise HTTPException(status_code=403, detail="Acesso negado.")
    if payload.block_resubmit and not payload.collect_email:
        raise HTTPException(status_code=422, detail="block_resubmit requer collect_email=true.")

    formulario.title = payload.title
    formulario.collect_name = payload.collect_name
    formulario.collect_email = payload.collect_email
    formulario.collect_phone = payload.collect_phone
    formulario.name_required = payload.name_required
    formulario.email_required = payload.email_required
    formulario.phone_required = payload.phone_required
    formulario.block_resubmit = payload.block_resubmit
    formulario.finish_mode = payload.finish_mode

    # Reconciliar em ordem de dependência: thresholds antes de grupos (FK)
    repo.reconciliar_thresholds(db, form_id, payload.thresholds)
    repo.reconciliar_regras(db, form_id, payload.rules)
    repo.reconciliar_perguntas(db, form_id, payload.questions)
    repo.reconciliar_variaveis(db, form_id, payload.variables)
    repo.reconciliar_grupos(db, form_id, payload.groups)

    db.commit()
    db.refresh(formulario)
    return formulario


def publicar(db: Session, form_id: uuid.UUID, owner_id: uuid.UUID) -> Formulario:
    formulario = repo.buscar_por_id(db, form_id)
    if not formulario:
        raise HTTPException(status_code=404, detail="Formulário não encontrado.")
    if formulario.owner_id != owner_id:
        raise HTTPException(status_code=403, detail="Acesso negado.")
    if formulario.status == "active":
        raise HTTPException(status_code=400, detail="Formulário já está publicado.")
    if formulario.status == "closed":
        raise HTTPException(status_code=400, detail="Formulário encerrado não pode ser republicado.")
    formulario.status = "active"
    db.commit()
    return formulario


def encerrar(db: Session, form_id: uuid.UUID, owner_id: uuid.UUID) -> Formulario:
    formulario = repo.buscar_por_id(db, form_id)
    if not formulario:
        raise HTTPException(status_code=404, detail="Formulário não encontrado.")
    if formulario.owner_id != owner_id:
        raise HTTPException(status_code=403, detail="Acesso negado.")
    if formulario.status == "draft":
        raise HTTPException(status_code=400, detail="Formulário em rascunho não pode ser encerrado.")
    if formulario.status == "closed":
        raise HTTPException(status_code=400, detail="Formulário já está encerrado.")
    formulario.status = "closed"
    db.commit()
    return formulario
