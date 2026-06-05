# CRUD de Formulários

## O que faz
Implementa todos os modelos ORM do domínio de formulários, o repositório, os serviços e os endpoints de criação, listagem, edição atômica, publicação e encerramento — incluindo as rotas de navegação do mestre.

## Comportamento
- Quando `GET /` é acessado sem autenticação, redireciona para `/auth/login`
- Quando `GET /` é acessado com autenticação, redireciona para `/dashboard`
- Quando `GET /dashboard` é acessado com autenticação, renderiza `dashboard/index.html` com: lista de formulários do mestre (id, title, status, created_at) e histórico de formulários respondidos (`responses.user_id = current_user.id`)
- Quando `POST /formularios/` é chamado com JWT válido, cria formulário com todos os defaults definidos no CLAUDE.md e redireciona para `GET /formularios/{id}/editar`
- Quando `GET /formularios/{id}/editar` é chamado pelo dono, renderiza `editor/editor.html` com dados completos do formulário (perguntas, grupos, variáveis, regras, thresholds)
- Quando `GET /formularios/{id}/editar` é chamado por outro usuário, retorna 403
- Quando `PATCH /formularios/{id}` recebe payload completo: itens sem UUID são criados, itens com UUID são atualizados, UUIDs presentes no banco mas ausentes no payload são deletados — tudo em transação única e atômica; `status` nunca é alterado pelo PATCH
- Quando `PATCH /formularios/{id}` recebe `block_resubmit=true` com `collect_email=false`, retorna 422
- Quando `POST /formularios/{id}/publicar` é chamado pelo dono com status `draft`, muda status para `active` e redireciona para `GET /formularios/{id}/painel`
- Quando `POST /formularios/{id}/publicar` é chamado com status `active` → 400 `{"detail": "Formulário já está publicado."}`
- Quando `POST /formularios/{id}/publicar` é chamado com status `closed` → 400 `{"detail": "Formulário encerrado não pode ser republicado."}`
- Quando `POST /formularios/{id}/encerrar` é chamado pelo dono com status `active`, muda status para `closed`
- Quando `POST /formularios/{id}/encerrar` é chamado com status `draft` → 400 `{"detail": "Formulário em rascunho não pode ser encerrado."}`
- Quando `POST /formularios/{id}/encerrar` é chamado com status `closed` → 400 `{"detail": "Formulário já está encerrado."}`
- Quando `GET /formularios/{id}/painel` é chamado pelo dono, renderiza `dashboard/painel_formulario.html` com dados do formulário (qualquer status)
- Formulários de outros donos retornam 403 em todos os endpoints acima

## Critérios verificáveis
- [ ] `POST /formularios/` com JWT válido → 303 redirect para `/formularios/{id}/editar`
- [ ] Formulário criado: `status=draft`, `collect_name=false`, `collect_email=false`, `collect_phone=false`, `finish_mode=generic`, `block_resubmit=false`
- [ ] `PATCH /formularios/{id}` enviando pergunta sem UUID → pergunta existe no banco após PATCH
- [ ] `PATCH /formularios/{id}` omitindo pergunta com UUID existente → pergunta deletada do banco após PATCH
- [ ] `PATCH /formularios/{id}` com `block_resubmit=true, collect_email=false` → 422
- [ ] `PATCH /formularios/{id}` com `status` no payload → `status` ignorado, não alterado
- [ ] `POST /formularios/{id}/publicar` → status vira `active`
- [ ] `POST /formularios/{id}/publicar` em formulário `active` → 400
- [ ] `POST /formularios/{id}/publicar` em formulário `closed` → 400
- [ ] `POST /formularios/{id}/encerrar` → status vira `closed`
- [ ] `POST /formularios/{id}/encerrar` em formulário `draft` → 400
- [ ] `POST /formularios/{id}/encerrar` em formulário `closed` → 400
- [ ] `GET /formularios/{id}/editar` por não-dono → 403
- [ ] `uv run pytest -v` passa

## Módulos afetados
- `formularios/orm.py` — criado: `Formulario`, `Pergunta`, `Grupo`, `Variavel`, `Regra`, `GrupoThreshold` com todos os campos do CLAUDE.md
- `formularios/modelos.py` — criado: schemas Pydantic `FormularioBase`, `PerguntaSchema`, `GrupoSchema`, `VariavelSchema`, `RegraSchema`, `ThresholdSchema`, `PatchFormulario` (payload completo do PATCH)
- `formularios/repositorio.py` — criado: `buscar_por_id()`, `listar_por_dono()`, `reconciliar_perguntas()`, `reconciliar_grupos()`, `reconciliar_variaveis()`, `reconciliar_regras()`, `reconciliar_thresholds()`
- `formularios/servicos.py` — criado: `criar_formulario()`, `patch_atomico()`, `publicar()`, `encerrar()`
- `formularios/rotas.py` — criado: `GET /`, `GET /dashboard`, `POST /formularios/`, `GET /formularios/{id}/editar`, `PATCH /formularios/{id}`, `POST /formularios/{id}/publicar`, `POST /formularios/{id}/encerrar`, `GET /formularios/{id}/painel`
- `templates/dashboard/index.html` — criado: stub com lista de formulários e histórico (layout básico funcional)
- `templates/dashboard/painel_formulario.html` — criado: stub com título do formulário e status (será expandido na spec 09_dashboard)
- `templates/editor/editor.html` — criado: stub exibindo dados brutos do formulário em JSON (será substituído na spec 05_editor_frontend)
- `alembic/versions/` — migration para tabelas `forms`, `questions`, `groups`, `variables`, `rules`, `group_thresholds`
- `alembic/env.py` — import de `formularios.orm` descomentado
- `main.py` — router de formulários registrado

## Não mexer
- `auth/` — já implementado
- `respostas/`, `ia/`
- `database.py`, `config.py`

## Decisões tomadas
- PATCH atômico → reconciliação por UUID dentro de transação SQLAlchemy; sem UUID = INSERT, com UUID = UPDATE, ausente = DELETE em cascata
- `status` → nunca alterado pelo PATCH; somente por `/publicar` e `/encerrar`
- Validação `block_resubmit + collect_email=false` → 422 no PATCH, conforme CLAUDE.md
- `editor.html` nesta spec → stub JSON para permitir verificação do backend; substituído na spec 05
- `painel_formulario.html` nesta spec → stub básico; expandido na spec 09
- Templates de dashboard nesta spec → stubs funcionais para navegação; expandidos na spec 09
- Rotas de dashboard (`GET /`, `GET /dashboard`, `GET /formularios/{id}/painel`) ficam em `formularios/rotas.py` — o domínio de dashboard tem serviços de agregação (spec 09), não rotas próprias de navegação

---
**Status:** concluida em 2026-06-05
