import uuid

from respostas.motor import avaliar

GID_A = uuid.uuid4()
GID_B = uuid.uuid4()
VID_1 = uuid.uuid4()
VID_2 = uuid.uuid4()
QID_1 = uuid.uuid4()  # text / multiple_choice
QID_2 = uuid.uuid4()  # checkbox
QID_3 = uuid.uuid4()  # scale
QID_4 = uuid.uuid4()  # number


def var(id_, nome, inicial=0):
    return {'id': id_, 'name': nome, 'initial_value': inicial}


def regra(order, conditions, logical_operator, action_type, action_target, action_value=None):
    return {
        'id': uuid.uuid4(), 'order': order,
        'conditions': conditions, 'logical_operator': logical_operator,
        'action_type': action_type,
        'action_target': str(action_target),
        'action_value': action_value,
    }


def cond(field, operator, value):
    return {'field': str(field), 'operator': operator, 'value': value}


def thr(group_id, variable_id, operator, value, order=1):
    return {
        'id': uuid.uuid4(), 'group_id': group_id,
        'variable_id': variable_id, 'operator': operator,
        'value': value, 'order': order,
    }


# ── testes ───────────────────────────────────────────────────────────────────

def test_assign_group_para_avaliacao():
    variaveis = [var(VID_1, 'pontos', 0)]
    regras = [
        regra(1, [cond(QID_1, 'eq', 'sim')], 'AND', 'assign_group', GID_A),
        regra(2, [cond(QID_1, 'eq', 'sim')], 'AND', 'add_score', VID_1, 10),
    ]
    grupo, scores = avaliar(regras, [], variaveis, {str(QID_1): 'sim'})
    assert grupo == GID_A
    assert scores['pontos'] == 0  # regra 2 não executou


def test_add_score_acumula():
    variaveis = [var(VID_1, 'pontos', 0)]
    regras = [
        regra(1, [cond(QID_3, 'gte', 5)], 'AND', 'add_score', VID_1, 10),
        regra(2, [cond(QID_3, 'gte', 8)], 'AND', 'add_score', VID_1, 5),
    ]
    grupo, scores = avaliar(regras, [], variaveis, {str(QID_3): 9})
    assert grupo is None
    assert scores['pontos'] == 15


def test_subtract_score_decrementa():
    variaveis = [var(VID_1, 'pontos', 20)]
    regras = [regra(1, [cond(QID_1, 'eq', 'ruim')], 'AND', 'subtract_score', VID_1, 5)]
    _, scores = avaliar(regras, [], variaveis, {str(QID_1): 'ruim'})
    assert scores['pontos'] == 15


def test_regras_avaliadas_em_ordem():
    variaveis = []
    regras = [
        regra(2, [cond(QID_3, 'gte', 1)], 'AND', 'assign_group', GID_B),
        regra(1, [cond(QID_3, 'gte', 1)], 'AND', 'assign_group', GID_A),
    ]
    grupo, _ = avaliar(regras, [], variaveis, {str(QID_3): 5})
    assert grupo == GID_A


def test_threshold_grupo_prioritario_vence():
    variaveis = [var(VID_1, 'pontos', 0)]
    regras = [regra(1, [cond(QID_3, 'gte', 1)], 'AND', 'add_score', VID_1, 40)]
    thresholds = [
        thr(GID_A, VID_1, 'gte', 30, order=1),
        thr(GID_B, VID_1, 'gte', 10, order=2),
    ]
    grupo, scores = avaliar(regras, thresholds, variaveis, {str(QID_3): 5})
    assert grupo == GID_A
    assert scores['pontos'] == 40


def test_threshold_todos_devem_passar():
    variaveis = [var(VID_1, 'pontos', 0), var(VID_2, 'bonus', 0)]
    regras = [regra(1, [cond(QID_3, 'gte', 1)], 'AND', 'add_score', VID_1, 30)]
    thresholds = [
        thr(GID_A, VID_1, 'gte', 20, order=1),
        thr(GID_A, VID_2, 'gte', 10, order=1),
    ]
    grupo, _ = avaliar(regras, thresholds, variaveis, {str(QID_3): 5})
    assert grupo is None  # pontos=30 ok, bonus=0 falha


def test_fallback_none():
    variaveis = [var(VID_1, 'pontos', 10)]
    grupo, scores = avaliar([], [], variaveis, {})
    assert grupo is None
    assert scores['pontos'] == 10


def test_operador_eq_text():
    regras = [regra(1, [cond(QID_1, 'eq', 'sim')], 'AND', 'assign_group', GID_A)]
    grupo, _ = avaliar(regras, [], [], {str(QID_1): 'sim'})
    assert grupo == GID_A
    grupo2, _ = avaliar(regras, [], [], {str(QID_1): 'nao'})
    assert grupo2 is None


def test_operador_neq_text():
    regras = [regra(1, [cond(QID_1, 'neq', 'ruim')], 'AND', 'assign_group', GID_A)]
    grupo, _ = avaliar(regras, [], [], {str(QID_1): 'bom'})
    assert grupo == GID_A
    grupo2, _ = avaliar(regras, [], [], {str(QID_1): 'ruim'})
    assert grupo2 is None


def test_operador_eq_checkbox():
    regras = [regra(1, [cond(QID_2, 'eq', 'opcao1')], 'AND', 'assign_group', GID_A)]
    grupo, _ = avaliar(regras, [], [], {str(QID_2): ['opcao1', 'opcao2']})
    assert grupo == GID_A
    grupo2, _ = avaliar(regras, [], [], {str(QID_2): ['opcao2']})
    assert grupo2 is None


def test_operador_neq_checkbox():
    regras = [regra(1, [cond(QID_2, 'neq', 'excluido')], 'AND', 'assign_group', GID_A)]
    grupo, _ = avaliar(regras, [], [], {str(QID_2): ['opcao1']})
    assert grupo == GID_A
    grupo2, _ = avaliar(regras, [], [], {str(QID_2): ['opcao1', 'excluido']})
    assert grupo2 is None


def test_operador_gte_scale():
    regras = [regra(1, [cond(QID_3, 'gte', 7)], 'AND', 'assign_group', GID_A)]
    grupo, _ = avaliar(regras, [], [], {str(QID_3): 7})
    assert grupo == GID_A
    grupo2, _ = avaliar(regras, [], [], {str(QID_3): 6})
    assert grupo2 is None


def test_operador_lte_scale():
    regras = [regra(1, [cond(QID_3, 'lte', 3)], 'AND', 'assign_group', GID_A)]
    grupo, _ = avaliar(regras, [], [], {str(QID_3): 3})
    assert grupo == GID_A
    grupo2, _ = avaliar(regras, [], [], {str(QID_3): 4})
    assert grupo2 is None


def test_operador_gt_number():
    regras = [regra(1, [cond(QID_4, 'gt', 10)], 'AND', 'assign_group', GID_A)]
    grupo, _ = avaliar(regras, [], [], {str(QID_4): 11})
    assert grupo == GID_A
    grupo2, _ = avaliar(regras, [], [], {str(QID_4): 10})
    assert grupo2 is None


def test_operador_lt_number():
    regras = [regra(1, [cond(QID_4, 'lt', 5)], 'AND', 'assign_group', GID_A)]
    grupo, _ = avaliar(regras, [], [], {str(QID_4): 4})
    assert grupo == GID_A
    grupo2, _ = avaliar(regras, [], [], {str(QID_4): 5})
    assert grupo2 is None


def test_condicoes_and_todas_devem_passar():
    condicoes = [cond(QID_1, 'eq', 'sim'), cond(QID_3, 'gte', 5)]
    regras = [regra(1, condicoes, 'AND', 'assign_group', GID_A)]
    grupo, _ = avaliar(regras, [], [], {str(QID_1): 'sim', str(QID_3): 7})
    assert grupo == GID_A
    grupo2, _ = avaliar(regras, [], [], {str(QID_1): 'sim', str(QID_3): 3})
    assert grupo2 is None


def test_condicoes_or_uma_basta():
    condicoes = [cond(QID_1, 'eq', 'sim'), cond(QID_3, 'gte', 5)]
    regras = [regra(1, condicoes, 'OR', 'assign_group', GID_A)]
    grupo, _ = avaliar(regras, [], [], {str(QID_1): 'sim', str(QID_3): 3})
    assert grupo == GID_A
    grupo2, _ = avaliar(regras, [], [], {str(QID_1): 'nao', str(QID_3): 3})
    assert grupo2 is None
