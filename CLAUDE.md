# FormMaster

## O que é
Plataforma web onde qualquer pessoa cria formulários personalizados com lógica de triagem automática. O mestre descreve o objetivo, a IA sugere perguntas e regras de classificação, ele edita e publica. Respondentes acessam por link público. O mestre acompanha resultados em painel com gráficos e drill-down individual.

---

## Stack

| Camada | Tecnologia |
|---|---|
| Backend | FastAPI + PostgreSQL |
| Autenticação | JWT (python-jose) armazenado em cookie httponly |
| IA | Gemini Flash API (google-genai) |
| Frontend | HTML + CSS + JS puro (Jinja2 via FastAPI) |
| Gráficos | Chart.js (radar) |
| Deploy | Railway ou Render |
| Testes | pytest |
| Gerenciador de pacotes | uv (pyproject.toml — sem requirements.txt) |

---

## Estrutura de pastas

```
formmaster/
├── alembic/                         # migrations Alembic (gerado por alembic init)
│   ├── env.py
│   └── versions/
├── alembic.ini                      # configuração do Alembic (na raiz do projeto)
├── main.py                          # entrypoint FastAPI — registra routers e middleware
├── config.py                        # Pydantic BaseSettings — lê variáveis do .env
├── database.py                      # conexão PostgreSQL (pool de conexões)
├── auth/
│   ├── __init__.py
│   ├── modelos.py                   # schemas Pydantic de autenticação
│   ├── orm.py                       # modelos SQLAlchemy — tabela users
│   ├── servicos.py                  # lógica JWT — geração, verificação, get_usuario_atual(), get_usuario_opcional()
│   └── rotas.py                     # endpoints: cadastro e login
├── formularios/
│   ├── __init__.py
│   ├── modelos.py                   # schemas Pydantic de formulários, perguntas, grupos, variáveis, regras
│   ├── orm.py                       # modelos SQLAlchemy — tabelas forms, questions, groups, variables, rules, group_thresholds
│   ├── servicos.py                  # lógica de criação, edição, publicação, encerramento
│   ├── repositorio.py               # queries ao banco
│   └── rotas.py                     # endpoints de formulários (inclui /publicar e /encerrar dedicados)
├── respostas/
│   ├── __init__.py
│   ├── modelos.py                   # schemas Pydantic de submissão e resultado
│   ├── orm.py                       # modelos SQLAlchemy — tabela responses
│   ├── motor.py                     # motor de regras — avaliação e classificação
│   ├── servicos.py                  # orquestração da submissão
│   ├── repositorio.py               # queries ao banco
│   └── rotas.py                     # endpoints de submissão de respostas
├── dashboard/
│   ├── __init__.py
│   ├── modelos.py                   # schemas de análise e drill-down
│   ├── servicos.py                  # agregações, contagens por grupo, scores médios
│   └── rotas.py                     # endpoints do painel do mestre
├── ia/
│   ├── __init__.py
│   └── construtor_prompt.py         # monta prompt estruturado e chama Gemini Flash
├── templates/                       # HTML Jinja2
│   ├── auth/
│   │   ├── login.html
│   │   └── cadastro.html
│   ├── dashboard/
│   │   ├── index.html               # painel principal do mestre
│   │   └── painel_formulario.html   # painel do formulário específico (abas)
│   ├── editor/
│   │   └── editor.html              # editor de formulário
│   ├── wizard_ia/
│   │   └── wizard.html              # formulário guiado antes de chamar a IA
│   └── responder/
│       ├── formulario.html          # página do respondente
│       ├── fim.html                 # tela final do respondente
│       └── encerrado.html           # página exibida quando o formulário está closed
├── static/
│   ├── css/
│   └── js/
├── pyproject.toml                   # dependências e configuração do projeto (uv)
├── .env                             # variáveis de ambiente (nunca commitar)
├── .env.example                     # template com todas as variáveis necessárias (sem valores reais)
└── tests/
    └── respostas/
        └── test_motor.py            # testes do motor de regras
```

---

## Modelo de dados

### users
| campo | tipo | descrição |
|---|---|---|
| id | UUID | chave primária |
| email | varchar | único, obrigatório |
| password_hash | varchar | hash bcrypt |
| created_at | timestamp | |

### forms
| campo | tipo | descrição |
|---|---|---|
| id | UUID | chave primária |
| owner_id | UUID | FK → users |
| title | varchar | nome do formulário |
| status | enum | draft / active / closed |
| block_resubmit | boolean | bloquear reenvio por email |
| collect_name | boolean | exibir campo nome para o respondente |
| collect_email | boolean | exibir campo email para o respondente |
| collect_phone | boolean | exibir campo telefone para o respondente |
| name_required | boolean | campo nome obrigatório (relevante apenas se collect_name=true) |
| email_required | boolean | campo email obrigatório (relevante apenas se collect_email=true; forçado true quando block_resubmit=true) |
| phone_required | boolean | campo telefone obrigatório (relevante apenas se collect_phone=true) |
| finish_mode | enum | generic / custom / show_group |
| created_at | timestamp | |

### questions
| campo | tipo | descrição |
|---|---|---|
| id | UUID | chave primária |
| form_id | UUID | FK → forms |
| order | integer | ordem de exibição |
| text | varchar | enunciado |
| type | enum | text / multiple_choice / checkbox / scale / number |
| options | jsonb | opções (para multiple_choice e checkbox: lista de strings; para scale: `{"min": 1, "max": 10}`) |
| required | boolean | |

### groups
| campo | tipo | descrição |
|---|---|---|
| id | UUID | chave primária |
| form_id | UUID | FK → forms |
| name | varchar | ex: "aprovado", "potencial", "rejeitado" |
| finish_message | text | mensagem final personalizada (opcional) |

### variables
| campo | tipo | descrição |
|---|---|---|
| id | UUID | chave primária |
| form_id | UUID | FK → forms |
| name | varchar | ex: "comprometimento", "conhecimento" |
| initial_value | integer | padrão 0 |

### rules
| campo | tipo | descrição |
|---|---|---|
| id | UUID | chave primária |
| form_id | UUID | FK → forms |
| order | integer | ordem de avaliação |
| conditions | jsonb | lista de condições |
| logical_operator | enum | AND / OR |
| action_type | enum | assign_group / add_score / subtract_score |
| action_target | varchar | UUID do grupo ou da variável — mapeado de nome para UUID no save do editor, mesmo processo de conditions[].field |
| action_value | integer (nullable) | valor a somar/subtrair (quando score); null quando action_type = assign_group |

### group_thresholds
| campo | tipo | descrição |
|---|---|---|
| id | UUID | chave primária |
| group_id | UUID | FK → groups |
| variable_id | UUID | FK → variables |
| operator | enum | gte / lte / eq / gt / lt |
| value | integer | threshold |
| order | integer | prioridade do **grupo** — todos os thresholds de um mesmo grupo compartilham o mesmo valor; o motor agrupa por `group_id`, ordena pelo `order` comum e testa o grupo inteiro de uma vez; o primeiro grupo que qualificar (menor `order`) vence |

### responses
| campo | tipo | descrição |
|---|---|---|
| id | UUID | chave primária |
| form_id | UUID | FK → forms |
| user_id | UUID | FK → users (nullable — respondente sem conta) |
| respondent_name | varchar | nullable |
| respondent_email | varchar | nullable |
| respondent_phone | varchar | nullable |
| assigned_group_id | UUID | FK → groups (nullable — quando nenhuma regra ou threshold classifica o respondente) |
| variable_scores | jsonb | ex: {"comprometimento": 40, "conhecimento": 15} |
| answers | jsonb | ex: `{"uuid-text": "resposta livre", "uuid-checkbox": ["opcao1", "opcao3"], "uuid-scale": 7}` — valor é string para text/multiple_choice, lista de strings para checkbox, inteiro para scale/number |
| submitted_at | timestamp | |

---

## Fluxos principais

### Fluxo do mestre

1. **Cadastro/login** → JWT gerado e armazenado em cookie httponly
2. **Painel principal** → lista de formulários criados + histórico de formulários respondidos
3. **Criar formulário** → escolhe entre IA ou manual
   - **Com IA:** preenche wizard guiado (objetivo, critérios, grupos, eliminações) → `ia/construtor_prompt.py` monta prompt → Gemini Flash retorna JSON → editor preenchido
   - **Manual:** editor em branco
4. **Editor** → configura:
   - Dados pessoais a coletar (nome, email, telefone — cada um com toggle obrigatório/opcional)
   - Bloqueio de reenvio por email (on/off — quando on, email vira obrigatório automaticamente)
   - Perguntas (todos os tipos, ordenáveis)
   - Grupos customizados com mensagem final opcional
   - Variáveis de pontuação com valor inicial
   - Regras combinadas (condição fixa → grupo OU condição → somar/subtrair em variável)
   - Thresholds finais (variável X ≥ N → grupo Y)
   - Modo de tela final: genérico / personalizado por grupo / mostrar grupo
5. **Publicar** → cai no painel do formulário
6. **Painel do formulário** (abas):
   - **Respostas:** contagem por grupo, radar médio por grupo, lista de respondentes com drill-down (respostas individuais + radar próprio)
   - **Compartilhar:** link público para copiar
   - **Editar:** volta pro editor
   - **Encerrar:** botão de ação na barra (não uma aba) — exibe `confirm()` antes de chamar `POST /formularios/{id}/encerrar`

### Fluxo do respondente

1. Acessa link público
2. Vê dados pessoais no topo (apenas os campos que o mestre configurou)
3. Preenche perguntas com scroll
4. Envia → motor de regras avalia e classifica
5. Vê tela final configurada pelo mestre
6. CTA no rodapé: "Quer criar seus próprios formulários? Cadastre-se"
7. Se criar conta, o histórico de respostas fica vinculado ao email

---

## Motor de regras

Executado no backend após cada submissão. Ordem de avaliação:

1. Inicializa todas as variáveis com `initial_value`
2. Avalia regras em ordem (`rules.order`)
3. Para cada regra: avalia condições com `logical_operator` (AND/OR)
   - Se condição satisfeita e `action_type = assign_group` → atribui grupo e **para a avaliação** (eliminação direta)
   - Se condição satisfeita e `action_type = add_score/subtract_score` → atualiza variável e continua
4. Após todas as regras: agrupa `group_thresholds` por `group_id`, ordena os grupos pelo `order` (todos os thresholds de um grupo têm o mesmo `order`) — avalia grupo a grupo em ordem crescente; o primeiro grupo cujos thresholds forem **todos** satisfeitos é atribuído
5. Se nenhum grupo for atribuído (nem por `assign_group` nem por `group_thresholds`): `assigned_group_id` fica null, frontend exibe mensagem genérica de fim
6. Persiste resultado em `responses`

---

## Integração com IA

Arquivo: `ia/construtor_prompt.py`

**Entrada:** respostas do wizard — campos concretos:

| campo | tipo | obrigatório | descrição |
|---|---|---|---|
| `objetivo` | textarea | sim | Objetivo do formulário e perfil ideal buscado (ex: "Selecionar jogadores para time amador de futebol") |
| `grupos` | lista dinâmica (mín. 2) | sim | Nomes dos grupos de classificação, do mais positivo ao menos positivo (ex: "aprovado", "potencial", "rejeitado") |
| `criterios` | textarea | sim | Fatores avaliados e como cada um influencia a classificação (ex: "Comprometimento com treinos pesa mais que experiência prévia") |
| `eliminacoes` | textarea | não | Condições que eliminam diretamente o candidato, independente dos demais fatores (ex: "Mora a mais de 1h do local") |
| `num_perguntas` | número inteiro | não (padrão: 8) | Quantidade aproximada de perguntas a gerar |

**Saída esperada do Gemini (JSON):**
```json
{
  "questions": [
    {
      "text": "Onde você mora em relação ao local de jogo?",
      "type": "multiple_choice",
      "options": ["perto (menos de 30min)", "médio (30-60min)", "longe (mais de 1h)"],
      "required": true
    }
  ],
  "variables": [
    { "name": "comprometimento", "initial_value": 0 },
    { "name": "conhecimento", "initial_value": 0 }
  ],
  "groups": [
    { "name": "aprovado" },
    { "name": "potencial" },
    { "name": "rejeitado" }
  ],
  "rules": [
    {
      "order": 1,
      "conditions": [{ "field": "distancia", "operator": "eq", "value": "longe (mais de 1h)" }],
      "logical_operator": "AND",
      "action_type": "assign_group",
      "action_target": "rejeitado",
      "action_value": null
    }
  ],
  "group_thresholds": [
    { "group": "aprovado", "variable": "comprometimento", "operator": "gte", "value": 40 }
  ]
}
```

**Regras do prompt:**
- Instruir o Gemini a retornar APENAS JSON válido, sem texto fora dele
- Validar o JSON recebido contra schema Pydantic antes de usar
- Se inválido: exibir mensagem amigável no wizard ("Não foi possível gerar o formulário. Tente novamente.") mantendo os dados preenchidos — o mestre reenvia sem repetir o formulário
- `conditions[].field` na saída da IA usa **nomes conceituais** (ex: "distancia"), não UUIDs — o editor exibe as perguntas geradas e o mestre seleciona explicitamente a pergunta correspondente em um dropdown; o frontend envia o UUID diretamente no save (sem mapeamento automático no backend)
- `group_thresholds` na saída da IA não inclui `order` — ao importar no editor, o `order` é atribuído sequencialmente pela primeira ocorrência de cada grupo distinto no array (1º grupo distinto = order 1, 2º = order 2, etc.)
- `num_perguntas` no prompt: o construtor inclui a instrução `"Gere aproximadamente {num_perguntas} perguntas."` no corpo do prompt enviado ao Gemini. Quando não informado pelo mestre, o padrão é 8.

---

## Regras de desenvolvimento

- Todo endpoint autenticado verifica JWT antes de qualquer lógica
- Nunca expor `password_hash` em nenhuma resposta
- Variáveis de ambiente obrigatórias: `DATABASE_URL`, `JWT_SECRET`, `GEMINI_API_KEY`. Opcional: `DEBUG=true` (desliga `secure` no cookie JWT para desenvolvimento local em HTTP — ausente em produção).
- Todas as queries usam parâmetros — nunca concatenar SQL
- Motor de regras deve ter cobertura de testes (`tests/respostas/test_motor.py`) — cobertura obrigatória: `assign_group` por regra, `add_score`/`subtract_score`, thresholds com AND/OR de condições, fallback null, operadores para cada tipo de pergunta (eq/neq em text/choice/checkbox, comparação numérica em scale/number). `block_resubmit` é validado no endpoint antes do motor — não pertence a esse arquivo. Outros módulos (servicos, repositorio) não exigem testes para MVP — exceção explícita à regra global de gerar testes junto com o código; prioridade é velocidade de entrega no MVP.
- Frontend usa Jinja2 — sem framework JS pesado
- Commits em português, mensagens descritivas
- Nomes de campos do banco e valores de enum (active/closed, assign_group, etc.) permanecem em inglês — nomes técnicos persistidos no DB, exceção explícita à regra de português do CLAUDE.md global

---

## Decisões de contexto

- **ORM:** SQLAlchemy ORM + Alembic para migrations — modelos em `orm.py` por domínio, separados dos schemas Pydantic em `modelos.py`
- **`rules.conditions[].field`:** UUID da pergunta no banco — o motor busca a resposta em `answers[question_id]`. A IA retorna nomes conceituais; o mapeamento para UUID ocorre no save do editor.
- **JWT:** token único, expiração em 7 dias, sem refresh token — projeto de portfólio
- **JWT cookie flags:** `httponly=True`, `secure=True` (HTTPS-only — Railway e Render servem HTTPS), `samesite="lax"`. Em desenvolvimento local com HTTP, `secure` pode ser desligado via variável de ambiente `DEBUG=true`.
- **JWT verification:** função `get_usuario_atual()` em `auth/servicos.py`, injetada via `Depends()` nas rotas autenticadas — nunca verificação inline por rota
- **JWT respondente:** rota pública do formulário usa `get_usuario_opcional()` (também em `auth/servicos.py`) — não levanta 401 se não houver token; se logado, `user_id` é preenchido na resposta; se anônimo, fica null
- **Formato de erro:** padrão nativo do FastAPI — `{"detail": "mensagem"}`
- **Status inicial de formulário:** formulários são criados com `status = draft`; só ficam acessíveis via link público após o mestre clicar em "Publicar" (`status → active`)
- **Endpoints de transição de status:** `POST /formularios/{id}/publicar` (draft→active) e `POST /formularios/{id}/encerrar` (active→closed) — endpoints dedicados; `PATCH /formularios/{id}` edita apenas conteúdo e nunca muda `status`
- **block_resubmit enforcement:** no endpoint de submissão, antes de salvar: (1) se `block_resubmit=true` e email não foi fornecido → 422; (2) se `block_resubmit=true` e já existe registro com mesmo `respondent_email + form_id` → 409 Conflict; o frontend deve tornar o campo email obrigatório quando `block_resubmit=true`
- **group_thresholds.order semântica:** o campo `order` representa a prioridade do grupo, não do threshold individual — todos os thresholds de um mesmo grupo devem ter o mesmo valor de `order`; o motor agrupa por `group_id` e ordena grupos pelo `order` comum
- **Fallback de classificação:** se nenhuma regra ou threshold classificar o respondente, `assigned_group_id` fica null e o frontend exibe a mensagem genérica de fim
- **Vinculação de respostas ao email:** nos endpoints de cadastro e login, após autenticar o usuário, executa `UPDATE responses SET user_id=usuario_id WHERE respondent_email=email AND user_id IS NULL` — comportamento idêntico nos dois fluxos; ver também "Vinculação de respostas no login" abaixo
- **Fallback IA JSON inválido:** exibe erro no wizard com botão "Tentar novamente", mantendo os dados preenchidos pelo mestre
- **Operadores em `rules.conditions`:** `eq / neq` para tipos `text`, `multiple_choice` e `checkbox`; `eq / neq / gte / lte / gt / lt` para tipos `scale` e `number`. O editor restringe as opções de operador com base no tipo da pergunta selecionada. O motor aplica comparação de strings para eq/neq em text/choice e comparação numérica para scale/number. Para checkbox, `eq` verifica se o valor está contido na lista de selecionados; `neq` verifica ausência.
- **Formato de resposta para checkbox:** `answers[question_id]` armazena lista JSON de strings com as opções marcadas — ex: `["opcao1", "opcao3"]`. O motor avalia condições sobre checkbox usando `in`/`not in` (mapeado de eq/neq).
- **Mapeamento nome conceitual → UUID no editor:** o editor usa dropdowns populados com as perguntas, grupos e variáveis do formulário. O frontend envia UUIDs diretamente no save — sem mapeamento automático no backend. Para formulários gerados pela IA, o editor exibe o nome conceitual como placeholder; o mestre seleciona explicitamente a pergunta, grupo ou variável correspondente antes de salvar. Isso se aplica a `conditions[].field`, `action_target` (assign_group → dropdown de grupos; add/subtract_score → dropdown de variáveis).
- **`action_target` armazena UUID:** ao contrário do que a IA retorna (nomes), o banco persiste UUID — o mapeamento ocorre via seleção explícita do mestre no editor, não automaticamente. Renomear um grupo ou variável não quebra regras existentes.
- **finish_mode com grupo null:** independente do `finish_mode` configurado (generic, custom ou show_group), se `assigned_group_id = null`, o frontend sempre exibe a mensagem genérica de fim.
- **Radar sem variáveis:** quando o formulário não possui variáveis, o gráfico radar é ocultado no painel do formulário e na tela de drill-down individual, sem mensagem de erro — a seção simplesmente não é renderizada.
- **block_resubmit e email_required:** quando `block_resubmit = true`, o backend força `email_required = true` independente do valor salvo; o frontend deve refletir isso tornando o campo email obrigatório na UI do respondente.
- **block_resubmit + collect_email=false:** combinação inválida — o editor força `collect_email = true` automaticamente ao ativar `block_resubmit`, e não permite desmarcar `collect_email` enquanto `block_resubmit` estiver ativo. O backend deve rejeitar com 422 se receber `block_resubmit=true` e `collect_email=false` no save do formulário.
- **Tipo scale:** valor armazenado como inteiro em `answers[question_id]`. Intervalo definido pelo mestre via `options: {"min": 1, "max": 10}` — defaults 1 e 10 quando não especificado. O formulário do respondente exibe a pergunta scale como slider horizontal com os valores min e max visíveis nas extremidades. O editor do mestre exibe apenas os campos de configuração min/max. O motor avalia condições sobre scale com comparação numérica (todos os operadores: eq/neq/gte/lte/gt/lt).
- **Permissões de edição por status:** formulários em qualquer status (draft, active, closed) podem ser editados pelo mestre via `PATCH /formularios/{id}`. Edições em formulários active têm efeito imediato — respostas existentes não são reavaliadas. O mestre é responsável pelo impacto. Formulários closed permitem edição para eventual reabertura, mas ficam inacessíveis para novos respondentes enquanto status=closed.
- **URL patterns de navegação do mestre:** `GET /` → redireciona para `/dashboard` se autenticado, para `/auth/login` se não; `GET /dashboard` → painel principal (`dashboard/index.html`); `GET /formularios/{id}/painel` → painel do formulário (`dashboard/painel_formulario.html`); `GET /formularios/{id}/editar` → editor (`editor/editor.html`); `GET /formularios/{id}/painel/resposta/{response_id}` → drill-down individual (renderizado em `painel_formulario.html` com contexto de resposta específica). Rotas de autenticação em `GET /auth/login` e `GET /auth/cadastro`.
- **Rotas do wizard IA:** `GET /formularios/wizard` exibe `wizard_ia/wizard.html`; `POST /formularios/wizard` recebe os dados do wizard, chama `ia/construtor_prompt.py`, e em caso de sucesso redireciona para `GET /formularios/{novo_id}/editar` com o formulário pré-preenchido; em caso de erro re-renderiza o wizard com os dados preservados. Ambas as rotas ficam em `formularios/rotas.py`.
- **Ordenação de perguntas no editor:** drag-and-drop — mesmo mecanismo usado para thresholds. A posição na lista determina o campo `order` enviado no PATCH.
- **Texto da mensagem genérica de fim:** "Obrigado por participar!" — exibido em `fim.html` nos casos: `finish_mode=generic`; `finish_mode=custom` sem `finish_message`; `assigned_group_id=null` independente do `finish_mode`.
- **URL pública do respondente:** `GET /r/{form_id}` — rota pública sem autenticação. Link exibido no painel do formulário para o mestre copiar e compartilhar.
- **`GET /r/{form_id}` por status:** se `draft` → 404 (o formulário não existe publicamente ainda); se `closed` → renderiza `responder/encerrado.html` com a mensagem "Este formulário foi encerrado e não aceita mais respostas." — o respondente recebe feedback claro em vez de erro genérico.
- **`POST /r/{form_id}` por status:** se `draft` → 404; se `closed` → 403 com `{"detail": "Formulário encerrado."}` — cobre o caso de o respondente ter a página aberta no momento em que o mestre encerra o formulário.
- **Valores padrão de formulário novo:** `title="Novo formulário"`, `collect_name=false`, `collect_email=false`, `collect_phone=false`, `name_required=false`, `email_required=false`, `phone_required=false`, `finish_mode=generic`, `block_resubmit=false`, `status=draft`.
- **"Histórico de formulários respondidos" no painel do mestre:** lista de respostas onde `responses.user_id = current_user.id` — ou seja, formulários que o próprio mestre respondeu como respondente (de outros mestres). Exibe título do formulário, data de submissão e grupo recebido.
- **Falha de rede/timeout na API do Gemini:** tratado como JSON inválido — exibe o mesmo erro amigável no wizard com botão "Tentar novamente". Não há retry automático.
- **`conditions[].value` tipo no JSONB:** armazenado com o tipo nativo do JSON — string para `text`, `multiple_choice` e `checkbox` (ex: `"longe (mais de 1h)"`); inteiro para `scale` e `number` (ex: `7`). O motor não faz cast — compara strings para text/choice/checkbox e compara numericamente para scale/number diretamente pelo tipo armazenado no JSONB.
- **Persistência do wizard no retry:** os dados do wizard são submetidos via POST ao backend; em caso de falha da IA (JSON inválido, timeout ou erro de rede), o backend re-renderiza `wizard.html` com os valores recebidos via `request.form`, mantendo todos os campos preenchidos. Nenhuma lógica de persistência no frontend é necessária.
- **Wizard `grupos` — submissão via form POST:** o campo `grupos` usa múltiplos `<input name="grupos">` adicionados/removidos dinamicamente via JS (botão "adicionar grupo" / "remover"). O backend recebe como `grupos: List[str] = Form(...)` no FastAPI. JS mínimo permitido para manipulação de DOM — sem biblioteca.
- **`finish_mode = show_group`:** exibe o texto "Você foi classificado como: **[nome do grupo]**" na tela final do respondente, sem mensagem adicional. Útil quando o mestre quer revelar a classificação mas sem elaborar. Diferença em relação a `custom`: `custom` exibe o `finish_message` do grupo (mensagem elaborada); `custom` sem `finish_message` cai para a mensagem genérica; `show_group` sempre exibe o nome do grupo com o texto contextual acima, independente de `finish_message`.
- **Vinculação de respostas no login:** além do cadastro, o login de usuário existente também executa `UPDATE responses SET user_id=usuario_id WHERE respondent_email=email AND user_id IS NULL` — mesmo comportamento do cadastro. Isso garante que respostas anônimas com o mesmo email sejam vinculadas ao fazer login, não apenas ao se cadastrar.
- **"Encerrar" no painel do formulário:** é um botão de ação na barra de abas (não uma aba com conteúdo próprio). Ao clicar, exibe um `confirm()` JavaScript com a mensagem "Encerrar este formulário? Ele ficará inacessível para novos respondentes." — somente após confirmação chama `POST /formularios/{id}/encerrar`.
- **`PATCH /formularios/{id}` — payload atômico:** um único PATCH salva o formulário inteiro — title, questions, groups, variables, rules e thresholds em uma só chamada. O serviço reconcilia pelo UUID: itens sem UUID são criados, itens com UUID são atualizados, UUIDs presentes no banco mas ausentes no payload são deletados. Operação atômica em transação única.
- **Radar "médio por grupo" no dashboard:** um gráfico radar separado por grupo, exibindo a média de `variable_scores` dos respondentes classificados naquele grupo. Grupos sem nenhum respondente classificado não geram radar. Os radares são renderizados em sequência na aba Respostas.
- **Respostas sem grupo no dashboard:** respostas onde `assigned_group_id = null` são contadas e exibidas como "Sem classificação" no painel, junto com os demais grupos. O mestre sabe quantos respondentes não foram classificados por nenhuma regra ou threshold. Esses respondentes também aparecem na lista individual de drill-down — sem rótulo de grupo, mas com respostas e radar (quando aplicável) normalmente exibidos.
- **`finish_mode = custom` com `finish_message` null/vazio:** se o grupo atribuído não tiver `finish_message` preenchido, exibe a mensagem genérica de fim (mesmo comportamento de `finish_mode = generic`). O editor exibe aviso visual indicando que o grupo não tem mensagem configurada, mas não bloqueia o save.
- **`group_thresholds.order` no editor manual:** a ordem de prioridade dos grupos nos thresholds é definida por drag-and-drop na lista de grupos da seção de thresholds. A posição na lista determina o `order` (1º = order 1, 2º = order 2, etc.) — sem campo numérico explícito.
- **Endpoint de submissão de resposta:** `POST /r/{form_id}` — mesmo prefixo da visualização, método diferente. GET exibe o formulário; POST recebe a submissão. O atributo `action` do `<form>` em `formulario.html` aponta para `/r/{form_id}`.
- **`action_value` para subtract_score:** `action_value` é sempre um inteiro positivo. O motor aplica `variável += action_value` para `add_score` e `variável -= action_value` para `subtract_score`. Nunca valor negativo no banco.
- **Editor — comportamento do save:** há um botão "Salvar" explícito que dispara o `PATCH /formularios/{id}`. Sem auto-save. Se o mestre navegar para fora sem salvar, as alterações são perdidas sem aviso — comportamento aceitável para o escopo do projeto.
- **Painel do formulário — acesso por status:** `painel_formulario.html` é acessível para formulários em qualquer status (draft, active, closed). O fluxo "Publicar → cai no painel" indica redirecionamento após publicação, não restrição de acesso. Em draft, o painel exibe os dados disponíveis e o botão "Publicar" em destaque.
- **Transições de status inválidas:** `POST /formularios/{id}/publicar` retorna 400 se o formulário já está `active` (`{"detail": "Formulário já está publicado."}`) ou `closed` (`{"detail": "Formulário encerrado não pode ser republicado."}`); `POST /formularios/{id}/encerrar` retorna 400 se o formulário está em `draft` (`{"detail": "Formulário em rascunho não pode ser encerrado."}`) ou já está `closed` (`{"detail": "Formulário já está encerrado."}`).
- **`group_thresholds.operator` sem `neq`:** intencional — thresholds avaliam scores numéricos acumulados, onde "diferente de X" não tem semântica útil. Os operadores disponíveis (`gte / lte / eq / gt / lt`) cobrem todos os casos práticos de classificação por pontuação. Diferente de `rules.conditions`, que opera sobre respostas brutas onde `neq` é necessário.
- **Limite do histórico de respostas no painel principal:** exibe as últimas 20 respostas onde `responses.user_id = current_user.id`, ordenadas por `submitted_at` decrescente — sem paginação para MVP.
- **Deploy (Railway/Render):** start command `uvicorn main:app --host 0.0.0.0 --port $PORT`. Sem Dockerfile — Railway e Render detectam Python automaticamente via `pyproject.toml`. Variáveis de ambiente configuradas no painel do serviço.

---

## Melhorias possíveis (pós-MVP)
- Exportar respostas como CSV
- Notificação por email ao mestre quando nova resposta chegar
- Preview do formulário antes de publicar
- Formulário multi-página (em vez de scroll único)
- Limite de respostas configurável pelo mestre
