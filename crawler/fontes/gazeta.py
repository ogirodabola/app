# crawler/fontes/gazeta.py

import requests
import feedparser
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


def coletar_noticias_gazeta(limit=20):
    feed = feedparser.parse(RSS_GAZETA)
    noticias = []

    for entry in feed.entries[:limit]:
        url = entry.get("link")

        if not url_valida(url):
            continue

        try:
            noticia = extrair_artigo_gazeta(url)
            if noticia:
                noticias.append(noticia)

        except Exception as e:
            print(f"[GAZETA] erro ao processar {url}: {e}")

    return noticias


def extrair_artigo_gazeta(url: str):
    response = requests.get(url, headers=HEADERS, timeout=10)

    if response.status_code != 200:
        return None

    soup = BeautifulSoup(response.text, "html.parser")

    # título
    titulo_el = soup.select_one("h1")
    if not titulo_el:
        return None

    titulo = titulo_el.get_text(strip=True)

    # subtítulo (nem sempre existe)
    subtitulo_el = soup.select_one("h2")
    subtitulo = subtitulo_el.get_text(strip=True) if subtitulo_el else None

    # conteúdo
    article = soup.select_one("div[itemprop='articleBody']")
    if not article:
        return None

    conteudo_html = str(article)

    # imagem
    imagem = extrair_imagem_artigo(soup)
    if not imagem:
        imagem = PLACEHOLDER_PADRAO

    # data
    publicado_em = None
    time_el = soup.select_one("time")
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
