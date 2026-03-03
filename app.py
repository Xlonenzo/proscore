"""PASSA - Passa que resolve.

Marketplace de serviços residenciais com IA.
"""
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from backend.database import init_db
from backend.api.routes import router as api_router
from backend.data.seed import seed_all

app = FastAPI(
    title="PASSA",
    description="Passa que resolve - Marketplace de Serviços com Precificação IA",
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


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/solicitar", response_class=HTMLResponse)
async def pagina_solicitar(request: Request):
    return templates.TemplateResponse("solicitar.html", {"request": request})


@app.get("/profissionais", response_class=HTMLResponse)
async def pagina_profissionais(request: Request):
    return templates.TemplateResponse("profissionais.html", {"request": request})


@app.get("/dashboard", response_class=HTMLResponse)
async def pagina_dashboard(request: Request):
    return templates.TemplateResponse("dashboard.html", {"request": request})


@app.get("/profissional/{profissional_id}", response_class=HTMLResponse)
async def pagina_profissional_detalhe(request: Request, profissional_id: int):
    return templates.TemplateResponse(
        "profissional_detalhe.html",
        {"request": request, "profissional_id": profissional_id},
    )


if __name__ == "__main__":
    import os
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("app:app", host="0.0.0.0", port=port, reload=True)
