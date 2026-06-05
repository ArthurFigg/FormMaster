import uuid

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

import dashboard.servicos as servicos
from auth.orm import Usuario
from auth.servicos import get_usuario_atual
from database import get_db

router = APIRouter()
templates = Jinja2Templates(directory="templates")


@router.get("/formularios/{form_id}/painel/resposta/{response_id}", response_class=HTMLResponse)
def drill_down_resposta(
    form_id: uuid.UUID,
    response_id: uuid.UUID,
    request: Request,
    usuario: Usuario = Depends(get_usuario_atual),
    db: Session = Depends(get_db),
):
    from fastapi import HTTPException
    from formularios.repositorio import buscar_por_id as buscar_form

    formulario = buscar_form(db, form_id)
    if not formulario:
        raise HTTPException(status_code=404)
    if formulario.owner_id != usuario.id:
        raise HTTPException(status_code=403)

    detalhe = servicos.buscar_detalhe_resposta(db, response_id)
    if not detalhe:
        raise HTTPException(status_code=404)

    return templates.TemplateResponse(
        request,
        "dashboard/painel_formulario.html",
        {
            "formulario": formulario,
            "modo_drill": True,
            "detalhe": detalhe,
        },
    )
