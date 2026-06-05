import json
import uuid

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

import formularios.repositorio as repo
import formularios.servicos as servicos
from auth.orm import Usuario
from auth.servicos import get_usuario_atual, get_usuario_opcional
from database import get_db
from formularios.modelos import PatchFormulario

router = APIRouter()
templates = Jinja2Templates(directory="templates")


@router.get("/", response_class=HTMLResponse)
def raiz(usuario: Usuario | None = Depends(get_usuario_opcional)):
    if usuario:
        return RedirectResponse(url="/dashboard", status_code=303)
    return RedirectResponse(url="/auth/login", status_code=303)


@router.get("/dashboard", response_class=HTMLResponse)
def dashboard(
    request: Request,
    usuario: Usuario = Depends(get_usuario_atual),
    db: Session = Depends(get_db),
):
    from sqlalchemy import func
    from dashboard.servicos import buscar_historico_usuario
    from respostas.orm import Resposta

    formularios_lista = repo.listar_por_dono(db, usuario.id)
    contagens: dict[str, int] = {}
    if formularios_lista:
        form_ids = [f.id for f in formularios_lista]
        rows = (
            db.query(Resposta.form_id, func.count(Resposta.id))
            .filter(Resposta.form_id.in_(form_ids))
            .group_by(Resposta.form_id)
            .all()
        )
        contagens = {str(fid): cnt for fid, cnt in rows}

    historico = buscar_historico_usuario(db, usuario.id)
    return templates.TemplateResponse(
        request,
        "dashboard/index.html",
        {
            "usuario": usuario,
            "formularios": formularios_lista,
            "contagens": contagens,
            "historico": historico,
        },
    )


@router.post("/formularios/")
def criar_formulario(
    usuario: Usuario = Depends(get_usuario_atual),
    db: Session = Depends(get_db),
):
    formulario = servicos.criar_formulario(db, usuario.id)
    return RedirectResponse(url=f"/formularios/{formulario.id}/editar", status_code=303)


@router.get("/formularios/wizard", response_class=HTMLResponse)
def wizard_ia_get(
    request: Request,
    usuario: Usuario = Depends(get_usuario_atual),
):
    return templates.TemplateResponse(request, "wizard_ia/wizard.html")


@router.post("/formularios/wizard")
def wizard_ia_post(
    request: Request,
    objetivo: str = Form(...),
    grupos: list[str] = Form(...),
    criterios: str = Form(...),
    eliminacoes: str = Form(""),
    num_perguntas: int = Form(8),
    usuario: Usuario = Depends(get_usuario_atual),
    db: Session = Depends(get_db),
):
    from ia.construtor_prompt import chamar_gemini, montar_prompt, validar_resposta_ia
    from pydantic import ValidationError

    def re_renderizar(erro: str):
        return templates.TemplateResponse(
            request,
            "wizard_ia/wizard.html",
            {
                "erro": erro,
                "objetivo": objetivo,
                "grupos": grupos,
                "criterios": criterios,
                "eliminacoes": eliminacoes,
                "num_perguntas": num_perguntas,
            },
        )

    if len(grupos) < 2:
        return re_renderizar("É necessário pelo menos 2 grupos.")

    prompt = montar_prompt(objetivo, grupos, criterios, eliminacoes, num_perguntas)

    try:
        dados_brutos = chamar_gemini(prompt)
        dados_ia = validar_resposta_ia(dados_brutos)
    except (ValueError, ValidationError):
        return re_renderizar("Não foi possível gerar o formulário. Tente novamente.")

    formulario = servicos.criar_formulario_de_ia(db, dados_ia, usuario.id, objetivo)
    return RedirectResponse(url=f"/formularios/{formulario.id}/editar", status_code=303)


@router.get("/formularios/{form_id}/editar", response_class=HTMLResponse)
def editar_formulario(
    form_id: uuid.UUID,
    request: Request,
    usuario: Usuario = Depends(get_usuario_atual),
    db: Session = Depends(get_db),
):
    formulario = repo.buscar_por_id(db, form_id)
    if not formulario:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Formulário não encontrado.")
    if formulario.owner_id != usuario.id:
        from fastapi import HTTPException
        raise HTTPException(status_code=403, detail="Acesso negado.")
    dados = repo.formulario_para_dict(formulario)
    return templates.TemplateResponse(
        request,
        "editor/editor.html",
        {"formulario": dados, "formulario_json": json.dumps(dados, indent=2, ensure_ascii=False)},
    )


@router.patch("/formularios/{form_id}")
def patch_formulario(
    form_id: uuid.UUID,
    payload: PatchFormulario,
    usuario: Usuario = Depends(get_usuario_atual),
    db: Session = Depends(get_db),
):
    formulario = servicos.patch_atomico(db, form_id, usuario.id, payload)
    return JSONResponse({"id": str(formulario.id), "status": formulario.status})


@router.post("/formularios/{form_id}/publicar")
def publicar_formulario(
    form_id: uuid.UUID,
    usuario: Usuario = Depends(get_usuario_atual),
    db: Session = Depends(get_db),
):
    servicos.publicar(db, form_id, usuario.id)
    return RedirectResponse(url=f"/formularios/{form_id}/painel", status_code=303)


@router.post("/formularios/{form_id}/encerrar")
def encerrar_formulario(
    form_id: uuid.UUID,
    usuario: Usuario = Depends(get_usuario_atual),
    db: Session = Depends(get_db),
):
    servicos.encerrar(db, form_id, usuario.id)
    return JSONResponse({"status": "closed"})


@router.get("/formularios/{form_id}/painel", response_class=HTMLResponse)
def painel_formulario(
    form_id: uuid.UUID,
    request: Request,
    usuario: Usuario = Depends(get_usuario_atual),
    db: Session = Depends(get_db),
):
    from fastapi import HTTPException
    import dashboard.servicos as dash_servicos

    formulario = repo.buscar_por_id(db, form_id)
    if not formulario:
        raise HTTPException(status_code=404, detail="Formulário não encontrado.")
    if formulario.owner_id != usuario.id:
        raise HTTPException(status_code=403, detail="Acesso negado.")

    resumos_grupos = dash_servicos.agregar_por_grupo(db, form_id)
    medias_grupos = dash_servicos.calcular_medias_por_grupo(db, form_id)
    respondentes = dash_servicos.listar_respondentes(db, form_id)
    nomes_variaveis = [v.name for v in formulario.variaveis]
    radar_por_grupo = [
        {"nome": mg.nome, "dados": [round(mg.scores_medios.get(n, 0), 1) for n in nomes_variaveis]}
        for mg in medias_grupos
    ]

    return templates.TemplateResponse(
        request,
        "dashboard/painel_formulario.html",
        {
            "formulario": formulario,
            "resumos_grupos": resumos_grupos,
            "respondentes": respondentes,
            "tem_variaveis": bool(nomes_variaveis),
            "nomes_variaveis": nomes_variaveis,
            "radar_por_grupo": radar_por_grupo,
            "modo_drill": False,
        },
    )
