'use strict';

let estado = {};
let FORM_ID = '';

document.addEventListener('DOMContentLoaded', () => {
  estado = JSON.parse(JSON.stringify(window.__dados));
  FORM_ID = estado.id;
  document.getElementById('titulo-form').addEventListener('input', e => {
    estado.title = e.target.value;
  });
  render();
});

function render() {
  renderConfig();
  renderPerguntas();
  renderGrupos();
  renderVariaveis();
  renderRegras();
  renderThresholds();
}

// ── helpers ─────────────────────────────────────────────────────────────────

function esc(s) {
  return String(s ?? '')
    .replace(/&/g, '&amp;').replace(/</g, '&lt;')
    .replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}

function selOpts(lista, atual) {
  return lista.map(o => `<option value="${esc(o.v)}"${o.v === atual ? ' selected' : ''}>${esc(o.l)}</option>`).join('');
}

function opsPorTipo(tipo) {
  if (tipo === 'scale' || tipo === 'number')
    return [
      { v: 'eq', l: '= igual' }, { v: 'neq', l: '≠ diferente' },
      { v: 'gte', l: '≥ maior/igual' }, { v: 'lte', l: '≤ menor/igual' },
      { v: 'gt', l: '> maior' }, { v: 'lt', l: '< menor' },
    ];
  return [{ v: 'eq', l: '= igual' }, { v: 'neq', l: '≠ diferente' }];
}

function qById(id) { return estado.questions.find(q => q.id === id) || null; }
function gById(id) { return estado.groups.find(g => g.id === id) || null; }

// ── config geral ─────────────────────────────────────────────────────────────

function renderConfig() {
  const c = document.getElementById('config-corpo');
  const s = estado;

  c.innerHTML = `
    <div class="toggle-row">
      <span class="texto">Bloquear reenvio por email</span>
      <label class="toggle"><input type="checkbox" id="cfg-block" ${s.block_resubmit ? 'checked' : ''}><span class="toggle-slider"></span></label>
    </div>

    <div class="toggle-row">
      <span class="texto">Coletar nome</span>
      <label class="toggle"><input type="checkbox" id="cfg-cname" ${s.collect_name ? 'checked' : ''}><span class="toggle-slider"></span></label>
    </div>
    ${s.collect_name ? `<div class="sub-toggle toggle-row"><span class="texto">Nome obrigatório</span>
      <label class="toggle"><input type="checkbox" id="cfg-nreq" ${s.name_required ? 'checked' : ''}><span class="toggle-slider"></span></label></div>` : ''}

    <div class="toggle-row">
      <span class="texto">Coletar email</span>
      <label class="toggle"><input type="checkbox" id="cfg-cemail" ${s.collect_email ? 'checked' : ''} ${s.block_resubmit ? 'disabled' : ''}><span class="toggle-slider"></span></label>
    </div>
    ${s.collect_email ? `<div class="sub-toggle toggle-row"><span class="texto">Email obrigatório</span>
      <label class="toggle"><input type="checkbox" id="cfg-ereq" ${s.email_required ? 'checked' : ''} ${s.block_resubmit ? 'disabled' : ''}><span class="toggle-slider"></span></label></div>` : ''}

    <div class="toggle-row">
      <span class="texto">Coletar telefone</span>
      <label class="toggle"><input type="checkbox" id="cfg-cphone" ${s.collect_phone ? 'checked' : ''}><span class="toggle-slider"></span></label>
    </div>
    ${s.collect_phone ? `<div class="sub-toggle toggle-row"><span class="texto">Telefone obrigatório</span>
      <label class="toggle"><input type="checkbox" id="cfg-preq" ${s.phone_required ? 'checked' : ''}><span class="toggle-slider"></span></label></div>` : ''}

    <div style="margin-top:12px" class="campo-inline">
      <label>Tela final do respondente</label>
      <select id="cfg-fmode" style="max-width:340px">
        ${selOpts([
          { v: 'generic', l: 'Genérico ("Obrigado por participar!")' },
          { v: 'custom', l: 'Personalizado por grupo' },
          { v: 'show_group', l: 'Mostrar nome do grupo' },
        ], s.finish_mode)}
      </select>
    </div>
  `;

  const bind = (id, campo, cb) => {
    const el = document.getElementById(id);
    if (!el) return;
    el.addEventListener('change', () => { estado[campo] = el.checked; if (cb) cb(); });
  };

  bind('cfg-block', 'block_resubmit', () => {
    if (estado.block_resubmit) { estado.collect_email = true; estado.email_required = true; }
    renderConfig();
  });
  bind('cfg-cname',  'collect_name',  renderConfig);
  bind('cfg-cemail', 'collect_email', renderConfig);
  bind('cfg-cphone', 'collect_phone', renderConfig);
  bind('cfg-nreq',   'name_required',  null);
  bind('cfg-ereq',   'email_required', null);
  bind('cfg-preq',   'phone_required', null);
  document.getElementById('cfg-fmode')?.addEventListener('change', e => {
    estado.finish_mode = e.target.value;
    renderGrupos();
  });
}

// ── perguntas ────────────────────────────────────────────────────────────────

let dragIdxQ = null;

function renderPerguntas() {
  const c = document.getElementById('perguntas-lista');
  c.innerHTML = '';
  if (estado.questions.length === 0) {
    c.innerHTML = '<p class="estado-vazio">Nenhuma pergunta adicionada.</p>';
    return;
  }
  estado.questions.forEach((q, idx) => {
    const div = criarItemPergunta(q, idx);
    c.appendChild(div);
  });
}

function criarItemPergunta(q, idx) {
  const div = document.createElement('div');
  div.className = 'item-lista';
  div.draggable = true;

  const tipos = [
    { v: 'text', l: 'Texto livre' }, { v: 'multiple_choice', l: 'Múltipla escolha' },
    { v: 'checkbox', l: 'Caixas de seleção' }, { v: 'scale', l: 'Escala' }, { v: 'number', l: 'Número' },
  ];

  let extra = '';
  if (q.type === 'multiple_choice' || q.type === 'checkbox') {
    const opts = (Array.isArray(q.options) ? q.options : [])
      .map((o, oi) => `<div class="opcao-row">
        <input type="text" class="opc-txt" data-oi="${oi}" value="${esc(o)}" placeholder="Opção ${oi + 1}">
        <button class="btn-rm opc-rm" data-oi="${oi}" type="button">✕</button>
      </div>`).join('');
    extra = `<div class="perg-extra"><div class="opcoes-lista">${opts}</div>
      <button class="btn-add-sm opc-add" type="button">+ Opção</button></div>`;
  } else if (q.type === 'scale') {
    const min = q.options?.min ?? 1;
    const max = q.options?.max ?? 10;
    extra = `<div class="perg-extra"><div class="scale-row">
      <label>Mín:</label><input type="number" class="scale-min" value="${esc(min)}">
      <label>Máx:</label><input type="number" class="scale-max" value="${esc(max)}">
    </div></div>`;
  }

  div.innerHTML = `
    <div class="item-header">
      <span class="drag-handle">⠿</span>
      <span class="item-num">#${idx + 1}</span>
      <button class="btn-rm perg-rm" type="button">Remover</button>
    </div>
    <div class="perg-linha1">
      <input type="text" class="perg-txt" value="${esc(q.text)}" placeholder="Enunciado da pergunta">
      <select class="perg-tipo">${selOpts(tipos, q.type)}</select>
      <label class="toggle" title="Obrigatória"><input type="checkbox" class="perg-req" ${q.required ? 'checked' : ''}><span class="toggle-slider"></span></label>
    </div>
    ${extra}
  `;

  // drag
  div.addEventListener('dragstart', e => { dragIdxQ = idx; div.classList.add('dragging'); e.dataTransfer.effectAllowed = 'move'; });
  div.addEventListener('dragend', () => { div.classList.remove('dragging'); document.querySelectorAll('#perguntas-lista .item-lista').forEach(el => el.classList.remove('drag-over')); });
  div.addEventListener('dragover', e => { e.preventDefault(); div.classList.add('drag-over'); });
  div.addEventListener('dragleave', () => div.classList.remove('drag-over'));
  div.addEventListener('drop', e => {
    e.preventDefault(); div.classList.remove('drag-over');
    if (dragIdxQ !== null && dragIdxQ !== idx) {
      const [item] = estado.questions.splice(dragIdxQ, 1);
      estado.questions.splice(idx, 0, item);
      renderPerguntas();
    }
  });

  // events
  div.querySelector('.perg-txt').addEventListener('input', e => { q.text = e.target.value; });
  div.querySelector('.perg-req').addEventListener('change', e => { q.required = e.target.checked; });
  div.querySelector('.perg-rm').addEventListener('click', () => { estado.questions.splice(idx, 1); renderPerguntas(); renderRegras(); });
  div.querySelector('.perg-tipo').addEventListener('change', e => {
    q.type = e.target.value;
    if (q.type === 'multiple_choice' || q.type === 'checkbox') q.options = Array.isArray(q.options) ? q.options : [];
    else if (q.type === 'scale') q.options = { min: 1, max: 10 };
    else q.options = null;
    renderPerguntas(); renderRegras();
  });

  if (q.type === 'multiple_choice' || q.type === 'checkbox') {
    div.querySelectorAll('.opc-txt').forEach(inp => {
      inp.addEventListener('input', e => { q.options[+inp.dataset.oi] = e.target.value; });
    });
    div.querySelectorAll('.opc-rm').forEach(btn => {
      btn.addEventListener('click', () => { q.options.splice(+btn.dataset.oi, 1); renderPerguntas(); });
    });
    div.querySelector('.opc-add').addEventListener('click', () => { q.options.push(''); renderPerguntas(); });
  }
  if (q.type === 'scale') {
    div.querySelector('.scale-min').addEventListener('input', e => { q.options = { ...q.options, min: +e.target.value || 1 }; });
    div.querySelector('.scale-max').addEventListener('input', e => { q.options = { ...q.options, max: +e.target.value || 10 }; });
  }

  return div;
}

function adicionarPergunta() {
  estado.questions.push({ id: null, order: estado.questions.length, text: '', type: 'text', options: null, required: false });
  renderPerguntas();
  document.getElementById('perguntas-lista').lastElementChild?.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
}

// ── grupos ───────────────────────────────────────────────────────────────────

function renderGrupos() {
  const c = document.getElementById('grupos-lista');
  c.innerHTML = '';
  if (estado.groups.length === 0) {
    c.innerHTML = '<p class="estado-vazio">Nenhum grupo adicionado.</p>';
    return;
  }
  estado.groups.forEach((g, idx) => {
    const semMsg = !g.finish_message?.trim();
    const isCustom = estado.finish_mode === 'custom';
    const isShow = estado.finish_mode === 'show_group';

    let aviso = '';
    if (isCustom && semMsg) aviso = '<div class="aviso">⚠ Sem mensagem — respondente verá mensagem genérica</div>';
    else if (isShow && !semMsg) aviso = '<div class="aviso-info">ℹ Mensagem ignorada no modo "mostrar grupo"</div>';

    const div = document.createElement('div');
    div.className = 'item-lista';
    div.innerHTML = `
      <div class="item-header">
        <span class="item-num">#${idx + 1}</span>
        <button class="btn-rm grp-rm" type="button">Remover</button>
      </div>
      <div style="display:flex;gap:12px">
        <div class="campo-inline" style="flex:1">
          <label>Nome do grupo</label>
          <input type="text" class="grp-nome" value="${esc(g.name)}" placeholder="ex: aprovado">
        </div>
        <div class="campo-inline" style="flex:2">
          <label>Mensagem final (opcional)</label>
          <textarea class="grp-msg" rows="2" placeholder="Exibida ao respondente classificado neste grupo">${esc(g.finish_message || '')}</textarea>
          ${aviso}
        </div>
      </div>
    `;
    div.querySelector('.grp-rm').addEventListener('click', () => { estado.groups.splice(idx, 1); renderGrupos(); renderRegras(); renderThresholds(); });
    div.querySelector('.grp-nome').addEventListener('input', e => { g.name = e.target.value; renderRegras(); renderThresholds(); });
    div.querySelector('.grp-msg').addEventListener('input', e => { g.finish_message = e.target.value || null; });
    c.appendChild(div);
  });
}

function adicionarGrupo() {
  estado.groups.push({ id: null, name: '', finish_message: null });
  renderGrupos(); renderRegras(); renderThresholds();
}

// ── variáveis ────────────────────────────────────────────────────────────────

function renderVariaveis() {
  const c = document.getElementById('variaveis-lista');
  c.innerHTML = '';
  if (estado.variables.length === 0) {
    c.innerHTML = '<p class="estado-vazio">Nenhuma variável adicionada.</p>';
    return;
  }
  estado.variables.forEach((v, idx) => {
    const div = document.createElement('div');
    div.className = 'item-lista';
    div.innerHTML = `
      <div class="item-header"><span class="item-num">#${idx + 1}</span>
        <button class="btn-rm var-rm" type="button">Remover</button></div>
      <div style="display:flex;gap:12px;align-items:flex-end">
        <div class="campo-inline" style="flex:1">
          <label>Nome da variável</label>
          <input type="text" class="var-nome" value="${esc(v.name)}" placeholder="ex: comprometimento">
        </div>
        <div class="campo-inline" style="width:120px">
          <label>Valor inicial</label>
          <input type="number" class="var-init" value="${esc(v.initial_value)}">
        </div>
      </div>
    `;
    div.querySelector('.var-rm').addEventListener('click', () => { estado.variables.splice(idx, 1); renderVariaveis(); renderRegras(); renderThresholds(); });
    div.querySelector('.var-nome').addEventListener('input', e => { v.name = e.target.value; renderRegras(); renderThresholds(); });
    div.querySelector('.var-init').addEventListener('input', e => { v.initial_value = parseInt(e.target.value) || 0; });
    c.appendChild(div);
  });
}

function adicionarVariavel() {
  estado.variables.push({ id: null, name: '', initial_value: 0 });
  renderVariaveis(); renderRegras(); renderThresholds();
}

// ── regras ───────────────────────────────────────────────────────────────────

function renderRegras() {
  const c = document.getElementById('regras-lista');
  c.innerHTML = '';
  if (estado.rules.length === 0) {
    c.innerHTML = '<p class="estado-vazio">Nenhuma regra adicionada.</p>';
    return;
  }
  estado.rules.forEach((r, idx) => {
    const div = document.createElement('div');
    div.className = 'item-lista';
    div.innerHTML = htmlRegra(r, idx);
    attachRegra(div, r, idx);
    c.appendChild(div);
  });
}

function htmlRegra(r, idx) {
  const condsHtml = r.conditions.map((cond, ci) => htmlCond(cond, idx, ci)).join('');
  const acaoTarget = htmlAcaoTarget(r);
  const acaoValor = (r.action_type !== 'assign_group')
    ? `<input type="number" class="acao-val" min="1" value="${esc(r.action_value ?? 1)}" style="width:80px">` : '';

  return `
    <div class="item-header">
      <span class="item-num">Regra #${idx + 1}</span>
      <button class="btn-rm regra-rm" type="button">Remover</button>
    </div>
    <div class="op-logico-row">
      <span>Condições:</span>
      <select class="op-logico">${selOpts([{ v: 'AND', l: 'Todas (AND)' }, { v: 'OR', l: 'Qualquer (OR)' }], r.logical_operator)}</select>
    </div>
    <div class="conds-wrap">${condsHtml}</div>
    <button class="btn-add-sm cond-add" type="button" style="margin-bottom:8px">+ Condição</button>
    <div class="regra-acao">
      <label>→ Ação:</label>
      <select class="acao-tipo">${selOpts([
        { v: 'assign_group', l: 'Classificar em grupo' },
        { v: 'add_score', l: 'Somar pontos' },
        { v: 'subtract_score', l: 'Subtrair pontos' },
      ], r.action_type)}</select>
      ${acaoTarget}
      ${acaoValor}
    </div>
  `;
}

function htmlCond(cond, ir, ic) {
  // Pergunta dropdown — detecta campo conceitual (não UUID de pergunta conhecida)
  const pergConhecida = estado.questions.some(q => q.id === cond.field);
  let optsP = estado.questions.map(q => {
    const txt = q.text || `Pergunta #${estado.questions.indexOf(q) + 1}`;
    return `<option value="${esc(q.id)}"${q.id === cond.field ? ' selected' : ''}>${esc(txt)}</option>`;
  }).join('');
  if (!pergConhecida && cond.field)
    optsP = `<option value="${esc(cond.field)}" selected disabled>[${esc(cond.field)}] — selecione</option>` + optsP;
  if (!optsP) optsP = '<option value="">— sem perguntas —</option>';

  const tipo = qById(cond.field)?.type || 'text';
  const optsOp = selOpts(opsPorTipo(tipo), cond.operator);

  return `<div class="cond-row" data-ir="${ir}" data-ic="${ic}">
    <select class="cond-field" data-ir="${ir}" data-ic="${ic}">${optsP}</select>
    <select class="cond-op"   data-ir="${ir}" data-ic="${ic}">${optsOp}</select>
    <input type="text" class="cond-val" data-ir="${ir}" data-ic="${ic}" value="${esc(cond.value)}" placeholder="valor">
    <button class="btn-rm cond-rm" type="button" data-ir="${ir}" data-ic="${ic}">✕</button>
  </div>`;
}

function htmlAcaoTarget(r) {
  if (r.action_type === 'assign_group') {
    const grupoConhecido = estado.groups.some(g => g.id === r.action_target);
    let opts = estado.groups.map(g => `<option value="${esc(g.id)}"${g.id === r.action_target ? ' selected' : ''}>${esc(g.name || 'Sem nome')}</option>`).join('');
    if (!grupoConhecido && r.action_target) opts = `<option value="${esc(r.action_target)}" selected disabled>[${esc(r.action_target)}] — selecione</option>` + opts;
    if (!opts) opts = '<option value="">— sem grupos —</option>';
    return `<select class="acao-grp">${opts}</select>`;
  }
  const varConhecida = estado.variables.some(v => v.id === r.action_target);
  let opts = estado.variables.map(v => `<option value="${esc(v.id)}"${v.id === r.action_target ? ' selected' : ''}>${esc(v.name || 'Sem nome')}</option>`).join('');
  if (!varConhecida && r.action_target) opts = `<option value="${esc(r.action_target)}" selected disabled>[${esc(r.action_target)}] — selecione</option>` + opts;
  if (!opts) opts = '<option value="">— sem variáveis —</option>';
  return `<select class="acao-var">${opts}</select>`;
}

function attachRegra(div, r, idx) {
  div.querySelector('.regra-rm').addEventListener('click', () => { estado.rules.splice(idx, 1); renderRegras(); });
  div.querySelector('.op-logico').addEventListener('change', e => { r.logical_operator = e.target.value; });
  div.querySelector('.acao-tipo').addEventListener('change', e => {
    r.action_type = e.target.value;
    r.action_target = '';
    r.action_value = r.action_type === 'assign_group' ? null : 1;
    renderRegras();
  });
  div.querySelector('.acao-grp')?.addEventListener('change', e => { r.action_target = e.target.value; });
  div.querySelector('.acao-var')?.addEventListener('change', e => { r.action_target = e.target.value; });
  div.querySelector('.acao-val')?.addEventListener('input', e => { r.action_value = parseInt(e.target.value) || 1; });
  div.querySelector('.cond-add').addEventListener('click', () => {
    r.conditions.push({ field: estado.questions[0]?.id || '', operator: 'eq', value: '' });
    renderRegras();
  });
  div.querySelectorAll('.cond-field').forEach(sel => {
    sel.addEventListener('change', e => {
      const ir = +sel.dataset.ir, ic = +sel.dataset.ic;
      estado.rules[ir].conditions[ic].field = e.target.value;
      estado.rules[ir].conditions[ic].operator = 'eq';
      renderRegras();
    });
  });
  div.querySelectorAll('.cond-op').forEach(sel => {
    sel.addEventListener('change', e => { estado.rules[+sel.dataset.ir].conditions[+sel.dataset.ic].operator = e.target.value; });
  });
  div.querySelectorAll('.cond-val').forEach(inp => {
    inp.addEventListener('input', e => { estado.rules[+inp.dataset.ir].conditions[+inp.dataset.ic].value = e.target.value; });
  });
  div.querySelectorAll('.cond-rm').forEach(btn => {
    btn.addEventListener('click', () => {
      const ir = +btn.dataset.ir, ic = +btn.dataset.ic;
      if (estado.rules[ir].conditions.length > 1) estado.rules[ir].conditions.splice(ic, 1);
      else estado.rules[ir].conditions[ic] = { field: estado.questions[0]?.id || '', operator: 'eq', value: '' };
      renderRegras();
    });
  });
}

function adicionarRegra() {
  const proxOrdem = estado.rules.length > 0 ? Math.max(...estado.rules.map(r => r.order)) + 1 : 1;
  estado.rules.push({
    id: null, order: proxOrdem,
    conditions: [{ field: estado.questions[0]?.id || '', operator: 'eq', value: '' }],
    logical_operator: 'AND', action_type: 'assign_group',
    action_target: estado.groups[0]?.id || '', action_value: null,
  });
  renderRegras();
}

// ── thresholds ───────────────────────────────────────────────────────────────

let dragGidThr = null;

function thrPorGrupo() {
  const mapa = new Map();
  estado.thresholds.forEach(t => {
    if (!mapa.has(t.group_id)) mapa.set(t.group_id, { group_id: t.group_id, order: t.order, rows: [] });
    mapa.get(t.group_id).rows.push(t);
  });
  return [...mapa.values()].sort((a, b) => a.order - b.order);
}

function renderThresholds() {
  const c = document.getElementById('thresholds-lista');
  c.innerHTML = '';
  const grupos = thrPorGrupo();

  if (grupos.length === 0) c.innerHTML = '<p class="estado-vazio">Nenhum grupo com threshold configurado.</p>';

  grupos.forEach((tg, pos) => {
    const g = gById(tg.group_id);
    const nome = g?.name || tg.group_id.substring(0, 8);

    const rowsHtml = tg.rows.map(t => {
      const varOpts = estado.variables.map(v => `<option value="${esc(v.id)}"${v.id === t.variable_id ? ' selected' : ''}>${esc(v.name || 'Sem nome')}</option>`).join('') || '<option value="">— sem variáveis —</option>';
      const opOpts = selOpts([
        { v: 'gte', l: '≥' }, { v: 'lte', l: '≤' }, { v: 'gt', l: '>' }, { v: 'lt', l: '<' }, { v: 'eq', l: '=' },
      ], t.operator);
      return `<div class="thr-row" data-gid="${esc(tg.group_id)}">
        <select class="thr-var">${varOpts}</select>
        <select class="thr-op">${opOpts}</select>
        <input type="number" class="thr-val" value="${esc(t.value)}">
        <button class="btn-rm thr-row-rm" type="button">✕</button>
      </div>`;
    }).join('');

    const div = document.createElement('div');
    div.className = 'thr-card';
    div.draggable = true;
    div.dataset.gid = tg.group_id;
    div.innerHTML = `
      <div class="thr-card-titulo">
        <span class="drag-handle">⠿</span>
        <span>${esc(nome)}</span>
        <span class="thr-prioridade">Prioridade ${pos + 1}</span>
        <button class="btn-rm thr-grp-rm" type="button">✕ grupo</button>
      </div>
      <div class="thr-rows">${rowsHtml}</div>
      <button class="btn-add-sm thr-add-row" type="button" style="margin-top:4px">+ Condição</button>
    `;

    // drag
    div.addEventListener('dragstart', e => { dragGidThr = tg.group_id; div.style.opacity = '0.35'; e.dataTransfer.effectAllowed = 'move'; });
    div.addEventListener('dragend', () => { div.style.opacity = ''; document.querySelectorAll('.thr-card').forEach(el => el.classList.remove('drag-over')); });
    div.addEventListener('dragover', e => { e.preventDefault(); div.classList.add('drag-over'); });
    div.addEventListener('dragleave', () => div.classList.remove('drag-over'));
    div.addEventListener('drop', e => {
      e.preventDefault(); div.classList.remove('drag-over');
      if (!dragGidThr || dragGidThr === tg.group_id) return;
      const lista = thrPorGrupo();
      const si = lista.findIndex(x => x.group_id === dragGidThr);
      const di = lista.findIndex(x => x.group_id === tg.group_id);
      const [m] = lista.splice(si, 1); lista.splice(di, 0, m);
      lista.forEach((g, i) => estado.thresholds.forEach(t => { if (t.group_id === g.group_id) t.order = i + 1; }));
      renderThresholds();
    });

    // row events
    div.querySelector('.thr-grp-rm').addEventListener('click', () => {
      estado.thresholds = estado.thresholds.filter(t => t.group_id !== tg.group_id);
      renderThresholds();
    });
    div.querySelector('.thr-add-row').addEventListener('click', () => {
      estado.thresholds.push({ id: null, group_id: tg.group_id, variable_id: estado.variables[0]?.id || '', operator: 'gte', value: 0, order: tg.order });
      renderThresholds();
    });
    div.querySelectorAll('.thr-row').forEach((row, ri) => {
      const t = tg.rows[ri];
      if (!t) return;
      row.querySelector('.thr-var')?.addEventListener('change', e => { t.variable_id = e.target.value; });
      row.querySelector('.thr-op')?.addEventListener('change', e => { t.operator = e.target.value; });
      row.querySelector('.thr-val')?.addEventListener('input', e => { t.value = parseInt(e.target.value) || 0; });
      row.querySelector('.thr-row-rm')?.addEventListener('click', () => {
        const i = estado.thresholds.indexOf(t);
        if (i !== -1) estado.thresholds.splice(i, 1);
        renderThresholds();
      });
    });

    c.appendChild(div);
  });

  // Seletor para adicionar grupo
  const addDiv = document.getElementById('thresholds-adicionar');
  addDiv.innerHTML = '';
  const comThr = new Set(estado.thresholds.map(t => t.group_id));
  const disponiveis = estado.groups.filter(g => g.id && !comThr.has(g.id));
  if (disponiveis.length === 0) return;
  const opts = disponiveis.map(g => `<option value="${esc(g.id)}">${esc(g.name || 'Sem nome')}</option>`).join('');
  addDiv.innerHTML = `<div class="thr-add-grupo">
    <select id="sel-thr-grp">${opts}</select>
    <button class="btn-add-sm" id="btn-thr-grp" type="button">+ Adicionar grupo</button>
  </div>`;
  document.getElementById('btn-thr-grp').addEventListener('click', () => {
    const gid = document.getElementById('sel-thr-grp').value;
    if (!gid) return;
    const novaOrdem = thrPorGrupo().length + 1;
    estado.thresholds.push({ id: null, group_id: gid, variable_id: estado.variables[0]?.id || '', operator: 'gte', value: 0, order: novaOrdem });
    renderThresholds();
  });
}

// ── salvar / publicar / encerrar ─────────────────────────────────────────────

async function salvar() {
  const fb = document.getElementById('feedback-save');
  const tituloEl = document.getElementById('titulo-form');
  if (tituloEl) estado.title = tituloEl.value;

  fb.textContent = 'Salvando…';
  fb.className = 'feedback-save';

  const payload = {
    title: estado.title,
    collect_name: estado.collect_name, collect_email: estado.collect_email, collect_phone: estado.collect_phone,
    name_required: estado.name_required, email_required: estado.email_required, phone_required: estado.phone_required,
    block_resubmit: estado.block_resubmit, finish_mode: estado.finish_mode,
    questions: estado.questions.map((q, i) => ({
      id: q.id || null, order: i, text: q.text, type: q.type, options: q.options, required: q.required,
    })),
    groups: estado.groups.map(g => ({ id: g.id || null, name: g.name, finish_message: g.finish_message })),
    variables: estado.variables.map(v => ({ id: v.id || null, name: v.name, initial_value: v.initial_value })),
    rules: estado.rules.map((r, i) => ({
      id: r.id || null, order: i + 1,
      conditions: r.conditions.map(cond => {
        const q = qById(cond.field);
        const val = (q?.type === 'scale' || q?.type === 'number') ? (parseInt(cond.value) || 0) : cond.value;
        return { field: cond.field, operator: cond.operator, value: val };
      }),
      logical_operator: r.logical_operator, action_type: r.action_type,
      action_target: r.action_target, action_value: r.action_value,
    })),
    thresholds: estado.thresholds
      .filter(t => t.group_id && t.variable_id)
      .map(t => ({ id: t.id || null, group_id: t.group_id, variable_id: t.variable_id, operator: t.operator, value: t.value, order: t.order })),
  };

  try {
    const resp = await fetch(`/formularios/${FORM_ID}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    if (resp.ok) {
      fb.textContent = '✓ Salvo com sucesso';
      setTimeout(() => window.location.reload(), 900);
    } else {
      const err = await resp.json().catch(() => ({ detail: resp.statusText }));
      fb.textContent = `✗ ${err.detail}`;
      fb.className = 'feedback-save erro';
    }
  } catch {
    fb.textContent = '✗ Erro de rede';
    fb.className = 'feedback-save erro';
  }
}

async function publicar() {
  try {
    await fetch(`/formularios/${FORM_ID}/publicar`, { method: 'POST' });
    window.location.href = `/formularios/${FORM_ID}/painel`;
  } catch {
    alert('Erro ao publicar.');
  }
}

async function encerrar() {
  if (!confirm('Encerrar este formulário? Ele ficará inacessível para novos respondentes.')) return;
  try {
    const resp = await fetch(`/formularios/${FORM_ID}/encerrar`, { method: 'POST' });
    if (resp.ok) window.location.reload();
    else { const e = await resp.json().catch(() => ({ detail: 'Erro' })); alert(e.detail); }
  } catch {
    alert('Erro ao encerrar.');
  }
}
