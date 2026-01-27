import requests
from bs4 import BeautifulSoup

from crawler.fontes import FONTES
from core.database import salvar_noticia

HEADERS = {
    "User-Agent": "Mozilla/5.0 (O Giro da Bola)"
}

MAX_POR_FONTE = 30


def extrair_noticias_fonte(fonte):
    """
    Extrai notícias de uma fonte específica.
    Retorna lista de dicts com titulo, url e fonte.
    """

    response = requests.get(
        fonte["url"],
        headers=HEADERS,
        timeout=10
    )
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "lxml")

    noticias = []

    for link in soup.select("a"):
        titulo = link.get_text(strip=True)
        url = link.get("href")

        if not titulo or not url:
            continue

        if not url.startswith("http"):
            continue

        # Limpeza básica
        titulo = titulo.replace("\n", " ").strip()

        noticias.append({
            "titulo": titulo,
            "url": url,
            "fonte": fonte["nome"]
        })

        if len(noticias) >= MAX_POR_FONTE:
            break

    return noticias


def rodar_crawler():
    total_salvas = 0

    for fonte in FONTES:
        print(f"[INFO] Coletando: {fonte['nome']}")

        try:
            noticias = extrair_noticias_fonte(fonte)

            for n in noticias:
                salvar_noticia(
                    titulo=n["titulo"],
                    url=n["url"],
                    fonte=n["fonte"]
                )
                total_salvas += 1

        except Exception as e:
            print(f"[ERRO] Fonte {fonte['nome']}: {e}")

    print(f"[OK] Total de notícias processadas: {total_salvas}")


if __name__ == "__main__":
    rodar_crawler()
