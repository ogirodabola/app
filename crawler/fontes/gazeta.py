# crawler/fontes/gazeta.py

import requests
from bs4 import BeautifulSoup
from datetime import datetime

from crawler.utils import extrair_imagem_artigo, PLACEHOLDER_PADRAO


RSS_GAZETA = "https://www.gazetaesportiva.com/feed/"

HEADERS = {
    "User-Agent": "GiroDesportivoBot/1.0"
}


# ======================================================
# VALIDAÇÃO DE URL
# ======================================================

def url_valida(url: str) -> bool:
    if not url:
        return False

    url = url.strip().lower()

    if "uol.com.br" in url:
        return False

    if "gazetaesportiva.com" not in url:
        return False

    return True


# ======================================================
# COLETA DE URLs DO RSS (ROBUSTA)
# ======================================================

def coletar_urls_rss():
    resp = requests.get(RSS_GAZETA, headers=HEADERS, timeout=15)
    resp.raise_for_status()

    soup = BeautifulSoup(resp.text, "xml")
    urls = []

    for item in soup.find_all("item"):
        url = None

        # 1️⃣ <link>
        link_tag = item.find("link")
        if link_tag and link_tag.text:
            url = link_tag.text.strip()

        # 2️⃣ <guid isPermaLink="true">
        if not url:
            guid = item.find("guid")
            if guid and guid.get("isPermaLink") == "true":
                url = guid.text.strip()

        if url and url_valida(url):
            urls.append(url)

    return urls


# ======================================================
# EXTRAÇÃO DO CONTEÚDO DO ARTIGO
# ======================================================

def extrai_conteudo_gazeta(soup):
    seletores = [
        "div[itemprop='articleBody']",
        "div.post-content",
        "div.entry-content",
        "article div",
        "article"
    ]

    for seletor in seletores:
        bloco = soup.select_one(seletor)
        if bloco:
            paragrafos = bloco.find_all("p")
            if len(paragrafos) >= 2:
                return str(bloco)

    return None


# ======================================================
# EXTRAÇÃO DO ARTIGO COMPLETO
# ======================================================

def extrair_artigo_gazeta(url: str):
    resp = requests.get(url, headers=HEADERS, timeout=15)
    if resp.status_code != 200:
        return None

    soup = BeautifulSoup(resp.text, "html.parser")

    # Título
    h1 = soup.find("h1")
    if not h1:
        return None

    titulo = h1.get_text(strip=True)

    # Subtítulo (opcional)
    h2 = soup.find("h2")
    subtitulo = h2.get_text(strip=True) if h2 else None

    # Conteúdo
    conteudo_html = extrai_conteudo_gazeta(soup)
    if not conteudo_html:
        return None

    # Imagem
    imagem = extrair_imagem_artigo(soup)
    if not imagem:
        imagem = PLACEHOLDER_PADRAO

    # Data
    publicado_em = None
    time_el = soup.find("time")
    if time_el and time_el.has_attr("datetime"):
        try:
            publicado_em = datetime.fromisoformat(
                time_el["datetime"].replace("Z", "")
            )
        except Exception:
            publicado_em = None

    return {
        "fonte": "gazeta_esportiva",
        "titulo": titulo,
        "subtitulo": subtitulo,
        "conteudo_html": conteudo_html,
        "imagem": imagem,
        "url": url,
        "publicado_em": publicado_em,
    }


# ======================================================
# COLETOR PRINCIPAL DA FONTE
# ======================================================

def coletar_noticias_gazeta(limit=20):
    noticias = []

    try:
        urls = coletar_urls_rss()
    except Exception as e:
        print(f"[GAZETA] erro ao ler RSS: {e}")
        return noticias

    for url in urls[:limit]:
        try:
            noticia = extrair_artigo_gazeta(url)
            if noticia:
                noticias.append(noticia)

        except Exception as e:
            print(f"[GAZETA] erro ao processar {url}: {e}")

    return noticias
