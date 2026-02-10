from fastapi import FastAPI, Request, HTTPException
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, PlainTextResponse
from pathlib import Path
from core.futebol_api import buscar_jogos_do_dia
from core.database import (
    criar_tabelas,
    listar_ultima_hora,
    listar_por_categoria,
    listar_categorias,
    buscar_noticia_por_slug,
    listar_recomendadas_por_slug,
    listar_ultimas_editoriais,
    buscar_classificacao_brasileirao
)

# ✅ CRIA O APP UMA ÚNICA VEZ
app = FastAPI()

from starlette.middleware.sessions import SessionMiddleware

app.add_middleware(
    SessionMiddleware,
    secret_key="MUDE_ESSA_CHAVE_SUPER_SECRETA"
)

from fastapi.responses import RedirectResponse
from fastapi import Request

def login_required(request: Request):
    if not request.session.get("admin_user"):
        return RedirectResponse("/admin/login", status_code=302)

from fastapi import Form
from fastapi.responses import RedirectResponse
from core.auth import autenticar_usuario

@app.get("/admin/login", response_class=HTMLResponse)
def admin_login(request: Request):
    return templates.TemplateResponse(
        "admin/login.html",
        {"request": request, "erro": None}
    )


@app.post("/admin/login")
def admin_login_post(
    request: Request,
    email: str = Form(...),
    senha: str = Form(...)
):
    user = autenticar_usuario(email, senha)

    if not user:
        return templates.TemplateResponse(
            "admin/login.html",
            {"request": request, "erro": "Credenciais inválidas"}
        )

    request.session["admin_user"] = {
        "id": user["id"],
        "email": user["email"]
    }

    return RedirectResponse("/admin/dashboard", status_code=302)

@app.get("/admin/logout")
def admin_logout(request: Request):
    request.session.clear()
    return RedirectResponse("/admin/login", status_code=302)

@app.get("/admin/dashboard", response_class=HTMLResponse)
def admin_dashboard(request: Request):
    auth = login_required(request)
    if auth:
        return auth

    return templates.TemplateResponse(
        "admin/dashboard.html",
        {
            "request": request,
            "usuario": request.session["admin_user"]
        }
    )

# ✅ ADS.TXT (rota na raiz)
@app.get("/ads.txt", response_class=PlainTextResponse)
def ads_txt():
    return "google.com, pub-6188298652182979, DIRECT, f08c47fec0942fa0"

BASE_DIR = Path(__file__).resolve().parent

# garante estrutura mínima
criar_tabelas()

# arquivos estáticos
app.mount(
    "/static",
    StaticFiles(directory=BASE_DIR / "static"),
    name="static"
)

templates = Jinja2Templates(directory=BASE_DIR / "templates")

from core.ads import render_ad
templates.env.globals["render_ad"] = render_ad

# ======================================================
# HOME
# ======================================================
@app.get("/", response_class=HTMLResponse)
def home(request: Request):

    tabela_completa = buscar_classificacao_brasileirao()

    jogos_do_dia = buscar_jogos_do_dia()  # SOMENTE API, SEM MOCK

    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,

            # topo / feed
            "ultima_hora": listar_ultima_hora(6),
            "ultimas_noticias": listar_ultimas_editoriais(6),

            # bloco brasileirão
            "brasileirao": listar_por_categoria("Brasileirão", limit=4),

            # widgets
            "tabela_brasileirao": tabela_completa[:8],
            "jogos_do_dia": jogos_do_dia,

            # navegação
            "categorias": listar_categorias(),
            "categoria_ativa": None
        }
    )


# ======================================================
# CLASSIFICAÇÃO COMPLETA
# ======================================================
@app.get("/classificacao", response_class=HTMLResponse)
def classificacao(request: Request):

    return templates.TemplateResponse(
        "classificacao.html",
        {
            "request": request,
            "tabela_brasileirao": buscar_classificacao_brasileirao(),
            "categorias": listar_categorias(),
            "categoria_ativa": "Classificação"
        }
    )

# ======================================================
# LISTAGEM POR CATEGORIA
# ======================================================
@app.get("/categoria/{categoria}", response_class=HTMLResponse)
def pagina_categoria(request: Request, categoria: str):

    return templates.TemplateResponse(
        "categoria.html",
        {
            "request": request,
            "categoria": categoria,
            "noticias": listar_por_categoria(categoria, 50),
            "categorias": listar_categorias(),
            "categoria_ativa": categoria
        }
    )

# ======================================================
# NOTÍCIA INDIVIDUAL
# ======================================================
@app.get("/noticia/{slug}", response_class=HTMLResponse)
def noticia(slug: str, request: Request):

    noticia = buscar_noticia_por_slug(slug)

    if not noticia:
        raise HTTPException(status_code=404, detail="Notícia não encontrada")

    recomendadas = listar_recomendadas_por_slug(slug, limit=5) or []

    return templates.TemplateResponse(
        "noticia.html",
        {
            "request": request,
            "noticia": noticia,
            "recomendadas": recomendadas,
            "categorias": listar_categorias(),
            "categoria_ativa": noticia.get("categoria")
        }
    )

# ======================================================
# SOBRE
# ======================================================
@app.get("/sobre", response_class=HTMLResponse)
def sobre(request: Request):
    return templates.TemplateResponse(
        "sobre.html",
        {
            "request": request,
            "categorias": listar_categorias(),
            "categoria_ativa": None
        }
    )

# ======================================================
# POLÍTICA EDITORIAL
# ======================================================
@app.get("/politica-editorial", response_class=HTMLResponse)
def politica_editorial(request: Request):
    return templates.TemplateResponse(
        "politica-editorial.html",
        {
            "request": request,
            "categorias": listar_categorias(),
            "categoria_ativa": None
        }
    )

# ======================================================
# POLÍTICA DE PRIVACIDADE
# ======================================================
@app.get("/privacidade", response_class=HTMLResponse)
def politica_privacidade(request: Request):
    return templates.TemplateResponse(
        "privacidade.html",
        {
            "request": request,
            "categorias": listar_categorias(),
            "categoria_ativa": None
        }
    )

# ======================================================
# TERMOS DE USO
# ======================================================
@app.get("/termos", response_class=HTMLResponse)
def termos(request: Request):
    return templates.TemplateResponse(
        "termos.html",
        {
            "request": request,
            "categorias": listar_categorias(),
            "categoria_ativa": None
        }
    )

# ======================================================
# ANUNCIE CONOSCO
# ======================================================
@app.get("/anuncie", response_class=HTMLResponse)
def anuncie(request: Request):
    return templates.TemplateResponse(
        "anuncie.html",
        {
            "request": request,
            "categorias": listar_categorias(),
            "categoria_ativa": None
        }
    )

from core.database import (
    listar_ads_slots,
    buscar_ads_slot,
    salvar_ads_script,
    atualizar_ads_slot_status
)

@app.get("/admin/ads", response_class=HTMLResponse)
def admin_ads(request: Request):
    auth = login_required(request)
    if auth:
        return auth

    slots = listar_ads_slots()

    return templates.TemplateResponse(
        "admin/ads_list.html",
        {
            "request": request,
            "slots": slots
        }
    )

@app.get("/admin/ads/{slot_id}", response_class=HTMLResponse)
def admin_ads_edit(slot_id: int, request: Request):
    auth = login_required(request)
    if auth:
        return auth

    slot = buscar_ads_slot(slot_id)

    if not slot:
        raise HTTPException(status_code=404, detail="Slot não encontrado")

    return templates.TemplateResponse(
        "admin/ads_edit.html",
        {
            "request": request,
            "slot": slot
        }
    )

@app.post("/admin/ads/{slot_id}")
def admin_ads_save(
    slot_id: int,
    request: Request,
    codigo: str = Form(...),
    ativo: bool = Form(False),
    dispositivo: str = Form("all")
):
    auth = login_required(request)
    if auth:
        return auth

    salvar_ads_script(slot_id, codigo, ativo)
    atualizar_ads_slot_dispositivo(slot_id, dispositivo)

    return RedirectResponse("/admin/ads", status_code=302)
302)
