# Dashboard do Mestre

## O que faz
Implementa o painel completo do mestre: painel principal com lista de formulários e histórico de respostas, painel do formulário com abas (Respostas com radares, Compartilhar), e drill-down de resposta individual.

## Comportamento

### `GET /dashboard` — Painel principal
- Lista de formulários do mestre com: título, status (badge colorido), data de criação, contagem de respostas
- Histórico de formulários respondidos pelo mestre como respondente: título do formulário, data de submissão, grupo recebido (ou "Sem classificação")
- Botão "Criar formulário" com opções "Com IA" (→ `/formularios/wizard`) e "Manual" (→ `POST /formularios/` direto)
- Formulários listados em ordem decrescente de `created_at`

### `GET /formularios/{id}/painel` — Painel do formulário
**Barra de ações:** abas "Respostas" e "Compartilhar", link "Editar" (→ `/formularios/{id}/editar`), botão "Publicar" (só se `status=draft`), botão "Encerrar" (só se `status=active`) com `confirm()` antes de chamar `POST /formularios/{id}/encerrar`

**Aba Respostas:**
- Contagem de respostas por grupo (incluindo "Sem classificação" para `assigned_group_id=null`)
- Para cada grupo com pelo menos 1 respondente: gráfico radar com a média dos `variable_scores` dos respondentes daquele grupo (Chart.js)
- Quando o formulário não tem variáveis: radares não são renderizados (sem mensagem de erro)
- Lista de todos os respondentes com: nome (ou "Anônimo"), email, grupo recebido, data de submissão, link "Ver detalhes"

**Aba Compartilhar:**
- Link público do formulário (`/r/{form_id}`) em campo de texto com botão "Copiar"

### `GET /formularios/{id}/painel/resposta/{response_id}` — Drill-down individual
- Exibe todas as respostas do respondente (pergunta + resposta formatada por tipo)
- Exibe `variable_scores` do respondente
- Exibe gráfico radar individual com os scores do respondente (oculto se formulário sem variáveis)
- Exibe grupo atribuído (ou "Sem classificação")
- Botão "Voltar" para o painel do formulário

## Critérios verificáveis
- [ ] `GET /dashboard` com autenticação → 200 com lista de formulários do mestre
- [ ] `GET /dashboard` → histórico inclui apenas respostas onde `responses.user_id = current_user.id`
- [ ] `GET /formularios/{id}/painel` → aba Respostas exibe contagem por grupo
- [ ] `GET /formularios/{id}/painel` com formulário sem variáveis → página renderiza sem erro, sem radar
- [ ] `GET /formularios/{id}/painel` com formulário `status=draft` → botão "Publicar" visível, "Encerrar" ausente
- [ ] `GET /formularios/{id}/painel` com formulário `status=active` → botão "Encerrar" visível, "Publicar" ausente
- [ ] `GET /formularios/{id}/painel/resposta/{response_id}` → exibe respostas e grupo
- [ ] Respostas com `assigned_group_id=null` → contadas e listadas como "Sem classificação"
- [ ] `uv run pytest -v` passa

## Módulos afetados
- `dashboard/modelos.py` — criado: `ResumoGrupo(nome, contagem)`, `MediaGrupo(nome, scores_medios)`, `ItemRespondente(nome, email, grupo, data, response_id)`, `DetalheResposta(...)`
- `dashboard/servicos.py` — criado: `agregar_por_grupo(form_id)`, `calcular_medias_por_grupo(form_id)`, `listar_respondentes(form_id)`, `buscar_detalhe_resposta(response_id)`
- `dashboard/rotas.py` — criado: `GET /formularios/{id}/painel/resposta/{response_id}` (os outros endpoints de painel já estão em `formularios/rotas.py`)
- `templates/dashboard/index.html` — substituído: implementação completa do painel principal
- `templates/dashboard/painel_formulario.html` — substituído: implementação completa com abas, radares (Chart.js), lista de respondentes e drill-down
- `formularios/rotas.py` — `GET /formularios/{id}/painel` atualizado para passar dados de agregação ao template (usando `dashboard/servicos.py`)

## Não mexer
- `respostas/motor.py`, `respostas/servicos.py`, `respostas/rotas.py`
- `auth/`, `ia/`
- Templates do respondente e do editor

## Decisões tomadas
- Radares → Chart.js via CDN; um canvas por grupo com dados de média dos `variable_scores`
- Radares individuais (drill-down) → mesma abordagem, dados do respondente específico
- "Sem classificação" → tratado como grupo virtual apenas no frontend; `assigned_group_id=null` no banco
- Drill-down → rota em `dashboard/rotas.py`; painel principal e painel do formulário ficam em `formularios/rotas.py` e chamam serviços de `dashboard/`
- Botão Copiar link → JS nativo `navigator.clipboard.writeText()`
- "Criar formulário" manual → `<form method="post" action="/formularios/">` com submit direto; sem página intermediária
- Respondentes sem nome → exibidos como "Anônimo" no painel
- Histórico no painel principal → limitado às últimas 20 respostas por padrão (sem paginação para MVP)
- Lista de respondentes no painel do formulário → sem paginação para MVP; todos exibidos
