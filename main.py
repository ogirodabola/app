from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from fastapi import HTTPException
from core.database import buscar_noticia_por_slug
from core.database import (
    criar_tabelas,
    listar_noticias,
    listar_hot_news,
    listar_categorias
)

BASE_DIR = Path(__file__).resolve().parent

app = FastAPI()

# garante que o banco e as tabelas existam
criar_tabelas()

app.mount(
    "/static",
    StaticFiles(directory=BASE_DIR / "static"),
    name="static"
)

templates = Jinja2Templates(directory=BASE_DIR / "templates")

@app.get("/")
def home(request: Request):
    hot_news = listar_hot_news(horas=3, limit=24)
    noticias = listar_noticias(limit=30)
    categorias = listar_categorias()

    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "hot_news": hot_news,
            "noticias": noticias,
            "categorias": categorias,
            "categoria_ativa": categoria
        }
    )


@app.get("/categoria/{categoria}")
def categoria(request: Request, categoria: str):
    noticias = listar_noticias(limit=50, categoria=categoria)
    categorias = listar_categorias()

    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "hot_news": [],
            "noticias": noticias,
            "categorias": categorias,
            "categoria_ativa": categoria
        }
    )
@app.get("/noticia/{slug}")
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
