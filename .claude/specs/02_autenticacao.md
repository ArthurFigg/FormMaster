# Autenticação

## O que faz
Implementa cadastro e login de mestres com JWT em cookie httponly, as funções de verificação de token reutilizadas por todos os endpoints autenticados, e vinculação automática de respostas anônimas ao usuário pelo email.

## Comportamento
- Quando `GET /auth/login` é acessado, renderiza `auth/login.html`
- Quando `GET /auth/cadastro` é acessado, renderiza `auth/cadastro.html`
- Quando `POST /auth/cadastro` recebe email e senha válidos: cria usuário com hash bcrypt, emite cookie JWT, executa vinculação de respostas anônimas pelo email, redireciona para `/dashboard`
- Quando `POST /auth/cadastro` recebe email já cadastrado: re-renderiza `auth/cadastro.html` com mensagem de erro — não levanta exceção não tratada
- Quando `POST /auth/login` recebe credenciais corretas: emite cookie JWT, executa vinculação de respostas anônimas pelo email, redireciona para `/dashboard`
- Quando `POST /auth/login` recebe senha incorreta ou email inexistente: re-renderiza `auth/login.html` com mensagem de erro — não levanta 500
- Quando `POST /auth/logout` é chamado: apaga o cookie JWT e redireciona para `/auth/login`
- `get_usuario_atual()`: se cookie ausente ou token inválido/expirado → levanta `HTTPException(401)`; se válido → retorna instância de `Usuario`
- `get_usuario_opcional()`: se cookie ausente ou token inválido → retorna `None`; se válido → retorna instância de `Usuario`; nunca levanta 401
- Cookie emitido com `httponly=True`, `samesite="lax"`, `secure=not configuracoes.DEBUG`

## Critérios verificáveis
- [ ] `POST /auth/cadastro` com email/senha → resposta contém `Set-Cookie` com `httponly`
- [ ] `POST /auth/cadastro` com email duplicado → 200 (re-render), página contém mensagem de erro, nenhum novo usuário criado no banco
- [ ] `POST /auth/login` com credenciais corretas → resposta contém `Set-Cookie`
- [ ] `POST /auth/login` com senha errada → 200 (re-render) ou 401, página exibe erro
- [ ] Endpoint autenticado sem cookie → 401
- [ ] Endpoint autenticado com cookie válido → 200
- [ ] Campo `password_hash` não aparece em nenhuma resposta JSON nem em variáveis de template
- [ ] `POST /auth/login` com credenciais corretas e respostas anônimas com o mesmo email no banco → `responses.user_id` preenchido após login
- [ ] `POST /auth/cadastro` com respostas anônimas com o mesmo email no banco → `responses.user_id` preenchido após cadastro
- [ ] `uv run pytest -v` passa (testes existentes não quebram)

## Módulos afetados
- `auth/orm.py` — criado: modelo `Usuario` mapeando tabela `users` (id UUID, email, password_hash, created_at)
- `auth/modelos.py` — criado: schemas Pydantic `UsuarioCadastro(email, senha)`, `UsuarioLogin(email, senha)`, `UsuarioPublico(id, email, created_at)`
- `auth/servicos.py` — criado: `gerar_token(usuario_id)`, `verificar_token(token) -> UUID`, `hash_senha(senha)`, `verificar_senha(senha, hash)`, `get_usuario_atual()`, `get_usuario_opcional()`
- `auth/rotas.py` — criado: `GET /auth/login`, `GET /auth/cadastro`, `POST /auth/cadastro`, `POST /auth/login`, `POST /auth/logout`
- `templates/auth/login.html` — criado: formulário de login com campo de erro opcional
- `templates/auth/cadastro.html` — criado: formulário de cadastro com campo de erro opcional
- `alembic/versions/` — migration criada para tabela `users`
- `alembic/env.py` — import de `auth.orm` descomentado
- `main.py` — router `auth/rotas.py` registrado com prefixo `/auth`

## Não mexer
- `formularios/`, `respostas/`, `dashboard/`, `ia/`
- `database.py`, `config.py`

## Decisões tomadas
- JWT → python-jose, algoritmo HS256, expiração 7 dias, sem refresh token
- Cookie → `httponly=True`, `samesite="lax"`, `secure` lido de `configuracoes.DEBUG`
- Hash de senha → passlib bcrypt
- Logout → `POST /auth/logout` deleta cookie e redireciona para `/auth/login`
- Vinculação de respostas → `UPDATE responses SET user_id=? WHERE respondent_email=? AND user_id IS NULL` executada tanto no cadastro quanto no login
- Formulários de cadastro/login submetidos via `application/x-www-form-urlencoded` (Form do FastAPI), não JSON
- Redirect após login/cadastro → `/dashboard`
- Erros de autenticação → re-render do template com mensagem, não redirect
