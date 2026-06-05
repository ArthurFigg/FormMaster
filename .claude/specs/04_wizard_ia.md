# Wizard IA

## O que faz
Implementa o fluxo guiado de geração de formulário via Gemini Flash: o mestre preenche o wizard, a IA retorna um JSON estruturado, o sistema cria o formulário pré-preenchido e redireciona para o editor.

## Comportamento
- Quando `GET /formularios/wizard` é acessado com autenticação, renderiza `wizard_ia/wizard.html` com o formulário vazio
- Quando `GET /formularios/wizard` é acessado sem autenticação → redireciona para `/auth/login`
- Quando `POST /formularios/wizard` recebe os dados do wizard com todos os campos obrigatórios preenchidos: monta prompt, chama Gemini Flash, valida o JSON retornado contra schema Pydantic, cria o formulário com os dados da IA (título derivado do objetivo), redireciona para `GET /formularios/{novo_id}/editar`
- Quando `POST /formularios/wizard` recebe JSON inválido do Gemini (ou timeout ou erro de rede), re-renderiza `wizard_ia/wizard.html` com todos os campos preenchidos preservados e mensagem "Não foi possível gerar o formulário. Tente novamente." — sem perda dos dados digitados
- Quando `num_perguntas` não é informado, o prompt usa o padrão de 8 perguntas
- O campo `grupos` é submetido como múltiplos `<input name="grupos">` — mínimo 2 grupos obrigatórios
- O formulário criado pela IA tem `status=draft` e os dados da IA preenchidos: perguntas, grupos, variáveis, regras, thresholds — com `conditions[].field` e `action_target` salvos como strings conceituais (nome), não UUIDs; o mestre fará o mapeamento explícito no editor antes de salvar

## Critérios verificáveis
- [ ] `GET /formularios/wizard` com autenticação → 200 com `wizard_ia/wizard.html`
- [ ] `GET /formularios/wizard` sem autenticação → redirect para `/auth/login`
- [ ] `POST /formularios/wizard` com campos válidos e Gemini retornando JSON correto → 303 redirect para `/formularios/{id}/editar`
- [ ] `POST /formularios/wizard` com Gemini retornando JSON inválido → 200 com `wizard_ia/wizard.html`, campos preservados, mensagem de erro visível
- [ ] `POST /formularios/wizard` sem autenticação → 401 (ou redirect para login)
- [ ] `POST /formularios/wizard` sem campos obrigatórios (`objetivo`, `grupos`, `criterios`) → 422 ou re-render com erro
- [ ] Formulário criado pelo wizard tem `status=draft`
- [ ] `uv run pytest -v` passa

## Módulos afetados
- `ia/construtor_prompt.py` — criado: `montar_prompt(dados_wizard) -> str`, `chamar_gemini(prompt) -> dict`, `validar_resposta_ia(dados) -> RespostaIA`; schema Pydantic `RespostaIA` validando a estrutura completa do JSON esperado
- `formularios/rotas.py` — adicionado: `GET /formularios/wizard`, `POST /formularios/wizard`
- `formularios/servicos.py` — adicionado: `criar_formulario_de_ia(dados_ia, owner_id)` — cria formulário completo a partir do JSON da IA
- `templates/wizard_ia/wizard.html` — criado: formulário com campos `objetivo` (textarea), `grupos` (lista dinâmica com JS mínimo), `criterios` (textarea), `eliminacoes` (textarea), `num_perguntas` (number), área de erro opcional com dados preservados

## Não mexer
- `auth/`, `respostas/`, `dashboard/`
- Editor de mapeamento UUID — o wizard cria o formulário com nomes conceituais; o mapeamento para UUID é responsabilidade do mestre no editor (spec 05)
- Lógica de reconciliação do PATCH — esta spec usa criação simples, não reconciliação

## Decisões tomadas
- Rota do wizard → `GET/POST /formularios/wizard` em `formularios/rotas.py` (wizard cria formulário, pertence ao domínio de formulários)
- Prompt → `construtor_prompt.py` monta texto estruturado instruindo Gemini a retornar APENAS JSON válido sem texto fora
- Validação do JSON → schema Pydantic `RespostaIA`; qualquer falha de validação, timeout ou erro de rede → mesmo tratamento (re-render com erro)
- Dados preservados no retry → backend recebe via `request.form` e re-renderiza o template com os valores; sem lógica no frontend
- `groups` no wizard → `List[str]` recebido via `Form(...)`, mínimo 2 itens
- Formulário criado → usa `criar_formulario_de_ia()` que persiste os dados via INSERT direto (não via PATCH de reconciliação)
- `conditions[].field` e `action_target` gravados como nome conceitual string — placeholder para o mestre mapear no editor
- `group_thresholds.order` no import da IA → atribuído sequencialmente pela primeira ocorrência de cada grupo no array conforme CLAUDE.md

---
**Status:** concluida em 2026-06-05
