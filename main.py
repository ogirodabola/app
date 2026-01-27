from fastapi import FastAPI, Request, HTTPException
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from pathlib import Path

from core.database import (
    criar_tabelas,
    listar_noticias,
    listar_hot_news,
    listar_categorias,
    buscar_noticia_por_slug
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
            "categoria_ativa": None
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
def pagina_noticia(request: Request, slug: str):
    noticia = buscar_noticia_por_slug(slug)

    if not noticia:
        raise HTTPException(status_code=404, detail="Notícia não encontrada")

    categorias = listar_categorias()

    return templates.TemplateResponse(
    "noticia.html",
    {
        "request": request,
        "titulo": noticia["titulo"],
        "conteudo": noticia["conteudo_editorial"],
        "imagem": noticia["imagem"],
        "data": noticia["criada_em"],
        "categoria": noticia["categoria"],
        "fonte": noticia["fonte"],
        "categorias": categorias,
        "categoria_ativa": noticia["categoria"]
    }
)
