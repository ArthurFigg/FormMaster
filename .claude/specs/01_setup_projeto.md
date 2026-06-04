# Setup do Projeto

## O que faz
Cria toda a estrutura de pastas, arquivos de configuração e scaffolding do FormMaster para que o projeto possa rodar localmente e aceitar implementações nos demais módulos.

## Comportamento
- Quando `uv sync` é executado, todas as dependências são instaladas sem erro
- Quando `uv run fastapi dev main.py` é executado com `.env` configurado, o servidor sobe na porta 8000 sem erro e sem ImportError
- Quando `uv run alembic current` é executado, o Alembic responde sem erro mesmo sem migrations criadas
- Todos os módulos (`auth`, `formularios`, `respostas`, `dashboard`, `ia`) existem como pacotes Python com `__init__.py` vazio
- `main.py` importa os routers de todos os módulos sem erro — routers podem estar vazios, mas devem ser importáveis
- `config.py` lê `DATABASE_URL`, `JWT_SECRET`, `GEMINI_API_KEY` do `.env` via Pydantic BaseSettings; se qualquer variável obrigatória estiver ausente, levanta `ValidationError` com mensagem descritiva na inicialização
- `database.py` expõe `motor`, `SessionLocal` e `Base`; a conexão é lazy — não conecta ao banco na importação
- `.env.example` lista todas as variáveis com comentários explicativos, sem valores reais

## Critérios verificáveis
- [ ] `uv sync` executa sem erro
- [ ] `uv run python -c "from config import configuracoes; print(configuracoes.JWT_SECRET)"` imprime o valor sem erro (com `.env` configurado)
- [ ] `uv run python -c "from database import SessionLocal, Base"` não levanta erro
- [ ] `uv run alembic current` executa sem erro
- [ ] `uv run fastapi dev main.py` sobe sem ImportError (com `.env` configurado)
- [ ] `.env.example` contém `DATABASE_URL`, `JWT_SECRET`, `GEMINI_API_KEY`, `DEBUG`

## Módulos afetados
- `pyproject.toml` — criado com dependências: `fastapi`, `uvicorn[standard]`, `sqlalchemy`, `alembic`, `pydantic-settings`, `python-jose[cryptography]`, `passlib[bcrypt]`, `google-generativeai`, `psycopg2-binary`, `python-multipart`, `jinja2`
- `config.py` — criado: `Configuracoes(BaseSettings)` lendo `DATABASE_URL`, `JWT_SECRET`, `GEMINI_API_KEY`, `DEBUG` (bool, padrão `False`); instância global `configuracoes`
- `database.py` — criado: `motor` (SQLAlchemy engine), `SessionLocal`, `Base` declarativa, função `get_db()` como gerador para injeção via `Depends()`
- `alembic.ini` — criado com `sqlalchemy.url` lendo de `config.py`
- `alembic/env.py` — configurado para usar `Base.metadata` de `database.py` e importar todos os `orm.py` dos módulos (pode ser lista de imports comentados a ser descomentada a cada spec)
- `main.py` — criado: app FastAPI, montagem de `StaticFiles` em `/static`, configuração de `Jinja2Templates`, registro dos routers de `auth`, `formularios`, `respostas`, `dashboard`
- `auth/__init__.py`, `formularios/__init__.py`, `respostas/__init__.py`, `dashboard/__init__.py`, `ia/__init__.py` — criados vazios
- `auth/rotas.py`, `formularios/rotas.py`, `respostas/rotas.py`, `dashboard/rotas.py` — criados com `APIRouter()` vazio
- `static/css/`, `static/js/` — diretórios criados (com `.gitkeep` para não ficarem vazios)
- `templates/` — estrutura de diretórios criada conforme CLAUDE.md
- `.env.example` — criado

## Não mexer
- Lógica de negócio de qualquer domínio
- Conteúdo dos módulos além do `__init__.py` e router vazio

## Decisões tomadas
- Gerenciador de pacotes → `uv` com `pyproject.toml`, sem `requirements.txt`
- ORM → SQLAlchemy + Alembic (Base declarativa centralizada em `database.py`)
- `alembic/env.py` → importa todos os `orm.py` para Alembic detectar modelos; cada spec que cria um `orm.py` ativo deve descomentar o import correspondente
- `config.py` exporta instância única `configuracoes` importável por todos os módulos
- `get_db()` em `database.py` — gerador padrão do SQLAlchemy para injeção de sessão via `Depends()`
- `DEBUG=False` por padrão; `True` em desenvolvimento local para desligar `secure` no cookie JWT
