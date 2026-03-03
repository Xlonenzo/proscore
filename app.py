"""PASSA - Passa que resolve.

Marketplace de servicos residenciais com IA.
"""
from fastapi import FastAPI, Request, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from backend.database import init_db, get_db
from backend.api.routes import router as api_router
from backend.data.seed import seed_all
from backend.auth import get_optional_user

app = FastAPI(
    title="PASSA",
    description="Passa que resolve - Marketplace de Servicos com Precificacao IA",
    version="1.0.0",
)

# Static files & templates
app.mount("/static", StaticFiles(directory="frontend/static"), name="static")
templates = Jinja2Templates(directory="frontend/templates")

# API routes
app.include_router(api_router)


@app.on_event("startup")
def startup():
    init_db()
    seed_all()


# ======== Pages ========


def _ctx(request: Request, db: Session, **extra):
    """Build template context with optional auth user."""
    usuario = get_optional_user(request, db)
    ctx = {"request": request, "usuario": usuario}
    ctx.update(extra)
    return ctx


@app.get("/", response_class=HTMLResponse)
async def home(request: Request, db: Session = Depends(get_db)):
    return templates.TemplateResponse("index.html", _ctx(request, db))


@app.get("/solicitar", response_class=HTMLResponse)
async def pagina_solicitar(request: Request, db: Session = Depends(get_db)):
    return templates.TemplateResponse("solicitar.html", _ctx(request, db))


@app.get("/profissionais", response_class=HTMLResponse)
async def pagina_profissionais(request: Request, db: Session = Depends(get_db)):
    return templates.TemplateResponse("profissionais.html", _ctx(request, db))


@app.get("/dashboard", response_class=HTMLResponse)
async def pagina_dashboard(request: Request, db: Session = Depends(get_db)):
    return templates.TemplateResponse("dashboard.html", _ctx(request, db))


@app.get("/profissional/{profissional_id}", response_class=HTMLResponse)
async def pagina_profissional_detalhe(
    request: Request, profissional_id: int, db: Session = Depends(get_db)
):
    return templates.TemplateResponse(
        "profissional_detalhe.html",
        _ctx(request, db, profissional_id=profissional_id),
    )


@app.get("/login", response_class=HTMLResponse)
async def pagina_login(request: Request, db: Session = Depends(get_db)):
    return templates.TemplateResponse("login.html", _ctx(request, db))


@app.get("/cadastro/cliente", response_class=HTMLResponse)
async def pagina_cadastro_cliente(request: Request, db: Session = Depends(get_db)):
    return templates.TemplateResponse("cadastro_cliente.html", _ctx(request, db))


@app.get("/cadastro/prestador", response_class=HTMLResponse)
async def pagina_cadastro_prestador(request: Request, db: Session = Depends(get_db)):
    return templates.TemplateResponse("cadastro_prestador.html", _ctx(request, db))


if __name__ == "__main__":
    import os
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("app:app", host="0.0.0.0", port=port, reload=True)
