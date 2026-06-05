import uuid

from sqlalchemy import func
from sqlalchemy.orm import Session

from dashboard.modelos import ItemRespondente, MediaGrupo, ResumoGrupo
from formularios.orm import Formulario, Grupo, Pergunta, Variavel
from respostas.orm import Resposta


def agregar_por_grupo(db: Session, form_id: uuid.UUID) -> list[ResumoGrupo]:
    grupos = db.query(Grupo).filter(Grupo.form_id == form_id).all()
    resultado = []
    for grupo in grupos:
        contagem = (
            db.query(func.count(Resposta.id))
            .filter(Resposta.form_id == form_id, Resposta.assigned_group_id == grupo.id)
            .scalar() or 0
        )
        resultado.append(ResumoGrupo(nome=grupo.name, contagem=contagem))

    sem_class = (
        db.query(func.count(Resposta.id))
        .filter(Resposta.form_id == form_id, Resposta.assigned_group_id.is_(None))
        .scalar() or 0
    )
    if sem_class > 0:
        resultado.append(ResumoGrupo(nome="Sem classificação", contagem=sem_class))

    return resultado


def calcular_medias_por_grupo(db: Session, form_id: uuid.UUID) -> list[MediaGrupo]:
    variaveis = db.query(Variavel).filter(Variavel.form_id == form_id).all()
    if not variaveis:
        return []

    grupos = db.query(Grupo).filter(Grupo.form_id == form_id).all()
    resultado = []
    for grupo in grupos:
        respostas = (
            db.query(Resposta)
            .filter(Resposta.form_id == form_id, Resposta.assigned_group_id == grupo.id)
            .all()
        )
        if not respostas:
            continue
        medias = {}
        for v in variaveis:
            scores = [r.variable_scores.get(v.name, 0) for r in respostas]
            medias[v.name] = round(sum(scores) / len(scores), 1)
        resultado.append(MediaGrupo(nome=grupo.name, scores_medios=medias))

    return resultado


def listar_respondentes(db: Session, form_id: uuid.UUID) -> list[ItemRespondente]:
    respostas = (
        db.query(Resposta)
        .filter(Resposta.form_id == form_id)
        .order_by(Resposta.submitted_at.desc())
        .all()
    )
    grupos = {
        str(g.id): g.name
        for g in db.query(Grupo).filter(Grupo.form_id == form_id).all()
    }
    resultado = []
    for r in respostas:
        grupo_nome = grupos.get(str(r.assigned_group_id)) if r.assigned_group_id else None
        resultado.append(
            ItemRespondente(
                response_id=r.id,
                nome=r.respondent_name or "Anônimo",
                email=r.respondent_email,
                grupo=grupo_nome,
                data=r.submitted_at,
            )
        )
    return resultado


def buscar_detalhe_resposta(db: Session, response_id: uuid.UUID) -> dict | None:
    resposta = db.get(Resposta, response_id)
    if not resposta:
        return None

    formulario = db.get(Formulario, resposta.form_id)
    if not formulario:
        return None

    perguntas = (
        db.query(Pergunta)
        .filter(Pergunta.form_id == resposta.form_id)
        .order_by(Pergunta.order)
        .all()
    )
    grupo = db.get(Grupo, resposta.assigned_group_id) if resposta.assigned_group_id else None
    variaveis = db.query(Variavel).filter(Variavel.form_id == resposta.form_id).all()

    respostas_formatadas = []
    for p in perguntas:
        valor = resposta.answers.get(str(p.id))
        if valor is None:
            formatado = "—"
        elif isinstance(valor, list):
            formatado = ", ".join(str(v) for v in valor) if valor else "—"
        else:
            formatado = str(valor)
        respostas_formatadas.append({"texto": p.text, "valor": formatado})

    nomes_variaveis = [v.name for v in variaveis]
    radar_dados = [resposta.variable_scores.get(n, 0) for n in nomes_variaveis]

    return {
        "resposta": resposta,
        "grupo": grupo,
        "respostas_formatadas": respostas_formatadas,
        "tem_variaveis": bool(variaveis),
        "nomes_variaveis": nomes_variaveis,
        "radar_dados": radar_dados,
    }


def buscar_historico_usuario(db: Session, user_id: uuid.UUID, limite: int = 20) -> list[dict]:
    respostas = (
        db.query(Resposta)
        .filter(Resposta.user_id == user_id)
        .order_by(Resposta.submitted_at.desc())
        .limit(limite)
        .all()
    )
    resultado = []
    for r in respostas:
        form = db.get(Formulario, r.form_id)
        grupo = db.get(Grupo, r.assigned_group_id) if r.assigned_group_id else None
        resultado.append({
            "form_id": str(r.form_id),
            "form_title": form.title if form else "Formulário excluído",
            "grupo": grupo.name if grupo else "Sem classificação",
            "data": r.submitted_at,
        })
    return resultado
