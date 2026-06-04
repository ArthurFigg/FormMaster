import uuid
from typing import Any, Optional, Union

from pydantic import BaseModel


class CondicaoSchema(BaseModel):
    field: str  # UUID da pergunta (ou nome conceitual para formulários da IA)
    operator: str  # eq / neq / gte / lte / gt / lt
    value: Union[str, int]


class PerguntaSchema(BaseModel):
    id: Optional[uuid.UUID] = None
    order: int = 0
    text: str
    type: str  # text / multiple_choice / checkbox / scale / number
    options: Optional[Any] = None  # lista de strings ou {"min": N, "max": N} para scale
    required: bool = False


class GrupoSchema(BaseModel):
    id: Optional[uuid.UUID] = None
    name: str
    finish_message: Optional[str] = None


class VariavelSchema(BaseModel):
    id: Optional[uuid.UUID] = None
    name: str
    initial_value: int = 0


class RegraSchema(BaseModel):
    id: Optional[uuid.UUID] = None
    order: int
    conditions: list[CondicaoSchema]
    logical_operator: str  # AND / OR
    action_type: str  # assign_group / add_score / subtract_score
    action_target: str  # UUID do grupo ou variável
    action_value: Optional[int] = None


class ThresholdSchema(BaseModel):
    id: Optional[uuid.UUID] = None
    group_id: uuid.UUID
    variable_id: uuid.UUID
    operator: str  # gte / lte / eq / gt / lt
    value: int
    order: int


class PatchFormulario(BaseModel):
    title: str
    collect_name: bool = False
    collect_email: bool = False
    collect_phone: bool = False
    name_required: bool = False
    email_required: bool = False
    phone_required: bool = False
    block_resubmit: bool = False
    finish_mode: str = "generic"
    questions: list[PerguntaSchema] = []
    groups: list[GrupoSchema] = []
    variables: list[VariavelSchema] = []
    rules: list[RegraSchema] = []
    thresholds: list[ThresholdSchema] = []
