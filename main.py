from fastapi import FastAPI, Request, HTTPException
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from fastapi.responses import HTMLResponse
from fastapi.requests import Request
from core.database import (
    criar_tabelas,
    listar_ultima_hora,
    listar_brasileirao,
    listar_mercado_bola,
    listar_analises,
    listar_bastidores,
    listar_categorias
)

BASE_DIR = Path(__file__).resolve().parent

app = FastAPI()

criar_tabelas()

app.mount(
    "/static",
    StaticFiles(directory=BASE_DIR / "static"),
    name="static"
)

templates = Jinja2Templates(directory=BASE_DIR / "templates")


@app.get("/")
def home(request: Request):
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,

            "ultima_hora": listar_ultima_hora(8),
            "brasileirao": listar_por_categoria("Brasileirão", 8),
            "mercado": listar_por_categoria("Mercado da Bola", 6),
            "analises": listar_por_categoria("Análises", 5),
            "bastidores": listar_por_categoria("Bastidores", 5),
        }
    )

@app.get("/categoria/{categoria_slug}")
def pagina_categoria(request: Request, categoria_slug: str):
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "hot_news": [],
            "noticias": listar_noticias(limit=50, categoria=categoria_slug),
            "categorias": listar_categorias(),
            "categoria_ativa": categoria_slug
        }
    )


@app.get("/noticia/{slug}", response_class=HTMLResponse)
def noticia(slug: str, request: Request):
    noticia = buscar_noticia_por_slug(slug)

    if not noticia:
        raise HTTPException(status_code=404, detail="Notícia não encontrada")

    return templates.TemplateResponse(
        "noticia.html",
        {
            "request": request,
            "noticia": noticia
        }
    )
