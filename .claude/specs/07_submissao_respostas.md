# Submissão de Respostas

## O que faz
Implementa o ORM de respostas, o endpoint `POST /r/{form_id}`, todas as validações de submissão (incluindo `block_resubmit`) e a orquestração que chama o motor de regras e persiste o resultado.

## Comportamento
- Quando `POST /r/{form_id}` recebe submissão de formulário `active`: valida dados, executa motor de regras, persiste em `responses`, redireciona para `GET /r/{form_id}/fim`
- Quando `POST /r/{form_id}` recebe formulário com `status=draft` → 404
- Quando `POST /r/{form_id}` recebe formulário com `status=closed` → 403 com `{"detail": "Formulário encerrado."}`
- Quando `block_resubmit=true` e email não foi fornecido → 422
- Quando `block_resubmit=true` e já existe `response` com mesmo `respondent_email + form_id` → 409 com `{"detail": "Você já respondeu este formulário."}`
- Quando o respondente está autenticado (`get_usuario_opcional()`), `user_id` é preenchido na resposta; se anônimo, fica null
- `variable_scores` é o resultado final do motor (variáveis inicializadas com `initial_value` e modificadas pelas regras)
- `assigned_group_id` é o resultado da classificação do motor (pode ser null)
- `answers` armazena as respostas no formato definido no CLAUDE.md: string para `text`/`multiple_choice`, lista de strings para `checkbox`, inteiro para `scale`/`number`
- Quando `GET /r/{form_id}/fim` é acessado com `response_id` válido, renderiza `responder/fim.html` com os dados da resposta
- Quando `GET /r/{form_id}/fim` é acessado sem `response_id` ou com `response_id` inválido/inexistente → renderiza `responder/fim.html` com a mensagem genérica "Obrigado por participar!" (sem grupo, sem scores) — não levanta 404 nem 500; o respondente vê uma tela de encerramento mesmo que o contexto tenha sido perdido

## Critérios verificáveis
- [ ] `POST /r/{form_id}` com formulário `active` e dados válidos → 303 redirect para `/r/{form_id}/fim`
- [ ] Registro criado em `responses` com `answers`, `variable_scores`, `assigned_group_id`, `submitted_at`
- [ ] `POST /r/{form_id}` com `status=draft` → 404
- [ ] `POST /r/{form_id}` com `status=closed` → 403
- [ ] `POST /r/{form_id}` com `block_resubmit=true` sem email → 422
- [ ] `POST /r/{form_id}` com email já registrado e `block_resubmit=true` → 409
- [ ] Resposta com usuário autenticado → `user_id` preenchido no banco
- [ ] `GET /r/{form_id}/fim` sem `response_id` → 200 com mensagem genérica "Obrigado por participar!", sem erro
- [ ] `GET /r/{form_id}/fim` com `response_id` inexistente → 200 com mensagem genérica, sem 404/500
- [ ] `uv run pytest -v` passa

## Módulos afetados
- `respostas/orm.py` — criado: modelo `Resposta` mapeando tabela `responses` com todos os campos do CLAUDE.md
- `respostas/modelos.py` — criado: schema `SubmissaoResposta` para receber o POST (campos pessoais + answers)
- `respostas/repositorio.py` — criado: `buscar_por_form_email()`, `criar_resposta()`
- `respostas/servicos.py` — criado: `processar_submissao()` — orquestra validações, chama `motor.avaliar()`, persiste resultado
- `respostas/rotas.py` — criado: `POST /r/{form_id}`, `GET /r/{form_id}/fim`
- `alembic/versions/` — migration para tabela `responses`
- `alembic/env.py` — import de `respostas.orm` descomentado
- `main.py` — router de respostas registrado

## Não mexer
- `respostas/motor.py` — já implementado; apenas importado por `servicos.py`
- `auth/`, `formularios/`, `dashboard/`, `ia/`
- Templates do respondente (`formulario.html`, `fim.html`) — são criados/expandidos na spec 08; esta spec assume que `fim.html` existe como stub

## Decisões tomadas
- Submissão → via `application/x-www-form-urlencoded` (Form do FastAPI), recebido de `formulario.html`
- Redirect após submissão → `GET /r/{form_id}/fim?response_id={id}` para carregar dados da resposta na tela final
- `GET /r/{form_id}/fim` → busca resposta por `response_id`, carrega grupo e `variable_scores`, passa para `fim.html`
- `block_resubmit` enforcement → verificado em `processar_submissao()` antes de qualquer outra lógica de negócio
- Motor → chamado com dados carregados do banco (regras, thresholds, variáveis do formulário) + `answers` recebidos
- `answers` → deserializado para o tipo correto antes de chamar o motor (checkbox como lista, scale/number como int)
- Formulários `active` sem nenhuma regra nem threshold → motor retorna `(None, {})`, `assigned_group_id=null` é salvo normalmente
