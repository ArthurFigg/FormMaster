import uuid
from typing import Any


def avaliar(
    regras: list[dict],
    thresholds: list[dict],
    variaveis: list[dict],
    respostas: dict[str, Any],
) -> tuple[uuid.UUID | None, dict[str, int]]:
    scores = {v['name']: v['initial_value'] for v in variaveis}
    id_para_nome = {str(v['id']): v['name'] for v in variaveis}

    for regra in sorted(regras, key=lambda r: r['order']):
        if _condicoes_ok(regra['conditions'], regra['logical_operator'], respostas):
            tipo = regra['action_type']
            if tipo == 'assign_group':
                return uuid.UUID(str(regra['action_target'])), scores
            nome = id_para_nome.get(str(regra['action_target']))
            if nome in scores:
                if tipo == 'add_score':
                    scores[nome] += regra['action_value']
                elif tipo == 'subtract_score':
                    scores[nome] -= regra['action_value']

    if thresholds:
        grupos: dict[str, dict] = {}
        for t in thresholds:
            gid = str(t['group_id'])
            if gid not in grupos:
                grupos[gid] = {'order': t['order'], 'rows': []}
            grupos[gid]['rows'].append(t)

        for gid_str, info in sorted(grupos.items(), key=lambda x: x[1]['order']):
            if _thresholds_ok(info['rows'], scores, id_para_nome):
                return uuid.UUID(gid_str), scores

    return None, scores


def _condicoes_ok(conditions: list[dict], op: str, respostas: dict) -> bool:
    resultados = [_cond_ok(c, respostas) for c in conditions]
    return all(resultados) if op == 'AND' else any(resultados)


def _cond_ok(cond: dict, respostas: dict) -> bool:
    resposta = respostas.get(str(cond['field']))
    if resposta is None:
        return False

    op = cond['operator']
    esperado = cond['value']

    if isinstance(resposta, list):
        if op == 'eq':  return esperado in resposta
        if op == 'neq': return esperado not in resposta
        return False

    if isinstance(resposta, (int, float)):
        if op == 'eq':  return resposta == esperado
        if op == 'neq': return resposta != esperado
        if op == 'gte': return resposta >= esperado
        if op == 'lte': return resposta <= esperado
        if op == 'gt':  return resposta > esperado
        if op == 'lt':  return resposta < esperado
        return False

    # text / multiple_choice
    if op == 'eq':  return str(resposta) == str(esperado)
    if op == 'neq': return str(resposta) != str(esperado)
    return False


def _thresholds_ok(rows: list[dict], scores: dict[str, int], id_para_nome: dict[str, str]) -> bool:
    for t in rows:
        nome = id_para_nome.get(str(t['variable_id']))
        if nome is None:
            return False
        score = scores.get(nome, 0)
        v = t['value']
        op = t['operator']
        if op == 'gte' and not score >= v: return False
        if op == 'lte' and not score <= v: return False
        if op == 'gt'  and not score > v:  return False
        if op == 'lt'  and not score < v:  return False
        if op == 'eq'  and not score == v: return False
    return True
