# crawler/fontes/goal.py

import requests
from bs4 import BeautifulSoup
from datetime import datetime
from crawler.utils import extrair_imagem_artigo, PLACEHOLDER_PADRAO

HEADERS = {
    "User-Agent": "GiroDesportivoBot/1.0"
}

PAGINAS_GOAL = [
    "https://www.goal.com/br/notícias",
    "https://www.goal.com/br/campeonatos/libertadores"
]

CLUBES_BR = [
    "flamengo", "palmeiras", "são paulo", "sao paulo",
    "corinthians", "santos", "grêmio", "gremio",
    "internacional", "atlético-mg", "atletico-mg",
    "cruzeiro", "vasco", "botafogo", "fluminense",
    "bahia", "fortaleza", "cuiabá", "cuiaba",
    "athletico-pr", "atlético-go", "atletico-go",
    "goiás", "goias", "bragantino", "red bull bragantino"
]


def url_valida(url: str) -> bool:
    if not url:
        return False

    if "uol.com.br" in url:
        return False

    if "goal.com" not in url:
        return False

    return True


def menciona_clube_br(texto: str) -> bool:
    texto = texto.lower()
    return any(clube in texto for clube in CLUBES_BR)


def coletar_noticias_goal(limit=20):
    urls = set()
    noticias = []

    for pagina in PAGINAS_GOAL:
        try:
            resp = requests.get(pagina, headers=HEADERS, timeout=10)
            if resp.status_code != 200:
                continue

            soup = BeautifulSoup(resp.text, "html.parser")

            for a in soup.select("a[href]"):
                href = a["href"]

                if not href.startswith("/br/"):
                    continue

                url = "https://www.goal.com" + href

                if url_valida(url):
                    urls.add(url)

        except Exception as e:
            print(f"[GOAL] erro ao coletar URLs: {e}")

    for url in list(urls)[:limit]:
        try:
            noticia = extrair_artigo_goal(url)
            if noticia:
                noticias.append(noticia)

        except Exception as e:
            print(f"[GOAL] erro ao processar {url}: {e}")

    return noticias


def extrair_artigo_goal(url: str):
    resp = requests.get(url, headers=HEADERS, timeout=10)

    if resp.status_code != 200:
        return None

    soup = BeautifulSoup(resp.text, "html.parser")

    titulo_el = soup.select_one("h1")
    if not titulo_el:
        return None

    titulo = titulo_el.get_text(strip=True)

    # Filtro editorial obrigatório
    # if not menciona_clube_br(titulo):
    #    return None

    subtitulo_el = soup.select_one("h2")
    subtitulo = subtitulo_el.get_text(strip=True) if subtitulo_el else None

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
        "fonte": "goal_brasil",
        "titulo": titulo,
        "subtitulo": subtitulo,
        "conteudo_html": conteudo_html,
        "imagem": imagem,
        "url": url,
        "publicado_em": publicado_em,
    }
