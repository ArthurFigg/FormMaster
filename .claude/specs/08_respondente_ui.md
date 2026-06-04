# UI do Respondente

## O que faz
Implementa o endpoint público `GET /r/{form_id}` e os três templates do respondente: formulário de perguntas, tela final e tela de formulário encerrado.

## Comportamento

### `GET /r/{form_id}`
- Quando `status=draft` → 404
- Quando `status=closed` → renderiza `responder/encerrado.html` com mensagem "Este formulário foi encerrado e não aceita mais respostas."
- Quando `status=active` → renderiza `responder/formulario.html` com os dados do formulário

### `responder/formulario.html`
- Exibe os campos de dados pessoais no topo apenas se configurados pelo mestre:
  - `collect_name=true` → campo nome (obrigatório se `name_required=true`)
  - `collect_email=true` → campo email (obrigatório se `email_required=true` ou `block_resubmit=true`)
  - `collect_phone=true` → campo telefone (obrigatório se `phone_required=true`)
- Exibe as perguntas em sequência com scroll, na ordem definida por `order`
- Perguntas com `required=true` têm campo obrigatório no HTML (`required`)
- Tipo `text` → `<input type="text">`
- Tipo `multiple_choice` → `<input type="radio">` para cada opção
- Tipo `checkbox` → `<input type="checkbox">` para cada opção
- Tipo `scale` → `<input type="range">` com `min`, `max` e valores visíveis nas extremidades
- Tipo `number` → `<input type="number">`
- `action` do form aponta para `POST /r/{form_id}`
- Rodapé com CTA: "Quer criar seus próprios formulários? Cadastre-se" com link para `/auth/cadastro`

### `responder/fim.html`
- `finish_mode=generic` OU `assigned_group_id=null` (qualquer `finish_mode`) → exibe "Obrigado por participar!"
- `finish_mode=custom` com `finish_message` preenchido → exibe `finish_message` do grupo
- `finish_mode=custom` sem `finish_message` → exibe "Obrigado por participar!"
- `finish_mode=show_group` com `assigned_group_id` não-null → exibe "Você foi classificado como: **[nome do grupo]**"
- `finish_mode=show_group` com `assigned_group_id=null` → exibe "Obrigado por participar!"
- Rodapé com CTA idêntico ao `formulario.html`

### `responder/encerrado.html`
- Mensagem: "Este formulário foi encerrado e não aceita mais respostas."
- Rodapé com CTA idêntico

## Critérios verificáveis
- [ ] `GET /r/{form_id}` com `status=draft` → 404
- [ ] `GET /r/{form_id}` com `status=closed` → 200 com `encerrado.html`
- [ ] `GET /r/{form_id}` com `status=active` → 200 com `formulario.html`
- [ ] `formulario.html` com `collect_name=false` → campo nome ausente no HTML
- [ ] `formulario.html` com `collect_name=true` → campo nome presente no HTML
- [ ] `formulario.html` com pergunta `scale` → `<input type="range">` com `min` e `max` visíveis
- [ ] `formulario.html` com `block_resubmit=true` → campo email com atributo `required`
- [ ] `fim.html` com `finish_mode=generic` → exibe "Obrigado por participar!"
- [ ] `fim.html` com `finish_mode=show_group` e grupo definido → exibe "Você foi classificado como: **[nome]**"
- [ ] `fim.html` com `assigned_group_id=null` → exibe "Obrigado por participar!" independente de `finish_mode`
- [ ] `uv run pytest -v` passa

## Módulos afetados
- `respostas/rotas.py` — adicionado: `GET /r/{form_id}` (verifica status e renderiza template correto)
- `templates/responder/formulario.html` — criado: formulário completo do respondente
- `templates/responder/fim.html` — substituído: implementação completa com lógica dos 3 `finish_mode`
- `templates/responder/encerrado.html` — criado: página de formulário encerrado

## Não mexer
- `POST /r/{form_id}` — já implementado na spec 07
- `respostas/motor.py`, `respostas/servicos.py`, `respostas/repositorio.py`
- Templates do mestre (`editor/`, `dashboard/`, `auth/`, `wizard_ia/`)

## Decisões tomadas
- `GET /r/{form_id}` → fica em `respostas/rotas.py` junto com o POST, mesmo prefixo `/r/`
- Texto genérico de fim → "Obrigado por participar!"
- `finish_mode=show_group` → texto fixo "Você foi classificado como: **[nome do grupo]**", sem `finish_message`
- CTA no rodapé → presente em todos os 3 templates do respondente
- Scale slider → `<input type="range">` com valores `min` e `max` exibidos como labels nas extremidades via HTML/CSS
- Dados pessoais → campos simples de texto/email/tel; sem validação de formato além do HTML nativo
