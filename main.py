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
    listar_ultimas_editoriais
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
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
             "ultimas_noticias": listar_ultimas_editoriais(5),
            "ultima_hora": listar_ultima_hora(6),
            "categorias": listar_categorias(),
            "categoria_ativa": None
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
            "recomendadas": recomendadas
        }
    )
