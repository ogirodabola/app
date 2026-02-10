# crawler/fontes/gazeta.py

import requests
from bs4 import BeautifulSoup
from datetime import datetime
from crawler.utils import extrair_imagem_artigo, PLACEHOLDER_PADRAO


RSS_GAZETA = "https://www.gazetaesportiva.com/feed/"

HEADERS = {
    "User-Agent": "GiroDesportivoBot/1.0"
}


def url_valida(url: str) -> bool:
    if not url:
        return False

    if "uol.com.br" in url:
        return False

    if "gazetaesportiva.com" not in url:
        return False

    return True


def coletar_urls_rss():
    resp = requests.get(RSS_GAZETA, headers=HEADERS, timeout=15)
    resp.raise_for_status()

    soup = BeautifulSoup(resp.text, "xml")
    urls = []

    for item in soup.find_all("item"):
        link = item.find("link")
        if link and url_valida(link.text):
            urls.append(link.text.strip())

    return urls


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

    # Subtítulo (nem sempre existe)
    h2 = soup.find("h2")
    subtitulo = h2.get_text(strip=True) if h2 else None

    # Conteúdo
    article = soup.select_one("div[itemprop='articleBody']")
    if not article:
        return None

    conteudo_html = str(article)

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
