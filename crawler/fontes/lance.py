import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse

from core.classificacao import classificar_noticia, gerar_slug
from crawler.utils import extrair_imagem_e_credito_por_url


BASE_URL = "https://www.lance.com.br"
EDITORIAS = [
    "/futebol-nacional",
    "/brasileirao"
]

HEADERS = {
    "User-Agent": "Giro Desportivo Bot"
}

MAX_NOTICIAS = 20


def coletar_noticias_lance():
    print("[LANCE] Iniciando crawler do Lance (editorias controladas)")

    links = set()

    for path in EDITORIAS:
        try:
            url_editoria = urljoin(BASE_URL, path)
            r = requests.get(url_editoria, headers=HEADERS, timeout=15)
            r.raise_for_status()
            soup = BeautifulSoup(r.text, "lxml")

            for a in soup.select("a[href]"):
                href = a.get("href")

                if not href:
                    continue

                if not href.startswith("/"):
                    continue

                if len(href) < 25:
                    continue

                url = urljoin(BASE_URL, href)

                # segurança absoluta: só domínio do Lance
                if urlparse(url).netloc != "www.lance.com.br":
                    continue

                # evita páginas de editoria, tags etc
                if any(x in url for x in ["/tag/", "/autor/", "/coluna/"]):
                    continue

                links.add(url)

                if len(links) >= MAX_NOTICIAS:
                    break

        except Exception as e:
            print(f"[LANCE ERRO] Editorias {path}: {e}")

    noticias = []

    for url in list(links)[:MAX_NOTICIAS]:
        try:
            r = requests.get(url, headers=HEADERS, timeout=15)
            r.raise_for_status()
            soup = BeautifulSoup(r.text, "lxml")

            h1 = soup.find("h1")
            if not h1:
                continue

            titulo = h1.get_text(strip=True)
            if len(titulo) < 15:
                continue

            imagem, credito = extrair_imagem_e_credito_por_url(
                url, fonte_nome="Lance!"
            )

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
