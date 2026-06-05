from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from database import Base, motor
from auth.rotas import router as router_auth
from formularios.rotas import router as router_formularios
from respostas.rotas import router as router_respostas
from dashboard.rotas import router as router_dashboard

app = FastAPI(title="FormMaster")

# Cria tabelas automaticamente no SQLite (dev). PostgreSQL usa Alembic.
if str(motor.url).startswith("sqlite"):
    Base.metadata.create_all(bind=motor)

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

app.include_router(router_auth)
app.include_router(router_formularios)
app.include_router(router_respostas)
app.include_router(router_dashboard)
