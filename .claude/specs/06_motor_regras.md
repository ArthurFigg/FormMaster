# Motor de Regras

## O que faz
Implementa `respostas/motor.py` com toda a lógica de avaliação de regras e classificação de respondentes, e `tests/respostas/test_motor.py` com cobertura completa dos cenários definidos no CLAUDE.md.

## Comportamento
- Quando `avaliar(formulario, respostas)` é chamado, executa a sequência completa de avaliação e retorna `(grupo_id | None, variable_scores)`
- **Passo 1 — Inicialização:** todas as variáveis inicializadas com `initial_value`
- **Passo 2 — Regras em ordem:** avalia cada regra pelo campo `order` (crescente)
  - Condições avaliadas com `logical_operator` AND/OR
  - Se condição satisfeita e `action_type = assign_group` → atribui `grupo_id` e interrompe toda avaliação (eliminação direta)
  - Se condição satisfeita e `action_type = add_score` → `variável += action_value`; continua
  - Se condição satisfeita e `action_type = subtract_score` → `variável -= action_value`; continua
- **Passo 3 — Thresholds:** agrupa por `group_id`, ordena grupos pelo `order` comum (crescente); para cada grupo, verifica se TODOS os thresholds são satisfeitos; o primeiro grupo cujos thresholds todos passarem é atribuído; avaliação para
- **Passo 4 — Fallback:** se nenhum grupo foi atribuído, retorna `None`
- **Operadores por tipo:**
  - `text`, `multiple_choice`: `eq` (igualdade de string), `neq` (diferença de string)
  - `checkbox`: `eq` (valor contido na lista), `neq` (valor ausente da lista)
  - `scale`, `number`: `eq`, `neq`, `gte`, `lte`, `gt`, `lt` (comparação numérica)
- O motor não acessa banco de dados — recebe dados já carregados como structs/dicts

## Critérios verificáveis
- [ ] `uv run pytest tests/respostas/test_motor.py -v` passa com todos os testes abaixo presentes e verdes:
  - [ ] `test_assign_group_para_avaliacao` — regra `assign_group` retorna grupo e interrompe restantes
  - [ ] `test_add_score_acumula` — múltiplas regras `add_score` acumulam corretamente
  - [ ] `test_subtract_score_decrementa` — `subtract_score` aplica decremento
  - [ ] `test_regras_avaliadas_em_ordem` — regras com `order` menor têm prioridade
  - [ ] `test_threshold_grupo_prioritario_vence` — grupo com menor `order` é atribuído quando todos os thresholds passam
  - [ ] `test_threshold_todos_devem_passar` — grupo com threshold falhando não é atribuído
  - [ ] `test_fallback_none` — sem regras nem thresholds → retorna `None`
  - [ ] `test_operador_eq_text` — `eq` em `multiple_choice` compara strings
  - [ ] `test_operador_neq_text` — `neq` em `multiple_choice` compara strings
  - [ ] `test_operador_eq_checkbox` — `eq` verifica presença na lista
  - [ ] `test_operador_neq_checkbox` — `neq` verifica ausência da lista
  - [ ] `test_operador_gte_scale` — comparação numérica ≥
  - [ ] `test_operador_lte_scale` — comparação numérica ≤
  - [ ] `test_operador_gt_number` — comparação numérica >
  - [ ] `test_operador_lt_number` — comparação numérica <
  - [ ] `test_condicoes_and_todas_devem_passar` — AND: todas as condições precisam ser verdadeiras
  - [ ] `test_condicoes_or_uma_basta` — OR: basta uma condição verdadeira

## Módulos afetados
- `respostas/motor.py` — criado: função pública `avaliar(regras, thresholds, variaveis, respostas) -> tuple[UUID | None, dict]`; funções privadas de avaliação de condição e threshold
- `tests/respostas/__init__.py` — criado vazio
- `tests/respostas/test_motor.py` — criado com todos os cenários listados nos critérios

## Não mexer
- Todos os outros módulos
- `respostas/orm.py`, `respostas/servicos.py`, `respostas/repositorio.py` — ainda não existem; serão criados na spec 07
- Banco de dados — o motor é pura lógica Python, sem I/O

## Decisões tomadas
- Interface do motor → `avaliar(regras, thresholds, variaveis, respostas)` recebe listas de dicts (ou dataclasses) já carregadas; sem acesso a banco
- Retorno → `tuple[UUID | None, dict[str, int]]` onde o primeiro elemento é o `assigned_group_id` e o segundo é o `variable_scores` final
- `action_value` → sempre inteiro positivo no banco; o motor aplica `+=` para `add_score` e `-=` para `subtract_score` conforme CLAUDE.md
- Comparação de tipos → sem cast: strings comparadas como string, inteiros como int, conforme tipo do `conditions[].value` no JSONB
- Testes → sem fixtures de banco, apenas dicts Python; testes puramente unitários

---
**Status:** concluida em 2026-06-05
