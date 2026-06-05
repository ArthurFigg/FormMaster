"""
Script descartável de seed — popula o banco com dados de demonstração.
Uso: uv run python seed.py
Credenciais criadas: admin@formmaster.com / admin123
"""
import uuid
from datetime import datetime, timedelta, timezone

from database import Base, motor, SessionLocal
from auth.orm import Usuario
from auth.servicos import hash_senha
from formularios.orm import Formulario, Pergunta, Grupo, Variavel, Regra, GrupoThreshold
from respostas.orm import Resposta
from respostas.motor import avaliar

Base.metadata.create_all(bind=motor)
db = SessionLocal()

# ── Usuário admin ─────────────────────────────────────────────────────────────

existente = db.query(Usuario).filter(Usuario.email == "admin@formmaster.com").first()
if existente:
    print("Usuário admin já existe — pulando criação.")
    admin = existente
else:
    admin = Usuario(
        email="admin@formmaster.com",
        password_hash=hash_senha("admin123"),
    )
    db.add(admin)
    db.flush()
    print(f"Usuário criado: admin@formmaster.com / admin123")

# ── Formulário ────────────────────────────────────────────────────────────────

form = Formulario(
    owner_id=admin.id,
    title="Seleção de Estagiários de Tecnologia",
    status="active",
    collect_name=True,
    collect_email=True,
    name_required=True,
    finish_mode="custom",
)
db.add(form)
db.flush()

# ── Perguntas ─────────────────────────────────────────────────────────────────

q_area = Pergunta(
    form_id=form.id, order=1, required=True,
    text="Qual sua área de interesse?",
    type="multiple_choice",
    options=["Backend", "Frontend", "Mobile", "Data Science"],
)
q_experiencia = Pergunta(
    form_id=form.id, order=2, required=True,
    text="Avalie seu nível de experiência com programação (1 = iniciante, 10 = expert):",
    type="scale",
    options={"min": 1, "max": 10},
)
q_horas = Pergunta(
    form_id=form.id, order=3, required=True,
    text="Quantas horas por semana pode dedicar ao estágio?",
    type="number",
    options=None,
)
q_tecnologias = Pergunta(
    form_id=form.id, order=4, required=False,
    text="Quais tecnologias você já usou? (marque todas que se aplicam)",
    type="checkbox",
    options=["Python", "JavaScript", "SQL", "Git"],
)
q_disponibilidade = Pergunta(
    form_id=form.id, order=5, required=True,
    text="Qual sua disponibilidade de trabalho?",
    type="multiple_choice",
    options=["Presencial", "Híbrido", "Apenas remoto"],
)
q_motivacao = Pergunta(
    form_id=form.id, order=6, required=False,
    text="Por que você quer estagiar conosco?",
    type="text",
    options=None,
)

for p in [q_area, q_experiencia, q_horas, q_tecnologias, q_disponibilidade, q_motivacao]:
    db.add(p)
db.flush()

# ── Grupos ────────────────────────────────────────────────────────────────────

g_aprovado = Grupo(
    form_id=form.id, name="Aprovado",
    finish_message="Parabéns! Você passa para a próxima fase do processo seletivo.",
)
g_analise = Grupo(
    form_id=form.id, name="Em análise",
    finish_message="Seu perfil é interessante e está sendo avaliado pela nossa equipe. Retornaremos em breve.",
)
g_reprovado = Grupo(
    form_id=form.id, name="Reprovado",
    finish_message="Agradecemos seu interesse. Infelizmente seu perfil não se encaixa nesta vaga no momento.",
)

for g in [g_aprovado, g_analise, g_reprovado]:
    db.add(g)
db.flush()

# ── Variáveis ─────────────────────────────────────────────────────────────────

v_tecnico = Variavel(form_id=form.id, name="tecnico", initial_value=0)
v_disponibilidade = Variavel(form_id=form.id, name="disponibilidade", initial_value=0)

for v in [v_tecnico, v_disponibilidade]:
    db.add(v)
db.flush()

# ── Regras ────────────────────────────────────────────────────────────────────
# conditions[].field = str(pergunta.id)
# action_target = str(grupo.id) para assign_group, str(variavel.id) para score

regras = [
    Regra(
        form_id=form.id, order=1,
        conditions=[{"field": str(q_disponibilidade.id), "operator": "eq", "value": "Apenas remoto"}],
        logical_operator="AND", action_type="assign_group",
        action_target=str(g_reprovado.id), action_value=None,
    ),
    Regra(
        form_id=form.id, order=2,
        conditions=[{"field": str(q_experiencia.id), "operator": "gte", "value": 7}],
        logical_operator="AND", action_type="add_score",
        action_target=str(v_tecnico.id), action_value=30,
    ),
    Regra(
        form_id=form.id, order=3,
        conditions=[{"field": str(q_horas.id), "operator": "gte", "value": 30}],
        logical_operator="AND", action_type="add_score",
        action_target=str(v_disponibilidade.id), action_value=30,
    ),
    Regra(
        form_id=form.id, order=4,
        conditions=[{"field": str(q_tecnologias.id), "operator": "eq", "value": "Python"}],
        logical_operator="AND", action_type="add_score",
        action_target=str(v_tecnico.id), action_value=20,
    ),
    Regra(
        form_id=form.id, order=5,
        conditions=[{"field": str(q_tecnologias.id), "operator": "eq", "value": "JavaScript"}],
        logical_operator="AND", action_type="add_score",
        action_target=str(v_tecnico.id), action_value=10,
    ),
    Regra(
        form_id=form.id, order=6,
        conditions=[{"field": str(q_tecnologias.id), "operator": "eq", "value": "SQL"}],
        logical_operator="AND", action_type="add_score",
        action_target=str(v_tecnico.id), action_value=10,
    ),
    Regra(
        form_id=form.id, order=7,
        conditions=[{"field": str(q_tecnologias.id), "operator": "eq", "value": "Git"}],
        logical_operator="AND", action_type="add_score",
        action_target=str(v_tecnico.id), action_value=10,
    ),
]

for r in regras:
    db.add(r)
db.flush()

# ── Thresholds ────────────────────────────────────────────────────────────────
# Aprovado (order=1): tecnico >= 40 E disponibilidade >= 20
# Em análise (order=2): tecnico >= 20

thresholds = [
    GrupoThreshold(group_id=g_aprovado.id, variable_id=v_tecnico.id,       operator="gte", value=40, order=1),
    GrupoThreshold(group_id=g_aprovado.id, variable_id=v_disponibilidade.id, operator="gte", value=20, order=1),
    GrupoThreshold(group_id=g_analise.id,  variable_id=v_tecnico.id,       operator="gte", value=20, order=2),
]

for t in thresholds:
    db.add(t)
db.flush()

# ── Helpers para o motor ──────────────────────────────────────────────────────

_regras_motor = [
    {
        "id": r.id, "order": r.order,
        "conditions": r.conditions,
        "logical_operator": r.logical_operator,
        "action_type": r.action_type,
        "action_target": r.action_target,
        "action_value": r.action_value,
    }
    for r in sorted(regras, key=lambda x: x.order)
]

_thresholds_motor = [
    {
        "id": t.id, "group_id": t.group_id,
        "variable_id": t.variable_id,
        "operator": t.operator, "value": t.value, "order": t.order,
    }
    for t in thresholds
]

_variaveis_motor = [
    {"id": v.id, "name": v.name, "initial_value": v.initial_value}
    for v in [v_tecnico, v_disponibilidade]
]


def _responder(nome, email, area, exp, horas, tecnologias, disp, motivacao, delta_dias=0):
    answers = {
        str(q_area.id):           area,
        str(q_experiencia.id):    exp,
        str(q_horas.id):          horas,
        str(q_tecnologias.id):    tecnologias,
        str(q_disponibilidade.id): disp,
        str(q_motivacao.id):      motivacao,
    }
    grupo_id, scores = avaliar(_regras_motor, _thresholds_motor, _variaveis_motor, answers)
    r = Resposta(
        form_id=form.id,
        respondent_name=nome,
        respondent_email=email,
        assigned_group_id=grupo_id,
        variable_scores=scores,
        answers=answers,
        submitted_at=datetime.now(timezone.utc) - timedelta(days=delta_dias),
    )
    db.add(r)
    grupo_nome = {
        str(g_aprovado.id): "Aprovado",
        str(g_analise.id):  "Em análise",
        str(g_reprovado.id): "Reprovado",
    }.get(str(grupo_id) if grupo_id else "", "Sem classificação")
    print(f"  {nome:<22} -> {grupo_nome}  | tecnico={scores['tecnico']:>3}  disponibilidade={scores['disponibilidade']:>3}")


# ── Respostas ─────────────────────────────────────────────────────────────────

print("\nCriando respostas:")

# Aprovados (tecnico >= 40 E disponibilidade >= 20)
_responder("Carlos Mendes",    "carlos@email.com",   "Backend",     9, 40, ["Python","SQL","Git"],              "Presencial", "Quero crescer na área.", delta_dias=12)
_responder("Ana Beatriz",      "ana@email.com",      "Data Science",8, 35, ["Python","JavaScript"],             "Híbrido",    "Adoro dados e IA.",       delta_dias=10)
_responder("Rafael Costa",     "rafael@email.com",   "Backend",     7, 30, ["Python","Git"],                    "Presencial", "Ótima empresa.",           delta_dias=8)
_responder("Bruno Neto",       "bruno@email.com",    "Backend",     9, 32, ["Python","JavaScript","SQL","Git"], "Presencial", "Meu objetivo de carreira.", delta_dias=5)

# Em análise (tecnico >= 20, mas não Aprovado)
_responder("Juliana Ferreira", "juliana@email.com",  "Frontend",    5, 25, ["JavaScript","Git"],                "Presencial", "Quero aprender mais.",     delta_dias=9)
_responder("Pedro Oliveira",   "pedro@email.com",    "Mobile",      6, 25, ["Python","JavaScript"],             "Híbrido",    "Fã do produto de vocês.",  delta_dias=7)
_responder("Isabela Santos",   "isabela@email.com",  "Frontend",    4, 35, ["JavaScript","SQL"],                "Presencial", "Indicação de um amigo.",   delta_dias=6)
_responder("Mariana Gomes",    "mariana@email.com",  "Backend",     7, 15, [],                                  "Híbrido",    "Quero experiência real.",  delta_dias=4)

# Reprovados (disponibilidade = "Apenas remoto" → eliminação direta)
_responder("Lucas Rodrigues",  "lucas@email.com",    "Backend",     9, 40, ["Python","SQL","Git"],              "Apenas remoto", "Só trabalho remoto.",   delta_dias=11)
_responder("Fernanda Lima",    "fernanda@email.com", "Data Science",8, 35, ["Python","JavaScript"],             "Apenas remoto", "Prefiro remoto.",       delta_dias=3)

# Sem classificação (tecnico < 20)
_responder("Thiago Alves",     "thiago@email.com",   "Frontend",    2, 10, ["JavaScript"],                     "Presencial", "Tentando a sorte.",        delta_dias=2)
_responder("Camila Pires",     "camila@email.com",   "Mobile",      3, 15, [],                                  "Híbrido",    "Gostei da empresa.",       delta_dias=1)

db.commit()
db.close()

print("\nSeed concluído.")
print("Login: admin@formmaster.com / admin123")
