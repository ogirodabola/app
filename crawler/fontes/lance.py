import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse

from core.classificacao import classificar_noticia, gerar_slug
from crawler.utils import extrair_imagem_e_credito_lance


HEADERS = {
    "User-Agent": "Giro Desportivo Bot"
}

BASE_URL = "https://www.lance.com.br"
MAX_NOTICIAS = 20


def coletar_links_lance():
    """
    Coleta APENAS links editoriais reais do Lance
    """
    response = requests.get(BASE_URL, headers=HEADERS, timeout=15)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "lxml")

    links = set()

    # Cards editoriais reais do Lance
    for a in soup.select("a[href^='/']"):
        href = a.get("href")

        # regra editorial: só futebol
        if "/futebol/" not in href:
            continue

        # ignora coisas curtas ou genéricas
        if len(href) < 25:
            continue

        url = urljoin(BASE_URL, href)

        # segurança absoluta: nunca sair do domínio
        if urlparse(url).netloc != "www.lance.com.br":
            continue

        links.add(url)

        if len(links) >= MAX_NOTICIAS:
            break

    return list(links)


def coletar_noticias_lance():
    print("[LANCE] Iniciando crawler do Lance")

    noticias = []
    links = coletar_links_lance()

    for url in links:
        try:
            r = requests.get(url, headers=HEADERS, timeout=15)
            r.raise_for_status()
            soup = BeautifulSoup(r.text, "lxml")

            # Título editorial
            h1 = soup.find("h1")
            if not h1:
                continue

            titulo = h1.get_text(strip=True)
            if len(titulo) < 20:
                continue

            imagem, credito = extrair_imagem_e_credito_lance(soup)

            noticias.append({
                "titulo": titulo,
                "url": url,
                "fonte": "Lance!",
                "categoria": classificar_noticia(titulo),
                "slug": gerar_slug(titulo),
                "resumo": titulo[:160],
                "imagem": imagem,
                "imagem_credito": credito
            })

        except Exception as e:
            print(f"[LANCE ERRO] {url}: {e}")

    print(f"[LANCE] Notícias coletadas: {len(noticias)}")
    return noticias
