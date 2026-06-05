import uuid
from datetime import datetime, timedelta, timezone

import bcrypt
from fastapi import Cookie, Depends, HTTPException
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from auth.orm import Usuario
from config import configuracoes
from database import get_db

_ALGORITMO = "HS256"
_EXPIRACAO_DIAS = 7


def gerar_token(usuario_id: uuid.UUID) -> str:
    expiracao = datetime.now(timezone.utc) + timedelta(days=_EXPIRACAO_DIAS)
    return jwt.encode(
        {"sub": str(usuario_id), "exp": expiracao},
        configuracoes.JWT_SECRET,
        algorithm=_ALGORITMO,
    )


def verificar_token(token: str) -> uuid.UUID:
    try:
        payload = jwt.decode(token, configuracoes.JWT_SECRET, algorithms=[_ALGORITMO])
        return uuid.UUID(payload["sub"])
    except (JWTError, KeyError, ValueError):
        raise HTTPException(status_code=401, detail="Token inválido ou expirado.")


def hash_senha(senha: str) -> str:
    return bcrypt.hashpw(senha.encode(), bcrypt.gensalt()).decode()


def verificar_senha(senha: str, hash_: str) -> bool:
    return bcrypt.checkpw(senha.encode(), hash_.encode())


def get_usuario_atual(
    access_token: str | None = Cookie(default=None),
    db: Session = Depends(get_db),
) -> Usuario:
    if not access_token:
        raise HTTPException(status_code=401, detail="Não autenticado.")
    usuario_id = verificar_token(access_token)
    usuario = db.get(Usuario, usuario_id)
    if not usuario:
        raise HTTPException(status_code=401, detail="Usuário não encontrado.")
    return usuario


def get_usuario_opcional(
    access_token: str | None = Cookie(default=None),
    db: Session = Depends(get_db),
) -> Usuario | None:
    if not access_token:
        return None
    try:
        usuario_id = verificar_token(access_token)
    except HTTPException:
        return None
    return db.get(Usuario, usuario_id)
