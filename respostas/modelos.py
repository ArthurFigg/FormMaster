from typing import Any, Optional

from pydantic import BaseModel


class SubmissaoResposta(BaseModel):
    respondent_name: Optional[str] = None
    respondent_email: Optional[str] = None
    respondent_phone: Optional[str] = None
    answers: dict[str, Any] = {}
