from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from core.database import criar_tabelas
from core.database import listar_noticias, listar_categorias
from crawler.crawler_noticias import rodar_crawler

@app.get("/_run-crawler")
def run_crawler():
    rodar_crawler()
    return {"status": "crawler executado"}

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
def home(request: Request, categoria: str = None):
    noticias = listar_noticias(limit=30, categoria=categoria)
    categorias = listar_categorias()

    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "noticias": noticias,
            "categorias": categorias,
            "categoria_ativa": categoria
        }
    )
