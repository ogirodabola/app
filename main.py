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
    listar_recomendadas_por_slug
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


# ======================================================
# HOME
# ======================================================
@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,

            # blocos principais
            "ultima_hora": listar_ultima_hora(8),
            "brasileirao": listar_por_categoria("Brasileirão", 8),
            "mercado": listar_por_categoria("Mercado da Bola", 6),
            "analises": listar_por_categoria("Análises", 5),
            "bastidores": listar_por_categoria("Bastidores", 5),

            # navegação
            "categorias": listar_categorias(),
            "categoria_ativa": None
        }
    )


# ======================================================
# LISTAGEM POR CATEGORIA
# ======================================================
@app.get("/categoria/{categoria}", response_class=HTMLResponse)
def pagina_categoria(categoria: str, request: Request):
    noticias = listar_por_categoria(categoria)

    return templates.TemplateResponse(
        "categoria.html",
        {
            "request": request,
            "categoria": categoria,
            "noticias": noticias,
            "categorias": listar_categorias(),
            "categoria_ativa": categoria,
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

    recomendadas = listar_recomendadas_por_slug(slug, limit=5)

    return templates.TemplateResponse(
        "noticia.html",
        {
            "request": request,
            "noticia": noticia,
            "recomendadas": recomendadas
        }
    )

/* ======================================================
GRID DE CARDS – HOME
====================================================== */
.cards-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 24px;
}

/* Tablet */
@media (max-width: 1024px) {
  .cards-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

/* Mobile */
@media (max-width: 640px) {
  .cards-grid {
    grid-template-columns: 1fr;
  }
}

/* ======================================================
CARD
====================================================== */
.card {
  display: block;
  background: rgba(255,255,255,0.04);
  border-radius: 14px;
  overflow: hidden;
  text-decoration: none;
  color: inherit;
  transition: transform 0.25s ease, box-shadow 0.25s ease;
}

.card:hover {
  transform: translateY(-4px);
  box-shadow: 0 20px 40px rgba(0,0,0,0.45);
}

.card-image {
  height: 180px;
  overflow: hidden;
}

.card-image img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.card-body {
  padding: 20px;
}

.card-title {
  margin: 12px 0;
  font-size: 16px;
  font-weight: 600;
  line-height: 1.3;
}

.card-meta {
  font-size: 12px;
  color: #9ca3af;
}
