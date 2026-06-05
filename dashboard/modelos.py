import uuid
from dataclasses import dataclass
from datetime import datetime


@dataclass
class ResumoGrupo:
    nome: str
    contagem: int


@dataclass
class MediaGrupo:
    nome: str
    scores_medios: dict[str, float]


@dataclass
class ItemRespondente:
    response_id: uuid.UUID
    nome: str
    email: str | None
    grupo: str | None
    data: datetime | None
