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
from core.database import listar_jogadores_por_noticia
from core.database import buscar_ou_criar_jogador
from core.futebol_api import buscar_jogador_na_api
from core.services.r2 import upload_noticia_image
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
    listar_editorial_publicado,
    listar_noticias_publicadas,
    buscar_ou_criar_jogador,
    limpar_vinculos_jogadores_noticia,
    buscar_jogador_por_slug,
    criar_jogador_basico,
    vincular_jogador_noticia,
    listar_noticias_por_jogador,
    buscar_time_por_slug,
    inserir_time,
    listar_midias,
    inserir_midia
)


# ✅ CRIA O APP UMA ÚNICA VEZ
app = FastAPI()

# ✅ MONTA ARQUIVOS ESTÁTICOS
app.mount("/static", StaticFiles(directory="static"), name="static")

from starlette.middleware.sessions import SessionMiddleware

app.add_middleware(
    SessionMiddleware,
    secret_key="MUDE_ESSA_CHAVE_SUPER_SECRETA"
)

import json

def gerar_breadcrumb_schema(itens):
    """
    itens = lista de tuplas:
    [
        ("Home", "https://girodesportivo.com/"),
        ("Brasileirão 2026", "https://girodesportivo.com/brasileirao-2026")
    ]
    """

    data = {
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": []
    }

    for index, (nome, url) in enumerate(itens, start=1):
        data["itemListElement"].append({
            "@type": "ListItem",
            "position": index,
            "name": nome,
            "item": url
        })

    return json.dumps(data, ensure_ascii=False)

def normalizar_slug_categoria(categoria: str) -> str:
    return slugify(categoria)

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
async def admin_noticia_criar(request: Request):

    auth = login_required(request)
    if auth:
        return auth

    form = await request.form()

    titulo_editorial = form.get("titulo_editorial")
    slug_input = form.get("slug")
    resumo = form.get("resumo")
    conteudo_editorial = form.get("conteudo_editorial")
    categoria = form.get("categoria")
    tags = form.get("tags", "")
    editorial_status = form.get("editorial_status", "pendente")

    # =========================
    # 🔥 CAPTURAR AUTOR DA SESSÃO
    # =========================
    usuario = request.session.get("user")

    if not usuario:
        # fallback de segurança
        autor_id = 1
    else:
        autor_id = usuario.get("autor_id") or 1

    # =========================
    # 🔥 CAMPOS SEO
    # =========================
    meta_title = form.get("meta_title")
    meta_description = form.get("meta_description")
    canonical_url = form.get("canonical_url")
    palavra_chave_principal = form.get("palavra_chave_principal")
    indexar = True if form.get("indexar") == "true" else False

    # =========================
    # SLUG
    # =========================
    slug_final = slugify(slug_input if slug_input else titulo_editorial)

    # =========================
    # IMAGEM (R2)
    # =========================
    imagem_file = form.get("imagem_file")
    imagem_url = None
    
    if imagem_file and imagem_file.filename:
        imagem_url = upload_noticia_image(
            file=imagem_file.file,
            filename=imagem_file.filename
        )

    # =========================
    # SALVAR NO BANCO
    # =========================
    criar_noticia({
        "titulo": titulo_editorial,
        "titulo_editorial": titulo_editorial,
        "resumo": resumo,
        "conteudo_editorial": conteudo_editorial,
        "imagem": imagem_url,
        "categoria": categoria,
        "tags": [t.strip() for t in tags.split(",") if t.strip()],
        "editorial_status": editorial_status,
        "slug": slug_final,
        "autor_id": autor_id,  # 🔥 AGORA VAI SALVAR CORRETAMENTE

        # 🔥 SEO
        "meta_title": meta_title,
        "meta_description": meta_description,
        "canonical_url": canonical_url,
        "palavra_chave_principal": palavra_chave_principal,
        "indexar": indexar
    })

    return RedirectResponse("/admin/noticias", status_code=302)

from slugify import slugify
from fastapi.responses import RedirectResponse
from core.database import buscar_ou_criar_jogador
from fastapi import UploadFile
from uuid import uuid4
import os
import shutil

@app.post("/admin/noticias/{id}")
async def salvar_noticia_admin(id: int, request: Request):

    form = await request.form()

    titulo = form.get("titulo_editorial")
    slug_form = form.get("slug")

    slug = slugify(slug_form if slug_form else titulo)

    # =============================
    # 🔥 CAMPOS SEO
    # =============================

    meta_title = form.get("meta_title")
    meta_description = form.get("meta_description")
    canonical_url = form.get("canonical_url")
    palavra_chave_principal = form.get("palavra_chave_principal")
    indexar = True if form.get("indexar") == "true" else False

    # =============================
    # 1️⃣ TRATAR IMAGEM
    # =============================

    imagem_atual = form.get("imagem_atual")
    file: UploadFile = form.get("imagem_file")

    imagem_url = imagem_atual

    if file and file.filename:
        ext = file.filename.split(".")[-1]
        nome_arquivo = f"{uuid4().hex}.{ext}"

        pasta_upload = "static/uploads"
        os.makedirs(pasta_upload, exist_ok=True)

        caminho = f"{pasta_upload}/{nome_arquivo}"

        with open(caminho, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        imagem_url = f"/{caminho}"

    # =============================
    # 2️⃣ DADOS DA NOTÍCIA
    # =============================

    dados = {
        "titulo_editorial": titulo,
        "resumo": form.get("resumo"),
        "conteudo_editorial": form.get("conteudo_editorial"),
        "imagem": imagem_url,
        "categoria": form.get("categoria"),
        "tags": [t.strip() for t in form.get("tags", "").split(",") if t.strip()],
        "editorial_status": form.get("editorial_status", "pendente"),
        "slug": slug,

        # 🔥 SEO
        "meta_title": meta_title,
        "meta_description": meta_description,
        "canonical_url": canonical_url,
        "palavra_chave_principal": palavra_chave_principal,
        "indexar": indexar
    }

    atualizar_noticia(id, dados)

    return RedirectResponse("/admin/noticias", status_code=303)

    # =============================
    # 3️⃣ PROCESSAR JOGADORES
    # =============================

    jogadores_raw = form.get("jogador_nome", "") or ""
    nomes_jogadores = [j.strip() for j in jogadores_raw.split(",") if j.strip()]

    limpar_vinculos_jogadores_noticia(id)

    from core.database import buscar_ou_criar_jogador
    from core.database import vincular_jogador_noticia

    for nome in nomes_jogadores:

        slug_jogador = slugify(nome)
        jogador = buscar_ou_criar_jogador(slug_jogador)

        if jogador:
            vincular_jogador_noticia(id, jogador["id"])

    return RedirectResponse("/admin/noticias", status_code=303)

    # ============================================
    # VINCULAR JOGADOR À NOTÍCIA (SISTEMA HÍBRIDO)
    # ============================================

    jogador_nome = form.get("jogador_nome")

    if jogador_nome and jogador_nome.strip():

        from core.database import buscar_ou_criar_jogador
        from core.database import vincular_jogador_noticia

        nomes = [j.strip() for j in jogador_nome.split(",") if j.strip()]

        for nome in nomes:

            slug_jogador = slugify(nome)

            jogador = buscar_ou_criar_jogador (slug_jogador)

            if jogador:
                vincular_jogador_noticia(id, jogador["id"])

    return RedirectResponse("/admin/noticias", status_code=303)

@app.get("/admin/logout")
def admin_logout(request: Request):
    request.session.clear()
    return RedirectResponse("/admin/login", status_code=302)

from core.database import dashboard_status_por_fonte
from core.database import obter_metricas_editoriais  # se existir

@app.get("/admin/dashboard", response_class=HTMLResponse)
def admin_dashboard(request: Request):
    auth = login_required(request)
    if auth:
        return auth

    metricas = obter_metricas_editoriais()
    stats = dashboard_status_por_fonte()

    return templates.TemplateResponse(
        "admin/dashboard.html",
        {
            "request": request,
            "usuario": request.session["admin_user"],
            "metricas": metricas,
            "stats_por_fonte": stats
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
templates.env.filters["slugify"] = slugify

from core.ads import render_ad
templates.env.globals["render_ad"] = render_ad

# ======================================================
# HOME
# ======================================================
from core.database import (
    listar_home_hero,
    listar_home_feed,
    listar_home_brasileirao,
    listar_home_mercado,
    listar_home_internacional,
    listar_home_analises,
    listar_home_bastidores,
    listar_home_mais_lidas,
)

@app.get("/", response_class=HTMLResponse)
def home(request: Request):

    hero = listar_home_hero() or []
    feed = listar_home_feed(limit=20) or []

    brasileirao = listar_home_brasileirao() or []
    mercado = listar_home_mercado() or []
    internacional = listar_home_internacional() or []
    analises = listar_home_analises() or []
    bastidores = listar_home_bastidores() or []
    mais_lidas = listar_home_mais_lidas() or []

    tabela_completa = buscar_classificacao_brasileirao() or []
    jogos_do_dia = buscar_jogos_do_dia() or []

    categorias = listar_categorias() or []

    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,

            "hero_principal": hero[0] if hero else None,
            "hero_secundarias": hero[1:] if len(hero) > 1 else [],

            "feed_noticias": feed,

            "brasileirao": brasileirao,
            "mercado": mercado,
            "internacional": internacional,
            "analises": analises,
            "bastidores": bastidores,
            "mais_lidas": mais_lidas,

            "tabela_brasileirao": tabela_completa[:8],
            "jogos_do_dia": jogos_do_dia,

            "categorias": categorias,
            "categoria_ativa": None
        }
    )


# ======================================================
# CLASSIFICAÇÃO COMPLETA
# ======================================================
@app.get("/classificacao-brasileirao-2026", response_class=HTMLResponse)
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
@app.get("/categoria/{categoria_slug}", response_class=HTMLResponse)
def pagina_categoria(request: Request, categoria_slug: str):

    categorias = listar_categorias()

    categoria_real = None

    for c in categorias:
        if slugify(c) == categoria_slug:
            categoria_real = c
            break

    if not categoria_real:
        raise HTTPException(status_code=404, detail="Categoria não encontrada")

    noticias = listar_por_categoria(categoria_real, 50)

    return templates.TemplateResponse(
        "categoria.html",
        {
            "request": request,
            "categoria": categoria_real,
            "noticias": noticias,
            "categorias": categorias,
            "categoria_ativa": categoria_real
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

    # =============================
    # JOGADORES RELACIONADOS
    # =============================

    jogadores_relacionados = listar_jogadores_por_noticia(noticia["id"]) or []

    # =============================
    # RECOMENDADAS
    # =============================

    recomendadas = listar_recomendadas_por_slug(slug, limit=5) or []

    # =============================
    # RELACIONADAS POR JOGADOR
    # =============================

    noticias_relacionadas = []

    for jogador in jogadores_relacionados:

        relacionadas = listar_noticias_por_jogador(
            jogador["id"],
            limit=3
        ) or []

        for n in relacionadas:
            if n["slug"] != slug:
                noticias_relacionadas.append(n)

    # remover duplicadas
    noticias_relacionadas = {
        n["id"]: n for n in noticias_relacionadas
    }.values()

    noticias_relacionadas = list(noticias_relacionadas)[:6]

    # =============================
    # BREADCRUMB
    # =============================

    categoria_nome = noticia.get("categoria") or "geral"

    breadcrumb = gerar_breadcrumb_schema([
        ("Home", "https://girodesportivo.com/"),
        (
            categoria_nome,
            f"https://girodesportivo.com/categoria/{slugify(categoria_nome)}"
        ),
        (
            noticia.get("titulo_editorial") or noticia.get("titulo"),
            f"https://girodesportivo.com/noticia/{slug}"
        )
    ])

    return templates.TemplateResponse(
        "noticia.html",
        {
            "request": request,
            "noticia": noticia,
            "recomendadas": recomendadas,
            "noticias_relacionadas": noticias_relacionadas,
            "breadcrumb_schema": breadcrumb,
            "categorias": listar_categorias(),
            "jogadores_relacionados": jogadores_relacionados,
            "categoria_ativa": categoria_nome
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

@app.get("/admin/noticias/{noticia_id}")
def admin_noticia_editar(noticia_id: int, request: Request):

    auth = login_required(request)
    if auth:
        return auth

    noticia = buscar_noticia_admin(noticia_id)

    if not noticia:
        raise HTTPException(status_code=404, detail="Notícia não encontrada")

    # ============================
    # 🔥 BUSCAR JOGADORES RELACIONADOS
    # ============================

    jogadores = listar_jogadores_por_noticia(noticia_id)

    nomes_jogadores = ", ".join(
        [j["nome"] for j in jogadores]
    ) if jogadores else ""

    return templates.TemplateResponse(
        "admin/noticias_edit.html",
        {
            "request": request,
            "noticia": noticia,
            "categorias": listar_categorias(),
            "jogador_nome": nomes_jogadores
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
    imagem_file: UploadFile = File(None),
    jogador_nome: str = Form("")
):

    auth = login_required(request)
    if auth:
        return auth

    # 🔥 Aqui sim você pode usar form
    form = await request.form()

    # =========================
    # 🔥 CAMPOS SEO
    # =========================
    meta_title = form.get("meta_title")
    meta_description = form.get("meta_description")
    canonical_url = form.get("canonical_url")
    palavra_chave_principal = form.get("palavra_chave_principal")
    indexar = True if form.get("indexar") == "true" else False

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
        "slug": slug_final,

    # 🔥 SEO
        "meta_title": meta_title,
        "meta_description": meta_description,
        "canonical_url": canonical_url,
        "palavra_chave_principal": palavra_chave_principal,
        "indexar": indexar
    })

    # ============================
    # 🔥 PROCESSAR JOGADORES
    # ============================

    form = await request.form()
    jogadores_raw = form.get("jogador_nome", "") or ""
    nomes_jogadores = [j.strip() for j in jogadores_raw.split(",") if j.strip()]

    limpar_vinculos_jogadores_noticia(noticia_id)

    for nome in nomes_jogadores:
        slug_jogador = slugify(nome)
        jogador = buscar_ou_criar_jogador(slug_jogador)

        if jogador:
            vincular_jogador_noticia(noticia_id, jogador["id"])

    return RedirectResponse("/admin/noticias", status_code=302)


@app.get("/admin/noticias")
def listar_noticias_view(
    request: Request,
    busca: str | None = None,
    status: str | None = None,
    categoria: str | None = None,
    fonte: str | None = None
):
    noticias = listar_noticias_admin(
        status=status,
        categoria=categoria,
        busca=busca,
        fonte=fonte
    )

    return templates.TemplateResponse(
        "admin/noticias_list.html",
        {
            "request": request,
            "noticias": noticias,
            "busca": busca,
            "status": status,
            "categoria": categoria,
            "fonte": fonte
        }
    )

# ======================================================
# ROBOTS
# ======================================================

@app.get("/robots.txt", response_class=PlainTextResponse)
def robots():
    return """
User-agent: *
Allow: /

Sitemap: https://girodesportivo.com/sitemap.xml
Sitemap: https://girodesportivo.com/sitemap-news.xml

"""

from fastapi.responses import Response
from datetime import datetime
import html

@app.get("/sitemap.xml", response_class=Response)
def sitemap():

    try:
        noticias = listar_noticias_publicadas(limit=5000)
        print("Noticias no sitemap:", len(noticias))
        print("Primeira noticia:", noticias[0] if noticias else "Vazio")
    except Exception as e:
        print("Erro ao buscar notícias:", e)
        noticias = []

    try:
        categorias = listar_categorias()
    except Exception as e:
        print("Erro ao buscar categorias:", e)
        categorias = []

    urls = []

    # HOME
    urls.append("""
    <url>
        <loc>https://girodesportivo.com/</loc>
        <changefreq>hourly</changefreq>
        <priority>1.0</priority>
    </url>
    """)

    # CATEGORIAS
    for c in categorias:
        if not c:
            continue

        c_safe = html.escape(str(c))

        urls.append(f"""
        <url>
            <loc>https://girodesportivo.com/categoria/{c_safe}</loc>
            <changefreq>daily</changefreq>
            <priority>0.7</priority>
        </url>
        """)

    # NOTÍCIAS
    for n in noticias:
        slug = n.get("slug")
        if not slug:
            continue

        slug_safe = html.escape(str(slug))

        criada_em = n.get("criada_em")
        if hasattr(criada_em, "strftime"):
            lastmod = criada_em.strftime("%Y-%m-%d")
        else:
            lastmod = datetime.utcnow().strftime("%Y-%m-%d")

        urls.append(f"""
        <url>
            <loc>https://girodesportivo.com/noticia/{slug_safe}</loc>
            <lastmod>{lastmod}</lastmod>
            <changefreq>daily</changefreq>
            <priority>0.8</priority>
        </url>
        """)

    xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
{''.join(urls)}
</urlset>
"""

    return Response(content=xml.strip(), media_type="application/xml")

from core.futebol_api import buscar_estatisticas_brasileirao

@app.get("/brasileirao-2026", response_class=HTMLResponse)
def brasileirao_2026(request: Request):

    classificacao = buscar_classificacao_brasileirao()
    noticias = listar_por_categoria("Brasileirão", 12)
    jogos = buscar_jogos_do_dia()
    artilharia = buscar_artilharia_brasileirao()
    estatisticas = buscar_estatisticas_brasileirao()

    breadcrumb = gerar_breadcrumb_schema([
        ("Home", "https://girodesportivo.com/"),
        ("Brasileirão 2026", "https://girodesportivo.com/brasileirao-2026")
    ])

    return templates.TemplateResponse(
        "brasileirao_2026.html",
        {
            "request": request,
            "classificacao": classificacao,
            "noticias": noticias,
            "jogos": jogos,
            "artilharia": artilharia,
            "breadcrumb_schema": breadcrumb,
            "categoria_ativa": "Brasileirão",
            "estatisticas": estatisticas
        }
    )


from fastapi.responses import Response
from datetime import datetime, timedelta

@app.get("/sitemap-news.xml", response_class=Response)
def sitemap_news():

    noticias = listar_noticias_publicadas(limit=200)

    agora = datetime.utcnow()
    limite = agora - timedelta(days=2)

    urls = []

    for n in noticias:
        criada = n.get("criada_em")

        if not criada:
            continue

        # Se vier como string, ignora
        if not hasattr(criada, "strftime"):
            continue

        # Remove timezone se existir
        criada_naive = criada.replace(tzinfo=None)

        if criada_naive < limite:
            continue

        titulo = (
        n.get("titulo_editorial")
        or n.get("titulo")
        or "Notícia Giro Desportivo"
    )


        urls.append(f"""
        <url>
            <loc>https://girodesportivo.com/noticia/{n.get('slug')}</loc>
            <news:news>
                <news:publication>
                    <news:name>Giro Desportivo</news:name>
                    <news:language>pt</news:language>
                </news:publication>
                <news:publication_date>{criada_naive.strftime('%Y-%m-%dT%H:%M:%S-03:00')}</news:publication_date>
                <news:title><![CDATA[{titulo}]]></news:title>
            </news:news>
        </url>
        """)

    xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"
        xmlns:news="http://www.google.com/schemas/sitemap-news/0.9">
{''.join(urls)}
</urlset>
"""

    return Response(content=xml.strip(), media_type="application/xml")

@app.get("/autor/redacao-giro-desportivo", response_class=HTMLResponse)
def autor_redacao(request: Request):

    noticias = listar_noticias_publicadas(limit=20)

    return templates.TemplateResponse(
        "autor.html",
        {
            "request": request,
            "autor_nome": "Redação Giro Desportivo",
            "autor_slug": "redacao-giro-desportivo",
            "autor_bio": "A Redação do Giro Desportivo é especializada na cobertura de futebol nacional e internacional, com foco em Campeonato Brasileiro, mercado da bola e grandes competições mundiais.",
            "noticias": noticias
        }
    )

@app.get("/artilharia-brasileirao-2026", response_class=HTMLResponse)
def artilharia(request: Request):

    artilharia = buscar_artilharia_brasileirao() or []

    return templates.TemplateResponse(
        "artilharia.html",
        {
            "request": request,
            "artilharia": artilharia,
            "categorias": listar_categorias(),
            "categoria_ativa": None
        }
    )

import requests
import os

def buscar_artilharia_brasileirao():

    BASE_URL = "https://v3.football.api-sports.io"
    API_KEY = os.getenv("API_FOOTBALL_KEY")

    if not API_KEY:
        print("API_FOOTBALL_KEY não encontrada")
        return []

    headers = {
        "x-apisports-key": API_KEY
    }

    url = f"{BASE_URL}/players/topscorers"

    for season in [2026, 2025, 2024, 2023]:

        params = {
            "league": 71,
            "season": season
        }

        try:
            response = requests.get(
                url,
                headers=headers,
                params=params,
                timeout=10
            )

            data = response.json()

        except Exception as e:
            print("Erro API:", e)
            continue

        if not data.get("response"):
            continue

        artilheiros = []

        for item in data["response"]:
            player = item.get("player", {})
            statistics = item.get("statistics", [{}])[0]

            artilheiros.append({
                "nome": player.get("name"),
                "foto": player.get("photo"),
                "time": statistics.get("team", {}).get("name"),
                "gols": statistics.get("goals", {}).get("total"),
                "jogos": statistics.get("games", {}).get("appearences"),
            })

        return artilheiros

    return []

@app.get("/jogador/{slug}", response_class=HTMLResponse)
def pagina_jogador(slug: str, request: Request):

    jogador = buscar_ou_criar_jogador(slug)

    if not jogador:
        raise HTTPException(status_code=404)

    noticias = listar_noticias_por_jogador(jogador["id"])

    return templates.TemplateResponse(
        "jogador.html",
        {
            "request": request,
            "jogador": jogador,
            "noticias": noticias,
            "categorias": listar_categorias(),
            "categoria_ativa": None
        }
    )

from core.database import buscar_jogadores_por_nome


@app.get("/admin/buscar-jogador")
def buscar_jogador_api(query: str):
    return buscar_jogadores_por_nome(query)

@app.get("/politica-de-correcao", response_class=HTMLResponse)
def politica_correcao(request: Request):
    return templates.TemplateResponse(
        "politica-correcao.html",
        {
            "request": request,
            "categorias": listar_categorias(),
            "categoria_ativa": None
        }
    )

from core.database import buscar_autor_por_slug, listar_noticias_por_autor

@app.get("/autor/{slug}", response_class=HTMLResponse)
def pagina_autor(slug: str, request: Request):

    autor = buscar_autor_por_slug(slug)

    if not autor:
        raise HTTPException(status_code=404)

    noticias = listar_noticias_por_autor(autor["id"], limit=12)

    return templates.TemplateResponse(
        "autor.html",
        {
            "request": request,
            "autor": autor,
            "noticias": noticias,
            "total_materias": len(noticias),
        }
    )

from fastapi import HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from openai import OpenAI
import os
import json

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


# ===============================
# 🔥 MODELO DE ENTRADA
# ===============================

class SEORequest(BaseModel):
    titulo: str
    resumo: str | None = None


# ===============================
# 🚀 ENDPOINT SEO
# ===============================

@app.post("/admin/seo-generate")
async def gerar_seo(payload: SEORequest):

    if not payload.titulo:
        raise HTTPException(status_code=400, detail="Título é obrigatório")

    titulo = payload.titulo
    resumo = payload.resumo or ""

    prompt = f"""
Você é um especialista em SEO para portais esportivos brasileiros.

Gere:

1) meta_title (até 60 caracteres, altamente clicável)
2) meta_description (até 155 caracteres, persuasiva)
3) slug_otimizado (minúsculo, com hífens, sem acentos)
4) h2_sugeridos (lista com 5 subtítulos estratégicos)

Base:
Título: {titulo}
Resumo: {resumo}

Responda exclusivamente em JSON válido neste formato:

{{
  "meta_title": "...",
  "meta_description": "...",
  "slug_otimizado": "...",
  "h2_sugeridos": ["...", "...", "...", "...", "..."]
}}
"""

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.4,
        )

        content = response.choices[0].message.content

        if not content:
            raise HTTPException(status_code=500, detail="IA retornou vazio")
        
        content = content.strip()
        
        # 🔥 Remove markdown code block se existir
        if content.startswith("```"):
            content = content.replace("```json", "")
            content = content.replace("```", "")
            content = content.strip()
        
        # 🔥 Tenta encontrar JSON dentro do texto
        import re
        
        json_match = re.search(r"\{.*\}", content, re.DOTALL)
        
        if not json_match:
            raise HTTPException(status_code=500, detail="IA não retornou JSON válido")
        
        json_str = json_match.group(0)
        
        seo_data = json.loads(json_str)
        
        return seo_data
        
    except json.JSONDecodeError:
        raise HTTPException(
            status_code=500,
            detail="Erro ao interpretar resposta da IA"
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao gerar SEO: {str(e)}"
        )

import requests
from slugify import slugify

API_FOOTBALL_KEY = os.getenv("API_FOOTBALL_KEY")


def buscar_time_api_football(nome: str):

    url = "https://v3.football.api-sports.io/teams"
    headers = {
        "x-apisports-key": API_FOOTBALL_KEY
    }

    response = requests.get(url, headers=headers, params={"search": nome})

    if response.status_code != 200:
        return None

    data = response.json()

    if not data.get("response"):
        return None

    team_data = data["response"][0]["team"]

    return {
        "nome": team_data["name"],
        "slug": slugify(team_data["name"]),
        "escudo_url": team_data["logo"],
        "api_id": team_data["id"]
    }

from fastapi import Query

@app.get("/api/time-info")
def api_time_info(nome: str = Query(...)):

    slug = slugify(nome)

    # 1️⃣ Busca no banco
    time = buscar_time_por_slug(slug)

    if time:
        return time

    # 2️⃣ Busca na API
    api_data = buscar_time_api_football(nome)

    if not api_data:
        return {"nome": nome, "escudo_url": "/static/img/default-team.png"}

    # 3️⃣ Salva no banco
    inserir_time(
        api_data["nome"],
        api_data["slug"],
        api_data["escudo_url"],
        api_data["api_id"]
    )

    return {
        "nome": api_data["nome"],
        "escudo_url": api_data["escudo_url"]
    }

from core.routers import midias

app.include_router(midias.router)
