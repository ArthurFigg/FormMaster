# Editor de Formulário (Frontend)

## O que faz
Implementa o `editor.html` completo com todas as seções de configuração do formulário, interatividade via JS mínimo (sem biblioteca), integração com o PATCH atômico e botões de ação (Salvar, Publicar, Encerrar).

## Comportamento

### Seção: Configurações gerais
- Quando o mestre altera o título, o valor é refletido no payload do PATCH
- Quando `block_resubmit` é ativado, `collect_email` é forçado para `true` automaticamente e seu toggle é desabilitado enquanto `block_resubmit` estiver ativo
- Os toggles `collect_name`, `collect_email`, `collect_phone` exibem sub-toggles de obrigatoriedade (`name_required`, `email_required`, `phone_required`) apenas quando o campo pai está ativo
- O seletor de `finish_mode` tem três opções: genérico, personalizado por grupo, mostrar grupo

### Seção: Perguntas
- Quando "Adicionar pergunta" é clicado, novo item é inserido na lista com campos: texto, tipo, obrigatoriedade
- Quando o tipo `multiple_choice` ou `checkbox` é selecionado, exibe área para adicionar/remover opções de texto
- Quando o tipo `scale` é selecionado, exibe campos `min` e `max` (padrão 1 e 10)
- Quando o tipo `number` ou `text` é selecionado, nenhuma opção adicional é exibida
- A ordem das perguntas é alterável por drag-and-drop; a posição na lista determina o campo `order` enviado no PATCH
- Quando "Remover" é clicado em uma pergunta, ela é removida da lista (e ausente no próximo PATCH será deletada do banco)

### Seção: Grupos
- Quando "Adicionar grupo" é clicado, novo item é inserido com campos: nome e `finish_message` (textarea opcional)
- Grupos sem `finish_message` exibem aviso visual "Sem mensagem configurada" — não bloqueia o save
- Quando `finish_mode=show_group` está selecionado, grupos que têm `finish_message` preenchido exibem aviso visual "Mensagem ignorada no modo 'mostrar grupo'" ao lado do campo — o mestre é avisado que a mensagem não será exibida nesse modo
- Quando "Remover" é clicado, grupo é removido da lista

### Seção: Variáveis
- Quando "Adicionar variável" é clicado, novo item com campos: nome e `initial_value` (padrão 0)
- Quando "Remover" é clicado, variável é removida da lista

### Seção: Regras
- Quando "Adicionar regra" é clicado, novo item com: lista de condições, operador lógico (AND/OR), tipo de ação, alvo e valor
- Condição: dropdown de pergunta, operador (filtrado por tipo da pergunta), valor (texto livre ou dropdown para `multiple_choice`/`checkbox`)
- `action_type = assign_group` → `action_target` é dropdown de grupos; `action_value` oculto
- `action_type = add_score` ou `subtract_score` → `action_target` é dropdown de variáveis; `action_value` é campo numérico positivo
- Operadores disponíveis por tipo de pergunta: `text/multiple_choice/checkbox` → eq/neq; `scale/number` → eq/neq/gte/lte/gt/lt
- Quando "Remover" é clicado, regra removida

### Seção: Thresholds
- Lista de grupos com campos por grupo: variável (dropdown), operador, valor numérico
- A ordem de prioridade dos grupos é definida por drag-and-drop; posição determina `order` enviado no PATCH

### Botões de ação
- "Salvar" → dispara `PATCH /formularios/{id}` com payload completo; exibe feedback visual de sucesso/erro
- "Publicar" → só exibido quando `status=draft`; chama `POST /formularios/{id}/publicar`
- "Encerrar" → exibido como botão na barra (não como aba); exibe `confirm()` antes de chamar `POST /formularios/{id}/encerrar`
- Sem auto-save; navegação sem salvar perde alterações sem aviso

### Formulários gerados pela IA
- `conditions[].field` com nome conceitual (não UUID) exibido como placeholder no dropdown de perguntas — o mestre seleciona explicitamente a pergunta antes de salvar
- `action_target` com nome conceitual exibido como placeholder no dropdown de grupos/variáveis — idem

## Critérios verificáveis
- [ ] `GET /formularios/{id}/editar` com formulário vazio → página exibe todas as seções sem erro JS no console
- [ ] Adicionar pergunta tipo `scale` → campos `min`/`max` aparecem
- [ ] Adicionar pergunta tipo `multiple_choice` → área de opções aparece
- [ ] Ativar `block_resubmit` → `collect_email` fica marcado e desabilitado
- [ ] Clicar "Salvar" → `PATCH /formularios/{id}` é chamado com `Content-Type: application/json`
- [ ] PATCH retorna 200 → feedback de sucesso visível ao mestre
- [ ] Formulário gerado pela IA → editor abre sem erro mesmo com `conditions[].field` sendo string conceitual

## Módulos afetados
- `templates/editor/editor.html` — substituído: implementação completa com todas as seções, JS inline mínimo sem biblioteca
- `static/css/` — estilos do editor (sem framework CSS externo)
- `static/js/` — se necessário, arquivos JS separados por seção

## Não mexer
- `formularios/rotas.py`, `formularios/servicos.py`, `formularios/repositorio.py` — o editor apenas consome o PATCH existente
- Nenhum outro módulo Python

## Decisões tomadas
- JS → mínimo inline ou em arquivos estáticos, sem biblioteca ou framework
- Drag-and-drop → implementado com HTML5 Drag and Drop API nativa
- Payload do PATCH → serializado como JSON via `JSON.stringify`; todos os itens incluídos com seus UUIDs (ou sem UUID se novos)
- Formulários da IA → campos conceituais exibidos como placeholder; o mestre é responsável pelo mapeamento antes de salvar; sem validação automática de mapeamento no frontend
- Aviso visual para grupo sem `finish_message` → texto em cor de atenção ao lado do campo; não bloqueia save
- Feedback de save → mensagem discreta ("Salvo com sucesso" / "Erro ao salvar") exibida por alguns segundos
