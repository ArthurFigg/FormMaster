import uuid
from datetime import datetime

from pydantic import BaseModel


class UsuarioCadastro(BaseModel):
    email: str
    senha: str


class UsuarioLogin(BaseModel):
    email: str
    senha: str


class UsuarioPublico(BaseModel):
    id: uuid.UUID
    email: str
    created_at: datetime

    model_config = {"from_attributes": True}
