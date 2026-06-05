import uuid
from typing import Annotated, Any, Optional

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

import respostas.repositorio as repo
from auth.orm import Usuario
from auth.servicos import get_usuario_opcional
from database import get_db
from formularios.repositorio import buscar_por_id as buscar_formulario
from respostas.servicos import processar_submissao

router = APIRouter()
templates = Jinja2Templates(directory="templates")


@router.get("/r/{form_id}", response_class=HTMLResponse)
def exibir_formulario(
    form_id: uuid.UUID,
    request: Request,
    usuario: Optional[Usuario] = Depends(get_usuario_opcional),
    db: Session = Depends(get_db),
):
    from fastapi import HTTPException

    formulario = buscar_formulario(db, form_id)
    if not formulario or formulario.status == 'draft':
        raise HTTPException(status_code=404)
    if formulario.status == 'closed':
        return templates.TemplateResponse(
            "responder/encerrado.html", {"request": request}
        )
    return templates.TemplateResponse(
        "responder/formulario.html",
        {"request": request, "formulario": formulario, "usuario": usuario},
    )


@router.post("/r/{form_id}")
async def receber_submissao(
    form_id: uuid.UUID,
    request: Request,
    usuario: Optional[Usuario] = Depends(get_usuario_opcional),
    db: Session = Depends(get_db),
):
    from fastapi import HTTPException

    formulario = buscar_formulario(db, form_id)
    if not formulario or formulario.status == 'draft':
        raise HTTPException(status_code=404)

    form_data = await request.form()

    respondent_name = form_data.get("respondent_name") or None
    respondent_email = form_data.get("respondent_email") or None
    respondent_phone = form_data.get("respondent_phone") or None

    # Monta answers: múltiplos valores para o mesmo campo → lista (checkbox)
    answers_raw: dict[str, Any] = {}
    for key, value in form_data.multi_items():
        if key.startswith("answer_"):
            qid = key[len("answer_"):]
            if qid in answers_raw:
                existing = answers_raw[qid]
                if isinstance(existing, list):
                    existing.append(value)
                else:
                    answers_raw[qid] = [existing, value]
            else:
                answers_raw[qid] = value

    resposta = processar_submissao(
        db=db,
        formulario=formulario,
        respondent_name=respondent_name,
        respondent_email=respondent_email,
        respondent_phone=respondent_phone,
        answers_raw=answers_raw,
        user_id=usuario.id if usuario else None,
    )

    return RedirectResponse(
        url=f"/r/{form_id}/fim?response_id={resposta.id}",
        status_code=303,
    )


@router.get("/r/{form_id}/fim", response_class=HTMLResponse)
def tela_fim(
    form_id: uuid.UUID,
    request: Request,
    response_id: Optional[uuid.UUID] = None,
    db: Session = Depends(get_db),
):
    formulario = buscar_formulario(db, form_id)
    resposta = None
    grupo = None

    if response_id:
        resposta = repo.buscar_por_id(db, response_id)
        if resposta and resposta.assigned_group_id and formulario:
            from formularios.orm import Grupo
            grupo = db.get(Grupo, resposta.assigned_group_id)

    return templates.TemplateResponse(
        "responder/fim.html",
        {
            "request": request,
            "formulario": formulario,
            "resposta": resposta,
            "grupo": grupo,
        },
    )
