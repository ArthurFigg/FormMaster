import uuid

from fastapi import APIRouter, Depends, Form, Request, Response
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from auth.orm import Usuario
from auth.servicos import gerar_token, hash_senha, verificar_senha
from config import configuracoes
from database import get_db

router = APIRouter(prefix="/auth", tags=["auth"])
templates = Jinja2Templates(directory="templates")


@router.get("/login", response_class=HTMLResponse)
def pagina_login(request: Request):
    return templates.TemplateResponse(request, "auth/login.html")


@router.get("/cadastro", response_class=HTMLResponse)
def pagina_cadastro(request: Request):
    return templates.TemplateResponse(request, "auth/cadastro.html")


@router.post("/cadastro")
def cadastrar(
    request: Request,
    email: str = Form(...),
    senha: str = Form(...),
    db: Session = Depends(get_db),
):
    existente = db.query(Usuario).filter(Usuario.email == email).first()
    if existente:
        return templates.TemplateResponse(
            request, "auth/cadastro.html", {"erro": "E-mail já cadastrado."}
        )

    usuario = Usuario(email=email, password_hash=hash_senha(senha))
    db.add(usuario)
    db.flush()

    _vincular_respostas(db, usuario.id, email)
    db.commit()

    resposta = RedirectResponse(url="/dashboard", status_code=303)
    _emitir_cookie(resposta, usuario.id)
    return resposta


@router.post("/login")
def login(
    request: Request,
    email: str = Form(...),
    senha: str = Form(...),
    db: Session = Depends(get_db),
):
    usuario = db.query(Usuario).filter(Usuario.email == email).first()
    if not usuario or not verificar_senha(senha, usuario.password_hash):
        return templates.TemplateResponse(
            request, "auth/login.html", {"erro": "E-mail ou senha incorretos."}
        )

    _vincular_respostas(db, usuario.id, email)
    db.commit()

    resposta = RedirectResponse(url="/dashboard", status_code=303)
    _emitir_cookie(resposta, usuario.id)
    return resposta


@router.post("/logout")
def logout():
    resposta = RedirectResponse(url="/auth/login", status_code=303)
    resposta.delete_cookie("access_token")
    return resposta


def _emitir_cookie(resposta: Response, usuario_id: uuid.UUID) -> None:
    resposta.set_cookie(
        key="access_token",
        value=gerar_token(usuario_id),
        httponly=True,
        samesite="lax",
        secure=not configuracoes.DEBUG,
    )


def _vincular_respostas(db: Session, usuario_id: uuid.UUID, email: str) -> None:
    # respostas.orm criado na spec 07; sem efeito até lá
    try:
        from respostas.orm import Resposta
    except ImportError:
        return
    db.query(Resposta).filter(
        Resposta.respondent_email == email,
        Resposta.user_id.is_(None),
    ).update({"user_id": usuario_id})
