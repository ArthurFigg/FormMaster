# FormMaster

Plataforma web para criação de formulários com triagem automática. O mestre descreve o objetivo, a IA sugere perguntas e regras de classificação, ele edita e publica. Respondentes acessam por link público e são automaticamente classificados em grupos ao enviar o formulário.

---

## Funcionalidades

- **Criação assistida por IA** — wizard guiado gera perguntas, variáveis, regras e grupos automaticamente via Gemini Flash
- **Editor completo** — criação manual ou edição do formulário gerado pela IA, com perguntas de vários tipos, grupos, variáveis de pontuação e regras de triagem
- **Motor de regras** — avalia condições sobre respostas, acumula scores em variáveis e classifica respondentes por thresholds configuráveis
- **Múltiplos tipos de pergunta** — texto livre, múltipla escolha, caixas de seleção, escala (slider) e número
- **Tela final personalizável** — mensagem genérica, mensagem por grupo ou exibição do nome do grupo
- **Painel do mestre** — gráficos radar por grupo, contagem por classificação e drill-down individual por respondente
- **Bloqueio de reenvio** — impede que o mesmo email responda um formulário mais de uma vez
- **Vinculação de respostas** — respostas anônimas são vinculadas ao usuário quando ele faz login ou cadastro com o mesmo email
- **Autenticação JWT** — cookie httponly, sem exposição do token no frontend
- **Controle de status** — formulários passam por `rascunho → ativo → encerrado`; só ficam públicos quando ativos

---

## Pré-requisitos

- Python 3.11+
- [uv](https://docs.astral.sh/uv/) (gerenciador de pacotes)
- PostgreSQL (produção) ou SQLite (desenvolvimento local — sem configuração adicional)
- Chave de API do [Google Gemini](https://aistudio.google.com/) para a funcionalidade de IA

---

## Instalação

```bash
git clone <url-do-repositorio>
cd FormMaster
uv sync
```

Copie o arquivo de variáveis de ambiente e preencha os valores:

```bash
cp .env.example .env
```

---

## Configuração

| Variável | Obrigatória | Descrição |
|---|---|---|
| `DATABASE_URL` | sim | URL de conexão PostgreSQL (ex: `postgresql://user:pass@localhost:5432/formmaster`) |
| `JWT_SECRET` | sim | Chave secreta para assinar tokens JWT — gere com `python -c "import secrets; print(secrets.token_hex(32))"` |
| `GEMINI_API_KEY` | sim | Chave da API do Gemini Flash — obtenha em [aistudio.google.com](https://aistudio.google.com/) |
| `DEBUG` | não | `true` desliga o flag `secure` no cookie JWT, necessário para desenvolvimento local em HTTP |

**Desenvolvimento local com SQLite:** basta omitir `DATABASE_URL` ou defini-la como `sqlite:///./formmaster.db`. As tabelas são criadas automaticamente na inicialização.

---

## Uso

### Desenvolvimento local

```bash
uv run uvicorn main:app --reload
```

O app estará disponível em `http://localhost:8000`.

### Produção

```bash
uvicorn main:app --host 0.0.0.0 --port $PORT
```

Em produção com PostgreSQL, aplique as migrations antes de subir:

```bash
uv run alembic upgrade head
```

---

## Fluxo principal

**Mestre:**
1. Acessa `/auth/cadastro` e cria uma conta
2. No painel (`/dashboard`), clica em "Novo formulário"
3. Escolhe entre o wizard de IA ou editor manual
4. Configura perguntas, grupos, variáveis, regras e thresholds
5. Publica o formulário — recebe o link público para compartilhar
6. Acompanha respostas e classificações no painel do formulário

**Respondente:**
1. Acessa o link público (`/r/{id}`)
2. Preenche o formulário com scroll único
3. Recebe a classificação e a mensagem configurada pelo mestre

---

## Estrutura do projeto

```
FormMaster/
├── main.py              # entrypoint FastAPI — registra routers
├── config.py            # variáveis de ambiente (Pydantic BaseSettings)
├── database.py          # conexão com o banco (SQLAlchemy)
├── auth/                # autenticação — JWT, cadastro, login
├── formularios/         # CRUD de formulários, perguntas, grupos, variáveis e regras
├── respostas/           # motor de regras, submissão e persistência de respostas
├── dashboard/           # agregações e painel do mestre
├── ia/                  # construção de prompt e integração com Gemini Flash
├── templates/           # páginas HTML (Jinja2)
│   ├── auth/            # login e cadastro
│   ├── dashboard/       # painel principal e painel do formulário
│   ├── editor/          # editor de formulário
│   ├── wizard_ia/       # wizard guiado para geração por IA
│   └── responder/       # páginas do respondente
├── static/              # CSS e JavaScript
├── alembic/             # migrations de banco de dados
└── tests/
    └── respostas/       # testes do motor de regras
```

---

## Testes

```bash
uv run pytest -v
```

Os testes cobrem o motor de regras: atribuição direta por regra, acúmulo e subtração de scores, thresholds com operadores variados, operadores por tipo de pergunta e fallback sem classificação.

---

## Dependências de produção

| Pacote | Versão | Uso |
|---|---|---|
| `fastapi` | ≥ 0.115 | framework web |
| `uvicorn[standard]` | ≥ 0.30 | servidor ASGI |
| `sqlalchemy` | ≥ 2.0 | ORM |
| `alembic` | ≥ 1.13 | migrations |
| `pydantic-settings` | ≥ 2.5 | configuração via variáveis de ambiente |
| `python-jose[cryptography]` | ≥ 3.3 | geração e verificação de JWT |
| `passlib[bcrypt]` | ≥ 1.7 | hash de senhas |
| `google-genai` | ≥ 1.0 | integração com Gemini Flash |
| `psycopg2-binary` | ≥ 2.9 | driver PostgreSQL |
| `python-multipart` | ≥ 0.0.12 | parsing de formulários HTML |
| `jinja2` | ≥ 3.1 | templates HTML |

---

## Deploy

O projeto está pronto para Railway ou Render. Nenhum Dockerfile necessário — a plataforma detecta Python via `pyproject.toml`.

**Start command:**
```
uvicorn main:app --host 0.0.0.0 --port $PORT
```

Configure as variáveis `DATABASE_URL`, `JWT_SECRET` e `GEMINI_API_KEY` no painel do serviço.

---

## Licença

MIT
