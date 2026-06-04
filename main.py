from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from auth.rotas import router as router_auth
from formularios.rotas import router as router_formularios
from respostas.rotas import router as router_respostas
from dashboard.rotas import router as router_dashboard

app = FastAPI(title="FormMaster")

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

app.include_router(router_auth)
app.include_router(router_formularios)
app.include_router(router_respostas)
app.include_router(router_dashboard)
