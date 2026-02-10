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
