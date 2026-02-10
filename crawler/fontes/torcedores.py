# crawler/fontes/torcedores.py

import requests
from bs4 import BeautifulSoup
from datetime import datetime
from crawler.utils import extrair_imagem_artigo, PLACEHOLDER_PADRAO

HEADERS = {
    "User-Agent": "GiroDesportivoBot/1.0"
}

PAGINAS_TORCEDORES = [
    "https://www.torcedores.com/noticias/futebol-brasileiro",
    "https://www.torcedores.com/noticias/mercado-da-bola"
]

PALAVRAS_MERCADO = [
    "mercado", "contratação", "contratacao",
    "reforço", "reforco", "negociação",
    "negociacao", "transferência", "transferencia",
    "sondagem", "proposta"
]


def url_valida(url: str) -> bool:
    if not url:
        return False

    if "uol.com.br" in url:
        return False

    if "torcedores.com" not in url:
        return False

    return True


def parece_mercado_da_bola(texto: str) -> bool:
    texto = texto.lower()
    return any(p in texto for p in PALAVRAS_MERCADO)


def coletar_noticias_torcedores(limit=30):
    urls = set()
    noticias = []

    for pagina in PAGINAS_TORCEDORES:
        try:
            resp = requests.get(pagina, headers=HEADERS, timeout=10)
            if resp.status_code != 200:
                continue

            soup = BeautifulSoup(resp.text, "html.parser")

            for a in soup.select("a[href]"):
                href = a["href"]

                if not href.startswith("https://www.torcedores.com"):
                    continue

                if url_valida(href):
                    urls.add(href)

        except Exception as e:
            print(f"[TORCEDORES] erro ao coletar URLs: {e}")

    for url in list(urls)[:limit]:
        try:
            noticia = extrair_artigo_torcedores(url)
            if noticia:
                noticias.append(noticia)

        except Exception as e:
            print(f"[TORCEDORES] erro ao processar {url}: {e}")

    return noticias


def extrair_artigo_torcedores(url: str):
    resp = requests.get(url, headers=HEADERS, timeout=10)

    if resp.status_code != 200:
        return None

    soup = BeautifulSoup(resp.text, "html.parser")

    titulo_el = soup.select_one("h1")
    if not titulo_el:
        return None

    titulo = titulo_el.get_text(strip=True)

    # Filtro editorial obrigatório
    if not parece_mercado_da_bola(titulo):
        return None

    article = soup.select_one("article")
    if not article:
        return None

    conteudo_html = str(article)

    imagem = extrair_imagem_artigo(soup)
    if not imagem:
        imagem = PLACEHOLDER_PADRAO

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
        "fonte": "torcedores",
        "titulo": titulo,
        "subtitulo": None,
        "conteudo_html": conteudo_html,
        "imagem": imagem,
        "url": url,
        "publicado_em": publicado_em,
    }
