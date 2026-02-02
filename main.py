from fastapi import FastAPI, Request, HTTPException
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from pathlib import Path

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

BASE_DIR = Path(__file__).resolve().parent

app = FastAPI()

# garante estrutura mínima
criar_tabelas()

# arquivos estáticos
app.mount(
    "/static",
    StaticFiles(directory=BASE_DIR / "static"),
    name="static"
)

templates = Jinja2Templates(directory=BASE_DIR / "templates")

# ======================================================
# HOME
# ======================================================
@app.get("/", response_class=HTMLResponse)
def home(request: Request):

    tabela_completa = buscar_classificacao_brasileirao()

    jogos_do_dia = [
        {
            "liga": "Supercopa do Brasil",
            "hora": "16:00",
            "casa": "Flamengo",
            "fora": "Corinthians",
            "casa_logo": "/static/img/flamengo.png",
            "fora_logo": "/static/img/corinthians.png",
            "gols_casa": 0,
            "gols_fora": 2,
            "link": "#"
        },
        {
            "liga": "La Liga",
            "hora": "10:00",
            "casa": "Real Madrid",
            "fora": "Rayo Vallecano",
            "casa_logo": "/static/img/real.png",
            "fora_logo": "/static/img/rayo.png",
            "gols_casa": 2,
            "gols_fora": 1,
            "link": "#"
        }
        # depois trocamos por API
    ]

    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,

            # topo / feed
            "ultima_hora": listar_ultima_hora(6),
            "ultimas_noticias": listar_ultimas_editoriais(6),

            # bloco brasileirão
            "brasileirao": listar_por_categoria("Brasileirão", limit=4),

            # widget lateral
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
