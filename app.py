"""PASSA - Passa que resolve.

Marketplace de servicos residenciais com IA.
"""
from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, Request, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from backend.database import init_db, get_db
from backend.api.routes import router as api_router
from backend.api.admin_routes import admin_router
from backend.data.seed import seed_all
from backend.auth import get_optional_user, get_admin_user

app = FastAPI(
    title="PASSA",
    description="Passa que resolve - Marketplace de Servicos com Precificacao IA",
    version="1.0.0",
)

# CORS — permite o app mobile acessar a API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static files & templates
app.mount("/static", StaticFiles(directory="frontend/static"), name="static")
import os
if os.path.isdir("media"):
    app.mount("/media", StaticFiles(directory="media"), name="media")
templates = Jinja2Templates(directory="frontend/templates")

# API routes
app.include_router(api_router)
app.include_router(admin_router)


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
    ctx = _ctx(request, db)
    if not ctx["usuario"]:
        return RedirectResponse(url="/login", status_code=302)
    return templates.TemplateResponse("dashboard.html", ctx)


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


# ======== Admin Pages ========


def _admin_ctx(request: Request, db: Session, active_tab: str):
    """Build admin template context, redirecting non-admins."""
    usuario = get_optional_user(request, db)
    if not usuario or not usuario.is_admin:
        return None
    return {"request": request, "usuario": usuario, "active_tab": active_tab}


@app.get("/admin", response_class=HTMLResponse)
async def admin_dashboard(request: Request, db: Session = Depends(get_db)):
    ctx = _admin_ctx(request, db, "dashboard")
    if not ctx:
        return RedirectResponse(url="/login", status_code=302)
    return templates.TemplateResponse("admin_dashboard.html", ctx)


@app.get("/admin/usuarios", response_class=HTMLResponse)
async def admin_usuarios(request: Request, db: Session = Depends(get_db)):
    ctx = _admin_ctx(request, db, "usuarios")
    if not ctx:
        return RedirectResponse(url="/login", status_code=302)
    return templates.TemplateResponse("admin_usuarios.html", ctx)


@app.get("/admin/solicitacoes", response_class=HTMLResponse)
async def admin_solicitacoes(request: Request, db: Session = Depends(get_db)):
    ctx = _admin_ctx(request, db, "solicitacoes")
    if not ctx:
        return RedirectResponse(url="/login", status_code=302)
    return templates.TemplateResponse("admin_solicitacoes.html", ctx)


@app.get("/admin/prestadores/lista", response_class=HTMLResponse)
async def admin_prestadores_lista(request: Request, db: Session = Depends(get_db)):
    ctx = _admin_ctx(request, db, "prestadores_lista")
    if not ctx:
        return RedirectResponse(url="/login", status_code=302)
    return templates.TemplateResponse("admin_prestadores_lista.html", ctx)


@app.get("/admin/prestadores", response_class=HTMLResponse)
async def admin_prestadores(request: Request, db: Session = Depends(get_db)):
    ctx = _admin_ctx(request, db, "prestadores")
    if not ctx:
        return RedirectResponse(url="/login", status_code=302)
    return templates.TemplateResponse("admin_prestadores.html", ctx)


@app.get("/admin/analytics", response_class=HTMLResponse)
async def admin_analytics(request: Request, db: Session = Depends(get_db)):
    ctx = _admin_ctx(request, db, "analytics")
    if not ctx:
        return RedirectResponse(url="/login", status_code=302)
    return templates.TemplateResponse("admin_analytics.html", ctx)


if __name__ == "__main__":
    import os
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("app:app", host="0.0.0.0", port=port, reload=True)
