from fastapi import FastAPI, Request, HTTPException
from fastapi import UploadFile, File
import shutil
import os
from slugify import slugify
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, PlainTextResponse
from pathlib import Path
from core.futebol_api import buscar_jogos_do_dia
from fastapi.responses import HTMLResponse
from core.database import listar_noticias_admin
from core.database import atualizar_ads_slot_dispositivo
from core.database import obter_metricas_editoriais
from core.database import (
    criar_tabelas,
    listar_ultima_hora,
    listar_por_categoria,
    listar_categorias,
    buscar_noticia_por_slug,
    listar_recomendadas_por_slug,
    listar_ultimas_editoriais,
    buscar_classificacao_brasileirao,
    listar_noticias,
    buscar_noticia_admin,
    criar_noticia,
    atualizar_noticia,
    listar_categorias,
    listar_ultima_hora_publicada,
    listar_editorial_publicado
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

from fastapi import Request
from fastapi.responses import RedirectResponse

from slugify import slugify

from slugify import slugify

@app.post("/admin/noticias/{id}")
async def salvar_noticia_admin(id: int, request: Request):
    form = await request.form()

    titulo = form.get("titulo_editorial")
    slug_form = form.get("slug")

    if not slug_form or slug_form.strip() == "":
        slug = slugify(titulo)
    else:
        slug = slugify(slug_form)

    dados = {
        "titulo_editorial": titulo,
        "resumo": form.get("resumo"),
        "conteudo_editorial": form.get("conteudo_editorial"),
        "imagem": form.get("imagem"),
        "categoria": form.get("categoria"),
        "tags": [t.strip() for t in form.get("tags", "").split(",") if t.strip()],
        "editorial_status": form.get("editorial_status", "pendente"),
        "slug": slug,
    }

    atualizar_noticia(id, dados)

    return RedirectResponse("/admin/noticias", status_code=303)


@app.get("/admin/logout")
def admin_logout(request: Request):
    request.session.clear()
    return RedirectResponse("/admin/login", status_code=302)

@app.get("/admin/dashboard", response_class=HTMLResponse)
def admin_dashboard(request: Request):
    auth = login_required(request)
    if auth:
        return auth

    metricas = obter_metricas_editoriais()

    return templates.TemplateResponse(
        "admin/dashboard.html",
        {
            "request": request,
            "usuario": request.session["admin_user"],
            "metricas": metricas
        }
    )

# ✅ ADS.TXT (rota na raiz)
@app.get("/ads.txt", response_class=PlainTextResponse)
def ads_txt():
    return "google.com, pub-6188298652182979, DIRECT, f08c47fec0942fa0"

BASE_DIR = Path(__file__).resolve().parent

# 🔥 GARANTE PASTA DE UPLOAD
UPLOAD_DIR = BASE_DIR / "static" / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

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

from core.database import listar_noticias_publicadas

@app.get("/", response_class=HTMLResponse)
def home(request: Request):

    tabela_completa = buscar_classificacao_brasileirao()
    jogos_do_dia = buscar_jogos_do_dia()

    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,

            # blocos editoriais (CMS manda)
            "ultima_hora": listar_ultima_hora_publicada(limit=6),
            "ultimas_noticias": listar_editorial_publicado(limit=6),


            # bloco esportivo específico
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
    atualizar_ads_slot_status,
    atualizar_ads_slot_dispositivo
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
    ativo: str = Form(None),
    dispositivo: str = Form("all")
):
    auth = login_required(request)
    if auth:
        return auth

    ativo_bool = True if ativo == "on" else False

    salvar_ads_script(slot_id, codigo, ativo_bool)
    atualizar_ads_slot_dispositivo(slot_id, dispositivo)

    return RedirectResponse("/admin/ads", status_code=302)

@app.get("/admin/ads/{slot_id}/preview", response_class=HTMLResponse)
def admin_ads_preview(slot_id: int, request: Request):
    auth = login_required(request)
    if auth:
        return auth

    slot = buscar_ads_slot(slot_id)
    if not slot:
        raise HTTPException(status_code=404, detail="Slot não encontrado")

    return templates.TemplateResponse(
        "admin/ads_preview.html",
        {
            "request": request,
            "slot": slot
        }
    )


@app.get("/admin/noticias/nova", response_class=HTMLResponse)
def admin_noticia_nova(request: Request):
    auth = login_required(request)
    if auth:
        return auth

    categorias = listar_categorias()

    return templates.TemplateResponse(
        "admin/noticias_edit.html",
        {
            "request": request,
            "noticia": None,
            "categorias": categorias
        }
    )

@app.post("/admin/noticias/nova")
async def admin_noticia_criar(
    request: Request,
    titulo_editorial: str = Form(...),
    slug: str = Form(""),
    resumo: str = Form(""),
    conteudo_editorial: str = Form(""),
    categoria: str = Form(""),
    tags: str = Form(""),
    editorial_status: str = Form("pendente"),
    imagem_file: UploadFile = File(None)
):
    auth = login_required(request)
    if auth:
        return auth

    slug_final = slugify(slug if slug else titulo_editorial)

    imagem_url = None

    if imagem_file and imagem_file.filename:
        filename = f"{slug_final}-{imagem_file.filename}"
        filepath = UPLOAD_DIR / filename

        with open(filepath, "wb") as buffer:
            shutil.copyfileobj(imagem_file.file, buffer)

        imagem_url = f"/static/uploads/{filename}"

    criar_noticia({
        "titulo_editorial": titulo_editorial,
        "resumo": resumo,
        "conteudo_editorial": conteudo_editorial,
        "imagem": imagem_url,
        "categoria": categoria,
        "tags": [t.strip() for t in tags.split(",") if t.strip()],
        "editorial_status": editorial_status,
        "slug": slug_final
    })

    return RedirectResponse("/admin/noticias", status_code=302)

@app.get("/admin/noticias/{noticia_id}", response_class=HTMLResponse)
def admin_noticia_editar(noticia_id: int, request: Request):
    auth = login_required(request)
    if auth:
        return auth

    noticia = buscar_noticia_admin(noticia_id)
    categorias = listar_categorias()

    return templates.TemplateResponse(
        "admin/noticias_edit.html",
        {
            "request": request,
            "noticia": noticia,
            "categorias": categorias
        }
    )

@app.post("/admin/noticias/{noticia_id}")
async def admin_noticia_atualizar(
    noticia_id: int,
    request: Request,
    titulo_editorial: str = Form(...),
    slug: str = Form(""),
    resumo: str = Form(""),
    conteudo_editorial: str = Form(""),
    categoria: str = Form(""),
    tags: str = Form(""),
    editorial_status: str = Form("pendente"),
    imagem_file: UploadFile = File(None)
):
    auth = login_required(request)
    if auth:
        return auth

    slug_final = slugify(slug if slug else titulo_editorial)

    imagem_url = None

    if imagem_file and imagem_file.filename:
        filename = f"{slug_final}-{imagem_file.filename}"
        filepath = UPLOAD_DIR / filename

        with open(filepath, "wb") as buffer:
            shutil.copyfileobj(imagem_file.file, buffer)

        imagem_url = f"/static/uploads/{filename}"

    else:
        noticia_existente = buscar_noticia_admin(noticia_id)
        imagem_url = noticia_existente["imagem"]

    atualizar_noticia(noticia_id, {
        "titulo_editorial": titulo_editorial,
        "resumo": resumo,
        "conteudo_editorial": conteudo_editorial,
        "imagem": imagem_url,
        "categoria": categoria,
        "tags": [t.strip() for t in tags.split(",") if t.strip()],
        "editorial_status": editorial_status,
        "slug": slug_final
    })

    return RedirectResponse("/admin/noticias", status_code=302)

@app.get("/admin/noticias")
def listar_noticias_view(
    request: Request,
    busca: str | None = None,
    status: str | None = None,
    categoria: str | None = None
):
    noticias = listar_noticias_admin(
        status=status,
        categoria=categoria,
        busca=busca
    )

    return templates.TemplateResponse(
        "admin/noticias_list.html",
        {
            "request": request,
            "noticias": noticias,
            "busca": busca,
            "status": status,
            "categoria": categoria,
        }
    )
