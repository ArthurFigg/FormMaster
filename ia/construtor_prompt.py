import json
import re
from typing import Optional, Union

from google import genai
from pydantic import BaseModel, ValidationError

from config import configuracoes

_MODELO = "gemini-2.0-flash"


class _PerguntaIA(BaseModel):
    text: str
    type: str
    options: Optional[Union[list, dict]] = None
    required: bool = True


class _GrupoIA(BaseModel):
    name: str


class _VariavelIA(BaseModel):
    name: str
    initial_value: int = 0


class _CondicaoIA(BaseModel):
    field: str
    operator: str
    value: Union[str, int]


class _RegraIA(BaseModel):
    order: int
    conditions: list[_CondicaoIA]
    logical_operator: str = "AND"
    action_type: str
    action_target: str
    action_value: Optional[int] = None


class _ThresholdIA(BaseModel):
    group: str
    variable: str
    operator: str
    value: int


class RespostaIA(BaseModel):
    questions: list[_PerguntaIA]
    variables: list[_VariavelIA] = []
    groups: list[_GrupoIA]
    rules: list[_RegraIA] = []
    group_thresholds: list[_ThresholdIA] = []


def montar_prompt(
    objetivo: str,
    grupos: list[str],
    criterios: str,
    eliminacoes: str,
    num_perguntas: int,
) -> str:
    grupos_str = ", ".join(f'"{g}"' for g in grupos)
    prompt = f"""Você é um assistente que cria formulários de triagem. Retorne APENAS JSON válido, sem nenhum texto fora do JSON.

Objetivo do formulário: {objetivo}

Grupos de classificação (do mais positivo ao menos positivo): {grupos_str}

Critérios de avaliação: {criterios}
"""
    if eliminacoes.strip():
        prompt += f"\nCondições de eliminação direta: {eliminacoes}\n"

    prompt += f"""
Gere aproximadamente {num_perguntas} perguntas.

Retorne um JSON com exatamente esta estrutura:
{{
  "questions": [
    {{
      "text": "texto da pergunta",
      "type": "multiple_choice",
      "options": ["opcao1", "opcao2"],
      "required": true
    }}
  ],
  "variables": [
    {{"name": "nome_variavel", "initial_value": 0}}
  ],
  "groups": [
    {{"name": "nome_grupo"}}
  ],
  "rules": [
    {{
      "order": 1,
      "conditions": [{{"field": "nome_conceitual", "operator": "eq", "value": "valor"}}],
      "logical_operator": "AND",
      "action_type": "assign_group",
      "action_target": "nome_grupo",
      "action_value": null
    }}
  ],
  "group_thresholds": [
    {{"group": "nome_grupo", "variable": "nome_variavel", "operator": "gte", "value": 40}}
  ]
}}

Regras obrigatórias:
- Tipos de pergunta válidos: text, multiple_choice, checkbox, scale, number
- Para scale, options deve ser {{"min": 1, "max": 10}}
- Operadores em rules: eq, neq para text/multiple_choice/checkbox; eq, neq, gte, lte, gt, lt para scale/number
- action_type válidos: assign_group, add_score, subtract_score
- action_value: null quando action_type=assign_group; inteiro positivo para add_score/subtract_score
- Operadores em group_thresholds: gte, lte, eq, gt, lt
- Use nomes conceituais em português para field, action_target e group/variable em thresholds
- Os grupos no JSON devem ser exatamente: {grupos_str}
"""
    return prompt


def chamar_gemini(prompt: str) -> dict:
    try:
        cliente = genai.Client(api_key=configuracoes.GEMINI_API_KEY)
        resposta = cliente.models.generate_content(model=_MODELO, contents=prompt)
        texto = resposta.text.strip()
        # Remove blocos de código se o modelo os incluir
        texto = re.sub(r"^```(?:json)?\s*", "", texto, flags=re.MULTILINE)
        texto = re.sub(r"\s*```$", "", texto, flags=re.MULTILINE)
        return json.loads(texto)
    except Exception as e:
        raise ValueError(f"Falha ao chamar Gemini: {e}") from e


def validar_resposta_ia(dados: dict) -> RespostaIA:
    return RespostaIA.model_validate(dados)
